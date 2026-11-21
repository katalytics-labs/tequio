# Quickstart example

From the Tequio folder:

```sh
python3 examples/quickstart/run_demo.py
```

This creates an isolated temporary project, installs the local snapshot, records pre-authored brief/analysis/plan, imports and claims a bounded task, copies the example helper, executes four actual success/error tests and records documentation reconciliation. It checks that completion refuses missing documentation and missing independent review, then leaves the task review-pending and checkpoints. The temporary project is cleaned up at exit.

To inspect files afterward, retain a new directory:

```sh
python3 examples/quickstart/run_demo.py --output /absolute/path/to/new-demo-project
```

An existing path is refused. No model API, network, dependency installation, global configuration or Git operation is used. This is a deterministic lifecycle smoke demonstration with pre-authored example material; it is not evidence that an AI generated the code or that an independent reviewer ran. The demo deliberately does not fabricate another actor to get a green completion record.

For an agent-led trial, use the retained project in your coding harness and ask a genuinely separate reviewer to inspect the task, actual helper/tests and docs. Its correct next action is `$tequio-inspect`; only register a real delivered report and close after acceptance. Or install Tequio into a fresh project, supply brief.md and walk through the four everyday skills yourself. Native host discovery/delegation remains harness-specific.

Each task includes an explicit security assessment. This isolated quickstart explains why its change introduces no security surface; the integrated replay classifies its CSV export as a security task. Classification still requires human or independent agent review. The example does not provide a security certification.

Task-authoring review receipts in this deterministic demo are explicitly synthetic, pre-authored fixtures. They demonstrate receipt/gate mechanics, not genuine independent review. Live projects must obtain separate actual correctness and red-team reports; implementation review remains a separate gate.
