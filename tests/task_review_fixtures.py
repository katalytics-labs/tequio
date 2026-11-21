"""Synthetic task-review receipts for lifecycle unit fixtures, never live review."""
import json
from tequio.task_review import TaskReview, AREAS

def reviewed_import(workspace, path):
    gate = TaskReview(workspace)
    batch = gate.prepare(path, 'synthetic-task-author')['batch']
    for kind in AREAS:
        report = 'reviews/synthetic-task-' + batch + '-' + kind + '.json'
        (workspace.path / report).write_text(json.dumps({
            'batch': batch,
            'summary': 'Synthetic deterministic task-review fixture: exercises local gate mechanics only, not independent semantic review or actual author identity.',
            'coverage': {area: 'Synthetic fixture coverage of ' + area + '; actual task quality remains outside this deterministic lifecycle test.' for area in AREAS[kind]},
            'findings': [],
        }))
        gate.review(batch, 'synthetic-task-' + kind, kind, report)
    return workspace.import_tasks(path)


def synthetic_draft(task):
    """Explicit synthetic planning decision, only for isolated gate tests."""
    task['stage'] = 'draft'
    task['draft'] = {'version': 1, 'category': 'unresolved-product-decision',
                     'reason': 'Synthetic fixture owner has not selected the required product behavior.',
                     'next_action': 'Ask the synthetic fixture owner to select the required product behavior.',
                     'source': task['sources'][0]}
    return task
