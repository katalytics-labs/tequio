"""Bounded private qualification-evidence integrity check, not an observation engine.

Manifest v1: artifacts [{path,sha256}], areas mapping each required id to
{status: pass|pending|fail, observations:[{evidence,action,result}], gaps:[str]}.
Paths are relative regular files below the manifest's directory. A pass requires
an actual referenced report/event file; the helper cannot authenticate its truth.
"""
import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from pathlib import Path
import sys

AREAS = (
    'topic-selection', 'project-status', 'offline-model-controls',
    'desktop-mobile-keyboard-motion-static-print', 'injection-network',
    'temp-first-no-destination', 'authorized-destination',
    'collision-failed-transfer-copy-cleanup', 'vault-package', 'environment-limits',
    'independent-teaching-inspection',
)
MAX_BYTES = 8 * 1024 * 1024

def inspect_html_assets(path, base, known):
    """Inspect bounded asset locations/markup, not arbitrary JavaScript behavior."""
    known_paths={p.resolve() for p in known.values()}
    def reference(value, image=False, anchor=False, source=None):
        if not isinstance(value,str) or not value.strip(): raise ValueError('Empty asset reference')
        value=value.strip()
        parsed=urlsplit(value)
        if anchor and parsed.scheme in ('http','https') and parsed.netloc: return
        if value.startswith('#'): return
        if image and re.match(r'^data:image/(?:png|jpeg|gif|webp);base64,[A-Za-z0-9+/=\s]+$',value): return
        if parsed.scheme or parsed.netloc or value.startswith('//'): raise ValueError('External or unsafe asset reference')
        decoded=unquote(parsed.path)
        if not decoded or '\\' in decoded or Path(decoded).is_absolute() or '..' in Path(decoded).parts: raise ValueError('Unsafe local asset path')
        target=(source or path).parent/decoded
        for ancestor in (target,*target.parents):
            if ancestor==base.parent: break
            if ancestor.is_symlink(): raise ValueError('Symlink asset refused')
        if not target.resolve().is_relative_to(base) or not target.is_file(): raise ValueError('Missing or out-of-bound local asset')
        if target.resolve() not in known_paths: raise ValueError('Local asset is not hashed in manifest')
    def css(text, source=None):
        if re.search(r'@import\b',text,re.I): raise ValueError('CSS imports refused')
        for match in re.finditer(r'url\(\s*([\'"]?)(.*?)\1\s*\)',text,re.I|re.S): reference(match[2],image=True,source=source)
    class Assets(HTMLParser):
        def __init__(self):super().__init__(convert_charrefs=True);self.in_style=False
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if any(k.lower().startswith('on') for k in attrs):raise ValueError('Event-handler attribute refused')
            if tag in ('iframe','frame','object','embed','base'):raise ValueError('Embedded document/base refused')
            if tag=='meta' and attrs.get('http-equiv','').lower()=='refresh':raise ValueError('Automatic navigation refused')
            if 'srcdoc' in attrs or 'action' in attrs or 'formaction' in attrs:raise ValueError('Active embedded/form destination refused')
            if 'srcset' in attrs:raise ValueError('Asset srcset requires explicit inspected alternative')
            if 'style' in attrs:css(attrs['style'])
            for key in ('src','href','xlink:href','poster','data'):
                if key in attrs:reference(attrs[key],image=tag in ('img','image'),anchor=tag=='a' and key=='href')
            if tag=='style':self.in_style=True
        def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
        def handle_endtag(self,tag):
            if tag=='style':self.in_style=False
        def handle_data(self,data):
            if self.in_style:css(data)
    parser=Assets();parser.feed(path.read_text(encoding='utf-8'));parser.close()
    for asset in known.values():
        if asset.suffix.lower()=='.css':css(asset.read_text(encoding='utf-8'),source=asset)

def inspect(manifest):
    manifest=Path(manifest)
    if manifest.is_symlink() or not manifest.is_file(): raise ValueError('Manifest must be a regular file')
    if manifest.stat().st_size > 1024*1024: raise ValueError('Manifest exceeds limit')
    base=manifest.parent.resolve(); data=json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('version')!=1: raise ValueError('Unsupported manifest version')
    artifacts=data.get('artifacts')
    if not isinstance(artifacts,list) or not 1<=len(artifacts)<=100: raise ValueError('Bounded artifact list required')
    known={}; total=0
    for artifact in artifacts:
        if not isinstance(artifact,dict): raise ValueError('Artifact must be an object')
        rel=artifact.get('path'); digest=artifact.get('sha256')
        if not isinstance(rel,str) or not rel or Path(rel).is_absolute() or '..' in Path(rel).parts: raise ValueError('Unsafe evidence path')
        path=base/rel
        for ancestor in (path,*path.parents):
            if ancestor==base.parent: break
            if ancestor.is_symlink(): raise ValueError('Symlink evidence refused')
        if not path.resolve().is_relative_to(base) or not path.is_file(): raise ValueError('Missing or out-of-bound evidence')
        size=path.stat().st_size; total+=size
        if size>MAX_BYTES or total>32*MAX_BYTES: raise ValueError('Evidence exceeds bounds')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest: raise ValueError('Evidence hash mismatch')
        if rel in known: raise ValueError('Duplicate evidence path')
        known[rel]=path
    if not any(path.suffix.lower()=='.html' for path in known.values()): raise ValueError('Actual generated HTML required')
    for path in known.values():
        if path.suffix.lower()=='.html':inspect_html_assets(path,base,known)
    areas=data.get('areas',{}); pending=[]
    if not isinstance(areas,dict): raise ValueError('Areas must be an object')
    for name in AREAS:
        area=areas.get(name)
        if not isinstance(area,dict) or area.get('status') not in ('pass','pending','fail'): raise ValueError('Missing or invalid area: '+name)
        observations=area.get('observations'); gaps=area.get('gaps')
        if not isinstance(observations,list) or not isinstance(gaps,list) or any(not isinstance(g,str) or not g.strip() for g in gaps): raise ValueError('Explicit observations/gaps required: '+name)
        for observation in observations:
            if not isinstance(observation,dict) or not isinstance(observation.get('evidence'),str) or observation.get('evidence') not in known: raise ValueError('Observation must reference hashed evidence: '+name)
            if any(not isinstance(observation.get(k),str) or len(observation[k].strip())<12 for k in ('action','result')): raise ValueError('Specific action/result required: '+name)
            path=known[observation['evidence']]
            if path.suffix.lower() not in ('.md','.txt','.json','.jsonl','.log'): raise ValueError('Observation report/event required: '+name)
        if area['status']=='pass' and (not observations or gaps): raise ValueError('Pass needs observations and no unresolved gaps: '+name)
        if area['status']!='pass':
            if not gaps: raise ValueError('Unresolved area needs explicit gaps: '+name)
            pending.append(name)
    return {'integrity':'valid','pending_areas':pending,'areas':len(AREAS),'artifacts':len(known),'observation_truth':'requires actual independent inspection'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',required=True);args=parser.parse_args()
    try:
        result=inspect(args.manifest)
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print(json.dumps({'integrity':'invalid','error':str(exc)}));return 1
    print(json.dumps(result,indent=2));return 0 if not result['pending_areas'] else 2

if __name__=='__main__':sys.exit(main())
