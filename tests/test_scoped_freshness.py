"""Source-level contract tests; no installer integrity bypass."""
from test_lifecycle import Lifecycle
from tequio.core import Error


class ScopedFreshness(Lifecycle):
    def task(self, *args, **kwargs):
        task = super().task(*args, **kwargs)
        task['freshness'] = {'mode':'scoped-v1', 'independent':True,
                             'shared_contracts':['contract.txt'], 'config':['config.txt'],
                             'mandatory_context':[]}
        return task

    def test_independent_writer_preserves_checks_and_docs(self):
        self.add(self.task('A'), self.task('B'))
        a=self.w.claim('one','A');self.w.claim('two','B')
        self.assertTrue(self.w.verify('A',a['token'])['passed'])
        self.docs(a)
        (self.root/'b.txt').write_text('Independent B implementation')
        self.assertEqual(self.w.status()['tasks'][0]['documentation']['state'],'current')
        self.w.review('A',a['token'],'reviewer','correctness',self.report(),[])
        self.w.complete('A',a['token'],'Actual fixture closure')

    def test_future_plan_does_not_stale_existing_work(self):
        self.add(self.task());a=self.w.claim('one')
        (self.w.path/'plans/future.md').write_text('An unreferenced future task')
        self.assertTrue(self.w.verify('A',a['token'])['passed'])

    def test_relevant_sources_and_mandatory_brief_stale(self):
        for relative in ('plans/delivery.md','briefs/new.md','specs/new.md'):
            with self.subTest(relative=relative):
                task=self.task('N'+str(len(relative)));self.add(task)
                (self.w.path/relative).write_text('Changed mandatory or referenced source')
                with self.assertRaises(Error):self.w.claim('one',task['id'])
                self.w.record('analysis');self.w.record('plan')

    def test_resources_stale_receipts(self):
        self.add(self.task());a=self.w.claim('one')
        for relative in ('contract.txt','config.txt','a.txt'):
            self.assertTrue(self.w.verify('A',a['token'])['passed'])
            self.docs(a)
            (self.root/relative).write_text('Changed relevant resource')
            self.assertEqual(self.w.status()['tasks'][0]['documentation']['state'],'outstanding')

    def test_recursive_dependency_change_stales_ready_child(self):
        self.add(self.task('A'),self.task('B',depends=['A']),self.task('C',depends=['B']))
        self.finish(self.w.claim('one','A'));self.finish(self.w.claim('two','B'))
        (self.root/'a.txt').write_text('Changed transitive dependency')
        with self.assertRaises(Error):self.w.claim('three','C')

    def test_invalid_policy_rejected(self):
        task=self.task();del task['freshness']['config']
        with self.assertRaises(Error):self.add(task)

    def test_legacy_falls_back(self):
        task=self.task();del task['freshness'];self.add(task);a=self.w.claim('one')
        self.assertTrue(self.w.verify('A',a['token'])['passed']);self.docs(a)
        (self.root/'unrelated.txt').write_text('Legacy global snapshot changes')
        self.assertEqual(self.w.status()['tasks'][0]['documentation']['state'],'outstanding')

    def test_changed_dependency_blocks_active_verification(self):
        self.add(self.task('A'), self.task('B',depends=['A']))
        self.finish(self.w.claim('one','A'))
        b=self.w.claim('two','B')
        (self.root/'a.txt').write_text('Changed upstream after claim')
        with self.assertRaises(Error):self.w.verify('B',b['token'])

    def test_shared_contract_lock(self):
        self.add(self.task('A'), self.task('B',writes=['contract.txt']))
        self.w.claim('one','A')
        with self.assertRaises(Error):self.w.claim('two','B')

    def test_explicit_context_read_and_specialist_changes(self):
        task=self.task(reads=['read.txt'])
        task['freshness']['mandatory_context']=['plans/context.md']
        (self.w.path/'plans/context.md').write_text('Required context')
        self.w.record('plan');self.add(task);a=self.w.claim('one')
        self.assertTrue(self.w.verify('A',a['token'])['passed']);self.docs(a)
        (self.root/'read.txt').write_text('Relevant read dependency')
        self.assertEqual(self.w.status()['tasks'][0]['documentation']['state'],'outstanding')
        (self.w.path/'plans/context.md').write_text('Changed explicit context')
        with self.assertRaises(Error):self.w.verify('A',a['token'])

    def test_config_and_specialist_binding_changes_stale_inputs(self):
        self.add(self.task());a=self.w.claim('one')
        original=self.w.specialist_bindings
        self.w.specialist_bindings=lambda task: {'changed':'qualification'}
        with self.assertRaises(Error):self.w.verify('A',a['token'])
        self.w.specialist_bindings=original
        with self.w.transaction() as con:
            con.execute("UPDATE meta SET value=? WHERE key='config'", ('{"max_parallel":2}',))
        with self.assertRaises(Error):self.w.verify('A',a['token'])

    def test_dot_prefixed_reserved_freshness_resources_refused(self):
        for key in ('shared_contracts', 'config'):
            for path in ('./.agents/private', './.git/config', './.tequio/private', '.', './'):
                with self.subTest(key=key, path=path):
                    task=self.task();task['freshness'][key]=[path]
                    with self.assertRaises(Error):self.add(task)

    def test_nested_resource_symlink_refused_before_evidence(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as outside:
            (self.root/'src').mkdir()
            (Path(outside)/'input.txt').write_text('original')
            (self.root/'src/linked').symlink_to(outside, target_is_directory=True)
            self.add(self.task(reads=['src']))
            claim=self.w.claim('writer')
            with self.assertRaisesRegex(Error,'Symlink descendants'):
                self.w.verify('A',claim['token'])

    def test_nested_mandatory_context_symlink_refused(self):
        (self.w.path/'briefs/linked').symlink_to(self.root, target_is_directory=True)
        self.w.record('analysis');self.w.record('plan')
        with self.assertRaisesRegex(Error,'Symlink descendants'):
            self.add(self.task())

    def test_symlink_added_after_review_blocks_closure(self):
        (self.root/'src').mkdir()
        self.add(self.task(reads=['src']));claim=self.w.claim('writer')
        self.assertTrue(self.w.verify('A',claim['token'])['passed']);self.docs(claim)
        self.w.review('A',claim['token'],'reviewer','correctness',self.report(),[])
        (self.root/'src/linked').symlink_to(self.root/'brief.md')
        with self.assertRaisesRegex(Error,'Symlink descendants'):
            self.w.complete('A',claim['token'],'Should not close')

    def test_root_mandatory_context_controlled_refusal(self):
        task=self.task();task['freshness']['mandatory_context']=['.']
        with self.assertRaisesRegex(Error,'concrete freshness paths'):
            self.add(task)
