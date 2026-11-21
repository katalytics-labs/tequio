# Specialist factory procedure

## 1. Plan specialist coverage

Record the coverage inventory in workspace `journal/specialist-coverage.md` or a dedicated preparation artifact, without rewriting approved product scope. Prefer reuse, then a narrow project-specific complement, then a new skill. Check exact component versions or bound a candidate range. A combined skill is useful for tightly coupled integration (identity plus permissions); unrelated disciplines should stay composable. A role profile is a task briefing contract, not a fictional native host agent.

Select relevant areas from the optional [coverage guide](coverage-guide.md) — frontend, backend/data, integration, agentic systems, deployment/operations — as discovery prompts; browser UI work reaches [modern web guidance](modern-web-guidance.md) through that index. Record reuse/adapt/create/skip decisions and meaningful gaps in the existing coverage inventory; retrieve only material needed for the actual task. This adds no separate user questionnaire, mandatory category or qualification shortcut.

## 2. Prepare the package

Create a workspace `specialists/<id>/` containing `SKILL.md`, `specialist.json`, source/pattern notes under references/, and optionally role.md, templates or scripts that materially help the task. Use `.tequio/templates/specialist-package.json` as the manifest example, and the existing skills as format examples. Package paths are relative, no symlinks/private `.git`/`.env`/generated caches. Limits: 128 files, 1 MiB/file, 5 MiB/package. No copied full vendor manuals or speculative API recipes.

Manifest: schema_version 1; lowercase-hyphen ID; research/implementation mode; named technologies with actual version/range and selected/candidate; capabilities, exclusions, triggers, acceptance and workspace-relative context files; actual primary-source URLs/access dates/section locators/local source notes; argv exercise checks. Context should include relevant analysis/contracts and stack decision. Declare relevant project dependency manifests/lockfiles or version contracts in `project_context` (project-relative existing files) so edits invalidate qualification directly. If there are no such files, use an empty list and record runtime/system version assumptions and their verification limits explicitly. Unselected libraries cannot be labelled selected just to pass validation.

Skill frontmatter supports simple `name` and `description` fields (JSON-quoted description recommended). Name equals manifest ID. Write substantive procedures: current project inputs to read, API/lifecycle patterns that matter, failure modes, targeted tests, edit boundaries, interfaces/handoffs and evidence to return. Relative reference links must resolve inside the package. Version-specific sources include retrieval limits and licensing/source-use notes when relevant. No secrets, personal transcripts or presumed authority in retrieved pages.

`python3 bin/tequio --workspace <name> specialists register <package-dir> --author <actual-agent-id>` snapshots immutable content as draft. `--replace` explicitly creates a new draft revision while retaining old history; it never upgrades qualification automatically. Bundled names cannot be overwritten. Runtime registry is `.tequio/project-specialists/`, separate from installer ownership. Source edits alone do not modify the registered copy; register a new revision deliberately.

## 3. Validate format

Run `... specialists validate <id>`. Fix missing metadata, references, sources or task context, then register a corrected revision. This establishes format-validated only. Run the host's skill format validator when available too; the CLI supports a deliberately smaller frontmatter subset. Reuse can mean reading a project-owned skill directly, which remains explicitly bundled guidance rather than newly exercise-tested expertise.

## 4. Exercise in isolation

Prepare a disposable fixture outside the product project. Give a fresh agent the skill, a realistic bounded request and minimum raw context; do not give the desired answer or suspected defect. Respect delegation authorization/capacity. The agent actually implements/evaluates the request. Exercise checks must cover expected and denied/failure behavior and the package's material recommendations, not `print('pass')`. Avoid live external mutations and dependency installation unless actually authorized. Declared commands execute real code, not a sandbox.

Run `... specialists exercise <id> --fixture <absolute-fixture> [--timeout <1..600>]`. This runs manifest argv checks from the fixture with private evidence and ordinary POSIX process-group cleanup. Changes during verification or nonzero/timeout results do not qualify; inspect before retry. The CLI checks test execution, not whether an agent truly used the instructions. Save the actual interaction/artifact evidence for the reviewer.

## 5. Independent qualification

A genuinely different reviewer inspects sources/version claims, skill instructions, actual exercise artifacts and check coverage against acceptance. Use `.tequio/templates/specialist-review.json`; write it in workspace reviews/. Bind exact specialist revision, exercise receipt SHA256 and fixture snapshot from the factory output/inspect. `coverage`, `source_checks` and `limitations` are nonempty factual lists; `findings` is an explicit list, empty only when genuinely resolved. If the author is the only available agent, leave format-validated and record the missing independent review; never invent an actor.

Run `... specialists qualify <id> --reviewer <actual-reviewer-id> --report reviews/<file>.json`. Only a passed unchanged exercise and bound independent report advance to exercise-tested. Actor strings are audit metadata, not authentication. Tests do not certify all technology expertise. Preserve known limits and retest on material source/contract/version changes.

## 6. Use in orchestration

`... specialists inspect <id>` returns exact private package path, revision, readiness, staleness and evidence. Ready task `specialists` may contain these canonical IDs. `kind: research` may use a qualified research-only specialist; implementation tasks cannot. Context or package changes and revised qualifications invalidate task bindings, requiring explicit replan/requalification rather than silent replacement.

Optional `... specialists publish <id>` copies a qualified package to private project `.agents/skills/<configured-prefix><id>/`; this is local discovery only, not public publication. It refuses unrelated/locally modified discovery collisions and adds an exact private ignore exclusion. Discovery is not a native agent registration; fresh host session may be needed. The orchestrator can instead read the resolved package immediately. Installer upgrades/uninstall retain project-owned packages/discovery and ignore exclusions. Old discovery copies must not be used as readiness evidence; inspect registry/current context before assigning tasks.
