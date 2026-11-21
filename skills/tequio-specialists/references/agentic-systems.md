# Agentic systems reference

Use when the project builds LLM-driven tools, workflows or autonomous behavior. Skip otherwise. Shared source, execution and qualification rules: [coverage guide](coverage-guide.md).

## Questions the agent resolves from project context

- Deterministic first: would a fixed workflow, script or ordinary code solve this reliably? Choose autonomy only where it demonstrably helps; multiagent design is never required.
- Tool contracts and least privilege: what exactly can each tool do, with what bounds, and what is explicitly denied? Prefer narrow tools over general execution.
- Context and state: what does the model see, what persists between steps, and what must never enter prompts or logs (secrets, private records)?
- Untrusted input and output: tool results, retrieved pages and user content can carry injection; model output can be wrong or unsafe. Validate outputs before acting, especially before external effects.
- Evals and limits: what realistic evals show the system works, and what stop conditions, step/time/cost caps and human approval gates bound it? Missing telemetry stays unknown, never zero.

## Sources

The selected provider/model/SDK's current primary documentation supplies actual behavior; vendor pattern articles are scoped and potentially dated. [Anthropic's building-effective-agents](https://www.anthropic.com/research/building-effective-agents) (accessed 2026-11-17) distinguishes workflows from agents and explicitly warns the tooling landscape changed since its December 2024 publication — use patterns cautiously, not APIs. The [OWASP GenAI LLM Top 10](https://genai.owasp.org/llm-top-10/) (2025 edition accessed 2026-11-17; observed entries include sensitive information disclosure, improper output handling, excessive agency and unbounded consumption) is risk guidance, not a security certification. No model-quality or performance claims are made or implied here.

## Exercise considerations

Realistic exercises include hostile tool output attempting to redirect the agent, an unauthorized external action that must be denied, and a bounded loop/cost cap that actually stops. Cover expected and denied/failure behavior with isolated fixtures and genuine independent review; reading this page qualifies nothing.
