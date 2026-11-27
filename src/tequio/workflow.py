"""Public skill names, separate from deterministic lifecycle verbs."""
SKILL_IDS = {'brief': 'tequio-briefing', 'analyze': 'tequio-explore', 'plan': 'tequio-design', 'write-todos': 'tequio-tasks', 'implement': 'tequio-build', 'verify': 'tequio-check', 'review': 'tequio-inspect', 'redteam': 'tequio-challenge', 'routing': 'tequio-routing', 'status': 'tequio-status', 'checkpoint': 'tequio-handoff', 'resume': 'tequio-pickup', 'replan': 'tequio-redirect', 'explain': 'tequio-explain', 'codify': 'tequio-learn', 'write-specialists': 'tequio-specialists', 'prepare-release': 'tequio-package'}
WORKFLOW_SKILLS = frozenset(SKILL_IDS.values())

def skill_id(phase):
    return SKILL_IDS[phase]
