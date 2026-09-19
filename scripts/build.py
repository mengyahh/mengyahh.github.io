#!/usr/bin/env python3
"""Render the static pages from data/*.json.

    python scripts/build.py

Writes: index.html, cooking/, blog/, about/, sitemap.xml, robots.txt   (stdlib only, no dependencies)

View counts: set GOATCOUNTER below (or the GOATCOUNTER env var) to your GoatCounter site code
(the "xxx" in xxx.goatcounter.com). Leave it empty to build without any tracking.
"""
import html
import json
import os
import re
import shutil
from urllib.parse import quote
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://mengyahh.com'
GSITE = 'https://sites.google.com/view/mengyahh'   # not-yet-migrated pages still live here
BIO = '思想的巨人，行為的侏儒。努力探尋前進目標，想過上自由的生活。'
EMAIL = 'mengyahh@gmail.com'
INSTAGRAM = 'https://www.instagram.com/mengyahh'
GOATCOUNTER = os.environ.get('GOATCOUNTER', 'mengyahh')    # -> https://mengyahh.goatcounter.com (set GOATCOUNTER= to build without tracking)
esc = html.escape

# Comments (Cloudflare Worker in /worker). Both must be set, otherwise pages are built without a comment area.
COMMENTS_API = os.environ.get('COMMENTS_API', '')            # e.g. https://comments.mengyahh.com
TURNSTILE_SITEKEY = os.environ.get('TURNSTILE_SITEKEY', '')  # public site key from Cloudflare Turnstile

# Blog categories. An article can belong to several. The sidebar shows them in these groups, in this order;
# categories with no article are hidden, and any category not listed here is appended to the last group.
CATEGORY_GROUPS = [
    ('類型', ['各種心得', '日常記事', '創作', '階段回顧', '其他']),
    ('主題', ['旅遊記事', '飲食料理', '自然筆記', '日本打工度假']),
]
CATEGORY_ORDER = [c for _, cats in CATEGORY_GROUPS for c in cats]

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
         '&family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@500;600;700&display=swap">')


def resolve(s, base):
    """Turn the importer's @ASSET/ and @BLOG/ placeholders into paths relative to the current page."""
    return s.replace('@ASSET/', f'{base}assets/').replace('@BLOG/', f'{base}blog/')


def layout(*, base, title, desc, path, body, current, css=(), js=(), og_image=None, og_type='website',
           extra_head=''):
    """Shared page shell. `base` is the relative prefix back to the site root ('', '../' or '../../')."""
    nav = [
        ('關於', f'{GSITE}/about', 'about'),
        ('作品集', f'{GSITE}/portfolio', 'portfolio'),
        ('料理紀錄', f'{base}cooking/', 'cooking'),
        ('部落格', f'{base}blog/', 'blog'),
    ]
    items = []
    for label, href, key in nav:
        ext = href.startswith('http')
        cur = ' aria-current="page"' if key == current else ''
        rel = ' rel="noopener"' if ext else ''
        arrow = ' ↗' if ext else ''
        items.append(f'<li><a href="{esc(href)}"{cur}{rel}>{label}{arrow}</a></li>')
    og = f'<meta property="og:image" content="{esc(og_image)}">' if og_image else ''
    styles = ''.join(f'<link rel="stylesheet" href="{base}assets/css/{c}.css">' for c in ('site',) + tuple(css))
    scripts = ''.join(f'<script src="{base}assets/js/{j}.js" defer></script>' for j in js)
    analytics = ''
    stats_note = ''
    if GOATCOUNTER:
        analytics = (f'<script data-goatcounter="https://{GOATCOUNTER}.goatcounter.com/count" '
                     f'async src="//gc.zgo.at/count.js"></script>')
        stats_note = '<p class="copy">本站以 GoatCounter 統計瀏覽次數：不使用 cookie，也不記錄個人資料。</p>'
    return f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%8C%B1%3C/text%3E%3C/svg%3E">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="萌芽中。">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{SITE}{path}">
{og}
{extra_head}
{FONTS}
{styles}
</head>
<body>
<a class="skip" href="#main">跳到主要內容</a>
<header class="topbar">
  <div class="wrap">
    <p class="wordmark"><a href="{base or './'}">萌芽中<span>。</span></a></p>
    <nav aria-label="主選單"><ul class="topnav">{''.join(items)}</ul></nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer>
  <div class="wrap">
    <p class="bio">{esc(BIO)}</p>
    <p>可能想聯絡的時候：<a href="mailto:{EMAIL}">{EMAIL}</a></p>
    <div class="links">
      <a href="{INSTAGRAM}" rel="noopener">Instagram ↗</a>
      <a href="{base}blog/">部落格</a>
    </div>
    <p class="copy">© 萌芽中。 All Rights Reserved.</p>
    {stats_note}
  </div>
</footer>
{scripts}
{analytics}
</body>
</html>
'''


def fmt_date(d):
    if len(d) == 6:
        return f'{d[:4]}.{d[4:]}'
    if len(d) == 4:
        return d
    return d.replace('-', '–')


def year_key(d):
    return d[:4] if len(d) in (4, 6) else d       # "2015-2019" stays its own group


# ------------------------------------------------------------------ cooking

def thumb_width(im):
    """Pixel width of the -t.webp rendition (longest side is capped at 640)."""
    longest = max(im['w'], im['h'])
    return im['w'] if longest <= 640 else round(im['w'] * 640 / longest)


def render_media(e):
    """Photos as a scroll-snap carousel (one photo = a plain frame; controls are added by carousel.js)."""
    imgs = e['images']
    if not imgs:
        return ''
    n = len(imgs)
    slides = []
    for i, im in enumerate(imgs, 1):
        cap = im.get('caption')
        alt = f"{e['title']}：{cap}" if cap else f"{e['title']}（照片 {i}/{n}）"
        fit = 'cover' if im['w'] / im['h'] >= 1.2 else 'contain'   # keep portrait shots whole
        slides.append(
            f'<a class="ph slide {fit}" href="../assets/cooking/{im["src"]}" data-group="{esc(e["id"])}" '
            f'data-title="{esc(cap or e["title"])}" data-alt="{esc(alt)}" role="group" '
            f'aria-roledescription="slide" aria-label="{i} / {n}">'
            f'<img src="../assets/cooking/{im["thumb"]}" '
            f'srcset="../assets/cooking/{im["thumb"]} {thumb_width(im)}w, ../assets/cooking/{im["src"]} {im["w"]}w" '
            f'sizes="(max-width: 820px) 100vw, 420px" width="{im["w"]}" height="{im["h"]}" '
            f'alt="{esc(alt)}" loading="lazy" decoding="async"></a>')
    return (f'<div class="media"><div class="carousel" role="group" aria-roledescription="carousel" '
            f'aria-label="{esc(e["title"])} 的照片"><div class="track">{"".join(slides)}</div></div></div>')


def render_entry(e):
    blocks = []
    for b in e['blocks']:
        if b['type'] == 'p':
            blocks.append(f'<p>{resolve(b["html"], "../")}</p>')
        else:
            blocks.append('<ul>' + ''.join(f'<li>{resolve(t, "../")}</li>' for t in b['items']) + '</ul>')
    place = f'<span class="chip">@{esc(e["place"])}</span>' if e.get('place') else ''
    body = f'<div class="body">{"".join(blocks)}</div>' if blocks else ''
    cls = ' '.join(c for c in ('entry', '' if e['images'] else 'no-media', '' if blocks else 'no-text') if c)
    # text first in the DOM (reading order); CSS puts the photos on the right / above on phones
    return (f'<article class="{cls}" id="{esc(e["id"])}">'
            f'<div class="text"><div class="meta"><time>{fmt_date(e["date"])}</time>{place}</div>'
            f'<h3><a href="#{esc(e["id"])}">{esc(e["title"])}</a></h3>{body}</div>'
            f'{render_media(e)}</article>')


def build_cooking(entries):
    years = OrderedDict()
    for e in entries:
        years.setdefault(year_key(e['date']), []).append(e)
    chips = ''.join(f'<li><a href="#y{esc(y)}">{esc(fmt_date(y))}</a></li>' for y in years)
    sections = []
    for y, es in years.items():
        sections.append(
            f'<section class="year" id="y{esc(y)}"><h2 class="serif">{esc(fmt_date(y))}'
            f'</h2>{"".join(render_entry(e) for e in es)}</section>')
    body = f'''<div class="wrap">
  <div class="page-head">
    <p class="eyebrow">Cooking Notes</p>
    <h1>料理紀錄</h1>
    <p class="lede">煮過的東西、當時的心得，和照片。</p>
    <ul class="years" aria-label="依年份跳轉">{chips}</ul>
  </div>
  {"".join(sections)}
</div>'''
    first_img = next((im for e in entries for im in e['images']), None)
    og = f'{SITE}/assets/cooking/{first_img["src"]}' if first_img else None
    return layout(base='../', title='料理紀錄 · 萌芽中。',
                  desc='萌芽的料理紀錄：煮過的東西、心得與照片。',
                  path='/cooking/', body=body, current='cooking',
                  css=('cooking',), js=('carousel', 'lightbox'), og_image=og)


# ------------------------------------------------------------------ blog

def short(s, n=110):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'


def fmt_full(d):
    return d.replace('-', '.')


def plain_text(h):
    """HTML fragment -> single-line plain text (used for the search index)."""
    t = re.sub(r'</?(p|br|li|h[1-6]|figcaption|blockquote)\b[^>]*>', ' ', h)
    t = re.sub(r'<[^>]+>', '', t)
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


def build_search_index(articles):
    return json.dumps([{'slug': a['slug'], 'title': a['title'], 'cats': a['categories'], 'tags': a.get('tags', []),
                        'abstract': a['abstract'], 'text': plain_text(a['html'])} for a in articles],
                      ensure_ascii=False, separators=(',', ':'))


def sort_cats(cats):
    """An article's categories in sidebar order (unknown ones last)."""
    return sorted(cats, key=lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else len(CATEGORY_ORDER))


def category_groups(articles):
    """[(group title, [categories that have articles])] following CATEGORY_GROUPS."""
    used = {c for a in articles for c in a['categories']}
    groups = [(title, [c for c in cats if c in used]) for title, cats in CATEGORY_GROUPS]
    extra = sorted(used - set(CATEGORY_ORDER))
    if extra and groups:
        groups[-1] = (groups[-1][0], groups[-1][1] + extra)
    return [(t, cs) for t, cs in groups if cs]


def build_blog_index(articles):
    years = OrderedDict()
    for a in articles:
        years.setdefault(a['date'][:4], []).append(a)
    sections = []
    for y, arts in years.items():
        rows = []
        for a in arts:
            cover = ''
            if a.get('cover'):
                c = a['cover']
                cover = (f'<div class="row-cover"><img src="../assets/{c["src"]}" width="{c["w"]}" height="{c["h"]}" '
                         f'alt="" loading="lazy" decoding="async"></div>')
            cats_sorted = sort_cats(a['categories'])
            chips = ''.join(f'<span class="chip">{esc(c)}</span>' for c in cats_sorted)
            rows.append(
                f'<li class="post-row" data-slug="{a["slug"]}" data-cats="{esc("|".join(cats_sorted))}"><a href="{a["slug"]}/">'
                f'<div class="row-text"><p class="row-meta"><time datetime="{a["date"]}">{fmt_full(a["date"])}</time>'
                f'{chips}</p>'
                f'<h3>{esc(a["title"])}</h3><p class="row-abs">{esc(short(a["abstract"], 120))}</p></div>{cover}</a></li>')
        sections.append(f'<section class="year" id="y{y}" data-year="{y}"><h2 class="serif">{y}</h2>'
                        f'<ul class="post-list">{"".join(rows)}</ul></section>')
    cat_widgets = ''.join(
        f'<section class="widget js-only" hidden><h2>{esc(title)}</h2><ul class="side-list cat-list">'
        + ''.join(f'<li><button type="button" class="side-btn" data-cat="{esc(cname)}" aria-pressed="false">{esc(cname)}</button></li>'
                  for cname in names)
        + '</ul></section>'
        for title, names in category_groups(articles))
    year_chips = ''.join(f'<li><a href="#y{y}" data-year="{y}" aria-pressed="false">{y}</a></li>' for y in years)
    recent = ''.join(f'<li><a href="{a["slug"]}/">{esc(a["title"])}</a></li>' for a in articles[:5])
    recent_comments = (f'<section class="widget rc-widget" data-api="{esc(COMMENTS_API)}" hidden><h2>近期留言</h2>'
                       f'<ul class="recent rc-list"></ul></section>') if COMMENTS_API else ''
    body = f"""<div class="wrap">
  <div class="page-head">
    <p class="eyebrow">Blog</p>
    <h1>部落格</h1>
    <p class="lede">心得、日常記事與創作。</p>
    <div class="year-row">
      <ul class="year-chips" aria-label="依年份篩選">{year_chips}</ul>
      <button type="button" class="clear" hidden>清除篩選</button>
    </div>
  </div>
  <div class="blog-layout">
    <div class="blog-main">
      {"".join(sections)}
      <p class="no-result" hidden>找不到符合的文章，換個關鍵字或清除篩選試試。</p>
    </div>
    <aside class="side" aria-label="找文章">
      <div class="side-find">
        <section class="widget js-only" hidden>
          <form class="search" role="search" data-index="../assets/data/blog-search.json">
            <label class="sr" for="q">搜尋文章</label>
            <input id="q" type="search" name="q" placeholder="搜尋標題與內文" autocomplete="off">
          </form>
        </section>
        {cat_widgets}
      </div>
      <div class="side-more">
        <section class="widget">
          <h2>近期文章</h2>
          <ul class="recent">{recent}</ul>
        </section>
        {recent_comments}
      </div>
    </aside>
  </div>
</div>"""
    first = next((a['cover'] for a in articles if a.get('cover')), None)
    return layout(base='../', title='部落格 · 萌芽中。',
                  desc='萌芽的部落格：心得、日常記事與創作。',
                  path='/blog/', body=body, current='blog', css=('cooking', 'blog'),
                  js=('blog-filter',) + (('recent-comments',) if COMMENTS_API else ()),
                  og_image=f'{SITE}/assets/{first["src"]}' if first else None)


def comments_section(a):
    if not (COMMENTS_API and TURNSTILE_SITEKEY):
        return ''
    return f'''<section class="comments narrow" id="comments" data-api="{esc(COMMENTS_API)}" data-page="/blog/{a["slug"]}/" data-sitekey="{esc(TURNSTILE_SITEKEY)}">
  <h2 class="serif">留言</h2>
  <p class="c-note">電子郵件不會公開，只用來辨識留言者。第一次留言會先經過審核，之後同一個電子郵件的留言會直接顯示。本留言區以 Cloudflare Turnstile 防止垃圾留言。</p>
  <div class="c-formwrap">
    <form class="c-form" novalidate hidden>
      <p class="c-replying" hidden></p>
      <div class="c-row">
        <label>名稱<input type="text" name="name" maxlength="40" autocomplete="nickname" placeholder="匿名訪客"></label>
        <label>電子郵件<input type="email" name="email" maxlength="254" autocomplete="email" placeholder="選填，不會公開"></label>
      </div>
      <label><span>留言 <span class="req" aria-hidden="true">*</span></span><textarea name="body" required maxlength="2000" rows="5"></textarea></label>
      <input class="c-hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
      <div class="c-turnstile"></div>
      <label class="c-remember"><input type="checkbox" name="remember"> 在這個瀏覽器記住我的名稱和電子郵件，下次留言時使用</label>
      <div class="c-actions"><button type="submit">發佈留言</button><button type="button" class="c-cancel" hidden>取消回覆</button></div>
    </form>
  </div>
  <p class="c-msg" role="status" aria-live="polite"></p>
  <div class="c-list" aria-live="polite"></div>
  <noscript><p class="c-note">留言功能需要開啟 JavaScript。</p></noscript>
</section>'''


def build_post(a, newer, older):
    path = f'/blog/{a["slug"]}/'
    tags = (''.join(f'<a class="chip" href="../?cat={quote(c)}">{esc(c)}</a>' for c in sort_cats(a['categories']))
            + ''.join(f'<span class="chip">{esc(t)}</span>' for t in a.get('tags', [])))
    views = (f'<span class="views" data-code="{esc(GOATCOUNTER)}" hidden></span>' if GOATCOUNTER else '')
    meta = f'<time datetime="{a["date"]}">{fmt_full(a["date"])}</time>{views}'

    def nav(art, label, cls):
        if not art:
            return f'<span class="pn {cls} empty"></span>'
        return (f'<a class="pn {cls}" href="../{art["slug"]}/"><small>{label}</small>'
                f'<span class="serif">{esc(art["title"])}</span></a>')

    body = f'''<article class="post">
  <header class="post-head narrow">
    <p class="eyebrow"><a href="../">部落格</a></p>
    <h1>{esc(a["title"])}</h1>
    <p class="post-meta">{meta}</p>
    {f'<div class="tags">{tags}</div>' if tags else ''}
  </header>
  <div class="prose narrow">{resolve(a["html"], "../../")}</div>
  <nav class="post-nav narrow" aria-label="上一篇與下一篇">{nav(newer, "較新的文章 →", "newer")}{nav(older, "← 較舊的文章", "older")}</nav>
  {comments_section(a)}
</article>'''
    c = a.get('cover')
    return layout(base='../../', title=f'{a["title"]} · 萌芽中。', desc=short(a['abstract'], 120), path=path,
                  body=body, current='blog', css=('blog',),
                  js=(('views',) if GOATCOUNTER else ()) + (('comments',) if COMMENTS_API and TURNSTILE_SITEKEY else ()),
                  og_image=f'{SITE}/assets/{c["src"]}' if c else None, og_type='article',
                  extra_head=f'<meta property="article:published_time" content="{a["date"]}">')


# ------------------------------------------------------------------ home / misc

def build_home(entries, articles):
    latest = [im for e in entries for im in e['images']][:4]
    thumbs = ''.join(
        f'<img src="assets/cooking/{im["thumb"]}" width="{im["w"]}" height="{im["h"]}" alt="" loading="lazy">'
        for im in latest)
    posts = ''.join(f'<li><a href="blog/{a["slug"]}/"><time>{fmt_full(a["date"])}</time>{esc(a["title"])}</a></li>'
                    for a in articles[:4])
    lede = ''.join(f'<span>{esc(s)}。</span>' for s in BIO.split('。') if s)
    body = f'''<div class="wrap">
  <div class="home-hero">
    <p class="eyebrow">mengyahh.com</p>
    <h1 class="serif">萌芽中<span>。</span></h1>
    <p class="lede">{lede}</p>
  </div>
  <div class="cards">
    <a class="card card-cooking" href="cooking/">
      <h2 class="serif">料理紀錄</h2>
      <p>煮過的東西、心得與照片。</p>
      <div class="thumbs" aria-hidden="true">{thumbs}</div>
    </a>
    <div class="card card-blog">
      <h2 class="serif"><a href="blog/">部落格</a></h2>
      <ul class="latest">{posts}</ul>
      <p class="more"><a href="blog/">所有文章 →</a></p>
    </div>
    <a class="card" href="{GSITE}/about" rel="noopener">
      <h2 class="serif">關於 ↗</h2>
      <p>自我介紹與經歷。</p>
    </a>
    <a class="card" href="{GSITE}/portfolio" rel="noopener">
      <h2 class="serif">作品集 ↗</h2>
      <p>過往的接案與作品。</p>
    </a>
    <a class="card" href="https://understory.mengyahh.com" rel="noopener">
      <h2 class="serif">Understory ↗</h2>
      <p>作品與接案品牌：給自由工作者的生活工作管理大師、白肉雞飼養紀錄。</p>
    </a>
  </div>
</div>'''
    return layout(base='', title='萌芽中。 · mengyahh', desc=BIO, path='/', body=body, current=None,
                  css=('home',))


def build_about_stub():
    target = f'{GSITE}/about'
    head = (f'<meta http-equiv="refresh" content="0; url={target}">'
            '<meta name="robots" content="noindex">')
    body = (f'<div class="wrap"><div class="page-head"><h1>關於</h1>'
            f'<p class="lede">正在前往關於頁⋯⋯如果沒有自動跳轉，請點 <a href="{target}">這裡</a>。</p></div></div>')
    return layout(base='../', title='關於 · 萌芽中。', desc='關於萌芽', path='/about/', body=body,
                  current='about', css=('cooking',), extra_head=head)


def build_sitemap(articles):
    urls = [('/', None), ('/cooking/', None), ('/blog/', articles[0]['date'] if articles else None)]
    urls += [(f'/blog/{a["slug"]}/', a['date']) for a in articles]
    rows = ''.join(f'<url><loc>{SITE}{p}</loc>' + (f'<lastmod>{d}</lastmod>' if d else '') + '</url>' for p, d in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}</urlset>\n')


def write(rel, content, quiet=False):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    if not quiet:
        print('wrote', rel, f'({len(content) // 1024} KB)')


def load(name, key):
    with open(os.path.join(ROOT, 'data', name), encoding='utf-8') as f:
        return json.load(f)[key]


if __name__ == '__main__':
    entries = load('cooking.json', 'entries')
    articles = sorted(load('blog.json', 'articles'), key=lambda a: a['date'], reverse=True)

    shutil.rmtree(os.path.join(ROOT, 'blog'), ignore_errors=True)      # drop pages of removed articles
    write('cooking/index.html', build_cooking(entries))
    write('blog/index.html', build_blog_index(articles))
    for i, a in enumerate(articles):
        newer = articles[i - 1] if i > 0 else None
        older = articles[i + 1] if i + 1 < len(articles) else None
        write(f'blog/{a["slug"]}/index.html', build_post(a, newer, older), quiet=True)
    print('wrote blog/<slug>/index.html x', len(articles))
    write('index.html', build_home(entries, articles))
    write('about/index.html', build_about_stub())
    write('assets/data/blog-search.json', build_search_index(articles))
    write('sitemap.xml', build_sitemap(articles))
    write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')
    print('comments:', COMMENTS_API if COMMENTS_API and TURNSTILE_SITEKEY else 'off (COMMENTS_API / TURNSTILE_SITEKEY not set)')
    print('view counts:', f'GoatCounter "{GOATCOUNTER}"' if GOATCOUNTER else 'off (GOATCOUNTER not set)')
