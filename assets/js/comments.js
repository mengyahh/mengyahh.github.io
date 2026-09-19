/* Comments for blog posts. Talks to the Cloudflare Worker in /worker (API base + Turnstile site key come from data-* attributes). */
(function () {
  'use strict';
  var root = document.getElementById('comments');
  if (!root) return;
  var API = (root.getAttribute('data-api') || '').replace(/\/+$/, '');
  var PAGE = root.getAttribute('data-page');
  var SITEKEY = root.getAttribute('data-sitekey');
  if (!API || !PAGE || !SITEKEY) return;

  var wrap = root.querySelector('.c-formwrap');
  var form = root.querySelector('.c-form');
  var list = root.querySelector('.c-list');
  var msg = root.querySelector('.c-msg');
  var submitBtn = form.querySelector('button[type=submit]');
  var cancelBtn = form.querySelector('.c-cancel');
  var replyNote = form.querySelector('.c-replying');
  var slot = wrap.parentNode;                     // where the form lives when it is not answering anyone
  var t0 = Date.now();
  var token = '';
  var widgetId = null;
  var tsRequested = false;
  var replyTarget = null;
  var byId = {};
  var NS = 'http://www.w3.org/2000/svg';
  var KEY_NAME = 'mh-comment-name', KEY_EMAIL = 'mh-comment-email';

  form.hidden = false;

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function say(text, kind) {
    msg.textContent = text || '';
    msg.className = 'c-msg' + (kind ? ' is-' + kind : '');
  }
  function store(k, v) { try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { /* private mode */ } }
  function stored(k) { try { return localStorage.getItem(k) || ''; } catch (e) { return ''; } }

  /* ---------- avatars: generated locally from the (keyed) hash, no third-party requests ---------- */
  function svgEl(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  function avatar(c) {
    var svg = svgEl('svg', { viewBox: '0 0 40 40', class: 'c-avatar', 'aria-hidden': 'true', focusable: 'false' });
    if (c.is_owner) {
      svg.classList.add('is-owner');
      svg.appendChild(svgEl('rect', { width: 40, height: 40, class: 'av-bg' }));
      var t = svgEl('text', { x: 20, y: 27, 'text-anchor': 'middle', class: 'av-mark' });
      t.textContent = '萌';
      svg.appendChild(t);
    } else if (c.avatar && /^[0-9a-f]{12}$/.test(c.avatar)) {
      var hue = Math.round(parseInt(c.avatar.slice(0, 2), 16) / 255 * 360);
      var bits = parseInt(c.avatar.slice(2, 8), 16);             // 24 bits: 15 are used (3 columns x 5 rows, mirrored)
      svg.appendChild(svgEl('rect', { width: 40, height: 40, fill: 'hsl(' + hue + ',40%,90%)' }));
      for (var i = 0; i < 15; i++) {
        if (!((bits >> i) & 1)) continue;
        var col = Math.floor(i / 5), row = i % 5;
        [col, 4 - col].forEach(function (cx, n) {
          if (n === 1 && cx === col) return;
          svg.appendChild(svgEl('rect', { x: 5 + cx * 6, y: 5 + row * 6, width: 6, height: 6, fill: 'hsl(' + hue + ',50%,42%)' }));
        });
      }
    } else {
      svg.classList.add('is-anon');
      svg.appendChild(svgEl('rect', { width: 40, height: 40, class: 'av-bg' }));
      svg.appendChild(svgEl('circle', { cx: 20, cy: 16, r: 6.5, class: 'av-fg' }));
      svg.appendChild(svgEl('path', { d: 'M7 40c0-9 6-14 13-14s13 5 13 14z', class: 'av-fg' }));
    }
    return svg;
  }

  var dtf = new Intl.DateTimeFormat('zh-TW', { timeZone: 'Asia/Taipei', hour12: false, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  function when(ms) {
    var p = {};
    dtf.formatToParts(new Date(ms)).forEach(function (x) { p[x.type] = x.value; });
    return p.year + '.' + p.month + '.' + p.day + ' / ' + (p.hour === '24' ? '00' : p.hour) + ':' + p.minute;
  }

  /* ---------- rendering ---------- */
  function item(c, isReply) {
    var box = el('div', 'c-item' + (isReply ? ' is-reply' : ''));
    box.setAttribute('data-id', c.id);
    box.id = 'c-' + c.id;
    box.appendChild(avatar(c));
    var main = el('div', 'c-main');
    var head = el('div', 'c-head');
    var who = el('span', 'c-name', c.name);
    head.appendChild(who);
    if (c.is_owner) head.appendChild(el('span', 'c-badge', '作者'));
    var time = el('time', 'c-time', when(c.created_at));
    time.setAttribute('datetime', new Date(c.created_at).toISOString());
    head.appendChild(time);
    var btn = el('button', 'c-reply', '回覆');
    btn.type = 'button';
    btn.setAttribute('aria-label', '回覆 ' + c.name + ' 的留言');
    btn.addEventListener('click', function () { startReply(c, box); });
    head.appendChild(btn);
    main.appendChild(head);
    var text = el('div', 'c-text');
    var target = c.reply_to && c.reply_to !== c.parent_id ? byId[c.reply_to] : null;
    if (target) text.appendChild(el('span', 'c-to', '回覆 ' + target.name + '　'));
    text.appendChild(document.createTextNode(c.body));            // plain text only: no HTML from commenters is ever interpreted
    main.appendChild(text);
    box.appendChild(main);
    return box;
  }

  function render(comments) {
    byId = {};
    comments.forEach(function (c) { byId[c.id] = c; });
    var tops = comments.filter(function (c) { return !c.parent_id; }).sort(function (a, b) { return b.created_at - a.created_at; });
    var kids = {};
    comments.forEach(function (c) { if (c.parent_id) (kids[c.parent_id] = kids[c.parent_id] || []).push(c); });
    cancelReply(true);                                            // the form must not be inside a node we are about to replace
    list.textContent = '';
    tops.forEach(function (c) {
      var top = item(c, false);
      var rs = (kids[c.id] || []).sort(function (a, b) { return a.created_at - b.created_at; });
      if (rs.length) {
        var box = el('div', 'c-replies');
        rs.forEach(function (r) { box.appendChild(item(r, true)); });
        top.querySelector('.c-main').appendChild(box);
      }
      list.appendChild(top);
    });
    if (!tops.length) list.appendChild(el('p', 'c-empty', '還沒有留言，來當第一個吧。'));
  }

  function jumpToHash() {
    if (!/^#c-\d+$/.test(location.hash)) return;
    var t = document.getElementById(location.hash.slice(1));
    if (!t) return;
    t.classList.add('is-target');
    t.scrollIntoView({ block: 'center' });
  }

  function load() {
    return fetch(API + '/comments?page=' + encodeURIComponent(PAGE))
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { render(d.comments || []); jumpToHash(); })
      .catch(function () { list.textContent = ''; list.appendChild(el('p', 'c-empty', '留言暫時載入失敗，請稍後重新整理。')); });
  }

  /* ---------- reply: the single form moves under the comment being answered ---------- */
  function moveForm(to) {
    to.appendChild(wrap);
    if (widgetId !== null && window.turnstile) {                  // iframes reload when moved: start a fresh challenge
      try { window.turnstile.remove(widgetId); } catch (e) { /* ignore */ }
      widgetId = null; token = '';
      renderWidget();
    }
  }
  function startReply(c, box) {
    replyTarget = c;
    replyNote.textContent = '回覆 ' + c.name;
    replyNote.hidden = false;
    cancelBtn.hidden = false;
    moveForm(box.querySelector('.c-main'));
    form.elements.body.focus();
  }
  function cancelReply(silent) {
    if (!replyTarget && wrap.parentNode === slot) return;
    replyTarget = null;
    replyNote.hidden = true;
    cancelBtn.hidden = true;
    if (silent) { slot.insertBefore(wrap, slot.querySelector('.c-msg')); return; }
    moveForm(slot);
    slot.insertBefore(wrap, slot.querySelector('.c-msg'));
  }
  cancelBtn.addEventListener('click', function () { cancelReply(false); });

  /* ---------- Turnstile (loaded only when someone starts writing) ---------- */
  function renderWidget() {
    if (!window.turnstile || widgetId !== null) return;
    widgetId = window.turnstile.render(form.querySelector('.c-turnstile'), {
      sitekey: SITEKEY,
      theme: 'auto',
      language: 'zh-tw',
      callback: function (t) { token = t; },
      'expired-callback': function () { token = ''; },
      'error-callback': function () { token = ''; say('驗證元件載入失敗，請重新整理頁面再試。', 'error'); },
    });
  }
  function ensureTurnstile() {
    if (window.turnstile) { renderWidget(); return; }
    if (tsRequested) return;
    tsRequested = true;
    var s = document.createElement('script');
    s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
    s.async = true;
    s.onload = renderWidget;
    s.onerror = function () { tsRequested = false; say('無法載入驗證元件，請確認網路後重新整理頁面。', 'error'); };
    document.head.appendChild(s);
  }
  form.addEventListener('focusin', ensureTurnstile);

  /* ---------- submit ---------- */
  form.elements.name.value = stored(KEY_NAME);
  form.elements.email.value = stored(KEY_EMAIL);
  if (form.elements.name.value || form.elements.email.value) form.elements.remember.checked = true;

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var body = form.elements.body.value.trim();
    if (!body) { say('請輸入留言內容。', 'error'); form.elements.body.focus(); return; }
    var email = form.elements.email.value.trim();
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { say('電子郵件的格式好像不太對。', 'error'); form.elements.email.focus(); return; }
    if (!token) { say('請先完成驗證（如果沒有看到驗證框，請稍候幾秒或重新整理頁面）。', 'error'); ensureTurnstile(); return; }

    submitBtn.disabled = true;
    say('送出中…');
    fetch(API + '/comments', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        page: PAGE,
        parent_id: replyTarget ? replyTarget.id : null,
        name: form.elements.name.value.trim(),
        email: email,
        body: body,
        token: token,
        elapsed: Date.now() - t0,
        website: form.elements.website.value,
      }),
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        if (!res.ok) throw new Error(res.d && res.d.error ? res.d.error : '送出失敗，請稍後再試。');
        if (form.elements.remember.checked) { store(KEY_NAME, form.elements.name.value.trim()); store(KEY_EMAIL, email); }
        else { store(KEY_NAME, null); store(KEY_EMAIL, null); }
        form.elements.body.value = '';
        if (res.d.status === 'approved') {
          say('留言已發佈，謝謝你！', 'ok');
          return load();
        }
        cancelReply(false);
        say('留言已送出，審核通過後就會顯示，謝謝你！', 'ok');
      })
      .catch(function (e) { say(e && e.message ? e.message : '送出失敗，請稍後再試。', 'error'); })
      .then(function () {
        submitBtn.disabled = false;
        token = '';
        t0 = Date.now();
        if (window.turnstile && widgetId !== null) { try { window.turnstile.reset(widgetId); } catch (e) { /* ignore */ } }
      });
  });

  load();
})();
