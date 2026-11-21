import argparse
import json
import sqlite3
from pathlib import Path
import sys
from .core import Error, Workspace, load
from .install import install, uninstall, bundle_root


def parser():
    p = argparse.ArgumentParser(prog='tequio', description='Project-local development workflow state and installation')
    p.epilog='Optional start: $tequio-briefing shapes an idea into a brief. Daily flow: $tequio-explore -> $tequio-design -> $tequio-tasks -> $tequio-build. Ask $tequio-status where you are and what is next. Documentation, checks, review and handoff run inside implementation; specialist factory only when needed.'
    p.add_argument('--project', default='.', help='Explicit project root (default current directory)')
    p.add_argument('--workspace', default='main', help='Explicit workspace (default main; never mtime-selected)')
    s = p.add_subparsers(dest='command', required=True)
    x = s.add_parser('install'); x.add_argument('target'); x.add_argument('--prefix', default=''); x.add_argument('--source', default=str(bundle_root()))
    x = s.add_parser('uninstall'); x.add_argument('target')
    x = s.add_parser('specialists', help='Project-owned specialist factory lifecycle')
    subs = x.add_subparsers(dest='specialist_command', required=True)
    subs.add_parser('list')
    q = subs.add_parser('register'); q.add_argument('package'); q.add_argument('--author', required=True); q.add_argument('--replace', action='store_true')
    for action in ['inspect','validate','exercise','qualify','publish']:
        q = subs.add_parser(action); q.add_argument('id')
        if action == 'exercise': q.add_argument('--fixture', required=True); q.add_argument('--timeout', type=int, default=120)
        if action == 'qualify': q.add_argument('--reviewer', required=True); q.add_argument('--report', required=True)

    x = s.add_parser('git', help='Optional Git worktree isolation; no repository is created')
    subs = x.add_subparsers(dest='git_command', required=True)
    subs.add_parser('status')
    q = subs.add_parser('configure'); q.add_argument('mode', choices=['shared', 'worktrees'])
    q = subs.add_parser('lane'); q.add_argument('name'); q.add_argument('--base', default='HEAD')

    x = s.add_parser('integration', help='Internal exact-commit recovery journal')
    subs = x.add_subparsers(dest='integration_command', required=True)
    q = subs.add_parser('plan'); q.add_argument('task'); q.add_argument('--token', required=True); q.add_argument('--lane', required=True); q.add_argument('--commit', required=True); q.add_argument('--branch', required=True)
    q = subs.add_parser('status'); q.add_argument('task', nargs='?')
    q = subs.add_parser('reconcile'); q.add_argument('task')

    x = s.add_parser('revise', help='Explicit reviewed scoped task revision; no implicit dependency aliases')
    subs = x.add_subparsers(dest='revision_command', required=True)
    for action in ('preview','prepare'):
        q = subs.add_parser(action); q.add_argument('--proposal',required=True)
        if action=='prepare': q.add_argument('--author',required=True)
    q = subs.add_parser('review'); q.add_argument('revision'); q.add_argument('--actor',required=True); q.add_argument('--kind',choices=['correctness','redteam'],required=True); q.add_argument('--report',required=True)
    q = subs.add_parser('status'); q.add_argument('revision')
    q = subs.add_parser('apply'); q.add_argument('--revision',required=True)

    x = s.add_parser('routing', help='Workspace-local optional model-routing preference toggle; never launches models')
    x.add_argument('routing_action', nargs='?', choices=['on','off','status'], default='status')

    x = s.add_parser('proof', help='Read-only concise task evidence'); x.add_argument('task', nargs='?')
    x = s.add_parser('progress', help='Read-only execution checkpoint and publication counts, not billing or acceptance'); x.add_argument('task', nargs='?')
    x = s.add_parser('workspace'); x.add_argument('--brief', required=True)
    x = s.add_parser('record'); x.add_argument('phase', choices=['analysis', 'plan'])
    x = s.add_parser('prepare-tasks'); x.add_argument('file'); x.add_argument('--author', required=True)
    x = s.add_parser('task-review-status'); x.add_argument('file')
    x = s.add_parser('review-tasks'); x.add_argument('batch'); x.add_argument('--actor', required=True); x.add_argument('--kind', choices=['correctness','redteam'], required=True); x.add_argument('--report', required=True)
    x = s.add_parser('import-tasks'); x.add_argument('file')
    x = s.add_parser('claim'); x.add_argument('--owner', required=True); x.add_argument('--task'); x.add_argument('--lease', type=int, default=1800)
    for cmd in ['heartbeat', 'verify', 'complete', 'release', 'review', 'record-docs']:
        x = s.add_parser(cmd); x.add_argument('task'); x.add_argument('--token', required=True)
        if cmd == 'record-docs': x.add_argument('--report', required=True)
        if cmd == 'verify':
            x.add_argument('--timeout', type=int, default=120)
            x.add_argument('--summary', action='store_true', help='Compact result and exact private receipt reference; full evidence is retained')
        if cmd == 'complete': x.add_argument('--summary', required=True)
        if cmd == 'release': x.add_argument('--reason', required=True); x.add_argument('--blocked', action='store_true')
        if cmd == 'review':
            x.add_argument('--actor', required=True); x.add_argument('--kind', choices=['correctness', 'security'], required=True); x.add_argument('--report', required=True); x.add_argument('--finding', action='append', default=[])
    x = s.add_parser('recover'); x.add_argument('task'); x.add_argument('--reason', required=True); x.add_argument('--stopped-check', action='store_true', help='Acknowledge inspected unknown launch is stopped; never overrides observed live lock/group')
    x = s.add_parser('verification-status', help='Read-only local verification observations'); x.add_argument('task')
    x = s.add_parser('replan'); x.add_argument('--reason', required=True)
    x = s.add_parser('checkpoint'); x.add_argument('--summary', required=True); x.add_argument('--next', required=True)
    for cmd in ['status', 'resume', 'doctor', 'hook']:
        q=s.add_parser(cmd)
        if cmd=='resume': q.add_argument('--summary',action='store_true',help='Compact private context; preserves unknowns and full default output')
        if cmd=='doctor':
            q.add_argument('--source',help='Explicit source comparison; never fetches or repairs')
            q.add_argument('--installation-only', action='store_true', help='Only installation health; omit workspace status and live lane inventory')
    return p


def verification_summary(envelope):
    """Fixed fields only; execution outcomes and identity come from publication."""
    receipt = envelope['receipt']
    if receipt.get('schema_version')==2:
        from .reporting import bounded_summary_counts
        diagnostics=envelope['diagnostics']
        return {'schema_version':2,'task':receipt['task'],'passed':receipt['passed'],'stable':receipt['stable'],'checks':bounded_summary_counts(receipt),'receipt':{k:envelope['reference'][k] for k in ('path','hash')},'diagnostics':diagnostics[:3],'omitted_diagnostics':max(0,len(diagnostics)-3),'capture':{k:receipt['capture'][k] for k in ('state','complete','max_bytes','retained_bytes','planned')}}
    passed = sum(r['exit_code'] == 0 for r in receipt['results'])
    diagnostics = envelope['diagnostics']
    return {'schema_version': 1, 'task': receipt['task'],
            'passed': receipt['passed'], 'stable': receipt['stable'],
            'checks': {'executed': len(receipt['results']), 'passed': passed,
                       'failed': len(receipt['results']) - passed},
            'receipt': {k: envelope['reference'][k] for k in ('path', 'hash')},
            'diagnostics': diagnostics[:3], 'omitted_diagnostics': max(0, len(diagnostics) - 3)}


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == 'install':
            result = install(args.source, args.target, args.prefix)
        elif args.command == 'uninstall':
            result = uninstall(args.target)
        elif args.command == 'doctor' and args.installation_only:
            from .git_isolation import _origin
            from .installation_health import health
            result = {'installation_health': health(_origin(args.project), args.source)}
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        elif args.command == 'git':
            from .git_isolation import detect, configure, create_lane, inspect_lanes
            if args.git_command == 'status':
                result = inspect_lanes(args.project)
            elif args.git_command == 'configure':
                result = configure(args.project, args.mode == 'worktrees')
            else:
                result = create_lane(args.project, args.name, args.base)

        else:
            from .git_isolation import inspect_lanes
            if args.command == 'integration':
                from .git_isolation import _origin
                isolation = {'control_root':str(_origin(args.project))}
            else:
                isolation = inspect_lanes(args.project)
            integration_read = args.command == 'integration' and args.integration_command == 'status'
            revision_read = args.command == 'revise' and args.revision_command in ('preview','status')
            routing_read = args.command == 'routing' and args.routing_action == 'status'
            if Path(args.project).resolve() != Path(isolation['control_root']).resolve() and not integration_read and not revision_read and not routing_read and args.command not in ('status', 'hook', 'doctor', 'resume', 'proof', 'progress', 'verification-status'):
                raise Error('Run task lifecycle commands with --project ' + isolation['control_root'] + '; lane checkouts share the original controller. Integrate lane changes before authoritative verification.')
            if integration_read or revision_read or routing_read or args.command in ('status', 'hook', 'doctor', 'resume', 'proof', 'progress', 'verification-status'):
                args.project = isolation['control_root']
            if args.command == 'routing':
                from .run_context import routing
                result = routing(args.project, args.workspace, args.routing_action)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return 0
            if (args.command in ('status','hook','doctor','proof','progress') or (args.command=='resume' and args.summary)) and not (Path(args.project).resolve()/'.tequio/workspaces'/args.workspace/'state.sqlite3').is_file():
                from .orientation import no_workspace
                result = no_workspace(args.project,args.workspace)
                from .git_isolation import inspect_lanes
                result['git_isolation'] = inspect_lanes(args.project)
                if args.command=='doctor':
                    from .installation_health import health
                    result['installation_health']=health(args.project,args.source)
                print(json.dumps(result,indent=2));return 0
            w = Workspace.create(args.project, args.workspace, args.brief) if args.command == 'workspace' else Workspace(args.project, args.workspace)
            if args.command == 'revise':
                from .revision import Revision
                revision = Revision(w)
                if args.revision_command=='preview': result=revision.preview(args.proposal)
                elif args.revision_command=='prepare': result=revision.prepare(args.proposal,args.author)
                elif args.revision_command=='review': result=revision.review(args.revision,args.actor,args.kind,args.report)
                elif args.revision_command=='status': result=revision.status(args.revision)
                else: result=revision.apply(args.revision)
            elif args.command == 'integration':
                from .integration import Journal
                journal = Journal(w)
                if args.integration_command == 'plan': result = journal.plan(args.task,args.token,args.lane,args.commit,args.branch)
                elif args.integration_command == 'reconcile': result = journal.reconcile(args.task)
                else: result = journal.status(args.task)
            elif args.command == 'proof':
                from .reporting import proof
                result = proof(args.project, args.workspace, args.task)
            elif args.command == 'progress':
                from .execution_progress import progress
                result = progress(args.project, args.workspace, args.task)
            elif args.command == 'specialists':
                from .specialists import Factory
                factory=Factory(w); action=args.specialist_command
                if action == 'list': result=factory.inspect()
                elif action == 'inspect': result=factory.inspect(args.id)
                elif action == 'register': result=factory.register(args.package,args.author,args.replace)
                elif action == 'validate': result=factory.validate(args.id)
                elif action == 'exercise': result=factory.exercise(args.id,args.fixture,args.timeout)
                elif action == 'qualify': result=factory.qualify(args.id,args.reviewer,args.report)
                elif action == 'publish': result=factory.publish(args.id)
            elif args.command == 'workspace': result = {'created': str(w.path)}
            elif args.command == 'record': result = w.record(args.phase)
            elif args.command in ('prepare-tasks','review-tasks','task-review-status'):
                from .task_review import TaskReview
                gate = TaskReview(w)
                if args.command == 'prepare-tasks': result = gate.prepare(args.file,args.author)
                elif args.command == 'review-tasks': result = gate.review(args.batch,args.actor,args.kind,args.report)
                else: result = gate.status(args.file)
            elif args.command == 'import-tasks': result = w.import_tasks(args.file)
            elif args.command == 'claim': result = w.claim(args.owner, args.task, args.lease)
            elif args.command == 'heartbeat': result = w.heartbeat(args.task, args.token)
            elif args.command == 'record-docs': result = w.document(args.task,args.token,args.report)
            elif args.command == 'verify':
                result = verification_summary(w._verify(args.task, args.token, args.timeout, summary=True)) if args.summary else w.verify(args.task, args.token, args.timeout)
            elif args.command == 'complete': result = w.complete(args.task, args.token, args.summary)
            elif args.command == 'release': result = w.release(args.task, args.token, args.reason, args.blocked)
            elif args.command == 'review': result = w.review(args.task, args.token, args.actor, args.kind, args.report, args.finding)
            elif args.command == 'recover': result = w.recover(args.task, args.reason, args.stopped_check)
            elif args.command == 'verification-status': result = w.verification_status(args.task)
            elif args.command == 'replan': result = w.replan(args.reason)
            elif args.command == 'checkpoint': result = w.checkpoint(args.summary, args.next)
            elif args.command == 'resume':
                if args.summary:
                    from .run_context import compact_resume
                    result=compact_resume(w)
                else:result=w.resume()
            elif args.command in ('status','doctor','hook'): result = w.status()
            else: raise Error('Unsupported command')
        if args.command=='doctor':
            from .installation_health import health
            result['installation_health']=health(args.project,args.source)
        if args.command in ('status', 'doctor', 'hook', 'resume') and not (args.command=='resume' and args.summary):
            from .git_isolation import inspect_lanes
            result['git_isolation'] = inspect_lanes(args.project)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if (args.command == 'verify' or (args.command == 'specialists' and args.specialist_command == 'exercise')) and not result['passed'] else 0
    except (Error, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
