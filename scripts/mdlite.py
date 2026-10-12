"""A very small Markdown helper for the Understory pages (stdlib only)."""
import html
import re
import struct

esc = lambda s: html.escape(s, quote=False)
IMG = re.compile(r'^!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)$')                    # ![alt](file "caption")
LINKED_IMG = re.compile(r'^\[!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)\]\(([^)\s]+)\)$')   # [![alt](file "caption")](https://...)


def split_front(text):
    text = text.replace('\r\n', '\n').lstrip('﻿')
    m = re.match(r'---\n(.*?)\n---\n?', text, re.S)
    if not m:
        raise SystemExit('missing front matter (the block between two --- lines at the top)')
    meta = {}
    for line in m.group(1).split('\n'):
        if line.strip() and not line.lstrip().startswith('#'):
            k, _, v = line.partition(':')
            meta[k.strip()] = v.strip()
    return meta, text[m.end():].strip('\n')


def inline(s):
    """Text with **bold**, [links](url), and the tags <br> <sub> <sup> <em> <s> <u> written directly."""
    s = esc(s)
    for tag in ('br', 'sub', 'sup', 'em', 's', 'u'):
        s = s.replace(f'&lt;{tag}&gt;', f'<{tag}>').replace(f'&lt;/{tag}&gt;', f'</{tag}>')
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return s.replace('\n', '<br>')


def image_size(path):
    """(width, height) of a WebP / PNG / JPEG file."""
    with open(path, 'rb') as f:
        d = f.read(65536)
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
    raise SystemExit(f'cannot read the size of {path} (use .webp or .png)')


def blocks(text):
    """Split text into (kind, raw) pieces on blank lines: h1..h4, ul, quote, hr, img, p."""
    out = []
    text = re.sub(r'^(#{1,4} .+)\n(?=\S)', r'\1\n\n', text, flags=re.M)
    img = r'!\[[^\]]*\]\([^)"]*(?:"[^"]*")?\)'
    text = re.sub(r'\n*(\[' + img + r'\]\([^)\s]+\)|' + img + r')[ \t]*\n*', r'\n\n\1\n\n', text)   # a picture (or a linked picture) is its own block
    for raw in re.split(r'\n\s*\n', text.strip()):
        lines = [l.rstrip() for l in raw.split('\n') if l.strip()]
        if not lines:
            continue
        raw = '\n'.join(lines)
        m = re.match(r'(#{1,4}) ', raw)
        if m:
            kind = f'h{len(m.group(1))}'
        elif raw == '---':
            kind = 'hr'
        elif IMG.match(raw) or LINKED_IMG.match(raw):
            kind = 'img'
        elif all(re.match(r'[-*] ', l) for l in lines):
            kind = 'ul'
        elif all(l.startswith('>') for l in lines):
            kind = 'quote'
        else:
            kind = 'p'
        out.append((kind, raw))
    return out


def list_items(raw):
    return [re.sub(r'^[-*] ', '', l).strip() for l in raw.split('\n')]


def quote_text(raw):
    return ' '.join(l.lstrip('>').strip() for l in raw.split('\n') if l.lstrip('>').strip())


def heading_text(raw):
    return re.sub(r'^#{1,4} ', '', raw).strip()


def directives(text):
    """Text -> [(type, args, body)] for every ::: type args ... ::: block."""
    out = []
    for m in re.finditer(r'^:::[ \t]*(\w+)[ \t]*(.*?)\n(.*?)\n:::[ \t]*$', text, re.S | re.M):
        out.append((m.group(1), m.group(2).strip(), m.group(3)))
    return out
