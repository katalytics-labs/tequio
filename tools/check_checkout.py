#!/usr/bin/env python3
"""Inspect explicitly configured development identity without repairing anything."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                            text=True, env=os.environ | {'GIT_OPTIONAL_LOCKS': '0'})
    return result.stdout.rstrip('\n') if result.returncode == 0 else None


def remote_identity(value):
    """Compare HTTPS/SSH Git endpoints; do not echo embedded credentials."""
    if not value:
        return None
    match = re.fullmatch(r'git@([^:]+):(.+)', value)
    if match:
        host, path = match.groups()
    else:
        parsed = urlsplit(value)
        if parsed.scheme not in ('https', 'ssh') or not parsed.hostname:
            return None
        if parsed.password or (parsed.scheme == 'https' and parsed.username):
            return None
        if parsed.query or parsed.fragment:
            return None
        host, path = parsed.hostname, parsed.path.lstrip('/')
        if parsed.port:
            host += ':' + str(parsed.port)
    path = path.rstrip('/')
    if path.endswith('.git'):
        path = path[:-4]
    return host.lower() + '/' + path if path else None


def same_path(value, expected):
    return isinstance(value, str) and Path(value).is_absolute() and Path(value).resolve() == Path(expected).resolve()


def inspect(project):
    root = Path(project).resolve()
    result = {'root': str(root), 'issues': [], 'warnings': []}
    issues = result['issues']
    top = git(root, 'rev-parse', '--show-toplevel')
    if top is None or Path(top).resolve() != root:
        issues.append('Requested directory is not the root of an existing Git checkout; investigate, do not initialize one.')
        return result
    required = {'root': 'tequio.canonicalRoot', 'origin': 'tequio.expectedOrigin',
                'branch': 'tequio.integrationBranch', 'lab': 'tequio.labPath'}
    config = {key: git(root, 'config', '--local', '--get', value)
              for key, value in required.items()}
    for key, value in config.items():
        if not value:
            issues.append('Missing verified local Git configuration: ' + required[key])
    if config['root'] and (not Path(config['root']).is_absolute() or Path(config['root']).resolve() != root):
        issues.append('Checkout root differs from the configured canonical root.')
    origin = git(root, 'config', '--local', '--get', 'remote.origin.url')
    identity = remote_identity(origin)
    expected = remote_identity(config['origin'])
    result['origin_identity'] = identity
    if not identity or not expected or identity != expected:
        issues.append('Origin is missing, credential-bearing, unsupported or differs from the configured expected origin.')
    result['branch'] = git(root, 'symbolic-ref', '--quiet', '--short', 'HEAD')
    result['head'] = git(root, 'rev-parse', '--verify', 'HEAD')
    if not result['head']:
        issues.append('Checkout has no committed HEAD.')
    if result['branch'] != config['branch']:
        issues.append('Branch differs from the configured integration branch, or HEAD is detached; reconcile before continuing.')
    try:
        tree = ast.parse((root / 'src/tequio/__init__.py').read_text())
        versions = [node.value.value for node in tree.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == '__version__' for target in node.targets)
                    and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)]
        if len(versions) != 1:
            raise ValueError('Missing unique package version')
        result['version'] = versions[0]
        readme = re.search(r'^Version ([0-9]+\.[0-9]+\.[0-9]+)\.', (root / 'README.md').read_text(), re.M)
        if not readme or readme.group(1) != versions[0]:
            issues.append('README and package version disagree or cannot be read.')
    except (OSError, SyntaxError, ValueError):
        issues.append('Cannot establish the package version from current source.')
    if config['lab']:
        lab = Path(config['lab'])
        result['lab'] = str(lab)
        if not lab.is_absolute() or lab.is_symlink() or not lab.is_dir() or lab.resolve().is_relative_to(root):
            issues.append('Private lab must be an existing separate directory, not a state symlink or part of the checkout.')
        else:
            try:
                layout = json.loads((lab / 'layout.json').read_text())
                if (not isinstance(layout, dict) or layout.get('schema_version') != 1
                        or not same_path(layout.get('canonical_checkout'), root)
                        or not same_path(layout.get('private_lab'), lab)):
                    issues.append('Private lab layout does not identify this canonical checkout and lab.')
                if not (lab / 'AGENTS.md').is_file():
                    issues.append('Private lab workflow guidance is missing.')
            except (OSError, ValueError):
                issues.append('Private lab layout.json is missing or invalid.')
    status = git(root, 'status', '--porcelain', '--untracked-files=normal')
    result['clean'] = status == ''
    if status is None:
        issues.append('Cannot inspect working-tree status.')
    elif status:
        result['warnings'].append('Uncommitted changes exist; inspect and preserve them before edits or commits.')
    tracked = git(root, 'ls-files', '--', '.tequio')
    if tracked:
        issues.append('Active private .tequio state is tracked by Git.')
    if git(root, 'check-ignore', '.tequio/identity-probe') is None:
        issues.append('Active .tequio state is not ignored.')
    result['briefing_skill_present'] = (root / 'skills/tequio-briefing/SKILL.md').is_file()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = inspect(args.project)
    except (OSError, ValueError) as exc:
        # Do not echo remote/config content from malformed input.
        result = {'issues': ['Inspection failed: ' + type(exc).__name__], 'warnings': []}
    print(json.dumps(result, indent=2))
    return 1 if result['issues'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
