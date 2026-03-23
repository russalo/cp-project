# AGENTS.md

This file mirrors the shared policy in `docs/reference/ai-guidance.md`.

## Project Context

cp-project is a full-stack web application for an underground wet utility pipeline contractor to
manage Extra Work Orders (EWOs) across field capture, costing, review, and billing.

**Current status:** Milestone 1 in progress. CI is in place; core backend API surfaces and an
initial Jobs UI page are implemented, with additional models and features still under active
development.

## Knowledge Pipeline Rules

- `INBOX.md`: raw capture only
- `VISION.md`: long-horizon product direction
- `CHARTER.md`: current product scope and constraints
- `DECISIONS.md`: accepted architectural choices
- `DECISIONS_INBOX.md`: pending decisions awaiting approval
- `MILESTONES.md`: formal roadmap and active sequencing
- `MILESTONES_INBOX.md`: draft sequencing awaiting approval
- `KNOWLEDGE-PIPELINE.md`: human-readable guide for the full system
- `docs/archive/`: preserved historical notes and superseded planning artifacts

## Domain Rules

- CP role belongs on `Contract`, not `Job`.
- `is_public_works` controls claims-workflow branching.
- Money calculations use Python `Decimal` only.
- Rates snapshot at EWO submission and remain immutable for historical records.
- GC acknowledgment absence is itself a recordable fact.
- Billing supports `UNIT`, `LUMP_SUM`, and `TM`.
- Field UI concepts are future-module work; the current EWO API is the data layer underneath.

## Working Rules

- Treat `CHARTER.md`, `DECISIONS.md`, and `MILESTONES.md` as the active source of truth.
- Route unapproved ideas to `INBOX.md`, `DECISIONS_INBOX.md`, or `MILESTONES_INBOX.md`.
- Do not place raw brainstorming directly into canonical docs.
- Preserve history by archiving notes in `docs/archive/` instead of deleting them.
- Review `KNOWLEDGE-PIPELINE.md` whenever the documentation structure changes.
