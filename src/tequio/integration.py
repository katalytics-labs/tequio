"""Exact-commit intent and observed recovery; never performs Git mutations."""
import contextlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
from .core import Error, require, digest, name


def git(path, *args, predicate=False, optional=False):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env['GIT_OPTIONAL_LOCKS'] = '0'
    env['GIT_NO_REPLACE_OBJECTS'] = '1'
    try:
        p = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(path), *args],
                           capture_output=True, timeout=5, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Error('Git observation unavailable') from exc
    if optional and p.returncode == 1:
        return None
    if predicate and p.returncode in (0, 1):
        return p.returncode == 0
    require(p.returncode == 0, 'Git observation unavailable')
    return p.stdout.decode('utf-8', errors='strict').rstrip('\n')


def identity(path):
    root = Path(git(path, 'rev-parse', '--show-toplevel')).resolve()
    raw_common = Path(git(path, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
    common = raw_common.resolve()
    metadata = Path(git(path, 'rev-parse', '--absolute-git-dir'))
    require(not any(p.is_symlink() for q in (Path(path), metadata, raw_common, root/'.git') for p in (q,*q.parents)), 'Symlink Git paths refused')
    return {'root': str(root), 'common': str(common),
            'branch': git(path, 'symbolic-ref', '--quiet', '--short', 'HEAD', optional=True),
            'head': git(path, 'rev-parse', '--verify', 'HEAD'), 'metadata': str(metadata)}


def refs(row, body):
    value = {'checks': json.loads(row['checks']) if row['checks'] else None,
             'docs': body.get('documentation_receipt'),
             'reviews': json.loads(row['reviews'] or '{}')}
    require(all(value[k] is None or isinstance(value[k],dict) for k in ('checks','docs')) and isinstance(value['reviews'],dict), 'Integration evidence references malformed')
    return value


class Journal:
    def __init__(self, workspace):
        self.w = workspace

    def read(self):
        con = sqlite3.connect((self.w.path/'state.sqlite3').as_uri()+'?mode=ro', uri=True)
        con.row_factory = sqlite3.Row
        return contextlib.closing(con)

    def tables(self, con):
        objects = list(con.execute("SELECT name,type FROM sqlite_master WHERE name IN ('integration_intents','integration_events')"))
        require(all(r[1] == 'table' for r in objects), 'Integration journal malformed objects')
        names = {r[0] for r in objects}
        require(not names or len(names) == 2, 'Integration journal incomplete')
        if names:
            for table, expected in [('integration_intents',{'task','intent'}),('integration_events',{'sequence','task','observation'})]:
                require({r[1] for r in con.execute('PRAGMA table_info('+table+')')} == expected, 'Integration journal malformed schema')
            require(not con.execute('SELECT 1 FROM integration_events e LEFT JOIN integration_intents i ON e.task=i.task WHERE i.task IS NULL LIMIT 1').fetchone(), 'Integration journal orphan observation')
            require(not con.execute('SELECT 1 FROM integration_intents i LEFT JOIN tasks t ON i.task=t.id WHERE t.id IS NULL LIMIT 1').fetchone(), 'Integration journal orphan intent')
        return bool(names)

    def intent(self, con, tid):
        if not self.tables(con):
            return None
        row = con.execute('SELECT intent FROM integration_intents WHERE task=?', (tid,)).fetchone()
        if not row:
            return None
        value = json.loads(row[0])
        require(value['version'] == 1 and value['task'] == tid and isinstance(value['commit'], str)
                and re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', value['commit']), 'Invalid integration intent')
        require(value['controller'] == str(self.w.project) and value['workspace'] == str(self.w.path), 'Integration identity mismatch')
        return value

    def events(self, con, tid):
        result = []
        for row in con.execute('SELECT observation FROM integration_events WHERE task=? ORDER BY sequence', (tid,)):
            event = json.loads(row[0])
            require(isinstance(event, dict) and type(event.get('epoch')) is int and event['epoch'] > 0, 'Integration observation malformed')
            if event.get('planned') is True or event.get('reconfirmed') is True:
                require(type(event.get('barrier')) is int and event['barrier'] >= 0, 'Integration authorization observation malformed')
            else:
                require(event.get('task') == tid and 'integrated' in event and (event['integrated'] is None or type(event['integrated']) is bool)
                        and event.get('state') in ('pending-integration','integrated-unrecorded','needs-checks','needs-docs','needs-review','ready-for-closure','accepted','blocked')
                        and all(isinstance(event.get(k),list) and all(isinstance(v,str) for v in event[k]) for k in ('blockers','warnings'))
                        and isinstance(event.get('commit'),str) and re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})',event['commit']), 'Integration observation malformed')
            if 'baseline' in event:
                require(event.get('integrated') is True and isinstance(event['baseline'],dict)
                        and set(event['baseline']) == {'checks','docs','reviews'} and isinstance(event['baseline']['reviews'],dict)
                        and type(event.get('barrier')) is int and event['barrier'] >= 0, 'Integration baseline malformed')
            result.append(event)
        return result

    def binding(self, body):
        from .freshness import RUNTIME_FIELDS
        return {'inputs': self.w.task_inputs(body), 'definition': digest(json.dumps({k:v for k,v in body.items() if k not in RUNTIME_FIELDS}, sort_keys=True).encode())}

    def epoch(self, con, tid):
        return max((r['seq'] for r in con.execute("SELECT seq,data FROM events WHERE kind='claimed'") if json.loads(r['data']).get('id') == tid), default=0)

    def barrier(self, con):
        return con.execute('SELECT COALESCE(MAX(seq),0) FROM events').fetchone()[0]

    def reconfirm(self, con, tid):
        epoch = self.epoch(con, tid)
        authorized = [x for x in self.events(con, tid) if x.get('planned') or x.get('reconfirmed')]
        if not authorized or authorized[-1].get('epoch') != epoch:
            con.execute('INSERT INTO integration_events(task,observation) VALUES (?,?)', (tid,json.dumps({'epoch':epoch,'reconfirmed':True,'barrier':self.barrier(con)},sort_keys=True)))

    def plan(self, tid, token, lane, commit, branch):
        from .verification import guard
        from .git_isolation import _origin, _state
        name(tid); name(lane)
        require(isinstance(commit, str) and re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', commit), 'Explicit full commit SHA required')
        with guard(self.w, tid, acceptance=True), self.w.transaction() as con:
            row = self.w.owned(con, tid, token)
            body = json.loads(row['body'])
            isolation = {**_state(self.w.project), 'control_root':str(_origin(self.w.project))}
            require(isolation['control_root'] == str(self.w.project), 'Plan from original controller only')
            target = identity(self.w.project)
            require(self.w.project.is_relative_to(Path(target['root'])) and target['branch'] == branch, 'Target checked-out branch/root mismatch')
            old = self.intent(con, tid)
            if old and git(self.w.project, 'merge-base', '--is-ancestor', old['commit'], target['head'], predicate=True):
                require(old['lane'] == lane and old['commit'] == commit and old['binding'] == self.binding(body)
                        and old['target'] == {k:target[k] for k in ('root','common','branch')}, 'Intent immutable; different commit/identity requires a new task and replan')
                require(not self.blockers(target), 'Target dirty or native operation in progress')
                self.reconfirm(con, tid)
                return old
            registered = next((x for x in isolation['lanes'] if x['lane'] == lane), None)
            require(registered is not None, 'Registered lane required')
            source = identity(registered['path'])
            require(source['common'] == target['common'] and source['root'] == str(Path(registered['worktree']).resolve()) and source['branch'] == registered['branch'] and Path(registered['path']).relative_to(Path(source['root'])) == self.w.project.relative_to(Path(target['root'])), 'Source lane identity mismatch')
            require(git(self.w.project, 'cat-file', '-t', commit) == 'commit', 'Exact commit object required')
            require(git(registered['path'], 'merge-base', '--is-ancestor', commit, 'HEAD', predicate=True), 'Selected commit absent from lane HEAD')
            candidate = {'version':1, 'task':tid, 'controller':str(self.w.project), 'workspace':str(self.w.path),
                         'binding':self.binding(body), 'lane':lane, 'source':{k:registered[k] for k in ('path','worktree','branch')},
                         'commit':commit, 'target':{k:target[k] for k in ('root','common','branch')}, 'base':target['head']}
            old = self.intent(con, tid)
            if old:
                # Target may have advanced since the immutable original request.
                candidate['base'] = old['base']
                require(candidate == old, 'Intent immutable; different commit/identity requires a new task and replan')
                self.reconfirm(con, tid)
                return old
            require(not self.blockers(target), 'Target dirty or native operation in progress')
            base = git(self.w.project, 'merge-base', target['head'], commit)
            paths = git(self.w.project, 'diff', '--no-ext-diff', '--no-textconv', '--no-renames', '--name-only', '-z', base, commit).split('\0')
            for path in filter(None, paths):
                p = Path(path)
                require(not p.is_absolute() and '..' not in p.parts and p.parts[0] not in ('.git','.tequio','.agents'), 'Private or unsafe source path')
                require(p.is_relative_to(self.w.project.relative_to(Path(target['root']))), 'Source delta outside controller project')
                p = p.relative_to(self.w.project.relative_to(Path(target['root'])))
                require(p.parts and p.parts[0] not in ('.git','.tequio','.agents'), 'Private source path')
                require(any(p == Path(w) or Path(w) in p.parents for w in body['writes']), 'Source delta outside task write ownership')
            con.execute('CREATE TABLE IF NOT EXISTS integration_intents(task TEXT PRIMARY KEY REFERENCES tasks(id), intent TEXT NOT NULL)')
            con.execute('CREATE TABLE IF NOT EXISTS integration_events(sequence INTEGER PRIMARY KEY, task TEXT NOT NULL REFERENCES integration_intents(task), observation TEXT NOT NULL)')
            con.execute('INSERT INTO integration_intents VALUES (?,?)', (tid, json.dumps(candidate, sort_keys=True)))
            con.execute('INSERT INTO integration_events(task,observation) VALUES (?,?)', (tid,json.dumps({'epoch':self.epoch(con,tid),'planned':True,'barrier':self.barrier(con)},sort_keys=True)))
            return candidate

    def blockers(self, target):
        out = []
        metadata = Path(target['metadata'])
        if any((metadata/p).exists() for p in ('MERGE_HEAD','rebase-merge','rebase-apply','CHERRY_PICK_HEAD','REVERT_HEAD','sequencer')):
            out.append('native-operation')
        status = git(target['root'], 'status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignore-submodules=none')
        if status:
            out.append('dirty')
            if any(x[:2] in ('DD','AU','UD','UA','DU','AA','UU') for x in status.split('\0')):
                out.append('conflicted')
        return out

    def classify(self, con, tid):
        intent = self.intent(con, tid)
        if intent is None:
            return None
        row = con.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
        require(row is not None, 'Journal task missing')
        body = json.loads(row['body'])
        events = self.events(con, tid)
        epoch = self.epoch(con, tid)
        baseline_event = next((x for x in events if x.get('integrated') is True and 'baseline' in x), None)
        baseline = baseline_event['baseline'] if baseline_event else None
        barrier = max([x.get('barrier',0) for x in events] or [0])
        result = {'task':tid, 'commit':intent['commit'], 'state':'pending-integration', 'integrated':None, 'blockers':[], 'warnings':[]}
        result['epoch'] = epoch
        from .security import state as security_state
        if security_state(self.w, body, historical=row['status'] in ('done','superseded'))['state'] == 'migration-required':
            result['blockers'].append('security-contract-migration-required')
        if row['status'] not in ('running','review','done'):
            result['blockers'].append('owner-inactive')
        authorized = [x for x in events if x.get('planned') or x.get('reconfirmed')]
        if not authorized or authorized[-1].get('epoch') != epoch:
            result['blockers'].append('owner-changed-reconfirm-plan')
        try:
            target = identity(self.w.project)
            result['head'] = target['head']
            result['integrated'] = git(self.w.project, 'merge-base', '--is-ancestor', intent['commit'], target['head'], predicate=True)
            if {k:target[k] for k in ('root','common','branch')} != intent['target']:
                result['blockers'].append('target-identity-mismatch')
            result['blockers'] += self.blockers(target)
            if not git(self.w.project, 'merge-base', '--is-ancestor', intent['base'], target['head'], predicate=True):
                result['blockers'].append('target-rewritten')
            if self.binding(body) != intent['binding'] or not self.w.dependencies_current(con,body):
                result['blockers'].append('task-binding-changed')
            try:
                source = identity(intent['source']['path'])
                if source['common'] != intent['target']['common'] or source['root'] != intent['source']['worktree'] or source['branch'] != intent['source']['branch']:
                    raise Error('Source mismatch')
                if not git(source['root'], 'merge-base', '--is-ancestor', intent['commit'], source['head'], predicate=True):
                    raise Error('Source moved')
                if source['head'] != intent['commit']:
                    result['warnings'].append('source-tip-moved')
            except (Error, OSError, ValueError):
                (result['warnings'] if result['integrated'] else result['blockers']).append('source-unavailable-or-moved')
        except (Error, OSError, ValueError):
            result['blockers'].append('git-unavailable')
        if result['blockers']:
            result['state'] = 'blocked'
        elif result['integrated']:
            if baseline is None:
                result['state'] = 'integrated-unrecorded'
            else:
                from .reporting import check_state, documentation, reviews
                checks = check_state(self.w, row, body)
                docs = documentation(self.w, body)
                review = reviews(self.w, row, body, checks, docs)
                current = refs(row, body)
                later = [(r['kind'],json.loads(r['data'])) for r in con.execute('SELECT kind,data FROM events WHERE seq>?',(barrier,)) if json.loads(r['data']).get('id') == tid]
                check_receipt=None
                if checks['state']=='current' and current['checks']:
                    try:check_receipt=self.w.check_receipt(body,current['checks'])
                    except (Error,OSError,ValueError,KeyError,TypeError):checks={'state':'invalid'}
                integrated_check = check_receipt.get('integration') if isinstance(check_receipt,dict) else None
                check_new = integrated_check == {k:result[k] for k in ('commit','head','epoch')} and any(k=='verified' and d.get('receipt') == current['checks'] for k,d in later)
                docs_new = any(k=='documentation-recorded' and d.get('receipt') == (current['docs'] or {}).get('path') for k,d in later)
                review_new = lambda kind: any(k=='reviewed' and d.get('kind') == kind and d.get('actor') == current['reviews'].get(kind,{}).get('actor') and d.get('reference') == current['reviews'].get(kind) for k,d in later)
                if checks['state'] != 'current' or current['checks'] == baseline['checks'] or not check_new:
                    result['state'] = 'needs-checks'
                elif docs['state'] != 'current' or current['docs'] == baseline['docs'] or not docs_new:
                    result['state'] = 'needs-docs'
                elif any(v['state'] != 'current' or current['reviews'].get(k) == baseline['reviews'].get(k) or not review_new(k) for k,v in review.items()):
                    result['state'] = 'needs-review'
                else:
                    result['state'] = 'accepted' if row['status'] == 'done' else 'ready-for-closure' if row['status'] == 'review' else 'blocked'
                    if result['state'] == 'blocked':
                        result['blockers'].append('evidence-lifecycle-mismatch')
        return result

    def projection(self, intent):
        result = {k:intent[k] for k in ('version','task','controller','workspace','lane','commit','base')}
        result['source'] = {k:intent['source'][k] for k in ('path','worktree','branch')}
        result['target'] = {k:intent['target'][k] for k in ('root','common','branch')}
        return result

    def status(self, tid=None):
        try:
            with self.read() as con:
                if not self.tables(con):
                    return {'tasks':[]}
                ids = [tid] if tid else [r[0] for r in con.execute('SELECT task FROM integration_intents ORDER BY task')]
                return {'tasks':[dict(x,intent=self.projection(self.intent(con,i)),history=[{k:v for k,v in e.items() if k in ('state','head','integrated','epoch','planned','reconfirmed')} for e in self.events(con,i)]) for i in ids if (x := self.classify(con, i)) is not None]}
        except (sqlite3.Error, Error, OSError, ValueError, KeyError, TypeError) as exc:
            return {'tasks':[], 'state':'invalid', 'issue':'Integration journal unavailable or malformed'}

    def reconcile(self, tid):
        from .verification import guard
        with guard(self.w, tid, acceptance=True), self.w.transaction() as con:
            result = self.classify(con, tid)
            require(result is not None, 'No integration intent')
            previous = self.events(con, tid)
            if result['state'] == 'integrated-unrecorded' and not any(x.get('integrated') is True and 'baseline' in x for x in previous):
                row = con.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
                result['baseline'] = refs(row, json.loads(row['body']))
                result['barrier'] = self.barrier(con)
                if not result['blockers']:
                    result['state'] = 'needs-checks'
            # Baseline belongs only to the first integrated event; dedup subsequent facts.
            if not previous or {k:v for k,v in previous[-1].items() if k not in ('baseline','barrier')} != {k:v for k,v in result.items() if k not in ('baseline','barrier')}:
                con.execute('INSERT INTO integration_events(task,observation) VALUES (?,?)', (tid,json.dumps(result,sort_keys=True)))
            return self.classify(con, tid)

    def gate(self, con, tid, completion=False):
        try:
            state = self.classify(con, tid)
            if state is None:
                return
            allowed = ('ready-for-closure',) if completion else ('needs-checks','needs-docs','needs-review','ready-for-closure')
            require(state['state'] in allowed, 'Integration journal requires ' + ('fresh integrated checks/docs/reviews' if completion else 'durable merged observation and clean matching target') + ': ' + state['state'])
        except (sqlite3.Error, ValueError, KeyError, TypeError) as exc:
            raise Error('Integration journal invalid; inspect before lifecycle continuation') from exc
