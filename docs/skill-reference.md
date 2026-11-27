# Tequio skill reference

## Everyday flow

Optional preparation: `$tequio-briefing` shapes intent through focused questions, then hands the concise brief to Explore. Skip it when a usable brief exists. Explore owns research whether existing material is available or not; briefing is not a fifth required development phase.

`$tequio-explore` → `$tequio-design` → `$tequio-tasks` → `$tequio-build`

`$tequio-status` explains where you are, the next step and remaining work.

## All current entry points

- `$tequio-briefing`
- `$tequio-explore`
- `$tequio-design`
- `$tequio-tasks`
- `$tequio-build`
- `$tequio-check`
- `$tequio-inspect`
- `$tequio-challenge`
- `$tequio-status`
- `$tequio-handoff`
- `$tequio-pickup`
- `$tequio-redirect`
- `$tequio-learn`
- `$tequio-specialists`
- `$tequio-package`
- `$tequio-routing` — optional workspace model-routing preferences; never selects or launches models.

Only these names are installed; no old skill aliases are retained. Internal Python lifecycle verbs and existing workspace state remain separate from public skill names. Upgrades remove unchanged installer-owned obsolete entries while retaining project-owned specialists and workspaces.

With a custom installation prefix such as `team-`, instructional Markdown in both discovery skills and bundled skill/reference copies uses invocations such as `$team-tequio-tasks`. Only whole known workflow invocation tokens are rendered. Bundled paths such as `.tequio/skills/tequio-tasks/SKILL.md` and reference frontmatter retain their asset identity. Unknown or already-prefixed tokens and source files are preserved; manifest hashes bind the rendered installed bytes. Default installation remains unprefixed.

## Optional project explanation

`$tequio-explain` explains a named project topic through a grounded offline interactive lesson and safe owner-selected delivery. With no topic, infer only an unambiguous immediate subject or ask one short question. The complete reference and HTML shell are installed with default and prefixed discovery. Learn/codify and the four development phase mappings are unchanged. See [Explain artifacts](explain-artifacts.md).
