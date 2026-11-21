"""Bounded, read-only local provenance. No repair, import, fetch or authority."""
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

from . import __version__
from .core import Error, inside
from .install import render_payload
from .workflow import WORKFLOW_SKILLS

MANIFEST_LIMIT = 4 * 1024 * 1024
PATH_LIMIT = 10000
BYTE_LIMIT = 256 * 1024 * 1024
CODES = ('missing','modified','mode-mismatch','unsafe-path','unreadable')


class Limit(Exception):
    pass


class Budget:
    def __init__(self, limit=None):
        self.left = BYTE_LIMIT if limit is None else limit

    def read(self, path, retain=False):
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
                raise Error('Not a regular asset')
            if os.fstat(f.fileno()).st_size > self.left:
                raise Limit()
            mode = os.fstat(f.fileno()).st_mode & 0o777
            h = hashlib.sha256(); chunks = []
            while True:
                data = f.read(min(65536, self.left + 1))
                if not data: break
                self.left -= len(data)
                if self.left < 0: raise Limit()
                h.update(data)
                if retain: chunks.append(data)
            return (b''.join(chunks) if retain else h.hexdigest()), mode


def manifest(path):
    data, _ = Budget(MANIFEST_LIMIT).read(path, True)
    return json.loads(data)


def safe_parts(rel):
    if (not isinstance(rel,str) or not rel or len(rel)>512 or '\\' in rel
            or not all(c.isprintable() for c in rel)):
        return None
    p=PurePosixPath(rel)
    if p.is_absolute() or str(p)!=rel or '..' in p.parts or any(x in ('__pycache__','.git','.env') for x in p.parts):
        return None
    return p.parts


def owned_path(rel,prefix):
    parts=safe_parts(rel)
    if not parts:return False
    if rel in ('bin/tequio','.tequio/LICENSE'):return True
    if len(parts)>=4 and parts[:2]==('.agents','skills'):
        return parts[2] in {prefix+s for s in WORKFLOW_SKILLS} and all(not x.startswith('.') for x in parts[3:])
    if len(parts)>=4 and parts[:2]==('.tequio','skills'):
        return parts[2] in WORKFLOW_SKILLS and all(not x.startswith('.') for x in parts[3:])
    if len(parts)==4 and parts[:3]==('.tequio','runtime','tequio'):
        return parts[3].endswith('.py') and not parts[3].startswith('.')
    return len(parts)>=3 and parts[0]=='.tequio' and parts[1] in ('roles','templates','profiles') and all(not x.startswith('.') for x in parts[2:])


def source_path(rel):
    parts=safe_parts(rel)
    return bool(parts and (rel=='LICENSE' or
        (len(parts)==3 and parts[:2]==('src','tequio') and parts[-1].endswith('.py') and not parts[-1].startswith('.')) or
        (len(parts)>=3 and parts[0]=='skills' and parts[1] in WORKFLOW_SKILLS and all(not x.startswith('.') for x in parts[2:])) or
        (len(parts)>1 and parts[0] in ('roles','templates','profiles') and all(not x.startswith('.') for x in parts[1:]))))


def version(data):
    tree=ast.parse(data.decode('utf-8'))
    values=[n.value.value for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant)
            and any(isinstance(t,ast.Name) and t.id=='__version__' for t in n.targets)]
    if len(values)!=1 or not valid_version(values[0]):raise Error('Invalid source version')
    return values[0]


def valid_version(value):
    return isinstance(value,str) and len(value)<=80 and re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?',value)


def valid_prefix(value):
    return isinstance(value,str) and len(value.encode('utf-8'))+max(map(len,WORKFLOW_SKILLS))<=255 and (not value or (value.endswith('-') and value.replace('-','').isalnum()))


def health(project,source=None):
    root=Path(project).resolve()
    here=Path(__file__).resolve()
    layout='source-checkout' if here.parent==root/'src/tequio' else 'installed-runtime' if here.parent==root/'.tequio/runtime/tequio' else 'other'
    result={'schema_version':1,'execution':{'version':__version__,'layout':layout},
            'installation':{'state':'not-installed','mode':'unknown','version':None,'prefix':None},
            'owned':{'state':'not-installed','checked':0,'issue_counts':dict.fromkeys(CODES,0),'issues':[],'omitted_issues':0},
            'source_comparison':{'state':'not-requested','source_version':None,'counts':dict.fromkeys(('added','removed','changed','mode_changed','unchanged'),0),'differences':[],'omitted_differences':0}}
    owned=result['owned']; comparison=result['source_comparison'];issues=[]
    if source is not None:comparison['state']='unavailable'
    try:
        m=manifest(inside(root,'.tequio/manifest.json'))
        if (not isinstance(m,dict) or not isinstance(m.get('files'),dict) or not m['files']
                or not valid_version(m.get('version')) or not valid_prefix(m.get('prefix'))
                or m.get('mode','unknown') not in ('unknown','snapshot','source-checkout')
                or not isinstance(m.get('modes',{}),dict)):
            raise Error('Invalid manifest')
        result['installation'].update(state='present',mode=m.get('mode','unknown'),version=m['version'],prefix=m['prefix'])
        if len(m['files'])>PATH_LIMIT:raise Limit()
        budget=Budget();observed={}
        for rel,expected in m['files'].items():
            if not owned_path(rel,m['prefix']):
                issues.append({'path':None,'code':'unsafe-path'});continue
            if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected):raise Error('Invalid digest')
            mode=m.get('modes',{}).get(rel,0o755 if rel=='bin/tequio' else 0o644)
            if type(mode) is not int or mode not in (0o644,0o755):raise Error('Invalid mode')
            try:
                p=inside(root,rel);h,actual_mode=budget.read(p);owned['checked']+=1
                observed[rel]=(h,actual_mode)
                if h!=expected:issues.append({'path':rel,'code':'modified'})
                if actual_mode!=mode:issues.append({'path':rel,'code':'mode-mismatch'})
            except FileNotFoundError:issues.append({'path':rel,'code':'missing'})
            except Error:issues.append({'path':None,'code':'unsafe-path'})
            except OSError:issues.append({'path':rel,'code':'unreadable'})
        for issue in issues:owned['issue_counts'][issue['code']]+=1
        issues.sort(key=lambda x:(x['path'] is None,x['path'] or '',x['code']))
        owned.update(state='drifted' if issues else 'intact',issues=issues[:10],omitted_issues=max(0,len(issues)-10))
        if source is not None:
            compare_source(root,Path(source),m,observed,comparison,budget)
    except FileNotFoundError:
        pass
    except Limit:
        owned['state']='incomplete'
        if source is not None:comparison['state']='incomplete'
    except (Error,ValueError,TypeError,KeyError,UnicodeError):
        result['installation']['state']='invalid';owned['state']='invalid'
    except OSError:
        result['installation']['state']='unavailable';owned['state']='unavailable'
    # Preserve already observed defects even when a later path exhausts a limit.
    owned['issue_counts']=dict.fromkeys(CODES,0)
    for issue in issues:owned['issue_counts'][issue['code']]+=1
    issues.sort(key=lambda x:(x['path'] is None,x['path'] or '',x['code']))
    owned.update(issues=issues[:10],omitted_issues=max(0,len(issues)-10))
    return result


def compare_source(root,source,m,observed,result,budget):
    differences=[]
    try:
        source=source.resolve();b=manifest(inside(source,'bundle.json'))
        if not isinstance(b,dict) or b.get('version')!=1 or not isinstance(b.get('files'),dict) or not b['files']:raise Error('Invalid bundle')
        if len(m['files'])+len(b['files'])>PATH_LIMIT:raise Limit()
        payload={}
        for rel,expected in b['files'].items():
            if not source_path(rel):raise Error('Unsafe source')
            data,_=budget.read(inside(source,rel),True)
            if not isinstance(expected,str) or hashlib.sha256(data).hexdigest()!=expected:raise Error('Source changed')
            payload[rel]=data
        required={'LICENSE','src/tequio/__init__.py','src/tequio/cli.py','src/tequio/core.py','src/tequio/install.py','skills/tequio-build/SKILL.md','roles/orchestrator.md','templates/task.json'}
        if not required<=payload.keys():raise Error('Incomplete source')
        # Inventory is bounded and compared before rendering any captured bytes.
        actual={'LICENSE'};visited=0
        for folder in ['src/tequio','skills','roles','templates','profiles']:
            base=inside(source,folder)
            for p in base.rglob('*'):
                visited+=1
                if visited>PATH_LIMIT:raise Limit()
                rel=str(p.relative_to(source))
                if p.is_symlink():raise Error('Symlink source')
                if p.is_file() and (folder!='src/tequio' or (p.parent==base and p.suffix=='.py')):
                    actual.add(rel)
                    if len(actual)>PATH_LIMIT:raise Limit()
        if actual!=set(payload):raise Error('Incomplete source inventory')
        result['source_version']=version(payload['src/tequio/__init__.py'])
        desired=render_payload(payload,m['prefix'])
        if source==root:desired.pop('bin/tequio',None)
        if any(not owned_path(rel,m['prefix']) for rel in desired):raise Error('Unsafe rendered namespace')
        if any(not owned_path(rel,m['prefix']) for rel in m['files']):raise Error('Unsafe comparison')
        differences=[]
        for rel in sorted(set(m['files'])|set(desired)):
            if rel not in desired:code='removed'
            elif rel not in m['files']:code='added'
            elif not owned_path(rel,m['prefix']):raise Error('Unsafe comparison')
            elif rel not in observed:result['state']='unavailable';return
            elif hashlib.sha256(desired[rel]).hexdigest()!=observed[rel][0]:code='changed'
            elif observed[rel][1]!=(0o755 if rel=='bin/tequio' else 0o644):code='mode-changed'
            else:code=None
            result['counts'][code.replace('-','_') if code else 'unchanged']+=1
            if code:differences.append({'path':rel,'code':code})
        result.update(state='differs' if differences else 'matches',differences=differences[:10],omitted_differences=max(0,len(differences)-10))
    except Limit:result['state']='incomplete'
    except FileNotFoundError:result['state']='unavailable'
    except (Error,ValueError,TypeError,KeyError,UnicodeError,SyntaxError):result['state']='invalid'
    except OSError:result['state']='unavailable'
    finally:
        result.update(differences=differences[:10],omitted_differences=max(0,len(differences)-10))
