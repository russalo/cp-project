# LABOR_PLAN - Labor management module design (#11)

## Purpose

Define a practical v1 design for labor management inside Extra Work Orders (EWOs), aligned to Milestone 2 and accepted decisions in `DECISIONS.md`.

## Scope

In scope for v1:

- Labor trade/rate setup with historical records.
- Labor line entry on EWOs.
- Server-side labor cost calculation using `Decimal`.
- Submission-time rate snapshots on labor lines.
- Lifecycle lock behavior aligned to `draft -> submitted -> approved/rejected -> billed`.
- Audit events for critical labor changes.

Out of scope for v1:

- Full customer/jobsite/contact model (deferred by `DEC-011`).
- File upload and PDF packaging features (deferred by `DEC-013`).
- Dropbox integration (deferred by `DEC-010`).

## Design constraints from existing decisions

- `DEC-011`: v1 EWO context stays minimal (job number reference only).
- `DEC-012`: app users and tracked labor are separate concepts.
- `DEC-014`: latest rate is active for new work, with history preserved.
- `DEC-015`: submitted EWOs snapshot applied rates.
- `DEC-016`: lifecycle baseline is `draft -> submitted -> approved/rejected -> billed`.

## V1 domain model proposal

## `LaborTrade`

Represents a labor classification (for example, Operator, Foreman, Laborer).

Suggested fields:

- `id`
- `code` (short unique key, optional)
- `name` (required, unique)
- `is_active` (default `true`)
- `created_at`, `updated_at`

## `LaborTradeRate`

Historical rate records per trade. Latest effective record is active for new lines.

Suggested fields:

- `id`
- `labor_trade_id` (FK -> `LaborTrade`)
- `hourly_rate` (`Decimal`, required)
- `effective_start` (date/datetime, required)
- `effective_end` (date/datetime, nullable)
- `source_note` (optional text: agreement/version note)
- `created_by` (FK -> user)
- `created_at`

Constraints:

- no overlapping effective windows per trade
- exactly one active window for a point in time
- rate values greater than zero

## `LaborEntry`

Labor line item attached to an EWO.

Suggested fields:

- `id`
- `ewo_id` (FK -> `ExtraWorkOrder`)
- `labor_trade_id` (FK -> `LaborTrade`)
- `description` (optional text)
- `hours` (`Decimal`, precision supports quarter-hours or finer)
- `applied_hourly_rate` (`Decimal`) - snapshot on submit
- `line_total` (`Decimal`) - server-calculated
- `rate_source` (enum: `table`, `manual_override`)
- `manual_rate_reason` (required when override used)
- `created_by`, `updated_by`
- `created_at`, `updated_at`

Important behavior:

- In `draft`, line may reference live table rate.
- On submit, line stores immutable `applied_hourly_rate` snapshot.
- `line_total` is always recalculated server-side from snapshot rate and hours.

## Cost calculation rules (v1)

- All money and quantities use `Decimal`; floats are disallowed.
- Baseline formula: `line_total = hours * applied_hourly_rate`.
- Rounding policy target: currency to 2 decimals; exact step timing to be finalized in `DEC-003`.
- Client never submits trusted totals; server computes and persists totals.

## Workflow behavior by lifecycle state

## `draft`

Allowed:

- create/edit/delete labor lines
- choose trade
- optional manual rate override with reason

## `submitted`

On transition:

- snapshot `applied_hourly_rate` for each labor line
- recompute and persist all labor `line_total` values
- freeze editable labor cost fields

After transition:

- no direct edits to labor financial fields

## `approved` / `rejected`

- financial fields remain locked
- rejection path behavior (return-to-draft vs explicit resubmit) to follow final lock policy write-up

## `billed`

- immutable for v1 except admin correction workflow if approved later

## Permissions matrix (initial)

Role labels are placeholders until Milestone 4 auth decisions are implemented.

- `field_user`:
  - create/edit labor lines in `draft`
  - cannot approve/reject/bill
- `reviewer`:
  - submit and approve/reject EWOs
  - cannot edit locked financial data post-submit
- `billing`:
  - move approved -> billed
- `admin`:
  - manage trade/rate tables
  - perform exceptional correction actions with audit reason

## API surface proposal (v1)

Exact conventions depend on `DEC-004`; this is a shape proposal.

Reference data:

- `GET /api/v1/labor-trades`
- `POST /api/v1/labor-trades`
- `PATCH /api/v1/labor-trades/{id}`
- `GET /api/v1/labor-trades/{id}/rates`
- `POST /api/v1/labor-trades/{id}/rates`

EWO labor lines:

- `GET /api/v1/ewos/{ewo_id}/labor-lines`
- `POST /api/v1/ewos/{ewo_id}/labor-lines`
- `PATCH /api/v1/ewos/{ewo_id}/labor-lines/{line_id}`
- `DELETE /api/v1/ewos/{ewo_id}/labor-lines/{line_id}`

Lifecycle actions:

- `POST /api/v1/ewos/{id}/submit`
- `POST /api/v1/ewos/{id}/approve`
- `POST /api/v1/ewos/{id}/reject`
- `POST /api/v1/ewos/{id}/bill`

## Validation and guardrails

- labor trade must exist and be active for new draft entries
- hours must be positive and within sane limit
- manual override requires non-empty reason
- submitted/approved/billed state blocks labor financial edits
- idempotency strategy for create/submit follows `DEC-005`

## Audit trail requirements

Capture at minimum:

- labor line created/updated/deleted in `draft`
- manual rate override set/changed
- submit transition with per-line snapshot values
- approval/rejection/billing transitions
- any admin correction after lock states

Store actor, timestamp, action type, record id, and before/after payload for financial fields.

## Reporting needs (v1)

Minimum useful outputs:

- labor totals by EWO
- labor totals by trade for date range
- draft vs submitted delta visibility
- billed labor amount summary for office handoff

## Delivery plan

## Phase 1 - Model + migrations

- implement `LaborTrade`, `LaborTradeRate`, and `LaborEntry`
- add DB constraints for effective windows and positive values

## Phase 2 - Core API + server calculations

- CRUD for labor lines in `draft`
- central service for labor total calculations with `Decimal`
- submit action snapshots rates and locks fields

## Phase 3 - Lifecycle + permissions + audit

- enforce state transitions and lock checks
- role checks for submit/approve/reject/bill
- write audit events for critical actions

## Phase 4 - Basic reporting endpoints

- add labor summary endpoints for EWO and date-range views
- verify figures against known examples

## Risks and open questions

- Final rounding timing and overtime/tax behavior are still open under `DEC-003`.
- API error/pagination/filter standards pending `DEC-004`.
- Duplicate prevention and idempotency behavior pending `DEC-005`.
- Post-approval correction policy still needs explicit accepted path.

## Decision checklist before implementation lock

- [ ] Confirm labor time precision for v1 (hours only vs hour/minute entry).
- [ ] Confirm rounding point and precision for labor totals.
- [ ] Confirm manual rate override policy and required approval threshold.
- [ ] Confirm reject workflow behavior (return to draft vs explicit resubmit).
- [ ] Confirm admin correction approach after approval/billing.
- [ ] Confirm API conventions once `DEC-004` is accepted.
- [ ] Confirm idempotency strategy once `DEC-005` is accepted.

## Links

- `MILESTONES.md` (Milestone 2)
- `DECISIONS.md` (`DEC-003`, `DEC-004`, `DEC-005`, `DEC-011`, `DEC-012`, `DEC-014`, `DEC-015`, `DEC-016`)
- `WORKFLOW.md`
- `WORKFLOW-SETUP.md`

