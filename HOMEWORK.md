# HOMEWORK

This file is the live homework tracker for the next planning batch.

## Current Status

- Homework batch `001` is complete and preserved in `HOMEWORK-001.md`.
- Homework batch `002` is complete and preserved in `HOMEWORK-002.md`; answers folded into `DECISIONS.md` as DEC-018 through DEC-027.
- Active homework batch: `003` in this file.

## How To Use

When a new batch of planning questions is created:

1. Add the new questions here.
2. Copy completed batches into numbered archives such as `HOMEWORK-002.md` when needed.
3. Record accepted answers in `DECISIONS.md` before implementation starts.
4. Leave unresolved items open until pros/cons are reviewed and a decision is ready.

## Session Rollover Rule

- At the end of each session, if the previous homework batch has been fully answered,
  add 10 new homework items to this file for the next session.

## Still Open From Batch 001

- Document storage strategy for future upload support is still unresolved;
  see `DEC-017` in `DECISIONS.md`.

---

## Homework Batch 002 (Complete — archived in HOMEWORK-002.md)

Answered: 2026-03-18. Decisions recorded as DEC-018 through DEC-027 in `DECISIONS.md`.

---

## Homework Batch 003 (Open)

Created: 2026-03-18

1. **Role permissions matrix:** what specific actions can each role (foreman,
   PM, office, admin) perform — create EWO, edit lines, submit, approve, mark
   sent, mark billed, manage reference data?
   - Answer: TBD

2. **Sent status tracking:** when an EWO is marked as sent to the GC, what
   information should be recorded — sent date, sent by, method (email, GC portal),
   reference/confirmation number?
   - Answer: TBD

3. **GC response tracking:** should the system record the GC's response to a
   submitted EWO (accepted, rejected, partial, pending) even though the
   submission itself happens outside the system?
   - Answer: TBD

4. **Billed status:** when is an EWO marked as billed — when it's included in
   a pay application, when payment is received, or when it's sent to accounting?
   - Answer: TBD

5. **Multiple work dates:** can a single EWO span multiple work dates (e.g.
   a T&M job that runs Tuesday through Thursday), or is one EWO always one
   work date?
   - Answer: TBD

6. **Employee CSV seed format:** what columns does the employee seed CSV need —
   is the Excel rate sheet (code, name, trade, rates) the source, or is there
   a separate HR/payroll export?
   - Answer: TBD

7. **Equipment type seed:** how should the initial `EquipmentType` records be
   populated — from the existing Excel rate reference, manual entry, or a
   dedicated CSV? Which Caltrans codes are actively used and need to be in
   the initial set?
   - Answer: TBD

8. **Job CRUD ownership:** who creates and manages job records in v1 — PM only,
   office/admin only, or any authenticated user?
   - Answer: TBD

9. **EWO description field:** is the work description a single free-text field,
   or does it need structure — e.g. separate fields for location, scope,
   reason it's extra work?
   - Answer: TBD

10. **Audit log visibility:** should the audit/history trail (who changed what
    and when) be visible to all roles, PM and above only, or admin only?
    - Answer: TBD
