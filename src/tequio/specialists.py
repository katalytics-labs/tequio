"""Project-owned specialist packages, provenance and evidence-backed readiness.

No model or network calls: the tequio-specialists skill performs substantive research
and authoring. This module validates, snapshots and qualifies those artifacts.
"""
import contextlib
from datetime import date
import fcntl
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import subprocess
import time
from urllib.parse import urlsplit
from .core import Error, digest, inside, load, name, require, tree_hash, write

STATES = ('draft', 'format-validated', 'exercise-tested')

def identifier(value):
    require(isinstance(value,str) and re.fullmatch(r'[a-z][a-z0-9-]{0,62}',value), 'Specialist ID must be lowercase letters, digits and hyphens')
    return value

def textlist(value, label):
    require(isinstance(value,list) and value and all(isinstance(x,str) and x.strip() for x in value), 'Missing nonempty string list: '+label)

def package_files(root):
    root=Path(root)
    require(root.is_dir() and not root.is_symlink(), 'Package directory required, no symlinks')
    files={}
    for p in root.rglob('*'):
        require(not p.is_symlink(), 'Package symlinks forbidden')
        require(not any(x in {'.git','.env','__pycache__'} for x in p.relative_to(root).parts), 'Private/generated package path forbidden')
        if p.is_file():
            require(p.stat().st_size<=1024*1024, 'Package file exceeds 1 MiB')
            files[str(p.relative_to(root))]=digest(p.read_bytes())
    require(0<len(files)<=128 and sum((root/p).stat().st_size for p in files)<=5*1024*1024, 'Package exceeds size/file limits')
    require('SKILL.md' in files and 'specialist.json' in files, 'SKILL.md and specialist.json required')
    return files

def validate_package(root):
    root=Path(root); files=package_files(root); spec=load(root/'specialist.json')
    require(isinstance(spec,dict) and spec.get('schema_version')==1, 'Unknown specialist schema')
    sid=identifier(spec.get('id'))
    require(spec.get('mode') in ('research','implementation'), 'Mode must be research or implementation')
    for key in ['capabilities','exclusions','triggers','acceptance','context']:
        textlist(spec.get(key),key)
    require(isinstance(spec.get('technologies'),list) and spec['technologies'], 'Technologies required')
    for tech in spec['technologies']:
        require(isinstance(tech,dict), 'Technology must be an object')
        require(all(isinstance(tech.get(k),str) and tech[k].strip() for k in ['name','version']), 'Technology name and version/range required')
        require(tech.get('selection') in ('selected','candidate'), 'Technology selection must be selected or candidate')
        require(spec['mode']=='research' or tech['selection']=='selected', 'Candidate technology cannot create an implementation specialist')
    skill=(root/'SKILL.md').read_text()
    match=re.match(r'\A---\r?\n(.*?)\r?\n---\r?\n(.*)',skill,re.S)
    require(match is not None, 'Skill frontmatter required')
    # A deliberately small supported frontmatter subset; JSON quoting handles punctuation.
    fields={}
    for line in match[1].splitlines():
        require(':' in line, 'Use simple name/description frontmatter')
        key,value=line.split(':',1);require(key not in fields,'Duplicate frontmatter key')
        value=value.strip(); fields[key]=json.loads(value) if value.startswith('"') else value
    require(set(fields)=={'name','description'} and fields['name']==sid, 'Skill name must match ID; supported frontmatter is name/description')
    require(isinstance(fields['description'],str) and fields['description'].strip() and len(match[2].strip())>=120, 'Substantive skill and description required')
    for raw in re.findall(r'\[[^\]]*\]\(([^)]+)\)',match[2]):
        if urlsplit(raw).scheme:
            require(urlsplit(raw).scheme=='https','Skill external links must use HTTPS');continue
        require(inside(root,raw.split('#')[0]).is_file(),'Missing package reference: '+raw)
    sources=spec.get('sources');require(isinstance(sources,list) and sources,'Primary sources required')
    for source in sources:
        require(isinstance(source,dict),'Source must be an object')
        u=urlsplit(source.get('url',''));require(u.scheme=='https' and u.hostname and not u.username and not u.password,'Source must be an HTTPS URL without credentials')
        require(source.get('kind')=='primary','Source must be labelled primary; author/reviewer verifies authority')
        accessed=date.fromisoformat(source.get('accessed',''));require(accessed<=date.today(),'Future source access date')
        require(isinstance(source.get('locator'),str) and source['locator'].strip(),'Source section locator required')
        p=inside(root,source.get('artifact'));require(p.is_file() and len(p.read_text().strip())>=80,'Substantive source notes required')
    require(isinstance(spec.get('project_context',[]),list) and all(isinstance(p,str) and p.strip() for p in spec.get('project_context',[])), 'project_context must be a list of project-relative file paths')
    checks=spec.get('checks');require(isinstance(checks,list) and checks,'Exercise checks required')
    for argv in checks:
        require(isinstance(argv,list) and argv and all(isinstance(x,str) and x for x in argv),'Checks must be nonempty argument arrays')
    return spec,files

class Factory:
    def __init__(self,workspace):
        self.w=workspace
        self.root=inside(workspace.project,'.tequio/project-specialists')
        self.index=self.root/'registry.json'

    @contextlib.contextmanager
    def locked(self, readonly=False):
        if readonly:
            require(self.index.is_file(),'No project specialist registry')
            data=load(self.index)
            require(data.get('version')==1 and isinstance(data.get('specialists'),dict),'Invalid specialist registry')
            yield data
            return
        self.root.mkdir(parents=True,exist_ok=True)
        lock=inside(self.root,'registry.lock')
        with lock.open('a+') as f:
            fcntl.flock(f,fcntl.LOCK_EX)
            try:
                data=load(self.index) if self.index.exists() else {'version':1,'specialists':{}}
                require(data.get('version')==1 and isinstance(data.get('specialists'),dict),'Invalid specialist registry')
                yield data
            finally:fcntl.flock(f,fcntl.LOCK_UN)

    def context(self,spec):
        result={rel:digest(inside(self.w.path,rel.split('#')[0]).read_bytes()) for rel in spec['context']}
        result.update({'project:'+rel:digest(inside(self.w.project,rel).read_bytes()) for rel in spec.get('project_context',[])})
        return result

    def entry(self,data,sid):
        identifier(sid)
        require(sid in data['specialists'],'Unknown specialist: '+sid)
        return data['specialists'][sid]

    def package(self,entry):
        return inside(self.root,entry['package'])

    def fresh(self,entry):
        require(entry['workspace']==str(self.w.path),'Specialist belongs to another workspace; explicitly generate/requalify for this context')
        spec,files=validate_package(self.package(entry))
        require(files==entry['files'],'Specialist package changed; register a new revision')
        require(self.context(spec)==entry['context'],'Specialist context changed; register and requalify')
        return spec

    def register(self,source,author,replace=False):
        name(author)
        source=Path(source).resolve()
        spec,files=validate_package(source);sid=spec['id'];context=self.context(spec)
        # Avoid collision with bundled capabilities and workflow entry points.
        require(not (self.w.project/'.tequio/skills'/sid/'SKILL.md').exists(),'Bundled specialist/workflow collision; choose a new ID')
        with self.locked() as data:
            require(replace or sid not in data['specialists'],'Specialist exists; --replace creates a new draft revision')
            prior_publication=data['specialists'].get(sid,{}).get('published')
            revision=secrets.token_hex(10);relative='packages/'+sid+'/'+revision;dest=inside(self.root,relative)
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(source,dest)
            require(package_files(dest)==files,'Source changed during registration')
            entry={'id':sid,'revision':revision,'package':relative,'files':files,'author':author,'workspace':str(self.w.path),'context':context,'status':'draft','mode':spec['mode'],'registered':time.time()}
            if prior_publication:entry['published']=prior_publication
            data['specialists'][sid]=entry;write(self.index,data)
        return {'id':sid,'revision':revision,'status':'draft','note':'Validated structure is not exercised competence. Old revisions retained.'}

    def validate(self,sid):
        with self.locked() as data:
            entry=self.entry(data,sid);self.fresh(entry)
            if entry['status']=='draft':entry['status']='format-validated'
            write(self.index,data)
            return {'id':sid,'status':entry['status'],'note':'Format/source declarations checked; factual accuracy requires actual source review'}

    def inspect(self,sid=None):
        if not self.index.exists():return {'specialists':[]}
        data=load(self.index);result=[]
        for entry in data['specialists'].values():
            if sid and entry['id']!=sid:continue
            try:
                self.fresh(entry)
                if entry['status']=='exercise-tested':self.resolve(entry['id'],kind='research')
                problem=None
            except (Error,OSError,ValueError,KeyError,TypeError) as e:problem=str(e)
            result.append({'id':entry['id'],'revision':entry['revision'],'mode':entry['mode'],'status':entry['status'],'stale':problem,'package':str(self.package(entry)),'exercise':entry.get('exercise'),'qualification':entry.get('qualification'),'published':entry.get('published')})
        require(not sid or result,'Unknown specialist')
        return {'specialists':result}

    def exercise(self,sid,fixture,timeout=120):
        require(1<=timeout<=600,'Exercise timeout must be 1..600 seconds')
        fixture=Path(fixture).resolve();require(fixture.is_dir(),'Exercise fixture missing')
        require(not fixture.is_relative_to(self.w.project) and not self.w.project.is_relative_to(fixture),'Exercise must use a separate isolated fixture')
        with self.locked() as data:
            entry=self.entry(data,sid);spec=self.fresh(entry)
            require(entry['status'] in ('format-validated','exercise-tested'),'Validate format before exercise')
            revision=entry['revision'];commands=spec['checks']
            # A new attempt must not leave an older green receipt usable after an error.
            entry['status']='format-validated';entry.pop('qualification',None);entry.pop('exercise',None)
            write(self.index,data)
        material=[]
        for p in fixture.rglob('*'):
            require(not p.is_symlink(), 'Exercise material may not contain symlinks')
            if p.is_file():
                require(p.name != '.env', 'Do not put secrets/environment files in exercise fixtures')
                material.append(p)
        require(len(material)<=512 and sum(p.stat().st_size for p in material)<=20*1024*1024, 'Use a bounded fixture: maximum 512 files and 20 MiB including dependencies')
        before=tree_hash(fixture);results=[]
        for argv in commands:
            try:
                process=subprocess.Popen(argv,cwd=fixture,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
                try:
                    out,err=process.communicate(timeout=timeout)
                    results.append({'argv':argv,'exit_code':process.returncode,'stdout':out.decode(errors='replace'),'stderr':err.decode(errors='replace')})
                except subprocess.TimeoutExpired:
                    results.append({'argv':argv,'exit_code':None,'error':'timeout'})
                finally:
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    process.communicate(timeout=2)
            except OSError as e:results.append({'argv':argv,'exit_code':None,'error':str(e)})
        snapshot=tree_hash(fixture)
        # Retain the actual exercised material, including local dependency/runtime files.
        capture='evidence/'+sid+'-'+secrets.token_hex(8)+'/fixture'
        capture_path=inside(self.root,capture)
        capture_path.parent.mkdir(parents=True,exist_ok=True)
        after_files=list(fixture.rglob('*'))
        require(all(not p.is_symlink() for p in after_files), 'Fixture symlink appeared during exercise')
        regular=[p for p in after_files if p.is_file()]
        require(len(regular)<=512 and sum(p.stat().st_size for p in regular)<=20*1024*1024,'Exercise output exceeded material capture limit')
        require(all(p.name!='.env' for p in regular),'Exercise generated a private environment file')
        shutil.copytree(fixture,capture_path)
        require(tree_hash(capture_path)==snapshot,'Fixture changed during evidence capture')
        passed=before==snapshot and all(r['exit_code']==0 for r in results)
        receipt={'id':sid,'revision':revision,'fixture':str(fixture),'snapshot':snapshot,'capture':capture,'results':results,'passed':passed,'at':time.time()}
        rel='evidence/'+sid+'-'+secrets.token_hex(8)+'.json';p=inside(self.root,rel);write(p,receipt)
        with self.locked() as data:
            entry=data['specialists'][sid];require(entry['revision']==revision,'Revision changed during exercise; receipt not adopted');self.fresh(entry)
            entry['status']='format-validated';entry.pop('qualification',None)
            entry['exercise']={'path':rel,'sha256':digest(p.read_bytes())};write(self.index,data)
        return receipt

    def qualify(self,sid,reviewer,report):
        name(reviewer);report=inside(self.w.path,report);review=load(report)
        require(isinstance(review,dict) and review.get('schema_version')==1,'Qualification review must be structured JSON')
        for key in ['coverage','source_checks','limitations']:
            textlist(review.get(key),key)
        require(review.get('findings')==[],'Unresolved qualification findings')
        with self.locked() as data:
            entry=self.entry(data,sid);spec=self.fresh(entry)
            require(reviewer!=entry['author'],'Author cannot attest independent qualification')
            require(review.get('reviewer')==reviewer and review.get('revision')==entry['revision'],'Reviewer/revision mismatch')
            ref=entry.get('exercise');require(ref,'Exercise required')
            p=inside(self.root,ref['path']);require(p.is_file() and digest(p.read_bytes())==ref['sha256'],'Exercise receipt altered')
            receipt=load(p);require(receipt['passed'],'Exercise failed')
            require('capture' in receipt and inside(self.root,receipt['capture']).is_dir() and tree_hash(inside(self.root,receipt['capture']))==receipt['snapshot'],'Captured exercise material changed or missing; rerun')
            require(review.get('exercise_sha256')==ref['sha256'],'Review must bind to actual exercise receipt')
            require(review.get('fixture_snapshot')==receipt['snapshot'],'Review fixture snapshot mismatch')
            entry['status']='exercise-tested';entry['qualification']={'reviewer':reviewer,'report':str(report.relative_to(self.w.path)),'sha256':digest(report.read_bytes()),'at':time.time()};write(self.index,data)
        return {'id':sid,'status':'exercise-tested','mode':spec['mode'],'note':'Bounded exercise qualification, not general expertise certification'}

    def resolve(self,sid,kind='implementation'):
        with self.locked(readonly=True) as data:
            entry=self.entry(data,sid);spec=self.fresh(entry)
            require(entry['status']=='exercise-tested','Generated specialist must be exercise-tested before task execution')
            require(kind=='research' or spec['mode']=='implementation','Research specialist cannot implement a selected stack')
            ref=entry['exercise'];receipt=inside(self.root,ref['path'])
            require(receipt.is_file() and digest(receipt.read_bytes())==ref['sha256'], 'Exercise evidence changed')
            receipt_data=load(receipt)
            captured=inside(self.root,receipt_data['capture'])
            require(captured.is_dir() and tree_hash(captured)==receipt_data['snapshot'], 'Captured exercise material changed')
            q=entry['qualification'];report=inside(self.w.path,q['report'])
            require(report.is_file() and digest(report.read_bytes())==q['sha256'],'Qualification report changed')
            return {'id':sid,'revision':entry['revision'],'mode':entry['mode'],'package':str(self.package(entry)),'files':entry['files'],'qualification':q['sha256']}

    def publish(self,sid):
        # Publishing here means private local skill discovery, never a public upload.
        resolved=self.resolve(sid,kind='research')
        manifest=inside(self.w.project,'.tequio/manifest.json');prefix=load(manifest).get('prefix','') if manifest.exists() else ''
        discovery=inside(self.w.project,'.agents/skills/'+prefix+sid)
        source=Path(resolved['package']);files=package_files(source)
        discovery_bytes={rel:(source/rel).read_bytes() for rel in files}
        discovery_bytes['SKILL.md']=re.sub(r'(?m)^name:.*$', 'name: '+prefix+sid, discovery_bytes['SKILL.md'].decode(), count=1).encode()
        files={rel:digest(content) for rel,content in discovery_bytes.items()}
        with self.locked() as data:
            entry=data['specialists'][sid];require(entry['revision']==resolved['revision'],'Revision changed')
            old=entry.get('published')
            previous=inside(self.w.project,old['directory']) if old else None
            if previous and previous != discovery and previous.exists():
                require(package_files(previous)==old['files'],'Previous discovery copy modified; reconcile before changing prefix')
            if discovery.exists():
                require(old and old['directory']==str(discovery.relative_to(self.w.project)) and package_files(discovery)==old['files'],'Discovery collision or modified generated skill')
            ignore=inside(self.w.project,'.gitignore');text=ignore.read_text() if ignore.exists() else ''
            exclusion='/'+str(discovery.relative_to(self.w.project))+'/'
            if exclusion not in text.splitlines():ignore.write_text(text.rstrip()+'\n'+exclusion+'\n')
            discovery.parent.mkdir(parents=True,exist_ok=True)
            if discovery.exists():shutil.rmtree(discovery)
            shutil.copytree(source,discovery)
            for rel,content in discovery_bytes.items():inside(discovery,rel).write_bytes(content)
            if previous and previous != discovery and previous.exists():shutil.rmtree(previous)
            entry['published']={'directory':str(discovery.relative_to(self.w.project)),'files':files,'revision':entry['revision']};write(self.index,data)
        return {'id':sid,'discovery':str(discovery),'note':'Private project-local skill; fresh host session may be needed. No native agent registered.'}
