# Task listing

`visible_tasks(rows, include_archived=False)` lists task rows in input order. Rows contain `id` and boolean `archived`. The intended default hides archived rows; the current implementation has a known filtering defect. Pass true to include archived rows.
