"""Read-only, allowlisted evidence summaries; never serialize stored task rows."""
import contextlib
import json
import sqlite3
from .core import Workspace, Error, inside, digest, name

_FAILURES = (Error, OSError, ValueError, KeyError, TypeError, AttributeError, IndexError)


def paths(values):
    """Render declared relative paths only, excluding unsafe or malformed values."""
    if not isinstance(values, list):
        return []
    return [p for p in values if isinstance(p, str) and p and not p.startswith('/')
            and '..' not in p.split('/') and all(c.isprintable() for c in p)]


def reference(w, ref, *, unavailable=False, task=None):
    if not isinstance(ref, dict):
        return 'invalid', None
    try:
        path = inside(w.path, ref['path'])
        if not path.is_file():
            return 'missing', None
        value = w.check_receipt(task,ref) if task is not None else w.receipt(ref)
        if not isinstance(value, dict):
            return 'invalid', None
        return 'current', value
    except OSError:
        return ('unavailable' if unavailable else 'invalid'), None
    except _FAILURES:
        return 'invalid', None


def check_state(w, row, body, *, unavailable=False):
    if not row['checks']:
        return {'state': 'missing'}
    state, receipt = reference(w, json.loads(row['checks']), unavailable=unavailable, task=body)
    if state != 'current':
        return {'state': state}
    results = receipt.get('results')
    if not capture_policy(body) and (receipt.get('task') != row['id'] or type(receipt.get('passed')) is not bool
            or not isinstance(results, list) or not results
            or len(results) != len(body['checks'])
            or any(not isinstance(r, dict) or (r.get('exit_code') is not None and type(r.get('exit_code')) is not int) for r in results)
            or type(receipt.get('stable')) is not bool
            or receipt['passed'] != (receipt['stable'] and all(r['exit_code'] == 0 for r in results))):
        return {'state': 'invalid'}
    result = {'state': 'current', 'receipt': paths([json.loads(row['checks'])['path']])[0], 'receipt_hash': json.loads(row['checks'])['hash'], 'executed': len(results),
              'passed': sum(r['exit_code'] == 0 for r in results)}
    if capture_policy(body):
        counts=bounded_summary_counts(receipt)
        result.update(attempted=counts['attempted'],executed=counts['executed'],passed=counts['passed'],skipped=counts['skipped'])
    if not receipt['passed']:
        result['state'] = 'failed'
    elif receipt['snapshot'] != w.task_snapshot(body) or receipt['inputs'] != w.task_inputs(body):
        result['state'] = 'stale'
    return result


def status_checks(w, row, body):
    """Concise evidence observation, not lifecycle acceptance or a proof scan."""
    if row['status'] in ('done', 'superseded'):
        return {'state': 'not-observed'}
    try:
        return {'state': check_state(w, row, body, unavailable=True)['state']}
    except (OSError, sqlite3.Error):
        return {'state': 'unavailable'}
    except _FAILURES:
        return {'state': 'invalid'}


def draft_readiness(row, body):
    if row['status'] != 'draft':
        return {'state': 'not-applicable', 'category': None}
    if 'draft' not in body:
        return {'state': 'legacy-unknown', 'category': None}
    try:
        from .task_review import validate_readiness
        validate_readiness([{**body, 'stage': 'draft'}])
        return {'state': 'recorded', 'category': body['draft']['category']}
    except _FAILURES:
        return {'state': 'invalid', 'category': None}


def documentation(w, body):
    if not body.get('documentation_receipt'):
        return {'state': 'missing'}
    state, receipt = reference(w, body['documentation_receipt'])
    if state != 'current':
        return {'state': state}
    try:
        report = inside(w.path, receipt['report'])
        if not report.is_file():
            return {'state': 'missing'}
        if digest(report.read_bytes()) != receipt['report_hash']:
            return {'state': 'invalid'}
        policy = w.documentation_policy(body)
        if receipt['policy'] != policy or set(receipt['doc_hashes']) != set(policy['paths']):
            return {'state': 'invalid'}
        for path, expected in receipt['doc_hashes'].items():
            file = inside(w.project, path)
            if not file.is_file() or digest(file.read_bytes()) != expected:
                return {'state': 'stale'}
        return {'state': 'current' if w.documentation_state(body)['state'] == 'current' else 'stale',
                'receipt': paths([body['documentation_receipt']['path']])[0],
                'report': paths([receipt['report']])[0],
                'receipt_hash': body['documentation_receipt']['hash'], 'declared_files': paths(policy['paths'])}
    except _FAILURES:
        return {'state': 'invalid'}


def reviews(w, row, body, checks, docs):
    recorded = json.loads(row['reviews'] or '{}')
    if not isinstance(recorded, dict):
        return {'state': 'invalid'}
    output = {}
    from .security import required_reviews
    for kind in required_reviews(body):
        r = recorded.get(kind)
        state = 'missing'
        if r is not None:
            try:
                file = inside(w.path, r['report'])
                if not file.is_file():
                    state = 'missing'
                elif digest(file.read_bytes()) != r['hash'] or not isinstance(r['findings'], list):
                    state = 'invalid'
                elif r['findings']:
                    state = 'failed'
                elif r['snapshot'] != w.task_snapshot(body) or checks['state'] != 'current' or docs['state'] != 'current':
                    state = 'stale'
                elif kind == 'correctness' and r.get('documentation_hash') != body['documentation_receipt']['hash']:
                    state = 'stale'
                else:
                    state = 'current'
            except _FAILURES:
                state = 'invalid'
        output[kind] = {'state': state}
        if state in ('current', 'stale', 'failed'):
            output[kind]['report_hash'] = digest(file.read_bytes())
            output[kind]['report'] = paths([r['report']])[0]
    return output


def proof(project, workspace, task=None):
    """Inspect authoritative records through SQLite mode=ro without transactions."""
    if task is not None:
        name(task)
    w = Workspace(project, workspace)
    with contextlib.closing(sqlite3.connect((w.path/'state.sqlite3').as_uri()+'?mode=ro', uri=True)) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute('SELECT id,body,status,checks,reviews FROM tasks' + (' WHERE id=?' if task else '') + ' ORDER BY id', (task,) if task else ()).fetchall()
    if task and not rows:
        raise Error('Task not found')
    output = []
    for row in rows:
        item = {'task': name(row['id']), 'lifecycle': row['status'] if row['status'] in ('draft','ready','running','review','done','superseded','blocked') else 'invalid'}
        try:
            body = json.loads(row['body'])
            if not isinstance(body, dict):
                raise Error('Task body must be an object')
            from .security import state as security_state
            security = security_state(w, body, historical=row['status'] in ('done','superseded'))
            item['security'] = security
            checks = check_state(w, row, body)
            docs = documentation(w, body)
            review = reviews(w, row, body, checks, docs)
            sources = paths(body.get('sources', []))
            files = paths(body.get('writes', []))
            item.update(sources=sources, declared_files=files,
                        requirements=[{'requirement': i+1, 'sources': sources, 'declared_files': files,
                                       'evidence': ['checks','documentation','reviews']}
                                      for i, _ in enumerate(body.get('acceptance', []))],
                        checks=checks, documentation=docs, reviews=review)
            dependencies = []
            with contextlib.closing(sqlite3.connect((w.path/'state.sqlite3').as_uri()+'?mode=ro', uri=True)) as con:
                con.row_factory = sqlite3.Row
                for tid in w.effective_dependencies(body,con):
                    dep = con.execute('SELECT body,status FROM tasks WHERE id=?', (tid,)).fetchone()
                    state = 'missing'
                    if dep:
                        definition = json.loads(dep[0])
                        from .freshness import scoped
                        state = 'current' if (dep[1] == 'done' and w.expected_inputs(definition,con) == w.task_inputs(definition)
                            and definition.get('result_hash') == w.resource_hash(definition['writes'])
                            and (not scoped(definition) or definition.get('result_snapshot') == w.task_snapshot(definition))
                            and w.dependencies_current(con, definition)) else 'stale'
                    dependencies.append({'task': name(tid), 'state': state})
            item['dependencies'] = dependencies
            current = all(r['state'] == 'current' for r in [checks, docs, *review.values(), *dependencies])
            if security['state']=='migration-required': current=False
            item['evidence'] = 'invalid' if item['lifecycle'] == 'invalid' else 'current' if current else ('historical' if row['status'] == 'done' else 'incomplete')
        except _FAILURES:
            # Discard partial observations; never inherit another row's state.
            item = {'task': name(row['id']), 'lifecycle': item['lifecycle'],
                    'security': {'state': 'unavailable'}, 'evidence': 'invalid'}
        from .integration import Journal
        try:
            diagnostics = Journal(w).status(row['id'])
        except (*_FAILURES, sqlite3.Error):
            diagnostics = {'state': 'unavailable'}
        if diagnostics.get('tasks') or diagnostics.get('state'):
            item['integration'] = diagnostics
        output.append(item)
    return {'tasks': output, 'note': 'Declared source/requirement associations, not semantic certification. Historical closure does not prove current evidence; receipts do not authenticate reviewer independence.'}

def capture_policy(task):
    """An immutable opt-in contract; absence preserves the legacy path."""
    from .core import require
    if 'capture' not in task:return None
    p=task['capture']
    require(isinstance(p,dict) and set(p)=={'version','mode','max_bytes'},'Invalid capture policy')
    require(type(p['version']) is int and p['version']==1 and p['mode']=='bounded-v1','Unsupported capture policy')
    require(type(p['max_bytes']) is int and 1<=p['max_bytes']<=16777216,'Invalid capture byte limit')
    return p


def validate_check_receipt(receipt,task):
    """Validate bounded execution outcomes before any consumer trusts passed."""
    import base64
    import binascii
    from .core import require
    policy=capture_policy(task)
    if policy is None:
        require('schema_version' not in receipt,'Unsupported check receipt version/policy')
        return
    require(type(receipt.get('schema_version')) is int and receipt['schema_version']==2,'Expected bounded check receipt version2')
    require(receipt.get('task')==task['id'] and type(receipt.get('stable')) is bool and type(receipt.get('passed')) is bool,'Invalid bounded check receipt')
    import math
    try:finite=type(receipt.get('at')) in (int,float) and math.isfinite(receipt['at']) and receipt['at']>=0
    except OverflowError:finite=False
    require(finite,'Invalid receipt timestamp')
    require(all(isinstance(receipt.get(k),str) and len(receipt[k])==64 and all(c in '0123456789abcdef' for c in receipt[k]) for k in ('inputs','snapshot')),'Invalid receipt input/snapshot envelope')
    cap=receipt.get('capture');results=receipt.get('results')
    keys={'version','mode','max_bytes','retained_bytes','observed_bytes','cleanup_discarded_bytes','complete','state','planned','attempted','executed','skipped'}
    require(isinstance(cap,dict) and set(cap)==keys and isinstance(results,list) and results,'Invalid bounded capture structure')
    require(type(cap['version']) is int and cap['version']==1 and cap['mode']==policy['mode'] and cap['max_bytes']==policy['max_bytes'],'Capture policy mismatch')
    numeric=['max_bytes','retained_bytes','observed_bytes','cleanup_discarded_bytes','planned','attempted','executed']
    require(all(type(cap[k]) is int and cap[k]>=0 for k in numeric),'Invalid capture accounting')
    require(cap['planned']==len(task['checks']) and cap['attempted']==len(results)<=cap['planned'],'Invalid attempted/planned counts')
    require(cap['retained_bytes']<=policy['max_bytes'] and cap['observed_bytes']<=policy['max_bytes']+65536,'Capture budget exceeded')
    require(type(cap['complete']) is bool and isinstance(cap['skipped'],list),'Invalid capture completion')
    retained=observed=launched=0;abort=None;launch_failure=False
    rkeys={'state','complete','stdout_observed_bytes','stderr_observed_bytes','stdout_retained_bytes','stderr_retained_bytes','stdout_base64','stderr_base64'}
    for index,r in enumerate(results,1):
        require(isinstance(r,dict) and type(r.get('check')) is int and r['check']==index and type(r.get('launched')) is bool,'Invalid check attempt identity')
        require(r.get('argv')==task['checks'][index-1],'Check argv mismatch')
        require('exit_code' in r and (r.get('exit_code') is None or type(r['exit_code']) is int),'Invalid process exit')
        c=r.get('capture');require(isinstance(c,dict) and set(c)==rkeys,'Invalid stream capture')
        require(type(c['complete']) is bool and c['state'] in {'complete','launch-failed','limit-exceeded','timeout','capture-failed'},'Invalid capture state')
        require(c['complete']==(c['state']=='complete'),'Inconsistent stream completion')
        if r['launched']:
            launched+=1;require(type(r['exit_code']) is int and c['state']!='launch-failed','Unobserved process cannot publish accepted result')
        else:
            require(r['exit_code'] is None and c['state']=='launch-failed','Invalid failed launch');launch_failure=True
        for stream in ('stdout','stderr'):
            n=c[stream+'_retained_bytes'];o=c[stream+'_observed_bytes'];encoded=c[stream+'_base64']
            require(type(n) is int and type(o) is int and 0<=n<=o and n<=policy['max_bytes'],'Invalid stream byte counts')
            require(isinstance(encoded,str) and len(encoded)<=4*((n+2)//3),'Invalid encoded capture length')
            try:raw=base64.b64decode(encoded,validate=True)
            except (ValueError,binascii.Error):raise Error('Invalid encoded capture') from None
            require(len(raw)==n and r.get(stream)==raw.decode('utf-8',errors='replace'),'Capture bytes/preview mismatch')
            if c['complete']:require(n==o,'Complete capture discarded observed output')
            if not r['launched']:require(n==o==0,'Unlaunched check has captured output')
            retained+=n;observed+=o
        if c['state'] in ('limit-exceeded','timeout','capture-failed'):
            require(index==len(results),'Checks continued after terminal capture condition');abort=c['state']
    require(cap['retained_bytes']==retained and cap['observed_bytes']==observed and cap['executed']==launched,'Inconsistent capture totals')
    state=abort or ('launch-failed' if launch_failure else 'complete')
    complete=state=='complete' and len(results)==len(task['checks'])
    require(cap['state']==state and cap['complete']==complete,'Inconsistent capture outcome')
    if state=='limit-exceeded':require(retained==policy['max_bytes'] and observed>retained,'Invalid limit outcome')
    else:require(observed==retained,'Capture lost observed bytes')
    if complete:require(cap['cleanup_discarded_bytes']==0,'Complete capture discarded cleanup output')
    skipped=[{'check':i,'reason':abort} for i in range(len(results)+1,len(task['checks'])+1)]
    require(all(isinstance(x,dict) and set(x)=={'check','reason'} and type(x['check']) is int for x in cap['skipped']),'Invalid skipped entries')
    require(cap['skipped']==skipped and (not skipped or abort is not None),'Invalid skipped check accounting')
    require(receipt['passed']==(receipt['stable'] and complete and all(r['exit_code']==0 for r in results)),'Inconsistent verification success')


def bounded_summary_counts(receipt):
    results=receipt['results']
    passed=sum(r['exit_code']==0 and r['capture']['complete'] for r in results)
    return {'attempted':len(results),'executed':receipt['capture']['executed'],'passed':passed,
            'failed':len(results)-passed,'skipped':len(receipt['capture']['skipped'])}
