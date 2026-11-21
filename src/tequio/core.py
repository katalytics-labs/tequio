"""Local lifecycle contracts. Instructions do the engineering; this module guards state."""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import sqlite3
import subprocess
import time

class Error(Exception):
    pass

def require(ok, message):
    if not ok:
        raise Error(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def load(path):
    return json.loads(Path(path).read_text())

def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + secrets.token_hex(5) + '.tmp')
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    os.replace(temporary, path)

def name(value):
    require(isinstance(value, str) and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', value), 'Invalid identifier')
    return value

def inside(root, relative):
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), 'Path must be relative')
    require('..' not in Path(relative).parts, 'Parent traversal is forbidden')
    root = Path(root).resolve()
    result = root / relative
    require(result.resolve().is_relative_to(root), 'Path escapes root')
    # Refuse symlink traversal even when the destination happens to be contained.
    cursor = root
    for part in Path(relative).parts:
        cursor = cursor / part
        require(not cursor.is_symlink(), 'Symlink paths are not supported')
    return result

def tree_hash(root, project=False, reject_symlinks=False):
    root = Path(root)
    entries = [('.', root.stat().st_mode & 0o777)]
    excluded = {'.git', '.tequio', '.agents', '__pycache__', '.venv', 'node_modules', '.pytest_cache'} if project else set()
    for base, dirs, files in os.walk(root, followlinks=False):
        if reject_symlinks:
            require(not any((Path(base) / entry).is_symlink() for entry in dirs + files), 'Symlink descendants are not supported in freshness resources')
        dirs[:] = sorted(d for d in dirs if d not in excluded)
        for d in dirs:
            p = Path(base) / d
            entries.append((str(p.relative_to(root)) + '/', p.lstat().st_mode & 0o777))
        for f in sorted(files + [d for d in dirs if (Path(base) / d).is_symlink()]):
            p = Path(base) / f
            rel = str(p.relative_to(root))
            if project and rel == 'bin/tequio':
                continue
            entries.append((rel, p.lstat().st_mode & 0o777, 'symlink:' + os.readlink(p) if p.is_symlink() else digest(p.read_bytes())))
    return digest(json.dumps(entries, separators=(',', ':')).encode())

SCHEMA = '''
CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, body TEXT NOT NULL, status TEXT NOT NULL,
 owner TEXT, token TEXT, lease REAL, baseline TEXT, checks TEXT, reviews TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, at REAL NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL);
'''

class Workspace:
    def __init__(self, project, workspace):
        self.project = Path(project).resolve()
        self.path = inside(self.project, '.tequio/workspaces/' + name(workspace))
        require((self.path / 'state.sqlite3').is_file(), 'Workspace missing; run workspace first')
        require(not (self.path / 'state.sqlite3').is_symlink(), 'Symlink database refused')
        from .revision import check_version
        check_version(self)

    @classmethod
    def create(cls, project, workspace, brief):
        project = Path(project).resolve()
        require(project.is_dir(), 'Project directory missing')
        path = inside(project, '.tequio/workspaces/' + name(workspace))
        require(not path.exists(), 'Workspace already exists')
        source = Path(brief)
        require(source.is_file() and source.read_text().strip(), 'A nonempty brief is required')
        path.mkdir(parents=True)
        for d in ['briefs', 'analysis', 'plans', 'specs', 'tasks', 'evidence', 'reviews', 'journal']:
            (path / d).mkdir()
        (path / 'briefs/brief.md').write_text(source.read_text())
        con = sqlite3.connect(path / 'state.sqlite3')
        con.executescript(SCHEMA)
        con.execute('INSERT INTO meta VALUES (?,?)', ('config', json.dumps({'max_parallel': 3})))
        con.commit()
        con.close()
        return cls(project, workspace)

    @contextlib.contextmanager
    def transaction(self):
        con = sqlite3.connect(self.path / 'state.sqlite3', timeout=10, isolation_level=None)
        con.row_factory = sqlite3.Row
        previous = getattr(self, '_revision_connection', None)
        self._revision_connection = con
        try:
            con.execute('PRAGMA foreign_keys=ON')
            con.execute('BEGIN IMMEDIATE')
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            self._revision_connection = previous
            con.close()

    def event(self, con, kind, data):
        con.execute('INSERT INTO events(at,kind,data) VALUES (?,?,?)', (time.time(), kind, json.dumps(data)))

    def inputs(self):
        return digest(''.join(tree_hash(self.path / d) for d in ['briefs', 'analysis', 'plans', 'specs']).encode())

    def task_inputs(self, task):
        from .freshness import inputs
        return inputs(self, task)

    def effective_dependencies(self, task, con=None):
        from .revision import dependencies
        return dependencies(self, task, con)

    def expected_inputs(self, task, con=None):
        from .revision import expected_inputs
        return expected_inputs(self, task, con)

    def task_snapshot(self, task):
        from .freshness import snapshot
        return snapshot(self, task)

    def task_current(self, con, task):
        from .freshness import scoped
        if not scoped(task):
            self.current(con)

    def phase_hash(self, phase):
        dirs = ['briefs', 'analysis', 'specs'] if phase == 'analysis' else ['briefs', 'analysis', 'specs', 'plans']
        return digest(''.join(tree_hash(self.path / d) for d in dirs).encode())

    def record(self, phase):
        require(phase in ('analysis', 'plan'), 'Unknown phase')
        folder = 'analysis' if phase == 'analysis' else 'plans'
        docs = list((self.path / folder).glob('*.md'))
        require(docs and all(p.read_text().strip() for p in docs), 'Write substantive phase artifacts first')
        with self.transaction() as con:
            if phase == 'plan':
                old = con.execute("SELECT value FROM meta WHERE key='analysis'").fetchone()
                require(old and old[0] == self.phase_hash('analysis'), 'Analysis missing or stale')
            con.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', (phase, self.phase_hash(phase)))
            self.event(con, 'phase-recorded', {'phase': phase})
        return {'phase': phase, 'fingerprint': self.phase_hash(phase), 'note': 'Receipt records files; semantic completeness requires review'}

    def current(self, con):
        for phase in ['analysis', 'plan']:
            row = con.execute('SELECT value FROM meta WHERE key=?', (phase,)).fetchone()
            require(row and row[0] == self.phase_hash(phase), phase + ' missing or stale; analyze/replan before implementation')

    def documentation_policy(self, task):
        policy = task.get('documentation')
        require(isinstance(policy, dict) and policy.get('mode') in ('update','not-needed'), 'Declare documentation impact: update or not-needed')
        require(isinstance(policy.get('reason'),str) and len(policy['reason'].strip()) >= 30, 'Explain documentation impact with a concrete reason')
        paths = policy.get('paths')
        require(isinstance(paths,list) and all(isinstance(x,str) and x for x in paths), 'Documentation paths must be a list')
        require(bool(paths) == (policy['mode']=='update'), 'Update requires paths; not-needed requires an empty path list')
        for path in paths:
            dest=inside(self.project,path)
            require(not any(c in path for c in '*?['), 'Documentation paths must be concrete files')
            require(Path(path).parts and Path(path).parts[0] not in ('.git','.tequio','.agents'), 'Documentation must not expose private toolkit state')
            require(any(dest.is_relative_to(inside(self.project,w)) for w in task['writes']), 'Documentation path must be inside task write ownership')
        return policy

    def validate_task(self, task):
        require(isinstance(task, dict), 'Task must be an object')
        name(task.get('id'))
        from .reporting import capture_policy
        capture_policy(task)
        from .freshness import validate
        validate(self, task)
        for key in ['title', 'outcome', 'scope', 'exclusions', 'handoff']:
            require(isinstance(task.get(key), str) and task[key].strip(), 'Missing task field: ' + key)
        for key in ['sources', 'acceptance', 'checks', 'writes']:
            require(isinstance(task.get(key), list) and task[key], 'Missing nonempty list: ' + key)
        require(isinstance(task.get('depends_on', []), list), 'depends_on must be a list')
        require(isinstance(task.get('reads', []), list), 'reads must be a list')
        require(task.get('risk') in ('normal', 'security'), 'risk must be normal or security')
        from .security import validate as validate_security
        validate_security(self, task)
        require(task.get('stage', 'ready') in ('draft', 'ready'), 'stage must be draft or ready')
        for source in task['sources']:
            p = inside(self.path, source.split('#')[0])
            require(p.is_file(), 'Missing task source: ' + source)
        for resource in task['writes'] + task.get('reads', []):
            require(not any(c in resource for c in '*?['), 'Use directory/file resources, not globs')
            p = inside(self.project, resource)
            require(not p.is_relative_to(self.project / '.tequio'), 'Product task cannot own toolkit state')
            require(Path(resource).parts and Path(resource).parts[0] not in ('.git', '.agents'), 'Reserved task resource')
        require(isinstance(task.get('specialists', []), list), 'specialists must be a list')
        require(task.get('kind', 'implementation') in ('research','implementation','release'), 'Task kind must be research, implementation or release')
        for spec in task.get('specialists', []):
            require(isinstance(spec, str) and spec.strip(), 'Invalid specialist')
        if task.get('stage','ready') == 'ready':
            self.documentation_policy(task)
            self.specialist_bindings(task)
        for acceptance in task['acceptance']:
            require(isinstance(acceptance, str) and acceptance.strip(), 'Invalid acceptance criterion')
        for argv in task['checks']:
            require(isinstance(argv, list) and argv and all(isinstance(a, str) and a for a in argv), 'Each check must be a nonempty argument vector')
        for dep in task.get('depends_on', []):
            name(dep)
            require(dep != task['id'], 'Task cannot depend on itself')

    def specialist_bindings(self, task):
        bindings = {}
        for sid in task.get('specialists', []):
            from .specialists import Factory
            bindings[sid] = Factory(self).resolve(sid, task.get('kind','implementation'))
        return bindings

    def import_tasks(self, path):
        tasks = load(path)
        require(isinstance(tasks, list) and tasks, 'Expected nonempty task array')
        for task in tasks:
            self.validate_task(task)
        require(len({t['id'] for t in tasks}) == len(tasks), 'Duplicate task IDs')
        with self.transaction() as con:
            self.current(con)
            from .task_review import TaskReview
            reviewed_batch = TaskReview(self).require_import(con, tasks)
            old = {r['id']: json.loads(r['body']) for r in con.execute('SELECT * FROM tasks')}
            require(not any(t['id'] in old for t in tasks), 'Task IDs immutable; use replan and new IDs')
            all_tasks = {**old, **{t['id']: t for t in tasks}}
            def visit(tid, trail):
                require(tid in all_tasks, 'Unknown dependency: ' + tid)
                require(tid not in trail, 'Dependency cycle')
                for dep in self.effective_dependencies(all_tasks[tid],con):
                    visit(dep, trail + [tid])
            for task in tasks:
                visit(task['id'], [])
            for task in tasks:
                body = {**task, 'inputs': self.task_inputs(task), 'specialist_bindings': self.specialist_bindings(task) if task.get('stage','ready')=='ready' else {}}
                con.execute('INSERT INTO tasks(id,body,status) VALUES (?,?,?)', (task['id'], json.dumps(body), task.get('stage', 'ready')))
            self.event(con, 'tasks-imported', {'ids': [t['id'] for t in tasks], 'reviewed_batch': reviewed_batch})
        for task in tasks:
            write(inside(self.path, 'tasks/' + task['id'] + '.json'), task)
        return {'imported': [t['id'] for t in tasks]}

    @staticmethod
    def overlaps(a, b):
        a, b = Path(a), Path(b)
        return a == b or a.is_relative_to(b) or b.is_relative_to(a)

    def dependency_issue(self, con, task, trail=()):
        """First causal stale prerequisite, without guessing old component hashes."""
        if task['id'] in trail:
            return 'dependency ' + task['id'] + ' cycle in evidence'
        for tid in self.effective_dependencies(task, con):
            row = con.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
            if not row or row['status'] != 'done':
                return 'dependency ' + tid + ' is incomplete or missing'
            try:
                body = json.loads(row['body'])
                issue = self.dependency_issue(con, body, trail + (task['id'],))
                if issue:
                    return issue
                if self.expected_inputs(body, con) != self.task_inputs(body):
                    return 'dependency ' + tid + ' task inputs changed'
                if body.get('result_hash') != self.resource_hash(body['writes']):
                    return 'dependency ' + tid + ' owned outputs changed'
                from .freshness import scoped
                if scoped(body) and body.get('result_snapshot') != self.task_snapshot(body):
                    return ('dependency ' + tid + ' scoped context snapshot changed '
                            '(reads/shared contracts/configuration/prerequisite context; '
                            'historical component hashes unavailable). Use reviewed fresh successors and an explicit unfinished-consumer rebind')
            except (Error, OSError, KeyError, ValueError, TypeError, sqlite3.Error):
                return 'dependency ' + tid + ' evidence unavailable or invalid; inspect current inputs, specialist qualification and resources'
        return None

    def dependencies_current(self, con, task, trail=()):
        return self.dependency_issue(con, task, trail) is None

    def ready(self, con, row, running):
        if row['status'] != 'ready':
            return False
        t = json.loads(row['body'])
        try:
            from .security import validate as validate_security
            validate_security(self, t, execution=True)
            if self.expected_inputs(t,con) != self.task_inputs(t):
                return False
            self.documentation_policy(t)
            if t.get('specialist_bindings', {}) != self.specialist_bindings(t): return False
        except (Error, OSError, KeyError, ValueError):
            return False
        if not self.dependencies_current(con, t):
            return False
        from .freshness import resources
        for active in running:
            other = json.loads(active['body'])
            if any(self.overlaps(a, b) for a in t['writes'] for b in other['writes'] + resources(other)):
                return False
            if any(self.overlaps(a, b) for a in resources(t) for b in other['writes']):
                return False
        return True

    @contextlib.contextmanager
    def claim_guard(self):
        lock = inside(self.project, '.tequio/claim.lock')
        with lock.open('a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def resource_hash(self, resources):
        values = []
        for relative in sorted(resources):
            p = inside(self.project, relative)
            value = tree_hash(p, reject_symlinks=True) if p.is_dir() else digest(p.read_bytes()) if p.is_file() else 'absent'
            values.append((relative, p.stat().st_mode & 0o777 if p.exists() else None, value))
        return digest(json.dumps(values).encode())

    def peer_claims(self):
        running = []
        for other in sorted((self.project / '.tequio/workspaces').iterdir()):
            if other == self.path or not other.is_dir():
                continue
            db = inside(self.project, str(other.relative_to(self.project)) + '/state.sqlite3')
            if not db.is_file():
                continue
            with contextlib.closing(sqlite3.connect('file:' + str(db) + '?mode=ro', uri=True)) as peer:
                peer.row_factory = sqlite3.Row
                running.extend(peer.execute("SELECT * FROM tasks WHERE status IN ('running','review')"))
        return running

    def claim(self, owner, task_id=None, lease=1800):
        name(owner)
        require(30 <= lease <= 86400, 'Lease must be 30..86400 seconds')
        with self.claim_guard(), self.transaction() as con:
            running = list(con.execute("SELECT * FROM tasks WHERE status IN ('running','review')"))
            running.extend(self.peer_claims())
            config = json.loads(con.execute("SELECT value FROM meta WHERE key='config'").fetchone()[0])
            require(len(running) < config['max_parallel'], 'Concurrency capacity reached')
            rows = list(con.execute('SELECT * FROM tasks ORDER BY rowid'))
            candidates = [x for x in rows if not task_id or x['id'] == task_id]
            row = next((x for x in candidates if self.ready(con, x, running)), None)
            if row is None:
                issue = next((issue for candidate in candidates if candidate['status'] == 'ready'
                              for issue in [self.dependency_issue(con, json.loads(candidate['body']))] if issue), None)
                raise Error('No ready nonconflicting task; ' + (issue or 'inspect status/dependencies/staleness'))
            from .verification import guard
            with guard(self, row['id']):
                pass
            body=json.loads(row['body'])
            self.task_current(con, body)
            policy=self.documentation_policy(body)
            body.setdefault('documentation_baseline',{path:(digest(inside(self.project,path).read_bytes()) if inside(self.project,path).is_file() else None) for path in policy['paths']})
            body.pop('documentation_receipt',None)
            con.execute('UPDATE tasks SET body=? WHERE id=?',(json.dumps(body),row['id']))
            token = secrets.token_hex(24)
            baseline = tree_hash(self.project, project=True)
            con.execute("UPDATE tasks SET status='running',owner=?,token=?,lease=?,baseline=?,checks=NULL,reviews=NULL WHERE id=?", (owner, token, time.time() + lease, baseline, row['id']))
            self.event(con, 'claimed', {'id': row['id'], 'owner': owner})
            return {'id': row['id'], 'owner': owner, 'token': token, 'workspace': str(self.path), 'task': body, 'lease_seconds': lease}

    def owned(self, con, tid, token, statuses=('running', 'review'), candidate_presence=False):
        row = con.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
        require(row is not None and row['status'] in statuses, 'Task not in expected active state')
        require(secrets.compare_digest(row['token'] or '', token), 'Owner token mismatch')
        require(row['lease'] > time.time(), 'Lease expired; inspect live work then explicitly recover')
        body = json.loads(row['body'])
        from .security import validate as validate_security
        validate_security(self, body, execution=True, candidate_presence=candidate_presence)
        self.task_current(con, body)
        require(self.expected_inputs(body,con) == self.task_inputs(body), 'Task inputs stale; replan')
        require(self.dependencies_current(con, body), 'Dependency evidence stale or incomplete')
        require(body.get('specialist_bindings', {}) == self.specialist_bindings(body), 'Specialist qualification changed; replan')
        return row

    def heartbeat(self, tid, token):
        with self.transaction() as con:
            row = con.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
            require(row and row['status'] in ('running', 'review') and secrets.compare_digest(row['token'] or '', token), 'Owner token mismatch or task inactive')
            drift = []
            try:
                body = json.loads(row['body'])
                from .security import validate as validate_security
                validate_security(self, body, execution=True)
                self.task_current(con, body)
                require(self.expected_inputs(body,con) == self.task_inputs(body), 'Task inputs stale; replan')
                require(self.dependencies_current(con, body), 'Dependency evidence stale or incomplete')
                require(body.get('specialist_bindings', {}) == self.specialist_bindings(body), 'Specialist qualification changed; replan')
            except (Error, OSError, ValueError, TypeError, KeyError):
                drift.append('Execution inputs, dependencies or qualifications changed; reconcile before verify/complete')
            con.execute('UPDATE tasks SET lease=? WHERE id=?', (time.time() + 1800, tid))
            self.event(con, 'heartbeat', {'id': tid, 'execution_drift': bool(drift)})
        return {'renewed': tid, 'execution_eligible': not drift, 'drift': drift}

    def verification_status(self, tid):
        from .verification import status
        return status(self, tid)

    def verify(self, tid, token, timeout=120):
        return self._verify(tid, token, timeout)

    def _verify(self, tid, token, timeout=120, *, summary=False):
        # Internal opt-in envelope captures publication identity under the guard.
        from .verification import guard, save
        require(1 <= timeout <= 3600, 'Check timeout outside 1..3600 seconds')
        with guard(self, tid) as metadata:
            with self.transaction() as con:
                row = self.owned(con, tid, token, candidate_presence=True)
                task = json.loads(row['body'])
                from .integration import Journal
                Journal(self).gate(con, tid)
                integration_before = Journal(self).classify(con, tid)
            attempt = {'version': 1, 'attempt': secrets.token_hex(16), 'state': 'preparing',
                       'started_at': time.time(), 'controller_pid': os.getpid(),
                       'child_pid': None, 'process_group': None}
            def record(state, **values):
                attempt.update(values, state=state, updated_at=time.time())
                save(metadata, attempt)
            record('preparing')
            try:
                before = self.task_snapshot(task)
                results = []
                diagnostics = []
                from .reporting import capture_policy, validate_check_receipt
                policy=capture_policy(task)
                if policy:
                    from .capture import CaptureBudget
                    budget=CaptureBudget(policy['max_bytes'])
                else:budget=None
                for index,argv in enumerate(task['checks'],1):
                    record('launching', child_pid=None, process_group=None)
                    if budget is not None:
                        result=budget.run_check(argv,self.project,timeout,index,lambda proc:record('running',child_pid=proc.pid,process_group=proc.pid,child_observed_at=time.time()))
                        record('stopped');results.append(result)
                        code={'launch-failed':'check-launch-failed','timeout':'check-timeout','limit-exceeded':'capture-limit-exceeded','capture-failed':'capture-failed'}.get(result['capture']['state'])
                        if code is None and result['exit_code']!=0:code='check-nonzero'
                        if code:diagnostics.append({'check':index,'code':code})
                        if budget.aborted:break
                        continue
                    proc = None
                    failure_code = None
                    try:
                        proc = subprocess.Popen(argv, cwd=self.project, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
                        record('running', child_pid=proc.pid, process_group=proc.pid, child_observed_at=time.time())
                        try:
                            stdout, stderr = proc.communicate(timeout=timeout)
                            result = {'argv': argv, 'exit_code': proc.returncode, 'stdout': stdout.decode(errors='replace'), 'stderr': stderr.decode(errors='replace')}
                            if proc.returncode != 0: failure_code = 'check-nonzero'
                        except subprocess.TimeoutExpired:
                            failure_code = 'check-timeout'
                            result = {'argv': argv, 'exit_code': None, 'error': 'timeout; process group terminated'}
                        finally:
                            try: os.killpg(proc.pid, signal.SIGKILL)
                            except ProcessLookupError: pass
                            proc.communicate()
                    except OSError as exc:
                        if proc is not None:
                            try: os.killpg(proc.pid, signal.SIGKILL)
                            except ProcessLookupError: pass
                            proc.communicate()
                            raise
                        failure_code = 'check-launch-failed'
                        result = {'argv': argv, 'exit_code': None, 'error': str(exc)}
                    except BaseException:
                        if proc is not None:
                            try: os.killpg(proc.pid, signal.SIGKILL)
                            except ProcessLookupError: pass
                            proc.communicate()
                        raise
                    record('stopped')
                    results.append(result)
                    if failure_code:
                        diagnostics.append({'check': len(results), 'code': failure_code})
                after = self.task_snapshot(task)
                receipt = {'task': tid, 'at': time.time(), 'snapshot': after, 'inputs': self.task_inputs(task), 'stable': before == after, 'results': results, 'passed': before == after and all(x['exit_code'] == 0 for x in results)}
                if budget is not None:
                    abort=budget.abort_state
                    complete=len(results)==len(task['checks']) and all(r['launched'] and r['capture']['complete'] for r in results)
                    state=abort or ('launch-failed' if any(not r['launched'] for r in results) else 'complete')
                    receipt.update(schema_version=2,capture={'version':1,'mode':'bounded-v1','max_bytes':policy['max_bytes'],'retained_bytes':budget.retained_bytes,'observed_bytes':budget.observed_bytes,'cleanup_discarded_bytes':budget.cleanup_discarded_bytes,'complete':complete,'state':state,'planned':len(task['checks']),'attempted':len(results),'executed':sum(r['launched'] for r in results),'skipped':[{'check':i,'reason':abort} for i in range(len(results)+1,len(task['checks'])+1)]})
                    receipt['passed']=receipt['stable'] and complete and all(r['exit_code']==0 for r in results)
                    validate_check_receipt(receipt,task)
                    require(len((json.dumps(receipt,indent=2,ensure_ascii=False)+'\n').encode())<=8*policy['max_bytes']+1048576,'Bounded receipt size limit exceeded')
                # An unchanged active owner may renew even after a long check exceeded its lease.
                self.heartbeat(tid, token)
                with self.transaction() as con:
                    self.owned(con, tid, token, candidate_presence=True)
                    from .integration import Journal
                    Journal(self).gate(con, tid)
                    integration_after = Journal(self).classify(con, tid)
                    require(integration_before == integration_after, 'Integration target changed during checks; verify again')
                    if integration_before is not None:
                        receipt['integration'] = {k:integration_before[k] for k in ('commit','head','epoch')}
                    if policy:
                        require(len((json.dumps(receipt,indent=2,ensure_ascii=False)+'\n').encode())<=8*policy['max_bytes']+1048576,'Bounded receipt size limit exceeded')
                    filename = 'evidence/' + tid + '-' + secrets.token_hex(6) + '.json'
                    write(inside(self.path, filename), receipt)
                    ref = {'path': filename, 'hash': digest((self.path / filename).read_bytes())}
                    con.execute('UPDATE tasks SET checks=?,reviews=NULL,status=? WHERE id=?', (json.dumps(ref), 'review' if receipt['passed'] else 'running', tid))
                    self.event(con, 'verified', {'id': tid, 'passed': receipt['passed'], 'receipt': ref})
                record('completed')
                if summary:
                    if not receipt['stable']:
                        diagnostics.append({'check': None, 'code': 'snapshot-unstable'})
                    return {'receipt': receipt, 'reference': ref, 'diagnostics': diagnostics}
                return receipt
            except BaseException:
                # Preserve launch/running uncertainty if hard interruption prevented observation.
                if attempt['state'] == 'preparing': record('stopped')
                raise

    def receipt(self, ref, *, max_bytes=None):
        p = inside(self.path, ref['path'])
        require(p.is_file(), 'Receipt missing or altered')
        if max_bytes is None:
            require(digest(p.read_bytes()) == ref['hash'], 'Receipt missing or altered')
            return load(p)
        require(p.stat().st_size<=max_bytes,'Bounded receipt size limit exceeded')
        with p.open('rb') as handle:raw=handle.read(max_bytes+1)
        require(len(raw)<=max_bytes and digest(raw)==ref['hash'],'Bounded receipt altered or oversized')
        return json.loads(raw)

    def check_receipt(self, task, ref, *, current=False):
        from .reporting import capture_policy, validate_check_receipt
        policy=capture_policy(task)
        # Preserve the legacy call shape for existing integrations/mocks.
        receipt=self.receipt(ref,max_bytes=8*policy['max_bytes']+1048576) if policy else self.receipt(ref)
        require(isinstance(receipt,dict),'Invalid check receipt')
        validate_check_receipt(receipt,task)
        if policy and current:require(receipt['inputs']==self.task_inputs(task),'Check inputs stale')
        return receipt

    def documentation_state(self, body, snapshot=None):
        try:
            self.documentation_policy(body)
            ref=body.get('documentation_receipt')
            require(ref, 'Documentation reconciliation not recorded')
            receipt=self.receipt(ref)
            report=inside(self.path,receipt['report'])
            require(report.is_file() and digest(report.read_bytes())==receipt['report_hash'], 'Documentation report altered')
            for relative,expected in receipt.get('doc_hashes',{}).items():
                file=inside(self.project,relative)
                require(file.is_file() and digest(file.read_bytes())==expected,'Declared documentation changed after reconciliation')
            require(receipt['snapshot']==(self.task_snapshot(body)) and receipt['inputs']==self.task_inputs(body), 'Documentation reconciliation stale')
            return {'state':'current','receipt_hash':ref['hash']}
        except (Error,OSError,KeyError,TypeError,ValueError) as exc:
            return {'state':'outstanding','reason':str(exc)}

    def document(self, tid, token, report):
        report_path=inside(self.path,report)
        data=load(report_path)
        require(isinstance(data,dict) and isinstance(data.get('summary'),str) and len(data['summary'].strip())>=60, 'Substantive documentation reconciliation summary required')
        require(data.get('deviations')==[], 'Resolve or replan deviations before recording documentation')
        from .verification import guard
        with guard(self, tid, acceptance=True), self.transaction() as con:
            row=self.owned(con,tid,token,('review',))
            task=json.loads(row['body']);policy=self.documentation_policy(task)
            checks=self.check_receipt(task,json.loads(row['checks']),current=True)
            snapshot=self.task_snapshot(task)
            require(checks['passed'] and checks['snapshot']==snapshot, 'Verify actual behavior and documentation first')
            entries=data.get('reconciliation')
            require(isinstance(entries,list) and entries, 'Map plan/task sources to actual implementation and documentation')
            covered=set(); documented=set()
            for entry in entries:
                require(isinstance(entry,dict) and entry.get('source') in task['sources'], 'Reconciliation source must match task source')
                require(isinstance(entry.get('notes'),str) and len(entry['notes'].strip())>=30, 'Explain intended versus actual behavior')
                require(entry.get('disposition') in ('implemented','outside-this-task'), 'Unresolved/partial task behavior must be triaged before completion')
                actual=entry.get('actual')
                require(isinstance(actual,list) and actual, 'Actual implementation references required')
                for relative in actual:
                    file=inside(self.project,relative)
                    require(file.is_file() and Path(relative).parts[0] not in ('.tequio','.git','.agents'), 'Actual references must be project files, not private planning artifacts')
                refs=entry.get('docs',[])
                require(isinstance(refs,list) and all(x in policy['paths'] for x in refs), 'Documentation references must match declared paths')
                covered.add(entry['source']);documented.update(refs)
            require(covered==set(task['sources']), 'Every task source needs reconciliation')
            require(any(e['disposition']=='implemented' for e in entries), 'Identify the behavior this task actually implements')
            require(documented==set(policy['paths']), 'Reconcile every declared documentation path')
            for relative in policy['paths']:
                file=inside(self.project,relative)
                require(file.is_file() and len(file.read_text().strip())>=40, 'Write substantive documentation in the declared files')
                require(digest(file.read_bytes())!=task.get('documentation_baseline',{}).get(relative), 'Declared documentation was not updated')
            receipt={'task':tid,'report':report,'report_hash':digest(report_path.read_bytes()),'policy':policy,'doc_hashes':{relative:digest(inside(self.project,relative).read_bytes()) for relative in policy['paths']},'snapshot':snapshot,'inputs':self.task_inputs(task),'at':time.time()}
            path='evidence/'+tid+'-docs-'+secrets.token_hex(6)+'.json';write(inside(self.path,path),receipt)
            task['documentation_receipt']={'path':path,'hash':digest((self.path/path).read_bytes())}
            con.execute('UPDATE tasks SET body=?,reviews=NULL WHERE id=?',(json.dumps(task),tid))
            self.event(con,'documentation-recorded',{'id':tid,'receipt':path,'mode':policy['mode']})
            return {'task':tid,'documentation':'recorded','mode':policy['mode'],'note':'Content/source coverage require independent review; receipt is not a semantic certificate'}

    def review(self, tid, token, actor, kind, report, findings):
        name(actor)
        require(kind in ('correctness', 'security'), 'Unknown reviewer kind')
        path = inside(self.path, report)
        require(path.is_file() and len(path.read_text().strip()) >= 80, 'Substantive workspace-relative review report required')
        require(isinstance(findings, list) and all(isinstance(f, str) and f.strip() for f in findings), 'Findings must be a string list')
        from .verification import guard
        with guard(self, tid, acceptance=True), self.transaction() as con:
            row = self.owned(con, tid, token, ('review',), candidate_presence=True)
            require(actor != row['owner'], 'Implementer cannot attest independent review')
            require(row['checks'], 'Successful checks required before review')
            task=json.loads(row['body'])
            checks = self.check_receipt(task,json.loads(row['checks']),current=True)
            snapshot = self.task_snapshot(json.loads(row['body']))
            require(checks['passed'] and checks['snapshot'] == snapshot, 'Checks stale or failed')
            from .security import release_report
            if kind == 'security': release_report(self, json.loads(row['body']), path)
            reviews = json.loads(row['reviews'] or '{}')
            require(all(r.get('actor') != actor for k, r in reviews.items() if k != kind), 'Correctness and security reviewers must be distinct')
            reviews[kind] = {'documentation_hash':self.documentation_state(json.loads(row['body']),snapshot).get('receipt_hash'), 'actor': actor, 'kind': kind, 'snapshot': snapshot, 'report': report, 'hash': digest(path.read_bytes()), 'findings': findings, 'at': time.time()}
            con.execute('UPDATE tasks SET reviews=? WHERE id=?', (json.dumps(reviews), tid))
            self.event(con, 'reviewed', {'id': tid, 'kind': kind, 'actor': actor, 'findings': findings, 'reference': reviews[kind]})
        return reviews[kind]

    def complete(self, tid, token, summary):
        require(isinstance(summary, str) and summary.strip(), 'Completion summary required')
        from .verification import guard
        with guard(self, tid, acceptance=True), self.transaction() as con:
            row = self.owned(con, tid, token, ('review',), candidate_presence=True)
            task = json.loads(row['body'])
            from .integration import Journal
            Journal(self).gate(con, tid, completion=True)
            checks = self.check_receipt(task,json.loads(row['checks']),current=True)
            snapshot = self.task_snapshot(json.loads(row['body']))
            require(checks['passed'] and checks['snapshot'] == snapshot, 'Checks failed or stale')
            doc_state=self.documentation_state(task,snapshot)
            require(doc_state['state']=='current',doc_state.get('reason','Documentation reconciliation required'))
            reviews = json.loads(row['reviews'] or '{}')
            from .security import required_reviews
            for kind in required_reviews(task):
                require(kind in reviews, 'Missing ' + kind + ' review')
                review = reviews[kind]
                p = inside(self.path, review['report'])
                require(review['snapshot'] == snapshot and p.is_file() and digest(p.read_bytes()) == review['hash'], 'Review stale or altered')
                require(not review['findings'], 'Unresolved review findings')
                if kind=='correctness':require(review.get('documentation_hash')==doc_state['receipt_hash'],'Correctness review must cover current documentation reconciliation')
            task['result_snapshot'] = snapshot
            task['result_hash'] = self.resource_hash(task['writes'])
            con.execute("UPDATE tasks SET status='done',token=NULL,lease=NULL,reason=?,body=? WHERE id=?", (summary, json.dumps(task), tid))
            self.event(con, 'completed', {'id': tid, 'summary': summary})
        return {'completed': tid}

    def release(self, tid, token, reason, blocked=False):
        require(reason.strip(), 'Reason and resumption condition required')
        from .verification import guard
        with guard(self, tid), self.transaction() as con:
            row = con.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
            require(row and row['status'] in ('running', 'review') and secrets.compare_digest(row['token'] or '', token), 'Owner token mismatch or task inactive')
            con.execute('UPDATE tasks SET status=?,owner=NULL,token=NULL,lease=NULL,checks=NULL,reviews=NULL,reason=? WHERE id=?', ('blocked' if blocked else 'ready', reason, tid))
            self.event(con, 'released', {'id': tid, 'reason': reason, 'blocked': blocked})
        return {'released': tid}

    def recover(self, tid, reason, stopped_check=False):
        require(reason.strip(), 'Recovery requires actual work inspection and reason')
        from .verification import guard, reconcile, read, TERMINAL
        with guard(self, tid, stopped_check, reason) as metadata, self.transaction() as con:
            row = con.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
            require(row, 'Task not recoverable')
            released = (row['status'] == 'ready' and bool(row['owner']) and
                        all(row[key] is None for key in ('token', 'lease', 'checks', 'reviews')))
            require(released or row['status'] in ('running', 'review', 'blocked'), 'Task not recoverable')
            if released:
                record = read(metadata)
                require(not record or record['state'] in TERMINAL or record.get('process_group'),
                        'Released ownership has unknown verification state; inspect and reconcile the operation first')
            else:
                require(row['status'] == 'blocked' or row['lease'] < time.time(), 'Live lease: contact current owner; do not steal')
            reconcile(metadata, reason)
            con.execute("UPDATE tasks SET status='ready',owner=NULL,token=NULL,lease=NULL,checks=NULL,reviews=NULL,reason=? WHERE id=?", (reason, tid))
            self.event(con, 'recovered', {'id': tid, 'reason': reason})
        return {'recovered': tid, 'note': 'No process killed or restarted; claim still requires current inputs and dependencies'}

    def replan(self, reason):
        require(reason.strip(), 'Replan reason required')
        with self.transaction() as con:
            require(not con.execute("SELECT 1 FROM tasks WHERE status IN ('running','review')").fetchone(), 'Release active tasks before replanning')
            con.execute("UPDATE tasks SET status='superseded',reason=? WHERE status!='done'", (reason,))
            con.execute("DELETE FROM meta WHERE key IN ('analysis','plan')")
            self.event(con, 'replanned', {'reason': reason})
        return {'replan': 'Record refreshed analysis and plan, then import replacement task IDs; old history retained'}

    def review_state(self, row, body, snapshot):
        try:
            from .security import validate as validate_security
            validate_security(self, body, execution=True)
            snapshot = self.task_snapshot(body)
            checks=self.check_receipt(body,json.loads(row['checks']),current=True)
            require(checks['passed'] and checks['snapshot']==snapshot,'Verification stale or failed')
            docs=self.documentation_state(body,snapshot)
            require(docs['state']=='current',docs.get('reason','Documentation outstanding'))
            reviews=json.loads(row['reviews'] or '{}')
            from .security import required_reviews
            for kind in required_reviews(body):
                if kind not in reviews:return {'state':'pending','kind':kind}
                report=reviews[kind];file=inside(self.path,report['report'])
                require(report['snapshot']==snapshot and file.is_file() and digest(file.read_bytes())==report['hash'],'Review stale or altered')
                if kind=='correctness':require(report.get('documentation_hash')==docs['receipt_hash'],'Review does not cover current documentation')
                if report['findings']:return {'state':'findings','kind':kind,'findings':report['findings']}
            return {'state':'current'}
        except (Error,OSError,KeyError,ValueError,TypeError) as exc:
            return {'state':'stale','reason':str(exc)}

    def status(self, *, _checkpoint=None):
        from .orientation import orient
        with contextlib.closing(sqlite3.connect('file:'+str(self.path/'state.sqlite3')+'?mode=ro',uri=True)) as con:
            con.row_factory=sqlite3.Row
            rows=list(con.execute('SELECT * FROM tasks ORDER BY rowid'))
            running=[x for x in rows if x['status'] in ('running','review')]+self.peer_claims()
            capacity=json.loads(con.execute("SELECT value FROM meta WHERE key='config'").fetchone()[0])['max_parallel']
            phases={}
            for phase in ['analysis','plan']:
                record=con.execute('SELECT value FROM meta WHERE key=?',(phase,)).fetchone()
                phases[phase]='missing' if not record else 'current' if record[0]==self.phase_hash(phase) else 'stale'
            stale=[phase for phase,value in phases.items() if value!='current']
            snapshot=None
            tasks=[]
            for row in rows:
                task=json.loads(row['body']);waiting=[]
                from .security import state as security_state
                security = security_state(self, task, historical=row['status'] in ('done','superseded'))
                if security['state']=='migration-required': waiting.append('security contract migration-required: '+security['reason'])
                operation = self.verification_status(row['id'])
                from .freshness import scoped
                dispatchable=(not stale or scoped(task)) and len(running)<capacity and self.ready(con,row,running)
                if row['status']=='ready' and not dispatchable:
                    if stale and not scoped(task):waiting.append('analysis/plan missing or stale')
                    if len(running)>=capacity:waiting.append('project concurrency capacity occupied')
                    try:
                        if self.expected_inputs(task,con)!=self.task_inputs(task):waiting.append('task inputs changed')
                    except (Error,OSError,KeyError,ValueError) as exc:waiting.append(str(exc))
                    try:self.documentation_policy(task)
                    except Error as exc:waiting.append(str(exc))
                    try:
                        if task.get('specialist_bindings',{})!=self.specialist_bindings(task):waiting.append('specialist binding changed')
                    except (Error,OSError,KeyError,ValueError) as exc:waiting.append(str(exc))
                    issue = self.dependency_issue(con, task)
                    if issue: waiting.append(issue)
                    if not waiting:waiting.append('declared resources overlap active work or a prerequisite needs requalification')
                try:self.documentation_policy(task);doc_policy_valid=True
                except (Error,KeyError,TypeError,ValueError):doc_policy_valid=False
                docs=self.documentation_state(task,snapshot) if row['status']=='review' else {'state':('recorded-historical' if task.get('documentation_receipt') else 'not-recorded-legacy') if row['status']=='done' else 'pending'}
                from .reporting import status_checks, draft_readiness
                tasks.append({'checks': status_checks(self,row,task), 'draft_readiness': draft_readiness(row,task), 'security':security, 'verification': operation, 'id':row['id'],'title':task['title'],'status':row['status'],'owner':row['owner'],'lease_expired':bool(row['lease'] and row['lease']<time.time()),'dispatchable':dispatchable,'reason':row['reason'],'waiting_on':waiting,'documentation':docs,'documentation_policy_valid':doc_policy_valid,'review':self.review_state(row,task,snapshot) if row['status']=='review' else {'state':'not-applicable'}})
            from .integration import Journal
            integration = Journal(self).status()
            from .execution_progress import status_observation
            return {**(status_observation(self) if _checkpoint is None else status_observation(self,checkpoint=_checkpoint)), 'integration':integration,'workspace':str(self.path),'phases':phases,'stale_phases':stale,'tasks':tasks,'workflow':orient(phases,tasks,integration),'warning':'Active records are claims, not evidence of a live agent/process. Inspect actual handles before recovery.'}

    def checkpoint(self, summary, next_action):
        require(summary.strip() and next_action.strip(), 'Summary and next action required')
        data = {'at': time.time(), 'summary': summary, 'next_action': next_action, 'project_snapshot': tree_hash(self.project, project=True), 'inputs': self.inputs(), 'status': self.status()}
        from .run_context import VERSION, snapshot
        data.update(checkpoint_version=VERSION, context=snapshot(self))
        write(self.path / 'checkpoint.json', data)
        return data

    def resume(self):
        from .run_context import resume
        return resume(self)
