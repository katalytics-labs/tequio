#!/usr/bin/env python3
"""Replay curated prebuilt application/tests and real lifecycle guards; no model calls."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from task_review_fixture import prepare_demo_reviews

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[1]

def run(project,*args,expected=0):
    proc=subprocess.run([sys.executable,str(project/'bin/tequio'),'--project',str(project),'--workspace','demo',*args],capture_output=True,text=True,timeout=60)
    if proc.returncode!=expected:raise RuntimeError(proc.stdout+proc.stderr)
    return json.loads(proc.stdout if expected==0 else proc.stderr)

def demonstrate(root):
    root.mkdir(parents=True,exist_ok=False)
    app=root/'application';shutil.copytree(HERE/'solution',app)
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=app,capture_output=True,text=True,timeout=60)
    if tests.returncode:raise RuntimeError(tests.stdout+tests.stderr)
    cli=subprocess.run([sys.executable,'-m','siteledger.cli','sample.json','--place','Kitchen'],cwd=app,capture_output=True,text=True,timeout=60)
    if cli.returncode or 'L-1' not in cli.stdout or 'L-2' in cli.stdout:raise RuntimeError('Application CLI contract failed')
    print('PASS: curated prebuilt query/export/CLI application and integration tests.')
    project=root/'workflow';project.mkdir()
    install=subprocess.run([sys.executable,str(SOURCE/'bin/tequio'),'install',str(project)],capture_output=True,text=True,timeout=60)
    if install.returncode:raise RuntimeError(install.stderr)
    (project/'brief.md').write_text('Demonstrate independent query and CSV export implementations with real scoped lifecycle checks and honest review-pending state.\n')
    shutil.copy2(app/'contract.md',project/'contract.md')
    (project/'siteledger').mkdir();(project/'siteledger/__init__.py').write_text('')
    (project/'tests').mkdir();(project/'docs').mkdir()
    run(project,'workspace','--brief',str(project/'brief.md'))
    w=project/'.tequio/workspaces/demo'
    (w/'analysis/requirements.md').write_text('Independent modules read immutable contract.md, validate errors and preserve input. Script copies curated solutions; this replay is not model or independent-review evidence.\n')
    (w/'specs/behavior.md').write_text((project/'contract.md').read_text())
    run(project,'record','analysis')
    (w/'plans/delivery.md').write_text('Claim two disjoint components concurrently; verify/document A, introduce independent B, retain A evidence. Checkpoint and inspect with new CLI process. Genuine review required before closure; do not fabricate.\n')
    run(project,'record','plan')
    sources=['briefs/brief.md','analysis/requirements.md','specs/behavior.md','plans/delivery.md']
    def task(tid,module):
        return dict(id=tid,title='Replay '+module,outcome='Run actual '+module+' behavior checks',scope='Curated code copy and lifecycle demonstration',exclusions='No model generation or fictional independent review',sources=sources,writes=['siteledger/'+module+'.py','tests/test_'+module+'.py','docs/'+module+'.md'],reads=['contract.md','siteledger/__init__.py'],depends_on=[],specialists=[],risk='security' if module=='export' else 'normal',security_assessment={'surfaces':['data-export'] if module=='export' else [],'reason':'The export component emits sample evidence as CSV; review its output boundary and spreadsheet consumption limits even though the replay contains only synthetic local data.' if module=='export' else 'This query component reads trusted local synthetic fixture data and changes no authentication, deployment or external data boundary.'},stage='ready',freshness={'mode':'scoped-v1','independent':True,'shared_contracts':['contract.md'],'config':[],'mandatory_context':[]},documentation={'mode':'update','paths':['docs/'+module+'.md'],'reason':'Curated component usage documentation is copied alongside its actual application implementation.'},acceptance=['Actual component tests pass and missing independent review blocks closure'],checks=[[sys.executable,'-m','unittest','discover','-s','tests','-p','test_'+module+'.py','-v']],handoff='Real independent review still needed; no fictitious reviewer')
    tasks=[task('A','query'),task('B','export')]
    file=w/'tasks/replay.json';file.write_text(json.dumps(tasks));prepare_demo_reviews(project,w,file,run);run(project,'import-tasks',str(file))
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims=list(pool.map(lambda tid:run(project,'claim','--owner','replay-'+tid.lower(),'--task',tid),['A','B']))
    for index,(tid,module) in enumerate([('A','query'),('B','export')]):
        for relative in ('siteledger/'+module+'.py','tests/test_'+module+'.py','docs/'+module+'.md'):
            shutil.copy2(app/relative,project/relative)
        claim=claims[index];result=run(project,'verify',tid,'--token',claim['token'])
        if not result['passed']:raise RuntimeError('Actual checks failed')
        reconciliation={'summary':'Mapped every declared source to the copied curated implementation, its actual passing component tests and maintained usage documentation. This is a mechanical replay and does not claim model generation or genuine independent review.','deviations':[],'reconciliation':[{'source':s,'actual':['siteledger/'+module+'.py','tests/test_'+module+'.py'],'docs':['docs/'+module+'.md'],'disposition':'implemented','notes':'The prebuilt source matches the declared immutable API contract and current executable tests. Independent semantic review remains absent in this replay.'} for s in sources]}
        report='reviews/'+tid+'-docs.json';(w/report).write_text(json.dumps(reconciliation))
        run(project,'record-docs',tid,'--token',claim['token'],'--report',report)
    proof=run(project,'proof','A')['tasks'][0]
    if proof['checks']['state']!='current' or proof['documentation']['state']!='current':raise RuntimeError('Independent B invalidated A')
    refused=run(project,'complete','A','--token',claims[0]['token'],'--summary','Must refuse absent genuine independent review',expected=2)
    if 'review' not in refused['error'].lower():raise RuntimeError('Wrong refusal')
    run(project,'checkpoint','--summary','Two real checks/docs receipts remain current; actual independent review is still absent','--next','Obtain genuine independent review before closure; preserve active ownership')
    resumed=run(project,'resume')
    if not resumed['checkpoint'] or len(resumed['current']['tasks'])!=2:raise RuntimeError('Checkpoint continuity failed')
    print('PASS: independent concurrent claims, scoped evidence through B writes, fresh-process checkpoint/resume.')
    (w/'analysis/requirements.md').write_text('Changed referenced requirement: reconcile the actual task before further verification.\n')
    stale=run(project,'verify','A','--token',claims[0]['token'],expected=2)
    if 'stale' not in stale['error'].lower():raise RuntimeError('Changed requirement did not invalidate work')
    print('PASS: closure refused without actual independent review; referenced requirement change blocks verification.')
    print('State: review-pending with changed inputs requiring reconciliation/replan.')
    print('Replay uses prebuilt code, not live agents, authenticated review, crash recovery or a productivity benchmark.')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    if args.output:
        if args.output.exists():parser.error('--output must not already exist')
        demonstrate(args.output.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix='tequio-integrated-') as folder:demonstrate(Path(folder)/'replay')
if __name__=='__main__':main()
