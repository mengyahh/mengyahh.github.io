#!/usr/bin/env python3
"""Render the static pages from data/*.json and content/**/*.md.

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

import mdcontent

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://mengyahh.com'
SITE_DESC = '萌芽的個人網站：料理紀錄、部落格文章與工作。'      # home page <meta description>
EMAIL = 'mengyahh@gmail.com'
INSTAGRAM = 'https://www.instagram.com/mengyahh'
WORK_URL = 'https://understory.mengyahh.com'      # the Understory site
GOATCOUNTER = os.environ.get('GOATCOUNTER', 'mengyahh')    # -> https://mengyahh.goatcounter.com (set GOATCOUNTER= to build without tracking)
esc = html.escape
AUTHOR = '萌芽'
DEFAULT_OG = 'assets/img/banner.webp'        # share image for pages that have no photo of their own

# Comments (Cloudflare Worker in /worker). Both must be set, otherwise pages are built without a comment area.
COMMENTS_API = os.environ.get('COMMENTS_API', 'https://comments.mengyahh.com')   # set COMMENTS_API= (empty) to build without comments
TURNSTILE_SITEKEY = os.environ.get('TURNSTILE_SITEKEY', '0x4AAAAAAE88bRoZ3yGytjgC')  # public site key from Cloudflare Turnstile (safe to publish)

# Blog categories. An article can belong to several. The sidebar shows them in these groups, in this order;
# categories with no article are hidden, and any category not listed here is appended to the last group.
CATEGORY_GROUPS = [
    ('類型', ['各種心得', '日常記事', '創作', '階段回顧', '其他']),
    ('主題', ['旅遊記事', '飲食料理', '自然筆記', '日本打工度假']),
]
CATEGORY_ORDER = [c for _, cats in CATEGORY_GROUPS for c in cats]

LANGS = ['zh', 'en', 'ja']
LANG, UP, OUT = 'zh', '', ''          # current language; UP = "../" prefix from a language folder back to the site root; OUT = output folder
HTML_LANG = {'zh': 'zh-Hant', 'en': 'en', 'ja': 'ja'}
LOCALE = {'zh': 'zh_TW', 'en': 'en_US', 'ja': 'ja_JP'}
LANG_NAME = {'zh': '中文', 'en': 'EN', 'ja': '日本語'}
AUTHORS = {'zh': '萌芽', 'en': 'Meng Ya', 'ja': 'Meng Ya'}

CATEGORY_LABELS = {
    'en': {'各種心得': 'Thoughts', '日常記事': 'Daily life', '創作': 'Creative writing', '階段回顧': 'Looking back', '其他': 'Other',
           '旅遊記事': 'Travel', '飲食料理': 'Food & cooking', '自然筆記': 'Nature notes', '日本打工度假': 'Working holiday in Japan',
           '類型': 'Type', '主題': 'Topic'},
    'ja': {'各種心得': '思ったこと', '日常記事': '日常', '創作': '創作', '階段回顧': 'ふりかえり', '其他': 'その他',
           '旅遊記事': '旅', '飲食料理': '食べもの・料理', '自然筆記': '自然ノート', '日本打工度假': 'ワーキングホリデー',
           '類型': 'タイプ', '主題': 'テーマ'},
}

STRINGS = {
    'zh': dict(
        site='萌芽中。', wm='萌芽中', dot='。', skip='跳到主要內容', main_nav='主選單',
        nav_about='關於', nav_work='工作', nav_cooking='料理紀錄', nav_blog='部落格',
        foot_contact='可能想聯絡的時候：', copy='© 萌芽中。 All Rights Reserved.',
        stats='本站以 GoatCounter 統計瀏覽次數：不使用 cookie，也不記錄個人資料。',
        photo_n='{title}（照片 {i}/{n}）', photo_cap='{title}：{cap}', carousel='{title} 的照片',
        cooking_h1='料理紀錄', cooking_lede='煮過的東西、當時的心得，和照片。', cooking_desc='萌芽的料理紀錄：煮過的東西、心得與照片。',
        years_aria='依年份跳轉', cooking_note='',
        blog_h1='部落格', blog_lede='心得、日常記事與創作。', blog_desc='萌芽的部落格：心得、日常記事與創作。', blog_note='',
        year_aria='依年份篩選', clear='清除篩選', none='找不到符合的文章，換個關鍵字或清除篩選試試。', more='顯示更多文章',
        side_aria='找文章', search_label='搜尋文章', search_ph='搜尋標題與內文', recent='近期文章', recent_comments='近期留言',
        kw='關鍵字', post_nav='上一篇與下一篇', newer='較新的文章 →', older='← 較舊的文章', views='瀏覽 {n} 次',
        home_title='萌芽中。 · mengyahh', home_desc='萌芽的個人網站：料理紀錄、部落格文章與工作。',
        home_all_posts='所有文章 →', home_all='全部 →', home_cooking_desc='煮過的東西、心得與照片。',
        home_more='看更多 →', home_about_desc='自我介紹與經歷。', home_go='前往 Understory ↗', home_work_desc='Understory：作品與接案品牌。',
        about_h1='關於', about_title='關於',
        about_desc='萌芽（Meng Ya）的自我介紹：接案 5 年的非典型自由工作者，擅長拆解問題與研究分析，提供從分析、規劃到製作的服務。',
        profile_alt='萌芽的照片'),
    'en': dict(
        site='Sprouting.', wm='Sprouting', dot='.', skip='Skip to main content', main_nav='Main menu',
        nav_about='About', nav_work='Work', nav_cooking='Cooking Notes', nav_blog='Blog',
        foot_contact='If you feel like getting in touch: ', copy='© 萌芽中。 All Rights Reserved.',
        stats='Page views are counted with GoatCounter: no cookies, no personal data.',
        photo_n='{title} (photo {i}/{n})', photo_cap='{title}: {cap}', carousel='Photos of {title}',
        cooking_h1='Cooking Notes', cooking_lede='What I cooked, what I thought at the time, and photos.',
        cooking_desc="Meng Ya's cooking notes: what I've cooked, thoughts and photos.",
        years_aria='Jump to a year',
        cooking_note='Only the newest entries are translated so far. <a href="/cooking/">All entries (in Chinese) →</a>',
        blog_h1='Blog', blog_lede='Thoughts, daily life and creative writing.', blog_desc="Meng Ya's blog: thoughts, daily life and creative writing.",
        blog_note='Only the newest posts are translated so far. <a href="/blog/">All posts (in Chinese) →</a>',
        year_aria='Filter by year', clear='Clear filters', none='No matching posts. Try another keyword or clear the filters.',
        more='Show more posts', side_aria='Find posts', search_label='Search posts', search_ph='Search titles and text',
        recent='Recent posts', recent_comments='',
        kw='Keywords', post_nav='Previous and next posts', newer='Newer post →', older='← Older post', views='{n} views',
        home_title='Sprouting. · mengyahh', home_desc="Meng Ya's personal site: cooking notes, blog posts and work.",
        home_all_posts='All posts →', home_all='All →', home_cooking_desc="What I've cooked, thoughts and photos.",
        home_more='Read more →', home_about_desc='Who I am and what I have done.', home_go='Go to Understory ↗',
        home_work_desc='Understory: my portfolio and freelance brand.',
        about_h1='About', about_title='About',
        about_desc='About Meng Ya: a freelancer of five years with an unconventional career, good at breaking problems down and researching, offering everything from analysis and planning to making.',
        profile_alt='Photo of Meng Ya'),
    'ja': dict(
        site='芽吹き中。', wm='芽吹き中', dot='。', skip='本文へスキップ', main_nav='メインメニュー',
        nav_about='プロフィール', nav_work='仕事', nav_cooking='料理記録', nav_blog='ブログ',
        foot_contact='連絡したくなったら：', copy='© 萌芽中。 All Rights Reserved.',
        stats='ページの閲覧数は GoatCounter で数えています。Cookie は使わず、個人情報も記録しません。',
        photo_n='{title}（写真 {i}/{n}）', photo_cap='{title}：{cap}', carousel='{title}の写真',
        cooking_h1='料理記録', cooking_lede='作ったもの、そのときの感想、写真。', cooking_desc='Meng Ya の料理記録：作ったもの、感想、写真。',
        years_aria='年へ移動',
        cooking_note='翻訳しているのは新しい記録だけです。<a href="/cooking/">すべての記録（中国語）→</a>',
        blog_h1='ブログ', blog_lede='思ったこと、日々のこと、創作。', blog_desc='Meng Ya のブログ：思ったこと、日々のこと、創作。',
        blog_note='翻訳しているのは新しい記事だけです。<a href="/blog/">すべての記事（中国語）→</a>',
        year_aria='年で絞り込む', clear='絞り込みを解除', none='該当する記事がありません。キーワードを変えるか、絞り込みを解除してみてください。',
        more='記事をもっと見る', side_aria='記事を探す', search_label='記事を検索', search_ph='タイトルと本文を検索',
        recent='最近の記事', recent_comments='',
        kw='キーワード', post_nav='前後の記事', newer='新しい記事 →', older='← 古い記事', views='{n} 回閲覧',
        home_title='芽吹き中。 · mengyahh', home_desc='Meng Ya の個人サイト：料理記録、ブログ、仕事のこと。',
        home_all_posts='すべての記事 →', home_all='すべて →', home_cooking_desc='作ったもの、感想、写真。',
        home_more='もっと見る →', home_about_desc='自己紹介と、これまでのこと。', home_go='Understory へ ↗',
        home_work_desc='Understory：作品と受託のブランド。',
        about_h1='プロフィール', about_title='プロフィール',
        about_desc='Meng Ya の自己紹介。フリーランス歴5年、問題を分解して調べて分析するのが得意で、分析・企画から制作までまるごと引き受けています。',
        profile_alt='Meng Ya の写真'),
}
S = STRINGS['zh']


def set_lang(lang):
    global LANG, UP, OUT, S
    LANG, S = lang, STRINGS[lang]
    UP = '' if lang == 'zh' else '../'
    OUT = '' if lang == 'zh' else lang + '/'
    mdcontent.set_lang(lang)


def cat_label(c):
    return CATEGORY_LABELS.get(LANG, {}).get(c, c)


def comments_on():
    return LANG == 'zh' and bool(COMMENTS_API and TURNSTILE_SITEKEY)


def prefix(lang):
    return '' if lang == 'zh' else f'/{lang}'


FONTS_JA = ('&family=Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@500;600;700')


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
         '&family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@500;600;700&display=swap">')


def resolve(s, base):
    """Turn the importer's @ASSET/, @BLOG/ and @SITE/ placeholders into paths relative to the current page."""
    return s.replace('@ASSET/', f'{base}{UP}assets/').replace('@BLOG/', f'{base}blog/').replace('@SITE/', base)


def jsonld(*objs):
    """<script type="application/ld+json"> blocks (structured data for search engines)."""
    return ''.join('<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>'
                   for o in objs)


def layout(*, base, title, desc, path, body, current, css=(), js=(), og_image=None, og_type='website',
           extra_head='', structured=(), alts=None):
    """Shared page shell. `base` is the relative prefix back to the site root ('', '../' or '../../')."""
    nav = [
        (S['nav_about'], f'{base}about/', 'about'),
        (S['nav_work'], WORK_URL, 'work'),                        # goes straight to the Understory site
        (S['nav_cooking'], f'{base}cooking/', 'cooking'),
        (S['nav_blog'], f'{base}blog/', 'blog'),
    ]
    items = []
    for label, href, key in nav:
        ext = href.startswith('http')
        cur = ' aria-current="page"' if key == current else ''
        rel = ' rel="noopener"' if ext else ''
        items.append(f'<li><a href="{esc(href)}"{cur}{rel}>{label}{" ↗" if ext else ""}</a></li>')
    alts = [l for l in (alts or LANGS)]
    if len(alts) > 1:
        items.append('<li class="langs" aria-label="Language">' + ' · '.join(
            f'<a href="{prefix(l)}{path}" hreflang="{HTML_LANG[l]}" lang="{HTML_LANG[l]}"' + (' aria-current="true"' if l == LANG else '') + f'>{LANG_NAME[l]}</a>'
            for l in alts) + '</li>')
    hreflang = ''.join(f'<link rel="alternate" hreflang="{HTML_LANG[l]}" href="{SITE}{prefix(l)}{path}">' for l in alts) if len(alts) > 1 else ''
    if hreflang:
        hreflang += f'<link rel="alternate" hreflang="x-default" href="{SITE}{path}">'
    og_image = og_image or f'{SITE}/{DEFAULT_OG}'
    og = (f'<meta property="og:image" content="{esc(og_image)}">'
          f'<meta property="og:locale" content="{LOCALE[LANG]}">'
          f'<meta name="twitter:card" content="summary_large_image">'
          f'<meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">'
          f'<meta name="twitter:image" content="{esc(og_image)}">')
    og += jsonld(*structured)
    styles = ''.join(f'<link rel="stylesheet" href="{base}{UP}assets/css/{c}.css">' for c in ('site',) + tuple(css))
    scripts = ''.join(f'<script src="{base}{UP}assets/js/{j}.js" defer></script>' for j in tuple(js))
    fonts = FONTS.replace('&display=swap', FONTS_JA + '&display=swap') if LANG == 'ja' else FONTS
    analytics = ''
    stats_note = ''
    if GOATCOUNTER:
        analytics = (f'<script data-goatcounter="https://{GOATCOUNTER}.goatcounter.com/count" '
                     f'async src="//gc.zgo.at/count.js"></script>')
        stats_note = f'<p class="copy">{S["stats"]}</p>'
    return f'''<!DOCTYPE html>
<html lang="{HTML_LANG[LANG]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%8C%B1%3C/text%3E%3C/svg%3E">
<link rel="canonical" href="{SITE}{prefix(LANG)}{path}">{hreflang}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{S['site']}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{SITE}{prefix(LANG)}{path}">
{og}
{extra_head}
{fonts}
{styles}
</head>
<body>
<a class="skip" href="#main">{S['skip']}</a>
<header class="topbar">
  <div class="wrap">
    <p class="wordmark"><a href="{base or './'}">{S['wm']}<span>{S['dot']}</span></a></p>
    <nav aria-label="{S['main_nav']}"><ul class="topnav">{''.join(items)}</ul></nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer>
  <div class="wrap">
    <p>{S['foot_contact']}<a href="mailto:{EMAIL}">{EMAIL}</a></p>
    <div class="links">
      <a href="{INSTAGRAM}" rel="noopener">Instagram ↗</a>
      <a href="{base}blog/">{S['nav_blog']}</a>
    </div>
    <p class="copy">{S['copy']}</p>
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
        alt = S['photo_cap'].format(title=e['title'], cap=cap) if cap else S['photo_n'].format(title=e['title'], i=i, n=n)
        fit = 'cover' if im['w'] / im['h'] >= 1.2 else 'contain'   # keep portrait shots whole
        slides.append(
            f'<a class="ph slide {fit}" href="{UP}../assets/cooking/{im["src"]}" data-group="{esc(e["id"])}" '
            f'data-title="{esc(cap or e["title"])}" data-alt="{esc(alt)}" role="group" '
            f'aria-roledescription="slide" aria-label="{i} / {n}">'
            f'<img src="{UP}../assets/cooking/{im["thumb"]}" '
            f'srcset="{UP}../assets/cooking/{im["thumb"]} {thumb_width(im)}w, {UP}../assets/cooking/{im["src"]} {im["w"]}w" '
            f'sizes="(max-width: 820px) 100vw, 420px" width="{im["w"]}" height="{im["h"]}" '
            f'alt="{esc(alt)}" loading="lazy" decoding="async"></a>')
    return (f'<div class="media"><div class="carousel" role="group" aria-roledescription="carousel" '
            f'aria-label="{esc(S["carousel"].format(title=e["title"]))}"><div class="track">{"".join(slides)}</div></div></div>')


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
    <h1>{S['cooking_h1']}</h1>
    <p class="lede">{S['cooking_lede']}</p>{note_html(S['cooking_note'])}
    <ul class="years" aria-label="{S['years_aria']}">{chips}</ul>
  </div>
  {"".join(sections)}
</div>'''
    first_img = next((im for e in entries for im in e['images']), None)
    og = f'{SITE}/assets/cooking/{first_img["src"]}' if first_img else None
    return layout(base='../', title=f'{S["cooking_h1"]} · {S["site"]}',
                  desc=S['cooking_desc'],
                  path='/cooking/', body=body, current='cooking',
                  css=('cooking', 'lightbox'), js=('carousel', 'lightbox'), og_image=og, alts=AVAILABLE)


# ------------------------------------------------------------------ blog

def note_html(t):
    return f'\n    <p class="lede">{t}</p>' if t else ''


def search_file():
    return 'blog-search.json' if LANG == 'zh' else f'blog-search-{LANG}.json'


def short(s, n=110):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'


def fmt_full(d):
    return d.replace('-', '.')


def date_disp(a):
    """Shown date; month-only sources (Instagram) carry a date_label such as "2025.11" next to their address date."""
    return a.get('date_label') or fmt_full(a['date'])


def plain_text(h):
    """HTML fragment -> single-line plain text (used for the search index)."""
    t = re.sub(r'</?(p|br|li|h[1-6]|figcaption|blockquote)\b[^>]*>', ' ', h)
    t = re.sub(r'<[^>]+>', '', t)
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


def build_search_index(articles):
    return json.dumps([{'slug': a['slug'], 'title': a['title'], 'cats': [cat_label(c) for c in a['categories']],
                        'tags': a.get('tags', []) + a.get('keywords', []) + a.get('kwlines', []),
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
                c = a.get('cover_thumb') or a['cover']
                cover = (f'<div class="row-cover"><img src="{UP}../assets/{c["src"]}" width="{c["w"]}" height="{c["h"]}" '
                         f'alt="" loading="lazy" decoding="async"></div>')
            cats_sorted = sort_cats(a['categories'])
            chips = ''.join(f'<span class="chip">{esc(cat_label(c))}</span>' for c in cats_sorted)
            rows.append(
                f'<li class="post-row" data-slug="{a["slug"]}" data-cats="{esc("|".join(cats_sorted))}"><a href="{a["slug"]}/">'
                f'<div class="row-text"><p class="row-meta"><time datetime="{a["date"]}">{date_disp(a)}</time>'
                f'{chips}</p>'
                f'<h3>{esc(a["title"])}</h3><p class="row-abs">{esc(short(a["abstract"], 120))}</p></div>{cover}</a></li>')
        sections.append(f'<section class="year" id="y{y}" data-year="{y}"><h2 class="serif">{y}</h2>'
                        f'<ul class="post-list">{"".join(rows)}</ul></section>')
    cat_widgets = ''.join(
        f'<section class="widget js-only" hidden><h2>{esc(cat_label(title))}</h2><ul class="side-list cat-list">'
        + ''.join(f'<li><button type="button" class="side-btn" data-cat="{esc(cname)}" aria-pressed="false">{esc(cat_label(cname))}</button></li>'
                  for cname in names)
        + '</ul></section>'
        for title, names in category_groups(articles))
    year_chips = ''.join(f'<li><a href="#y{y}" data-year="{y}" aria-pressed="false">{y}</a></li>' for y in years)
    recent = ''.join(f'<li><a href="{a["slug"]}/">{esc(a["title"])}</a></li>' for a in articles[:5])
    recent_comments = (f'<section class="widget rc-widget" data-api="{esc(COMMENTS_API)}" hidden><h2>{S["recent_comments"]}</h2>'
                       f'<ul class="recent rc-list"></ul></section>') if COMMENTS_API and LANG == 'zh' else ''
    body = f"""<div class="wrap">
  <div class="page-head">
    <p class="eyebrow">Blog</p>
    <h1>{S['blog_h1']}</h1>
    <p class="lede">{S['blog_lede']}</p>{note_html(S['blog_note'])}
    <div class="year-row">
      <ul class="year-chips" aria-label="{S['year_aria']}">{year_chips}</ul>
      <button type="button" class="clear" hidden>{S['clear']}</button>
    </div>
  </div>
  <div class="blog-layout">
    <div class="blog-main">
      {"".join(sections)}
      <p class="no-result" hidden>{S['none']}</p>
      <div class="load-more" hidden><button type="button" class="btn ghost">{S['more']}</button></div>
    </div>
    <aside class="side" aria-label="{S['side_aria']}">
      <div class="side-find">
        <section class="widget js-only" hidden>
          <form class="search" role="search" data-index="{UP}../assets/data/{search_file()}">
            <label class="sr" for="q">{S['search_label']}</label>
            <input id="q" type="search" name="q" placeholder="{S['search_ph']}" autocomplete="off">
          </form>
        </section>
        {cat_widgets}
      </div>
      <div class="side-more">
        <section class="widget">
          <h2>{S['recent']}</h2>
          <ul class="recent">{recent}</ul>
        </section>
        {recent_comments}
      </div>
    </aside>
  </div>
</div>"""
    first = next((a['cover'] for a in articles if a.get('cover')), None)
    return layout(base='../', title=f'{S["blog_h1"]} · {S["site"]}',
                  desc=S['blog_desc'],
                  path='/blog/', body=body, current='blog', css=('cooking', 'blog'),
                  js=('blog-filter',) + (('recent-comments',) if COMMENTS_API and LANG == 'zh' else ()),
                  og_image=f'{SITE}/assets/{first["src"]}' if first else None, alts=AVAILABLE)


def comments_section(a):
    if not comments_on():
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


def keywords_html(a):
    kws = a.get('keywords')
    if not kws:
        return ''
    return f'<p class="post-kw narrow"><span>{S["kw"]}</span>{"".join(f"<em>{esc(k)}</em>" for k in kws)}</p>'


def build_post(a, newer, older, alts=None):
    path = f'/blog/{a["slug"]}/'
    tags = (''.join(f'<a class="chip" href="../?cat={quote(c)}">{esc(cat_label(c))}</a>' for c in sort_cats(a['categories']))
            + ''.join(f'<span class="chip">{esc(t)}</span>' for t in a.get('tags', [])))
    views = (f'<span class="views" data-code="{esc(GOATCOUNTER)}" data-tpl="{esc(S["views"])}" hidden></span>' if GOATCOUNTER else '')
    meta = f'<time datetime="{a["date"]}">{date_disp(a)}</time>{views}'

    def nav(art, label, cls):
        if not art:
            return f'<span class="pn {cls} empty"></span>'
        return (f'<a class="pn {cls}" href="../{art["slug"]}/"><small>{label}</small>'
                f'<span class="serif">{esc(art["title"])}</span></a>')

    c = a.get('cover')
    cover_html = (f'<figure class="post-cover narrow"><img src="{UP}../../assets/{c["src"]}" width="{c["w"]}" height="{c["h"]}" alt="" decoding="async"></figure>'
                  if c and not a.get('cover_is_first_image') else '')
    body = f'''<article class="post">
  <header class="post-head narrow">
    <p class="eyebrow"><a href="../">{S['blog_h1']}</a></p>
    <h1>{esc(a["title"])}</h1>
    <p class="post-meta">{meta}</p>
    {f'<div class="tags">{tags}</div>' if tags else ''}
  </header>
  {cover_html}
  <div class="prose narrow">{resolve(a["html"], "../../")}</div>{keywords_html(a)}
  <nav class="post-nav narrow" aria-label="{S['post_nav']}">{nav(newer, S["newer"], "newer")}{nav(older, S["older"], "older")}</nav>
  {comments_section(a)}
</article>'''
    c = a.get('cover')
    url = f'{SITE}{prefix(LANG)}{path}'
    posting = {'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': a['title'], 'description': short(a['abstract'], 160),
               'datePublished': a['date'], 'dateModified': a['date'], 'inLanguage': HTML_LANG[LANG], 'url': url,
               'mainEntityOfPage': {'@type': 'WebPage', '@id': url},
               'author': {'@type': 'Person', 'name': AUTHORS[LANG], 'url': SITE + prefix(LANG) + '/'},
               'publisher': {'@type': 'Organization', 'name': S['site'], 'url': SITE + prefix(LANG) + '/'}}
    if c:
        posting['image'] = f'{SITE}/assets/{c["src"]}'
    kws = a.get('keywords') or a.get('tags')
    if kws:
        posting['keywords'] = ', '.join(kws)
    crumbs = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': S['site'], 'item': SITE + prefix(LANG) + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': S['blog_h1'], 'item': SITE + prefix(LANG) + '/blog/'},
        {'@type': 'ListItem', 'position': 3, 'name': a['title'], 'item': url}]}
    return layout(base='../../', title=f'{a["title"]} · {S["site"]}', desc=short(a['abstract'], 120), path=path, alts=alts,
                  body=body, current='blog', css=('blog',) + (('lightbox',) if 'class="gallery"' in a['html'] else ()),
                  js=(('lightbox',) if 'class="gallery"' in a['html'] else ()) + (('views',) if GOATCOUNTER else ()) + (('comments',) if comments_on() else ()),
                  og_image=f'{SITE}/assets/{c["src"]}' if c else None, og_type='article',
                  extra_head=f'<meta property="article:published_time" content="{a["date"]}">', structured=(posting, crumbs))


# ------------------------------------------------------------------ home / misc

def build_home(entries, articles):
    latest = [im for e in entries for im in e['images']][:4]
    thumbs = ''.join(
        f'<a href="cooking/"><img src="{UP}assets/cooking/{im["thumb"]}" width="{im["w"]}" height="{im["h"]}" alt="" loading="lazy"></a>'
        for im in latest)
    posts = ''.join(f'<li><a href="blog/{a["slug"]}/"><time>{date_disp(a)}</time>{esc(a["title"])}</a></li>'
                    for a in articles[:5])
    body = f'''<div class="wrap">
  <div class="home-hero">
    <p class="eyebrow">mengyahh.com</p>
    <h1 class="serif">{S['wm']}<span>{S['dot']}</span></h1>
  </div>
  <section class="home-sec">
    <div class="sec-head"><h2 class="serif"><a href="blog/">{S['nav_blog']}</a></h2><a class="sec-more" href="blog/">{S['home_all_posts']}</a></div>
    <ul class="latest">{posts}</ul>
  </section>
  <section class="home-sec">
    <div class="sec-head"><h2 class="serif"><a href="cooking/">{S['nav_cooking']}</a></h2><a class="sec-more" href="cooking/">{S['home_all']}</a></div>
    <p class="sec-desc">{S['home_cooking_desc']}</p>
    <div class="thumbs">{thumbs}</div>
  </section>
  <div class="home-duo">
    <section class="home-sec">
      <div class="sec-head"><h2 class="serif"><a href="about/">{S['nav_about']}</a></h2><a class="sec-more" href="about/">{S['home_more']}</a></div>
      <p class="sec-desc">{S['home_about_desc']}</p>
    </section>
    <section class="home-sec">
      <div class="sec-head"><h2 class="serif"><a href="{WORK_URL}" rel="noopener">{S['nav_work']}</a></h2><a class="sec-more" href="{WORK_URL}" rel="noopener">{S['home_go']}</a></div>
      <p class="sec-desc">{S['home_work_desc']}</p>
    </section>
  </div>
</div>'''
    site = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': S['site'], 'url': SITE + prefix(LANG) + '/', 'inLanguage': HTML_LANG[LANG]}
    me = {'@context': 'https://schema.org', '@type': 'Person', 'name': AUTHORS[LANG], 'url': SITE + prefix(LANG) + '/',
          'sameAs': [INSTAGRAM]}
    return layout(base='', title=S['home_title'], desc=S['home_desc'], path='/', body=body, current=None,
                  css=('home',), structured=(site, me), alts=AVAILABLE)


def banner_html(base, banner):
    return (f'<figure class="banner"><img src="{base}{UP}assets/{banner["src"]}" width="{banner["w"]}" height="{banner["h"]}" '
            f'alt="" decoding="async"></figure>')


def build_about(a):
    base = '../'
    secs = []
    for sec in a['sections']:
        tags = ''.join(f'<li>{esc(t)}</li>' for t in sec['tags'])
        body = []
        for b in sec['blocks']:
            if b['type'] == 'p':
                body.append(f'<p>{resolve(b["html"], base)}</p>')
            else:
                body.append(f'<{b["type"]}>' + ''.join(f'<li>{resolve(i, base)}</li>' for i in b['items']) + f'</{b["type"]}>')
        secs.append(f'<section class="about-sec" id="{sec["id"]}"><div class="sec-side"><h2 class="serif">{esc(sec["title"])}</h2>'
                    f'<ul class="tag-list">{tags}</ul></div><div class="sec-body">{"".join(body)}</div></section>')
    btns = ''.join(f'<a class="btn{" ghost" if i else ""}" href="{esc(resolve(b["href"], base))}">⮕ {esc(b["label"])}</a>'
                   for i, b in enumerate(a['buttons']))
    pr = a['profile']
    q = a['quote']
    bio = ''.join(f'<p>{b}</p>' for b in pr['bio'])
    body = f'''<div class="wrap">
  {banner_html(base, a['banner'])}
  <div class="page-head">
    <p class="eyebrow">About</p>
    <h1>{S['about_h1']}</h1>
  </div>
  <blockquote class="quote"><p>{q["html"]}</p><cite>{esc(q["source"])}</cite></blockquote>
  {"".join(secs)}
  <div class="btn-row">{btns}</div>
  <section class="profile">
    <img src="{base}{UP}assets/{pr["img"]["src"]}" width="{pr["img"]["w"]}" height="{pr["img"]["h"]}" alt="{S['profile_alt']}" loading="lazy" decoding="async">
    <div>
      <h2 class="serif">{esc(pr["name"])}</h2>
      {bio}
      <p>{pr["contact"]}</p>
      <p class="links"><a href="{INSTAGRAM}" rel="noopener">Instagram ↗</a></p>
    </div>
  </section>
</div>'''
    return layout(base=base, title=f'{S["about_title"]} · {S["site"]}', desc=S['about_desc'],
                  path='/about/', body=body, current='about', css=('pages',),
                  og_image=f'{SITE}/assets/{a["profile"]["img"]["src"]}', alts=AVAILABLE)


# The portfolio moved to the Understory site: these old addresses stay alive as redirects.
UNDERSTORY = 'https://understory.mengyahh.com'
MOVED = {
    '/portfolio/': f'{UNDERSTORY}/about.html#projects',
    '/portfolio/lecheng/': f'{UNDERSTORY}/portfolio/lecheng/',
    '/portfolio/daodu-hexi/': f'{UNDERSTORY}/portfolio/daodu-hexi/',
}


def build_redirect(target):
    t = esc(target)
    return (f'<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n<title>已搬到 Understory</title>\n'
            f'<link rel="canonical" href="{t}">\n<meta http-equiv="refresh" content="0; url={t}">\n'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">\n</head>\n<body>\n'
            f'<p>作品集已經搬到 Understory：<a href="{t}">{t}</a></p>\n</body>\n</html>\n')


def build_sitemap(langdata):
    urls = []
    for lang, (entries, articles) in langdata.items():
        pre = prefix(lang)
        urls += [(pre + '/', None), (pre + '/about/', None), (pre + '/cooking/', None),
                 (pre + '/blog/', articles[0]['date'] if articles else None)]
        urls += [(f'{pre}/blog/{a["slug"]}/', a['date']) for a in articles]
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


AVAILABLE = ['zh']        # languages that have pages (filled in below)

if __name__ == '__main__':
    # data/*.json holds the migrated Google Sites / Vocus / Strikingly content; content/**/*.md holds what is written from now on
    set_lang('zh')
    entries = mdcontent.merge_cooking(load('cooking.json', 'entries'), mdcontent.cooking_entries())
    json_articles = load('blog.json', 'articles')
    for old, new in mdcontent.filename_mismatches():
        print(f'note: {os.path.basename(old)} has a different date than its file name (publish.py renames it to {os.path.basename(new)})')
    articles = sorted(json_articles + mdcontent.blog_articles(json_articles), key=lambda a: (a['date'], a.get('seq', 1)), reverse=True)
    langdata = {'zh': (entries, articles)}
    abouts = {'zh': json.load(open(os.path.join(ROOT, 'data', 'about.json'), encoding='utf-8'))}
    for lang in LANGS[1:]:                                   # content/en/, content/ja/ : translations (see content/README.md)
        if not os.path.isdir(os.path.join(ROOT, 'content', lang)):
            continue
        set_lang(lang)
        l_entries = mdcontent.merge_cooking([], mdcontent.cooking_entries())
        l_articles = sorted(mdcontent.blog_articles([]), key=lambda a: (a['date'], a.get('seq', 1)), reverse=True)
        langdata[lang] = (l_entries, l_articles)
        ap = os.path.join(ROOT, 'content', lang, 'about.json')
        abouts[lang] = json.load(open(ap, encoding='utf-8')) if os.path.isfile(ap) else abouts['zh']
    AVAILABLE = list(langdata)

    for lang, (l_entries, l_articles) in langdata.items():
        set_lang(lang)
        print('---', lang)
        shutil.rmtree(os.path.join(ROOT, OUT + 'blog'), ignore_errors=True)      # drop pages of removed articles
        write(OUT + 'cooking/index.html', build_cooking(l_entries))
        write(OUT + 'blog/index.html', build_blog_index(l_articles))
        for i, a in enumerate(l_articles):
            newer = l_articles[i - 1] if i > 0 else None
            older = l_articles[i + 1] if i + 1 < len(l_articles) else None
            has = [l for l in langdata if any(x['slug'] == a['slug'] for x in langdata[l][1])]
            write(f'{OUT}blog/{a["slug"]}/index.html', build_post(a, newer, older, alts=has), quiet=True)
        print('wrote', OUT + 'blog/<slug>/index.html x', len(l_articles))
        write(OUT + 'index.html', build_home(l_entries, l_articles))
        write(OUT + 'about/index.html', build_about(abouts[lang]))
        write('assets/data/' + search_file(), build_search_index(l_articles))
    set_lang('zh')
    for path, target in MOVED.items():
        write(path.strip('/') + '/index.html', build_redirect(target), quiet=True)
    print('wrote', len(MOVED), 'redirects for the moved portfolio')
    write('sitemap.xml', build_sitemap(langdata))
    write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')
    print('comments:', COMMENTS_API if COMMENTS_API and TURNSTILE_SITEKEY else 'off (COMMENTS_API / TURNSTILE_SITEKEY not set)')
    print('view counts:', f'GoatCounter "{GOATCOUNTER}"' if GOATCOUNTER else 'off (GOATCOUNTER not set)')
