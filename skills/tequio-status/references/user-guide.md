# Using Tequio

Tequio guides a coding agent; it is not a model service or a program that autonomously writes code when its Python CLI runs alone. Install into an existing project, start a new host session for discovery and start with an idea or existing brief. The agent handles workspace files, task ownership and internal receipts.

## Optional start

Use `$tequio-briefing` when you need help shaping intent. Expect a few focused questions and a short brief with unknowns left visible, not an exhaustive questionnaire. Drafts can be saved and resumed privately before workspace creation. Skip this step when a usable brief already exists. Research belongs to Explore.

## Four everyday commands

1. `$tequio-explore` — “Read this brief and inspect the project. Work out requirements, risks, open questions and relevant contracts.” Reuse existing research or investigate material gaps when none exists; record evidence and uncertainty.
2. `$tequio-design` — “Recommend the architecture and delivery approach.” Discuss material decisions; keep approved versus candidate choices explicit.
3. `$tequio-tasks` — “Turn the agreed plan into detailed bounded tasks.” Include acceptance, integration, docs impact, dependencies and relevant expertise. Complete scope stays visible; unfinished plans do not become implemented claims.
4. `$tequio-build` — “Do the next ready chunk.” Agent coordinates relevant expertise, implements real behavior, updates docs alongside it, executes checks, records plan/todo/code reconciliation, obtains independent review, closes only with evidence, and leaves a checkpoint. Default one bounded chunk, not an unchecked drain of the entire backlog.

Whenever disoriented: `$tequio-status` or ask “Where are we and what is the next step?”. It reports a short checkpoint without executing anything, including relevant configured time/verification checkpoint advice and unknown usage. Such advice does not change task readiness or stop active work; missing legacy limits do not require a new questionnaire. Ask “How do I use Tequio?” for this guide. CLI `python3 bin/tequio --help` describes internal operations and summarizes the daily flow; users need not memorize those internal commands.

## Only when needed

- `$tequio-specialists`: missing expertise for this project's actual stack; not a required step for every task. Tequio ships the factory, not another project's specialists.
- `$tequio-pickup`: reconcile actual state after a session/interruption; implementation normally does this automatically.
- `$tequio-redirect`: changed requirements/architecture; preserve history and update affected tasks deliberately.
- `$tequio-inspect` / `$tequio-challenge` / `$tequio-check`: explicitly inspect a change. Appropriate checks and review are normally part of implementation.
- `$tequio-handoff` / `$tequio-learn`: explicit handoff or durable learning; ordinary task execution already leaves progress.
- `$tequio-package`: inspect a local candidate when appropriate. It does not authorize publishing.

Documentation is part of implementation, not another command to remember. Reconcile plans and detailed todos against current code/tests; write what works now, mark incomplete scope honestly and triage deviations. Relevant docs may include interfaces, state/data/permission contracts, installation/operation, recovery and accepted architecture decisions. Private prompts, transcripts and development chatter do not become product documentation.

Skills remain modular internally so the orchestrator loads relevant procedures only. The everyday surface is four steps plus status; no separate document or help skill. Supported host discovery/delegation still depends on the harness; direct instructions and Python lifecycle tooling have documented limits.

When installation provenance is relevant, existing `doctor` offers on-demand installation_health, including no-workspace cases. Only explicit `doctor --source PATH` compares selected source bytes. Separate an intact older snapshot from owner modifications; neither observation grants repair/upgrade permission. Keep asset scans out of routine Status and omit raw private diagnostics from owner summaries.

## Milestone orientation

Ordinary Status combines the next useful action with a compact milestone docket for substantial projects, grounded in existing plans and actual acceptance evidence. It distinguishes backend from client delivery, reviewed design from owner approval, and isolated qualification from attended device acceptance. Ask “brief status” or “next action only” for a shorter answer. Overnight/parallel suggestions are proposals from dependencies/ownership, not permission to start work. Unknown milestone mapping stays explicit; no new docket document is required. See [milestone orientation](milestone-docket.md).
