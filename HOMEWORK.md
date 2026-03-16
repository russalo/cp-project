# HOMEWORK

This file is the live homework tracker for the next planning batch.

## Current Status

- Homework batch `001` is complete and preserved in `HOMEWORK-001.md`.
- Accepted answers from that batch have been folded into `DECISIONS.md`.
- Active homework batch: `002` in this file.

## How To Use

When a new batch of planning questions is created:

1. Add the new questions here.
2. Copy completed batches into numbered archives such as `HOMEWORK-002.md` when needed.
3. Record accepted answers in `DECISIONS.md` before implementation starts.
4. Leave unresolved items open until pros/cons are reviewed and a decision is ready.

## Session Rollover Rule

- At the end of each session, if the previous homework batch has been fully answered, add 10 new homework items to this file for the next session.

## Still Open From Batch 001

- Document storage strategy for future upload support is still unresolved; see `DEC-017` in `DECISIONS.md`.

## Homework Batch 002 (Open)

Created automatically during stop-session rollover on 2026-03-14.

1. **EWO numbering strategy:** should EWO IDs be sequential globally, per customer, or per job number?
   - Answer: TBD
2. **Job number validation:** what format rules should v1 enforce for job number entry (required prefix/length/characters)?
   - Answer: TBD
3. **Labor unit policy:** should labor be captured in hours only, or support hour + minute precision in v1?
   - Answer: TBD
4. **Equipment quantity model:** should equipment usage be time-based only, quantity-based only, or both with explicit unit types?
   - Answer: TBD
5. **Material pricing entry rule:** should materials default to unit cost x quantity, with optional manual total override?
   - Answer: TBD
6. **Rounding policy detail:** where should rounding occur (line item, category subtotal, final total), and to how many decimals?
   - Answer: TBD
7. **Tax policy boundary:** should tax be excluded from v1, optional per EWO, or required per material line category?
   - Answer: TBD
8. **Overtime modeling:** should overtime be represented as separate labor line types or a multiplier on standard labor lines?
   - Answer: TBD
9. **Approval authority:** which role is allowed to approve/reject EWOs in v1, and is dual-approval needed?
   - Answer: TBD
10. **Post-approval edits:** if an approved EWO must change, should it reopen, clone to revision, or require admin override with audit reason?
   - Answer: TBD
