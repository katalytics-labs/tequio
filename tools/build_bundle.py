#!/usr/bin/env python3
"""Refresh release payload identity after reviewed source/skill changes."""
import hashlib
import json
from pathlib import Path
r=Path(__file__).resolve().parents[1]
# The reusable distribution contains workflow skills, not project expertise.
import sys
sys.path.insert(0,str(r/'src'))
from tequio.workflow import WORKFLOW_SKILLS
workflow=set(WORKFLOW_SKILLS)
actual={p.name for p in (r/'skills').iterdir() if p.is_dir()}
if actual != workflow:
    raise SystemExit('Distribution boundary: only declared workflow skills may ship; keep project specialists outside this checkout')
if {p.name for p in (r/'profiles').iterdir()} != {'generic.md'}:
    raise SystemExit('Distribution boundary: project profiles must stay outside this checkout')
files=sorted([r/'LICENSE']+[p for p in (r/'src/tequio').glob('*.py')]+[p for folder in ['skills','roles','templates','profiles'] for p in (r/folder).rglob('*') if p.is_file()])
manifest={'version':1,'files':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(r/'bundle.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Bundle manifest:',len(files),'payload files')
