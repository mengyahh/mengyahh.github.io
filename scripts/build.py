#!/usr/bin/env python3
"""Render the static pages from data/cooking.json.

    python scripts/build.py

Writes: index.html, cooking/index.html, about/index.html   (stdlib only, no dependencies)
"""
import html
import json
import os
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://mengyahh.com'
GSITE = 'https://sites.google.com/view/mengyahh'   # not-yet-migrated pages still live here
BLOGS = [
    ('(2020-) 閱讀&生存報告', 'https://vocus.cc/salon/65a14b9efd89780001c9e45f/room/ThankYouGrowingPain'),
    ('(2023-) 日常&思想', 'https://vocus.cc/salon/65a14b9efd89780001c9e45f/room/writingforanti-aging'),
    ('(2015-2020) 創作&日常', 'https://mengrr.mystrikingly.com/'),
]
BIO = '思想的巨人，行為的侏儒。努力探尋前進目標，想過上自由的生活。'
EMAIL = 'mengyahh@gmail.com'
INSTAGRAM = 'https://www.instagram.com/mengyahh'
esc = html.escape

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
         '&family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@500;600;700&display=swap">')


def layout(*, base, title, desc, path, body, current, css=(), js=(), og_image=None, extra_head=''):
    """Shared page shell. `base` is the relative prefix back to the site root ('' or '../')."""
    nav = [
        ('關於', f'{GSITE}/about', 'about'),
        ('作品集', f'{GSITE}/portfolio', 'portfolio'),
        ('料理紀錄', f'{base}cooking/', 'cooking'),
        ('部落格', BLOGS[0][1], 'blog'),
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
    blog_links = ''.join(f'<a href="{esc(u)}" rel="noopener">{esc(t)} ↗</a>' for t, u in BLOGS)
    return f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%8C%B1%3C/text%3E%3C/svg%3E">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website">
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
      {blog_links}
    </div>
    <p class="copy">© 萌芽中。 All Rights Reserved.</p>
  </div>
</footer>
{scripts}
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
        alt = f"{e['title']}（照片 {i}/{n}）"
        fit = 'cover' if im['w'] / im['h'] >= 1.2 else 'contain'   # keep portrait shots whole
        slides.append(
            f'<a class="ph slide {fit}" href="../assets/cooking/{im["src"]}" data-group="{esc(e["id"])}" '
            f'data-title="{esc(e["title"])}" data-alt="{esc(alt)}" role="group" '
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
            blocks.append(f'<p>{b["html"]}</p>')
        else:
            blocks.append('<ul>' + ''.join(f'<li>{t}</li>' for t in b['items']) + '</ul>')
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
            f'<small>{len(es)} 則</small></h2>{"".join(render_entry(e) for e in es)}</section>')
    span_first = fmt_date(list(years)[-1]).split('–')[0]
    span_last = fmt_date(list(years)[0])
    body = f'''<div class="wrap">
  <div class="page-head">
    <p class="eyebrow">Cooking Notes</p>
    <h1>料理紀錄</h1>
    <p class="lede">煮過的東西、當時的心得，和照片。共 {len(entries)} 則，從 {span_first} 到 {span_last}。</p>
    <ul class="years" aria-label="依年份跳轉">{chips}</ul>
  </div>
  {"".join(sections)}
</div>'''
    first_img = next((im for e in entries for im in e['images']), None)
    og = f'{SITE}/assets/cooking/{first_img["src"]}' if first_img else None
    return layout(base='../', title='料理紀錄 · 萌芽中。',
                  desc=f'萌芽的料理紀錄：{len(entries)} 則煮過的東西、心得與照片。',
                  path='/cooking/', body=body, current='cooking',
                  css=('cooking',), js=('carousel', 'lightbox'), og_image=og)


def build_home(entries):
    latest = [im for e in entries for im in e['images']][:4]
    thumbs = ''.join(
        f'<img src="assets/cooking/{im["thumb"]}" width="{im["w"]}" height="{im["h"]}" alt="" loading="lazy">'
        for im in latest)
    blog_items = ''.join(f'<li><a href="{esc(u)}" rel="noopener">{esc(t)} ↗</a></li>' for t, u in BLOGS)
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
      <p>煮過的東西、心得與照片（{len(entries)} 則）。</p>
      <div class="thumbs" aria-hidden="true">{thumbs}</div>
    </a>
    <div class="card">
      <h2 class="serif">部落格</h2>
      <ul>{blog_items}</ul>
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


def write(rel, content):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print('wrote', rel, f'({len(content) // 1024} KB)')


if __name__ == '__main__':
    with open(os.path.join(ROOT, 'data', 'cooking.json'), encoding='utf-8') as f:
        entries = json.load(f)['entries']
    write('cooking/index.html', build_cooking(entries))
    write('index.html', build_home(entries))
    write('about/index.html', build_about_stub())
