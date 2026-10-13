"""The 工作 / Work / 仕事 section of mengyahh.com, generated from content/work/ (Chinese) and content/work/<lang>/ (en, ja).

    about.md          -> /work/                     what I do, projects, how we work, the AppSheet section, contact
    appsheet.md       -> (the AppSheet section of /work/)
    products/*.md     -> /work/appsheet/<slug>/     one page per existing work
    portfolio/*.md    -> /work/portfolio/<slug>/    project galleries (Chinese only)

English and Japanese live under /en/work/ and /ja/work/. Pictures are in assets/work/ (portfolio/, screenshots/);
in the Markdown they are written relative to that folder. build.py puts the returned page dicts into the shared
mengyahh.com layout. Stdlib only.
"""
import glob
import os
import re

import mdlite as M

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = '\n'
ASSETS = '/assets/work/'
PROJECTS_VISIBLE = None                    # None: show every project; a number: show that many and fold the rest behind "show more"

STR = {
    'zh': dict(site='萌芽中。', title='工作', cta='來信申請試用', for_='適用對象：', more='了解更多 →', back_appsheet='← 回到 AppSheet 管理系統',
               back_projects='← 回到做過的專案', portfolio='作品集', copy='複製 email', copied='已複製', selected='已選取，請按複製',
               projects_more='看其餘 {n} 個專案', page_nav='頁內導覽', contact='聯絡', video='播放影片：{label}', piece='{label}：作品 {i}'),
    'en': dict(site='Sprouting.', title='Work', cta='Ask for a trial by email', for_='Suited for: ', more='Read more →',
               back_appsheet='← Back to AppSheet systems', back_projects='← Back to the projects', portfolio='Portfolio',
               copy='Copy email', copied='Copied', selected='Selected, press copy', projects_more='Show the other {n} projects',
               page_nav='On this page', contact='Contact', video='Play video: {label}', piece='{label}: piece {i}'),
    'ja': dict(site='芽吹き中。', title='仕事', cta='メールでトライアルを申し込む', for_='対象：', more='詳しく見る →',
               back_appsheet='← AppSheet システム一覧へ', back_projects='← プロジェクト一覧へ', portfolio='ポートフォリオ',
               copy='メールをコピー', copied='コピーしました', selected='選択しました。コピーしてください',
               projects_more='ほかの{n}件のプロジェクトを見る', page_nav='このページの内容', contact='お問い合わせ',
               video='動画を再生：{label}', piece='{label}：作品 {i}'),
}
LANG = 'zh'
S = STR['zh']
CONTENT = os.path.join(ROOT, 'content', 'work')
P = ''                    # URL prefix of the language: '' or '/en' or '/ja'
LANGDIR = ''              # the same as a folder prefix: '' or 'en/'


def set_lang(lang):
    global LANG, S, CONTENT, P, LANGDIR
    LANG, S = lang, STR[lang]
    CONTENT = os.path.join(ROOT, 'content', 'work') if lang == 'zh' else os.path.join(ROOT, 'content', 'work', lang)
    P = '' if lang == 'zh' else f'/{lang}'
    LANGDIR = '' if lang == 'zh' else f'{lang}/'


def has_content(lang):
    base = os.path.join(ROOT, 'content', 'work') if lang == 'zh' else os.path.join(ROOT, 'content', 'work', lang)
    return os.path.isfile(os.path.join(base, 'about.md'))


def copy_js():
    return '''<script>
(function () {
  var b = document.getElementById('copy');
  if (!b) return;
  b.addEventListener('click', function () {
    var text = document.getElementById('addr').textContent;
    function done(msg) { b.textContent = msg; setTimeout(function () { b.textContent = '@@COPY@@'; }, 1800); }
    function fallback() {
      var r = document.createRange(); r.selectNodeContents(document.getElementById('addr'));
      var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); done('@@SELECTED@@');
    }
    try { navigator.clipboard.writeText(text).then(function () { done('@@COPIED@@'); }, fallback); } catch (e) { fallback(); }
  });
})();
</script>'''.replace('@@COPY@@', S['copy']).replace('@@COPIED@@', S['copied']).replace('@@SELECTED@@', S['selected'])


def local_links(body):
    """Links written in the Markdown files are relative to the work section (portfolio/lecheng/ -> /work/portfolio/lecheng/,
    /en/work/... for English). Links that start with / or http are left alone."""
    def fix(m):
        u = m.group(2)
        if re.match(r'(https?:|mailto:|#|/|tel:)', u):
            return m.group(0)
        return f'{m.group(1)}{P}/work/{u}"'
    return re.sub(r'(href=")([^"]+)"', fix, body)


def asset(src):
    return ASSETS + src


def screenshot(src):
    """English / Japanese app screenshots in assets/work/screenshots/<lang>/ (same file name) replace the Chinese ones."""
    if LANG != 'zh':
        cand = f'screenshots/{LANG}/{os.path.basename(src)}'
        if os.path.isfile(os.path.join(ROOT, 'assets', 'work', cand)):
            return asset(cand)
    return asset(src)


# ------------------------------------------------------------------ about.md  ->  /work/

def section(sid, kicker, inner):
    return (f'<section class="block" id="{sid}">\n  <div class="wrap">\n    <p class="kicker">{M.esc(kicker)}</p>\n{inner}\n  </div>\n</section>\n')


def r_hero(args, body, page_title):
    lines = body.strip().split('\n')
    eyebrow, rest = lines[0].strip(), '\n'.join(lines[1:])
    bl = M.blocks(rest)
    h1 = next((r for k, r in bl if k == 'h1'), None)
    if not h1:
        raise SystemExit('content/work/about.md: ::: hero needs a "# heading" line')
    title = re.sub(r'\*\*(.+?)\*\*', r'<span class="ask">\1</span>', M.esc(M.heading_text(h1)))
    lede = ''.join(f'<p class="lede">{M.inline(r)}</p>' for k, r in bl if k == 'p')
    return (f'<header class="hero" id="about">\n  <div class="wrap">\n    <div class="page-head"><p class="eyebrow">{M.esc(eyebrow)}</p>\n'
            f'    <h1>{M.esc(page_title)}</h1></div>\n    <p class="statement">{title}</p>\n    {lede}\n  </div>\n</header>\n')


def split_pair(item):
    """"label：text" (or "label: text") -> (label, text)"""
    return re.split(r'[：:]\s*', item, maxsplit=1)


def r_skills(args, body):
    h2, intro, cards, fields, tools = '', '', [], '', ''
    state, cur, in_tools = 'head', None, None
    for kind, raw in M.blocks(body):
        if kind == 'h2':
            h2 = f'    <h2>{M.inline(M.heading_text(raw))}</h2>\n'
        elif kind == 'h3':
            cur = {'title': M.heading_text(raw), 'parts': []}
            cards.append(cur)
            state = 'cards'
        elif kind == 'hr':
            state, cur = 'after', None
        elif kind == 'h4':
            in_tools = {'title': M.heading_text(raw), 'items': []}
            state = 'tools'
        elif state == 'head' and kind == 'p':
            intro = f'    <p class="intro">{M.inline(raw)}</p>\n'
        elif state == 'cards' and cur is not None:
            if kind == 'p':
                cur['parts'].append(f'<p>{M.inline(raw)}</p>')
            elif kind == 'quote':
                cur['parts'].append(f'<p class="note">{M.inline(M.quote_text(raw))}</p>')
            elif kind == 'ul':
                dl = ''.join(f'<dt>{M.inline(a)}</dt><dd>{M.inline(b)}</dd>' for a, b in (split_pair(i) for i in M.list_items(raw)))
                cur['parts'].append(f'<dl>{dl}</dl>')
        elif state == 'after' and kind == 'p':
            fields = f'    <p class="fields">{M.inline(raw)}</p>\n'
        elif state == 'tools' and kind == 'ul':
            in_tools['items'] = [split_pair(i) for i in M.list_items(raw)]
    cards_html = ''.join('      <div class="skill">\n        <h3>%s</h3>\n        %s\n      </div>\n' % (M.inline(c['title']), '\n        '.join(c['parts'])) for c in cards)
    if in_tools:
        dl = ''.join(f'<dt>{M.inline(a)}</dt><dd>' + ''.join(f'<span>{M.inline(x.strip())}</span>' for x in re.split(r'[、,，]\s*', b.replace('\n', ''))) + '</dd>'
                     for a, b in in_tools['items'])
        tools = f'\n    <div class="tools">\n      <h3>{M.inline(in_tools["title"])}</h3>\n      <dl>{dl}</dl>\n    </div>'
    return h2 + intro + f'    <div class="skills">\n{cards_html}    </div>\n' + fields + tools


def link_arrow(text, url):
    return f'<a class="plink" href="{url}">{text} {"↗" if re.match(r"https?://", url) else "→"}</a>'


def r_projects(args, body):
    h2, intro, items, after = '', '', [], ''
    state, cur = 'head', None
    for kind, raw in M.blocks(body):
        if kind == 'h2':
            h2 = f'    <h2>{M.inline(M.heading_text(raw))}</h2>\n'
        elif kind == 'h3':
            t = M.heading_text(raw)
            m = re.match(r'^(.*?)\s*\[([^\]]+)\]\(([^)\s]+)\)\s*$', t)
            title, link = (m.group(1), link_arrow(M.esc(m.group(2)), m.group(3))) if m else (t, '')
            cur = {'title': title, 'link': link, 'tags': ''}
            items.append(cur)
            state = 'items'
        elif kind == 'hr':
            state, cur = 'after', None
        elif state == 'head' and kind == 'p':
            intro = f'    <p class="intro">{M.inline(raw)}</p>\n'
        elif state == 'items' and kind == 'p' and cur is not None:
            cur['tags'] = ''.join(f'<span>{M.inline(x.strip())}</span>' for x in re.split(r'[、,，]\s*', raw.replace('\n', '')) if x.strip())
        elif state == 'after' and kind == 'p':
            after = f'    <p class="after">{M.inline(raw)}</p>\n'

    def row(i):
        return f'      <li><span class="head"><span class="type">{M.inline(i["title"])}</span>{i["link"]}</span><span class="tags">{i["tags"]}</span></li>\n'
    shown, rest = (items, []) if PROJECTS_VISIBLE is None else (items[:PROJECTS_VISIBLE], items[PROJECTS_VISIBLE:])
    out = f'    <ul class="projects">\n{"".join(row(i) for i in shown)}    </ul>\n'
    if rest:
        out += (f'    <details class="more-info proj-more">\n      <summary>{S["projects_more"].format(n=len(rest))}</summary>\n'
                f'      <ul class="projects">\n{"".join(row(i) for i in rest)}      </ul>\n    </details>\n')
    return h2 + intro + out + after


def r_process(args, body):
    h2, intro, steps, diag, cur = '', '', [], '', None
    state = 'head'
    for kind, raw in M.blocks(body):
        if kind == 'h2':
            h2 = f'    <h2>{M.inline(M.heading_text(raw))}</h2>\n'
        elif kind == 'h3':
            cur = {'title': M.heading_text(raw), 'text': ''}
            steps.append(cur)
            state = 'steps'
        elif kind == 'hr':
            state = 'after'
        elif state == 'head' and kind == 'p':
            intro = f'    <p class="intro">{M.inline(raw)}</p>\n'
        elif state == 'steps' and kind == 'p' and cur is not None:
            cur['text'] = raw
        elif state == 'after' and kind == 'p':
            diag = f'    <p class="diag">{M.inline(raw)}</p>\n'
    lis = ''.join(f'      <li><h3>{M.inline(s["title"])}</h3><p>{M.inline(s["text"])}</p></li>\n' for s in steps)
    return h2 + intro + f'    <ol class="steps">\n{lis}    </ol>\n' + diag


def r_why(args, body):
    h2, lis = '', ''
    for kind, raw in M.blocks(body):
        if kind == 'h2':
            h2 = f'    <h2>{M.inline(M.heading_text(raw))}</h2>\n'
        elif kind == 'ul':
            for item in M.list_items(raw):
                m = re.match(r'^\*\*(.+?)\*\*[：:]\s*(.*)$', item)
                if not m:
                    raise SystemExit(f'content/work/about.md: ::: why items must look like "- **標題**：說明" (got "{item[:30]}")')
                lis += f'      <li><strong>{M.inline(m.group(1))}</strong><span>{M.inline(m.group(2))}</span></li>\n'
    return h2 + f'    <ul class="why">\n{lis}    </ul>\n'


def r_name(args, body):
    return ''.join(f'    <p class="name-note">{M.inline(r)}</p>\n' for k, r in M.blocks(body) if k == 'p')


def contact_html(body, email):
    h2, lead, links = 'Contact', '', ''
    for kind, raw in M.blocks(body):
        if kind == 'h2':
            h2 = M.inline(M.heading_text(raw))
        elif kind == 'p' and not lead:
            lead = M.inline(raw)
        elif kind == 'ul':
            for item in M.list_items(raw):
                m = re.match(r'^\[([^\]]+)\]\(([^)\s]+)\)$', item)
                if not m:
                    raise SystemExit(f'content/work/about.md: ::: contact links must look like "- [文字](網址)" (got "{item[:30]}")')
                links += f'      <a href="{m.group(2)}">{M.esc(m.group(1))}</a>\n'
    links_html = f'    <div class="links">\n{links}    </div>\n' if links else ''
    return (f'<section class="contact" id="contact">\n  <div class="wrap">\n    <h2>{h2}</h2>\n    <p class="lead">{lead}</p>\n'
            f'    <div class="mailbox">\n      <span class="addr" id="addr">{M.esc(email)}</span>\n      <button type="button" id="copy">{S["copy"]}</button>\n    </div>\n'
            f'{links_html}  </div>\n</section>\n')


BLOCKS = {'skills': r_skills, 'projects': r_projects, 'process': r_process, 'why': r_why, 'name': r_name}


def read(*parts):
    return M.split_front(open(os.path.join(CONTENT, *parts), encoding='utf-8').read())


def build_about():
    """-> (page dict, contact section html)"""
    meta, text = read('about.md')
    email = meta.get('email', 'mengyahh@gmail.com')
    parts, contact, nav = [], '', []
    for typ, args, body in M.directives(text):
        if typ == 'hero':
            parts.append(r_hero(args, body, meta.get('title', S['title'])))
        elif typ == 'contact':
            contact = contact_html(body, email)
            parts.append(contact)
            nav.append(('contact', S['contact']))
        elif typ == 'appsheet':
            parts.append(section('appsheet', args or 'AppSheet', render_appsheet()))
            nav.append(('appsheet', args or 'AppSheet'))
        elif typ in BLOCKS:
            parts.append(section(typ, args or typ, BLOCKS[typ](args, body)))
            if typ != 'name':
                nav.append((typ, args or typ))
        else:
            raise SystemExit(f'content/work/about.md: unknown block "::: {typ}" (known: hero, skills, appsheet, projects, process, why, name, contact)')
    if nav and parts:
        links = ''.join(f'<a href="#{i}">{M.esc(t)}</a>' for i, t in nav)
        parts.insert(1, f'<nav class="page-nav" aria-label="{S["page_nav"]}"><div class="wrap">{links}</div></nav>\n')
    page = {'path': f'{LANGDIR}work/index.html', 'url': f'{P}/work/', 'lpath': '/work/', 'title': f'{meta.get("title", S["title"])} · {S["site"]}',
            'desc': meta.get('description', ''), 'body': local_links('\n'.join(parts)), 'depth': 1, 'css': ('work',), 'js': ()}
    return page, contact


# ------------------------------------------------------------------ products/<slug>.md and appsheet.md

def r_features(args, body):
    items = []
    for kind, raw in M.blocks(body):
        if kind == 'h3':
            items.append({'title': M.heading_text(raw), 'text': ''})
        elif kind == 'p' and items:
            items[-1]['text'] = raw
    cells = ''.join(f'      <div class="feature">\n        <h3>{M.inline(i["title"])}</h3>\n        <p>{M.inline(i["text"])}</p>\n      </div>\n' for i in items)
    return f'    <div class="feature-grid">\n{cells}    </div>\n'


def r_screens(args, body):
    shots, note, after = [], '', False
    for kind, raw in M.blocks(body):
        if kind == 'img':
            alt, src, cap = M.IMG.match(raw).groups()
            shots.append(f'        <div class="screen-shot">\n          <img src="{screenshot(src)}" alt="{M.esc(alt)}" loading="lazy">\n          <p>{M.inline(cap or "")}</p>\n        </div>\n')
        elif kind == 'hr':
            after = True
        elif kind == 'p' and after:
            note = f'      <p class="chart-caption">{M.inline(raw)}</p>\n'
    return (f'    <div class="screens-block">\n      <p class="chart-title">{M.inline(args)}</p>\n      <div class="screens-grid">\n{"".join(shots)}'
            f'      </div>\n{note}    </div>\n')


def r_note(args, body):
    return f'    <p class="reference-note">{M.inline(body.strip())}</p>\n'


def r_callout(args, body):
    paras, links = [], []
    for kind, raw in M.blocks(body):
        if kind == 'p':
            paras.append(M.inline(raw))
        elif kind == 'ul':
            for item in M.list_items(raw):
                m = re.match(r'^\[([^\]]+)\]\(([^)\s]+)\)$', item)
                if not m:
                    raise SystemExit(f'::: callout buttons must look like "- [文字](網址)" (got "{item[:30]}")')
                links.append((m.group(1), m.group(2)))
    cls = 'callout open' if args.strip() == 'open' else 'callout'
    q = chr(34)
    btns = ''.join(f'<a class="cta-btn{"" if i == 0 else " secondary"}" href="{u}"{"" if u.startswith("mailto:") else " target=" + q + "_blank" + q + " rel=" + q + "noopener" + q}>{M.esc(t)}</a>\n        '
                   for i, (t, u) in enumerate(links))
    cta = f'\n      <div class="cta-row">\n        {btns.rstrip()}\n      </div>' if links else ''
    return f'    <div class="{cls}">\n      {"<br><br>".join(paras)}{cta}\n    </div>\n'


def product_files():
    works = []
    for path in sorted(glob.glob(os.path.join(CONTENT, 'products', '*.md'))):
        name = os.path.basename(path)
        if name.startswith('_'):
            continue
        meta, body = M.split_front(open(path, encoding='utf-8').read())
        works.append((int(meta.get('order', '99')), os.path.splitext(name)[0], meta, body, name))
    return sorted(works, key=lambda w: w[0])


def work_cards():
    """The same card for every work: title, who it suits, one-line summary."""
    rows = ''
    for _, slug, pm, _, _ in product_files():
        who = f'        <p class="sys-for">{S["for_"]}{M.inline(pm["for"])}</p>{NL}' if pm.get('for') else ''
        href = f'{P}/work/appsheet/{slug}/'
        rows += (f'      <article class="system" id="{slug}">{NL}        <h3><a href="{href}">{M.inline(pm.get("title", slug))}</a></h3>{NL}{who}'
                 f'        <p>{M.inline(pm.get("summary", ""))}</p>{NL}'
                 f'        <p class="sys-more"><a href="{href}">{S["more"]}</a></p>{NL}      </article>{NL}')
    return f'    <div class="systems">{NL}{rows}    </div>{NL}'


def build_products(contact):
    pages = []
    for _, slug, meta, body, name in product_files():
        title = meta.get('title') or slug
        for_line = f'    <p class="sys-for">{S["for_"]}{M.inline(meta["for"])}</p>\n' if meta.get('for') else ''
        first = body.find(':::')
        intro_text, rest = (body, '') if first < 0 else (body[:first], body[first:])
        intro = ''.join(f'<p>{M.inline(r)}</p>' for k, r in M.blocks(intro_text) if k == 'p')
        parts = []
        for typ, args, dbody in M.directives(rest):
            if typ == 'features':
                parts.append(r_features(args, dbody))
            elif typ == 'screens':
                parts.append(r_screens(args, dbody))
            elif typ == 'note':
                parts.append(r_note(args, dbody))
            elif typ == 'callout':
                parts.append(r_callout(args, dbody))
            else:
                raise SystemExit(f'content/work/products/{name}: unknown block "::: {typ}" (known: features, screens, note, callout)')
        inner = (f'<section class="product">\n  <div class="wrap">\n    <div class="page-head"><p class="eyebrow">{M.esc(meta.get("eyebrow", ""))}</p>\n'
                 f'    <h1>{M.inline(title)}</h1></div>\n{for_line}    <div class="prose">{intro}</div>\n{"".join(parts)}'
                 f'    <p class="back"><a href="{P}/work/#appsheet">{S["back_appsheet"]}</a></p>\n  </div>\n</section>\n\n{contact}')
        shot = re.search(r'!\[[^\]]*\]\(([^)\s"]+)', body)
        pages.append({'path': f'{LANGDIR}work/appsheet/{slug}/index.html', 'url': f'{P}/work/appsheet/{slug}/', 'lpath': f'/work/appsheet/{slug}/',
                      'title': f'{title} · {S["site"]}', 'desc': meta.get('description') or title, 'body': local_links(inner), 'depth': 3,
                      'css': ('work',), 'js': (), 'og_image': screenshot(shot.group(1)) if shot else None})
    return pages


def render_appsheet():
    """The AppSheet section of /work/, written in content/work/appsheet.md:
    intro, a button, ::: offers (cards), ::: systems (one card per work), ::: details (folded lists)."""
    meta, body = read('appsheet.md')
    first = body.find(':::')
    intro_text, rest = (body, '') if first < 0 else (body[:first], body[first:])
    intro = ''.join(f'<p>{M.inline(r)}</p>' for k, r in M.blocks(intro_text) if k == 'p')
    out = [f'    <h2>{M.inline(meta.get("title", "AppSheet"))}</h2>\n    <div class="prose">{intro}</div>\n'
           f'    <p class="cta-line"><a class="cta-btn" href="#contact">{M.esc(meta.get("cta", S["cta"]))}</a></p>\n']
    folded = []
    for typ, args, dbody in M.directives(rest):
        if typ == 'offers':
            cards, notes = '', ''
            for kind, raw in M.blocks(dbody):
                if kind == 'ul':
                    for item in M.list_items(raw):
                        m = re.match(r'^\*\*(.+?)\*\*\s*(.*)$', item)
                        label, text = (m.group(1).rstrip('：:'), m.group(2)) if m else (item, '')
                        cards += f'      <div class="offer"><h4>{M.inline(label)}</h4><p>{M.inline(text)}</p></div>\n'
                elif kind == 'p':
                    notes += f'    <p class="offer-note">{M.inline(raw)}</p>\n'
            out.append(f'    <h3 class="points-title">{M.inline(args)}</h3>\n    <div class="offers">\n{cards}    </div>\n{notes}')
        elif typ == 'systems':
            lead = ''.join(f'    <p class="lede">{M.inline(raw)}</p>\n' for kind, raw in M.blocks(dbody) if kind == 'p')
            out.append(f'    <h3 class="points-title">{M.inline(args)}</h3>\n{lead}{work_cards()}')
        elif typ == 'details':
            lis = ''.join(f'        <li>{M.inline(i)}</li>\n' for kind, raw in M.blocks(dbody) if kind == 'ul' for i in M.list_items(raw))
            folded.append(f'    <details class="more-info">\n      <summary>{M.inline(args)}</summary>\n      <ul class="points">\n{lis}      </ul>\n    </details>\n')
        else:
            raise SystemExit(f'content/work/appsheet.md: unknown block "::: {typ}" (known: offers, systems, details)')
    return ''.join(out) + ''.join(folded)


# ------------------------------------------------------------------ portfolio/<slug>.md  (Chinese only)

def portfolio_rows(body, gi, name):
    rows, cur = [], None
    for kind, raw in M.blocks(body):
        if kind == 'h2':
            cur = {'label': M.heading_text(raw), 'desc': [], 'media': []}
            rows.append(cur)
        elif cur is None:
            continue
        elif kind == 'img':
            cur['media'].append(raw)
        elif kind in ('p', 'quote') and not cur['media']:
            cur['desc'].append(raw)
    out = []
    for ri, r in enumerate(rows):
        n = len(r['media'])
        has_video = any('(youtube:' in m for m in r['media'])
        cls = 'wide' if has_video else {1: 'c1', 2: 'c2'}.get(n, 'c3')
        gid, items = f'pf-{gi}-{ri}', []
        for i, raw in enumerate(r['media'], 1):
            lm = M.LINKED_IMG.match(raw)
            if lm:
                alt, src, cap, href = lm.groups()
            else:
                alt, src, cap = M.IMG.match(raw).groups()
                href = None
            figcap = f'<figcaption>{M.inline(cap)}</figcaption>' if cap else ''
            if src.startswith('youtube:'):
                yid = src[len('youtube:'):]
                poster = f'portfolio/yt-{yid}.webp'
                w, h = M.image_size(os.path.join(ROOT, 'assets', 'work', poster))
                items.append(f'<figure class="pf-item"><button type="button" class="yt" data-yt="{M.esc(yid)}" aria-label="{M.esc(S["video"].format(label=r["label"]))}">'
                             f'<img src="{asset(poster)}" width="{w}" height="{h}" alt="" loading="lazy" decoding="async">'
                             f'<span class="yt-play" aria-hidden="true"></span></button>{figcap}</figure>')
                continue
            full = os.path.join(ROOT, 'assets', 'work', src)
            if not os.path.isfile(full):
                raise SystemExit(f'{name}: picture "{src}" not found in assets/work/')
            thumb = re.sub(r'\.(\w+)$', r'-t.\1', src)
            if not os.path.isfile(os.path.join(ROOT, 'assets', 'work', thumb)):
                thumb = src
            w, h = M.image_size(os.path.join(ROOT, 'assets', 'work', thumb))
            a = alt or S['piece'].format(label=r['label'], i=i)
            if href:
                items.append(f'<figure class="pf-item"><a class="out" href="{M.esc(href)}" target="_blank" rel="noopener">'
                             f'<img src="{asset(thumb)}" width="{w}" height="{h}" alt="{M.esc(a)}" loading="lazy" decoding="async"></a>{figcap}</figure>')
            else:
                items.append(f'<figure class="pf-item"><a class="ph" href="{asset(src)}" data-group="{gid}" data-title="{M.esc(r["label"])}" data-alt="{M.esc(a)}">'
                             f'<img src="{asset(thumb)}" width="{w}" height="{h}" alt="{M.esc(a)}" loading="lazy" decoding="async"></a>{figcap}</figure>')
        desc = ''.join(f'<p>{M.inline(d.replace("@SITE/", "/"))}</p>' for d in r['desc'])
        out.append(f'<article class="pf-row"><div class="pf-info"><h2>{M.esc(r["label"])}</h2>{desc}</div>'
                   f'<div class="pf-grid {cls}">{"".join(items)}</div></article>')
    return ''.join(out), [r['label'] for r in rows]


def build_portfolio(contact):
    pages = []
    files = [p for p in sorted(glob.glob(os.path.join(CONTENT, 'portfolio', '*.md'))) if not os.path.basename(p).startswith('_')]
    for gi, path in enumerate(files):
        name = os.path.basename(path)
        slug = os.path.splitext(name)[0]
        meta, body = M.split_front(open(path, encoding='utf-8').read())
        title = meta.get('title') or slug
        rows_html, labels = portfolio_rows(body, gi, name)
        lab = '、'.join(labels)
        first = re.search(r'!\[[^\]]*\]\(([^)\s"]+)', body)
        img = None
        if first:
            src = first.group(1)
            img = asset(f'portfolio/yt-{src[len("youtube:"):]}.webp') if src.startswith('youtube:') else asset(src)
        inner = (f'<header class="hero">\n  <div class="wrap">\n    <div class="page-head"><p class="eyebrow"><a href="{P}/work/#projects">{S["portfolio"]}</a></p>\n'
                 f'    <h1>{M.inline(title)}</h1><p class="lede">{M.esc(lab)}</p></div>\n  </div>\n</header>\n\n'
                 f'<section class="pf">\n  <div class="wrap">\n    {rows_html}\n    <p class="back"><a href="{P}/work/#projects">{S["back_projects"]}</a></p>\n  </div>\n</section>\n\n{contact}')
        pages.append({'path': f'{LANGDIR}work/portfolio/{slug}/index.html', 'url': f'{P}/work/portfolio/{slug}/', 'lpath': f'/work/portfolio/{slug}/',
                      'title': f'{title} · {S["site"]}', 'desc': meta.get('description') or f'{title}：{lab}。', 'body': local_links(inner), 'depth': 3,
                      'css': ('work', 'lightbox'), 'js': ('lightbox', 'yt'), 'og_image': img})
    return pages


def build_all(lang='zh'):
    """-> [page dict] for one language. Every page has: path (file, relative to the site root), url (with the language prefix),
    lpath (the address without the language prefix, for the language switcher), title, desc, body (already wrapped in
    <div class="work">), depth, css, js."""
    set_lang(lang)
    about, contact = build_about()
    pages = [about] + build_products(contact)
    if lang == 'zh':                          # the project galleries are Chinese only
        pages += build_portfolio(contact)
    for p in pages:
        extra = copy_js() if 'id="copy"' in p['body'] else ''
        p['body'] = f'<div class="work">\n{p["body"]}\n</div>\n{extra}'
    return pages
