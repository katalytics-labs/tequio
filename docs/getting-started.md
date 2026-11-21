# Getting started with Tequio

You can ask your coding agent to do the setup or run the commands yourself. Keep two folders distinct: **Tequio’s source copy** supplies the installer; **your project** is where you build your software and use the installed skills.

## Check your environment first

- Python 3.11+ is required; current 0.18.0 qualification uses macOS with Python 3.14.5. The runtime needs POSIX file locks and process-group controls.
- macOS is tested. Linux is not yet qualified. Native Windows is unsupported; the [WSL 2 guide](windows-wsl.md) describes an experimental route with explicit setup handoffs.
- Your agent needs permission to read/write the selected project and execute its approved checks. Model accounts, subscriptions and command permissions belong to your agent, not Tequio.
- The runtime uses the Python standard library. Additional tools may be needed by your own project’s checks; Tequio does not authorize their installation automatically.

Read the [compatibility evidence](compatibility.md) before treating a specific host setup as supported. In particular, `.agents/skills/` discovery varies by harness. You can ask an agent to read `.tequio/skills/<skill>/SKILL.md` directly if it can access local files but does not discover a command.

## Ask your agent to install

Use the copyable [setup prompt in the README](../README.md#ask-your-agent). Open your intended project first. The prompt asks the agent to inspect requirements, preserve existing files, install into that project, check health and explain how to return later. It does not start product implementation.

On Windows, the general prompt should lead to the [experimental WSL setup prompt](windows-wsl.md#ask-your-agent-to-help). An agent cannot guarantee it can elevate privileges, restart Windows, complete a browser login or automatically reopen itself in Linux. Those are explicit handoffs, not failed Tequio tasks.

## Install manually

Run from a macOS terminal, or a Linux/WSL shell after accepting its current qualification limits:

```sh
git clone https://github.com/katalytics-labs/tequio.git
cd tequio
python3 --version
python3 bin/tequio install "/absolute/path/to/your-project"
```

Replace the quoted path with a real **existing** project folder. Python’s version check must report 3.11 or later. If Python is missing, ask the agent for the official installation route for your environment; do not work around it by installing a package named `fcntl` or rewriting Tequio during setup.

If you downloaded a ZIP, extract it and use the extracted directory instead of the `git clone` step. Preserve the complete source layout. Then switch to your project:

```sh
cd "/absolute/path/to/your-project"
python3 bin/tequio doctor --installation-only
```

Expected for an unmodified ordinary installation: installation is present, owned assets are intact, and execution uses the installed runtime. Exact counts depend on release/prefix; don’t use a hardcoded count as a success test. `doctor` reports observations even when assets are missing or modified, so inspect the health object and any gaps. Do not assume exit0 alone means success. An optional explicit `--source "/absolute/path/to/tequio"` compares the installed snapshot against a selected complete source copy; it does not fetch or repair it.

Start a **fresh agent session in your project** for skill discovery. Ask it to read `.tequio/skills/tequio-status/SKILL.md` if the skill is not visible. No global hook, native subagent registration or host-specific settings are installed.

## Choose a starting point

Use either README prompt: [an idea](../README.md#i-have-an-idea) or [an existing brief/project](../README.md#i-already-have-a-brief-or-project). Briefing asks enough discovery questions to shape intent, then Explore owns research and important unknowns. You don’t need to bring a polished specification.

After Explore, ask for Tequio Design, then Tasks, then Build. A task is a bounded outcome with declared checks and acceptance; Tasks obtains independent design reviews before import. Build performs the work and obtains current checks/docs and applicable independent implementation review. Missing actual review stays pending. Your agent’s ability to delegate depends on its host.

For an existing workspace, name it in your requests. If none is selected, the default is `main`; Tequio does not guess by the most recently modified folder. A normal status request does not claim a task, recover a worker or start a new phase.

## Try one small change

This practice uses a supplied Python task-list helper with a real archive-filter defect. It keeps the exercise in a new folder rather than changing your application. You need no application-service account; a live agent still uses its normal provider/account and may incur usage.

From your **Tequio source copy**, choose a new path that does not exist. This example uses a folder in your home directory; change the name if it is already present:

```sh
mkdir "$HOME/tequio-first-task"
cp examples/existing-project/task_list.py "$HOME/tequio-first-task/"
cp examples/existing-project/test_task_list.py "$HOME/tequio-first-task/"
cp examples/existing-project/usage.md "$HOME/tequio-first-task/"
cp examples/existing-project/brief.md "$HOME/tequio-first-task/"
python3 bin/tequio install "$HOME/tequio-first-task"
cd "$HOME/tequio-first-task"
python3 -m unittest discover -s . -p 'test_task_list.py' -v
```

Run the commands individually. **If `mkdir` reports that the folder exists, stop and choose a new name before any `cp` command.** The initial tests intentionally fail two archive-filter cases. Keep that evidence; it is the defect you’re asking the agent to investigate. Don’t run the deterministic demo as a substitute for the live exercise.

Open a fresh agent session **in `tequio-first-task`** and paste:

```text
Use Tequio Explore for this small existing-project correction in workspace main.
Read brief.md, task_list.py, test_task_list.py and usage.md. Reproduce the archive
filter defect and explain the intended behavior and a focused next step. Keep
scope to this bug, nearby checks and the usage contract. Do not implement yet.
If needed, read .tequio/skills/tequio-explore/SKILL.md directly.
```

Then, when ready, send these as separate requests:

```text
Use Tequio Design for this bounded correction in workspace main.
```

```text
Use Tequio Tasks for the reviewed plan in workspace main. Arrange actual separate
correctness and red-team design reviews; retain a precise review gap if the host
cannot supply them.
```

```text
Use Tequio Build for the ready task in workspace main. Preserve the declared
scope, run the checks, reconcile documentation and obtain actual independent
implementation review before closing. Do not commit or publish anything.
```

The supplied four tests should pass after a correct fix, but that alone does not establish task completion. Ask:

```text
Use Tequio Status in workspace main. What behavior is delivered, which checks
and reviews are evidenced, and what remains? Read the installed Status skill
if needed. Do not start or recover work during this status request.
```

The expected report distinguishes accepted work from checks-only or review-pending work. It should not invent reviewers to finish the exercise. A host without delegation can still inspect the files and show the gap; do not call it a fully accepted Tequio task until genuine review exists.

For a model-free demonstration instead, run `python3 examples/quickstart/run_demo.py` from the source copy. It executes pre-authored mechanics and deliberately stops review-pending; it does not test a model’s reasoning. [Details](../examples/quickstart/README.md).

## What was installed and what stays private

- `bin/tequio`: local launcher for the snapshot runtime.
- `.agents/skills/`: project-local workflow skill discovery directories, with an optional chosen prefix.
- `.tequio/`: runtime/reference snapshot, manifest and private workspace/evidence state; generated specialists are project-owned separately from installer assets.
- `.gitignore`: a marked block protecting private installed/state paths.

The installer preserves unrelated existing files and project instructions. It refuses collisions and changed installer-owned assets. An ignore rule does not remove tracked files or history. Inspect what you commit; do not publish task databases, reports, prompts, tokens, captures or credentials.

Tequio has no hosted model service of its own. The agent can send content to its provider according to its settings; review those settings for confidential work. Project-local storage is not a promise of offline/private model processing.

## Update or uninstall

Keep a complete source copy available to perform these operations. If you used Git and have no source edits to preserve, update that copy with `git pull --ff-only` after reviewing the release; ZIP users download/extract a new complete copy. Neither action upgrades your projects automatically.

Before upgrading a project, inspect real active task/check handles and reconcile a safe pause/checkpoint; use a consistent private backup of the project/state as appropriate. Version-sensitive recovery overlays must not be downgraded to an older runtime. Preserve modified owned files rather than forcing an installer refusal away.

From the selected **source copy**, update one project:

```sh
python3 bin/tequio install "/absolute/path/to/your-project"
```

From the **project** afterward:

```sh
python3 bin/tequio doctor --installation-only
```

Inspect health, then open a fresh agent session in the project. Your generated specialist packages and task history are not automatically rewritten/requalified by an installer refresh.

To remove installer-owned assets, run this alternative action from the source copy:

```sh
python3 bin/tequio uninstall "/absolute/path/to/your-project"
```

Modified owned files cause a refusal. Workspace evidence, unrelated files, project-owned specialists and private ignore protections remain. Uninstall is not “erase every private record”; keep or delete your own retained data deliberately. Do not delete the whole `.agents/` directory, since other tools may use it.

## If setup stops

Ask the agent to name the exact missing requirement or conflict and one next action in plain language. Keep the existing state intact. Don’t bypass ownership, reset task history, turn a stale check into a PASS or install dependencies just to silence a refusal. [Operator guide](operator-guide.md) · [Evidence recovery](prerequisite-recovery.md) · [Compatibility](compatibility.md).
