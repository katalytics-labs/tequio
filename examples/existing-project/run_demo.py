#!/usr/bin/env python3
"""Deterministic brownfield lifecycle fixture; no model or independent-review evidence."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from task_review_fixture import prepare_demo_reviews

SOURCE=Path(__file__).resolve().parents[2]
EXAMPLE=Path(__file__).resolve().parent

def run(project,*args,expected=0):
    command=[sys.executable,str(project/'bin/tequio'),'--project',str(project),'--workspace','demo',*args]
    result=subprocess.run(command,capture_output=True,text=True,timeout=60)
    if result.returncode!=expected:
        raise RuntimeError('Command failed: '+args[0]+'\n'+result.stderr+result.stdout)
    return json.loads(result.stdout if expected==0 else result.stderr)

def demonstrate(project):
    project.mkdir(parents=True,exist_ok=False)
    install=subprocess.run([sys.executable,str(SOURCE/'bin/tequio'),'install',str(project)],capture_output=True,text=True,timeout=60)
    if install.returncode:raise RuntimeError(install.stderr)
    shutil.copy2(EXAMPLE/'task_list.py',project/'task_list.py')
    (project/'tests').mkdir();shutil.copy2(EXAMPLE/'test_task_list.py',project/'tests/test_task_list.py')
    (project/'docs').mkdir();shutil.copy2(EXAMPLE/'usage.md',project/'docs/usage.md')
    baseline=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=project,capture_output=True,text=True,timeout=60)
    if baseline.returncode != 1 or 'FAILED (failures=2)' not in baseline.stderr:
        raise RuntimeError('Expected exactly the two archive-filter regressions before correction: '+baseline.stderr)
    print('Baseline: two archive filtering regressions fail; nearby tests pass.')
    run(project,'workspace','--brief',str(EXAMPLE/'brief.md'))
    workspace=project/'.tequio/workspaces/demo'
    (workspace/'analysis/requirements.md').write_text('# Archive filter requirements\n\nR1 (briefs/brief.md): default and explicit false exclude archived rows. Observed task_list.py:visible_tasks predicate uses `is not None`, which accepts false. R2: explicit true preserves both rows in input order. R3: empty input and input immutability remain unchanged; tests/test_task_list.py demonstrates these boundaries. No storage or schema change.\n')
    (workspace/'specs/change.md').write_text('# Filter contract\n\nR1: for boolean include_archived, include a row iff the flag is true or archived is false. R2/R3 preserve input order and rows. Scope: task_list.py:visible_tasks and docs/usage.md; malformed row validation remains outside this fix. Acceptance: both observed filtering failures become passing and nearby true/empty/immutability tests remain passing.\n')
    run(project,'record','analysis')
    (workspace/'plans/delivery.md').write_text('# Delivery\n\nR1 maps to one bounded task correcting task_list.py:visible_tasks boolean filtering and updates docs/usage.md. R2/R3 map to existing regression tests preserving row schema, ordering and immutability. Integration owner: demo-script. No new architecture or dependencies. Verify real behavior, reconcile each source to code and docs, then obtain genuine independent review before closure.\n')
    run(project,'record','plan')
    task={'id':'DEMO-1','title':'Fix archive filtering','outcome':'Archived tasks are hidden by default and explicit false','scope':'One existing filter, its regression tests and current usage contract','exclusions':'No model calls, network, services or specialist generation','sources':['briefs/brief.md','analysis/requirements.md','specs/change.md','plans/delivery.md'],'depends_on':[],'reads':['tests'],'writes':['task_list.py','docs/usage.md'],'specialists':[],'risk':'normal','security_assessment':{'surfaces':[],'reason':'This bounded deterministic replay changes no authentication, trust boundary or deployment behavior and uses only isolated local fixture data.'},'stage':'ready','documentation':{'mode':'update','paths':['docs/usage.md'],'reason':'This correction changes archive visibility and its maintained usage contract.'},'acceptance':['Default and explicit false hide archived rows','True includes both in order; empty input and immutability remain valid','Documentation states implemented behavior and limitations'],'checks':[[sys.executable,'-m','unittest','discover','-s','tests','-v']],'handoff':'Return actual tests/docs evidence and request a separate reviewer; never invent one'}
    tasks=workspace/'tasks/demo.json';tasks.write_text(json.dumps([task],indent=2))
    prepare_demo_reviews(project,workspace,tasks,run)
    run(project,'import-tasks',str(tasks))
    claim=run(project,'claim','--owner','demo-script','--task','DEMO-1');token=claim['token']
    target=project/'task_list.py'
    target.write_text(target.read_text().replace('include_archived is not None', 'include_archived'))
    (project/'docs/usage.md').write_text('# Task listing\n\nvisible_tasks accepts rows with id and boolean archived. By default or with explicit false, it excludes archived rows. Explicit true includes all rows in input order. It does not mutate input rows. Malformed-row validation is outside this helper contract.\n')
    verified=run(project,'verify','DEMO-1','--token',token)
    assert verified['passed'],'Actual archive-filter checks must pass'
    missing=run(project,'complete','DEMO-1','--token',token,'--summary','Attempt before documentation/review',expected=2)
    assert 'Documentation' in missing['error']
    reconciliation={'summary':'Compared every focused source with the corrected archive predicate, four passing regression/nearby tests and updated existing usage contract. No broader product changes are claimed.','deviations':[],'reconciliation':[{'source':s,'actual':['task_list.py','tests/test_task_list.py'],'docs':['docs/usage.md'],'disposition':'implemented','notes':'Actual tests exercise default/false filtering, explicit true ordering, empty input and non-mutation. The maintained usage contract states those behaviors; malformed rows remain excluded.'} for s in task['sources']]}
    report=workspace/'reviews/docs.json';report.write_text(json.dumps(reconciliation,indent=2))
    run(project,'record-docs','DEMO-1','--token',token,'--report','reviews/docs.json')
    review_missing=run(project,'complete','DEMO-1','--token',token,'--summary','Attempt before independent review',expected=2)
    assert 'review' in review_missing['error'].lower()
    run(project,'checkpoint','--summary','Four real archive-filter tests pass; docs reconciled; genuinely independent review remains unavailable in this deterministic demo','--next','Have a separate reviewer inspect actual code/tests/docs, register their real report, then close only if accepted')
    state=run(project,'status')
    assert state['tasks'][0]['status']=='review'
    print('PASS: installed snapshot; analysis/plan; detailed task; actual brownfield correction/tests; docs reconciliation.')
    print('PASS: completion refused missing docs and missing independent review.')
    print('State: review-pending. Next: obtain a genuine independent correctness report before closure.')
    print('Project:',project)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='New directory to retain the demo (must not exist)')
    args=parser.parse_args()
    if args.output:
        if args.output.exists():parser.error('--output must be a new directory; existing work is never overwritten')
        demonstrate(args.output.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix='tequio-demo-') as temp:
            demonstrate(Path(temp)/'project')
        print('Temporary example cleaned up. Use --output PATH to retain it.')

if __name__=='__main__':main()
