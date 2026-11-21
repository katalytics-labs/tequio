# Optional Git isolation

Shared-folder coordination is the default, including in Git repositories. It uses task dependencies, declared read/write ownership, claims, evidence and independent review, without physical file isolation. Git hosting is irrelevant: an existing local repository or linked worktree is sufficient. Detection does not initialize a repository or write configuration.

Git isolation is an explicit project-local opt-in. Before enabling it, supply an ignore rule covering the project's `.tequio/` directory and ensure that directory has no tracked files. Tequio does not edit ignore rules or Git configuration. These private configuration and controller-pointer files must not be symlinks. Keep `.tequio/` private and excluded from publication.

```sh
python3 bin/tequio --project /path/to/project git status
python3 bin/tequio --project /path/to/project git configure worktrees
python3 bin/tequio --project /path/to/project git lane implementation
python3 bin/tequio --project /path/to/project git status
python3 bin/tequio --project /path/to/project git configure shared
```

Check `tequio git --help` for the installed CLI syntax. The Python API in `tequio.git_isolation` provides `detect(project)`, `configure(project, enabled)`, `create_lane(project, lane, base='HEAD')`, and `inspect_lanes(project)`. Results are dictionaries; refusals raise `GitIsolationError`, a `ValueError`. `control_root` identifies the original authoritative project.

A lane creates branch `tequio/<lane>` and a sibling checkout named `<repository>-tequio-<lane>`. A project below the repository root retains its relative subdirectory in the new checkout. Lane names contain 1–64 letters, digits, underscores or hyphens, starting with a letter or digit. The base must resolve to an existing commit. Creation requires a clean original worktree, including untracked files, and refuses existing targets, branches or registry entries. Existing ignored files are not copied into the new checkout. If configuration was enabled only via a local exclude rule, the lane must also inherit a rule covering its private metadata; committed `.gitignore` rules are the simplest consistent approach.

The original project's `.tequio/git-isolation.json` is the central lane registry. A lane's `.tequio/git-isolation-origin.json` points back to it. The controller, task claims, evidence and final integration remain authoritative at the original project. Run task lifecycle commands with `--project` pointing there. Worktree creation does not establish automatic task synchronization, transfer evidence or provide automatic integration. Independent writing lanes can use their checkouts, reviewers can inspect them, and one owner must integrate the changes into the original checkout and verify the integrated result there.

Configuration and creation serialize through an exclusive local lock. Contention fails immediately. A crashed process may leave `.tequio/git-isolation.lock`; inspect the process and repository before manually removing a stale lock. The registry uses atomic replacement. Git separately locks its refs. External Git processes are outside Tequio's lock, and detection/inspection are read-only snapshots rather than concurrency guarantees.

On partial failure, Tequio preserves the branch and checkout and reports both for inspection. It does not delete either as rollback, so a failed call may leave unregistered work. Inspect `git worktree list`, the reported checkout and branch, and the original registry before deciding how to recover. A pointer whose registry entry was never saved is refused rather than treated as another controller. Recovery and integration are manual in this version.

Disabling isolation changes future lane creation only; it preserves registered lanes and their work. This feature does not initialize repositories, commit, merge, push, publish, reset, remove worktrees, delete branches or modify global Git configuration. Git subprocesses have a 30-second timeout and do not inherit `GIT_*` environment overrides. Tests use disposable repositories only.

Autonomous overnight orchestration, worker commits, merge ownership enforcement and automatic integration are separate policy and implementation work. This helper does not implement those behaviors.

## Who commits and merges?

The host orchestrator owns integration. Under an explicitly agreed backlog run policy, writers may commit their task-owned files on lane branches, while the orchestrator reviews those commits and merges them serially into the designated integration branch. It then checks the combined result, refreshes authoritative evidence and review, closes completed tasks and selects more ready work. Native Git performs those operations; the lane helper only manages optional checkout creation. See the execution-mode procedure in `skills/tequio-build/SKILL.md` and the `templates/run-policy.json` starting template.

The default is one chunk with no automatic commit/merge permission. A user can authorize a bounded autonomous run once, including local commits and merges, so routine integration does not require repeated confirmation. Pushes and publication are separate. Missing identity, unresolved conflicts, failed checks, missing independent review or session limits produce a preserved checkpoint/blocker. No overnight-completion or multi-session scheduling guarantee is implied.

Installed launchers and private runtime files are not copied into a lane. Invoke the original launcher using its absolute path. For read-only status or Git inspection the lane may be supplied as `--project`; lifecycle mutation commands require `--project` to point to the original control root. Status from a lane reads that original controller. Do not install a second controller into the lane.

Status now also provides [actual lane health snapshots](lane-health.md): expected registry values remain intact alongside actual root/common directory/branch/HEAD, dirty/index/conflict and ongoing-operation state. A healthy observation is not accepted task evidence or permission to integrate.
