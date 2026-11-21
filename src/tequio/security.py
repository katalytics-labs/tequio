"""Explicit security classification and release coverage; no safety inference."""
from pathlib import Path

SURFACES = frozenset(('authorization', 'authentication', 'secrets', 'personal-data',
    'data-export', 'untrusted-input', 'code-execution', 'dependencies', 'configuration', 'network', 'storage'))
COVERAGE = ('candidate-inventory', 'dependencies', 'configuration', 'privacy-export')


def validate(workspace, task, execution=False, candidate_presence=False):
    from .core import require, inside
    assessment = task.get('security_assessment')
    required = execution or task.get('stage', 'ready') == 'ready'
    if 'security_assessment' not in task:
        require(not required, 'Security assessment missing; migration-required: replan unfinished task with explicit assessment')
    else:
        require(isinstance(assessment, dict), 'security_assessment must be an object')
        surfaces = assessment.get('surfaces')
        require(isinstance(surfaces, list) and all(isinstance(s, str) and s in SURFACES for s in surfaces)
                and len(surfaces) == len(set(surfaces)), 'Security surfaces must be unique documented categories')
        require(isinstance(assessment.get('reason'), str) and len(assessment['reason'].strip()) >= 30,
                'Security assessment requires a concrete reason of at least 30 characters')
        require(not surfaces or task.get('risk') == 'security', 'Security surfaces require security risk')
    if task.get('kind') == 'release':
        require(task.get('risk') == 'security', 'Release requires security risk')
        candidates = task.get('candidate_paths')
        require(isinstance(candidates, list) and candidates and all(isinstance(p, str) and p for p in candidates),
                'Release requires nonempty candidate_paths')
        for relative in candidates:
            require(not any(c in relative for c in '*?[') and bool(Path(relative).parts), 'Candidate paths must be concrete')
            p = inside(workspace.project, relative)
            require(bool(Path(relative).parts) and not any(part in ('.tequio', '.agents', '.git') for part in Path(relative).parts), 'Reserved candidate path')
            require(any(p.is_relative_to(inside(workspace.project, resource)) for resource in task.get('reads', []) + task.get('writes', [])),
                    'Candidate paths must be covered by read/write ownership')
            if candidate_presence:
                require(p.exists() and (p.is_file() or p.is_dir()), 'Release candidate missing: ' + relative)
                workspace.resource_hash([relative])  # Reject nested symbolic links as well.


def state(workspace, task, historical=False):
    if historical:
        return {'state': 'historical', 'note': 'Historical closure is not qualification under the current security contract'}
    from .core import Error
    try:
        validate(workspace, task, execution=task.get('stage', 'ready') != 'draft')
        return {'state': 'current' if task.get('security_assessment') else 'draft-unassessed'}
    except (Error, ValueError, OSError, KeyError, TypeError) as exc:
        return {'state': 'migration-required', 'reason': str(exc)}


def required_reviews(task):
    return ['correctness'] + (['security'] if task.get('risk') == 'security' else [])


def release_report(workspace, task, path):
    from .core import require, load, inside
    if task.get('kind') != 'release':
        return
    report = load(path)
    require(isinstance(report, dict) and report.get('candidate_paths') == task['candidate_paths'], 'Release report must identify exact candidate_paths')
    coverage = report.get('coverage')
    require(isinstance(coverage, dict) and set(coverage) == set(COVERAGE), 'Release security report requires all coverage areas')
    for area in COVERAGE:
        item = coverage[area]
        require(isinstance(item, dict) and item.get('disposition') in ('reviewed', 'not-applicable'), 'Invalid release coverage disposition')
        require(isinstance(item.get('reason'), str) and len(item['reason'].strip()) >= 30, 'Explain each release coverage area and gaps')
        evidence = item.get('evidence')
        require(isinstance(evidence, list) and all(isinstance(p, str) and p for p in evidence), 'Coverage evidence must be project paths')
        require(item['disposition'] == 'not-applicable' or evidence, 'Reviewed coverage requires evidence')
        require(area != 'candidate-inventory' or item['disposition'] == 'reviewed', 'Candidate inventory cannot be not-applicable')
        for relative in evidence:
            p = inside(workspace.project, relative)
            require(p.exists() and any(p.is_relative_to(inside(workspace.project, resource)) for resource in task.get('reads', []) + task.get('writes', [])), 'Release evidence must exist within declared resources')
    require(isinstance(report.get('gaps'), list) and all(isinstance(g, str) and g.strip() for g in report['gaps']), 'Release report requires explicit coverage gaps list')
