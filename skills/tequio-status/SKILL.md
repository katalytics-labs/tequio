---
name: tequio-status
description: "Orient users who ask where they are, what is next, what remains, or how to use Tequio; read workflow state without starting work."
---

# Tequio Status

Use this for `$tequio-status` and natural questions such as “Where am I?”, “What do I do next?”, “What is still outstanding?” and “How do I use Tequio?”. No extra guide agent is needed.

Select the actual project and explicit workspace from the request/context, default main only when appropriate. Run `python3 bin/tequio --project <root> --workspace <name> status`. No workspace returns intake or workspace-selection guidance without creating one. At intake, recommend `$tequio-briefing` for an idea or `$tequio-explore` for an existing usable brief. Read supplied context before recommending repeated discovery. Never guess the most recently modified workspace. Status is a read-only checkpoint, not permission to claim, recover, implement, write docs or publish.

## Overview and milestone docket

Give a brief present-tense overview of delivered outcomes, current focus, actual blocker and one useful next action. For substantial projects, follow it with a compact milestone docket using [milestone orientation](references/milestone-docket.md). In an installed discovery copy, read `.tequio/skills/tequio-status/references/milestone-docket.md`. Usually show around6–10 milestone rows, grouping older completed work where meaningful; do not pad small projects to meet a row target. Tiny projects, explicit “brief status” and “next action only” requests can omit the table. Offer fuller detail on request rather than dumping task history.

Use project-relevant names, honest state and the consequential remaining acceptance or next step. Connect the immediate next action to that docket. Counts support the explanation: distinguish ready-and-dispatchable, ready-but-waiting, drafts and explicit deferrals. Implementation, integration, qualification, owner approval and physical-device acceptance are different claims; say which are actually evidenced. Completed todos alone never prove product readiness.

Read only the existing relevant plan/milestone map, recent applicable handoff and task/evidence details needed for consequential claims. Do not invent milestones or a mandatory docket file. Superseded/legacy envelopes and successor work must not be double-counted; historical completion is not a current prerequisite. Ambiguous mapping remains briefly explicit, without reconstructing the entire project or starting another planning/review loop.

For overnight/parallel requests, suggest at most one or two coherent bounded outcomes from actual dependencies and read/write ownership. State setup/reconciliation first and owner acceptance needed later. Unknown independence stays unknown. Suggestions do not authorize agents, worktrees, claims, recovery, execution, spending or publication, and refreshed specialists alone are not a reason to repeat qualification. No promised hours or token savings without evidence.

Read the returned execution_checkpoints and usage alongside workflow/phases/tasks. Surface a configured due checkpoint or material invalid/unavailable observation in the concise answer, while keeping advisory limits separate from lifecycle readiness. Missing/legacy limits or unknown time stay explicit unknowns; do not turn each Status into an owner budget questionnaire. A configured policy with no usable clock can be baselined internally by the next authorized Build. Status never writes that baseline, stops checks, releases claims or grants scope. Reads are sequential observations, not an atomic snapshot.

Use the returned workflow/phases/tasks for recommendations and read relevant plans/task/evidence when a title/count is insufficient. The CLI reports recorded state, not a verified running process or semantic scope coverage. Do not announce tests or document updates unless their evidence exists. If the user asks for help, read [short user guide](references/user-guide.md) on demand (installed equivalent `.tequio/skills/tequio-status/references/user-guide.md`) and explain the four-command daily flow. Keep optional maintenance commands out of the basic tutorial unless relevant. A request to proceed after status may authorize the next workflow; the status check itself must not start it.

For coordination cost questions, Status already includes concise checkpoint/usage advice; internal `progress [TASK]` gives read-only published verification/review counts and optional time/loop checkpoint advice. Counts are historical, not current acceptance or all host activity. Token/cost usage is unknown in this version. Report missing limits or unusable time explicitly; use proof for current evidence, not progress counters.


Use Status `checks.state` to distinguish current evidence from missing/failed/stale/invalid/unavailable verification. `verification-required` means finish outstanding implementation and documentation edits, then verify a stable candidate before recording reconciliation or requesting independent review. Editing docs and recording their reconciliation are different steps; do not reverify automatically on every stale observation. Live-operation, migration, phase and integration reconciliation retain priority. Status itself executes nothing.

Draft `draft_readiness` shows only structural state/category. Inspect the named task's existing sourced resolution action privately before asking an owner question; a recorded category is not proof that owner input is necessary. Legacy/invalid metadata stays unknown, ready dependency waiting remains ready, and no extra draft paperwork is required. Done/superseded checks are not-observed rather than requalified by a status read.

When installation provenance is relevant, existing `doctor` offers on-demand installation_health, including no-workspace cases. Only explicit `doctor --source PATH` compares selected source bytes. Separate an intact older snapshot from owner modifications; neither observation grants repair/upgrade permission. Keep asset scans out of routine Status and omit raw private diagnostics from owner summaries.

## Useful outcome and remaining acceptance

Orient around delivered product behavior, open acceptance and the next useful slice, using counts as context. If revision is relevant, inspect its read-only status and effective dependency impact; an applied revision or unchanged consumer ID is not current proof. Keep historical completed work distinct from current prerequisites. For experiments, report the actual decision and evidence gap; missing prerequisites/budget remains unqualified. Surface cumulative checkpoint/correction limits and unknown billing without inventing performance savings or starting work.

## Optional model-delegation policy

For optional workspace routing questions, use `$tequio-routing status` (omitted action also means status), backed by `python3 bin/tequio --project ROOT --workspace NAME routing status`. Read `.tequio/skills/tequio-routing/SKILL.md` for complete installed defaults/schema/limits. Status creates nothing; invalid/unreadable enabled is unknown, not disabled. Report configuration state/digest without private choices/rationales or inferred actual-model compliance. On/off needs explicit owner intent; status must not mutate preferences. Missing host controls/identity remain unknown, with required enabled diversity pending at the host level, not a new CLI completion gate.

For an installation-specific question, `doctor --installation-only [--source PATH]` returns only installation health without workspace status or live lane inventory. It preserves existing health observations and limits; it does not upgrade or repair. Default doctor stays unchanged. Use this on demand, not as a routine Status asset scan.
