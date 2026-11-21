---
name: tequio-briefing
description: "Shape an idea or existing material into a concise product brief through focused discovery questions before research and exploration."
---

# Tequio Briefing

## Purpose and boundaries

Help the user express what they want to build. This is optional preparation before the four development phases, not a new CLI phase. Existing usable briefs can go directly to `$tequio-explore`. Use the installation prefix, if any, when invoking workflow skills (for example `$team-tequio-explore`). User/host instructions govern; agreeing a brief does not authorize implementation, publication or external service changes. Keep guidance independent of product/runtime frameworks.

## Conversation

Read supplied context, prior decisions and any existing draft first. Accept an idea, research collection or existing brief. Summarize what is already known; never make the user repeat settled answers. Do not require research, market validation or a technical specification from the user. Research belongs in Explore.

Ask one to three short, high-value questions per round, adapting to the answers rather than running a questionnaire. Start with the problem, intended user and a concrete successful use case. Clarify initial scope, exclusions, desired outcome and major constraints only where they affect direction. Offer simple options when helpful without silently deciding for the user. Reflect understanding and distinguish user decisions, agent proposals and open assumptions.

## Keep it tight

Aim for a few focused rounds, not exhaustive discovery. Before every follow-up, ask whether the answer would materially change the problem, user, main workflow, scope or a major constraint. If it would not, record an open question or leave it for Explore/Design. Do not pursue field lists, edge-case inventories, detailed acceptance criteria, implementation choices, architecture or feature-by-feature micromanagement unless essential to understanding the idea or explicitly requested. Do not invent mandatory sections or force answers to every prompt.

Stop when the problem, intended user, main use case, initial scope and major constraints are clear enough to investigate, with material unknowns visible. A constraint may be unknown or absent. Prefer a concise imperfect brief over another low-value question. If discussion loops, summarize settled intent and remaining uncertainty and offer the handoff. Respect a user's request to stop, save or explore sooner; do not use a round quota as a readiness certificate. Go deeper only when the user wants it or a concrete contradiction prevents a coherent brief.

## Draft and handoff

Maintain a concise draft covering the problem/users, desired outcome, main use case, first-version scope/exclusions, major constraints and decisions, available source references and open questions as relevant. Never manufacture evidence or present suggestions as approved requirements. Carry research questions forward without asking the user to research them.

Save drafts and a short resume note at an explicitly identified private project path before workspace creation; use `.tequio/intake/<name>/brief.md` and `notes.md` by default. These are agent-authored files, not CLI-managed intake state. Do not overwrite an existing draft or workspace silently; inspect and reconcile it. Keep private material out of product/public docs. Save on interruption and resume from that draft without restarting the interview.

Present the brief and remaining unknowns for user review. Ask whether it captures intent and is ready to explore unless current authorization already covers that handoff. Further polishing is optional. When ready, use `$tequio-explore` with the saved brief and explicit project/workspace. Explore creates the workspace with `workspace --brief <file>` when needed. Do not create a workspace from an unfinished draft just to record progress, run `record analysis` here, or begin implementation.
