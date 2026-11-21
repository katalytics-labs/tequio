"""Existing task-list helper with the reported bug preserved."""

def visible_tasks(rows, include_archived=False):
    return [row for row in rows if include_archived is not None or not row["archived"]]
