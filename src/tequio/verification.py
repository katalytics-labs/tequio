"""Local POSIX verification serialization and durable, conservative observations."""
import contextlib
import fcntl
import json
import os
import secrets
import time

from .core import Error, inside, name, require

TERMINAL = {'completed', 'stopped', 'reconciled'}


def paths(workspace, tid):
    base = 'verification/' + name(tid)
    return inside(workspace.path, base + '.lock'), inside(workspace.path, base + '.json')


def save(path, record):
    temporary = path.with_name(path.name + '.' + secrets.token_hex(6) + '.tmp')
    try:
        with temporary.open('x') as handle:
            json.dump(record, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def read(path):
    if not path.exists(): return None
    try:
        record = json.loads(path.read_text())
        require(isinstance(record, dict) and record.get('version') == 1 and
                record.get('state') in TERMINAL | {'preparing', 'launching', 'running'},
                'Invalid verification state')
        for key in ('child_pid', 'process_group'):
            require(record.get(key) is None or (type(record[key]) is int and record[key] > 1),
                    'Invalid verification process identity')
        return record
    except (OSError, ValueError, TypeError, Error):
        return {'state': 'unknown', 'issue': 'unreadable attempt metadata'}


def group_live(record):
    if not record or not record.get('process_group'): return False
    try: os.killpg(record['process_group'], 0)
    except ProcessLookupError: return False
    except PermissionError: return True
    return True


@contextlib.contextmanager
def guard(workspace, tid, stopped_check=False, reason='', acceptance=False):
    lock, metadata = paths(workspace, tid)
    lock.parent.mkdir(exist_ok=True)
    with lock.open('a+') as handle:
        try: fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise Error('Verification operation active; inspect actual check handles')
        try:
            record = read(metadata)
            require(not group_live(record), 'Observed verification process group still live; recovery cannot kill or override it')
            require(not acceptance or not record or record['state'] in {'completed', 'reconciled'},
                    'Unresolved verification result; verify again or explicitly reconcile recovery')
            if record and record['state'] not in TERMINAL:
                require(not acceptance, 'Unresolved verification attempt; verify again or explicitly reconcile recovery')
                # A recorded child whose group disappeared is observable local cessation.
                unknown = not record.get('process_group')
                require(not unknown or (stopped_check and len(reason.strip()) >= 20),
                        'Unresolved verification launch; inspect handles and use --stopped-check with substantive reason')
            yield metadata
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def status(workspace, tid):
    """No files/directories/state are created or changed by this observation."""
    lock, metadata = paths(workspace, tid)
    held = False
    if lock.exists():
        with lock.open('r') as handle:
            try: fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: held = True
            else: fcntl.flock(handle, fcntl.LOCK_UN)
    record = read(metadata)
    public = {key: record.get(key) for key in ('attempt', 'state', 'started_at', 'updated_at',
              'controller_pid', 'child_pid', 'process_group', 'child_observed_at', 'issue')} if record else None
    return {'task': tid, 'lock_held': held, 'attempt': public,
            'observed_group_live': group_live(record),
            'warning': 'Local observations only; lease expiry and absent lock do not prove external work stopped'}


def reconcile(metadata, reason):
    """Caller holds operation lock and has validated recovery eligibility in its transaction."""
    record = read(metadata)
    if record and record['state'] not in TERMINAL:
        require(not group_live(record), 'Observed verification process group still live')
        unknown = not record.get('process_group')
        record.update(version=1, attempt=record.get('attempt') or secrets.token_hex(16), state='reconciled', reconciled_at=time.time(), reason=reason,
                      reconciliation='explicit-stopped-acknowledgement' if unknown else 'observed-group-absent')
        save(metadata, record)
