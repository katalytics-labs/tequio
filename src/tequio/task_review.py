"""Content-bound review of proposed task batches, before immutable import.

Actor identities and report content are local assertions, not authenticated
independence or semantic certification. This gate does not execute tasks.
"""
import json
from .core import Error, digest, inside, load, name, require

AREAS = {
    'correctness': ('requirements', 'readiness', 'dependencies', 'ownership', 'checks'),
    'redteam': ('failure-cases', 'security-classification', 'privacy-export', 'workflow-traps'),
}


DRAFT_CATEGORIES = frozenset({
    'unresolved-product-decision', 'external-prerequisite',
    'missing-specialist-qualification', 'explicit-deferral',
})


def validate_readiness(tasks):
    """Validate new proposal declarations, not the truth of their prose."""
    for task in tasks:
        if task.get('stage', 'ready') != 'draft':
            continue
        decision = task.get('draft')
        require(isinstance(decision, dict) and set(decision) ==
                {'version', 'category', 'reason', 'next_action', 'source'},
                'Draft requires a sourced draft decision: ' + task['id'])
        require(type(decision['version']) is int and decision['version'] == 1,
                'Draft decision version must be 1')
        require(isinstance(decision['category'], str) and
                decision['category'] in DRAFT_CATEGORIES, 'Unsupported draft category')
        require(all(isinstance(decision[k], str) and len(decision[k].strip()) >= 30
                    for k in ('reason', 'next_action')),
                'Draft requires substantive reason and next_action')
        require(isinstance(decision['source'], str) and
                decision['source'] in task['sources'],
                'Draft decision source must be an exact task source')
        require(decision['category'] != 'missing-specialist-qualification' or
                bool(task.get('specialists', [])), 'Draft qualification requires named specialists')


def readiness_summary(tasks):
    drafts = [t for t in tasks if t.get('stage', 'ready') == 'draft']
    return {'ready': len(tasks) - len(drafts), 'draft': len(drafts),
            'drafts': [{'id': t['id'], 'category': t['draft']['category']} for t in drafts]}


def task_digest(tasks):
    return digest(json.dumps(tasks, sort_keys=True, separators=(',', ':')).encode())


class TaskReview:
    def __init__(self, workspace):
        self.w = workspace

    def _tasks(self, path):
        tasks = load(path)
        require(isinstance(tasks, list) and tasks, 'Expected nonempty task array')
        for task in tasks:
            self.w.validate_task(task)
        validate_readiness(tasks)
        require(len({t['id'] for t in tasks}) == len(tasks), 'Duplicate task IDs')
        return tasks

    def context(self, tasks, *, binding_tasks=None):
        # Sources may live outside phase directories; every cited file matters.
        sources = sorted({src.split('#')[0] for task in tasks for src in task['sources']})
        files = [(src, digest(inside(self.w.path, src).read_bytes())) for src in sources]
        bindings = [(task['id'], self.w.specialist_bindings(task))
                    for task in (tasks if binding_tasks is None else binding_tasks)
                    if task.get('stage', 'ready') == 'ready']
        return digest(json.dumps([self.w.inputs(), files, bindings], sort_keys=True).encode())

    def prepare(self, path, author):
        name(author)
        tasks = self._tasks(path)
        fingerprint = task_digest(tasks)
        with self.w.transaction() as con:
            self.w.current(con)
            context = self.context(tasks)
            batch = digest((fingerprint + context).encode())
            key = 'task-batch:' + batch
            old = con.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
            if old:
                record = json.loads(old[0])
                require(record['author'] == author, 'Task batch author is immutable')
            else:
                record = {'batch': batch, 'author': author, 'task_hash': fingerprint,
                          'inputs': context, 'task_ids': [t['id'] for t in tasks],
                          'tasks': tasks, 'reviews': {}}
                con.execute('INSERT INTO meta VALUES (?,?)', (key, json.dumps(record)))
                self.w.event(con, 'task-batch-prepared', record)
        return {'batch': batch, 'author': author, 'tasks': record['task_ids'], 'readiness': readiness_summary(tasks),
                'next': 'Obtain distinct correctness and redteam reviews, then import the unchanged task file.'}

    def _record(self, con, batch):
        require(isinstance(batch, str) and len(batch) == 64 and
                all(c in '0123456789abcdef' for c in batch), 'Invalid task batch ID')
        row = con.execute('SELECT value FROM meta WHERE key=?', ('task-batch:' + batch,)).fetchone()
        require(row, 'Unknown task batch; prepare-tasks first')
        record = json.loads(row[0])
        validate_readiness(record['tasks'])
        self.w.current(con)
        require(record['inputs'] == self.context(record['tasks']), 'Task review context stale; prepare and review current inputs')
        return record

    def review(self, batch, actor, kind, report):
        name(actor)
        require(kind in AREAS, 'Task review kind must be correctness or redteam')
        path = inside(self.w.path, report)
        report_bytes = path.read_bytes()
        body = json.loads(report_bytes)
        require(isinstance(body, dict), 'Task review report must be an object')
        require(body.get('batch') == batch, 'Report must bind exact task batch')
        require(isinstance(body.get('summary'), str) and len(body['summary'].strip()) >= 80,
                'Write a substantive task-review summary')
        coverage = body.get('coverage')
        require(isinstance(coverage, dict) and set(coverage) == set(AREAS[kind]),
                'Task review requires all coverage areas for ' + kind)
        require(all(isinstance(v, str) and len(v.strip()) >= 30 for v in coverage.values()),
                'Explain actual evidence and limits for each task-review area')
        findings = body.get('findings')
        require(isinstance(findings, list) and all(isinstance(f, str) and f.strip() for f in findings),
                'Task review requires explicit findings list')
        with self.w.transaction() as con:
            record = self._record(con, batch)
            require(actor != record['author'], 'Task author cannot attest independent task review')
            require(all(r['actor'] != actor for k, r in record['reviews'].items() if k != kind),
                    'Task correctness and redteam reviewers must be distinct')
            receipt = {'actor': actor, 'kind': kind, 'report': report,
                       'hash': digest(report_bytes), 'findings': findings}
            record['reviews'][kind] = receipt
            con.execute('UPDATE meta SET value=? WHERE key=?',
                        (json.dumps(record), 'task-batch:' + batch))
            self.w.event(con, 'task-batch-reviewed', {'batch': batch, **receipt})
        return {'batch': batch, 'kind': kind, 'findings': findings,
                'note': 'Receipt binds local assertions, not authenticated identity or semantic completeness'}

    def require_import(self, con, tasks):
        validate_readiness(tasks)
        fingerprint = task_digest(tasks)
        batch = digest((fingerprint + self.context(tasks)).encode())
        row = con.execute('SELECT value FROM meta WHERE key=?', ('task-batch:' + batch,)).fetchone()
        require(row, 'Task batch unreviewed; prepare-tasks and obtain correctness/redteam reviews before import')
        record = self._record(con, batch)
        for kind in AREAS:
            receipt = record['reviews'].get(kind)
            require(receipt, 'Missing task-batch ' + kind + ' review')
            require(not receipt['findings'], 'Resolve task-batch ' + kind + ' findings before import')
            path = inside(self.w.path, receipt['report'])
            require(path.is_file() and digest(path.read_bytes()) == receipt['hash'],
                    'Task-batch ' + kind + ' report missing or changed; review again')
        return batch

    def status(self, path):
        tasks = self._tasks(path)
        with self.w.transaction() as con:
            try:
                batch = self.require_import(con, tasks)
                return {'state': 'reviewed', 'batch': batch}
            except Error as exc:
                return {'state': 'review-required', 'reason': str(exc)}
