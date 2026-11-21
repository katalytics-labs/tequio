"""Pre-authored synthetic planning-review replay; not genuine independent review.

Used only by deterministic demos to exercise the gates. Real projects must obtain
actual separate reviewer reports; these actor labels do not provide that evidence.
"""
import json

def prepare_demo_reviews(project, workspace, task_file, run):
    batch = run(project, 'prepare-tasks', str(task_file), '--author', 'synthetic-demo-author')['batch']
    areas = {'correctness': ['requirements','readiness','dependencies','ownership','checks'],
             'redteam': ['failure-cases','security-classification','privacy-export','workflow-traps']}
    for kind, keys in areas.items():
        report = 'reviews/synthetic-planning-' + kind + '.json'
        (workspace / report).write_text(json.dumps({'batch': batch,
            'summary': 'Pre-authored synthetic task-review replay for deterministic demonstration only. It does not represent an actual independent review of model-generated work.',
            'coverage': {key: 'Synthetic demonstration of ' + key + ' report binding; no real independent semantic assessment claimed.' for key in keys}, 'findings': []}))
        run(project, 'review-tasks', batch, '--actor', 'synthetic-demo-' + kind, '--kind', kind, '--report', report)
    print('Planning review: synthetic receipt replay only, not genuine independent assessment.')
