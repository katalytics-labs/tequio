# Specialist factory

Invoke `$tequio-specialists` after stack analysis/planning, or use it to prepare research-only guidance while comparing candidates. It inventories existing expertise, researches primary sources, authors focused packages and qualifies them through actual exercise and independent review. It does not select a stack, install libraries or confer expertise from a component name.

## Optional coverage areas

The factory ships an optional [coverage guide](../skills/tequio-specialists/references/coverage-guide.md) with five overlapping discovery areas — frontend, backend/data, API/messaging/integration, agentic systems and deployment/operations — plus focused references for the latter four. Browser work reuses the preserved [modern web reference](../skills/tequio-specialists/references/modern-web-guidance.md); native/platform UX needs the selected platform's own sources. The areas are prompts for selecting relevant primary sources and shaping exercise criteria, recorded as reuse/adapt/create/skip in the existing coverage inventory. They are not generic role profiles, registry categories, per-area agent quotas or a universal specialist; concrete stack expertise remains project-owned and qualifies through the normal register → validate → exercise → independent review lifecycle. Shared source-provenance, licensing, execution and privacy boundaries apply to every area; nothing here enforces agent behavior or authorizes retrieval, installation or deployment.

## Materialization

- Workflow skill: skills/tequio-specialists/SKILL.md and its procedure reference.
- Package: SKILL.md, specialist.json and supporting references/optional role/scripts/templates.
- Manifest and review examples: templates/specialist-package.json and specialist-review.json.
- Private project-owned registry and immutable revisions: `.tequio/project-specialists/`.
- Optional discovery copy: `.agents/skills/<configured-prefix><id>/`; never a global installation or native agent registration.
- Task integration: canonical IDs bind exact package revision, files and qualification. The orchestrator reads the returned package path and briefs an actual available agent.

## CLI

All commands use `python3 bin/tequio --project <root> --workspace <name> specialists ...`.

| Command | Meaning |
|---|---|
| `list` / `inspect <id>` | Inspect current readiness, staleness, revision, package and evidence. |
| `register <package> --author <actual-id>` | Snapshot a valid structured package as draft. `--replace` explicitly creates a new draft revision, retaining prior history. |
| `validate <id>` | Check format, source declarations, references and current project context. Not factual verification. |
| `exercise <id> --fixture <separate-dir>` | Execute declared checks against bounded isolated material; save output and full material capture privately. |
| `qualify <id> --reviewer <actual-id> --report reviews/<file>.json` | Promote only with successful bound evidence and delivered independent review without findings. |
| `publish <id>` | Activate a qualified skill for private local discovery only. Respect prefixes; refuse collisions/modified copies. No public upload. |

## Readiness and freshness

Draft → format-validated → exercise-tested. Exercise success alone does not advance the final state. Failed checks, missing evidence, changed package/context, unreviewed source assumptions or unresolved findings are not clean qualification. Actor IDs are declared audit identities, not cryptographic authentication; real independent work must supply the report. Framework workflow skills are not stack specialists; task specialist IDs resolve only to qualified project packages.

Candidate technologies can only generate research-mode specialists. Implementation packages require selected technologies. Ready tasks require exercise-tested generated specialists; `kind: research` may use research-mode, implementation may not. Draft tasks can record missing/unqualified future skill IDs without executing them. Declared project dependency manifests/lockfiles (`project_context`), package/context/review changes invalidate bound tasks instead of silently substituting instructions. Replan/requalify explicitly.

Qualification is historical evidence of a bounded exercise. Original OS temp fixture edits/deletion do not rewrite the observed result: the actual tested material is retained under private evidence with full content/mode fingerprint, including local dependency/runtime files. Tampering/deleting the retained capture or receipt invalidates use. External interpreter/system dependencies are version assumptions documented by the author/reviewer, not fully captured or continuously monitored runtime guarantees.

## Bounds and privacy

Packages: 128 files, 1 MiB/file, 5 MiB total; no symlinks, `.git`, `.env` or bytecode caches. Exercise material: separate from project and ancestors, at most 512 files/20 MiB before and after commands, no symlinks or `.env`. Full capture is deliberate; authors must ensure no private credentials/customer data. Do not use a full dependency tree when it exceeds the bound; design a smaller representative fixture with explicit environment/version assumptions.

Checks run actual local argv commands (1–600 seconds each), with ordinary POSIX group cleanup; they are not sandboxed. Generated bytecode is disabled for exercise stability. Check coverage, source authority, safe command choice and semantic quality remain author/reviewer responsibilities. Fake or trivial tests cannot establish competence merely by producing green receipts.

Generated packages/discovery are not installer-owned: toolkit upgrade/removal preserves them and private exclusions. Changing a discovery prefix moves only a previously owned unchanged copy. Edited copies require deliberate reconciliation. Registration does not auto-activate a skill; old discovery copies are not authority for current readiness. A new host session may be needed for discovery; an existing orchestrator can explicitly read the resolved private path immediately.

## Maintenance

Revisit packages when versions/contracts change, source assumptions age, exercises expose missing behavior or actual tasks reveal a useful gap. Prefer updating a narrow skill/reference over adding another persona or global rule. Preserve exercised evidence and limits. Project-owned generated packages are not silently promoted into Tequio's reusable bundled catalog; that is a separate deliberate maintenance choice.
