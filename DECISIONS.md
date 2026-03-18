# DECISIONS

## Purpose

This file is the project decision log for architecture and process choices that need options review.
Use it to record what was considered, what was chosen, and why.

## How To Use

1. Add or update an entry when a milestone item marked `Decision:` is being evaluated.
2. Compare at least two options with pros/cons.
3. Mark the final status (`proposed`, `accepted`, `deferred`, `rejected`).
4. Link the decision ID in PR descriptions and milestone updates.

## Decision Index

| ID | Milestone | Topic | Status | Owner | Target Date |
|---|---|---|---|---|---|
| DEC-001 | M1 | CI gate strategy | accepted | TBD | 2026-03-14 |
| DEC-002 | M1 | Production Python/runtime pinning | accepted | TBD | 2026-03-13 |
| DEC-003 | M2 | Source of truth and calculation boundary | accepted | TBD | 2026-03-18 |
| DEC-004 | M2 | API contract conventions | proposed | TBD | TBD |
| DEC-005 | M2 | Duplicate-prevention/idempotency approach | proposed | TBD | TBD |
| DEC-006 | M3 | TypeScript migration strategy | proposed | TBD | TBD |
| DEC-007 | M4 | Auth architecture | proposed | TBD | TBD |
| DEC-008 | M5 | Deployment strategy | proposed | TBD | TBD |
| DEC-009 | M5 | Rollback model | proposed | TBD | TBD |
| DEC-010 | M6 | Dropbox integration strategy | accepted | TBD | 2026-03-14 |
| DEC-011 | M2 | v1 EWO minimum context | accepted | TBD | 2026-03-14 |
| DEC-012 | M2 | People model boundary | accepted | TBD | 2026-03-14 |
| DEC-013 | M6 | Material evidence and PDF feature boundary | accepted | TBD | 2026-03-14 |
| DEC-014 | M2 | Rate precedence and history | accepted | TBD | 2026-03-14 |
| DEC-015 | M2 | Submitted EWO rate snapshot behavior | accepted | TBD | 2026-03-14 |
| DEC-016 | M2 | v1 EWO lifecycle baseline | accepted | TBD | 2026-03-14 |
| DEC-017 | M6 | Document storage strategy | proposed | TBD | TBD |
| DEC-018 | M2 | EWO numbering format | accepted | TBD | 2026-03-18 |
| DEC-019 | M2 | Job number validation format | accepted | TBD | 2026-03-18 |
| DEC-020 | M2 | Labor hours precision | accepted | TBD | 2026-03-18 |
| DEC-021 | M2 | Equipment usage model | accepted | TBD | 2026-03-18 |
| DEC-022 | M2 | Material pricing rule | accepted | TBD | 2026-03-18 |
| DEC-023 | M2 | Currency rounding policy | accepted | TBD | 2026-03-18 |
| DEC-024 | M2 | Tax policy | accepted | TBD | 2026-03-18 |
| DEC-025 | M2 | Overtime labor model | accepted | TBD | 2026-03-18 |
| DEC-026 | M2 | EWO approval authority | accepted | TBD | 2026-03-18 |
| DEC-027 | M2 | Post-approval edit model | accepted | TBD | 2026-03-18 |
| DEC-028 | M2 | Auth model | accepted | TBD | 2026-03-18 |
| DEC-029 | M2 | Named vs generic labor | accepted | TBD | 2026-03-18 |
| DEC-030 | M2 | Trade classification override | accepted | TBD | 2026-03-18 |
| DEC-031 | M2 | EWO calculation timing and lock | accepted | TBD | 2026-03-18 |
| DEC-032 | M2 | Django app structure and package selection | accepted | TBD | 2026-03-18 |

## Decision Template

```markdown
## DEC-XXX: <Short title>
- Status: proposed | accepted | deferred | rejected
- Milestone: M#
- Owner: <name>
- Date proposed: YYYY-MM-DD
- Date decided: YYYY-MM-DD

### Context
<What problem is being solved and why now?>

### Options considered
1. Option A
   - Pros:
   - Cons:
2. Option B
   - Pros:
   - Cons:

### Decision
<Chosen option and short rationale>

### Consequences
<Expected trade-offs, follow-up actions, and risks>

### Links
- Related milestone item: `MILESTONES.md`
- Related workflow/pipeline notes: `WORKFLOW.md`
- Related implementation PR(s): <link>
```

## Decision Records

## DEC-001: CI gate strategy
- Status: accepted
- Milestone: M1
- Owner: TBD
- Date proposed: 2026-03-13
- Date decided: 2026-03-14

### Context
Milestone 1 expects CI with linting and tests, but current CI only enforces lint/build/check gates.

### Options considered
1. Add smoke tests now and full test suites later.
   - Pros: Fast to implement; introduces test discipline immediately.
   - Cons: Limited coverage initially.
2. Block milestone until fuller backend/frontend suites are in place.
   - Pros: Stronger quality gate at baseline.
   - Cons: Slows setup and deploy readiness work.

### Decision
Adopt a phased CI gate policy:

- For Milestone 1, require the current baseline checks on every PR and `main` push:
  - backend `manage.py check`
  - backend `manage.py migrate --noinput`
  - frontend `npm run lint`
  - frontend `npm run build`
- Add smoke tests as soon as basic backend/frontend test scaffolding exists.
- Promote backend and frontend automated tests to required CI gates before Milestone 2 closeout.

This balances immediate delivery readiness with a clear, time-bound path to stronger automated quality coverage.

### Consequences
- M1 is not blocked by the absence of full test suites, but CI still enforces meaningful quality gates.
- Test implementation is now a tracked follow-up and cannot be treated as optional backlog noise.
- Branch protection should require the current CI job checks now, then be updated to include test jobs when added.
- Milestone tracking and workflow docs should continue to state current-vs-target test gate status explicitly to avoid ambiguity.

### Links
- Related milestone item: `MILESTONES.md`
- Related workflow/pipeline notes: `WORKFLOW.md`
- Related implementation PR(s): TBD

## DEC-002: Production Python/runtime pinning
- Status: accepted
- Milestone: M1
- Owner: TBD
- Date proposed: 2026-03-13
- Date decided: 2026-03-13

### Context
The project needs a production runtime strategy that is stable enough for reliable deployment, but not so rigid that normal security and patch updates become painful. Earlier discussion established Ubuntu 24.04 as the production OS target and aligned CI to Python 3.12.

### Options considered
1. Pin exact major and minor runtime versions, but allow patch updates within that line.
   - Pros: Good balance of stability and maintainability; CI and production stay aligned; security updates remain practical.
   - Cons: Requires occasional review when moving from one minor line to another.
2. Track newest available runtime versions aggressively.
   - Pros: Fast access to new features and improvements.
   - Cons: Higher deployment risk; more surprises from dependency compatibility changes.
3. Pin exact full versions for everything for long periods.
   - Pros: Maximum reproducibility.
   - Cons: Patch and security maintenance becomes heavier; drift accumulates if updates are postponed too long.

### Decision
Use a stable LTS-style runtime baseline in production:

- Ubuntu Server 24.04 LTS
- Python 3.12.x for backend runtime and CI
- Node 22.x LTS for frontend build/runtime tooling
- PostgreSQL pinned by major version on the server once installed

Allow patch-version updates within the pinned major/minor line after CI passes. Revisit major or minor version upgrades intentionally, not implicitly.

### Consequences
- CI should stay aligned to Python 3.12 and Node 22.
- Server provisioning and deploy docs should reference Ubuntu 24.04 and these runtime targets.
- Production should avoid unplanned jumps to new Python or Node minor/major lines.
- Runtime upgrades become explicit maintenance decisions and should result in a new decision entry or an update to this one.

### Links
- Related milestone item: `MILESTONES.md`
- Related workflow/pipeline notes: `WORKFLOW.md`
- Related implementation PR(s): TBD

## DEC-010: Dropbox integration strategy
- Status: accepted
- Milestone: M6
- Owner: TBD
- Date proposed: 2026-03-13
- Date decided: 2026-03-14

### Context
The company already uses Dropbox and wants integration options investigated for document workflows. The app is also introducing material evidence uploads and finished EWO PDF packages, so integration boundaries should be defined early without blocking core delivery.

### Options considered
1. Direct Dropbox API integration for import/export in v1.
   - Pros: Native workflow alignment for users already on Dropbox.
   - Cons: OAuth/token/security complexity early in the project.
2. Shared-folder/manual ingest workflow for v1, defer API automation.
   - Pros: Lower implementation risk; keeps focus on core EWO workflow.
   - Cons: More manual steps and weaker automation.
3. No Dropbox support in v1, revisit after core stability.
   - Pros: Simplest path to reliable baseline release.
   - Cons: Does not address immediate team workflow preference.

### Decision
Do not include Dropbox integration in v1. Revisit it after the core EWO workflow is stable and after document workflows are proven useful enough to justify extra integration complexity.

### Consequences
- Dropbox is not part of baseline or v1 acceptance criteria.
- The project avoids early OAuth, token storage, and sync/source-of-truth complexity.
- If revisited later, first validate whether the practical benefit is import, export, shared-folder convenience, or no integration at all.

### Links
- Related milestone item: `MILESTONES.md`
- Related workflow/pipeline notes: `WORKFLOW.md`
- Related implementation PR(s): TBD

## DEC-011: v1 EWO minimum context
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-14
- Date decided: 2026-03-14

### Context
The spreadsheet review showed a richer domain of customer -> job -> job site -> location, but the first product slice needs a simpler starting point so the team can create EWOs without over-modeling the entire job hierarchy too early.

### Options considered
1. Require full `Customer`, `Job`, `JobSite`, and optional `WorkLocation` models before allowing EWO creation.
   - Pros: Stronger relational structure from the start.
   - Cons: Slower path to first working workflow; more assumptions made before the process is refined.
2. Start v1 with a job-number reference on the EWO and defer the richer job hierarchy.
   - Pros: Faster delivery; leaves room to refine relationships after more discovery.
   - Cons: Later migration work will be needed when richer models are introduced.

### Decision
For v1, only the job number needs to be tracked on the EWO. Full `Job`, `Customer`, `JobSite`, and location models are deferred until the workflow is clearer.

### Consequences
- The initial schema can stay smaller and focused on EWO creation.
- A future milestone should introduce the richer job/customer hierarchy with a migration plan.
- v1 forms and APIs should avoid pretending the full relationship model already exists.

### Links
- Related milestone item: `MILESTONES.md`
- Related workflow/pipeline notes: `WORKFLOW.md`
- Related implementation PR(s): TBD

## DEC-012: People model boundary
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-14
- Date decided: 2026-03-14

### Context
The project uses “people” in three different ways: application users, labor tracked on the work, and customer-side contacts. Combining them too early would create confusion between authentication, costing, and customer relationship data.

### Options considered
1. Use a single person model for users, labor, and customer contacts.
   - Pros: Fewer tables initially.
   - Cons: Blurs important business distinctions and complicates permissions and costing.
2. Keep separate concepts for application users, tracked labor, and customer contacts.
   - Pros: Cleaner boundaries; easier to reason about auth vs costing vs customer communication.
   - Cons: Slightly more design work up front.

### Decision
Treat these as separate concepts. In v1, include only application users and tracked labor, and do not intermingle them. Customer-side contacts are deferred until customer/job features are added.

### Consequences
- Authentication design can stay separate from labor costing.
- Labor records can evolve around rate and trade rules without being constrained by auth-user requirements.
- Customer contact modeling becomes a later, explicit addition rather than accidental scope creep.

### Links
- Related milestone item: `MILESTONES.md`
- Related workflow/pipeline notes: `WORKFLOW.md`
- Related implementation PR(s): TBD

## DEC-013: Material evidence and PDF feature boundary
- Status: accepted
- Milestone: M6
- Owner: TBD
- Date proposed: 2026-03-14
- Date decided: 2026-03-14

### Context
Document evidence and finished PDF packages are valuable capabilities, but the first release should stay focused on getting the core EWO workflow correct. The team also clarified that supporting material PDFs are optional rather than mandatory.

### Options considered
1. Include material PDF uploads and finished EWO PDF package generation in v1.
   - Pros: More complete document workflow from the start.
   - Cons: Adds file handling, storage, validation, and PDF composition complexity before the base workflow is proven.
2. Defer document uploads and finished PDF packaging until after v1, while keeping them in the longer-term product direction.
   - Pros: Keeps v1 focused; reduces implementation and infrastructure risk.
   - Cons: Document-backed workflows arrive later.

### Decision
Do not require PDF upload capability in v1, and do not make final EWO PDF package composition part of v1. When the document workflow is added later, supporting material evidence remains optional, and the long-term goal is to let users choose what elements are included in the final PDF output.

### Consequences
- File upload, file validation, and PDF packaging are deferred from baseline delivery.
- Milestones and setup docs should not treat document workflow as a blocker for v1 completion.
- The future document feature should preserve optionality rather than forcing evidence on every material line.

### Links
- Related milestone item: `MILESTONES.md`
- Related workflow/pipeline notes: `WORKFLOW-SETUP.md`
- Related implementation PR(s): TBD

## DEC-014: Rate precedence and history
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-14
- Date decided: 2026-03-14

### Context
Rates may come from maintained tables and later manual or updated entries. The system needs a predictable rule for what rate is active, while still preserving how rates changed over time.

### Options considered
1. Keep one mutable current rate and overwrite older values.
   - Pros: Simple implementation.
   - Cons: Loses history and weakens auditability.
2. Treat the latest entry as active while preserving prior rate history.
   - Pros: Clear operational rule with audit trail.
   - Cons: Requires historical rate storage/query design.

### Decision
The latest rate entry is the rate used for new work. The system should preserve past rates for at least `Equipment` and `LaborTrade` records.

### Consequences
- Rate models should support historical records rather than destructive overwrite only.
- UI and APIs should make it clear which rate is current versus historical.
- This works together with EWO submission snapshots so later rate changes do not rewrite prior work.

### Links
- Related milestone item: `MILESTONES.md`
- Related workflow/pipeline notes: `WORKFLOW-SETUP.md`
- Related implementation PR(s): TBD

## DEC-015: Submitted EWO rate snapshot behavior
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-14
- Date decided: 2026-03-14

### Context
Global labor and equipment rates will change over time. Submitted work needs pricing stability so approved or reviewable EWOs remain defensible even after source rates are updated.

### Options considered
1. Always recalculate EWO line items from the latest global rates.
   - Pros: Uses the newest pricing automatically.
   - Cons: Historical EWOs can change unexpectedly and become hard to defend.
2. Snapshot applied rates onto the EWO when it is submitted.
   - Pros: Preserves historical accuracy and supports auditability.
   - Cons: Requires explicit snapshot fields/data model.

### Decision
The rate used when an EWO is submitted becomes the rate for that EWO. Later global rate changes do not alter the submitted record.

### Consequences
- EWO line items need snapshot values stored at submission time.
- Edit/lock rules should specify whether resubmission creates a new snapshot or preserves the old one.
- Reporting must distinguish historical EWO pricing from currently active rate tables.

### Links
- Related milestone item: `MILESTONES.md`
- Related workflow/pipeline notes: `WORKFLOW-SETUP.md`
- Related implementation PR(s): TBD

## DEC-016: v1 EWO lifecycle baseline
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-14
- Date decided: 2026-03-18

### Context
The product will likely expand beyond Extra Work Orders into cost analysis or estimate-style outputs, but the first implementation still needs a concrete EWO lifecycle so validations, permissions, and edit-lock behavior can be designed coherently.

### Options considered
1. Delay lifecycle definition until multiple document types are modeled.
   - Pros: Avoids rework if broader workflows arrive quickly.
   - Cons: Leaves current EWO behavior underspecified.
2. Define a focused v1 lifecycle now and expand later if the product grows into additional document types.
   - Pros: Gives immediate clarity for workflow, permissions, and locking.
   - Cons: May need later extension.

### Decision
v1 EWO lifecycle: `open → submitted → approved → sent → billed`, with `rejected → open` for corrections.

State semantics:
- `open` — actively being built; lines editable
- `submitted` — sent to PM for review; lines locked; rates snapshotted
- `approved` — PM has approved; ready to send to GC (GC submission happens outside the system)
- `rejected` — PM has rejected; reopens to `open` for correction
- `sent` — EWO has been transmitted to the GC via external means (email, GC portal)
- `billed` — included in a pay application

Post-approval edits use a revision model: original approved EWO is locked permanently; a revision is a new EWO record with `parent_ewo` FK and `revision` integer field (0 = original, 1 = first revision, etc.). EWO number carries a decimal suffix: `1886-001.1`. Revisions go through the full lifecycle same as originals (see DEC-027).

### Consequences
- Role and edit-lock rules can now be defined against concrete states.
- APIs and UI flows should reflect this state machine explicitly.
- Future document types should extend the workflow deliberately rather than overloading EWO status semantics.
- The `rejected` state does not appear in the forward path — it is a branch back to `open`.

### Links
- Related milestone item: `MILESTONES.md`
- Related workflow/pipeline notes: `WORKFLOW-SETUP.md`
- Related implementation PR(s): TBD

## DEC-017: Document storage strategy
- Status: proposed
- Milestone: M6
- Owner: TBD
- Date proposed: 2026-03-14
- Date decided: TBD

### Context
Document upload support is deferred from v1, but the team has already identified that materials may eventually need supporting PDFs and finished EWO packages. Storage strategy should be decided before implementation begins.

### Options considered
1. Store uploaded files on VPS local media first.
   - Pros: Simpler initial implementation; no extra cloud service dependency.
   - Cons: Harder future scaling and durability concerns; backups become more coupled to the app host.
2. Abstract storage from day one and target object storage when document features are implemented.
   - Pros: Better long-term flexibility and separation of concerns.
   - Cons: More upfront design and setup complexity before the document workflow is even proven.

### Decision
TBD after a focused pros/cons review closer to document-feature implementation.

### Consequences
- The project does not need to commit to a document storage backend for baseline or v1.
- Before implementing uploads, choose the storage approach together with backup, retention, access control, and final PDF packaging needs.

### Links
- Related milestone item: `MILESTONES.md`
- Related workflow/pipeline notes: `WORKFLOW-SETUP.md`
- Related implementation PR(s): TBD

## DEC-003: Source of truth and calculation boundary
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-14
- Date decided: 2026-03-18

### Context
EWO line totals, OH&P, and the final total must be calculated somewhere. The boundary choice affects auditability, frontend complexity, and what the database stores as authoritative.

### Options considered
1. Always recalculate from live rate tables on every request.
   - Pros: No stored totals to go stale.
   - Cons: Submitted EWOs would change if rates change; no audit-stable record.
2. Calculate client-side (React) and POST the totals.
   - Pros: Responsive UI.
   - Cons: Server cannot trust posted numbers; requires validation duplication.
3. Recalculate server-side on status transition (`open → submitted`); lock thereafter.
   - Pros: One authoritative calculation path; snapshots are stable; audit-safe.
   - Cons: Totals not available until submission; open EWO shows no stored total.

### Decision
Recalculate on status transition (option 3). When an EWO transitions from `open` to `submitted`, `calculate_ewo_totals(ewo)` runs once, writes all snapshot values and computed totals to the EWO record, and the EWO locks. All money math lives in `ewo/services.py` — never in views or serializers. After submission, stored values are the record; no recalculation ever touches a submitted EWO.

### Consequences
- `ewo/services.py` is the single calculation boundary; test it exhaustively with `freezegun`.
- Open EWOs do not have stored totals — the UI can compute a live preview client-side for display only.
- Rate changes after submission never affect the record.

### Links
- Related milestone item: `MILESTONES.md`
- Related decision: DEC-031

## DEC-018: EWO numbering format
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
EWOs need a human-readable reference number that ties them to a job and maintains order within that job.

### Decision
EWO number = job number + hyphen + zero-padded 3-digit sequence per job (e.g. `26E-001`, `1886-003`). Sequence is per-job, auto-incremented at creation, atomic to prevent race conditions. Model also carries optional reference fields: `rfi_reference`, `addendum_ref`, `plan_revision`.

### Consequences
- Sequence counter must be incremented atomically (e.g. `select_for_update` or database sequence).
- Display format for revisions appends decimal suffix: `1886-001.1` (see DEC-027).

### Links
- Related decision: DEC-027

## DEC-019: Job number validation format
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
The company uses two distinct job number formats that must both be accepted by the system.

### Decision
Two job categories:
- **Regular jobs:** sequential integer, no padding (e.g. `1886`, `42`). Validation: `^\d+$`
- **Small/misc jobs:** 2-digit year + sequential letter(s) starting at A, continuing to AA, AB, AC when year exceeds 26 entries (e.g. `26A`, `26AA`). Validation: `^\d{2}[A-Z]+$`

### Consequences
- Job number field stores as a string; validation enforces one of the two formats.
- No auto-generation of job numbers — entered by PM or office staff.

### Links
- Related milestone item: `MILESTONES.md`

## DEC-020: Labor hours precision
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
Field labor is typically tracked by the half hour in this trade. Full minute precision is unnecessary and adds complexity to rate calculations.

### Decision
Labor stored in half-hour increments only. Field: `DecimalField(decimal_places=1)`. Valid values are multiples of 0.5. Validation: `(value * 2) == int(value * 2)`.

### Consequences
- Applies to `reg_hours`, `ot_hours`, and `dt_hours` on `LaborLine`.
- UI should enforce half-hour steps (e.g. 0.5 increment spinner).

### Links
- Related decision: DEC-025

## DEC-021: Equipment usage model
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
Caltrans rates include three distinct billing modes: operating (rental rate), standby/delay (rw_delay rate), and overtime (rental + ot adder). The data model must capture which mode is being billed on each line.

### Decision
Equipment usage is time-based only — no quantity field. Each `EquipmentLine` has a `usage_type` field:
- `operating` — bills at `rental_rate`
- `standby` — bills at `rw_delay_rate`
- `overtime` — bills at `rental_rate + overtime_rate`

Standby/delay time is a separate `EquipmentLine` record with `usage_type = 'standby'`, not a field on the working line.

### Consequences
- One equipment line per usage type per day per piece of equipment.
- All three Caltrans rate components (`rental_rate`, `rw_delay_rate`, `overtime_rate`) must be snapshotted at submission.

### Links
- Related decision: DEC-015, DEC-031

## DEC-022: Material pricing rule
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
Simple rule needed for how material line totals are calculated, with no ambiguity for edge cases like lump-sum invoices.

### Decision
Material line total is always `unit_cost × quantity`. No manual total override. Lump-sum items use unit type `LS` with quantity `1` and the full invoice amount as `unit_cost`. No special cases.

### Consequences
- No `total_override` field needed on `MaterialLine`.
- Tax handling: if a material receipt includes sales tax, the full invoice amount (tax included) is entered as the `unit_cost` on an `LS` line (see DEC-024).

### Links
- Related decision: DEC-024

## DEC-023: Currency rounding policy
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
Money calculations on EWOs accumulate across many line items, OH&P markups, and a bond add-on. A consistent rounding rule must be established to prevent fractional-cent accumulation and ensure predictable billing totals.

### Decision
Round UP to the nearest cent (`decimal.ROUND_UP`) at every point where a calculation occurs: line totals, OH&P amounts, bond amount, and final total. No fractional cents ever carry forward. Use `decimal.ROUND_UP` throughout `ewo/services.py`. Never use float arithmetic on currency.

### Consequences
- All currency fields use `DecimalField`.
- `ewo/services.py` applies `ROUND_UP` at each calculation step, not just at the final total.
- This slightly favors the contractor (rounds up), which is appropriate for billing.

### Links
- Related decision: DEC-003

## DEC-024: Tax policy
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
The company performs installed construction work, not product sales. Tax handling must be defined to avoid adding unnecessary complexity.

### Decision
Tax is excluded entirely from the system. CP performs installed work — no sales tax on billings. If a material receipt includes sales tax, the full invoice amount (tax included) is entered as the `unit_cost` on an `LS` line. The system never acknowledges tax as a concept.

### Consequences
- No tax fields, tax rates, or tax line items anywhere in the data model.
- Receipts with embedded tax are handled at the line level by the person entering materials.

### Links
- Related decision: DEC-022

## DEC-025: Overtime labor model
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
Field work regularly spans regular time, overtime, and double time in a single day. The model must capture all three without forcing artificial splitting into separate records.

### Decision
Single `LaborLine` per worker per day with three hour fields: `reg_hours`, `ot_hours`, `dt_hours`. Standard thresholds (OT after 8 reg hours, DT after 4 OT hours) are NOT auto-calculated — the person entering labor knows where in the workday the extra work fell and enters the correct breakdown manually.

Each time type is calculated independently, rounded per DEC-023, then summed to line total. Three rate snapshots stored at submission: `rate_reg_snapshot`, `rate_ot_snapshot`, `rate_dt_snapshot`.

### Consequences
- `LaborLine` has 6 critical fields: `reg_hours`, `ot_hours`, `dt_hours`, `rate_reg_snapshot`, `rate_ot_snapshot`, `rate_dt_snapshot`.
- UI must show all three time-type inputs without requiring all to be filled.
- Line total = `(reg_hours × rate_reg) + (ot_hours × rate_ot) + (dt_hours × rate_dt)`, each component rounded before summing.

### Links
- Related decision: DEC-020, DEC-023

## DEC-026: EWO approval authority
- Status: accepted
- Milestone: M2 / M4
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
EWOs must be reviewed before being sent to the GC. Approval authority and dual-approval requirements must be defined before building the state machine.

### Decision
PM role only has approval authority in v1. Single approval is sufficient — no dual approval. "Approved" means the EWO is ready to send to the GC; it does not mean the GC has accepted it. GC submission happens outside the system via email or the GC's own portal.

### Consequences
- Role matrix for M4 must grant `approve` and `reject` actions to PM role only.
- Foreman and office roles cannot approve.
- The `sent` state (EWO transmitted to GC) is tracked separately from `approved` (see DEC-016).

### Links
- Related decision: DEC-016

## DEC-027: Post-approval edit model
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
Approved EWOs occasionally need correction after approval. A strategy is needed that preserves the audit trail while allowing corrections.

### Options considered
1. Reopen and edit the approved EWO directly.
   - Pros: Simple.
   - Cons: Destroys the audit record; original approved version is lost.
2. Clone to a revision; lock original.
   - Pros: Original is preserved; revision has its own lifecycle.
   - Cons: Slightly more model complexity.
3. Admin override with audit reason.
   - Pros: Keeps single record.
   - Cons: Muddies the immutable record principle.

### Decision
Revision model with decimal suffix. Original approved EWO is locked permanently and never edited. A revision is a new `ExtraWorkOrder` record linked to its parent via a `parent_ewo` FK, with all lines cloned as a starting point. `revision` integer field: 0 = original, 1 = first revision, etc. EWO display number: `1886-001.1`, `1886-001.2`. Revisions go through the full lifecycle the same as original EWOs.

### Consequences
- `ExtraWorkOrder` needs `parent_ewo` FK (nullable, self-referential) and `revision` integer field.
- Locking logic must prevent any edits to EWOs in `approved` state or later.
- Reporting should identify the "current" revision of a given EWO chain.

### Links
- Related decision: DEC-016, DEC-018

## DEC-028: Auth model
- Status: accepted
- Milestone: M2 / M4
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
Django provides a built-in User model. Custom AppUser models add complexity; the alternative is to extend via a profile model.

### Options considered
1. Custom `AppUser` swapping out Django's `AUTH_USER_MODEL`.
   - Pros: Full control over user fields.
   - Cons: Requires setting `AUTH_USER_MODEL` before first migration; hard to change later; unnecessary for v1 needs.
2. Django built-in `User` + one-to-one `UserProfile`.
   - Pros: Standard pattern; avoids auth model swap complexity; easy to extend.
   - Cons: Two models instead of one.

### Decision
No custom AppUser. Extend Django's built-in `User` with a one-to-one `UserProfile`:

```python
class UserProfile(models.Model):
    user   = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role   = models.CharField(max_length=50)  # 'foreman', 'pm', 'office', 'admin'
    active = models.BooleanField(default=True)
```

`ExtraWorkOrder.created_by` points to Django `User` directly.

### Consequences
- No `AUTH_USER_MODEL` setting needed; Django default applies.
- Role-based access control in M4 reads from `UserProfile.role`.

### Links
- Related decision: DEC-026

## DEC-029: Named vs generic labor
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
EWOs are sometimes built from actual crew records (named labor) and sometimes from estimates or placeholders (generic labor). The model must support both without requiring an employee record for every line.

### Decision
`LaborLine` supports two labor types via a `labor_type` field:
- `named` — specific employee; `employee` FK populated
- `generic` — placeholder for estimating or T&M where the specific crew member isn't known; `employee` FK null

One line per worker per day always — no quantity field on labor lines.

### Consequences
- `employee` FK on `LaborLine` is nullable.
- Rate lookup for generic lines requires `trade_classification` to be specified directly.
- Generic labor is valid in both T&M and change order EWOs.

### Links
- Related decision: DEC-030

## DEC-030: Trade classification override
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
Employees normally bill under their default trade classification, but field conditions sometimes require billing under a different classification (e.g. an Operator Foreman acting as Superintendent for the day). The override must be auditable.

### Decision
Lock to employee's default trade classification but allow override per line with a required reason. `LaborLine` carries:
- `employee_default_trade` FK — snapshot of employee's trade at line creation (denormalized; protects against future employee record changes rewriting history)
- `trade_classification` FK — the trade actually billed (may differ from default)
- `trade_override_reason` — required when the two differ, blank otherwise

The `is_trade_override` property returns `True` when `trade_classification != employee_default_trade` for named labor lines.

### Consequences
- `employee_default_trade` is set automatically on save from the employee record when `labor_type = 'named'`.
- UI must surface an override reason field when the user selects a non-default trade.

### Links
- Related decision: DEC-029

## DEC-031: EWO calculation timing and lock
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
This is the implementation detail for DEC-003's accepted approach: when exactly calculations run, what gets stored, and how the lock is enforced.

### Decision
On `open → submitted` transition:
1. `calculate_ewo_totals(ewo)` runs once in `ewo/services.py`
2. All rate snapshots and computed totals are written to the EWO record atomically
3. EWO status becomes `submitted`; lines and totals lock — no further edits permitted

Required service functions in `ewo/services.py`:
- `get_labor_rate(trade_classification, work_date)`
- `get_equipment_rates(caltrans_rate_line, work_date)`
- `calculate_labor_line(line)`
- `calculate_equipment_line(line)`
- `calculate_material_line(line)`
- `calculate_ewo_totals(ewo)` — labor subtotal, labor OH&P, equip+mat subtotal, equip+mat OH&P, bond, total

After submission, stored values are the permanent record. Rate changes, CBA negotiations, and Caltrans schedule updates never affect a submitted EWO.

### Consequences
- Write `ewo/services.py` and test it exhaustively with `freezegun` before building any views or serializers.
- The transition function must wrap snapshot + status change in a single database transaction.
- Open EWO total is not stored — the UI shows a live preview computed client-side for display only.

### Links
- Related decision: DEC-003, DEC-015, DEC-023

## DEC-032: Django app structure and package selection
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
Before writing any models, the Django project needs a stable app boundary layout and a confirmed package set. App structure is expensive to change after migrations exist.

### Decision

**App structure — 4 apps:**

| App | Responsibility | Models |
|-----|---------------|--------|
| `accounts` | User extension and role management | `UserProfile` |
| `resources` | All reference/master data — the building blocks that populate EWOs | `TradeClassification`, `LaborRate`, `Employee`, `CaltransSchedule`, `CaltransRateLine`, `EquipmentType`, `EquipmentUnit`, `MaterialCategory`, `MaterialCatalog` |
| `jobs` | Job reference; lightweight v1, future home for customer/job hierarchy | `Job` |
| `ewo` | EWO transactions and calculation logic | `ExtraWorkOrder`, `LaborLine`, `EquipmentLine`, `MaterialLine`, `services.py` |

Dependency direction: `ewo` imports from `resources`, `jobs`, `accounts`. No reverse imports.

**Package selection:**

Installed for M2:
- `djangorestframework` — API endpoints
- `django-cors-headers` — cross-origin requests from React frontend
- `drf-spectacular` — OpenAPI schema generation from serializers
- `django-simple-history` — audit trail on key models (added at model definition time, not retrofitted)
- `django-import-export` — CSV import for Caltrans rate schedule and employee seed data
- `pytest-django` — test runner (CI gate before M2 closeout per DEC-001)
- `model-bakery` — test fixture generation
- `freezegun` — freeze time for rate effective-date tests
- `django-extensions` — dev tooling (`shell_plus`, etc.)
- `django-debug-toolbar` — SQL query inspection during development

Deferred to M4:
- `djangorestframework-simplejwt` — JWT auth; not needed until auth milestone

Explicitly rejected:
- `django-money` — single-currency (USD) app; `MoneyField` overhead not justified; rounding policy enforced in `ewo/services.py` per DEC-023
- `django-environ` — already using `python-dotenv` with custom helpers in `settings.py`
- `psycopg2-binary` — already on psycopg3 (`psycopg` + `psycopg-binary`), which is newer and preferred

### Consequences
- All 4 apps created before any model code is written.
- `django-simple-history` `HistoricalRecords()` added to models at definition time — not retrofitted.
- `ewo/services.py` is the only file that performs currency arithmetic; all `DecimalField` currency fields use `max_digits=10, decimal_places=2`.

### Links
- Related decisions: DEC-003, DEC-011, DEC-028, DEC-031
