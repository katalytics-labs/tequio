# Windows setup with an agent: experimental WSL 2 route

**Native Windows is unsupported. WSL 2 is an experimental option, not yet qualified with Tequio on Windows.** This guide is a setup proposal based on official Windows/agent documentation, not a tested compatibility claim. A successful install/health report is only a first observation; process cleanup, concurrency, recovery and the agent’s real workflow still need qualification on that machine.

Tequio’s CLI uses POSIX file locking and process-group controls. Git Bash plus Windows Python does not supply those mechanisms. Do not ask an agent to port Tequio, install a package named `fcntl`, skip cleanup checks or broadly disable its permission controls during setup.

WSL runs a Linux environment on Windows. Plan to keep **the project, Python, Tequio and the agent’s terminal execution inside the same WSL environment**. Claude Code supports an installation inside WSL, independently of an existing native Windows install. For Codex or Antigravity, verify the actual version’s Linux/WSL or remote-environment instructions and tool execution; this guide does not claim equivalent integration. If your agent cannot operate there, stop with a precise limitation. [Claude Code setup](https://code.claude.com/docs/en/setup).

## Ask your agent to help

Paste into your current agent on Windows:

```text
Help me prepare an experimental WSL 2 environment for Tequio. Read Tequio's
README, docs/windows-wsl.md and current official WSL/agent setup instructions.
First inspect Windows/WSL status and my existing agent setup without changing
anything. Explain what is already available and what is missing in plain words.
Native Windows Tequio is unsupported; don't port it or skip its safeguards.

Before system changes, explain the proposed distribution/installations and ask
for my approval. Preserve existing distributions, projects, credentials, global
agent configuration and unsaved work. Don't reset/unregister WSL or move/copy my
existing project without asking. Use an existing suitable environment if present.

Walk me through any administrator approval, restart, Linux username/password
creation or agent sign-in that only I can complete. Never ask me to paste a
password or authentication token into chat. Don't restart the computer yourself.
Before a restart, give me a short continuation message and the exact next app
or terminal to open. Save a continuation file only at a private path I approve.

After setup, verify the agent's actual Linux command execution, Python 3.11+,
required POSIX features and the chosen project path inside WSL before invoking
Tequio. Explain which environment and folder are active. Install Tequio only into
that selected project after following its installation guide. Inspect health;
report gaps honestly. No product implementation, commits, publication or blanket
permission bypasses. Give me a short 'how to reopen this tomorrow' instruction
using the exact distribution, agent launch route and project path that worked.
Do not describe this experimental path as fully qualified Windows support.
```

The agent’s ability to inspect or install depends on its permissions and version. A chat-only agent can guide you but cannot configure the computer. An installation may need more than one session; the continuation handoff is part of the setup.

## What you may need to do yourself

Microsoft’s current streamlined instructions cover Windows 11 or Windows 10 version 2004/build 19041 and later. They use an administrator PowerShell window and can require a restart. Existing WSL installations need inspection before choosing a command; an older Windows version or virtualization/policy restriction can require another documented path. [Microsoft WSL install guide](https://learn.microsoft.com/en-us/windows/wsl/install).

For a suitable machine with no WSL installed, the documented starting command is:

```powershell
wsl --install
```

**This changes Windows and installs a Linux distribution. Run it only after reviewing/approving that setup.** Complete any administrator prompt and choose when to restart after saving work. Afterward, open the installed distribution, commonly **Ubuntu**, and create its requested Linux username/password yourself. This login is separate from your Windows login and agent account. The agent should explain what each screen needs without collecting credentials.

To inspect installed distributions from PowerShell:

```powershell
wsl --list --verbose
```

Do not unregister, delete, convert or replace a distribution merely because an installation command fails. Give your agent the non-sensitive error and ask for the official troubleshooting route. Any additional system/virtualization change needs an explanation and your approval.

## Work inside the Linux environment

Once the selected WSL 2 distribution is available, install/launch your agent there using its current official instructions and complete authentication yourself when required. Having Claude Code on Windows does not demonstrate that its Linux installation or account session is ready.

Keep a new practice project under the Linux home directory, for example `/home/your-linux-name/projects/my-project`. Microsoft recommends keeping Linux-command-line projects in the Linux filesystem rather than under `/mnt/c/...` for cross-filesystem performance. This is not permission to move an existing project; decide that separately. [WSL filesystem guidance](https://learn.microsoft.com/en-us/windows/wsl/filesystems).

Inside the selected Linux terminal, check:

```sh
pwd
python3 --version
python3 -c "import fcntl, os; print('file-lock module available; process-group API:', hasattr(os, 'killpg'))"
```

These are prerequisite observations, not process-cleanup/locking qualification. Confirm the Python version is 3.11+ and that the agent executes the Linux Python, not `python.exe` from Windows. If a requirement is absent, have the agent propose the relevant official installation step and obtain permission before changing the environment.

Then use the [normal Tequio installation guide](getting-started.md#install-manually) from that same Linux environment, with the selected Linux project path. Check installation health before claiming setup succeeded. Start with a disposable practice project before trusting important work; retain errors and evidence rather than patching tests to get green output.

## Coming back tomorrow

Your agent should finish setup with instructions specific to what it actually verified. For an Ubuntu-based terminal setup, the shape is:

1. Open **Ubuntu** from the Windows Start menu, or enter `wsl --distribution Ubuntu` in PowerShell if that is the actual configured distribution.
2. In its Linux terminal, `cd` to the exact project folder recorded during setup.
3. Launch your agent using the Linux command it actually installed and verified, then sign in if requested. If using an editor/remote integration, use the verified WSL-open procedure instead.
4. Ask: “Use Tequio Status in workspace main. Tell me what works, what remains and the next action. If needed, read `.tequio/skills/tequio-status/SKILL.md`.”

A Windows-native agent window opened in another folder is not automatically the same execution environment. If you are unsure, ask the agent to inspect the environment/path first rather than create another project copy or resume work blindly.

## Evidence boundary

Official source pages above were inspected on 2026-11-21; installation details can change and agents should recheck them when used. We have not completed a Windows/WSL Tequio qualification or a cold setup trial with Claude Code, Codex or Antigravity there. Published support should remain experimental until actual installation, discovery, independent review, interrupted-check recovery and normal task lifecycle have been exercised with honest results. Nothing in this document authorizes changing a user's machine without their approval.
