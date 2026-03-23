# AI Guidance

## Purpose

This document is the shared documentation-policy source for AI tools working in this repository.
Tool-specific note files should mirror these rules closely.

## Documentation Pipeline

- `INBOX.md`: raw capture only
- `VISION.md`: long-horizon ideas not yet sequenced into active work
- `DECISIONS_INBOX.md`: pending design decisions awaiting approval
- `MILESTONES_INBOX.md`: draft sequencing awaiting approval
- `CHARTER.md`: active scope and current explicit rules
- `DECISIONS.md`: accepted canonical decision log
- `MILESTONES.md`: formal roadmap and active sequencing
- `docs/archive/`: preserved history and superseded notes

## Source Of Truth

When current implementation behavior is unclear, prefer:

1. `CHARTER.md`
2. `DECISIONS.md`
3. `MILESTONES.md`
4. `KNOWLEDGE-PIPELINE.md`

Inbox and archive documents are not the active source of truth.

## Rules For Writing

- Do not write raw brainstorming directly into `DECISIONS.md`.
- Do not write draft sequencing directly into `MILESTONES.md` unless it is approved.
- Do not treat `INBOX.md` as a canonical requirements document.
- Do not delete historical notes when they can be archived.
- Keep assistant guidance aligned across tool-specific note files.
- If the documentation structure changes, review `KNOWLEDGE-PIPELINE.md`.

## Review-First Automation

Documentation scripts in this repo are intended to audit, summarize, and draft suggestions.
They should not directly rewrite canonical docs like `CHARTER.md`, `DECISIONS.md`, or
`MILESTONES.md` without human review.

## Supported Tool Mirrors

These files should mirror this guidance where supported:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`
