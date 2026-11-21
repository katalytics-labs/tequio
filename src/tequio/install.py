"""Non-destructive, project-local snapshot installation."""
import json
import re
from pathlib import Path
import shutil
from . import __version__
from .core import Error, digest, inside, load, require, write

MARK_START = '# BEGIN TEQUIO PRIVATE PATHS'
MARK_END = '# END TEQUIO PRIVATE PATHS'

def bundle_root():
    return Path(__file__).resolve().parents[2]

def desired(source, prefix):
    source = Path(source)
    require((source / 'src/tequio/cli.py').is_file() and (source / 'src/tequio/core.py').is_file() and (source / 'src/tequio/install.py').is_file() and (source / 'skills/tequio-build/SKILL.md').is_file() and (source / 'roles/orchestrator.md').is_file() and (source / 'templates/task.json').is_file(), 'Incomplete source checkout; run the checkout installer or pass --source /path/to/tequio. Installed runtime is not an upgrade source.')
    manifest_path = source / 'bundle.json'
    require(manifest_path.is_file(), 'Incomplete source checkout: missing bundle.json; build the source bundle first')
    bundle = load(manifest_path)
    require(bundle.get('version') == 1 and isinstance(bundle.get('files'), dict) and bundle['files'], 'Invalid source bundle manifest')
    require((source/'LICENSE').is_file(), 'Distribution LICENSE is required')
    actual = {'LICENSE'} | {str(p.relative_to(source)) for p in (source / 'src/tequio').glob('*.py')}
    actual.update(str(p.relative_to(source)) for folder in ['skills','roles','templates','profiles'] for p in (source / folder).rglob('*') if p.is_file())
    require(actual == set(bundle['files']), 'Incomplete source bundle: missing or unexpected payload paths')
    for rel, expected in bundle['files'].items():
        p = inside(source, rel)
        require(p.is_file() and digest(p.read_bytes()) == expected, 'Source bundle changed: rebuild reviewed manifest before installation: ' + rel)
    payload = {rel: inside(source, rel).read_bytes() for rel in bundle['files']}
    require(all(digest(data) == bundle['files'][rel] for rel,data in payload.items()), 'Source bundle changed during read')
    return render_payload(payload, prefix)

def render_payload(payload, prefix):
    """Pure projection of the same validated source bytes, also used by doctor."""
    skills = sorted(Path(k).parent.name for k in payload if k.startswith('skills/') and len(Path(k).parts)==3 and k.endswith('/SKILL.md'))
    invocations = re.compile(r'(?<![\w$-])\$(' + '|'.join(re.escape(s) for s in skills) + r')(?![\w-])')

    def render(p):
        data = payload[str(p)]
        if prefix and p.suffix.lower() == '.md':
            return invocations.sub(lambda m: '$' + prefix + m[1], data.decode('utf-8')).encode('utf-8')
        return data

    result = {'.tequio/LICENSE': payload['LICENSE']}
    for rel, data in payload.items():
        p = Path(rel)
        if rel.startswith('src/tequio/'):
            result['.tequio/runtime/tequio/' + p.name] = data
        elif p.parts[0] in ('skills','roles','templates','profiles'):
            result['.tequio/' + rel] = render(p) if p.parts[0] != 'templates' else data
    for skill in skills:
        p = Path('skills') / skill / 'SKILL.md'
        installed = prefix + skill
        text = render(p).decode('utf-8').replace('\r\n', '\n').replace('\r', '\n').replace('name: ' + skill + '\n', 'name: ' + installed + '\n')
        text += '\nInstalled references: read `.tequio/skills/' + skill + '/SKILL.md` for bundled relative references. Runtime: `python3 bin/tequio --help`.\n'
        result['.agents/skills/' + installed + '/SKILL.md'] = text.encode()
        for rel in payload:
            asset = Path(rel)
            if asset != p and asset.is_relative_to(p.parent):
                result['.agents/skills/' + installed + '/' + str(asset.relative_to(p.parent))] = render(asset)
    result['bin/tequio'] = b'#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]/".tequio/runtime"))\nfrom tequio.cli import main\nraise SystemExit(main())\n'
    return result

def install(source, project, prefix=''):
    require(not prefix or (prefix.endswith('-') and prefix.replace('-', '').isalnum()), 'Prefix must be empty or a safe name ending in -')
    root = Path(project).resolve()
    require(root.is_dir(), 'Create the project directory first')
    manifest_path = inside(root, '.tequio/manifest.json')
    old = load(manifest_path) if manifest_path.exists() else {'files': {}}
    require(isinstance(old.get('files'), dict), 'Invalid installation manifest')
    new = desired(source, prefix)
    self_source = Path(source).resolve() == root
    if self_source:
        # Never adopt a source-controlled launcher into installer ownership.
        require('bin/tequio' not in old['files'], 'Existing installation owns the launcher; reconcile before source-checkout installation')
        require(inside(root, 'bin/tequio').is_file(), 'Source-checkout installation requires an existing regular source launcher')
        del new['bin/tequio']
    # Full preflight before touching destination: never clobber owner modifications or unrelated files.
    for rel, expected in old['files'].items():
        p = inside(root, rel)
        require(p.is_file() and digest(p.read_bytes()) == expected and (rel not in old.get('modes', {}) or p.stat().st_mode & 0o777 == old['modes'][rel]), 'Owned file changed/missing; preserve and reconcile before upgrade: ' + rel)
    for rel in new:
        p = inside(root, rel)
        require(not p.exists() or rel in old['files'], 'Installation collision: ' + rel)
        for parent in p.parents:
            if parent == root: break
            require(not parent.exists() or parent.is_dir(), 'Destination parent is not a directory: ' + str(parent))
    ignore = inside(root, '.gitignore')
    ignore_text = ignore.read_text() if ignore.exists() else ''
    require(ignore_text.count(MARK_START) == ignore_text.count(MARK_END) <= 1, 'Malformed Tequio ignore block')
    # Keep old exclusions on upgrades so retained private workspace/skill remnants cannot become public by accident.
    exclusions = ['/.tequio/'] + ['/' + '/'.join(Path(p).parts[:3]) + '/' for p in new if p.startswith('.agents/skills/')] + (['/bin/tequio'] if 'bin/tequio' in new else [])
    old_block = ''
    if MARK_START in ignore_text:
        before, tail = ignore_text.split(MARK_START, 1)
        old_block, after = tail.split(MARK_END, 1)
        ignore_text = before.rstrip() + '\n' + after.lstrip('\n')
    exclusions += [x for x in old_block.splitlines() if x.startswith('/')]
    block = MARK_START + '\n' + '\n'.join(sorted(set(exclusions))) + '\n' + MARK_END + '\n'
    # Copy snapshots; existing unrelated project guidance/config stays untouched.
    for rel, data in new.items():
        p = inside(root, rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        p.chmod(0o755 if rel == 'bin/tequio' else 0o644)
    for rel in set(old['files']) - set(new):
        obsolete=inside(root,rel)
        obsolete.unlink()
        parent=obsolete.parent
        while parent != root:
            try:parent.rmdir()
            except OSError:break
            parent=parent.parent
    if 'bin/tequio' in new:
        (root / 'bin/tequio').chmod(0o755)
    ignore.write_text(ignore_text.rstrip() + '\n\n' + block)
    manifest = {'mode': 'source-checkout' if self_source else 'snapshot', 'version': __version__, 'prefix': prefix, 'files': {k: digest(v) for k, v in new.items()}, 'modes': {k: (0o755 if k == 'bin/tequio' else 0o644) for k in new}, 'private_state': '.tequio/workspaces', 'note': 'Ignore is not removal of tracked files/history. No host hooks or native agents registered.'}
    write(manifest_path, manifest)
    return {'installed': str(root), 'mode': manifest['mode'], 'files': len(new), 'prefix': prefix, 'next': 'Start a fresh agent session in this project to discover project-local skills. No global settings changed.'}

def uninstall(project):
    root = Path(project).resolve()
    manifest_path = inside(root, '.tequio/manifest.json')
    require(manifest_path.is_file(), 'No installation manifest')
    manifest = load(manifest_path)
    for rel, expected in manifest['files'].items():
        p = inside(root, rel)
        require(p.is_file() and digest(p.read_bytes()) == expected and (rel not in manifest.get('modes', {}) or p.stat().st_mode & 0o777 == manifest['modes'][rel]), 'Modified owned file; refusing uninstall: ' + rel)
    for rel in manifest['files']:
        inside(root, rel).unlink()
    manifest_path.unlink()
    # Retain ignore protections and workspace evidence intentionally.
    return {'uninstalled': str(root), 'retained': 'Workspace evidence, unrelated files and private ignore exclusions'}
