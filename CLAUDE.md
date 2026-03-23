# Claude Cowork & Code Context

This file mirrors the shared policy in `docs/reference/ai-guidance.md`.

## Role & Background

Operating Engineer at an underground wet utility pipeline contractor. Python/Django developer.
Building the cp-project EWO management system.

## Knowledge Pipeline Rules

- `INBOX.md`: dump raw ideas here
- `VISION.md`: long-horizon product direction
- `CHARTER.md`: current product scope and constraints
- `DECISIONS.md`: accepted architectural choices
- `DECISIONS_INBOX.md`: pending decisions that need review before promotion
- `MILESTONES.md`: formal roadmap and active sequencing
- `MILESTONES_INBOX.md`: draft sequencing awaiting approval
- `SESSION_PREP.md`: current session plan when present
- `KNOWLEDGE-PIPELINE.md`: human-readable guide for the full system
- `docs/archive/`: preserved historical notes and superseded planning artifacts

## Local LLM Routing

- Use `claude-local` (Ollama/qwen3-coder:30b) for commit messages, `DEV-SESSION` updates,
  boilerplate, test scaffolding, docstrings, and anything containing proprietary field data.
- Use `claude-api` (Anthropic API) for architecture decisions, rate/money calculation logic,
  state machine design, security, and complex refactors.

## Domain Core Rules

- Contract Chain: CP operates in 5 configurations. Look up `cp_role` on `Contract`, never `Job`.
- Party Authority: A CM agent cannot authorize extra work. Authorization requires the party who
  holds the contract with CP.
- Public Works: `is_public_works` determines the claims workflow.
- Notice Requirements: Missing a notice window voids a claim. `notice_given_date` is strictly
  enforced. The email timestamp from `ewo@cp.construction` is the legal notice timestamp.
- Inspector Authority: An inspector signing a T&M sheet is not the same as a formal GC/CM directive.
- Decimal Rule: Python `Decimal` only. No floats. Applies to LD rates, overhead, and retention.
- Billing Types: `PayItem.billing_type` determines earned value (`UNIT`, `LUMP_SUM`, or `TM`).
- Legal Weight: `Party.legal_weight` is computed from role plus contract context. It is not stored.
- Witnesses: EWO witnesses are always a `ForeignKey` to `Party`, never a plain string.
- Unrecognized Work: When a `DailyReport` entry does not map to a `PayItem`, it triggers
  `UnrecognizedWork`, which initiates the EWO workflow.
- Standby vs EWO: Standby is a separate event lifecycle. Do not merge standby into EWO line items.
- Field UI Goal: The mobile UI is framed as "Protect Yourself", constrained by the 3-tap rule.

## Working Rules

- Use `CHARTER.md`, `DECISIONS.md`, and `MILESTONES.md` as the active source of truth.
- Route unapproved ideas through `INBOX.md`, `DECISIONS_INBOX.md`, or `MILESTONES_INBOX.md`
  before promoting them.
- Do not write raw brainstorming directly into canonical docs.
- Do not delete old notes when they can be moved into `docs/archive/`.
- Review `KNOWLEDGE-PIPELINE.md` whenever the documentation structure changes.
