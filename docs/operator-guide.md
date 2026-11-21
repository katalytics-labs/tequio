# Operator guide

## Four phases and orientation

Use `$tequio-explore`, `$tequio-design`, `$tequio-tasks`, then `$tequio-build`. Ask `$tequio-status` for location, one next action and outstanding work. The agent manages internal state; users need not handle claim tokens. Documentation/checks/review/handoff are part of implementation. Other skills are optional maintenance/inspection entry points.

All internal commands have the form `python3 bin/tequio --project ROOT --workspace NAME COMMAND ...`. ROOT defaults to the current directory; NAME defaults to main. Global options precede COMMAND. Do not infer a workspace from timestamps.

## Optional briefing preparation

Use `$tequio-briefing` for an idea, supplied research or a draft that needs shaping. The agent reads existing decisions first, asks one to three useful questions per round and stops once intent is sufficient for investigation. It avoids detailed feature/field/edge-case inventories and architecture choices unless essential or requested. Save interrupted drafts privately under `.tequio/intake/<name>/` with a resume note; resume without repeating settled answers. No workspace or analysis receipt is needed during drafting.

Present the concise brief and material unknowns for user review, respecting prior authorization for the handoff. Explore then creates the explicit workspace from the saved brief when needed. If the workspace already exists, reconcile its current brief instead of silently replacing it; changed inputs retain existing invalidation rules. Explore inventories sources, reuses relevant research and investigates gaps itself. Record source quality, access limits and unresolved decisions rather than burdening the user with agent-researchable questions. No mandatory market-validation gate is introduced.

## Lifecycle

1. `workspace --brief FILE` copies a substantive brief. The agent writes source-linked requirements/contracts under analysis/ and specs/, then records `record analysis`.
2. Write the architecture and dependency-aware delivery plan under plans/; `record plan`.
3. Author JSON tasks using templates/task.json, including source references, acceptance/check argv, dependencies, read/write ownership and documentation impact. `import-tasks FILE` validates them. Draft tasks preserve provisional scope without making it executable.
4. `claim --owner ID [--task ID]` returns a private token and the detailed ready task. Coordinate disjoint work within local capacity; host authorization and agent availability still apply. Use the actual source/contracts, not a remembered task title.
5. Implement real behavior and update declared docs alongside it. `heartbeat TASK --token TOKEN` renews genuinely live work. `release ... --reason TEXT [--blocked]` stops ownership or records a blocker/resumption condition.
6. `verify TASK --token TOKEN` executes task argv checks in the project root. Inspect their actual coverage/results. Nonzero, missing, timed-out or changing-content checks do not produce successful evidence.
7. Write a private reconciliation from templates/documentation-report.json: every task source maps to actual project files and declared doc paths. Explain broader out-of-task scope honestly. Resolve deviations through replanning. `record-docs TASK --token TOKEN --report reviews/docs.json` binds the result to current inputs/checks/content and invalidates prior review.
8. Obtain a genuinely independent correctness review, and adversarial security review for security-risk tasks. Reports must inspect actual acceptance, wiring, docs and failure cases. Register delivered evidence with `review TASK --token TOKEN --actor REVIEWER --kind correctness --report reviews/report.md [--finding TEXT]` (security uses `--kind security`). No reviewer means review-pending, not a fictional identity.
9. `complete TASK --token TOKEN --summary TEXT` refuses missing/stale/altered checks, docs, required reviews or unresolved findings. `checkpoint --summary TEXT --next TEXT` saves a durable handoff. At milestone boundaries inspect combined results and refresh provisional work; individual closed tasks do not establish whole-product readiness.

## Documentation and task contracts

Every ready task declares `documentation` as update (owned concrete paths and impact reason) or not-needed (empty paths and a specific reason for review). Update files must actually change from the claim baseline; a matching receipt is not proof of correct prose. Correctness review must cover the current reconciliation and challenge unjustified no-change decisions. Plans are intended behavior; code/tests establish observed behavior. Do not document unfinished plans as shipped functionality or silently adjust approved scope to match accidental code.

Task states: draft, ready, running, review, blocked, done, superseded. SQLite holds authoritative immutable task detail/status; JSON task files are readable inputs, not a silent mutation mechanism. Relevant contracts are in [task-contract.md](../templates/task-contract.md).

## Recovery and replanning

`status` and `resume` are read-only execution-state checks. Claims and leases are not evidence of a live/stopped process. Inspect genuine host handles, reconnect to confirmed live work, and recover only with a recorded reason after inspection. `recover TASK --reason TEXT` permits expired/blocked records; it never kills or restarts processes.

When requirements, specialist qualifications or architecture change, reconcile live work, release active claims, then `replan --reason TEXT`. Refresh analysis/specs/plans, record phase receipts and import replacement IDs. Superseded history and completed results remain evidence, not proof of new requirements. Older unfinished task formats lacking current documentation/specialist contracts require this explicit path; never patch SQLite to bypass it.

## Specialists, privacy and release preparation

Use `$tequio-specialists` only when relevant project expertise is missing. Qualified packages are project-owned and outside installer ownership. Research candidates do not become implementation authority. See [specialist factory](specialist-factory.md).

Commands/checks execute real code in the inherited environment, not a sandbox. Keep tokens/output/evidence private. The hook command is a read-only status audit, not automatic host interception. `$tequio-package` prepares an inspected local candidate; it does not authorize remote pushes, publication or deployment. Use the source installer for upgrades; locally modified owned files require deliberate reconciliation. See [compatibility](compatibility.md) and [validation](validation.md).

## Scoped work and evidence inspection

Use the conservative default unless independence can be assessed explicitly. A new `scoped-v1` task must declare reads/writes, shared contracts, configuration and mandatory context; see [freshness](freshness.md). Checks do not infer dependencies from command arguments. Unreferenced future plan additions may leave a scoped task eligible, while global phase orientation still conservatively requests reconciliation; new task imports require current phase receipts. Do not edit old task bodies to retrofit scope. Later work that intentionally changes a completed prerequisite's files needs an explicit current-state milestone/replan rather than pretending its old evidence remains current.

Use `proof` or `proof TASK` to inspect actual checks, docs and required reviews without running work. It lists safe local receipt/report references and distinguishes historical closure from current evidence. Follow [the report contract](evidence-report.md); do not publish the output as though paths alone were safe customer data.

## Backlog runs and Git lanes

Default build mode executes the next chunk. The user may authorize a bounded backlog/milestone once. Record scope/task IDs, parallel capacity, integration branch and allowed local commit/merge operations in private workspace `run-policy.json`, using the installed template. Build follows that established policy, dispatches ready work, obtains genuine review and continues until completion, a real blocker or a host/session limit. The host must remain running or resume from checkpoint. No overnight-completion guarantee follows from the policy.

`git status` discovers existing repository/isolation state. `git configure worktrees` explicitly enables isolation; `git lane NAME` creates an independent writing checkout; `git configure shared` preserves existing lanes but disables new creation. `.tequio/` must be ignored and untracked. Never create a repository merely to enable Tequio. Installed ignored launchers/runtime are absent in lanes: call the original launcher's absolute path, keeping lifecycle `--project` at the original controller. Worktree creation itself does not commit or merge.

Under the agreed policy, workers commit only inspected task-owned files; the host orchestrator alone integrates accepted commits serially on the agreed branch. Preserve user changes and inspect in-progress Git operations before merge. Verify the combined result, reconcile docs and refresh genuine reviews before closure. Resolve conflicts within scope or preserve them and checkpoint a blocker. No blanket staging, forced reset, implicit cleanup, push or publication. See [Git prerequisites/recovery](git-isolation.md) and the build skill's complete procedure.

Inspect `.tequio/manifest.json` for the executing installer release and owned payload hashes. An alternate `--source` remains subject to full bundle validation; metadata is not a substitute for current source/content verification.

## Recovering a controller-started check

Read `status` task verification observations or `verification-status TASK`; inspect genuine host/local process handles as well. A held operation lock or observed live group prevents recovery/release/reassignment and completion despite lease expiry. Do not delete a lock file: replacing its inode defeats coordination. After actually stopped handles, use ordinary inspected `recover`; an unknown launch interval additionally needs `--stopped-check` with a substantive reason. That acknowledgement cannot override a held lock/observed group and is not authenticated proof. Recovery never kills/restarts the worker. Exact unsupported cases and persistence ordering: [check recovery](check-recovery.md).

Heartbeat now renews the current active token independently of stale inputs and reports execution drift. Reconcile drift before verification/closure; a renewed lease does not make stale work acceptable. Interrupted attempts without accepted receipt attachment cannot reuse an older successful result for completion.

## Resume context and damaged checkpoints

Compare `policy_changed`, `task_scope_changed` and `task_progress_changed`; unknown values remain null for absent/legacy/damaged context. A changed policy or newly imported task is not an implicit scope/permission grant. Reconcile with the latest persistent user authorization and current policy, then continue authorized work without asking routine questions again. Invalid policy needs reconciliation; validity only describes structure. A damaged checkpoint returns a structured issue and current status, preserving original bytes; there is no automatic repair or fallback that silently pretends old input is current. See [the schema and legacy behavior](run-context.md).

## Record integration before native merge

For an opted-in Git task, use `integration plan TASK --token TOKEN --lane NAME --commit FULL_SHA --branch BRANCH` from its original controller/workspace. Inspect the complete unmerged delta against task ownership and obtain the real code review required by your workflow. Plan records metadata; it grants no Git permission. Merge the recorded full SHA under the existing host run policy, never a newer branch tip selected implicitly.

On continuation, `integration status TASK` shows pinned intent and current facts. `integrated-unrecorded` means do not repeat the merge: reconcile first. `integration reconcile TASK` records deduplicated observations, with no token because it cannot grant approval or complete work. Fresh verify/docs/required review follow the recorded boundary. `ready-for-closure` is not `accepted`; normal guarded `complete` remains necessary. A replacement owner must authenticate the identical plan retry before continuing. Wrong/dirty/conflicted/unavailable/rewritten state is preserved for inspection; null integrated status means unknown, never proof of absence.

Closed tasks and accepted history can become stale when target HEAD or requirements change. Do not attempt to reopen a done task by patching records; plan an explicit current-state qualification/milestone when needed. Cherry-pick/squash/rebase equivalence is not inferred, and pending is not permission to blindly merge again. See [the journal states and ordering](integration-journal.md).

## Task-authoring review gate

Before new task imports, use prepare-tasks and distinct correctness/redteam reports as described in [task review](task-review.md). The gate also covers draft batches. It is separate from implementation and integrated-release reviews; existing stored history is preserved.

## Execution progress and economic checkpoints

Internal `progress [TASK]` reads historical CLI publication counts and optional `execution_checkpoints` advice without executing checks, accepting work or changing state. Counts do not certify current acceptance; use proof for that question. Declare time/loop checkpoints before prolonged autonomous work, keep unavailable token/cost usage explicitly unknown, and report before extending the agreed chunk. Legacy policies remain compatible but visibly unbudgeted. Do not turn every intermediate edit into a full dual-review lifecycle; final actual independent correctness/security reviews still cover a stable verified/documented candidate. See [the exact limits and rollout procedure](execution-efficiency.md).

## Installing into the Tequio source checkout

Run `python3 bin/tequio install /absolute/path/to/this-checkout` from reviewed source to add project-local skills and private runtime/reference snapshots to the same directory. Resolved source and target must be identical for `source-checkout` mode. The existing safe regular source `bin/tequio` remains untouched, including permissions, and is never installer-owned or newly ignored. Installation refuses to convert a manifest that already owns that launcher. Ordinary different-source collisions and modified-owned-file refusals remain unchanged. Uninstall removes only owned private assets and retains the source launcher and workspace evidence.

In this mode `bin/tequio` deliberately continues executing current `src/` code; copied runtime/assets and skill discovery are installation snapshots. This is not a frozen execution controller. After reviewed changes, rebuild the source bundle and explicitly reinstall to refresh snapshots; a new agent session discovers the installed project-local skills. No global hooks/settings, external project upgrades or automatic live-state migrations are implied.


## Checkpoint advice in Status

Existing-workspace `status` also returns additive top-level `execution_checkpoints` and `usage` objects, reusing the exact `progress` field shapes and semantics. It does not duplicate progress task lists/counters. Existing workflow.next, lifecycle readiness, intake and lane routing are unchanged. In-repo consumers accept these additive fields; external closed-schema consumers may need adaptation.

A failed checkpoint observation yields a fixed unavailable envelope: state/clock `unavailable`, limits/elapsed_wall_seconds null, checkpoint_required true and reasons `[{"reason":"observation-incomplete"}]`. Usage is `{tokens:null,cost:null,source:unavailable}`. No private exception text, policy prose or automatic repair is included. Observations are sequential, not atomic across files/database. This fallback concerns checkpoint observation; it does not promise arbitrary corrupted workspace state is readable.

The Status agent surfaces a configured due checkpoint or material invalid/unavailable observation while keeping one immediate action. Missing/legacy limits and unknown usage remain unknown, without mandatory owner budget questions. If a configured policy has no usable time anchor, the next authorized Build may record its baseline internally; Status stays read-only. Advice never stops a live operation, releases ownership, changes acceptance or grants authorization. Full progress/proof details remain optional internal inspection.


## Evidence-aware Status prerequisites

Status adds per-task `checks:{state}` with current, missing, failed, stale, invalid, unavailable or not-observed. It uses the existing check-evidence validator for unfinished tasks without returning raw arguments/output/errors or invoking full proof; done/superseded history is not-observed. This is a sequential advisory observation, not acceptance or a changed-file explanation.

For an otherwise review-stage task without current checks, workflow stage `verification-required` recommends existing Build: finish outstanding implementation/docs edits, then verify the stable candidate before recording reconciliation or obtaining review. Consumers matching a closed workflow-stage list must allow the new stage. All existing fields remain; live/uncertain operations, migration, stale phases and integration reconciliation retain priority. Current checks then lead to reconciliation, required review, findings correction or closure as appropriate. A status read never launches checks, recovers ownership or grants scope.

Draft rows add `draft_readiness:{state,category}`: recorded, legacy-unknown, invalid or not-applicable, with a known existing category or null. Draft-only guidance names the first relevant task in recorded order. It omits blocker reason/action/source prose; the agent privately inspects the sourced resolution action and judges whether owner input is actually needed. Metadata is not semantic truth. No imported history is rewritten, no draft is promoted and fully specified dependency-waiting work stays ready.

A durable stopped verification attempt still requires result reconciliation: an older otherwise-current PASS does not remove that guard. Integration journal needs-checks/needs-docs/needs-review states likewise require fresh post-integration evidence even when ordinary receipt fields look current. Status recommends inspecting that context rather than announcing closure.


## On-demand installation health

`doctor [--source PATH]` preserves task/intake/git observations and adds version1 `installation_health` even without a workspace. Its execution, installation, owned and source_comparison objects distinguish executing layout/version, recorded snapshot metadata, owned byte/mode drift and an explicitly selected source. An intact older snapshot can coexist with live source; equal versions do not imply equal payload. Exit0 means observations were delivered, not pristine assets or permission to upgrade.

Ordinary Status/hook/resume never scan owned assets. Doctor never repairs, fetches, imports selected source, creates a workspace or changes launcher/ignore/metadata. Unsafe manifest paths yield null-path diagnostics and are not read/echoed; only installer namespaces/known workflow discovery assets are eligible. Manifests are capped at4MiB, paths10000 and asset bytes256MiB per observation; limit exhaustion is incomplete, not intact. Issues/differences cap10 with total/omitted counts. Missing, invalid and unavailable states stay distinct. Source comparison captures and validates bounded bytes before pure prefix rendering and parses the version constant with AST. It is sequential local evidence, not atomic/authenticated ownership or public-safe metadata. Existing collision/modified-owned/refusal/removal protections remain unchanged; real snapshot refresh is a separate action.


## Opt-in compact pickup

`resume --summary` delivers version1 fixed context without duplicated saved/current task arrays or saved prose. Default CLI/Workspace.resume output remains unchanged. The compact object includes workflow reason codes, lifecycle counts, changed/unknown flags, context digests, checkpoint issue/reference, optional next-task focus, active count/first3items/omitted count, checkpoint advice with first3reasons/omissions and unknown usage. Normal long-prose/many-history fixtures stay below8KiB; this is delivery volume, not parsing-memory/cost measurement.

A no-follow regular checkpoint acquisition happens before Status/progress; the same immutable bytes are injected through private clock helpers and hashed for the reference. Replacement cannot bind a later file to earlier parsed content or follow an external symlink indirectly. Unsafe/missing/unreadable/invalid/legacy/unsupported context remains explicit; no authority or liveness is inferred. Malformed projected enums/IDs become invalid/unknown, not raw private text. Existing-workspace summary preserves sequential-observation limits. Missing workspace in summary mode returns existing intake/selection guidance without creating state; default resume still refuses it. Git lanes read the original controller. Summary is private operator metadata, not a public export or execution authorization.

Compact acquisition pins no-follow directory descriptors from the canonical project anchor. If the workspace parent is unsafe, it returns unavailable context without inspecting aliased current state; active count/omissions are null because they are unknown, not zero. This does not alter the default full-resume parser.

## Bounded refinement and experiments

Use Redirect/Tasks and [reviewed revision](revision.md) when selected unfinished producers need replacement and unchanged consumers can explicitly rebind. Preview impact first; prepare, obtain distinct actual correctness/redteam reviews, then apply the exact digest. Changed consumer contracts require new IDs. Done history stays untouched; add a reviewed successor before rebinding unfinished consumers. Broad replan remains appropriate for broad remaining-plan changes. Back up and explicitly upgrade before overlay use; old-runtime downgrade is unsupported.

An uncertain product path may use the short optional [experiment template](../templates/experiment.md). Reuse existing evidence, choose the smallest faithful positive/adverse observations and declare effects/limits. Supported/unsuitable requires complete sufficient observations; missing prerequisites or exhausted budget remain unqualified. Return the usable outcome, open acceptance, next useful slice and checkpoint/usage limits. Cheap feedback precedes costly stable integration; required current checks and genuine final reviews still govern closure.
