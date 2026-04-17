# INBOX.md
## Purpose
Raw capture file. Dump ideas here during any session.
The nightly local LLM job processes and routes items.
Never delete directly - items are cleared by the processing script.

## Unprocessed Items

### 2026-04-17 — EWO/WorkDay state: draft / in-progress / final
Surfaced during the UI walkthrough on the phone. Current `ExtraWorkOrder.Status`
has six values (`OPEN | SUBMITTED | APPROVED | REJECTED | SENT | BILLED`) but
the user’s natural mental model is simpler: **draft** (pre-work, estimating /
scoping) → **in progress** (being filled in with daily reality) → **final**
(locked, submitted, ready to bill).

Open questions for routing to `DECISIONS_INBOX.md`:
- Is this a new independent axis, or a re-label of existing statuses (e.g.
  draft ≈ ESTIMATE/EWE, in-progress ≈ OPEN, final ≈ SUBMITTED-and-beyond)?
- Does the WorkDay also have its own per-day state (draft-day / locked-day)
  or does it inherit from the parent EWO?
- Interaction with DEC-071 (Sandbox / EWE / EWO as three artifacts) — if that
  decision lands, "draft" probably maps to Sandbox/EWE and "in-progress/final"
  to EWO lifecycle phases.
- UX affordance: when the UI renders an EWO, is the status badge enough, or
  do we want a colored bar + text ("DRAFT — still being priced") so a foreman
  tapping in on their phone knows at a glance what they’re looking at?

Captured 2026-04-17 during the Phase 3 iPad/phone walkthrough.
