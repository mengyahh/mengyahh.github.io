/* Blog index: search + category/year filters (sidebar). Without JS the whole list stays visible and the year links just jump. */
(function () {
  var rows = Array.prototype.slice.call(document.querySelectorAll('.post-row'));
  if (!rows.length) return;
  var years = Array.prototype.slice.call(document.querySelectorAll('.year[data-year]'));
  var catBtns = Array.prototype.slice.call(document.querySelectorAll('.cat-list [data-cat]'));
  var yearBtns = Array.prototype.slice.call(document.querySelectorAll('.year-chips [data-year]'));
  var form = document.querySelector('form.search');
  var input = document.getElementById('q');
  var clearBtn = document.querySelector('.clear');
  var empty = document.querySelector('.no-result');
  Array.prototype.forEach.call(document.querySelectorAll('.js-only'), function (el) { el.hidden = false; });

  var PAGE = 10;                                            // articles shown at first / per "load more"
  var limit = PAGE;
  var moreBox = document.querySelector('.load-more');
  var state = { q: '', cat: '', year: '' };
  var index = null, indexPromise = null;
  var origAbs = {};
  rows.forEach(function (r) { var a = r.querySelector('.row-abs'); origAbs[r.getAttribute('data-slug')] = a ? a.textContent : ''; });

  function loadIndex() {
    if (index) return Promise.resolve(index);
    if (!indexPromise) {
      indexPromise = fetch(form.getAttribute('data-index')).then(function (r) { return r.json(); }).then(function (list) {
        index = {};
        list.forEach(function (a) {
          a.hay = (a.title + ' ' + (a.cats || []).join(' ') + ' ' + (a.tags || []).join(' ') + ' ' + a.abstract + ' ' + a.text).toLowerCase();
          index[a.slug] = a;
        });
        return index;
      }).catch(function () { indexPromise = null; index = null; return null; });
    }
    return indexPromise;
  }

  function terms() { return state.q.toLowerCase().split(/\s+/).filter(Boolean); }

  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function snippet(a, ts) {
    var text = a.text, low = text.toLowerCase(), at = -1, len = 0;
    for (var i = 0; i < ts.length; i++) {
      var k = low.indexOf(ts[i]);
      if (k >= 0 && (at < 0 || k < at)) { at = k; len = ts[i].length; }
    }
    if (at < 0) return null;                                  // matched only in the title / abstract
    var from = Math.max(0, at - 30), to = Math.min(text.length, at + len + 60);
    var out = esc(text.slice(from, at)) + '<mark>' + esc(text.slice(at, at + len)) + '</mark>' + esc(text.slice(at + len, to));
    return (from > 0 ? '…' : '') + out + (to < text.length ? '…' : '');
  }

  function apply() {
    var ts = terms();
    var visible = 0;
    rows.forEach(function (r) {
      var slug = r.getAttribute('data-slug');
      var ok = true;
      if (state.cat && (r.getAttribute('data-cats') || '').split('|').indexOf(state.cat) === -1) ok = false;
      if (ok && state.year && r.closest('.year').getAttribute('data-year') !== state.year) ok = false;
      var abs = r.querySelector('.row-abs');
      if (ok && ts.length) {
        var a = index && index[slug];
        if (!a) ok = false;
        else {
          ok = ts.every(function (t) { return a.hay.indexOf(t) !== -1; });
          if (ok && abs) { var sn = snippet(a, ts); if (sn) abs.innerHTML = sn; else abs.textContent = origAbs[slug]; }
        }
      } else if (abs) {
        abs.textContent = origAbs[slug];
      }
      r.hidden = !ok;
      r._match = ok;
      if (ok) visible++;
    });
    var shown = 0;                                            // only the first `limit` matches stay visible
    rows.forEach(function (r) {
      if (!r._match) return;
      if (shown >= limit) r.hidden = true; else shown++;
    });
    if (moreBox) moreBox.hidden = shown >= visible;
    years.forEach(function (y) { y.hidden = !y.querySelector('.post-row:not([hidden])'); });
    if (empty) empty.hidden = visible > 0 || (terms().length > 0 && !index);   // wait for the index before saying "nothing found"
    catBtns.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-cat') === state.cat ? 'true' : 'false'); });
    yearBtns.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-year') === state.year ? 'true' : 'false'); });
    if (clearBtn) clearBtn.hidden = !(state.q || state.cat || state.year);
    try {
      var p = new URLSearchParams();
      if (state.q) p.set('q', state.q);
      if (state.cat) p.set('cat', state.cat);
      if (state.year) p.set('year', state.year);
      history.replaceState(null, '', location.pathname + (p.toString() ? '?' + p.toString() : ''));
    } catch (e) { /* file:// or blocked: ignore */ }
  }

  function showMore() { limit += PAGE; apply(); }

  function setState(patch) {
    limit = PAGE;                                             // a new search/filter starts from the top again
    for (var k in patch) state[k] = patch[k];
    if (state.q && !index) { loadIndex().then(apply); }
    apply();
  }

  catBtns.forEach(function (b) {
    b.addEventListener('click', function () { setState({ cat: state.cat === b.getAttribute('data-cat') ? '' : b.getAttribute('data-cat') }); });
  });
  yearBtns.forEach(function (b) {
    b.addEventListener('click', function (ev) {
      ev.preventDefault();
      setState({ year: state.year === b.getAttribute('data-year') ? '' : b.getAttribute('data-year') });
    });
  });
  if (input) {
    input.addEventListener('focus', loadIndex);
    input.addEventListener('input', function () { setState({ q: input.value.trim() }); });
  }
  if (form) form.addEventListener('submit', function (ev) { ev.preventDefault(); });
  if (clearBtn) clearBtn.addEventListener('click', function () { if (input) input.value = ''; setState({ q: '', cat: '', year: '' }); });

  if (moreBox) {
    var btn = moreBox.querySelector('button');
    btn.addEventListener('click', showMore);
    if ('IntersectionObserver' in window) {                   // reaching the bottom loads the next batch
      new IntersectionObserver(function (es) { if (es[0].isIntersecting && !moreBox.hidden) showMore(); }, { rootMargin: '300px 0px' }).observe(moreBox);
    }
  }

  // restore state from the URL (?q=&cat=&year=)
  try {
    var qs = new URLSearchParams(location.search);
    var init = { q: qs.get('q') || '', cat: qs.get('cat') || '', year: qs.get('year') || '' };
    if (input) input.value = init.q;
    if (init.q || init.cat || init.year) setState(init);
  } catch (e) { /* ignore */ }
  apply();                                                    // hide everything beyond the first batch
})();
