# Integrated build and continuation

This example provides a synthetic evidence-ledger application: validated place/status queries, correctly quoted CSV evidence export, and a command-line interface composing both. It has no network or third-party dependencies. The curated implementation was produced in a bounded live host-agent exercise; the replay below uses that prebuilt code.

```sh
python3 examples/integrated-build/run_demo.py
# Optional: retain a fresh replay folder for inspection
python3 examples/integrated-build/run_demo.py --output /absolute/new/folder
```

The replay runs actual application tests and a filtered CLI export, installs a standalone Tequio snapshot, claims two disjoint components concurrently, verifies real component behavior and documentation, preserves A's scoped evidence through B's independent writes, and reads a checkpoint from a fresh CLI process. It deliberately stops review-pending and proves that a missing genuine independent review blocks completion. It also changes a referenced requirement and confirms that further verification is blocked until reconciliation/replan. It never impersonates the live reviewers or transfers their receipts to the replay. `--output` refuses an existing directory.

## Live workflow exercised

The live exercise used independent writing agents in separate optional Git lanes. Each claimed its central task, implemented only its assigned module/tests/docs, tested and committed locally. A genuine independent reviewer inspected both lane commits. The host orchestrator merged them serially, ran checks in the authoritative checkout, reconciled documentation, confirmed A's evidence survived B's merge, and registered delivered review before closure.

A dependent CLI integration then used a planned checkpoint/release and a fresh no-history agent continuation. This is cooperative handoff, not recovery from a killed agent. Git integration used native Git under the host orchestrator's bounded local commit/merge permission; the helper did not perform autonomous merges. Source code, tests and current user documentation are curated here; prompts, internal conversations, tokens, local databases and raw host logs are excluded.

A separate bounded installed Codex CLI observation exercises the four workflow skills across preparation and a resumed recorded session. Consult the current [compatibility notes](../../docs/compatibility.md) for observed version, scope and limits; do not infer universal discovery or automatic quality.

## Interpretation

This is one small application workflow on one host configuration, with independent review and real integration. It is not a production application, an adoption study, a crash-recovery guarantee, an unattended-overnight guarantee or a matched comparison against another framework. Model/provider cost was not independently measured. The deterministic replay does not call a model and cannot reproduce the live agents' reasoning or establish review independence.

## Observed result

The live application finished three tasks with 25 passing combined tests. Two writing claims overlapped and produced separate reviewed commits; A retained current checks/docs after B integration. The dependent task continued from one agent's deliberate checkpoint/release in a different no-history agent. Independent review found that non-array JSON could slip through the CLI; the corrected implementation was re-tested and accepted before integration.

The separate native CLI observation used version 0.167.0 on macOS. Preparation took 106.91 seconds; a read-only resume stopped without a false success (65.11 seconds); an explicitly writable resume replanned a malformed supplemental check and completed after genuine delegated review (137.53 seconds). Those timings are observed process durations, not a matched performance comparison. Existing account authentication and host capabilities were available; this was not a clean-machine qualification.

Task-authoring review receipts in this deterministic demo are explicitly synthetic, pre-authored fixtures. They demonstrate receipt/gate mechanics, not genuine independent review. Live projects must obtain separate actual correctness and red-team reports; implementation review remains a separate gate.
