"""Explicit, local Git worktree isolation; coordination stays at the original root."""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


class GitIsolationError(ValueError):
    """A Git operation was refused or could not safely complete."""


def _git(path, *args):
    try:
        result = subprocess.run(['git', '-C', str(path), *args], text=True,
                                capture_output=True, check=False, timeout=30,
                                env={k: v for k, v in os.environ.items() if not k.startswith('GIT_')})
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitIsolationError(f'Git is unavailable: {exc}') from exc
    if result.returncode:
        raise GitIsolationError(result.stderr.strip() or 'Git operation failed')
    return result.stdout.rstrip('\n')


def _project(project):
    path = Path(project).resolve()
    if not path.is_dir():
        raise GitIsolationError('Project must be an existing directory')
    return path


def _read(path):
    if path.is_symlink() or path.parent.is_symlink():
        raise GitIsolationError('Private isolation paths must not be symlinks')
    try:
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            raise GitIsolationError('Private isolation metadata must be an object')
        return value
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise GitIsolationError(f'Cannot read isolation configuration: {path}') from exc


def _origin(project):
    project = _project(project)
    for parent in (project, *project.parents):
        pointer = _read(parent / '.tequio/git-isolation-origin.json')
        if pointer is not None:
            if not isinstance(pointer, dict) or not isinstance(pointer.get('controller'), str):
                raise GitIsolationError('Invalid lane controller pointer')
            origin = _project(pointer['controller'])
            state = _state(origin)
            if not state or not any(Path(x['path']).resolve() == parent for x in state.get('lanes', [])):
                raise GitIsolationError('Lane is not registered with its controller')
            return origin
        if (parent / '.tequio/git-isolation.json').exists():
            return parent
    return project


def _state(project):
    value = _read(project / '.tequio/git-isolation.json')
    if value is None:
        return {'version': 1, 'enabled': False, 'controller': str(project), 'lanes': []}
    if (not isinstance(value, dict) or value.get('version') != 1
            or not isinstance(value.get('enabled'), bool)
            or value.get('controller') != str(project)
            or not isinstance(value.get('lanes'), list)
            or any(not isinstance(item, dict) or any(not isinstance(item.get(key), str)
                   for key in ('lane', 'path', 'branch', 'worktree', 'base_commit'))
                   for item in value.get('lanes', []))):
        raise GitIsolationError('Unsupported isolation configuration')
    return value


@contextmanager
def _locked(project):
    folder = project / '.tequio'
    if folder.is_symlink():
        raise GitIsolationError('Private isolation directory must not be a symlink')
    folder.mkdir(exist_ok=True)
    lock = folder / 'git-isolation.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise GitIsolationError(f'Isolation operation already locked: {lock}; inspect before manually removing a stale lock') from exc
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        lock.unlink()


def _save(project, state):
    folder = project / '.tequio'
    fd, name = tempfile.mkstemp(prefix='git-isolation-', dir=folder)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(state, stream, indent=2)
            stream.write('\n')
        os.replace(name, folder / 'git-isolation.json')
    finally:
        if os.path.exists(name):
            os.unlink(name)


def detect(project):
    """Read-only discovery, including linked worktrees and repository subfolders."""
    project = _project(project)
    controller = _origin(project)
    state = _state(controller)
    try:
        root = _git(project, 'rev-parse', '--show-toplevel')
        common = _git(project, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    except GitIsolationError:
        return {'repository': False, 'enabled': False, 'controller': str(controller), 'control_root': str(controller), 'mode': 'shared-folder'}
    return {'repository': True, 'repository_root': root, 'git_common_dir': common,
            'controller': str(controller), 'control_root': str(controller), 'enabled': bool(state['enabled']),
            'mode': 'git-worktrees' if state['enabled'] else 'shared-folder'}


def configure(project, enabled):
    """Persist explicit opt-in privately; never initialize a repository."""
    if not isinstance(enabled, bool):
        raise GitIsolationError('enabled must be a boolean')
    controller = _origin(project)
    if enabled and not detect(controller)['repository']:
        raise GitIsolationError('Git isolation requires an existing repository')
    if enabled:
        # Ignore rules must be supplied by the owner; do not alter Git metadata.
        _git(controller, 'check-ignore', '--no-index', '.tequio/')
        tracked = _git(controller, 'ls-files', '--', '.tequio')
        if tracked:
            raise GitIsolationError('Git isolation requires an untracked, ignored .tequio directory')
    with _locked(controller):
        state = _state(controller)
        state['enabled'] = enabled
        _save(controller, state)
    return detect(controller)


def _inspection_git(path, *args):
    """Bound each observation and prevent Git's optional index refresh writes."""
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env['GIT_OPTIONAL_LOCKS'] = '0'
    try:
        result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(path), *args], text=True,
                                capture_output=True, check=False, timeout=5, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitIsolationError('Git observation unavailable') from exc
    if result.returncode:
        raise GitIsolationError('Git observation unavailable')
    return result.stdout.rstrip('\n')


def _has_symlink(path):
    return any(part.is_symlink() for part in (path, *path.parents))


def _observe_lane(lane, controller_common):
    path = Path(lane['path'])
    result = {**lane, 'exists': path.is_dir(), 'actual': None,
              'health': 'unavailable', 'issues': []}
    if (_has_symlink(path) or _has_symlink(Path(lane['worktree']))
            or (Path(lane['worktree']) / '.git').is_symlink()):
        result['issues'] = ['symlink-path']
        return result
    if not result['exists']:
        result.update(health='missing', issues=['missing'])
        return result
    try:
        root = Path(_inspection_git(path, 'rev-parse', '--show-toplevel')).resolve()
        common = Path(_inspection_git(path, 'rev-parse', '--path-format=absolute',
                                      '--git-common-dir'))
        # Resolve actual Git metadata, not merely the registered directory name.
        git_dir = Path(_inspection_git(path, 'rev-parse', '--absolute-git-dir'))
        if _has_symlink(git_dir) or _has_symlink(common):
            raise GitIsolationError('Symlink Git metadata')
        common = common.resolve()
        head = _inspection_git(path, 'rev-parse', '--verify', 'HEAD')
        branch = _inspection_git(path, 'rev-parse', '--abbrev-ref', 'HEAD')
        branch = None if branch == 'HEAD' else branch
        status = _inspection_git(path, 'status', '--porcelain=v1', '-z',
                                 '--untracked-files=all', '--ignore-submodules=none')
        operations = [name for name in ('MERGE_HEAD', 'rebase-merge', 'rebase-apply',
                                       'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'sequencer')
                      if (git_dir / name).exists()]
        codes = []
        entries = iter(status.split('\0'))
        for entry in entries:
            if not entry:
                continue
            code = entry[:2]
            codes.append(code)
            if 'R' in code or 'C' in code:
                next(entries, None)  # porcelain -z rename/copy source pathname
        conflicted = any(code in ('DD', 'AU', 'UD', 'UA', 'DU', 'AA', 'UU')
                         for code in codes)
        result['actual'] = {'repository_root': str(root), 'git_common_dir': str(common),
                            'branch': branch, 'head': head, 'dirty': bool(status),
                            'index_dirty': any(code[0] not in (' ', '?', '!') for code in codes),
                            'worktree_dirty': any(code[1] not in (' ', '?', '!') for code in codes),
                            'untracked': '??' in codes,
                            'conflicted': conflicted, 'in_progress': operations}
        issues = []
        if controller_common is None:
            issues.append('unavailable')
        elif common != controller_common or root != Path(lane['worktree']).resolve():
            issues.append('foreign')
        if branch is None:
            issues.append('detached')
        elif branch != lane['branch']:
            issues.append('branch-mismatch')
        if status:
            issues.append('dirty')
        result.update(health=issues[0] if issues else 'healthy', issues=issues)
    except GitIsolationError:
        result['issues'] = ['unavailable']
    return result


def inspect_lanes(project):
    """Read-only snapshot of expected registry identity and actual lane health.

    Dirty work is an observation, never acceptance or rejection of a task.
    """
    controller = _origin(project)
    state = _state(controller)
    try:
        common = Path(_inspection_git(controller, 'rev-parse', '--path-format=absolute',
                                      '--git-common-dir')).resolve()
    except GitIsolationError:
        common = None
    return {**detect(project), 'lanes': [_observe_lane(lane, common)
                                        for lane in state['lanes']]}


def create_lane(project, lane, base='HEAD'):
    """Create one branch/worktree; preserve and report all partial Git side effects."""
    if not isinstance(lane, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', lane):
        raise GitIsolationError('Lane must contain 1-64 letters, digits, underscores or hyphens')
    if not isinstance(base, str) or not base or base.startswith('-') or '\x00' in base:
        raise GitIsolationError('Invalid base reference')
    controller = _origin(project)
    initial = detect(controller)
    if not initial['repository'] or not initial['enabled']:
        raise GitIsolationError('Git isolation is disabled; shared-folder mode remains available')
    with _locked(controller):
        info = detect(controller)
        if not info['repository'] or not info['enabled']:
            raise GitIsolationError('Git isolation is disabled; shared-folder mode remains available')
        root = Path(info['repository_root']).resolve()
        # Ignore only our private files, never other user changes.
        status = _git(root, 'status', '--porcelain', '--untracked-files=all')
        if status:
            raise GitIsolationError('Base worktree has changes; preserve or commit them before creating a lane')
        commit = _git(root, 'rev-parse', '--verify', '--end-of-options', base + '^{commit}')
        branch = 'tequio/' + lane
        _git(root, 'check-ref-format', '--branch', branch)
        target = root.parent / (root.name + '-tequio-' + lane)
        state = _state(controller)
        if target.exists() or target.is_symlink() or any(x['lane'] == lane for x in state['lanes']):
            raise GitIsolationError('Lane or target already exists')
        refs = _git(root, 'for-each-ref', '--format=%(refname)', 'refs/heads/' + branch)
        if refs:
            raise GitIsolationError('Lane branch already exists')
        # Git performs its own atomic ref locking; no destructive rollback is attempted.
        try:
            _git(root, 'worktree', 'add', '-b', branch, str(target), commit)
            relative = controller.relative_to(root)
            lane_project = target / relative
            component = target
            for part in relative.parts:
                component = component / part
                if component.is_symlink():
                    raise GitIsolationError('Lane project path must not contain symlinks')
            try:
                lane_project.resolve().relative_to(target.resolve())
            except ValueError as exc:
                raise GitIsolationError('Lane project path escapes its worktree') from exc
            lane_project.mkdir(parents=True, exist_ok=True)
            private = lane_project / '.tequio'
            if private.is_symlink():
                raise GitIsolationError('Lane private directory must not be a symlink')
            _git(lane_project, 'check-ignore', '--no-index', '.tequio/')
            private.mkdir(exist_ok=True)
            pointer = private / 'git-isolation-origin.json'
            with pointer.open('x') as stream:
                json.dump({'controller': str(controller)}, stream)
            record = {'lane': lane, 'branch': branch, 'path': str(lane_project),
                      'worktree': str(target), 'base_commit': commit}
            state['lanes'].append(record)
            _save(controller, state)
            return record
        except (OSError, GitIsolationError) as exc:
            raise GitIsolationError(f'Lane creation failed; inspect preserved branch {branch} and worktree {target} before retrying: {exc}') from exc
