#!/usr/bin/env python3
"""Build, commit and push everything to the live site (asks before pushing).

    python publish.py                    (or double-click publish.bat)
    python publish.py "message"          (commit message)
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))
import mdcontent

msg = sys.argv[1] if len(sys.argv) > 1 else 'Update content'


def run(*cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if check and r.returncode:
        sys.exit(f'\n*** {" ".join(cmd)} failed:\n{(r.stderr or r.stdout).strip()}')
    return r.stdout.strip()


for old, new in mdcontent.sync_filenames():
    print(f'Renamed to match its date: {old}  ->  {new}')
run(sys.executable, 'scripts/build.py')
print('Built.')
status = run('git', 'status', '--short')
if not status:
    sys.exit('Nothing changed - nothing to publish.')
print(status)
if input('\nPush these changes to the live site (mengyahh.com)?  [y/N] ').strip().lower() != 'y':
    sys.exit('Cancelled. (Nothing was committed.)')
run('git', 'add', '-A')
run('git', 'commit', '-m', msg)
pushed = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True, encoding='utf-8')
if pushed.returncode:
    print('Push was rejected, trying "git pull --rebase" first...')
    run('git', 'pull', '--rebase', 'origin', 'main')
    run('git', 'push', 'origin', 'main')
print('\nDone. GitHub Pages usually updates within a minute or two: https://mengyahh.com')
