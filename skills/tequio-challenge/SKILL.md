---
name: tequio-challenge
description: "Challenge a bounded change or milestone against concrete failure and security scenarios, retaining evidence and unresolved findings."
---

# Tequio Challenge

## Runtime and context

Use `python3 bin/tequio --project <absolute-project> --workspace <name> ...`. Select workspace explicitly from the user's task or the default `main`; never pick by modification time. Installed instructions/assets are under `.tequio/`. Read `.tequio/roles/orchestrator.md` and only relevant specialist skills. User/host instructions govern; this toolkit does not override authorization or grant tools. Keep task tokens, evidence, prompts and working notes private. Do not print secrets in summaries.

## Procedure

Read `.tequio/roles/security-reviewer.md`. Derive attack/failure surfaces from requirements and actual code: trust boundaries, authorization, state transitions, input parsing, retries/concurrency, private outputs and release paths. Try to refute the guarantees, including denied/off-happy-path cases; passing correctness tests is not security proof.

Scope the work to the assigned change/milestone and authorize only isolated fixture operations. Write evidence-based workspace reviews/ findings with reproduction, severity/impact, tested surfaces, coverage gaps and correction criteria. Return actual delivered evidence; do not count a failed agent as zero findings. Security-sensitive tasks require their own security report/receipt. Bound correction rounds to concrete findings; if unresolved, leave the task open with a precise blocker rather than claim convergence. At milestone boundaries review the integrated union, not only the latest shard.

## Security workflow

Challenge the task security classification and actual boundary behavior. Release security review must cover the exact integrated candidate, dependencies/locks, configuration/defaults and privacy/export boundaries using the structured report. Read [security workflow](../tequio-tasks/references/security-workflow.md); record unresolved gaps honestly as findings.
