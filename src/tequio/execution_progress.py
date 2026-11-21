"""Read-only, fixed-field execution observations; no acceptance or spending gate."""
import contextlib
import json
import math
import sqlite3
import time

from .core import Error, Workspace, name
from .run_context import policy, valid_context

_UNSET = object()

_STATES = frozenset(('draft', 'ready', 'running', 'review', 'blocked', 'done', 'superseded'))
_COUNTERS = ('published_verifications', 'successful_verifications', 'documentation_records',
             'correctness_reviews', 'security_reviews', 'completion_records')


def _limits(path):
    """Load and validate the same policy bytes; never export private fields."""
    # policy() supplies canonical state/digest; a second read must match that digest.
    from .run_context import digest
    observed = policy(path)
    if observed['state'] != 'valid':
        return observed, 'policy-' + observed['state'], None
    try:
        value = json.loads((path / 'run-policy.json').read_bytes())
        if digest(value) != observed['digest']:
            return {'state': 'changed-during-read', 'digest': None}, 'policy-changed-during-read', None
    except (OSError, ValueError, UnicodeError, TypeError):
        return {'state': 'changed-during-read', 'digest': None}, 'policy-changed-during-read', None
    limits = value.get('execution_checkpoints')
    return observed, 'configured' if limits is not None else 'legacy-unbudgeted', limits


def _finite_time(value):
    try:
        return type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def _clock(path, current_policy, now, checkpoint=_UNSET):
    try:
        if checkpoint is not _UNSET:
            if checkpoint.get('issue'):return ('missing' if checkpoint['issue']=='missing' else 'unusable'), None
            saved = json.loads(checkpoint['raw'])
        else:
            saved = json.loads((path / 'checkpoint.json').read_bytes())
    except FileNotFoundError:
        return 'missing', None
    except (OSError, ValueError, UnicodeError):
        return 'unusable', None
    required = {'summary': str, 'next_action': str, 'project_snapshot': str, 'inputs': str, 'status': dict}
    if (not isinstance(saved, dict) or type(saved.get('checkpoint_version')) is not int
            or saved['checkpoint_version'] != 1
            or any(not isinstance(saved.get(k), kind) for k, kind in required.items())
            or not valid_context(saved.get('context'))):
        return 'unusable', None
    if current_policy['state'] != 'valid':
        return 'policy-unavailable', None
    if saved['context']['policy'] != current_policy:
        return 'policy-drift', None
    at = saved.get('at')
    if not _finite_time(at) or not _finite_time(now) or now < at:
        return 'invalid-time', None
    return 'observed', now - at


def progress(project, workspace, task=None, *, now=None, _checkpoint=_UNSET):
    """Count historical CLI publications, not report files or hidden host activity."""
    if task is not None:
        name(task)
    w = Workspace(project, workspace)
    with contextlib.closing(sqlite3.connect((w.path / 'state.sqlite3').as_uri() + '?mode=ro', uri=True)) as con:
        con.execute('BEGIN')  # One read snapshot; no schema/receipt/process mutation.
        rows = con.execute('SELECT id,status FROM tasks' + (' WHERE id=?' if task else '') + ' ORDER BY id',
                           (task,) if task else ()).fetchall()
        if task and not rows:
            raise Error('Task not found')
        events = con.execute("SELECT kind,data FROM events WHERE kind IN ('verified','reviewed','documentation-recorded','completed') ORDER BY seq").fetchall()
    tasks = {name(tid): {'task': tid, 'lifecycle': state if state in _STATES else 'invalid',
                         **dict.fromkeys(_COUNTERS, 0)} for tid, state in rows}
    issues = sum(item['lifecycle'] == 'invalid' for item in tasks.values())
    for kind, raw in events:
        try:
            data = json.loads(raw)
            if not isinstance(data, dict) or not isinstance(data.get('id'), str):
                raise ValueError('Invalid event')
            if data['id'] not in tasks:
                if task is None:
                    issues += 1
                continue
            item = tasks[data['id']]
            if kind == 'verified':
                item['published_verifications'] += 1
                if type(data.get('passed')) is not bool:
                    issues += 1
                elif data['passed']:
                    item['successful_verifications'] += 1
            elif kind == 'documentation-recorded':
                item['documentation_records'] += 1
            elif kind == 'completed':
                item['completion_records'] += 1
            elif data.get('kind') in ('correctness', 'security'):
                item[data['kind'] + '_reviews'] += 1
            else:
                issues += 1
        except (ValueError, TypeError, UnicodeError):
            issues += 1
    current_policy, state, limits = _limits(w.path)
    clock_state, elapsed = _clock(w.path, current_policy, time.time() if now is None else now, _checkpoint)
    reasons = []
    if state != 'configured':
        reasons.append({'reason': state})
    else:
        if elapsed is None:
            reasons.append({'reason': 'checkpoint-time-unknown'})
        elif elapsed >= limits['wall_minutes'] * 60:
            reasons.append({'reason': 'wall-time-checkpoint'})
        for item in tasks.values():
            if (item['lifecycle'] not in ('done', 'superseded')
                    and item['published_verifications'] >= limits['max_verifications_per_task']):
                reasons.append({'reason': 'verification-checkpoint', 'task': item['task']})
    if issues:
        reasons.append({'reason': 'observation-incomplete'})
    return {'schema_version': 1, 'tasks': list(tasks.values()),
            'recorded_tasks': len(tasks), 'recorded_done': sum(t['lifecycle'] == 'done' for t in tasks.values()),
            'observation_issues': issues,
            'execution_checkpoints': {'state': state, 'limits': limits,
                                      'clock': clock_state, 'elapsed_wall_seconds': elapsed,
                                      'checkpoint_required': bool(reasons), 'reasons': reasons},
            'usage': {'tokens': None, 'cost': None, 'source': 'unavailable'},
            'limits': 'Historical CLI publications only, not current acceptance, all launched attempts, external effects, arbitrary agent reviews or active work time. Checkpoint advice neither grants authorization nor blocks lifecycle transitions. Usage is unknown; use proof for current evidence.'}


def status_observation(workspace, *, checkpoint=_UNSET):
    """Reuse progress semantics without duplicating its task list in Status."""
    try:
        observed = progress(workspace.project, workspace.path.name, _checkpoint=checkpoint)
        return {k: observed[k] for k in ('execution_checkpoints', 'usage')}
    except (Error, OSError, sqlite3.Error, ValueError, KeyError, TypeError, AttributeError, IndexError):
        return {'execution_checkpoints': {
                    'state': 'unavailable', 'limits': None, 'clock': 'unavailable',
                    'elapsed_wall_seconds': None, 'checkpoint_required': True,
                    'reasons': [{'reason': 'observation-incomplete'}]},
                'usage': {'tokens': None, 'cost': None, 'source': 'unavailable'}}
