---
name: tequio-explore
description: "Investigate a project brief and current source to produce evidence-linked requirements, contracts and risk analysis before planning."
---

# Tequio Explore

## Runtime and context

Use `python3 bin/tequio --project <absolute-project> --workspace <name> ...`. Select workspace explicitly from the user's task or the default `main`; never pick by modification time. Installed instructions/assets are under `.tequio/`. Read `.tequio/roles/orchestrator.md` and only relevant specialist skills. User/host instructions govern; this toolkit does not override authorization or grant tools. Keep task tokens, evidence, prompts and working notes private. Do not print secrets in summaries.

## Research responsibility

Start with a usable brief; suggest `$tequio-briefing` if product intent still needs shaping. A brief can be concise and have open questions. Do not require completed research as an entry condition.

Inventory supplied research and decisions first, retaining source references, dates, evidence quality and conflicts. Reuse relevant findings and verify drift-prone or consequential claims. When research is absent or insufficient, perform proportionate investigation of the questions that affect scope, feasibility, contracts or risk: inspect actual source/tests/interfaces and consult relevant primary documentation or external evidence where needed and available. Product/domain research is appropriate when material to the brief; market validation is not a mandatory gate. Avoid open-ended research or collecting sources without a decision they inform.

Keep facts, user decisions, recommendations and assumptions distinct. Record what was investigated, sources and limitations, and unresolved questions. If access/tools are unavailable, state the gap and whether it blocks planning; never invent research or declare a gap resolved. Ask the user for intent decisions and essential facts only they can supply, not for research the agent can conduct. Research may reveal a need to revise the brief: reconcile material changes with the user and refresh affected receipts rather than silently expanding scope. Stop when evidence is sufficient for planning and remaining uncertainty is explicit.

## Procedure

Read the workspace brief and user-supplied research/decisions. If no workspace exists, create it with `workspace --brief <file>`; creating a workspace copies the brief, not an implementation. Inspect current source and actual interfaces, including existing tests and limitations. Reuse dated research where relevant and investigate meaningful gaps; do not assume a market-validation gate or invent product requirements.

Write substantive Markdown under workspace `analysis/` and `specs/`: requirements with source IDs; user journeys and failure cases where applicable; current versus intended state; contracts/data/access/state boundaries; alternatives and recommendation; assumptions, evidence quality and unresolved decisions. Map every in-scope requirement to a spec/analysis section. Request targeted specialist/reviewer input when authorized and useful. Capture actual findings, not ceremonial approval.

Run `record analysis` only after the artifacts exist and have been checked. The receipt hashes files; it does not establish semantic completeness. Report what is settled, what is unknown and whether planning can proceed. Do not implement product code in this phase.

## Existing-project bug or small feature

Scale the analysis to the requested delta. Read repository guidance, the affected call path, tests and maintained contract first. A short brief should identify the observed symptom or desired addition, a reproducible input, expected output and explicit exclusions. Keep existing product decisions as context rather than regenerating the product brief.

For a bounded change, one focused `analysis/change.md` and one focused `specs/change.md` can suffice: cite the brief and actual file/symbol evidence; distinguish observed behavior from hypotheses; state the changed contract, preserved invariants, acceptance cases and relevant failure cases. These must be substantive, nonempty artifacts. If investigation reveals a wider contract, migration or access boundary, expand the affected analysis and plan before execution. Record the normal analysis receipt; proportionality does not waive source coverage or freshness.

## Decisive investigation

Name the uncertainty and useful product outcome it blocks. Inventory reusable code, research and current evidence first. When execution is needed to resolve it, propose the smallest faithful positive/adverse observations, prerequisites, actual effects and time/correction/resource ceiling; use optional `.tequio/templates/experiment.md` when helpful. Explore does not authorize product implementation or costly effects by itself. Supported/unsuitable needs sufficient complete observations; inaccessible input or exhausted budget remains unqualified. Hand off the decision, evidence gap and next useful slice.
