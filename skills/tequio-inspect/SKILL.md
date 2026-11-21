---
name: tequio-inspect
description: "Independently assess a completed task\u2019s actual behavior, requirement coverage, integration and evidence before closure."
---

# Tequio Inspect

## Runtime and context

Use `python3 bin/tequio --project <absolute-project> --workspace <name> ...`. Select workspace explicitly from the user's task or the default `main`; never pick by modification time. Installed instructions/assets are under `.tequio/`. Read `.tequio/roles/orchestrator.md` and only relevant specialist skills. User/host instructions govern; this toolkit does not override authorization or grant tools. Keep task tokens, evidence, prompts and working notes private. Do not print secrets in summaries.

## Procedure

Read `.tequio/roles/correctness-reviewer.md`, the full task/sources and current code, not an implementer's conclusion. Confirm a real execution receipt exists; inspect its commands, outputs and coverage. Check acceptance criteria one by one, integration beyond the diff, unintended regressions and documentation/contract freshness. Run targeted checks where they resolve uncertainty. Independent review is separate from a test suite.

Write a substantive workspace reviews/ Markdown report recording reviewer identity, paths/behavior inspected, commands/results, criteria coverage, limitations and open findings. An unavailable or errored review is not a clean report. Give the orchestrator the report path and explicit findings for the `review --kind correctness` receipt. Never invent an independent identity. Do not silently fix the code being independently reviewed; return actionable findings for the owner.

Check the documentation reconciliation against the actual plan/spec sources, todo scope, implementation and tests. Confirm declared doc updates explain current behavior and omit unimplemented promises/private chatter; challenge unjustified not-needed decisions and scope drift. The correctness review must cover the current docs receipt; a green test command or matching file names is not semantic proof. Return unresolved discrepancies as findings.

## Review scope and proportion

Identify whether the assignment is developer feedback, focused finding recheck, stable final correctness review or combined qualification. Partial feedback cannot satisfy final acceptance. Inspect exact current delta, checks/docs references, affected surfaces, unresolved findings and limits; use independent cheap controls where they resolve uncertainty. Repeat costly effects only for substantive reproduction/current-proof need. Material authorization/privacy/interface/process/configuration corrections need fresh affected proof and actual independent review. Retain all required final correctness/security coverage.

Check effective revision edges/input bindings as well as immutable bodies; prior consumer proof cannot survive rebinding. For experiments, distinguish sufficient completed observations from missing input/budget and require a concrete next product slice. Synthetic actor labels demonstrate mechanics only. Report usable outcome and open acceptance without claiming whole-product readiness from task closure.

## Optional model-delegation policy

Read `.tequio/skills/tequio-routing/SKILL.md` and applicable private policy when selected-review diversity is requested. Independent actors and diverse models are separate: same-model distinct actors may satisfy existing independence; different-model self-review cannot. Required diversity needs sufficient observed underlying reviewer/implementer identity difference; aliases, requests, provider names and self-report do not establish host-verified difference. Unknown stays host review-pending; preferred fallback follows policy. The CLI does not compare/authenticate models or enforce this additional instruction. Cite optional private delegation records truthfully without changing report schemas or weakening mandatory current checks/docs/review.
