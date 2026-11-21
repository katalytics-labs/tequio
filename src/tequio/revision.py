"""Reviewed atomic backlog revisions; immutable definitions and explicit edge overlays."""
import contextlib
import json
import sqlite3
from .core import Error, digest, inside, name, require
from .task_review import TaskReview, AREAS, validate_readiness
from . import verification


def _definition(task):
    from .freshness import RUNTIME_FIELDS
    return _hash({k: v for k, v in task.items() if k not in RUNTIME_FIELDS})


def _hash(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


@contextlib.contextmanager
def _connection(w, con=None):
    con = con or getattr(w, '_revision_connection', None)
    if con is not None:
        yield con
    else:
        db = sqlite3.connect((w.path / 'state.sqlite3').as_uri() + '?mode=ro', uri=True)
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()


def _get(con, key):
    row = con.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
    return json.loads(row[0]) if row else None


def check_version(w, con=None):
    with _connection(w, con) as db:
        marker = _get(db, 'revision-version')
        require(marker is None or type(marker) is int and marker == 1,
                'Unsupported revision workspace version')
        overlays = db.execute("SELECT key FROM meta WHERE key LIKE 'revision-binding:%' LIMIT 1").fetchone()
        require(not overlays or marker == 1, 'Revision capability marker missing')


def binding(w, task, con=None):
    with _connection(w, con) as db:
        check_version(w, db)
        value = _get(db, 'revision-binding:' + task['id'])
        if value is None:
            return None
        require(isinstance(value, dict) and set(value) == {'version', 'revision', 'definition', 'dependencies', 'inputs'},
                'Invalid revision binding')
        require(type(value['version']) is int and value['version'] == 1 and value['definition'] == _definition(task), 'Revision definition binding changed')
        require(isinstance(value['inputs'], str) and len(value['inputs']) == 64, 'Invalid revision input binding')
        _ids(value['dependencies'])
        history = _get(db, 'revision-binding-history:' + value['revision'] + ':' + task['id'])
        require(history == value, 'Revision binding history changed')
        if not getattr(w, '_revision_applying', False):
            app = _get(db, 'revision-application:' + value['revision'])
            require(app and app.get('version') == 1 and app.get('hash') == _hash([app['result'], app['changes'], app['reviews']]) and app['changes'].get(task['id'], {}).get('binding') == value, 'Revision application binding changed')
        return value


def dependencies(w, task, con=None):
    value = binding(w, task, con)
    return list(value['dependencies'] if value else task.get('depends_on', []))


def expected_inputs(w, task, con=None):
    value = binding(w, task, con)
    return value['inputs'] if value else task.get('inputs')


def salt(w, task, base):
    value = binding(w, task)
    return _hash([base, value['revision'], value['definition'], value['dependencies']]) if value else base


def _ids(value):
    require(isinstance(value, list) and all(isinstance(v, str) for v in value), 'Expected dependency ID list')
    for v in value:
        name(v)
    require(len(set(value)) == len(value), 'Duplicate IDs or edges')


class Revision:
    def __init__(self, workspace):
        self.w = workspace

    def _proposal(self, relative):
        raw = inside(self.w.path, relative).read_bytes()
        def pairs(items):
            obj = {}
            for key, value in items:
                require(key not in obj, 'Duplicate proposal JSON key')
                obj[key] = value
            return obj
        p = json.loads(raw, object_pairs_hook=pairs)
        require(isinstance(p, dict) and set(p) == {'version', 'reason', 'supersede', 'replacements', 'tasks', 'rebindings'}, 'Invalid revision proposal keys')
        require(type(p['version']) is int and p['version'] == 1, 'Unsupported revision proposal version')
        require(isinstance(p['reason'], str) and p['reason'].strip(), 'Revision reason required')
        _ids(p['supersede'])
        require(isinstance(p['tasks'], list) and isinstance(p['replacements'], dict) and isinstance(p['rebindings'], list), 'Invalid revision collections')
        ids = []
        for t in p['tasks']:
            self.w.validate_task(t)
            _ids(t.get('depends_on', []))
            ids.append(t['id'])
        validate_readiness(p['tasks'])
        _ids(ids)
        require(set(p['replacements']) == set(p['supersede']), 'Replacement relation must cover exactly superseded IDs')
        covered = set()
        for targets in p['replacements'].values():
            _ids(targets)
            require(targets and set(targets) <= set(ids), 'Replacement relation requires new tasks')
            covered.update(targets)
        require(covered == set(ids), 'Every new task needs a replacement relation; use ordinary import for add-only work')
        consumers = []
        for r in p['rebindings']:
            require(isinstance(r, dict) and set(r) == {'consumer', 'from', 'to'}, 'Invalid rebinding keys')
            name(r['consumer']); consumers.append(r['consumer'])
            _ids(r['from']); _ids(r['to'])
            require(r['from'] != r['to'], 'Rebinding must change dependencies')
        _ids(consumers)
        require(p['supersede'] or p['rebindings'], 'Empty material revision')
        return p, digest(raw)

    def _inspect(self, con, relative, guarded=False):
        check_version(self.w, con)
        p, raw_hash = self._proposal(relative)
        rows = {r['id']: dict(r) for r in con.execute('SELECT * FROM tasks ORDER BY id')}
        bodies = {tid: json.loads(r['body']) for tid, r in rows.items()}
        old_edges = {tid: dependencies(self.w, t, con) for tid, t in bodies.items()}
        selected = set(p['supersede']); new = {t['id']: t for t in p['tasks']}
        require(not set(new) & set(rows), 'Task IDs immutable; replacement IDs must be new')
        require(selected <= set(rows), 'Unknown superseded task')
        require(all(rows[t]['status'] != 'done' and rows[t]['status'] != 'superseded' for t in selected), 'Cannot supersede completed or superseded task')
        edges = dict(old_edges); edges.update({tid: t.get('depends_on', []) for tid, t in new.items()})
        for r in p['rebindings']:
            tid = r['consumer']
            require(tid in rows and tid not in selected, 'Rebinding requires unchanged existing consumer')
            require(rows[tid]['status'] in {'ready', 'draft', 'blocked'}, 'Consumer must be unfinished and unclaimed')
            require(old_edges[tid] == r['from'], 'Rebinding from differs from current effective dependencies')
            edges[tid] = r['to']
        historical = set()
        for tid, deps in edges.items():
            if tid in selected or rows.get(tid, {}).get('status') == 'superseded':
                continue
            bad = set(deps) & (selected | {i for i, row in rows.items() if row['status'] == 'superseded'})
            if bad and rows.get(tid, {}).get('status') == 'done': historical.add(tid)
            else: require(not bad, 'Unfinished incoming edge to superseded task: ' + tid)
        def visit(tid, trail):
            require(tid in edges, 'Unknown dependency: ' + tid)
            require(tid not in trail, 'Dependency cycle')
            if tid in selected or rows.get(tid, {}).get('status') == 'superseded': return
            for dep in edges[tid]: visit(dep, trail | {tid})
        for tid in edges: visit(tid, set())
        affected = selected | {r['consumer'] for r in p['rebindings']}
        changed = True
        while changed:
            extra = {tid for tid, deps in old_edges.items() if rows[tid]['status'] != 'superseded' and set(deps) & affected}
            changed = not extra <= affected; affected |= extra
        historical |= {tid for tid in affected if rows[tid]['status'] == 'done'}
        unfinished = sorted(affected - historical)
        blockers = []
        for tid in unfinished:
            row = rows[tid]
            if row['status'] in {'running', 'review', 'superseded'} or any(row[k] is not None for k in ('owner', 'token', 'lease')):
                blockers.append({'task': tid, 'reason': 'active ownership or ineligible state'})
            state = verification.status(self.w, tid)
            attempt = state['attempt']
            if (state['lock_held'] and not guarded) or state['observed_group_live'] or attempt and attempt['state'] not in {'completed', 'reconciled'}:
                blockers.append({'task': tid, 'reason': 'unresolved verification operation'})
        try: self.w.current(con)
        except Error: blockers.append({'reason': 'phase receipts missing or stale'})
        # Completed definitions/sources remain hashed history, not live work to requalify.
        context_tasks = [t for tid, t in bodies.items() if rows[tid]['status'] != 'superseded'] + p['tasks']
        live_tasks = [t for tid, t in bodies.items() if rows[tid]['status'] not in {'done', 'superseded'}] + p['tasks']
        context = TaskReview(self.w).context(context_tasks, binding_tasks=live_tasks)
        state_hash = _hash([rows, old_edges, [(tid, _get(con, 'revision-binding:' + tid)) for tid in rows]])
        identity = {'operation': 'revision', 'version': 1, 'proposal_hash': raw_hash, 'context': context,
                    'state_hash': state_hash, 'graph_hash': _hash(edges)}
        rid = _hash(identity)
        public = {'revision': rid, **identity, 'supersede': p['supersede'], 'new_tasks': list(new),
                  'rebindings': p['rebindings'], 'affected_unfinished': unfinished,
                  'historical_consumers': sorted(historical), 'unaffected': sorted(set(rows) - affected), 'blockers': blockers}
        return p, public

    def preview(self, proposal_relative_path):
        with _connection(self.w) as con:
            return self._inspect(con, proposal_relative_path)[1]

    def prepare(self, path, author):
        name(author)
        with self.w.transaction() as con:
            p, view = self._inspect(con, path)
            require(not view['blockers'], 'Revision blocked; inspect preview')
            rid = view['revision']; key = 'revision-intent:' + rid
            old = _get(con, key)
            if old:
                require(old['author'] == author, 'Revision author is immutable')
            else:
                record = {'version': 1, 'operation': 'revision', 'revision': rid, 'path': path,
                          'author': author, 'proposal': p, 'preview': view}
                con.execute('INSERT INTO meta VALUES (?,?)', (key, json.dumps(record)))
                self.w.event(con, 'revision-prepared', {'revision': rid, 'author': author})
        return {**view, 'author': author}

    def _record(self, con, rid, current=True, guarded=False):
        require(isinstance(rid, str) and len(rid) == 64 and all(c in '0123456789abcdef' for c in rid), 'Invalid revision ID')
        record = _get(con, 'revision-intent:' + rid)
        require(record and record.get('operation') == 'revision' and record.get('version') == 1, 'Unknown or unsupported revision intent')
        view = record['preview']
        require(_hash({k: view[k] for k in ('operation', 'version', 'proposal_hash', 'context', 'state_hash', 'graph_hash')}) == rid, 'Revision intent changed')
        p, raw = self._proposal(record['path'])
        require(p == record['proposal'] and raw == view['proposal_hash'], 'Revision proposal changed')
        if current:
            _, actual = self._inspect(con, record['path'], guarded=guarded)
            require(actual == view, 'Revision context or graph stale; prepare and review again')
            require(not actual['blockers'], 'Revision blocked')
        return record

    def _reviews(self, con, rid):
        result = {}
        for row in con.execute("SELECT value FROM meta WHERE key LIKE ? ORDER BY key", ('revision-review:' + rid + ':%',)):
            receipt = json.loads(row[0]); result[receipt['kind']] = receipt
        return result

    def review(self, revision, actor, kind, report_relative):
        name(actor); require(kind in AREAS, 'Review kind must be correctness or redteam')
        raw = inside(self.w.path, report_relative).read_bytes(); body = json.loads(raw)
        require(isinstance(body, dict) and set(body) == {'operation', 'revision', 'summary', 'coverage', 'findings'} and body.get('operation') == 'revision' and body.get('revision') == revision, 'Report must bind exact revision operation')
        require(isinstance(body.get('summary'), str) and len(body['summary'].strip()) >= 80, 'Write substantive review summary')
        coverage = body.get('coverage')
        require(isinstance(coverage, dict) and set(coverage) == set(AREAS[kind]) and all(isinstance(v, str) and len(v.strip()) >= 30 for v in coverage.values()), 'Review requires all substantive coverage areas')
        findings = body.get('findings')
        require(isinstance(findings, list) and all(isinstance(f, str) and f.strip() for f in findings), 'Explicit findings list required')
        with self.w.transaction() as con:
            record = self._record(con, revision)
            require(actor != record['author'], 'Revision author cannot review')
            require(all(r['actor'] != actor for k, r in self._reviews(con, revision).items() if k != kind), 'Reviewers must be distinct')
            receipt = {'actor': actor, 'kind': kind, 'report': report_relative, 'hash': digest(raw), 'findings': findings}
            seq = con.execute('SELECT COALESCE(MAX(seq),0)+1 FROM events').fetchone()[0]
            con.execute('INSERT INTO meta VALUES (?,?)', ('revision-review:' + revision + ':' + str(seq).zfill(20), json.dumps(receipt)))
            self.w.event(con, 'revision-reviewed', {'revision': revision, **receipt})
        return {'revision': revision, 'kind': kind, 'findings': findings}

    def _require_reviews(self, con, rid):
        reviews = self._reviews(con, rid)
        for kind in AREAS:
            receipt = reviews.get(kind)
            require(receipt and not receipt['findings'], 'Missing or unresolved revision ' + kind + ' review')
            path = inside(self.w.path, receipt['report'])
            require(path.is_file() and digest(path.read_bytes()) == receipt['hash'], 'Revision review report missing or changed')
        return reviews

    def status(self, revision):
        with _connection(self.w) as con:
            record = self._record(con, revision, current=False)
            applied = _get(con, 'revision-application:' + revision)
            if applied:
                self._applied(con, revision, applied)
                return {**applied['result'], 'state': 'applied'}
            try:
                self._record(con, revision); self._require_reviews(con, revision)
                state = 'reviewed'; issue = None
            except Error as exc:
                state = 'review-required'; issue = str(exc)
            return {'revision': revision, 'state': state, 'reason': issue, 'tasks': record['preview']['new_tasks']}

    def _applied(self, con, rid, app):
        require(app.get('version') == 1 and app.get('revision') == rid and app.get('hash') == _hash([app['result'], app['changes'], app['reviews']]), 'Revision application integrity failure')
        require(set(app['reviews']) == set(AREAS), 'Applied revision reviews missing')
        for receipt in app['reviews'].values():
            path = inside(self.w.path, receipt['report'])
            require(path.is_file() and digest(path.read_bytes()) == receipt['hash'], 'Applied revision review report missing or changed')
        for tid, data in app['changes'].items():
            row = con.execute('SELECT body FROM tasks WHERE id=?', (tid,)).fetchone()
            require(row and _definition(json.loads(row[0])) == data['body_hash'], 'Applied task definition changed')
            if 'binding' in data:
                require(_get(con, 'revision-binding-history:' + rid + ':' + tid) == data['binding'], 'Applied binding history changed')
        return {**app['result'], 'already_applied': True}

    def apply(self, revision):
        with _connection(self.w) as con:
            record = self._record(con, revision, current=False)
            app = _get(con, 'revision-application:' + revision)
            if app: return self._applied(con, revision, app)
        with contextlib.ExitStack() as stack:
            for tid in sorted(record['preview']['affected_unfinished']):
                stack.enter_context(verification.guard(self.w, tid, acceptance=True))
            stack.enter_context(self.w.claim_guard())
            with self.w.transaction() as con:
                app = _get(con, 'revision-application:' + revision)
                if app: return self._applied(con, revision, app)
                record = self._record(con, revision, guarded=True)
                reviews = self._require_reviews(con, revision)
                p = record['proposal']; changes = {}
                con.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', ('revision-version', '1'))
                for tid in p['supersede']:
                    con.execute("UPDATE tasks SET status='superseded' WHERE id=?", (tid,))
                    body = con.execute('SELECT body FROM tasks WHERE id=?', (tid,)).fetchone()[0]
                    changes[tid] = {'body_hash': _definition(json.loads(body))}
                previous = getattr(self.w, '_revision_connection', None)
                self.w._revision_connection = con
                self.w._revision_applying = True
                try:
                    for task in p['tasks']:
                        body = {**task, 'inputs': self.w.task_inputs(task), 'specialist_bindings': self.w.specialist_bindings(task) if task.get('stage', 'ready') == 'ready' else {}}
                        text = json.dumps(body)
                        con.execute('INSERT INTO tasks(id,body,status) VALUES (?,?,?)', (task['id'], text, task.get('stage', 'ready')))
                        changes[task['id']] = {'body_hash': _definition(body)}
                    binding_edges = {e['consumer']: e['to'] for e in p['rebindings']}
                    for tid in record['preview']['affected_unfinished']:
                        if tid not in p['supersede'] and tid not in binding_edges:
                            t = json.loads(con.execute('SELECT body FROM tasks WHERE id=?', (tid,)).fetchone()[0])
                            binding_edges[tid] = dependencies(self.w, t, con)
                    for tid, deps in binding_edges.items():
                        text = con.execute('SELECT body FROM tasks WHERE id=?', (tid,)).fetchone()[0]; task = json.loads(text)
                        value = {'version': 1, 'revision': revision, 'definition': _definition(task), 'dependencies': deps, 'inputs': '0' * 64}
                        key = 'revision-binding:' + tid; history = 'revision-binding-history:' + revision + ':' + tid
                        for target in (key, history): con.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', (target, json.dumps(value)))
                    for tid in binding_edges:
                        task = json.loads(con.execute('SELECT body FROM tasks WHERE id=?', (tid,)).fetchone()[0])
                        value = _get(con, 'revision-binding:' + tid); value['inputs'] = self.w.task_inputs(task)
                        for target in ('revision-binding:' + tid, 'revision-binding-history:' + revision + ':' + tid):
                            con.execute('UPDATE meta SET value=? WHERE key=?', (json.dumps(value), target))
                        changes[tid] = {'body_hash': _definition(task), 'binding': value}
                finally:
                    self.w._revision_connection = previous
                    self.w._revision_applying = False
                result = {'revision': revision, 'superseded': p['supersede'], 'imported': [t['id'] for t in p['tasks']], 'rebound': [e['consumer'] for e in p['rebindings']]}
                app = {'version': 1, 'revision': revision, 'result': result, 'changes': changes, 'reviews': reviews, 'hash': _hash([result, changes, reviews])}
                con.execute('INSERT INTO meta VALUES (?,?)', ('revision-application:' + revision, json.dumps(app)))
                self.w.event(con, 'revision-applied', result)
        return result
