"""Bounded local health with real isolated installations; no real upgrades."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tequio.install import install,desired
from tequio.installation_health import health
from tequio import installation_health as h
ROOT=Path(__file__).resolve().parents[1]


class Health(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'project';self.root.mkdir();install(ROOT,self.root,'team-')
    def tearDown(self):self.temp.cleanup()
    def image(self):return {str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
    def observe(self,source=None):
        before=self.image();r=health(self.root,source);self.assertEqual(before,self.image());return r
    def manifest(self,update):
        p=self.root/'.tequio/manifest.json';m=json.loads(p.read_text());update(m);p.write_text(json.dumps(m))
    def source(self,name="source"):
        p=Path(self.temp.name)/name;shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('.git','.tequio','.agents','__pycache__'));return p
    def rehash(self,source,rel):
        p=source/'bundle.json';b=json.loads(p.read_text());b['files'][rel]=hashlib.sha256((source/rel).read_bytes()).hexdigest();p.write_text(json.dumps(b))
    def test_fresh_prefixed_snapshot_and_no_workspace_cli(self):
        r=self.observe(ROOT);self.assertEqual(r['owned']['state'],'intact');self.assertEqual(r['source_comparison']['state'],'matches')
        p=subprocess.run([sys.executable,str(self.root/'bin/tequio'),'--project',str(self.root),'doctor','--source',str(ROOT)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);r=json.loads(p.stdout);self.assertEqual(r['workflow']['stage'],'intake');self.assertEqual(r['installation_health']['execution']['layout'],'installed-runtime');self.assertFalse((self.root/'.tequio/workspaces').exists())
    def test_modified_missing_modes_and_legacy(self):
        skill=self.root/'.agents/skills/team-tequio-build/SKILL.md';skill.write_bytes(skill.read_bytes()+b' owner edit');skill.chmod(0o600)
        (self.root/'.tequio/LICENSE').unlink();r=self.observe();self.assertEqual(r['owned']['state'],'drifted')
        for code in ['modified','mode-mismatch','missing']:self.assertGreater(r['owned']['issue_counts'][code],0)
        self.manifest(lambda m:m.pop('mode'));self.assertEqual(self.observe()['installation']['mode'],'unknown')
    def test_forged_paths_not_read_or_echoed_even_with_source(self):
        unsafe=['.env-PRIVATE','.tequio/workspaces/PRIVATE/state.sqlite3','.agents/skills/PRIVATE-owner/SKILL.md']
        self.manifest(lambda m:m['files'].update({k:'0'*64 for k in unsafe}))
        original=h.Budget.read;seen=[]
        def read(b,p,*args,**kw):seen.append(str(p));return original(b,p,*args,**kw)
        with patch.object(h.Budget,'read',read):r=self.observe(ROOT)
        self.assertEqual(r['owned']['issue_counts']['unsafe-path'],3);self.assertNotIn('PRIVATE',json.dumps(r));self.assertFalse(any('PRIVATE' in p for p in seen));self.assertEqual(r['source_comparison']['state'],'invalid')
    def test_symlink_and_size_limits(self):
        p=self.root/'.tequio/LICENSE';p.unlink();outside=Path(self.temp.name)/'PRIVATE';outside.write_text('PRIVATE CONTENT');p.symlink_to(outside)
        r=health(self.root);self.assertEqual(r['owned']['issue_counts']['unsafe-path'],1);self.assertNotIn('PRIVATE',json.dumps(r))
        p.unlink();p.write_bytes((ROOT/'LICENSE').read_bytes())
        with patch.object(h,'BYTE_LIMIT',1):self.assertEqual(health(self.root)['owned']['state'],'incomplete')
        with patch.object(h,'MANIFEST_LIMIT',1):self.assertEqual(health(self.root)['owned']['state'],'incomplete')
        with patch.object(h,'PATH_LIMIT',1):self.assertEqual(health(self.root)['owned']['state'],'incomplete')
    def test_same_version_source_difference_and_ast_not_execution(self):
        source=self.source();rel='src/tequio/__init__.py';(source/rel).write_text((source/rel).read_text()+"\nraise RuntimeError('must not execute selected source')\n");self.rehash(source,rel)
        r=self.observe(source);self.assertEqual(r['source_comparison']['source_version'],r['installation']['version']);self.assertEqual(r['source_comparison']['state'],'differs')
    def test_forged_source_workflow_not_read_or_echoed(self):
        for index,rel in enumerate(['skills/PRIVATE-owner/SKILL.md','src/tequio/.PRIVATE.py']):
            with self.subTest(rel=rel):
                source=self.source('source'+str(index));p=source/rel;p.parent.mkdir(exist_ok=True);p.write_text('private source asset');self.rehash(source,rel)
                original=h.Budget.read;seen=[]
                def spy(b,path,*a,**kw):seen.append(str(path));return original(b,path,*a,**kw)
                with patch.object(h.Budget,'read',spy):r=self.observe(source)
                self.assertEqual(r['source_comparison']['state'],'invalid');self.assertNotIn('PRIVATE',json.dumps(r));self.assertFalse(any('PRIVATE' in x for x in seen))

    def test_source_uses_validated_bytes_after_path_replacement(self):
        source=self.source();rel='profiles/generic.md';original=h.Budget.read
        def swap(b,p,*args,**kw):
            result=original(b,p,*args,**kw)
            if p==source/rel:p.write_bytes(b'changed after captured bytes')
            return result
        with patch.object(h.Budget,'read',swap):r=self.observe(source)
        self.assertEqual(r['source_comparison']['state'],'matches')
    def test_missing_malformed_and_large_issue_caps(self):
        p=self.root/'.tequio/manifest.json';p.write_text('null');self.assertEqual(self.observe()['installation']['state'],'invalid');p.unlink();self.assertEqual(self.observe()['installation']['state'],'not-installed')
    def test_nonregular_fifo_assets_and_manifests_do_not_block(self):
        p=self.root/'.tequio/LICENSE';p.unlink();os.mkfifo(p)
        argv=[sys.executable,str(ROOT/'bin/tequio'),'--project',str(self.root),'doctor']
        r=subprocess.run(argv,capture_output=True,text=True,timeout=2);self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['installation_health']['owned']['issue_counts']['unsafe-path'],1)
        p=self.root/'.tequio/manifest.json';p.unlink();os.mkfifo(p)
        r=subprocess.run(argv,capture_output=True,text=True,timeout=2);self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['installation_health']['installation']['state'],'invalid')

    def test_source_and_owned_share_one_byte_budget(self):
        m=json.loads((self.root/'.tequio/manifest.json').read_text());owned=sum((self.root/p).stat().st_size for p in m['files'])
        with patch.object(h,'BYTE_LIMIT',owned+1):
            r=health(self.root,ROOT)
        self.assertEqual(r['owned']['state'],'intact');self.assertEqual(r['source_comparison']['state'],'incomplete')

    def test_partial_limit_preserves_observed_issues(self):
        a='.tequio/runtime/tequio/a.py';b='.tequio/runtime/tequio/b.py'
        (self.root/a).write_bytes(b'bad!');(self.root/b).write_bytes(b'xxxx')
        self.manifest(lambda m:m.update(files={a:hashlib.sha256(b'good').hexdigest(),b:hashlib.sha256(b'xxxx').hexdigest()},modes={}))
        with patch.object(h,'BYTE_LIMIT',4):r=health(self.root)['owned']
        self.assertEqual(r['state'],'incomplete');self.assertEqual(r['checked'],1);self.assertEqual(r['issue_counts']['modified'],1);self.assertEqual(r['issues'],[{'path':a,'code':'modified'}])

    def test_partial_source_comparison_counts_match_difference_projection(self):
        m=json.loads((self.root/'.tequio/manifest.json').read_text());observed={p:(hashlib.sha256((self.root/p).read_bytes()).hexdigest(),(self.root/p).stat().st_mode&0o777) for p in m['files']};first,second=sorted(observed)[:2];observed[first]=('0'*64,0o644);del observed[second]
        result={'state':'unavailable','source_version':None,'counts':dict.fromkeys(['added','removed','changed','mode_changed','unchanged'],0),'differences':[],'omitted_differences':0}
        h.compare_source(self.root,ROOT,m,observed,result,h.Budget())
        self.assertEqual(result['state'],'unavailable');self.assertEqual(result['counts']['changed'],1);self.assertEqual(result['differences'],[{'path':first,'code':'changed'}])

    def test_supported_long_prefix_remains_valid(self):
        other=Path(self.temp.name)/'long';other.mkdir();prefix='a'*90+'-';install(ROOT,other,prefix)
        r=health(other,ROOT);self.assertEqual(r['owned']['state'],'intact');self.assertEqual(r['source_comparison']['state'],'matches')

    def test_issue_cap_reports_omissions(self):
        m=json.loads((self.root/'.tequio/manifest.json').read_text())
        for rel in list(m['files'])[:12]:(self.root/rel).unlink()
        r=health(self.root)['owned'];self.assertEqual(r['issue_counts']['missing'],12);self.assertEqual(len(r['issues']),10);self.assertEqual(r['omitted_issues'],2)

    def test_source_checkout_snapshot_split_and_render_matches(self):
        source=self.source();install(source,source)
        rel='profiles/generic.md';(source/rel).write_text((source/rel).read_text()+'\nNew source, same version\n');self.rehash(source,rel)
        r=health(source,source);self.assertEqual(r['owned']['state'],'intact');self.assertEqual(r['source_comparison']['state'],'differs')
        from tequio.install import render_payload
        b=json.loads((ROOT/'bundle.json').read_text());payload={p:(ROOT/p).read_bytes() for p in b['files']};self.assertEqual(render_payload(payload,'team-'),desired(ROOT,'team-'))

    def focused(self, *extra, project=None):
        import io
        from contextlib import redirect_stdout
        from tequio.cli import main
        out=io.StringIO()
        with patch('tequio.git_isolation.inspect_lanes', side_effect=AssertionError('lane inventory ran')), patch('tequio.core.Workspace.status', side_effect=AssertionError('status ran')), redirect_stdout(out):
            code=main(['--project',str(project or self.root),'doctor','--installation-only',*map(str,extra)])
        self.assertEqual(code,0)
        return json.loads(out.getvalue())

    def test_installation_only_equal_health_no_workspace_or_writes(self):
        for source in (None,ROOT,self.root/'missing-source'):
            args=[] if source is None else ['--source',source]
            before=self.image();result=self.focused(*args)
            self.assertEqual(set(result),{'installation_health'})
            self.assertEqual(result['installation_health'],health(self.root,source))
            self.assertEqual(before,self.image())
        self.assertFalse((self.root/'.tequio/workspaces').exists())

    def test_installation_only_ignores_damaged_workspace(self):
        state=self.root/'.tequio/workspaces/main/state.sqlite3';state.parent.mkdir(parents=True);state.write_bytes(b'not SQLite')
        before=self.image();self.assertEqual(self.focused()['installation_health'],health(self.root));self.assertEqual(before,self.image())

    def test_installation_only_resolves_registered_controller(self):
        lane=Path(self.temp.name)/'lane';(lane/'.tequio').mkdir(parents=True)
        (lane/'.tequio/git-isolation-origin.json').write_text(json.dumps({'controller':str(self.root.resolve())}))
        (self.root/'.tequio/git-isolation.json').write_text(json.dumps({'version':1,'enabled':True,'controller':str(self.root.resolve()),'lanes':[{'lane':'sample','path':str(lane.resolve()),'worktree':str(lane.resolve()),'branch':'lane','base_commit':'0'*40}]}))
        self.assertEqual(self.focused(project=lane)['installation_health'],health(self.root))
        (self.root/'.tequio/git-isolation.json').unlink()
        from tequio.cli import main
        import io
        from contextlib import redirect_stderr
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--project',str(lane),'doctor','--installation-only']),2)

    def test_installation_only_preserves_unsafe_observations(self):
        self.manifest(lambda m:m['files'].update({'.env-PRIVATE':'0'*64}))
        result=self.focused('--source',ROOT)['installation_health']
        self.assertEqual(result,health(self.root,ROOT));self.assertEqual(result['owned']['issue_counts']['unsafe-path'],1)
        self.assertNotIn('PRIVATE',json.dumps(result))

    def test_installation_only_avoids_history_delivery(self):
        import io
        from contextlib import redirect_stdout
        from tequio.cli import main
        from tequio.core import Workspace
        brief=Path(self.temp.name)/'brief.md';brief.write_text('A bounded synthetic installation diagnostic example with no product execution.')
        Workspace.create(self.root,'main',brief)
        history={'tasks':[{'id':str(n),'reason':'synthetic history '*30} for n in range(300)]}
        out=io.StringIO()
        with patch('tequio.core.Workspace.status',return_value=history), redirect_stdout(out):
            self.assertEqual(main(['--project',str(self.root),'doctor']),0)
        full=json.loads(out.getvalue());focused=self.focused()
        self.assertEqual(full['installation_health'],focused['installation_health'])
        self.assertLess(len(json.dumps(focused)),len(json.dumps(full))//10)

if __name__=='__main__':unittest.main()
