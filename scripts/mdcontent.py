"""Markdown content -> the same article / entry dicts that build.py reads from data/*.json.

    content/blog/*.md      one blog article per file
    content/cooking/*.md   one cooking note per file

Files whose name starts with "_" (or whose front matter says `draft: yes`) are skipped, so they can be drafts.
See content/README.md for the writing conventions. Stdlib only.
"""
import glob
import html
import os
import re
import struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
esc = lambda s: html.escape(s, quote=False)
IMG_LINE = re.compile(r'^!\[([^\]]*)\]\(([^)\s]+)\)$')


# ------------------------------------------------------------------ reading files

def split_front(text):
    text = text.replace('\r\n', '\n').lstrip('﻿')
    m = re.match(r'---\n(.*?)\n---\n?', text, re.S)
    if not m:
        raise ValueError('missing front matter (the block between two --- lines at the top)')
    meta = {}
    for line in m.group(1).split('\n'):
        if line.strip() and not line.lstrip().startswith('#'):
            k, _, v = line.partition(':')
            meta[k.strip()] = v.strip()
    return meta, text[m.end():].strip()


def as_list(v):
    return [x.strip() for x in (v or '').strip().strip('[]').split(',') if x.strip()]


def read_dir(sub):
    """[(meta, body, path)] for every non-draft .md file in content/<sub>."""
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'content', sub, '*.md'))):
        name = os.path.basename(path)
        if name.startswith('_'):
            continue
        try:
            meta, body = split_front(open(path, encoding='utf-8').read())
        except ValueError as e:
            raise SystemExit(f'{name}: {e}')
        if meta.get('draft', '').lower() in ('yes', 'true', '1'):
            continue
        out.append((meta, body, path))
    return out


def image_size(path):
    """(width, height) of a WebP / PNG / JPEG file without any imaging library."""
    with open(path, 'rb') as f:
        d = f.read(65536 if not path.lower().endswith(('.jpg', '.jpeg')) else 1 << 22)
    if d[:4] == b'RIFF' and d[8:12] == b'WEBP':
        kind = d[12:16]
        if kind == b'VP8X':
            return 1 + int.from_bytes(d[24:27], 'little'), 1 + int.from_bytes(d[27:30], 'little')
        if kind == b'VP8L':
            b = int.from_bytes(d[21:25], 'little')
            return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
        if kind == b'VP8 ':
            w, h = struct.unpack('<HH', d[26:30])
            return w & 0x3FFF, h & 0x3FFF
    if d[:8] == b'\x89PNG\r\n\x1a\n':
        return struct.unpack('>II', d[16:24])
    if d[:2] == b'\xff\xd8':
        i = 2
        while i + 9 < len(d):
            if d[i] != 0xFF:
                i += 1
                continue
            m = d[i + 1]
            if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack('>HH', d[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack('>H', d[i + 2:i + 4])[0]
    raise ValueError(f'cannot read the size of {path}')


# ------------------------------------------------------------------ Markdown -> HTML

def inline(s, titles):
    s = esc(s)
    # 〈another article's title〉 becomes a link to it; the part before "：" is enough
    s = re.sub(r'〈([^〉]+)〉', lambda m: (f'<a href="@BLOG/{titles[m.group(1)]}/">〈{m.group(1)}〉</a>'
                                        if m.group(1) in titles else m.group(0)), s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+|@[A-Z]+/[^)\s]*)\)', lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![*\w])\*([^*\n]+)\*(?![*\w])', r'<em>\1</em>', s)
    return s.replace('\n', '<br>')


def chunks(body):
    """Body text -> (kind, raw text) blocks; the trailing 關鍵字 block is returned separately."""
    kw_lines = []
    m = re.search(r'\n*\*\*關鍵字\*\*\s*\n+(.*)$', body, re.S)
    if m:
        kw_lines = [l.strip() for l in m.group(1).strip().split('\n') if l.strip()]
        body = body[:m.start()]
    body = re.sub(r'\n*(!\[[^\]]*\]\([^)\s]+\))[ \t]*\n*', r'\n\n\1\n\n', body)           # a photo is its own block
    body = re.sub(r'^(#{2,4} .+)\n(?=\S)', r'\1\n\n', body, flags=re.M)                     # heading, then text
    out = []
    for raw in re.split(r'\n\s*\n', body.strip()):
        lines = [l.rstrip() for l in raw.split('\n') if l.strip()]
        if not lines:
            continue
        raw = '\n'.join(lines)
        if IMG_LINE.match(raw):
            kind = 'img'
        elif re.match(r'^#{2,4} ', raw):
            kind = 'h'
        elif raw == '**備忘**':
            kind = 'memo'
        elif raw == '---':
            kind = 'hr'
        elif all(re.match(r'^[-*] ', l) for l in lines):
            kind = 'ul'
        elif all(re.match(r'^\d+[.)] ', l) for l in lines):
            kind = 'ol'
        elif all(l.startswith('>') for l in lines):
            kind = 'quote'
        else:
            kind = 'p'
        out.append((kind, raw))
    return out, kw_lines


def render_block(kind, raw, titles, after_memo=False):
    lines = raw.split('\n')
    if kind == 'h':
        lvl = len(raw) - len(raw.lstrip('#'))
        return f'<h{lvl}>{inline(raw[lvl:].strip(), titles)}</h{lvl}>'
    if kind == 'memo':
        return '<p class="memo-label">備忘</p>'
    if kind == 'hr':
        return '<hr>'
    if kind == 'ul':
        lis = ''.join(f'<li>{inline(l[2:].strip(), titles)}</li>' for l in lines)
        return f'<ul class="memo">{lis}</ul>' if after_memo else f'<ul>{lis}</ul>'
    if kind == 'ol':
        return '<ol>' + ''.join(f'<li>{inline(re.sub(r"^\d+[.)] ", "", l), titles)}</li>' for l in lines) + '</ol>'
    if kind == 'quote':
        return '<blockquote><p>' + inline('\n'.join(l.lstrip('>').strip() for l in lines), titles) + '</p></blockquote>'
    return f'<p>{inline(raw, titles)}</p>'


def title_map(json_articles, md_metas):
    """article title (and its part before "：") -> slug"""
    t = {}
    pairs = [(a['title'], a['slug']) for a in json_articles] + [(m['title'], m['date']) for m in md_metas]
    for title, slug in pairs:
        t[title] = slug
    for title, slug in pairs:
        t.setdefault(title.split('：')[0], slug)
    return t


# ------------------------------------------------------------------ blog

def blog_articles(json_articles):
    """Render content/blog/*.md into article dicts (same shape as data/blog.json)."""
    files = read_dir('blog')
    titles = title_map(json_articles, [m for m, _, _ in files])
    taken = {a['slug'] for a in json_articles}
    arts = []
    for meta, body, path in files:
        name = os.path.basename(path)
        slug = meta.get('date', '')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', slug):
            raise SystemExit(f'{name}: date must look like 2025-09-29 (it is also the article address); got "{slug}"')
        if slug in taken:
            raise SystemExit(f'{name}: another article already uses the address /blog/{slug}/')
        taken.add(slug)
        for k in ('title', 'categories'):
            if not meta.get(k):
                raise SystemExit(f'{name}: front matter needs "{k}"')
        imgdir = os.path.join(ROOT, 'assets', 'blog', slug)
        blocks, kw_lines = chunks(body)
        parts, n, first = [], 0, None
        after_memo = False
        for kind, raw in blocks:
            if kind == 'img':
                alt, fn = IMG_LINE.match(raw).groups()
                if not os.path.isfile(os.path.join(imgdir, fn)):
                    raise SystemExit(f'{name}: photo "{fn}" not found in assets/blog/{slug}/')
                w, h = image_size(os.path.join(imgdir, fn))
                n += 1
                first = first or fn
                alt = alt or f'{meta["title"]}（照片 {n}）'
                parts.append(f'<figure><img src="@ASSET/blog/{slug}/{fn}" width="{w}" height="{h}" '
                             f'alt="{html.escape(alt)}" loading="lazy" decoding="async"></figure>')
            else:
                parts.append(render_block(kind, raw, titles, after_memo=(kind == 'ul' and after_memo)))
            after_memo = kind == 'memo'
        cover = None
        cover_fn = meta.get('cover') or ('cover.webp' if os.path.isfile(os.path.join(imgdir, 'cover.webp')) else first)
        if cover_fn:
            if not os.path.isfile(os.path.join(imgdir, cover_fn)):
                raise SystemExit(f'{name}: cover "{cover_fn}" not found in assets/blog/{slug}/')
            w, h = image_size(os.path.join(imgdir, cover_fn))
            cover = {'src': f'blog/{slug}/{cover_fn}', 'w': w, 'h': h}
        art = {'slug': slug, 'source': 'markdown', 'title': meta['title'], 'date': slug,
               'categories': as_list(meta['categories']), 'tags': [], 'abstract': meta.get('summary', ''),
               'keywords': as_list(meta.get('keywords')), 'kwlines': kw_lines, 'cover': cover, 'html': ''.join(parts)}
        if meta.get('date_label'):
            art['date_label'] = meta['date_label']
        if cover and meta.get('banner', '').lower() not in ('yes', 'true', '1'):
            art['cover_is_first_image'] = True          # the list thumbnail only; the article opens with its text
        arts.append(art)
    return arts


# ------------------------------------------------------------------ cooking

def cooking_entries():
    """Render content/cooking/*.md into entry dicts (same shape as data/cooking.json)."""
    files = read_dir('cooking')
    titles = {}
    entries = []
    for meta, body, path in files:
        name = os.path.basename(path)
        day = meta.get('date', '')
        m = re.fullmatch(r'(\d{4})-(\d{2})(-\d{2})?', day)
        if not m:
            raise SystemExit(f'{name}: date must look like 2025-07-12 (or 2025-07); got "{day}"')
        if not meta.get('title'):
            raise SystemExit(f'{name}: front matter needs "title"')
        blocks, _ = chunks(body)
        out_blocks, images = [], []
        for kind, raw in blocks:
            if kind == 'img':
                cap, fn = IMG_LINE.match(raw).groups()
                p = os.path.join(ROOT, 'assets', 'cooking', fn)
                if not os.path.isfile(p):
                    raise SystemExit(f'{name}: photo "{fn}" not found in assets/cooking/')
                w, h = image_size(p)
                thumb = re.sub(r'\.(\w+)$', r'-t.\1', fn)
                if not os.path.isfile(os.path.join(ROOT, 'assets', 'cooking', thumb)):
                    thumb = fn
                im = {'src': fn, 'thumb': thumb, 'w': w, 'h': h}
                if cap:
                    im['caption'] = cap
                images.append(im)
            elif kind in ('h', 'memo'):
                txt = '備忘' if kind == 'memo' else raw.lstrip('#').strip()
                out_blocks.append({'type': 'p', 'html': f'<strong>{inline(txt, titles)}</strong>'})
            elif kind in ('ul', 'ol'):
                out_blocks.append({'type': 'ul', 'items': [inline(re.sub(r'^([-*]|\d+[.)]) ', '', l), titles) for l in raw.split('\n')]})
            else:
                out_blocks.append({'type': 'p', 'html': inline(raw, titles)})
        e = {'id': meta.get('id') or f'{m.group(1)}{m.group(2)}-{os.path.splitext(name)[0]}', 'source': 'markdown',
             'date': m.group(1) + m.group(2), 'day': day, 'title': meta['title'], 'blocks': out_blocks, 'images': images}
        if meta.get('place'):
            e['place'] = meta['place']
        entries.append(e)
    return entries


def merge_cooking(json_entries, md_entries):
    """Newest first. json entries only know their month, so a note from the same month goes before them."""
    def day_of(e):
        d = e.get('day') or e['date']
        return d + '-15' if len(d) == 7 else d
    merged = list(json_entries)
    for e in sorted(md_entries, key=day_of, reverse=True):
        pos = len(merged)
        for i, x in enumerate(merged):
            if x.get('day'):
                older = day_of(x) < day_of(e)
            else:
                older = len(x['date']) == 6 and x['date'] <= e['date']
            if older:
                pos = i
                break
        merged.insert(pos, e)
    return merged
