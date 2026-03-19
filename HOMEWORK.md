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
   - Answer: Four roles (foreman, pm, office, admin). Foreman: create EWO,
     edit own open EWO lines, submit. PM: all foreman actions + edit any open
     EWO, approve, reject, mark sent. Office: all PM actions except
     approve/reject + mark billed, manage reference data (rates, employees,
     equipment). Admin: all actions + manage users. All roles can read any EWO
     and view audit history.
   - Decision: DEC-033

2. **Sent status tracking:** when an EWO is marked as sent to the GC, what
   information should be recorded — sent date, sent by, method (email, GC portal),
   reference/confirmation number?
   - Answer: Four fields on `ExtraWorkOrder`, all nullable and populated atomically
     on the `approved → sent` transition: `sent_date` (DateField, auto-set to
     today), `sent_by` (FK to User, auto-set to current user), `sent_method`
     (CharField choices: email / gc_portal / hand_delivered / other),
     `sent_reference` (CharField optional — email thread subject, portal
     confirmation number, etc.). No separate model needed.
   - Decision: DEC-034

3. **GC response tracking:** should the system record the GC's response to a
   submitted EWO (accepted, rejected, partial, pending) even though the
   submission itself happens outside the system?
   - Answer: Yes — the charter explicitly requires GC acknowledgment tracking.
     Three fields on `ExtraWorkOrder` (metadata, not a lifecycle state):
     `gc_acknowledged_by` (CharField; name string per DEC-012, not a User FK),
     `gc_acknowledged_at` (DateTimeField nullable), `gc_acknowledgment_method`
     (CharField choices: signature / email / verbal / none_recorded). Absence
     is explicitly recordable. Fields are editable by PM and office after the
     `sent` transition.
   - Decision: DEC-035

4. **Billed status:** when is an EWO marked as billed — when it's included in
   a pay application, when payment is received, or when it's sent to accounting?
   - Answer: Billed = included in a pay application (already defined in
     DEC-016). The `sent → billed` transition is triggered by office or admin
     only. Add `pay_app_reference` (CharField optional) to record the pay
     application number/name for cross-referencing (e.g. "PA-14"). Also
     `billed_date` (DateField auto-set) and `billed_by` (FK to User auto-set)
     on transition. No payment-received tracking in v1 — that is an accounting
     system concern.
   - Decision: DEC-036

5. **Multiple work dates:** can a single EWO span multiple work dates (e.g.
   a T&M job that runs Tuesday through Thursday), or is one EWO always one
   work date?
   - Answer: Yes — multi-day EWOs are the norm, not the exception. The printed
     output has one page per day (with that day's work description) plus a
     summary cover page. This requires a `WorkDay` grouping model: one record
     per calendar date per EWO, carrying its own `work_date`, `location`, and
     `description`. `LaborLine` and `EquipmentLine` belong to a `WorkDay`, not
     directly to the EWO. `MaterialLine` stays at EWO level (materials are not
     tied to a specific day). The EWO header carries a summary `description`
     for the cover page.
   - Decision: DEC-037

6. **Employee CSV seed format:** what columns does the employee seed CSV need —
   is the Excel rate sheet (code, name, trade, rates) the source, or is there
   a separate HR/payroll export?
   - Answer: Source is the existing Excel rate sheet. CSV columns:
     `employee_id` (optional internal identifier; blank = auto-assign),
     `first_name`, `last_name`, `default_trade_code` (must match a
     TradeClassification.code already in the system), `union` (choices:
     IUOE / LIUNA / OPCMIA / IBT). Import via `django-import-export` admin
     mixin. Template committed at
     `backend/resources/seed/employees_template.csv`.
   - Decision: DEC-038

7. **Equipment type seed:** how should the initial `EquipmentType` records be
   populated — from the existing Excel rate reference, manual entry, or a
   dedicated CSV? Which Caltrans codes are actively used and need to be in
   the initial set?
   - Answer: Convert the relevant pages of the Caltrans Equipment Rental Rate
     schedule to CSV; import via `django-import-export` admin action on
     `CaltransRateLine`. CSV columns: `schedule_year`, `class_code`, `make`,
     `model`, `rental_rate`, `rw_delay_rate`, `overtime_rate`, `effective_date`.
     CSV committed at `backend/resources/seed/caltrans_rates_<year>.csv`. Only
     the codes CP actively uses are included — PM or office provides the list
     of active Caltrans codes before the seed file is built.
   - Decision: DEC-039

8. **Job CRUD ownership:** who creates and manages job records in v1 — PM only,
   office/admin only, or any authenticated user?
   - Answer: PM and office can create, edit, and deactivate Job records.
     Foreman is read-only (can select a job when creating an EWO but cannot
     create or modify jobs). Admin has full access. Jobs are entered manually
     in-app — job numbers come from the estimating/bidding process outside the
     system. Job model fields: `job_number` (validated per DEC-019),
     `job_name` (optional free text), `active` boolean (deactivation hides
     the job from new-EWO dropdowns without deleting it).
   - Decision: DEC-040

9. **EWO description field:** is the work description a single free-text field,
   or does it need structure — e.g. separate fields for location, scope,
   reason it's extra work?
   - Answer: Description lives at two levels. On `WorkDay` (per DEC-037):
     `location` (CharField) and `description` (TextField) specific to that
     day's work — these drive each day's printed page. On `ExtraWorkOrder`
     header: a summary `description` (TextField) for the cover page; `location`
     on the header is optional (defaults to the job location context). Both
     `WorkDay` fields required at submission; header `description` required at
     submission. No separate `reason_for_extra` field in v1.
   - Decision: DEC-041

10. **Audit log visibility:** should the audit/history trail (who changed what
    and when) be visible to all roles, PM and above only, or admin only?
    - Answer: All authenticated users can read the history trail for any EWO
      they can view. History records are read-only for all roles. The Django
      admin history view is restricted to admin. Small internal team —
      transparency supports accountability without meaningful risk.
    - Decision: DEC-042
