"""Disposable real-Git interruption and lifecycle ordering exercises."""
import concurrent.futures
import contextlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tequio.core import Error
from task_review_fixtures import reviewed_import
from tequio.integration import Journal
from tequio.git_isolation import configure, create_lane
from test_lifecycle import Lifecycle


class Integration(Lifecycle):
    # Reuse fixture helpers, not the unrelated inherited tests.
    def setUp(self):
        super().setUp()
        self.run_git(self.root,'init','-b','main')
        self.run_git(self.root,'config','user.name','Synthetic Fixture')
        self.run_git(self.root,'config','user.email','fixture@example.invalid')
        (self.root/'.gitignore').write_text('.tequio/\n')
        (self.root/'a.txt').write_text('initial\n')
        self.run_git(self.root,'add','.gitignore','a.txt','brief.md')
        self.run_git(self.root,'commit','-m','Synthetic fixture baseline')
        configure(self.root,True)
        self.lane = create_lane(self.root,'worker')
        self.lane_path = Path(self.lane['path'])
        (self.lane_path/'a.txt').write_text('integrated output\n')
        self.run_git(self.lane_path,'add','a.txt')
        self.run_git(self.lane_path,'commit','-m','Synthetic worker output')
        self.sha = self.run_git(self.lane_path,'rev-parse','HEAD')
        self.add(self.task())
        self.c = self.w.claim('synthetic-writer','A')
        self.j = Journal(self.w)

    def tearDown(self):
        # Worktrees live next to the controller temp directory.
        import shutil
        if hasattr(self,'lane_path'):
            shutil.rmtree(self.lane_path,ignore_errors=True)
        super().tearDown()

    def run_git(self,path,*args):
        return subprocess.run(['git','-C',str(path),*args],capture_output=True,text=True,check=True).stdout.strip()

    def plan(self,token=None,commit=None):
        return self.j.plan('A',token or self.c['token'],'worker',commit or self.sha,'main')

    def merge(self):
        self.run_git(self.root,'merge','--no-edit',self.sha)

    def state(self):
        return self.j.status('A')['tasks'][0]['state']

    def count(self):
        with self.j.read() as con:
            return con.execute('SELECT COUNT(*) FROM integration_events').fetchone()[0]

    def test_interrupt_boundaries_and_actual_acceptance(self):
        self.plan()
        self.assertEqual(self.state(),'pending-integration')
        with self.assertRaises(Error): self.w.verify('A',self.c['token'])
        self.merge()
        self.assertEqual(self.state(),'integrated-unrecorded')
        with self.assertRaises(Error): self.w.verify('A',self.c['token'])
        self.j.reconcile('A')
        self.assertEqual(self.state(),'needs-checks')
        self.assertTrue(self.w.verify('A',self.c['token'])['passed'])
        self.assertEqual(self.state(),'needs-docs')
        self.docs(self.c)
        self.assertEqual(self.state(),'needs-review')
        self.w.review('A',self.c['token'],'synthetic-reviewer','correctness',self.report(),[])
        self.assertEqual(self.state(),'ready-for-closure')
        self.w.complete('A',self.c['token'],'Synthetic fixture accepted with fresh evidence')
        self.assertEqual(self.state(),'accepted')
        (self.root/'a.txt').write_text('dirty after acceptance')
        self.assertEqual(self.state(),'blocked')

    def test_legacy_security_contract_blocks_integration_readiness(self):
        self.plan();self.merge();self.j.reconcile('A')
        self.w.verify('A',self.c['token']);self.docs(self.c)
        self.w.review('A',self.c['token'],'synthetic-reviewer','correctness',self.report(),[])
        self.assertEqual(self.state(),'ready-for-closure')
        # Emulate a genuine pre-contract body and its corresponding immutable intent.
        with self.w.transaction() as con:
            body=json.loads(con.execute("SELECT body FROM tasks WHERE id='A'").fetchone()[0]);body.pop('security_assessment')
            intent=self.j.intent(con,'A');intent['binding']=self.j.binding(body)
            con.execute("UPDATE tasks SET body=? WHERE id='A'",(json.dumps(body),))
            con.execute("UPDATE integration_intents SET intent=? WHERE task='A'",(json.dumps(intent),))
        self.assertEqual(self.state(),'blocked')
        self.assertIn('security-contract-migration-required',self.j.status('A')['tasks'][0]['blockers'])
        with self.assertRaises(Error):self.w.complete('A',self.c['token'],'Legacy contract denied')

    def test_no_journal_status_is_read_only(self):
        db=self.w.path/'state.sqlite3';before=db.read_bytes()
        self.assertEqual(self.j.status(),{'tasks':[]})
        self.w.status()
        self.assertEqual(before,db.read_bytes())
        with self.j.read() as con:
            self.assertFalse(self.j.tables(con))

    def test_bad_token_scope_and_full_sha_preserve_database(self):
        db=self.w.path/'state.sqlite3';before=db.read_bytes()
        for token,sha in [('bad',self.sha),(self.c['token'],'HEAD'),(self.c['token'],self.sha[:10])]:
            with self.assertRaises(Error):self.plan(token,sha)
        self.assertEqual(before,db.read_bytes())
        (self.lane_path/'private.txt').write_text('out of scope')
        self.run_git(self.lane_path,'add','private.txt');self.run_git(self.lane_path,'commit','-m','outside scope')
        with self.assertRaises(Error):self.plan(commit=self.run_git(self.lane_path,'rev-parse','HEAD'))
        self.assertEqual(before,db.read_bytes())

    def test_idempotent_concurrent_plan_and_observe(self):
        def attempt(fn):
            try:return fn()
            except Error as exc:
                self.assertIn('Verification operation active',str(exc))
                return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            results=list(ex.map(lambda _:attempt(self.plan),range(4)))
        succeeded=[x for x in results if x is not None]
        self.assertTrue(succeeded)
        self.assertTrue(all(x==succeeded[0] for x in succeeded))
        self.assertEqual(self.plan(),succeeded[0])
        self.assertEqual(self.count(),1)
        self.merge()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(lambda _:attempt(lambda:self.j.reconcile('A')),range(4)))
        # One integrated boundary and one needs-checks observation.
        count=self.count();self.j.reconcile('A');self.assertEqual(self.count(),count)
        with self.j.read() as con:
            self.assertEqual(sum('baseline' in x for x in self.j.events(con,'A')),1)

    def test_moving_source_tip_does_not_select_new_sha(self):
        self.plan()
        (self.lane_path/'a.txt').write_text('newer unselected output\n')
        self.run_git(self.lane_path,'add','a.txt');self.run_git(self.lane_path,'commit','-m','new tip')
        with self.assertRaises(Error):self.plan(commit=self.run_git(self.lane_path,'rev-parse','HEAD'))
        self.merge()
        self.assertEqual((self.root/'a.txt').read_text(),'integrated output\n')
        self.assertEqual(self.j.status()['tasks'][0]['commit'],self.sha)
        self.j.reconcile('A');self.assertEqual(self.state(),'needs-checks')

    def test_fault_rolls_back_lazy_schema_and_intent(self):
        original=self.w.transaction
        from contextlib import contextmanager
        @contextmanager
        def fail():
            with original() as con:
                yield con
                raise RuntimeError('Synthetic interruption before commit')
        with patch.object(self.w,'transaction',fail):
            with self.assertRaises(RuntimeError):self.plan()
        with self.j.read() as con:self.assertFalse(self.j.tables(con))
        self.plan();self.merge()
        before=self.count()
        with patch.object(self.w,'transaction',fail):
            with self.assertRaises(RuntimeError):self.j.reconcile('A')
        self.assertEqual(self.count(),before)
        self.assertEqual(self.state(),'integrated-unrecorded')

    def test_detached_target_preserves_exact_integration_fact(self):
        self.plan();self.merge()
        self.run_git(self.root,'checkout','--detach','HEAD')
        current=self.j.status()['tasks'][0]
        self.assertTrue(current['integrated'])
        self.assertIn('target-identity-mismatch',current['blockers'])
        self.j.reconcile('A')
        with self.j.read() as con:self.assertFalse(any('baseline' in e for e in self.j.events(con,'A')))
        with self.assertRaises(Error):self.plan()
        with self.assertRaises(Error):self.w.verify('A',self.c['token'])
        self.run_git(self.root,'checkout','main')
        self.assertEqual(self.state(),'integrated-unrecorded')

    def test_dirty_or_wrong_branch_merge_does_not_establish_baseline(self):
        self.plan();self.merge()
        (self.root/'a.txt').write_text('dirty merged fixture')
        self.j.reconcile('A')
        with self.j.read() as con:self.assertFalse(any('baseline' in e for e in self.j.events(con,'A')))
        self.run_git(self.root,'restore','a.txt')
        self.run_git(self.root,'checkout','-b','wrong-target')
        self.j.reconcile('A')
        with self.j.read() as con:self.assertFalse(any('baseline' in e for e in self.j.events(con,'A')))
        self.run_git(self.root,'checkout','main')
        self.assertEqual(self.state(),'integrated-unrecorded')
        self.j.reconcile('A');self.assertEqual(self.state(),'needs-checks')
        self.w.release('A',self.c['token'],'Fixture owner stopped after observed integration')
        self.assertIn('owner-inactive',self.j.status()['tasks'][0]['blockers'])

    def test_wrong_branch_dirty_and_rewrite_preserved(self):
        self.plan();self.merge();self.j.reconcile('A')
        self.run_git(self.root,'checkout','-b','wrong')
        self.assertEqual(self.state(),'blocked')
        self.run_git(self.root,'checkout','main')
        (self.root/'a.txt').write_text('private dirty bytes')
        self.j.reconcile('A');self.assertEqual((self.root/'a.txt').read_text(),'private dirty bytes')
        with self.assertRaises(Error):self.w.verify('A',self.c['token'])
        self.run_git(self.root,'restore','a.txt')
        self.run_git(self.root,'checkout','--orphan','unrelated')
        self.run_git(self.root,'commit','-m','rewritten synthetic history')
        self.run_git(self.root,'branch','-f','main','HEAD');self.run_git(self.root,'checkout','main')
        self.assertIn('target-rewritten',self.j.status()['tasks'][0]['blockers'])

    def test_old_receipts_and_restored_records_do_not_pass_barrier(self):
        self.assertTrue(self.w.verify('A',self.c['token'])['passed']);self.docs(self.c)
        self.w.review('A',self.c['token'],'synthetic-reviewer','correctness',self.report(),[])
        with self.j.read() as con:old=dict(con.execute('SELECT * FROM tasks WHERE id="A"').fetchone())
        self.plan();self.merge();self.j.reconcile('A')
        self.assertEqual(self.state(),'needs-checks')
        with self.w.transaction() as con:
            con.execute('UPDATE tasks SET body=?,checks=?,reviews=? WHERE id="A"',(old['body'],old['checks'],old['reviews']))
        self.assertEqual(self.state(),'needs-checks')
        with self.assertRaises(Error):self.w.complete('A',self.c['token'],'Cannot reuse old records')

    def test_recovery_requires_same_intent_owner_reconfirmation(self):
        self.plan();self.merge();self.j.reconcile('A')
        self.w.release('A',self.c['token'],'Synthetic worker stopped at a durable boundary')
        self.c=self.w.claim('new-synthetic-owner','A')
        self.assertIn('owner-changed-reconfirm-plan',self.j.status()['tasks'][0]['blockers'])
        self.j.reconcile('A');self.j.reconcile('A')
        self.assertIn('owner-changed-reconfirm-plan',self.j.status()['tasks'][0]['blockers'])
        with self.assertRaises(Error):self.w.verify('A',self.c['token'])
        self.plan();self.assertEqual(self.state(),'needs-checks')

    def test_malformed_event_and_orphan_observation_fail_closed(self):
        self.plan()
        with self.w.transaction() as con:
            con.execute("INSERT INTO integration_events(task,observation) VALUES ('A','[]')")
        self.assertEqual(self.j.status()['state'],'invalid')
        with self.assertRaises(Error):self.w.verify('A',self.c['token'])
        # External corruption can bypass SQLite's foreign-key setting.
        with contextlib.closing(sqlite3.connect(self.w.path/'state.sqlite3')) as con:
            con.execute("DELETE FROM integration_intents WHERE task='A'");con.commit()
        self.assertEqual(self.j.status()['state'],'invalid')
        with self.assertRaises(Error):self.w.verify('A',self.c['token'])

    def test_repeated_transitions_preserved_but_retries_deduplicated(self):
        self.plan();self.merge();self.j.reconcile('A')
        clean=self.count()
        for _ in range(2):
            (self.root/'a.txt').write_text('repeated dirty fixture')
            self.j.reconcile('A');dirty=self.count()
            self.j.reconcile('A');self.assertEqual(self.count(),dirty)
            self.run_git(self.root,'restore','a.txt')
            self.j.reconcile('A');current=self.count()
            self.j.reconcile('A');self.assertEqual(self.count(),current)
        self.assertEqual(self.count(),clean+4)

    def test_partial_journal_schema_fails_closed(self):
        with self.w.transaction() as con:con.execute('CREATE TABLE integration_intents(task TEXT, intent TEXT)')
        self.assertEqual(self.j.status()['state'],'invalid')
        with self.assertRaises(Error):self.w.verify('A',self.c['token'])

    def test_git_environment_overrides_and_external_diff_are_ignored(self):
        import os
        marker=self.root/'diff-was-executed'
        self.run_git(self.root,'config','diff.external',str(marker))
        with patch.dict(os.environ,{'GIT_DIR':'/missing/synthetic/gitdir','GIT_WORK_TREE':'/missing/synthetic/worktree','GIT_EXTERNAL_DIFF':str(marker)}):
            self.plan()
            self.assertEqual(self.state(),'pending-integration')
        self.assertFalse(marker.exists())

    def test_rename_checks_both_paths_and_rejects_tag_object(self):
        self.run_git(self.lane_path,'mv','a.txt','outside.txt')
        self.run_git(self.lane_path,'commit','-m','Synthetic rename outside scope')
        with self.assertRaises(Error):self.plan(commit=self.run_git(self.lane_path,'rev-parse','HEAD'))
        self.run_git(self.lane_path,'tag','-a','synthetic-tag','-m','Annotated tag',self.sha)
        tag=self.run_git(self.lane_path,'rev-parse','synthetic-tag')
        with self.assertRaises(Error):self.plan(commit=tag)
        with self.j.read() as con:self.assertFalse(self.j.tables(con))

    def test_conflict_and_missing_source_preserve_native_state(self):
        self.plan()
        (self.root/'a.txt').write_text('conflicting target output\n')
        self.run_git(self.root,'add','a.txt');self.run_git(self.root,'commit','-m','Synthetic conflict target')
        p=subprocess.run(['git','-C',str(self.root),'merge',self.sha],capture_output=True)
        self.assertNotEqual(p.returncode,0)
        before=(self.root/'a.txt').read_bytes()
        self.j.reconcile('A')
        self.assertIn('conflicted',self.j.status()['tasks'][0]['blockers'])
        self.assertEqual((self.root/'a.txt').read_bytes(),before)
        self.assertTrue((self.root/'.git/MERGE_HEAD').exists())
        self.run_git(self.root,'merge','--abort')
        # Missing lane is a blocker until exact selected SHA is integrated.
        import shutil
        shutil.rmtree(self.lane_path)
        self.assertIn('source-unavailable-or-moved',self.j.status()['tasks'][0]['blockers'])

    def test_merged_source_lane_missing_warns_and_missing_object_blocks(self):
        self.plan();self.merge();self.j.reconcile('A')
        import shutil
        shutil.rmtree(self.lane_path)
        self.assertEqual(self.state(),'needs-checks')
        self.assertIn('source-unavailable-or-moved',self.j.status()['tasks'][0]['warnings'])
        self.w.release('A',self.c['token'],'Synthetic stopped owner; source lane intentionally gone')
        self.c=self.w.claim('new-owner-without-lane','A');self.plan()
        self.assertEqual(self.state(),'needs-checks')
        # Corrupt missing object in a disposable fixture, never a real repository.
        obj=self.root/'.git/objects'/self.sha[:2]/self.sha[2:]
        obj.unlink()
        self.assertEqual(self.state(),'blocked')
        self.assertIsNone(self.j.status()['tasks'][0]['integrated'])

    def test_target_head_movement_after_checks_requires_new_receipts(self):
        self.plan();self.merge();self.j.reconcile('A')
        self.w.verify('A',self.c['token']);self.docs(self.c)
        self.w.review('A',self.c['token'],'synthetic-reviewer','correctness',self.report(),[])
        self.assertEqual(self.state(),'ready-for-closure')
        self.run_git(self.root,'commit','--allow-empty','-m','Synthetic target moved after verification')
        self.assertEqual(self.state(),'needs-checks')
        with self.assertRaises(Error):self.w.complete('A',self.c['token'],'Old target checks must not accept new target')
        self.w.verify('A',self.c['token']);self.docs(self.c)
        self.w.review('A',self.c['token'],'synthetic-reviewer','correctness',self.report(),[])
        self.assertEqual(self.state(),'ready-for-closure')

    def test_target_head_movement_during_checks_refuses_publication(self):
        self.plan();self.merge();self.j.reconcile('A')
        original=self.w.task_snapshot;calls=0
        def move(body):
            nonlocal calls
            calls+=1
            if calls==2:
                self.run_git(self.root,'commit','--allow-empty','-m','Concurrent synthetic target movement')
            return original(body)
        with patch.object(self.w,'task_snapshot',move):
            with self.assertRaises(Error):self.w.verify('A',self.c['token'])
        with self.j.read() as con:
            self.assertIsNone(con.execute('SELECT checks FROM tasks WHERE id="A"').fetchone()[0])

    def test_nested_controller_scope_translation(self):
        from tequio.core import Workspace
        nested=self.root/'nested';nested.mkdir();(nested/'brief.md').write_text('Nested project fixture sources and boundaries.\n')
        (nested/'a.txt').write_text('initial nested\n')
        self.run_git(self.root,'add','nested');self.run_git(self.root,'commit','-m','Nested fixture')
        w=Workspace.create(nested,'fixture',nested/'brief.md')
        (w.path/'analysis/requirements.md').write_text('Nested fixture analysis is explicit and substantive.\n');w.record('analysis')
        (w.path/'plans/delivery.md').write_text('Nested fixture plan preserves repository boundaries.\n');w.record('plan')
        outer_config=self.root/'.tequio/git-isolation.json';saved=outer_config.read_bytes();outer_config.unlink()
        try:configure(nested,True)
        finally:outer_config.write_bytes(saved)
        lane=create_lane(nested,'nestedworker');path=Path(lane['path'])
        try:
            (path/'a.txt').write_text('selected nested output\n')
            self.run_git(path,'add','a.txt');self.run_git(path,'commit','-m','Nested selected output')
            sha=self.run_git(path,'rev-parse','HEAD')
            t=self.task();p=w.path/'tasks/import.json';p.write_text(json.dumps([t]));reviewed_import(w,p)
            c=w.claim('synthetic-nested-writer','A');j=Journal(w)
            j.plan('A',c['token'],'nestedworker',sha,'main')
            self.assertEqual(j.status()['tasks'][0]['state'],'pending-integration')
            # New task cannot include a repository-root path outside nested project.
            outside=Path(lane['worktree'])/'outside.txt';outside.write_text('outside nested controller')
            self.run_git(path,'add',str(outside));self.run_git(path,'commit','-m','Outside nested controller')
            t=self.task('B');p.write_text(json.dumps([t]));reviewed_import(w,p);b=w.claim('synthetic-nested-writer','B')
            with self.assertRaises(Error):j.plan('B',b['token'],'nestedworker',self.run_git(path,'rev-parse','HEAD'),'main')
        finally:
            import shutil
            shutil.rmtree(Path(lane['worktree']),ignore_errors=True)

    def test_fresh_cli_observes_without_recording(self):
        self.plan();self.merge();before=self.count()
        p=subprocess.run([sys.executable,'-m','tequio.cli','--project',str(self.root),'--workspace','fixture','integration','status','A'],env={**__import__('os').environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')},capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout)['tasks'][0]['state'],'integrated-unrecorded')
        self.assertEqual(before,self.count())

    def test_readonly_status_exposes_original_intent_identity(self):
        planned=self.plan()
        before=(self.w.path/'state.sqlite3').read_bytes()
        shown=self.j.status('A')['tasks'][0]['intent']
        for key in ('task','controller','workspace','lane','source','commit','target','base'):
            self.assertEqual(shown[key],planned[key])
        self.assertNotIn('binding',shown)
        self.assertNotIn(self.c['token'],json.dumps(shown))
        self.assertEqual(before,(self.w.path/'state.sqlite3').read_bytes())
        # Unknown nested metadata is not part of the operator-facing projection.
        with self.w.transaction() as con:
            intent=self.j.intent(con,'A')
            intent['source']['private_note']='PRIVATE-PROJECTION-CANARY'
            con.execute('UPDATE integration_intents SET intent=? WHERE task=?',(json.dumps(intent),'A'))
        before=(self.w.path/'state.sqlite3').read_bytes()
        self.assertNotIn('PRIVATE-PROJECTION-CANARY',json.dumps(self.j.status('A')))
        self.assertEqual(before,(self.w.path/'state.sqlite3').read_bytes())

# The imported base supplies reusable helpers; run its suite separately.
for _name in list(vars(Lifecycle)):
    if _name.startswith('test_') and _name not in vars(Integration):
        setattr(Integration,_name,None)
del Lifecycle

if __name__=='__main__':unittest.main()
