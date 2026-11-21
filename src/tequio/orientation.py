"""Pure workflow orientation: recommendations, never execution or authorization."""
from collections import Counter
from pathlib import Path
from .workflow import skill_id

def orient(phases,tasks,integration=None):
    outstanding=[t for t in tasks if t['status'] not in ('done','superseded')]
    counts=dict(Counter(t['status'] for t in tasks))
    def result(stage,skill,reason,task=None):
        return {'stage':stage,'next':{'skill':skill_id(skill),'reason':reason,'task':task},'outstanding':len(outstanding),'counts':counts,'scope':'Recorded workspace tasks only; not a product-readiness or release authorization claim.'}
    active=[t for t in outstanding if t['status'] in ('running','review')]
    operation=next((t for t in active if t.get('verification',{}).get('lock_held')
                    or t.get('verification',{}).get('observed_group_live')
                    or (t.get('verification',{}).get('attempt') or {}).get('state') in ('preparing','launching','running','stopped','unknown')),None)
    if operation:
        return result('reconcile-active-work','resume','Inspect and reconnect to actual check handles before continuing; do not duplicate verification, recover or kill from an observation.',operation['id'])
    if any(t['lease_expired'] for t in active) or (active and any(v!='current' for v in phases.values())):
        return result('reconcile-active-work','resume','Inspect actual agent/process handles and changed inputs before replanning or recovery; claims are not proof of live work.',active[0]['id'])
    migration=next((t for t in outstanding if t.get('security',{}).get('state')=='migration-required'),None)
    if migration:return result('task-contract-migration','replan','Security contract migration-required: inspect live work, release active ownership, then replan with explicit assessment and candidate scope.',migration['id'])
    legacy=next((t for t in active if not t.get('documentation_policy_valid',True)),None)
    if legacy:return result('task-contract-migration','replan','This active task lacks the current documentation-impact contract. Inspect live work, release the claim deliberately, then replace unfinished tasks through replan; do not edit the task database.',legacy['id'])
    if phases['analysis']!='current':
        return result('analysis','analyze' if phases['analysis']=='missing' else 'replan','Complete source-linked analysis.' if phases['analysis']=='missing' else 'Analysis inputs changed; reconcile and refresh affected analysis/plan/todos.')
    if phases['plan']!='current':
        return result('planning','plan' if phases['plan']=='missing' else 'replan','Write the delivery plan.' if phases['plan']=='missing' else 'Plan changed; reconcile detailed tasks before continuing.')
    integration=integration or {}
    integration_task=next((t for t in active if any(
            item.get('task')==t['id'] and item.get('state') in
            ('pending-integration','integrated-unrecorded','blocked','needs-checks','needs-docs','needs-review')
            for item in integration.get('tasks',[]))),None)
    if active and (integration.get('state')=='invalid' or integration_task):
        target=integration_task if integration.get('state')!='invalid' else active[0]
        return result('reconcile-active-work','resume','Inspect the integration journal, actual target and required fresh post-integration evidence before continuing; do not infer closure, merge or recovery authority.',target['id'])
    review=next((t for t in active if t['status']=='review'),None)
    if review:
        if review.get('checks',{}).get('state','unavailable')!='current':
            return result('verification-required','implement','Verification is missing, failed, stale, invalid or unavailable. Finish outstanding implementation/documentation edits, then verify the stable candidate before recording reconciliation or obtaining review.',review['id'])
        if review['documentation']['state']!='current':
            return result('documentation-and-review','implement','Checks are current. Reconcile actual behavior with the plan and documentation; if further implementation/docs edits are needed, verify the stable candidate again before recording reconciliation and obtaining independent review.',review['id'])
        reviewed=review.get('review',{})
        if reviewed.get('state')=='current':return result('ready-for-closure','implement','Recorded checks, documentation and required reviews are current; the owner can close the task and checkpoint after a final state check.',review['id'])
        if reviewed.get('state') in ('findings','stale'):return result('review-follow-up','implement','Resolve current findings or refresh stale evidence before another review: '+reviewed.get('reason','; '.join(reviewed.get('findings',[]))),review['id'])
        if reviewed.get('kind')=='security':return result('security-review','redteam','Correctness review is recorded; the required independent adversarial review remains outstanding.',review['id'])
        return result('review','review','Review the actual change, acceptance evidence and documentation reconciliation before closure.',review['id'])
    if active:
        return result('implementation','implement','Reconnect to the assigned owner and finish the bounded task; do not claim a duplicate.',active[0]['id'])
    ready=next((t for t in outstanding if t['dispatchable']),None)
    if ready:return result('ready-to-implement','implement','Execute the next ready bounded outcome, including docs, verification and review.',ready['id'])
    blocked=next((t for t in outstanding if t['status']=='blocked'),None)
    if blocked:return result('blocked','status','Resolve the recorded blocker/resumption condition before recovery: '+(blocked['reason'] or 'No reason recorded'),blocked['id'])
    if any(t['status']=='ready' for t in outstanding):
        task=next(t for t in outstanding if t['status']=='ready')
        reasons='; '.join(task.get('waiting_on',[]))
        if 'specialist' in reasons.lower():return result('specialist-preparation','write-specialists',reasons,task['id'])
        if 'documentation' in reasons.lower():return result('todo-preparation','replan','Reconcile the task documentation impact before replacing the immutable ready task: '+reasons,task['id'])
        return result('waiting-for-prerequisites','status','Inspect unmet dependencies, specialist qualification, documentation impact, changed outputs or peer ownership: '+'; '.join(task.get('waiting_on',[])),task['id'])
    drafts=[t for t in outstanding if t['status']=='draft']
    draft=next((t for t in drafts if t.get('draft_readiness',{}).get('state')=='recorded'),drafts[0] if drafts else None)
    if draft:
        recorded=draft.get('draft_readiness',{}).get('state')=='recorded'
        reason=('Inspect this draft’s sourced resolution action and assess its recorded category; metadata alone does not prove an owner answer is required.' if recorded else 'Reconcile this draft’s missing or invalid decision record from its actual sources; preserve unknowns and do not invent an owner question.')
        return result('todo-preparation','write-todos',reason,draft['id'])
    if outstanding:return result('todo-preparation','write-todos','Refine provisional tasks and qualifications into detailed ready work; do not execute draft tasks.')
    if counts.get('done'):
        return result('recorded-work-complete','review','Check integrated milestone acceptance and remaining scope before choosing further work or release preparation. Individual task closure is not proof the whole product is ready.')
    return result('todo-preparation','write-todos','Turn the current plan into detailed bounded tasks; the user need not manage agent internals.')

def no_workspace(project,workspace):
    from .core import name,require
    name(workspace)
    root=Path(project).resolve();require(root.is_dir(),'Project directory missing');folder=root/'.tequio/workspaces'
    available=sorted(p.name for p in folder.iterdir() if p.is_dir() and not p.is_symlink() and (p/'state.sqlite3').is_file()) if folder.is_dir() and not folder.is_symlink() else []
    return {'workspace':None,'requested_workspace':workspace,'available_workspaces':available,'tasks':[],'workflow':{'stage':'select-workspace' if available else 'intake','next':{'skill':skill_id('status' if available else 'brief'),'reason':'Select the intended workspace explicitly; no recent-workspace guessing.' if available else 'Shape an idea with tequio-briefing, or use tequio-explore with an existing brief; no workspace has been created by this check.','task':None},'outstanding':None},'note':'Read-only orientation; no tasks, workspaces or documentation were created.'}
