#!/usr/bin/env python3
r"""Add photos to an article or a cooking note: resize, convert to WebP, strip EXIF/GPS, print the Markdown lines to paste.

    python scripts/photo.py blog content/blog/2025-09-29_小豆島.md D:\pics\a.jpg D:\pics\b.jpg
    python scripts/photo.py cooking 202601-a D:\pics\a.jpg

blog    -> the article's photo folder (photos: or date in the front matter): assets/blog/<folder>/<date>-<article no.>_<photo no.>.webp
           e.g. 20260910-01_03.webp (+ 20260910-01_03-t.webp, the thumbnail for galleries); give its .md file.
cooking -> assets/cooking/<name>-N.webp + <name>-N-t.webp (<name> is any label, e.g. 202601-a; numbering continues)
Needs Pillow:  pip install pillow
"""
import os
import re
import sys

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit('This tool needs Pillow:  pip install pillow')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def save(im, dst, max_w, q):
    im = im.convert('RGB')
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    im.save(dst, 'WEBP', quality=q, method=6)               # re-encoding drops EXIF / GPS


def next_no(folder, pattern):
    nums = [int(m.group(1)) for f in os.listdir(folder) if (m := re.fullmatch(pattern, f))] if os.path.isdir(folder) else []
    return max(nums, default=0) + 1


def main():
    if len(sys.argv) < 4 or sys.argv[1] not in ('blog', 'cooking'):
        sys.exit(__doc__)
    kind, name, files = sys.argv[1], sys.argv[2], sys.argv[3:]
    lines = []
    if kind == 'blog':
        if name.lower().endswith('.md'):                       # the article's .md file: its date, seq and `photos:` folder
            meta = {}
            with open(name, encoding='utf-8') as fh:
                front = fh.read().replace('\r\n', '\n').split('---')[1]
            for line in front.split('\n'):
                k, _, v = line.partition(':')
                meta[k.strip()] = v.strip()
            date, seq = meta.get('date') or sys.exit('No date in the front matter'), int(meta.get('seq') or 1)
            folder_name = meta.get('photos') or (date if seq == 1 else f'{date}-{seq}')
        else:                                                   # a date such as 2025-09-29 (or 2025-09-29-2 for the 2nd article that day)
            m = re.fullmatch(r'(\d{4}-\d{2}-\d{2})(?:-(\d{1,2}))?', name) or sys.exit('Give the article .md file, or its date like 2025-09-29')
            date, seq = m.group(1), int(m.group(2) or 1)
            folder_name = name
        # file names: <date>-<article no. of that day>_<photo no.>.webp   e.g. 20260910-01_03.webp
        prefix = f'{date.replace("-", "")}-{seq:02d}_'
        folder = os.path.join(ROOT, 'assets', 'blog', folder_name)
        os.makedirs(folder, exist_ok=True)
        n = next_no(folder, re.escape(prefix) + r'(\d\d)\.webp')
        for f in files:
            im = ImageOps.exif_transpose(Image.open(f))
            fn = f'{prefix}{n:02d}.webp'
            save(im, os.path.join(folder, fn), 1440, 82)
            save(im, os.path.join(folder, fn.replace('.webp', '-t.webp')), 480, 74)     # thumbnail for :::gallery
            lines.append(f'![]({fn})')
            n += 1
    else:
        folder = os.path.join(ROOT, 'assets', 'cooking')
        n = next_no(folder, re.escape(name) + r'-(\d+)\.webp')
        for f in files:
            im = ImageOps.exif_transpose(Image.open(f))
            save(im, os.path.join(folder, f'{name}-{n}.webp'), 1280, 80)
            save(im, os.path.join(folder, f'{name}-{n}-t.webp'), 640, 76)
            lines.append(f'![]({name}-{n}.webp)')
            n += 1
    print('Saved. Paste these lines into the .md file where the photos should go.')
    print('Tip: write a short description of what is in the photo inside the [ ] (helps Google Images and screen readers).\n')
    print('\n\n'.join(lines))


if __name__ == '__main__':
    main()
