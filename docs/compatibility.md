# Compatibility

## Historical multi-version qualification

Version 0.10.0 is exercised on macOS with CPython 3.12.13, 3.13.13 and 3.14.5. Runtime dependencies are Python standard-library modules. Source requires Python 3.11+ and POSIX flock/process-group behavior; Linux and Python 3.11 remain unqualified; testing three local interpreters does not qualify the full platform range. Native Windows is unsupported.

## Experimental Windows onboarding

An [agent-assisted WSL 2 setup guide](windows-wsl.md) is available as an experimental route. It is not a completed Windows/Linux qualification. Native Windows Python (including under Git Bash) cannot provide the runtime’s POSIX file locking/process controls. Keep project/tools and agent execution inside the chosen WSL environment, preserve existing data and obtain approval for system changes. The guide covers administrator/restart/login handoffs and returning to the project; setup and basic health checks alone do not qualify concurrency or recovery. Do not claim equivalent WSL integration for every harness.

## Harness integration

The installer copies standard SKILL.md directories into project `.agents/skills/` and a standalone local Python snapshot. Start a fresh host session for skill discovery. Another host may require a different discovery adapter; portable text and a CLI do not establish universal harness compatibility.

Role files are briefing contracts for the host's actual agents. They do not register native specialist types or provide an independent model runtime. If delegation/review is unavailable, work stays review-pending. Host permissions and user authorization outrank workflow instructions.

The optional hook command only prints selected workspace status. No host hooks/global settings are installed automatically, and it does not implement a native event protocol. Native UI discovery, automatic selection quality and other harnesses have not been qualified in this release.

## Bounded Codex CLI observation

A fresh local Codex CLI 0.167.0 process on macOS completed an explicit `$tequio-status` request in an ephemeral read-only session. It executed the installed project's `bin/tequio --workspace <workspace> status` successfully. The process reported that `tequio-status` was already present in its startup available-skills list at `.agents/skills/tequio-status/SKILL.md`; that discovery detail is model-reported, rather than an independently captured startup-list dump. This qualifies one explicit namespaced CLI invocation, not native graphical UI discovery or automatic selection quality.

The pilot used `codex exec --skip-git-repo-check --ephemeral --sandbox read-only --ignore-user-config --color never -C <installed-project> -`, supplying the bounded request on stdin with a 100-second timeout. It exited 0 in 13.06 seconds. Authentication used the existing local account; no global configuration or account changes were made. Ordinary evidence checks do not contact a model provider.

Delegation controls were reported by that fresh process but were not exercised in the pilot. Session recovery was not exercised: ephemeral mode deliberately leaves no resumable session. That pilot alone does not establish fresh CLI delegation or recovery. The separate bounded four-stage observation below supplies additional evidence. Other Codex versions, UI discovery, automatic skill selection, general host-agent crash recovery and other harnesses remain unqualified. No native specialist type registration is implied.

## Bounded four-stage and continuation observation

A separate fresh installed, non-Git project was exercised with Codex CLI 0.167.0 on macOS. Actual tool traces show project-local explore/design/tasks skill reads, current phase receipts, a detailed ready task and checkpoint. A resumed recorded session read build but stopped at read-only access, preserving unclaimed work. An explicitly writable resume of that specific session used supported replan to replace a malformed supplemental check, implemented the bounded existing-project correction/docs, passed three regression tests plus supplemental assertions, spawned a genuine independent reviewer, saved/registered accepted review and completed the replacement task. Native persisted function-call and tool-response provenance were inspected rather than relying only on a final model assertion.

Observed process durations were 106.91s preparation, 65.11s blocked resume, and 137.53s successful writable resume. Per-invocation sandbox configuration mattered; do not assume resume preserves the intended write policy. Current official [non-interactive guidance](https://learn.chatgpt.com/docs/non-interactive-mode) describes explicit session resume; local CLI help and actual version were checked. No global account/config changes or globally installed Tequio skills were needed. Existing account authentication and generic host capabilities were available, so this is not a clean-machine or automatic-discovery qualification. Raw traces, session IDs and private reports are not distributed.

A separate actual host-agent exercise used two independent Git writing lanes, genuine review and serial host merges, then a deliberate checkpoint/release and a different no-history agent continuation for a dependent task. Its 25-test application and honest prebuilt [replay](../examples/integrated-build/README.md) are included. Neither observation proves crash recovery, unrestricted unattended scheduling, overnight product completion, universal harness support or comparative productivity.

Pilot command examples use generic workspace placeholders; machine-local names and identifiers are omitted from the public package. Installed version metadata follows the executing installer release and payload integrity is checked separately by hashes.

## Local interruption qualification

The 0.5.0 recovery tests use disposable local verifier processes on macOS, including SIGKILL of a controller while its child group survives. Independent separate-CLI probes confirmed that lease expiry/stopped acknowledgement cannot bypass a held lock or observed group; recovery works after inspected group absence. Other cases cover unknown launch state, invalid-caller evidence preservation and metadata/database failure ordering. This qualifies the bounded local POSIX controller guard, not arbitrary model-host, remote/detached-agent or distributed recovery. PID reuse/zombies and an unobserved spawn/persistence interval can conservatively require manual inspection. No automatic process kill or successful overnight product completion is promised.

Run-context tests include read-only CLI resume after malformed/nonobject/missing-field/unknown-version checkpoint data, legacy context and policy/scope/progress drift. Git health tests include changed/detached branches, foreign/missing checkouts and worktree-specific operation metadata. Additional [contracts](check-recovery.md), [context](run-context.md) and [Git observations](lane-health.md) define the exact boundary.

## Journal interruption boundaries

Disposable Git fixtures exercise exact commit planning, branch movement, nested projects and rename/out-of-scope refusal, clean/dirty/conflicted/rewritten/detached states, duplicate/concurrent requests, rollback, malformed/orphan journal data, owner reconfirmation and evidence publication ordering. A separate synthetic project performed a native merge, then a fresh no-history agent read persisted state and identified the exact commit as integrated but unrecorded. It reconciled without repeating the merge; actual checks/docs, a delivered independent review and guarded completion then produced accepted state.

This tests preserved integration boundaries and fresh-session interpretation, not arbitrary host crash/power-loss durability or automatic merge recovery. The primary SQLite transaction binds journal facts, while Git may change externally between observations. No semantic equivalence for cherry-picks/rebase/squashes, authenticated actors, automatic Git mutations or universal repository configurations are promised. [Contract and limits](integration-journal.md).


## On-demand installation health

`doctor [--source PATH]` preserves task/intake/git observations and adds version1 `installation_health` even without a workspace. Its execution, installation, owned and source_comparison objects distinguish executing layout/version, recorded snapshot metadata, owned byte/mode drift and an explicitly selected source. An intact older snapshot can coexist with live source; equal versions do not imply equal payload. Exit0 means observations were delivered, not pristine assets or permission to upgrade.

Ordinary Status/hook/resume never scan owned assets. Doctor never repairs, fetches, imports selected source, creates a workspace or changes launcher/ignore/metadata. Unsafe manifest paths yield null-path diagnostics and are not read/echoed; only installer namespaces/known workflow discovery assets are eligible. Manifests are capped at4MiB, paths10000 and asset bytes256MiB per observation; limit exhaustion is incomplete, not intact. Issues/differences cap10 with total/omitted counts. Missing, invalid and unavailable states stay distinct. Source comparison captures and validates bounded bytes before pure prefix rendering and parses the version constant with AST. It is sequential local evidence, not atomic/authenticated ownership or public-safe metadata. Existing collision/modified-owned/refusal/removal protections remain unchanged; real snapshot refresh is a separate action.

## 0.13.0 scoped revision qualification

Version 0.13.0 is exercised locally on macOS/CPython3.14.5; historical multi-version results do not qualify these additions. It adds standard-library SQLite revision state and no service/runtime dependency. Workspaces with no overlays retain their existing fingerprint structure and broad-replan behavior. Revision requires an explicitly upgraded controller and versioned capability support; old unmodified0.12 runtimes cannot enforce a future marker. Opening an overlay workspace with an older controller/downgrading it is unsupported. Preserve backups and historical receipts; do not edit database bodies or installed historical controllers.

Scoped policy separation is explicit authoring and reviewed successor migration, not an automatic migration for legacy declarations. Existing global/mixed producers stay conservative. Source launcher execution and installed skill/runtime snapshots remain distinct; `doctor --source PATH` observes them without repair. Source-checkout snapshots need a separately authorized refresh and fresh host session for skill discovery. Collision/modified-owned refusals, private ignore protections and tracked-history limitations remain; no target installation or public export is performed by qualification. See [policy boundaries](policy-boundaries.md).
