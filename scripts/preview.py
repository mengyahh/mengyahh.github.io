#!/usr/bin/env python3
"""Local preview: builds the site, serves it at http://localhost:8000 and rebuilds whenever a file in
content/ or data/ is saved (just press F5 in the browser).   Stop with Ctrl+C."""
import http.server
import os
import socketserver
import subprocess
import sys
import threading
import time
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get('PORT', '8000'))


def snapshot():
    state = {}
    for base in ('content', 'data'):
        for dp, _, fs in os.walk(os.path.join(ROOT, base)):
            for f in fs:
                p = os.path.join(dp, f)
                state[p] = os.path.getmtime(p)
    for f in ('scripts/build.py', 'scripts/mdcontent.py'):
        state[f] = os.path.getmtime(os.path.join(ROOT, f))
    return state


def build():
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'build.py')], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    if r.returncode:
        print('\n*** Build failed:', (r.stderr or r.stdout).strip().splitlines()[-1])
    else:
        print(time.strftime('%H:%M:%S'), 'built - refresh the browser')
    return r.returncode == 0


class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    build()
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', PORT), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f'Preview: http://localhost:{PORT}   (Ctrl+C to stop)')
    if not os.environ.get('NO_BROWSER'):
        webbrowser.open(f'http://localhost:{PORT}')
    seen = snapshot()
    try:
        while True:
            time.sleep(1)
            now = snapshot()
            if now != seen:
                time.sleep(0.4)                       # let the editor finish writing
                seen = snapshot()
                build()
    except KeyboardInterrupt:
        srv.shutdown()
