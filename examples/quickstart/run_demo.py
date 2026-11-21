#!/usr/bin/env python3
"""Reproducible pre-authored lifecycle smoke demo; no generated/fake review."""
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
    run(project,'workspace','--brief',str(EXAMPLE/'brief.md'))
    workspace=project/'.tequio/workspaces/demo'
    (workspace/'analysis/requirements.md').write_text('# Requirements\n\nThe helper preserves Unicode, collapses whitespace, rejects empty text with ValueError, rejects non-text with TypeError, and documents current behavior. Four focused tests must demonstrate these cases.\n')
    run(project,'record','analysis')
    (workspace/'plans/delivery.md').write_text('# Delivery\n\nOne bounded task implements normalizer.py, four behavior/error tests and docs/usage.md. Use only the standard library. Verify real behavior, reconcile each source to code and docs, then obtain genuine independent review before closure.\n')
    run(project,'record','plan')
    task={'id':'DEMO-1','title':'Implement label normalization','outcome':'Text labels normalize predictably with explicit error behavior','scope':'One helper, tests and current usage contract','exclusions':'No model calls, network, services or specialist generation','sources':['briefs/brief.md','analysis/requirements.md','plans/delivery.md'],'depends_on':[],'reads':[],'writes':['normalizer.py','tests','docs/usage.md'],'specialists':[],'risk':'normal','security_assessment':{'surfaces':[],'reason':'This bounded deterministic replay changes no authentication, trust boundary or deployment behavior and uses only isolated local fixture data.'},'stage':'ready','documentation':{'mode':'update','paths':['docs/usage.md'],'reason':'This helper introduces public behavior and errors that users must understand.'},'acceptance':['Whitespace normalizes; Unicode is preserved','Empty and non-text values fail explicitly','Documentation states implemented behavior and limitations'],'checks':[[sys.executable,'-m','unittest','discover','-s','tests','-v']],'handoff':'Return actual tests/docs evidence and request a separate reviewer; never invent one'}
    tasks=workspace/'tasks/demo.json';tasks.write_text(json.dumps([task],indent=2))
    prepare_demo_reviews(project,workspace,tasks,run)
    run(project,'import-tasks',str(tasks))
    claim=run(project,'claim','--owner','demo-script','--task','DEMO-1');token=claim['token']
    shutil.copy2(EXAMPLE/'normalizer.py',project/'normalizer.py')
    (project/'tests').mkdir();shutil.copy2(EXAMPLE/'test_normalizer.py',project/'tests/test_normalizer.py')
    (project/'docs').mkdir();(project/'docs/usage.md').write_text('# Label normalization\n\nnormalize_label accepts text, trims and collapses whitespace, and preserves Unicode. Empty text raises ValueError; non-text raises TypeError. It performs no case conversion, translation or network access.\n')
    verified=run(project,'verify','DEMO-1','--token',token)
    assert verified['passed'],'Actual helper checks must pass'
    missing=run(project,'complete','DEMO-1','--token',token,'--summary','Attempt before documentation/review',expected=2)
    assert 'Documentation' in missing['error']
    reconciliation={'summary':'Compared the brief and delivery task to the actual helper, its four passing tests and documented behavior. No planned feature is represented as shipped beyond this bounded helper.','deviations':[],'reconciliation':[{'source':s,'actual':['normalizer.py','tests/test_normalizer.py'],'docs':['docs/usage.md'],'disposition':'implemented','notes':'Actual tests exercise whitespace, Unicode, empty text and non-text failures; the usage document states exactly these behaviors and excludes transformations not implemented.'} for s in task['sources']]}
    report=workspace/'reviews/docs.json';report.write_text(json.dumps(reconciliation,indent=2))
    run(project,'record-docs','DEMO-1','--token',token,'--report','reviews/docs.json')
    review_missing=run(project,'complete','DEMO-1','--token',token,'--summary','Attempt before independent review',expected=2)
    assert 'review' in review_missing['error'].lower()
    run(project,'checkpoint','--summary','Four real helper tests pass; docs reconciled; genuinely independent review remains unavailable in this deterministic demo','--next','Have a separate reviewer inspect actual code/tests/docs, register their real report, then close only if accepted')
    state=run(project,'status')
    assert state['tasks'][0]['status']=='review'
    assert state['workflow']['next']['skill']=='tequio-inspect'
    print('PASS: installed snapshot; analysis/plan; detailed task; actual helper/tests; docs reconciliation.')
    print('PASS: completion refused missing docs and missing independent review.')
    print('State: review-pending. Next: $tequio-inspect with a genuine independent reviewer.')
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
