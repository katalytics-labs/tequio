#!/usr/bin/env python3
"""Read a source-only candidate inventory from an exact commit; create no export."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT_FILES = frozenset(('.gitignore', 'README.md', 'CONTRIBUTING.md', 'LICENSE', 'bundle.json'))
ROOT_DIRS = frozenset(('bin', 'docs', 'examples', 'profiles', 'roles', 'skills', 'src', 'templates', 'tests', 'tools'))
PRIVATE_PARTS = frozenset(('.git', '.tequio', '.agents', '.codex', '__pycache__', '.venv',
                           'node_modules', 'notes', 'journal', 'reviews', 'sessions', 'rollouts', 'archive'))
PRIVATE_SUFFIXES = frozenset(('.pyc', '.pyo', '.jsonl', '.sqlite', '.sqlite3', '.db', '.log', '.key', '.pem'))


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                            env=os.environ | {'GIT_OPTIONAL_LOCKS': '0'})
    if result.returncode:
        raise ValueError('Cannot read the requested Git source identity or object.')
    return result.stdout


def inventory(project, commit):
    root = Path(project).resolve()
    if not re.fullmatch(r'(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})', commit):
        raise ValueError('Specify the exact full commit SHA, not HEAD, a branch, tag or abbreviated hash.')
    commit = commit.lower()
    top = git(root, 'rev-parse', '--show-toplevel').decode().rstrip('\n')
    if Path(top).resolve() != root:
        raise ValueError('Requested source directory is not the Git checkout root.')
    if git(root, 'cat-file', '-t', commit).strip() != b'commit':
        raise ValueError('The specified object must be a commit, not a tag or tree.')
    files, omitted = {}, []
    for item in git(root, 'ls-tree', '-rz', '--full-tree', commit).split(b'\0'):
        if not item:
            continue
        meta, raw_path = item.split(b'\t', 1)
        mode, kind, sha = meta.decode().split()
        path = raw_path.decode('utf-8')
        parts = PurePosixPath(path).parts
        if path == 'AGENTS.md':
            omitted.append(path)  # Private development instructions, not product/runtime content.
            continue
        if (not parts or PurePosixPath(path).is_absolute() or '..' in parts
                or any(ord(c) < 32 for c in path)):
            raise ValueError('Invalid source path in commit inventory.')
        if (PRIVATE_PARTS.intersection(parts) or PurePosixPath(path).suffix.lower() in PRIVATE_SUFFIXES
                or any(part.startswith('.env') and part != '.env.example' for part in parts)
                or PurePosixPath(path).name in ('AGENTS.md', 'auth.json', 'config.toml', '.DS_Store')):
            raise ValueError('Private/generated or development-only path requires explicit review: ' + path)
        if path not in ROOT_FILES and not (len(parts) > 1 and parts[0] in ROOT_DIRS):
            raise ValueError('Undeclared public source path requires explicit review: ' + path)
        if mode not in ('100644', '100755') or kind != 'blob':
            raise ValueError('Only regular source files may enter the candidate: ' + path)
        content = git(root, 'cat-file', 'blob', sha)
        files[path] = {'mode': mode, 'sha256': hashlib.sha256(content).hexdigest()}
    missing = sorted(ROOT_FILES - files.keys())
    if missing:
        raise ValueError('Required product root files are missing: ' + ', '.join(missing))
    return {'schema_version': 1, 'source_commit': commit, 'files': files,
            'omitted_development_files': omitted, 'creates_export': False,
            'limits': 'Inventory only: content/privacy review and owner authorization remain required. No Git history or author metadata is exported.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    try:
        result = inventory(args.project, args.commit)
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({'error': str(exc), 'creates_export': False}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
