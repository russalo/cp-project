# KNOWLEDGE-PIPELINE

## Why This Exists

This repository has accumulated planning notes, session artifacts, accepted decisions, future ideas,
and tool-specific guidance over time. Without structure, those documents blur together. Raw ideas
end up mixed into active scope. Historical notes linger in the repo root and look current. People
and AI tools have to guess which file is the real source of truth.

This pipeline exists to solve that problem.

Its purpose is simple: every kind of information should have an obvious home, a clear approval path,
and a known lifecycle. The system should make it hard to lose good thinking and just as hard to
mistake unapproved thinking for active project truth.

## The Problem It Solves

Most documentation drift comes from one of four failures:

1. Ideas are captured but never routed.
2. Future concepts are written directly into active planning files.
3. Accepted project rules are spread across multiple documents with slight differences.
4. Old notes remain visible but are not clearly marked as historical.

The knowledge pipeline gives the project a structured flow:

- capture first
- review and sort second
- approve into canonical docs third
- preserve history without cluttering active work

## The Stages

### Stage 1: Raw Capture

File: `INBOX.md`

This is the landing zone for fresh thoughts. Use it for:

- brainstorm fragments
- notes copied from chats
- ideas from field experience
- rough implementation thoughts
- things worth preserving before they are fully formed

Do not treat `INBOX.md` as a source of truth. It is a holding layer.

### Stage 2: Future Vision

File: `VISION.md`

This document holds expanded product direction that is not yet part of the active roadmap. Use it
for ideas that are important enough to preserve, but are still too broad or too early for current
milestones.

Use `VISION.md` when an idea is:

- real and valuable
- beyond current scope
- not yet approved for implementation
- likely to influence future architecture or product direction

### Stage 3: Pending Decisions

File: `DECISIONS_INBOX.md`

This is where unresolved architectural and workflow choices wait for review. These are not accepted
project rules yet. They are candidates for future promotion into `DECISIONS.md`.

Use `DECISIONS_INBOX.md` when the project needs a real decision but the choice is not final.

### Stage 4: Draft Sequencing

File: `MILESTONES_INBOX.md`

This file is for proposed roadmap sequencing that is not yet part of the canonical milestone plan.
It is the right place for "we should probably do this in M3/M4/M5" thinking before it gets folded
into the formal roadmap.

### Stage 5: Active Scope and Rules

File: `CHARTER.md`

`CHARTER.md` is where the current product boundary lives. It should describe what the system is,
what rules are active, and what explicit constraints govern present-day implementation.

If a rule changes how the current product must behave, and it is already accepted, it belongs in
the charter or in the canonical decision log that the charter references.

### Stage 6: Accepted Decisions

File: `DECISIONS.md`

This is the canonical decision log. It contains accepted, proposed, deferred, and rejected
architectural choices in a structured format. It is not the place for raw brainstorming.

Use `DECISIONS.md` for decisions that are formal enough to track with IDs, options, context, and
consequences.

### Stage 7: Active Roadmap

File: `MILESTONES.md`

This is the formal delivery plan. It is for current sequencing, milestone scope, and accepted work
ordering. It should stay planning-first and human-readable.

### Stage 8: Preserved History

Folder: `docs/archive/`

Historical notes, superseded planning docs, completed homework batches, and older session artifacts
should be moved here rather than deleted. Archive material stays available for reference, but it is
separated from active controls so it does not read like current truth.

Common archive locations include:

- `docs/archive/session-notes/`
- `docs/archive/homework/`
- `docs/archive/plans/`
- `docs/archive/reference/`

## Source-Of-Truth Hierarchy

When two documents seem to disagree, use this order of trust:

1. `CHARTER.md` for active scope and core product rules
2. `DECISIONS.md` for accepted architectural and process choices
3. `MILESTONES.md` for active sequencing
4. `KNOWLEDGE-PIPELINE.md` for documentation structure and routing rules
5. `VISION.md`, `DECISIONS_INBOX.md`, and `MILESTONES_INBOX.md` for pending or future-state material
6. `INBOX.md` for raw capture only
7. `docs/archive/` for historical reference

## What Goes Where

Here are the common cases:

- "I had an idea and do not want to lose it."
  Put it in `INBOX.md`.
- "This is a real future feature area, but not active yet."
  Put it in `VISION.md`.
- "We need to choose between two implementation approaches."
  Put it in `DECISIONS_INBOX.md` first, then promote it to `DECISIONS.md` when approved.
- "This work belongs in a future milestone, but the sequencing is not official yet."
  Put it in `MILESTONES_INBOX.md`.
- "This is now an active, accepted product rule."
  Put it in `CHARTER.md` and/or `DECISIONS.md`, depending on whether it is scope or a tracked decision.
- "This old note still matters historically, but it should not stay in the root."
  Move it to `docs/archive/`.

## Approval Flow

Information is supposed to move through the system like this:

`INBOX.md` -> review -> one of:

- `VISION.md`
- `DECISIONS_INBOX.md`
- `MILESTONES_INBOX.md`
- `CHARTER.md`
- `DECISIONS.md`
- `MILESTONES.md`
- `docs/archive/`

Not every note takes the same path. The important rule is that capture happens first, then review,
then promotion into the correct long-term home.

## Archive Policy

The archive is not a trash can. It is a preserved history layer.

Move documents into `docs/archive/` when they are:

- completed
- superseded
- historically useful but no longer active
- too specific or old to keep in the repo root

Do not delete notes just because the active docs have changed.

## Session Workflow

The session commands should support this pipeline:

- `make start-session`
  - shows the current branch and recent status
  - surfaces priority Markdown files that need review
  - warns if the pipeline guide may be stale
- `make stop-session`
  - summarizes documentation changes made during the session
  - warns when pipeline-related docs changed without updating `KNOWLEDGE-PIPELINE.md`

## Script Support

The repo includes documentation maintenance helpers. Their job is to make the pipeline easier to
use, not to silently rewrite canonical documents.

Current `make` targets:

- `make docs-audit`
- `make knowledge-pipeline-check`
- `make inbox-status`
- `make inbox-route-draft`
- `make archive-audit`
- `make assistant-doc-check`

The scripts are review-first. They audit, summarize, and draft suggestions. They do not directly
append accepted material into `CHARTER.md`, `DECISIONS.md`, or `MILESTONES.md`.

## AI Assistant Alignment

Humans and AI tools should follow the same documentation structure.

The shared AI guidance lives in:

- `docs/reference/ai-guidance.md`

Tool-facing note files should mirror that guidance where supported:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`

If a tool does not support a recognized repo-level instructions file, the shared guidance document
remains the canonical source.

## Common Mistakes To Avoid

- Do not put raw notes directly into `DECISIONS.md`.
- Do not put future-scope product ideas directly into `MILESTONES.md`.
- Do not leave old planning documents in the root once they become historical.
- Do not assume archive means delete.
- Do not let AI instruction files drift from one another.
- Do not change the documentation structure without checking whether `KNOWLEDGE-PIPELINE.md`
  should be updated too.
