# INBOX.md
## Purpose
Raw capture file. Dump ideas here during any session.
The nightly local LLM job processes and routes items.
Never delete directly - items are cleared by the processing script.

## Unprocessed Items

### 2026-04-17 — EWO/WorkDay state: draft / in-progress / final
**Bundle with DEC-071** (Sandbox / EWE / EWO as three artifacts). User
explicitly asked these be resolved together — designing a
draft/in-progress/final axis on the current `ExtraWorkOrder` alone would
create migration churn when EWE lands.

User's natural mental model: **draft** (pre-work, estimating / scoping) →
**in progress** (being filled in with daily reality) → **final** (locked,
submitted, ready to bill). Current `ExtraWorkOrder.Status` has six values
(`OPEN | SUBMITTED | APPROVED | REJECTED | SENT | BILLED`) which maps
roughly to in-progress (OPEN) + final (SUBMITTED onward), with nothing
representing "draft."

Questions to carry into the DEC-071 scoping:
- Likely mapping: draft ≈ Sandbox/EWE, in-progress ≈ EWO.OPEN,
  final ≈ EWO.SUBMITTED-and-beyond. Confirm or reject.
- Does WorkDay have its own per-day state (draft-day / locked-day) or
  does it inherit from parent?
- UX affordance: is the status badge enough, or do we want a colored
  bar + text ("DRAFT — still being priced") so a foreman tapping on
  their phone knows at a glance what they're looking at?

Captured 2026-04-17 during the Phase 3 iPad/phone walkthrough.
