# Fix archive filtering

The existing task listing hides archived rows only when `include_archived` is false. Currently explicitly passing false still includes archived tasks. Reproduce using one active and one archived row. Preserve ordering, input rows and the default behavior (hide archived). Explicit true must still include both. Do not add storage, UI, dependencies or change the row schema. Update the existing usage contract and verify nearby behavior.
