"""Explicit opt-in freshness contracts; absent contracts retain global semantics."""
import json
import sqlite3
import contextlib
from pathlib import Path

RUNTIME_FIELDS = {'inputs', 'specialist_bindings', 'documentation_baseline',
                  'documentation_receipt', 'result_hash', 'result_snapshot'}


def scoped(task):
    return task.get('freshness', {}).get('mode') == 'scoped-v1'


def validate(workspace, task):
    from .core import inside, require
    policy = task.get('freshness')
    if policy is None:
        return
    require(isinstance(policy, dict) and policy.get('mode') in ('global', 'scoped-v1'), 'Unknown freshness contract')
    if policy['mode'] == 'global':
        return
    require('reads' in task and 'writes' in task, 'Scoped freshness requires explicit reads and writes')
    require(policy.get('independent') is True, 'Scoped freshness requires explicit independence assessment')
    for key in ('shared_contracts', 'config', 'mandatory_context'):
        paths = policy.get(key)
        require(isinstance(paths, list), 'Scoped freshness requires explicit ' + key)
        for relative in paths:
            require(isinstance(relative, str) and relative and not any(c in relative for c in '*?['), 'Use concrete freshness paths')
            require(bool(Path(relative).parts), 'Use concrete freshness paths')
            p = inside(workspace.path if key == 'mandatory_context' else workspace.project, relative)
            if key != 'mandatory_context':
                require(p.parts and not p.is_relative_to(workspace.project / '.tequio') and Path(relative).parts[0] not in ('.agents', '.git'), 'Reserved freshness resource')
            else:
                require(Path(relative).parts[0] in ('briefs', 'analysis', 'plans', 'specs'), 'Mandatory context must be a phase source')


def resources(task):
    policy = task.get('freshness', {})
    return sorted(set(task.get('reads', []) + task.get('candidate_paths', []) + policy.get('shared_contracts', []) + policy.get('config', []) + task.get('documentation', {}).get('paths', [])))


def inputs(workspace, task, trail=()):
    from .core import digest, inside, tree_hash, require
    if not scoped(task):
        from .revision import salt
        return salt(workspace, task, workspace.inputs())
    validate(workspace, task)
    require(task['id'] not in trail, 'Dependency cycle in freshness')
    sources = sorted(set(['briefs', 'specs'] + [x.split('#')[0] for x in task['sources']] + task['freshness']['mandatory_context']))
    phase = []
    for relative in sources:
        p = inside(workspace.path, relative)
        phase.append((relative, p.stat().st_mode & 0o777 if p.exists() else None, tree_hash(p, reject_symlinks=True) if p.is_dir() else digest(p.read_bytes()) if p.is_file() else 'absent'))
    with contextlib.closing(sqlite3.connect('file:' + str(workspace.path / 'state.sqlite3') + '?mode=ro', uri=True)) as con:
        config = con.execute("SELECT value FROM meta WHERE key='config'").fetchone()[0]
    definition = {k: v for k, v in task.items() if k not in RUNTIME_FIELDS}
    from .revision import salt
    return salt(workspace, task, digest(json.dumps([definition, phase, config, workspace.specialist_bindings(task)], sort_keys=True).encode()))


def snapshot(workspace, task, trail=()):
    from .core import digest, tree_hash, require
    if not scoped(task):
        from .revision import salt
        base = salt(workspace, task, tree_hash(workspace.project, project=True))
        if task.get('kind') == 'release':
            return digest(json.dumps([base, workspace.resource_hash(resources(task) + task['writes'])]).encode())
        if task.get('candidate_paths'):
            return digest(json.dumps([base, workspace.resource_hash(task['candidate_paths'])]).encode())
        return base
    require(task['id'] not in trail, 'Dependency cycle in freshness')
    with contextlib.closing(sqlite3.connect('file:' + str(workspace.path / 'state.sqlite3') + '?mode=ro', uri=True)) as con:
        deps = []
        for tid in workspace.effective_dependencies(task):
            row = con.execute('SELECT body,status FROM tasks WHERE id=?', (tid,)).fetchone()
            require(row, 'Missing freshness dependency')
            deps.append((json.loads(row[0]), row[1]))
    return digest(json.dumps([inputs(workspace, task), workspace.resource_hash(resources(task) + task['writes']),
        [(d['id'], state, d.get('result_hash'), snapshot(workspace, d, trail + (task['id'],))) for d, state in deps]], sort_keys=True).encode())
