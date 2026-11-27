"""Portable Explain distribution and actual shipped finite-model regressions."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from tequio.install import install, uninstall
from tequio.workflow import WORKFLOW_SKILLS

SHELL = ROOT / 'skills/tequio-explain/templates/lesson.html'

class ExplainArtifacts(unittest.TestCase):
    def test_complete_default_and_prefixed_install_preserves_lessons(self):
        self.assertIn('tequio-explain', WORKFLOW_SKILLS)
        for prefix in ('', 'sample-'):
            with self.subTest(prefix=prefix), tempfile.TemporaryDirectory() as folder:
                project = Path(folder)
                lesson = project / 'Learning/owner-lesson.html'
                lesson.parent.mkdir(); lesson.write_text('Owner lesson', encoding='utf-8')
                install(ROOT, project, prefix=prefix)
                base = project / '.agents/skills' / (prefix + 'tequio-explain')
                for rel in ('SKILL.md', 'references/teaching-artifacts.md', 'templates/lesson.html'):
                    self.assertTrue((base / rel).is_file(), rel)
                    self.assertTrue((project / '.tequio/skills/tequio-explain' / rel).is_file())
                self.assertIn('name: ' + prefix + 'tequio-explain', (base / 'SKILL.md').read_text())
                self.assertIn('$' + prefix + 'tequio-learn', (base / 'SKILL.md').read_text())
                self.assertEqual((base / 'templates/lesson.html').read_bytes(), SHELL.read_bytes())
                install(ROOT, project, prefix=prefix)
                uninstall(project)
                self.assertEqual(lesson.read_text(), 'Owner lesson')
                self.assertFalse((base / "SKILL.md").exists())

    def test_actual_shipped_model_boundaries_and_accounting(self):
        runner = shutil.which('node')
        self.assertIsNotNone(runner, 'Required actual JavaScript model runner unavailable; qualification stays pending')
        html = SHELL.read_text(encoding='utf-8')
        script = re.search(r'<script id="routing-model">(.*?)</script>', html, re.S).group(1)
        checks = r'''
const assert=require('node:assert/strict');
const m=createRoutingModel();
const invariant=s=>{assert.equal(s.arrivals,s.completed+s.dropped+s.queues.reduce((a,b)=>a+b,0));s.queues.forEach(q=>assert.ok(q>=0&&q<=8));};
let s=m.step({load:0}).state;assert.equal(s.completed,0);invariant(s);
m.reset();let r=m.step();assert.deepEqual(r.processed,[1,1,1]);assert.equal(r.state.completed,3);invariant(r.state);
m.reset();r=m.step({load:6,capacity:2,enabled:[true,true,false]});assert.deepEqual(r.state.queues,[1,1,0]);assert.equal(r.state.dropped,0);
m.reset();for(let i=0;i<3;i++){r=m.step({load:12,capacity:1});invariant(r.state);}assert.equal(r.state.dropped,6);assert.deepEqual(r.state.queues,[7,7,7]);
r=m.step({load:0,enabled:[false,true,true]});assert.equal(r.disabledDrops,7);assert.equal(r.state.queues[0],0);invariant(r.state);
r=m.step({load:5,enabled:[false,false,false]});assert.equal(r.droppedNow,17);assert.deepEqual(r.state.queues,[0,0,0]);invariant(r.state);
r=m.step({load:3,enabled:[true,true,true]});assert.deepEqual(r.assigned,[1,1,1]);invariant(r.state);
let copy=m.snapshot();copy.queues[0]=999;copy.enabled[0]=false;assert.notEqual(m.snapshot().queues[0],999);assert.equal(m.snapshot().enabled[0],true);
m.reset();r=m.step({load:999,capacity:-2});assert.equal(r.state.load,12);assert.equal(r.state.capacity,1);
r=m.step({load:NaN,capacity:Infinity});assert.equal(r.state.load,3);assert.equal(r.state.capacity,2);
r=m.step({load:2.9,capacity:3.9});assert.equal(r.state.load,2);assert.equal(r.state.capacity,3);
m.reset();for(let i=0;i<125;i++){r=m.step({load:12,capacity:1});invariant(r.state);}assert.equal(r.state.tick,120);assert.equal(r.state.arrivals,1440);assert.equal(r.terminal,true);
let before=m.snapshot();m.step({load:0});assert.deepEqual(m.snapshot(),before);
assert.deepEqual(m.reset(),{enabled:[true,true,true],queues:[0,0,0],pointer:0,arrivals:0,completed:0,dropped:0,tick:0,load:3,capacity:2});
console.log('actual-model: baseline, overload, disable, all-off, reenable, bounds, snapshot, ceiling, reset passed');
'''
        result = subprocess.run([runner, '-e', script + '\n' + checks], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_probe_malformed_types_fail_closed(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('explain_probe',ROOT/'tests/explain_artifact_probe.py')
        probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);manifest=root/'manifest.json'
            for data in ([],None,{'version':1,'artifacts':[False]}, {'version':1,'artifacts':[None]}):
                manifest.write_text(json.dumps(data))
                with self.subTest(data=data), self.assertRaises(ValueError):probe.inspect(manifest)
            artifact=root/'lesson.html';artifact.write_text('<h1>Example</h1>')
            import hashlib
            entry={'path':'lesson.html','sha256':hashlib.sha256(artifact.read_bytes()).hexdigest()}
            for areas in ([],False,{'topic-selection':True}):
                manifest.write_text(json.dumps({'version':1,'artifacts':[entry],'areas':areas}))
                with self.subTest(areas=areas),self.assertRaises(ValueError):probe.inspect(manifest)

    def test_pause_settles_actual_replay_to_committed_queues(self):
        runner=shutil.which('node');self.assertIsNotNone(runner)
        html=SHELL.read_text()
        functions=re.search(r'(function settleReplay\(\).*?)\nfunction render',html,re.S).group(1)
        checks=r"""
const assert=require('node:assert/strict');
const nodes={};let timer=42,frame=7;
const lastResult={state:{tick:3,queues:[7,7,7]}};
const get=id=>nodes[id];
let cleared=false;nodes['moving-requests']={replaceChildren(){cleared=true;}};
for(let i=0;i<3;i++){nodes['queue-'+i]={children:Array.from({length:8},()=>({full:false,classList:{toggle(k,v){this.parent.full=v;}}}))};nodes['queue-'+i].children.forEach(n=>n.classList.parent=n);nodes['queue-label-'+i]={textContent:'6 in replay queue'};}
nodes['phase-caption']={};nodes.play={setAttribute(){},textContent:'Pause play'};
let frozen=false;function freeze(){frozen=true;}function clearInterval(value){assert.equal(value,42);}
stop();assert.equal(timer,null);assert.ok(frozen&&cleared);
for(let i=0;i<3;i++){assert.equal(nodes['queue-label-'+i].textContent,'7 waiting');assert.equal(nodes['queue-'+i].children.filter(n=>n.full).length,7);}
assert.match(nodes['phase-caption'].textContent,/committed state/);
"""
        result=subprocess.run([runner,'-e',functions+'\n'+checks],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_probe_actual_asset_markup_and_references(self):
        import importlib.util,hashlib
        spec=importlib.util.spec_from_file_location('asset_probe',ROOT/'tests/explain_artifact_probe.py')
        probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);html=root/'lesson.html';manifest=root/'manifest.json'
            def run(content,extra=(),areas=None):
                html.write_text(content)
                files=[html,*extra]
                data={'version':1,'artifacts':[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files], 'areas':areas or {key:{'status':'pending','observations':[],'gaps':['Actual host observation pending.']} for key in probe.AREAS}}
                manifest.write_text(json.dumps(data));return probe.inspect(manifest)
            for content in ('<script src="https://bad.invalid/x.js"></script>','<img src="https://bad.invalid/a.png">','<button onclick="alert(1)">bad</button>','<iframe srcdoc="bad"></iframe>','<img src="../secret.png">','<img src="missing.png">','<style>@import "https://bad.invalid/x.css";</style>','<style>p{background:url(https://bad.invalid/x.png)}</style>','<a href="javascript:alert(1)">bad</a>'):
                with self.subTest(content=content),self.assertRaises(ValueError):run(content)
            asset=root/'diagram.png';asset.write_bytes(b'synthetic image bytes')
            with self.assertRaises(ValueError):run('<img src="diagram.png">')
            self.assertEqual(run('<img src="diagram.png"><a href="https://example.org/source">Source</a>',[asset])['integrity'],'valid')
            styles=root/'styles';styles.mkdir()
            css=styles/'style.css';css.write_text('p{background:url(diagram.png)}')
            with self.assertRaises(ValueError):run('<link rel="stylesheet" href="styles/style.css">',[css,asset])
            nested=styles/'diagram.png';nested.write_bytes(b'nested synthetic image')
            self.assertEqual(run('<link rel="stylesheet" href="styles/style.css">',[css,nested])['integrity'],'valid')
            link=root/'linked.png';link.symlink_to(asset)
            with self.assertRaises(ValueError):run('<img src="linked.png">',[asset])
            areas={key:{'status':'pending','observations':[],'gaps':['Actual host observation pending.']} for key in probe.AREAS}
            areas['topic-selection']['observations']=[{'evidence':[], 'action':'Observe a topic selection', 'result':'Actual observed selection'}]
            with self.assertRaises(ValueError):run('<h1>Safe</h1>',areas=areas)

    def test_self_contained_safety_structure(self):
        from html.parser import HTMLParser
        class Assets(HTMLParser):
            def __init__(self): super().__init__(); self.remote=[]; self.csp=None
            def handle_starttag(self, tag, attrs):
                a=dict(attrs)
                if tag=='meta' and a.get('http-equiv')=='Content-Security-Policy':self.csp=a.get('content')
                for key in ('src','srcset'):
                    if key in a and not a[key].startswith('data:'):self.remote.append((tag,key,a[key]))
                if tag=='link':self.remote.append((tag,'href',a.get('href')))
        html=SHELL.read_text(encoding='utf-8'); parser=Assets();parser.feed(html)
        self.assertEqual(parser.remote,[]);self.assertIn("connect-src 'none'",parser.csp)
        scripts='\n'.join(re.findall(r'<script[^>]*>(.*?)</script>',html,re.S))
        self.assertIsNone(re.search(r'\b(?:eval|fetch|WebSocket|XMLHttpRequest|importScripts)\s*\(|\.innerHTML\s*=|\bnew\s+Function\b',scripts))
        self.assertIn('<noscript>',html)

if __name__ == '__main__': unittest.main()
