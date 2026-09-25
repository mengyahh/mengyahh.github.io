#!/usr/bin/env python3
"""Make the small list thumbnail (NN-t.webp) for every article's cover photo that does not have one yet.

Runs automatically from preview.py and publish.py (needs Pillow: pip install pillow; without it this does nothing
and the article list just uses the full-size cover photo).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mdcontent as M

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None


def ensure():
    """Create missing cover thumbnails; returns the list of files created."""
    if Image is None:
        return []
    made = []
    for meta, body, path in M.read_dir('blog'):
        slug = meta.get('date', '')
        folder = meta.get('photos') or slug
        imgdir = os.path.join(M.ROOT, 'assets', 'blog', folder)
        fn = M.cover_file(meta, body, imgdir)
        if not fn or fn.endswith('-t.webp') or not os.path.isfile(os.path.join(imgdir, fn)):
            continue
        dst = os.path.join(imgdir, M.thumb_name(fn))
        if os.path.exists(dst):
            continue
        im = ImageOps.exif_transpose(Image.open(os.path.join(imgdir, fn))).convert('RGB')
        if im.width > 480:
            im = im.resize((480, round(im.height * 480 / im.width)), Image.LANCZOS)
        im.save(dst, 'WEBP', quality=74, method=6)
        made.append(os.path.relpath(dst, M.ROOT))
    return made


if __name__ == '__main__':
    done = ensure()
    print(f'{len(done)} thumbnail(s) created' + (': ' + ', '.join(done) if done else ''))
    if Image is None:
        print('(Pillow is not installed: pip install pillow)')
