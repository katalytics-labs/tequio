"""Non-authoritative context observations and explicit workspace routing configuration."""
import contextlib
import hashlib
import json
import sqlite3
from .freshness import RUNTIME_FIELDS

VERSION = 1


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def valid_checkpoints(value):
    return (isinstance(value, dict)
            and set(value) == {'version', 'wall_minutes', 'max_verifications_per_task'}
            and type(value['version']) is int and value['version'] == 1
            and all(type(value[key]) is int and value[key] > 0
                    for key in ('wall_minutes', 'max_verifications_per_task')))


def valid_model_delegation(value):
    """Pure structural validation; identifiers imply no availability or authority."""
    def text(v, cap, trimmed=False):
        return isinstance(v, str) and bool(v.strip()) and (not trimmed or v == v.strip()) and len(v) <= cap and v.isprintable()
    if not isinstance(value, dict) or set(value) != {'version', 'enabled', 'available_choices', 'routing_preferences', 'review_diversity', 'fallback'}:
        return False
    if type(value['version']) is not int or value['version'] != 1 or type(value['enabled']) is not bool:
        return False
    choices = value['available_choices']; preferences = value['routing_preferences']
    if not isinstance(choices, list) or len(choices) > 32 or not all(text(v, 256, True) for v in choices) or len(set(choices)) != len(choices):
        return False
    if not isinstance(preferences, list) or len(preferences) > 32:
        return False
    works = set()
    for item in preferences:
        if not isinstance(item, dict) or set(item) != {'work', 'choice', 'reason'}:
            return False
        if not text(item['work'], 1024) or not text(item['reason'], 1024) or not isinstance(item['choice'], str) or item['choice'] not in choices or item['work'] in works:
            return False
        works.add(item['work'])
    diversity = value['review_diversity']; fallback = value['fallback']
    return (isinstance(diversity, dict) and set(diversity) == {'basis', 'correctness', 'security'}
            and diversity['basis'] == 'different-model'
            and all(isinstance(diversity[k], str) and diversity[k] in ('optional', 'preferred', 'required') for k in ('correctness', 'security'))
            and isinstance(fallback, dict) and set(fallback) == {'unavailable_choice', 'unmet_preferred_diversity'}
            and isinstance(fallback['unavailable_choice'], str) and fallback['unavailable_choice'] in ('host-default', 'stop')
            and isinstance(fallback['unmet_preferred_diversity'], str) and fallback['unmet_preferred_diversity'] in ('record-and-continue', 'review-pending'))


def model_delegation_defaults():
    return {'version': 1, 'enabled': True, 'available_choices': [], 'routing_preferences': [],
            'review_diversity': {'basis': 'different-model', 'correctness': 'optional', 'security': 'preferred'},
            'fallback': {'unavailable_choice': 'host-default', 'unmet_preferred_diversity': 'record-and-continue'}}


def _policy_bytes(path):
    """Bounded nonblocking leaf read. No paths, locks or metadata are created."""
    import os
    import stat
    fd = None
    try:
        fd = os.open(path / 'run-policy.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > 1048576:
            return 'unreadable', None, None
        chunks = []; remaining = 1048577
        while remaining:
            data = os.read(fd, min(65536, remaining))
            if not data: break
            chunks.append(data); remaining -= len(data)
        raw = b''.join(chunks)
        if len(raw) > 1048576: return 'unreadable', None, None
        return 'read', raw, (info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode))
    except FileNotFoundError:
        return 'missing', None, None
    except OSError:
        return 'unreadable', None, None
    finally:
        if fd is not None: os.close(fd)


def _policy_observation(path):
    state, raw, identity = _policy_bytes(path)
    if state != 'read': return {'state': state, 'digest': None}, None, raw, identity
    try:
        observation, value = _parsed_policy(raw)
    except RecursionError:
        return {'state': 'invalid', 'digest': hashlib.sha256(raw).hexdigest()}, None, raw, identity
    return observation, value, raw, identity


def _parsed_policy(raw):
    try:
        value = json.loads(raw)
        fingerprint = digest(value)
    except (ValueError, UnicodeError):
        return {'state': 'invalid', 'digest': hashlib.sha256(raw).hexdigest()}, None
    valid = isinstance(value, dict)
    if valid:
        valid = (value.get('mode') in ('next-chunk', 'backlog')
                 and isinstance(value.get('tasks'), list)
                 and all(isinstance(x, str) and x.strip() for x in value['tasks'])
                 and len(set(value['tasks'])) == len(value['tasks'])
                 and isinstance(value.get('scope'), str) and bool(value['scope'].strip())
                 and (value.get('integration_branch') is None or isinstance(value['integration_branch'], str))
                 and all(type(value.get(k)) is bool for k in ('allow_local_commits', 'allow_local_merges', 'allow_push'))
                 and type(value.get('parallel_writers')) is int and value['parallel_writers'] > 0
                 and (value['mode'] != 'backlog' or bool(value['tasks']))
                 and ('execution_checkpoints' not in value or valid_checkpoints(value['execution_checkpoints']))
                 and ('model_delegation' not in value or valid_model_delegation(value['model_delegation'])))
    return {'state': 'valid' if valid else 'invalid', 'digest': fingerprint}, value


def policy(path):
    # Existing observers retain their legacy read/parser semantics. The bounded
    # safe-file contract belongs to the explicit routing operation.
    try:
        raw = (path / 'run-policy.json').read_bytes()
    except FileNotFoundError:
        return {'state': 'missing', 'digest': None}
    except OSError:
        return {'state': 'unreadable', 'digest': None}
    return _parsed_policy(raw)[0]


def routing(project, workspace_name, action='status'):
    """Explicit workspace configuration only; never selects models or claims work."""
    import os
    import tempfile
    from pathlib import Path
    from .core import Workspace, require, Error, name
    require(action in ('status', 'on', 'off'), 'Invalid routing action')
    mutation = action != 'status'
    if workspace_name is None:
        require(not mutation, 'Routing mutation requires an existing workspace')
        return {'schema_version': 1, 'workspace': None, 'configured': False, 'enabled': False,
                'policy_state': 'missing', 'changed': False, 'policy_digest': None}
    name(workspace_name)
    from .core import inside
    controller = inside(Path(project).resolve(), '.tequio/workspaces/' + workspace_name)
    if not (controller / 'state.sqlite3').exists():
        require(not mutation, 'Routing mutation requires an existing workspace')
        return routing(project, None, 'status')
    w = Workspace(project, workspace_name)
    def observe():
        observation, value, raw, identity = _policy_observation(w.path)
        configured = observation['state'] == 'valid' and 'model_delegation' in value
        result = {'schema_version': 1, 'workspace': workspace_name, 'configured': configured,
                  'enabled': value['model_delegation']['enabled'] if configured else False if observation['state'] in ('missing', 'valid') else None,
                  'policy_state': observation['state'], 'changed': False, 'policy_digest': observation['digest']}
        return result, value, raw, identity
    def needs_change(result):
        require(result['policy_state'] in ('valid', 'missing'), 'Routing policy invalid or unreadable; inspect without automatic repair')
        return result['enabled'] != (action == 'on')
    observed, value, raw, identity = observe()
    if not mutation: return observed
    if not needs_change(observed): return {**observed, 'previous_policy_digest': observed['policy_digest']}
    with w.claim_guard():
        # Re-read after coordination; do not base an update on a stale snapshot.
        observed, value, raw, identity = observe()
        if not needs_change(observed): return {**observed, 'previous_policy_digest': observed['policy_digest']}
        previous = observed['policy_digest']
        if value is None:
            value = {'mode': 'next-chunk', 'tasks': [], 'scope': 'Routing configuration only; grants no execution authorization.',
                     'integration_branch': None, 'allow_local_commits': False, 'allow_local_merges': False,
                     'allow_push': False, 'parallel_writers': 1,
                     'execution_checkpoints': {'version': 1, 'wall_minutes': 30, 'max_verifications_per_task': 3}}
        value.setdefault('model_delegation', model_delegation_defaults())
        value['model_delegation']['enabled'] = action == 'on'
        try:
            # Compact encoding avoids quadratic indentation expansion on deep input.
            published = json.dumps(value, ensure_ascii=True, separators=(',', ':')).encode() + b'\n'
        except RecursionError as exc:
            raise Error('Routing policy cannot be serialized; no replacement published') from exc
        require(len(published) <= 1048576, 'Updated routing policy exceeds size limit')
        temporary = None
        try:
            fd, temporary = tempfile.mkstemp(prefix='.run-policy-', dir=w.path)
            with os.fdopen(fd, 'wb') as handle:
                os.fchmod(handle.fileno(), identity[2] if identity else 0o600)
                handle.write(published); handle.flush(); os.fsync(handle.fileno())
            state2, raw2, identity2 = _policy_bytes(w.path)
            require(state2 == ('read' if raw is not None else 'missing') and raw2 == raw and identity2 == identity,
                    'Routing policy changed externally; update refused')
            os.replace(temporary, w.path / 'run-policy.json')
            temporary = None
            directory = os.open(w.path, os.O_RDONLY | os.O_DIRECTORY)
            try: os.fsync(directory)
            finally: os.close(directory)
        except OSError as exc:
            raise Error('Routing publication failed; inspect routing status before retry; replacement may have occurred') from exc
        finally:
            if temporary is not None:
                try: os.unlink(temporary)
                except FileNotFoundError: pass
        result, _, current_raw, _ = observe()
        require(current_raw == published and result['policy_state'] == 'valid', 'Routing publication changed or unavailable; inspect status')
        return {**result, 'changed': True, 'previous_policy_digest': previous}


def snapshot(workspace):
    with contextlib.closing(sqlite3.connect((workspace.path / 'state.sqlite3').as_uri() + '?mode=ro', uri=True)) as con:
        rows = con.execute('SELECT id,body,status FROM tasks ORDER BY id').fetchall()
    definitions = []
    from .revision import binding
    for tid, body, state in rows:
        task = json.loads(body)
        item = (tid, {k: v for k, v in task.items() if k not in RUNTIME_FIELDS})
        edge = binding(workspace, task)
        if edge is not None:
            item = (*item, edge)
        definitions.append(item)
    return {'policy': policy(workspace.path), 'task_ids': [r[0] for r in rows],
            'task_scope_digest': digest(definitions),
            'progress_digest': digest([(tid, status) for tid, body, status in rows])}


def valid_context(value):
    def hash_value(x):
        return isinstance(x, str) and len(x) == 64 and all(c in '0123456789abcdef' for c in x)
    if not isinstance(value, dict) or not isinstance(value.get('policy'), dict):
        return False
    p = value['policy']
    if set(value) != {'policy', 'task_ids', 'task_scope_digest', 'progress_digest'} or set(p) != {'state', 'digest'}:
        return False
    return (p.get('state') in ('valid', 'invalid', 'missing', 'unreadable')
            and (hash_value(p.get('digest')) if p['state'] in ('valid', 'invalid') else p.get('digest') is None)
            and isinstance(value.get('task_ids'), list) and all(isinstance(x, str) for x in value['task_ids'])
            and hash_value(value.get('task_scope_digest')) and hash_value(value.get('progress_digest')))


def resume(workspace):
    return _resume(workspace)


def _resume(workspace, checkpoint=None):
    current = workspace.status() if checkpoint is None else workspace.status(_checkpoint=checkpoint)
    context = snapshot(workspace)
    result = {'current': current, 'context': context, 'checkpoint': None,
              'checkpoint_issue': None, 'project_changed': None, 'inputs_changed': None,
              'policy_changed': None, 'task_scope_changed': None, 'task_progress_changed': None, 'context_unknown': True,
              'action': 'Reconcile run policy and approved task scope with current user authorization, files, receipts and actual agent/process handles before continuation. Context digests are observations, never permission; lease expiry is not process termination.'}
    try:
        if checkpoint is not None:
            if checkpoint.get('issue'):
                result['checkpoint_issue']={'code':checkpoint['issue']}
                return result
            saved=json.loads(checkpoint['raw'])
        else:
            saved = json.loads((workspace.path / 'checkpoint.json').read_bytes())
    except FileNotFoundError:
        result['checkpoint_issue'] = {'code': 'missing'}
        return result
    except (ValueError, UnicodeError, OSError):
        result['checkpoint_issue'] = {'code': 'unreadable-or-invalid-json'}
        return result
    if not isinstance(saved, dict):
        result['checkpoint_issue'] = {'code': 'invalid-shape'}
        return result
    required = {'at': (int, float), 'summary': (str,), 'next_action': (str,), 'project_snapshot': (str,), 'inputs': (str,), 'status': (dict,)}
    if any(k not in saved or not isinstance(saved[k], types) or isinstance(saved[k], bool) for k, types in required.items()):
        result['checkpoint_issue'] = {'code': 'invalid-shape'}
        return result
    if 'checkpoint_version' in saved and (type(saved['checkpoint_version']) is not int or saved['checkpoint_version'] != VERSION):
        result['checkpoint_issue'] = {'code': 'unsupported-version'}
        return result
    legacy = 'checkpoint_version' not in saved
    if not legacy and not valid_context(saved.get('context')):
        result['checkpoint_issue'] = {'code': 'invalid-context'}
        return result
    from .core import tree_hash
    result.update(checkpoint=saved, project_changed=saved['project_snapshot'] != tree_hash(workspace.project, project=True), inputs_changed=saved['inputs'] != workspace.inputs())
    if legacy:
        result['checkpoint_issue'] = {'code': 'legacy-context-unknown'}
    else:
        result.update(context_unknown=False, policy_changed=saved['context']['policy'] != context['policy'], task_scope_changed=saved['context']['task_scope_digest'] != context['task_scope_digest'], task_progress_changed=saved['context']['progress_digest'] != context['progress_digest'])
    return result


def _checkpoint_bytes(workspace):
    """Pin every directory from the project anchor; never resolve a parent alias."""
    import os
    import stat
    from .core import Error
    fd=None;parent_safe=False
    try:
        flags=os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_NONBLOCK
        fd=os.open('/',flags)
        for part in workspace.project.parts[1:]+('.tequio','workspaces',workspace.path.name):
            child=os.open(part,flags,dir_fd=fd);os.close(fd);fd=child
        parent_safe=True
        final=os.open('checkpoint.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        with os.fdopen(final,'rb') as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):raise Error('Unsafe checkpoint')
            raw=f.read()
        return {'raw':raw,'hash':hashlib.sha256(raw).hexdigest(),'issue':None,'parent_safe':True}
    except FileNotFoundError:return {'raw':None,'hash':None,'issue':'missing','parent_safe':parent_safe}
    except Error:return {'raw':None,'hash':None,'issue':'unsafe-checkpoint','parent_safe':parent_safe}
    except OSError:return {'raw':None,'hash':None,'issue':'unsafe-checkpoint','parent_safe':parent_safe}
    finally:
        if fd is not None:os.close(fd)


def _unavailable_compact(workspace):
    return {'schema_version':1,'workspace':workspace.path.name,
            'workflow':{'stage':'inspect-current-context','next':{'skill':'tequio-pickup','task':None,'reason_code':'inspect-current-context'}},
            'counts':{},'changes':dict.fromkeys(('project_changed','inputs_changed','policy_changed','task_scope_changed','task_progress_changed'))|{'context_unknown':True},
            'context':{'policy':{'state':'unreadable','digest':None},'task_scope_digest':None,'progress_digest':None},
            'checkpoint':{'state':'unavailable','issue_code':'unsafe-checkpoint','reference':None},'focus':None,
            'active':{'count':None,'items':[],'omitted':None},
            'execution_checkpoints':{'state':'unavailable','limits':None,'clock':'unavailable','elapsed_wall_seconds':None,'checkpoint_required':True,'reasons':[{'reason':'observation-incomplete'}],'omitted_reasons':0},
            'usage':{'tokens':None,'cost':None,'source':'unavailable'}}


def compact_resume(workspace):
    """Fixed-field delivery, not a smaller parsing workload or authorization."""
    from .core import name,Error
    from .workflow import WORKFLOW_SKILLS
    saved=_checkpoint_bytes(workspace)
    if not saved.get('parent_safe',True):return _unavailable_compact(workspace)
    r=_resume(workspace,saved);current=r['current'];bad=False
    def ident(value):
        nonlocal bad
        if value is None:return None
        try:return name(value)
        except Error:bad=True;return None
    def enum(value,allowed,default='unavailable'):
        nonlocal bad
        try:
            if value in allowed:return value
        except TypeError:pass
        bad=True;return default
    states={'draft','ready','running','review','blocked','done','superseded'}
    stages={'reconcile-active-work','task-contract-migration','analysis','planning','verification-required','documentation-and-review','ready-for-closure','review-follow-up','security-review','review','implementation','ready-to-implement','blocked','specialist-preparation','todo-preparation','waiting-for-prerequisites','recorded-work-complete'}
    workflow=current['workflow'];stage=enum(workflow.get('stage'),stages,'inspect-current-context');nxt=workflow.get('next',{})
    skill=nxt.get('skill');skill=enum(skill,WORKFLOW_SKILLS,None)
    task_id=ident(nxt.get('task'))
    counts={}
    for key,value in workflow.get('counts',{}).items():
        if key not in states:bad=True;key='invalid'
        if type(value) is int and value>=0:counts[key]=counts.get(key,0)+value
        else:bad=True
    focus=None
    for t in current['tasks']:
        if task_id is not None and t['id']==task_id:
            focus={'task':task_id,'lifecycle':enum(t['status'],states,'invalid'),
                   'checks':{'state':enum(t.get('checks',{}).get('state'),{'current','missing','failed','stale','invalid','unavailable','not-observed'})},
                   'documentation':{'state':enum(t.get('documentation',{}).get('state'),{'current','outstanding','pending','recorded-historical','not-recorded-legacy'})},
                   'review':{'state':enum(t.get('review',{}).get('state'),{'current','pending','stale','findings','not-applicable'}),'kind':enum(t.get('review',{}).get('kind'),{None,'correctness','security'},None)},
                   'draft_readiness':{'state':enum(t.get('draft_readiness',{}).get('state'),{'recorded','legacy-unknown','invalid','not-applicable'}),'category':enum(t.get('draft_readiness',{}).get('category'),{None,'unresolved-product-decision','external-prerequisite','missing-specialist-qualification','explicit-deferral'},None)}}
    active=[t for t in current['tasks'] if t['status'] in ('running','review')];items=[]
    for t in active[:3]:
        v=t.get('verification',{});a=v.get('attempt') or {}
        items.append({'task':ident(t['id']),'lifecycle':t['status'],'verification':{
            'lock_held':v.get('lock_held') if type(v.get('lock_held')) is bool else None,
            'observed_group_live':v.get('observed_group_live') if type(v.get('observed_group_live')) is bool else None,
            'attempt_state':enum(a.get('state'),{None,'completed','stopped','reconciled','preparing','launching','running','unknown'},'unknown')}})
    cp=current['execution_checkpoints'];reasons=[]
    codes={'policy-missing','policy-invalid','policy-unreadable','policy-changed-during-read','legacy-unbudgeted','checkpoint-time-unknown','wall-time-checkpoint','verification-checkpoint','observation-incomplete'}
    raw_reasons=cp.get('reasons',[])
    if not isinstance(raw_reasons,list):bad=True;raw_reasons=[{'reason':'observation-incomplete'}]
    for reason in raw_reasons[:3]:
        if not isinstance(reason,dict):bad=True;reason={'reason':'observation-incomplete'}
        item={'reason':enum(reason.get('reason'),codes,'observation-incomplete')}
        if 'task' in reason:item['task']=ident(reason['task'])
        reasons.append(item)
    from .execution_progress import _finite_time
    elapsed=cp.get('elapsed_wall_seconds')
    if elapsed is not None and not _finite_time(elapsed):bad=True;elapsed=None
    limits=cp.get('limits')
    if limits is not None and not valid_checkpoints(limits):bad=True;limits=None
    required=cp.get('checkpoint_required')
    if type(required) is not bool:bad=True;required=True
    checkpoint={'state':enum(cp.get('state'),{'configured','legacy-unbudgeted','policy-missing','policy-invalid','policy-unreadable','policy-changed-during-read','unavailable'}),
                'limits':dict(limits) if limits is not None else None,
                'clock':enum(cp.get('clock'),{'missing','unusable','policy-unavailable','policy-drift','invalid-time','observed','unavailable'}),
                'elapsed_wall_seconds':elapsed,'checkpoint_required':required,
                'reasons':reasons,'omitted_reasons':max(0,len(raw_reasons)-3)}
    issue=(r['checkpoint_issue'] or {}).get('code')
    checkpoint_state={'missing':'missing','unsafe-checkpoint':'unavailable','unreadable-checkpoint':'unavailable','legacy-context-unknown':'legacy','unsupported-version':'unsupported'}.get(issue,'invalid' if issue else 'available')
    if issue not in {None,'missing','unsafe-checkpoint','unreadable-checkpoint','legacy-context-unknown','unsupported-version','unreadable-or-invalid-json','invalid-shape','invalid-context'}:bad=True;issue='invalid-context';checkpoint_state='invalid'
    def hash_or_none(value):
        nonlocal bad
        if isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value):return value
        bad=True;return None
    ctx=r['context'];pol=ctx['policy'];policy_digest=pol.get('digest')
    context={'policy':{'state':enum(pol.get('state'),{'valid','invalid','missing','unreadable'}),'digest':hash_or_none(policy_digest) if policy_digest is not None else None},'task_scope_digest':hash_or_none(ctx.get('task_scope_digest')),'progress_digest':hash_or_none(ctx.get('progress_digest'))}
    usage={'tokens':None,'cost':None,'source':'unavailable'}
    if current.get('usage')!=usage:bad=True
    changes={k:r[k] for k in ('project_changed','inputs_changed','policy_changed','task_scope_changed','task_progress_changed','context_unknown')}
    for key in changes:
        if changes[key] is not None and type(changes[key]) is not bool:bad=True;changes[key]=None
    if bad:changes['context_unknown']=True
    return {'schema_version':1,'workspace':workspace.path.name,
            'workflow':{'stage':stage,'next':{'skill':skill,'task':task_id,'reason_code':stage}},
            'counts':counts,'changes':changes,
            'context':context,
            'checkpoint':{'state':checkpoint_state,'issue_code':issue,'reference':{'path':'checkpoint.json','hash':saved['hash']} if saved['hash'] else None},
            'focus':focus,'active':{'count':len(active),'items':items,'omitted':max(0,len(active)-3)},
            'execution_checkpoints':checkpoint,'usage':usage}
