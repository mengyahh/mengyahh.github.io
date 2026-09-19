/**
 * mengyahh.com comments API — Cloudflare Worker + D1.  Single file, no dependencies.
 *
 * Public:  GET  /comments?page=/blog/2022-08-24/   approved comments of one page (never includes emails)
 *          POST /comments                          new comment (Turnstile-checked, moderated)
 * Admin:   GET  /admin                             moderation page (asks for ADMIN_TOKEN)
 *          GET/POST /admin/api/...                 needs "Authorization: Bearer <ADMIN_TOKEN>"
 *
 * Bindings / settings (see worker/README.md):
 *   DB (D1)            TURNSTILE_SECRET (secret)   ADMIN_TOKEN (secret)   PEPPER (secret, long random string)
 *   ALLOWED_ORIGINS    e.g. "https://mengyahh.com"   (comma separated)
 *   OWNER_NAME         display name of the site owner, reserved so nobody else can use it
 */

const MAX_BODY = 2000;
const MAX_NAME = 40;
const MAX_EMAIL = 254;
const PAGE_RE = /^\/blog\/\d{4}-\d{2}-\d{2}\/$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_FILL_MS = 2500;                      // humans need more than this to type a comment
const RATE_10MIN = 3;
const RATE_DAY = 15;
const enc = new TextEncoder();

const json = (data, status = 200, headers = {}) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...headers },
  });

function corsHeaders(request, env) {
  const origin = request.headers.get('Origin');
  const allowed = (env.ALLOWED_ORIGINS || 'https://mengyahh.com').split(',').map((s) => s.trim()).filter(Boolean);
  if (origin && allowed.includes(origin)) {
    return {
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'content-type',
      'Access-Control-Max-Age': '86400',
      Vary: 'Origin',
    };
  }
  return {};
}

async function hmac(secret, message, len = 12) {
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(message));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, '0')).join('').slice(0, len);
}

async function safeEqual(a, b, pepper) {
  // compare keyed digests so the comparison time does not depend on where the strings differ
  return (await hmac(pepper, 'cmp:' + a, 32)) === (await hmac(pepper, 'cmp:' + b, 32));
}

const publicComment = (r) => ({
  id: r.id,
  parent_id: r.parent_id,
  reply_to: r.reply_to,
  name: r.name,
  avatar: r.avatar || '',
  body: r.body,
  is_owner: !!r.is_owner,
  created_at: r.created_at,
});

const normName = (s) => s.toLowerCase().replace(/[\s　·._-]+/g, '');

/* ------------------------------------------------------------------ public API */

async function listComments(url, env, cors) {
  const page = url.searchParams.get('page') || '';
  if (!PAGE_RE.test(page)) return json({ error: '不支援的頁面' }, 400, cors);
  const { results } = await env.DB
    .prepare("SELECT id, parent_id, reply_to, name, avatar, body, is_owner, created_at FROM comments WHERE page = ? AND status = 'approved' ORDER BY created_at ASC LIMIT 500")
    .bind(page)
    .all();
  return json({ comments: results.map(publicComment) }, 200, cors);
}

async function verifyTurnstile(env, token, ip) {
  if (!token) return false;
  const form = new FormData();
  form.append('secret', env.TURNSTILE_SECRET);
  form.append('response', token);
  if (ip) form.append('remoteip', ip);
  try {
    const r = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: form });
    const d = await r.json();
    return !!d.success;
  } catch (e) {
    return false;
  }
}

async function postComment(request, env, cors) {
  let data;
  try {
    if (Number(request.headers.get('content-length') || 0) > 20000) throw new Error('too large');
    data = await request.json();
  } catch (e) {
    return json({ error: '格式錯誤' }, 400, cors);
  }
  if (!data || typeof data !== 'object') return json({ error: '格式錯誤' }, 400, cors);

  // honeypot: real people never see this field; pretend everything went fine
  if (data.website) return json({ status: 'pending' }, 200, cors);

  const page = String(data.page || '');
  if (!PAGE_RE.test(page)) return json({ error: '不支援的頁面' }, 400, cors);

  const body = String(data.body || '').replace(/\r\n/g, '\n').trim();
  if (!body) return json({ error: '請輸入留言內容' }, 400, cors);
  if (body.length > MAX_BODY) return json({ error: `留言請在 ${MAX_BODY} 字以內` }, 400, cors);

  let name = String(data.name || '').replace(/\s+/g, ' ').trim().slice(0, MAX_NAME);
  if (!name) name = '匿名訪客';
  const reserved = [env.OWNER_NAME || '萌芽', ...(env.RESERVED_NAMES || '').split(',')].map((s) => normName(s.trim())).filter(Boolean);
  if (reserved.includes(normName(name))) return json({ error: '這個名稱是站長專用的，請換一個名稱' }, 400, cors);

  const email = String(data.email || '').trim().toLowerCase();
  if (email && (email.length > MAX_EMAIL || !EMAIL_RE.test(email))) return json({ error: '電子郵件格式不正確' }, 400, cors);

  if (!(Number(data.elapsed) >= MIN_FILL_MS)) return json({ error: '送出得太快了，請稍後再試一次' }, 400, cors);

  const ip = request.headers.get('CF-Connecting-IP') || '';
  if (!(await verifyTurnstile(env, data.token, ip))) return json({ error: '驗證沒有通過，請重新整理頁面後再試' }, 400, cors);

  const now = Date.now();
  const ipHash = await hmac(env.PEPPER, 'ip:' + ip, 16);
  const recent = await env.DB.prepare('SELECT COUNT(*) AS c FROM comments WHERE ip_hash = ? AND created_at > ?').bind(ipHash, now - 10 * 60 * 1000).first();
  const today = await env.DB.prepare('SELECT COUNT(*) AS c FROM comments WHERE ip_hash = ? AND created_at > ?').bind(ipHash, now - 24 * 3600 * 1000).first();
  if (recent.c >= RATE_10MIN || today.c >= RATE_DAY) return json({ error: '留言太頻繁了，請稍後再試' }, 429, cors);

  // replies: always attach to the top-level comment, remember who was answered
  let parentId = null;
  let replyTo = null;
  if (data.parent_id) {
    const target = await env.DB.prepare("SELECT id, page, parent_id FROM comments WHERE id = ? AND status = 'approved'").bind(Number(data.parent_id)).first();
    if (!target || target.page !== page) return json({ error: '找不到要回覆的留言' }, 400, cors);
    parentId = target.parent_id || target.id;
    replyTo = target.id;
  }

  // status: known (previously approved) email + no link spam => published, otherwise wait for review
  const blocked = email ? await env.DB.prepare('SELECT 1 AS x FROM blocked WHERE email = ?').bind(email).first() : null;
  const links = (body.match(/https?:\/\/|www\./gi) || []).length;
  let status = 'pending';
  if (blocked) {
    status = 'spam';
  } else if (email && links <= 1) {
    const known = await env.DB.prepare("SELECT 1 AS x FROM comments WHERE email = ? AND status = 'approved' AND is_owner = 0 LIMIT 1").bind(email).first();
    if (known) status = 'approved';
  }

  const avatar = email ? await hmac(env.PEPPER, 'email:' + email, 12) : '';
  const res = await env.DB
    .prepare('INSERT INTO comments (page, parent_id, reply_to, name, email, avatar, body, status, is_owner, ip_hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)')
    .bind(page, parentId, replyTo, name, email, avatar, body, status, ipHash, now)
    .run();

  if (status === 'approved') {
    return json({ status, comment: publicComment({ id: res.meta.last_row_id, parent_id: parentId, reply_to: replyTo, name, avatar, body, is_owner: 0, created_at: now }) }, 200, cors);
  }
  return json({ status: status === 'spam' ? 'pending' : status }, 200, cors);   // never tell a blocked sender
}

/* ------------------------------------------------------------------ admin API */

async function adminApi(request, url, env) {
  const auth = request.headers.get('Authorization') || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : '';
  if (!env.ADMIN_TOKEN || !token || !(await safeEqual(token, env.ADMIN_TOKEN, env.PEPPER))) return json({ error: 'unauthorized' }, 401);

  const path = url.pathname.replace(/^\/admin\/api/, '');

  if (request.method === 'GET' && path === '/comments') {
    const status = ['pending', 'approved', 'spam'].includes(url.searchParams.get('status')) ? url.searchParams.get('status') : 'pending';
    const { results } = await env.DB
      .prepare('SELECT id, page, parent_id, reply_to, name, email, body, status, is_owner, created_at FROM comments WHERE status = ? ORDER BY created_at DESC LIMIT 200')
      .bind(status)
      .all();
    const counts = await env.DB.prepare('SELECT status, COUNT(*) AS c FROM comments GROUP BY status').all();
    return json({ comments: results, counts: Object.fromEntries(counts.results.map((r) => [r.status, r.c])) });
  }

  const m = path.match(/^\/comments\/(\d+)\/(approve|delete|spam|block)$/);
  if (request.method === 'POST' && m) {
    const id = Number(m[1]);
    const row = await env.DB.prepare('SELECT id, email FROM comments WHERE id = ?').bind(id).first();
    if (!row) return json({ error: 'not found' }, 404);
    if (m[2] === 'approve') await env.DB.prepare("UPDATE comments SET status = 'approved' WHERE id = ?").bind(id).run();
    else if (m[2] === 'spam') await env.DB.prepare("UPDATE comments SET status = 'spam' WHERE id = ?").bind(id).run();
    else if (m[2] === 'delete') await env.DB.prepare('DELETE FROM comments WHERE id = ? OR parent_id = ?').bind(id, id).run();
    else if (m[2] === 'block') {
      if (!row.email) return json({ error: '這則留言沒有 Email，無法封鎖' }, 400);
      await env.DB.prepare('INSERT OR IGNORE INTO blocked (email) VALUES (?)').bind(row.email).run();
      await env.DB.prepare("UPDATE comments SET status = 'spam' WHERE email = ? AND is_owner = 0").bind(row.email).run();
    }
    return json({ ok: true });
  }

  if (request.method === 'POST' && path === '/reply') {
    let d;
    try { d = await request.json(); } catch (e) { return json({ error: '格式錯誤' }, 400); }
    const page = String(d.page || '');
    const body = String(d.body || '').replace(/\r\n/g, '\n').trim();
    if (!PAGE_RE.test(page) || !body || body.length > MAX_BODY) return json({ error: '內容不正確' }, 400);
    let parentId = null;
    let replyTo = null;
    if (d.parent_id) {
      const t = await env.DB.prepare('SELECT id, page, parent_id FROM comments WHERE id = ?').bind(Number(d.parent_id)).first();
      if (!t || t.page !== page) return json({ error: '找不到要回覆的留言' }, 400);
      parentId = t.parent_id || t.id;
      replyTo = t.id;
      await env.DB.prepare("UPDATE comments SET status = 'approved' WHERE id = ? AND status = 'pending'").bind(t.id).run();   // answering = approving
    }
    const res = await env.DB
      .prepare("INSERT INTO comments (page, parent_id, reply_to, name, email, avatar, body, status, is_owner, ip_hash, created_at) VALUES (?, ?, ?, ?, '', '', ?, 'approved', 1, '', ?)")
      .bind(page, parentId, replyTo, env.OWNER_NAME || '萌芽', body, Date.now())
      .run();
    return json({ ok: true, id: res.meta.last_row_id });
  }
  return json({ error: 'not found' }, 404);
}

const ADMIN_HTML = `<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>留言管理</title>
<style>
body{font:15px/1.7 system-ui,"Noto Sans TC","Microsoft JhengHei",sans-serif;margin:0;background:#faf8f1;color:#262a21}
main{max-width:860px;margin:0 auto;padding:24px 18px 80px}
h1{font-size:22px;margin:0 0 14px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 18px}
button{font:inherit;font-size:14px;padding:6px 14px;border-radius:999px;border:1px solid #b9b6a6;background:#fff;color:inherit;cursor:pointer}
button[aria-pressed=true]{background:#4b7a3c;border-color:#4b7a3c;color:#fff}
button.ok{border-color:#4b7a3c;color:#4b7a3c}button.bad{border-color:#b3402f;color:#b3402f}
.c{background:#fff;border:1px solid #dcd8c8;border-radius:10px;padding:14px 16px;margin:0 0 12px}
.m{font-size:13px;color:#6f6b5a;margin:0 0 8px;overflow-wrap:anywhere}.m b{color:#262a21}
.t{white-space:pre-wrap;overflow-wrap:anywhere;margin:0 0 10px}
.a{display:flex;flex-wrap:wrap;gap:8px}textarea{width:100%;font:inherit;padding:8px;border:1px solid #b9b6a6;border-radius:8px;margin-top:8px}
.owner{background:#e3ecdc;border-radius:999px;padding:0 8px;font-size:12px}
#login{display:flex;gap:8px}input{font:inherit;padding:8px 12px;border:1px solid #b9b6a6;border-radius:8px;flex:1}
p.err{color:#b3402f}
</style></head><body><main>
<h1>留言管理</h1>
<form id="login" hidden><input id="tok" type="password" placeholder="管理密碼（ADMIN_TOKEN）" autocomplete="current-password"><button>登入</button></form>
<p class="err" id="err"></p>
<div id="app" hidden><div class="bar" id="tabs"></div><div id="list"></div></div>
<script>
var T=sessionStorage.getItem('tok')||'',S='pending',$=function(i){return document.getElementById(i)};
function api(p,o){o=o||{};o.headers=Object.assign({Authorization:'Bearer '+T,'content-type':'application/json'},o.headers||{});return fetch('/admin/api'+p,o).then(function(r){if(r.status===401){T='';sessionStorage.removeItem('tok');show();throw new Error('登入失敗')}return r.json()})}
function show(){$('login').hidden=!!T;$('app').hidden=!T;if(T)load()}
$('login').onsubmit=function(e){e.preventDefault();T=$('tok').value.trim();sessionStorage.setItem('tok',T);$('err').textContent='';show()};
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
function fmt(ms){return new Date(ms).toLocaleString('zh-TW',{timeZone:'Asia/Taipei',hour12:false})}
function act(id,what,ask){return function(){if(ask&&!confirm(ask))return;api('/comments/'+id+'/'+what,{method:'POST'}).then(load).catch(function(e){$('err').textContent=e.message})}}
function load(){api('/comments?status='+S).then(function(d){
 var tabs=$('tabs');tabs.textContent='';[['pending','待審核'],['approved','已公開'],['spam','垃圾']].forEach(function(x){var b=el('button','',x[1]+' '+((d.counts&&d.counts[x[0]])||0));b.setAttribute('aria-pressed',S===x[0]);b.onclick=function(){S=x[0];load()};tabs.appendChild(b)});
 var l=$('list');l.textContent='';if(!d.comments.length)l.appendChild(el('p','','沒有留言。'));
 d.comments.forEach(function(c){var box=el('div','c'),m=el('p','m');m.appendChild(el('b','',c.name));if(c.is_owner)m.appendChild(el('span','owner','作者'));
  m.appendChild(document.createTextNode(' · '+(c.email||'（沒有 Email）')+' · '+fmt(c.created_at)+' · '));var a=el('a','',c.page);a.href='https://mengyahh.com'+c.page;a.target='_blank';a.rel='noopener';m.appendChild(a);
  box.appendChild(m);box.appendChild(el('p','t',c.body));var ac=el('div','a');
  if(c.status!=='approved'){var b1=el('button','ok','核准');b1.onclick=act(c.id,'approve');ac.appendChild(b1)}
  var r=el('button','','回覆（以作者身分）');r.onclick=function(){var ta=box.querySelector('textarea');if(ta){ta.remove();box.querySelector('.send').remove();return}ta=el('textarea');ta.rows=3;box.appendChild(ta);var s=el('button','ok send','送出回覆');s.style.marginTop='8px';s.onclick=function(){if(!ta.value.trim())return;api('/reply',{method:'POST',body:JSON.stringify({page:c.page,parent_id:c.id,body:ta.value})}).then(function(x){if(x.error)throw new Error(x.error);load()}).catch(function(e){$('err').textContent=e.message})};box.appendChild(s)};ac.appendChild(r);
  if(c.status!=='spam'){var b3=el('button','bad','標記垃圾');b3.onclick=act(c.id,'spam');ac.appendChild(b3)}
  if(c.email&&!c.is_owner){var b4=el('button','bad','封鎖此 Email');b4.onclick=act(c.id,'block','封鎖 '+c.email+'？之後這個 Email 的留言都會被當成垃圾。');ac.appendChild(b4)}
  var b2=el('button','bad','刪除');b2.onclick=act(c.id,'delete','確定刪除這則留言（與它底下的回覆）？');ac.appendChild(b2);
  box.appendChild(ac);l.appendChild(box)})}).catch(function(e){$('err').textContent=e.message})}
show();
</script></main></body></html>`;

/* ------------------------------------------------------------------ router */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = corsHeaders(request, env);

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });

    if (url.pathname === '/') {
      // deployment self-check: which settings exist (never their values)
      return json({
        service: 'mengyahh comments',
        db: !!env.DB,
        turnstile_secret: !!env.TURNSTILE_SECRET,
        admin_token: !!env.ADMIN_TOKEN,
        pepper: !!env.PEPPER,
        allowed_origins: (env.ALLOWED_ORIGINS || 'https://mengyahh.com').split(',').map((s) => s.trim()),
      });
    }
    if (!env.DB || !env.PEPPER) return json({ error: '後端尚未設定完成（DB / PEPPER）' }, 500, cors);

    try {
      if (url.pathname === '/admin' && request.method === 'GET') {
        return new Response(ADMIN_HTML, {
          headers: {
            'content-type': 'text/html; charset=utf-8',
            'cache-control': 'no-store',
            'x-robots-tag': 'noindex',
            'content-security-policy': "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
          },
        });
      }
      if (url.pathname.startsWith('/admin/api/')) return await adminApi(request, url, env);
      if (url.pathname === '/comments' && request.method === 'GET') return await listComments(url, env, cors);
      if (url.pathname === '/comments' && request.method === 'POST') {
        if (!env.TURNSTILE_SECRET) return json({ error: '後端尚未設定完成（TURNSTILE_SECRET）' }, 500, cors);
        return await postComment(request, env, cors);
      }
      return json({ error: 'not found' }, 404, cors);
    } catch (e) {
      return json({ error: '伺服器發生錯誤，請稍後再試' }, 500, cors);
    }
  },
};
