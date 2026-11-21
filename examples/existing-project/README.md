# Existing-project archive-filter correction

This is a deterministic, pre-authored lifecycle exercise for an existing Python helper. It uses no model, network, generated specialist or invented reviewer. The fixture contains a real boolean predicate defect: `False is not None` evaluates true, so archived tasks leak into default and explicit-false listings.

Run from the source root:

```sh
python3 examples/existing-project/run_demo.py
# Keep the disposable project for inspection (path must not exist):
python3 examples/existing-project/run_demo.py --output /tmp/archive-filter-demo
```

The source bundle must be current and valid for installation. Installation integrity failures are real failures; refresh the bundle through the normal source packaging procedure before retrying. The script never disables integrity checks or changes an existing output folder.

The script installs Tequio into a new temporary project, copies the buggy existing helper/tests/docs, and proves that two filtering tests fail while nearby tests pass. It records focused nonempty analysis, spec and plan, imports and claims one task, applies a prewritten one-line correction, updates the existing usage document and runs all four tests through `verify`. It reconciles every declared source to actual code/tests/docs and tests that completion is refused first without documentation evidence and then without independent review. Tokens remain private. Its final checkpoint is review pending; the default temporary project is then removed. Use `--output` to retain evidence and arrange a real reviewer.

This proves only the behavior actually exercised by the script when it runs successfully. The Markdown artifacts and patch are authored in advance; they do not prove model reasoning, interactive skill discovery, delegation, cross-session recovery or speed gains. A reviewer must inspect the retained actual artifacts and produce their own substantive report before anyone records review or closes the task. The script never supplies a reviewer identity.

For a hands-on agent exercise, use `brief.md` and the buggy fixture as input, then follow the existing four skills. Do not present that run as equivalent to this deterministic check: retain its actual commands, failures, changes and genuine review evidence separately.

Task-authoring review receipts in this deterministic demo are explicitly synthetic, pre-authored fixtures. They demonstrate receipt/gate mechanics, not genuine independent review. Live projects must obtain separate actual correctness and red-team reports; implementation review remains a separate gate.
