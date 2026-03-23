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

| ID | Milestone | Topic | Status | Date | Summary |
|---|---|---|---|---|---|
| DEC-001 | M1 | CI gate strategy | accepted | 2026-03-14 | Lint/build/check gates now; backend tests before M2 closeout |
| DEC-002 | M1 | Production Python/runtime pinning | accepted | 2026-03-13 | Pin Python 3.12.x, Node 22.x, PostgreSQL major; allow patch updates |
| DEC-003 | M2 | Source of truth and calculation boundary | accepted | 2026-03-18 | Server-only in `ewo/services.py`; never in views, serializers, or client |
| DEC-004 | M2 | API contract conventions | proposed | TBD | Error format, pagination, filtering style, versioning — to be decided |
| DEC-005 | M2 | Duplicate-prevention/idempotency approach | proposed | TBD | EWO creation idempotency strategy — to be decided |
| DEC-006 | M3 | TypeScript migration strategy | proposed | TBD | Big-bang vs incremental TS migration — to be decided in M3 |
| DEC-007 | M4 | Auth architecture (mechanism) | proposed | TBD | Session cookies vs JWT — to be decided in M4; see also DEC-028 |
| DEC-008 | M5 | Deployment strategy | proposed | TBD | Git pull on host vs artifact/release deployment — to be decided |
| DEC-009 | M5 | Rollback model | proposed | TBD | Previous-commit checkout vs release-symlink switch — to be decided |
| DEC-010 | M6 | Dropbox integration strategy | accepted | 2026-03-14 | Deferred to M6 or post-v1; no Dropbox in v1 |
| DEC-011 | M2 | v1 EWO minimum context | accepted | 2026-03-14 | Store job number only; defer Customer/Job/Site modeling to post-v1 |
| DEC-012 | M2 | People model boundary | accepted | 2026-03-14 | Field crew as name strings; no relational Person model in v1 |
| DEC-013 | M6 | Material evidence and PDF feature boundary | accepted | 2026-03-14 | PDF upload/output deferred to M6 |
| DEC-014 | M2 | Rate precedence and history | accepted | 2026-03-14 | Latest LaborRate/CaltransRateLine effective on or before work_date wins |
| DEC-015 | M2 | Submitted EWO rate snapshot behavior | accepted | 2026-03-14 | All rate components snapshotted at submission; immutable thereafter |
| DEC-016 | M2 | v1 EWO lifecycle baseline | accepted | 2026-03-14 | open→submitted→approved→sent→billed; rejected→open for corrections |
| DEC-017 | M6 | Document storage strategy | proposed | TBD | Where to store PDF attachments — to be decided before M6 upload work |
| DEC-018 | M2 | EWO numbering format | accepted | 2026-03-18 | `{job_number}-{3-digit-seq}`; revisions use decimal suffix `.1`, `.2` |
| DEC-019 | M2 | Job number validation format | accepted | 2026-03-18 | Regular: `^\d+$`; small/misc: `^\d{2}[A-Z]+$` |
| DEC-020 | M2 | Labor hours precision | accepted | 2026-03-18 | `DecimalField(decimal_places=1)`; half-hour increments; reg/OT/DT fields |
| DEC-021 | M2 | Equipment usage model | accepted | 2026-03-18 | Time-based only; `usage_type` = operating/standby/overtime; no quantity |
| DEC-022 | M2 | Material pricing rule | accepted | 2026-03-18 | Always `unit_cost × quantity`; LS unit = qty 1; no manual total override |
| DEC-023 | M2 | Currency rounding policy | accepted | 2026-03-18 | `decimal.ROUND_UP` to nearest cent at every calculation point; no float |
| DEC-024 | M2 | Tax policy | accepted | 2026-03-18 | Tax excluded from system; receipts with embedded tax entered as LS lines |
| DEC-025 | M2 | Overtime labor model | accepted | 2026-03-18 | Single LaborLine per worker per day with reg/OT/DT hour fields |
| DEC-026 | M2 | EWO approval authority | accepted | 2026-03-18 | PM role only; single approval; "approved" = ready to send to GC |
| DEC-027 | M2 | Post-approval edit model | accepted | 2026-03-18 | Revision with decimal suffix; original locked; revision goes full lifecycle |
| DEC-028 | M2 | Auth model (data layer) | accepted | 2026-03-18 | Django built-in User + one-to-one UserProfile; no custom AUTH_USER_MODEL |
| DEC-029 | M2 | Named vs generic labor | accepted | 2026-03-18 | LaborLine supports named (Employee FK) or generic (labor_type string) |
| DEC-030 | M2 | Trade classification override | accepted | 2026-03-18 | Override allowed on LaborLine with required reason field |
| DEC-031 | M2 | EWO calculation timing and lock | accepted | 2026-03-18 | Calculations run at open→submitted; atomic with select_for_update |
| DEC-032 | M2 | Django app structure and package selection | accepted | 2026-03-18 | Four apps: accounts, jobs, ewo, resources; simple-history, DRF, drf-spectacular |
| DEC-033 | M4 | Role permissions matrix | accepted | 2026-03-18 | Foreman/PM/Office/Admin role matrix defined for all EWO actions |
| DEC-034 | M2 | Sent status fields | accepted | 2026-03-18 | sent_date, sent_by, sent_method, sent_reference on ExtraWorkOrder |
| DEC-035 | M2 | GC acknowledgment fields | accepted | 2026-03-18 | gc_acknowledged_by/at/method as metadata; absence is itself recordable |
| DEC-036 | M2 | Billed status definition and fields | accepted | 2026-03-18 | billed = included in pay app; pay_app_reference, billed_date, billed_by |
| DEC-037 | M2 | Multi-date EWOs | accepted | 2026-03-18 | EWO can span multiple dates; work_date lives on each line, not the header |
| DEC-038 | M2 | Employee CSV seed format | accepted | 2026-03-18 | CSV via django-import-export; template at resources/seed/employees_template.csv |
| DEC-039 | M2 | Equipment type seed approach | accepted | 2026-03-18 | Caltrans schedule → CSV → admin import; committed at resources/seed/ |
| DEC-040 | M2 | Job CRUD ownership | accepted | 2026-03-18 | PM and Office create/edit/deactivate jobs; Foreman read-only |
| DEC-041 | M2 | EWO description field structure | accepted | 2026-03-18 | Two fields: location (CharField) + description (TextField); both required at submission |
| DEC-042 | M2 | Audit log visibility | accepted | 2026-03-18 | All authenticated users can read history; admin-only for Django admin history view |
| DEC-043 | post-v1 | Daily report feature | deferred | TBD | Full daily report module deferred post-v1 |
| DEC-044 | post-v1 | Crew builder feature | deferred | TBD | Crew builder/template feature deferred post-v1 |

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

## DEC-007: Auth architecture (mechanism)
- Status: proposed
- Milestone: M4
- Date proposed: 2026-03-13

### Context
DEC-028 (M2, accepted) settled the user data model: Django built-in `User` + one-to-one
`UserProfile`. This decision addresses the *mechanism*: how client requests prove identity to
the API — session cookies vs. token/JWT.

### Options considered
1. Django session-based auth — browser cookie managed by Django's session framework.
   - Pros: Standard for same-origin SPAs; built into Django; no token refresh logic needed.
   - Cons: Stateful; requires session store consideration at scale.
2. JWT (djangorestframework-simplejwt) — stateless tokens returned at login.
   - Pros: Stateless; better suited for mobile or multi-origin deployments; standard for SPA+API separation.
   - Cons: Requires access/refresh token rotation; token revocation is non-trivial.

### Decision
Deferred to M4. DEC-028's `User + UserProfile` choice is compatible with both options — no
custom `AUTH_USER_MODEL` means simplejwt or session auth can be added without model changes.

### Consequences
- No auth implementation until M4; current API endpoints are unauthenticated in development.
- Whichever mechanism is chosen, `UserProfile.role` (from DEC-028) is the single source of
  permissions truth (role matrix: DEC-033).

### Links
- Complements DEC-028 (auth data model — accepted)
- Related: DEC-033 (role permissions matrix)

## DEC-010: Dropbox integration strategy
- Status: accepted
- Milestone: M6
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
- Pending decision: DEC-007 (auth mechanism — session vs JWT; to be resolved in M4). DEC-028
  settles the *data model* layer; DEC-007 will settle the *request authentication* mechanism.
  The two decisions are complementary: `User + UserProfile` is compatible with both session
  auth and JWT without model changes.

## DEC-029: Named vs generic labor
- Status: accepted
- Milestone: M2
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
| `ewo` | EWO transactions and calculation logic | `ExtraWorkOrder`, `WorkDay`, `LaborLine`, `EquipmentLine`, `MaterialLine`, `services.py` |

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

## DEC-033: Role permissions matrix
- Status: accepted
- Milestone: M4
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
Before building any permission checks, view guards, or API authorization, the exact set of allowed
actions per role must be defined. DEC-026 established PM-only approval authority; this decision
extends that to a full matrix covering all lifecycle transitions and data management actions.

### Decision
Four roles (foreman, pm, office, admin) with the following permissions:

| Action                                   | foreman | pm | office | admin |
|------------------------------------------|---------|----|--------|-------|
| Create EWO                               | ✓       | ✓  | ✓      | ✓     |
| Edit lines on own open EWO               | ✓       | ✓  | ✓      | ✓     |
| Edit lines on any open EWO               | —       | ✓  | ✓      | ✓     |
| Submit EWO (open → submitted)            | ✓       | ✓  | ✓      | ✓     |
| Approve EWO (submitted → approved)       | —       | ✓  | —      | ✓     |
| Reject EWO (submitted → open)            | —       | ✓  | —      | ✓     |
| Mark sent (approved → sent)              | —       | ✓  | ✓      | ✓     |
| Mark billed (sent → billed)              | —       | —  | ✓      | ✓     |
| Manage reference data                    | —       | —  | ✓      | ✓     |
| Manage users / UserProfile               | —       | —  | —      | ✓     |
| Read any EWO                             | ✓       | ✓  | ✓      | ✓     |
| View audit history                       | ✓       | ✓  | ✓      | ✓     |

### Consequences
- Permission checks in M4 read from `UserProfile.role` (per DEC-028).
- "Edit any open EWO" is given to PM and office to allow data entry assistance for foremen.
- Foreman cannot approve, reject, or advance past `submitted`.
- Office does not approve or reject — that responsibility remains with PM only.

### Links
- Related decisions: DEC-026, DEC-028, DEC-016

## DEC-034: Sent status fields
- Status: accepted
- Milestone: M2
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
When an EWO is marked `sent`, the system should capture how it was transmitted to the GC
for audit and follow-up purposes. DEC-016 defines the `sent` state; this decision defines
what data is collected at that transition.

### Decision
Four fields on `ExtraWorkOrder`, all nullable, populated atomically on `approved → sent`:
- `sent_date` — DateField, auto-set to today
- `sent_by` — FK to `User`, auto-set to current user
- `sent_method` — CharField choices: `email` / `gc_portal` / `hand_delivered` / `other`
- `sent_reference` — CharField optional (email thread subject, portal confirmation number, etc.)

No separate model. PM and office roles can trigger this transition (per DEC-033).

### Consequences
- `sent_method` is required on the transition form — the user must choose one option.
- `sent_reference` is optional; leave blank if no reference number exists.

### Links
- Related decisions: DEC-016, DEC-033

## DEC-035: GC acknowledgment fields
- Status: accepted
- Milestone: M2
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
The shared project guidance explicitly requires: "GC acknowledgment tracked per EWO: who, when,
method (signature/email/verbal) — absence is itself recordable." This is distinct from the `sent`
state — it tracks the GC's receipt/acknowledgment of the EWO, not CP's act of sending it.

### Decision
Three fields on `ExtraWorkOrder` as metadata (not a lifecycle state):
- `gc_acknowledged_by` — CharField (name string per DEC-012; not a User FK)
- `gc_acknowledged_at` — DateTimeField nullable
- `gc_acknowledgment_method` — CharField choices: `signature` / `email` / `verbal` / `none_recorded`

An EWO can be `sent` with `gc_acknowledgment_method = 'none_recorded'` — absence is explicitly
recordable. Fields are editable by PM and office after the `sent` transition.

### Consequences
- These fields are not part of the state machine; they can be updated at any time after `sent`.
- `gc_acknowledged_by` is a free-text name, not a FK, consistent with DEC-012 (people as name strings in v1).
- `none_recorded` is a valid, intentional choice — not a null/unknown.

### Links
- Related decisions: DEC-016, DEC-012, DEC-033

## DEC-036: Billed status definition and fields
- Status: accepted
- Milestone: M2
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
DEC-016 defines `billed` as included in a pay application, but did not specify what data to
capture at that transition or what the pay application reference should look like.

### Decision
`billed` = included in a pay application. The `sent → billed` transition is triggered by office
or admin only (per DEC-033). Fields populated atomically on transition:
- `billed_date` — DateField, auto-set to today
- `billed_by` — FK to `User`, auto-set to current user
- `pay_app_reference` — CharField optional (e.g. "PA-14", "March 2026 Pay App")

No payment-received tracking in v1 — that is an accounting system concern outside this app.

### Consequences
- `pay_app_reference` is optional; some offices may track pay app numbers, others may not.
- Payment confirmation, lien waivers, and AR tracking are explicitly out of scope for v1.

### Links
- Related decisions: DEC-016, DEC-033

## DEC-037: Multi-date EWOs and WorkDay model
- Status: accepted
- Milestone: M2
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
T&M extra work often spans multiple consecutive days. The printed EWO output has one page per
calendar day (with that day's specific work description, crew, and equipment) plus a summary cover
page. This output structure drives the data model — day-level grouping is a first-class concept.

### Decision
Introduce a `WorkDay` model as the grouping unit between `ExtraWorkOrder` and line items:

```
ExtraWorkOrder  (cover page — summary description, totals)
  └── WorkDay   (one per calendar date — date-specific location + description + lines)
        ├── LaborLine
        └── EquipmentLine
MaterialLine    (stays at EWO level — not tied to a specific day)
```

`WorkDay` fields:
- `ewo` — FK to `ExtraWorkOrder`
- `work_date` — DateField required
- `location` — CharField (where the work occurred that day)
- `description` — TextField (what was done that day)

`LaborLine` and `EquipmentLine` FK to `WorkDay` (not directly to `ExtraWorkOrder`).
`MaterialLine` FK remains directly on `ExtraWorkOrder`.

`ExtraWorkOrder` header carries a summary `description` (TextField) for the cover page.
No `ewo_date` header field — the date range is derived from `WorkDay.work_date` values.

### Consequences
- `work_date` lives on `WorkDay`, not on individual `LaborLine`/`EquipmentLine` records.
- Rate lookup uses `WorkDay.work_date` to find the effective rate per DEC-014.
- Both `WorkDay.location` and `WorkDay.description` are required at submission (optional while open).
- Printed output: cover page from EWO header; one page per `WorkDay` ordered by `work_date`.
- `WorkDay` is in the `ewo` app (DEC-032) alongside the line models.

### Links
- Related decisions: DEC-014, DEC-025, DEC-041

## DEC-038: Employee CSV seed format
- Status: accepted
- Milestone: M2
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
The `Employee` model (in the `resources` app per DEC-032) needs to be populated before EWOs with
named labor can be created. The company already has employee/trade data in an Excel rate sheet —
the seed import should draw from that source.

### Decision
Source: existing Excel rate sheet. CSV columns for employee seed import via `django-import-export`:
- `employee_id` — optional internal identifier string; blank = auto-assign
- `first_name` — required
- `last_name` — required
- `default_trade_code` — required; must match a `TradeClassification.code` already in the system
- `union` — required; choices: `IUOE` / `LIUNA` / `OPCMIA` / `IBT`

A blank template is committed at `backend/resources/seed/employees_template.csv`. Import runs via
the Django admin `django-import-export` mixin on the `Employee` model admin.

### Consequences
- `TradeClassification` records must be seeded before the employee CSV import runs.
- The template CSV must be filled out by PM or office before the first data load.
- Employee photos, phone numbers, and other HR fields are not in scope for v1.

### Links
- Related decisions: DEC-012, DEC-029, DEC-032

## DEC-039: Equipment type seed approach
- Status: accepted
- Milestone: M2
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
`CaltransRateLine` records (in the `resources` app per DEC-032) are the source for equipment billing
rates. The Caltrans Equipment Rental Rate schedule is published periodically as a PDF table. An import
approach is needed before equipment lines can be added to EWOs.

### Decision
Convert the relevant pages of the Caltrans schedule to CSV (one-time manual step). Import via
`django-import-export` admin action on `CaltransRateLine`. CSV committed at
`backend/resources/seed/caltrans_rates_<year>.csv`.

CSV columns:
- `schedule_year` — e.g. `2025`
- `class_code` — Caltrans equipment class identifier
- `make` — manufacturer name
- `model` — model description
- `rental_rate` — operating rate (Rental_Rate column in Caltrans schedule)
- `rw_delay_rate` — standby rate (Rw_Delay column)
- `overtime_rate` — overtime adder (Overtime column)
- `effective_date` — start date of this rate period

Only the Caltrans codes CP actively uses are included in the initial seed — a filtered subset of
the full schedule. PM or office provides the list of active codes before the seed file is built.

### Consequences
- Full Caltrans schedule import is not required — targeted subset only.
- New rate periods (annual Caltrans updates) are imported the same way as new CSV rows.
- `django-import-export` is already selected in DEC-032; no new package needed.

### Links
- Related decisions: DEC-014, DEC-021, DEC-032

## DEC-040: Job CRUD ownership
- Status: accepted
- Milestone: M2
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
DEC-011 established a lightweight `Job` model (job number only in v1). The access pattern for who
can create and manage jobs must be defined before building the jobs app.

### Decision
PM and office roles can create, edit, and deactivate `Job` records. Foreman is read-only (can select
a job when creating an EWO but cannot create or modify jobs). Admin has full access.

Jobs are entered manually in-app — job numbers come from the estimating/bidding process outside this
system. No external sync in v1. `Job` model fields:
- `job_number` — validated per DEC-019
- `job_name` — CharField optional (free-text description)
- `active` — BooleanField default True; deactivation hides the job from new-EWO dropdowns without deleting it

### Consequences
- Job creation permission gates match the office/PM split from DEC-033.
- Soft deactivation (not deletion) prevents orphaning EWOs tied to a job number.
- Future job hierarchy (customer, site, location per DEC-011) extends this model rather than replacing it.

### Links
- Related decisions: DEC-011, DEC-019, DEC-033

## DEC-041: EWO description field structure
- Status: accepted
- Milestone: M2
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
The printed EWO has a summary cover page and one page per work day. Each day's page must carry
a description of that day's specific work. This means description is a two-level concept:
a summary at the EWO header (cover page) and a day-specific narrative at the `WorkDay` level.

### Decision
Description lives at two levels:

**On `WorkDay`** (drives each day's printed page):
- `location` — CharField (where the work occurred that day; e.g. "Sta. 42+00, south trench wall")
- `description` — TextField (what was done that day and why it qualifies as extra work)
- Both required at submission; optional while EWO is open.

**On `ExtraWorkOrder` header** (drives the cover page):
- `description` — TextField (summary of the overall extra work scope)
- `location` — CharField optional (general area; often redundant with WorkDay locations)
- Header `description` required at submission.

No `reason_for_extra` field in v1 — justification context goes in `description` at the day level.

### Consequences
- UI must present per-day description entry alongside line item entry for each `WorkDay`.
- Cover page summary `description` is a separate input at the EWO header level.
- `location` CharField max length TBD at implementation (suggest 200 chars).

### Links
- Related decisions: DEC-016, DEC-037

## DEC-042: Audit log visibility
- Status: accepted
- Milestone: M2
- Date proposed: 2026-03-18
- Date decided: 2026-03-18

### Context
`django-simple-history` is already committed to (DEC-032) and will be applied to key models at
definition time. The access policy for who can read the history trail must be decided before
building the history API endpoint.

### Decision
All authenticated users can read the `django-simple-history` trail for any EWO they can view.
History records are read-only for all roles. The Django admin history interface is restricted to
admin only.

### Consequences
- The history API endpoint applies the same object-level read permission as the EWO itself —
  if you can read the EWO, you can read its history.
- No separate permission check is needed for history vs. EWO reads.
- Admin-only Django admin history is the default `django-simple-history` behavior; no override needed.

### Links
- Related decisions: DEC-032, DEC-033

## DEC-043: Daily report feature
- Status: deferred
- Milestone: post-v1
- Date proposed: 2026-03-18
- Date decided: TBD

### Context
Foremen currently track daily field activity (crew, hours, equipment, and notes) outside the system.
A future Daily Report feature would let foremen log this directly, pulling from the employee and
equipment database, and flag any work as "extra" — creating or linking to an EWO. This mirrors the
EWO `WorkDay` structure closely: one report per calendar date, with labor lines, equipment lines,
and a narrative.

### Deferred because
Core EWO workflow must be stable and in production use before adding a parallel data entry workflow.
The exact relationship between daily reports and EWOs (flag → auto-draft vs. manual link) needs
discovery with foremen users before being designed.

### V1 model constraints to preserve this option
- `Employee` and `EquipmentUnit` in the `resources` app must not be designed in a way that prevents
  their reuse as the population source for daily report lines.
- `WorkDay` field names (`work_date`, `location`, `description`, `LaborLine`, `EquipmentLine`)
  should be named consistently with what a daily report day will look like — these may share a
  common base structure or simply maintain consistent naming conventions.
- The EWO → job relationship must stay clean enough for a daily report entry to reference a job
  and generate an EWO stub.

### Population mechanisms (resolved 2026-03-18)
Two fast-entry paths for foremen, both producing an editable starting point:

1. **Apply a saved crew** — foreman or PM has pre-built a crew for the job (see DEC-044);
   applying it pre-fills the day's labor and equipment lines. Foreman then adds or removes
   what is different for that day.

2. **Copy from previous workday** — for daily reports in particular, the system can
   auto-populate lines by copying the most recent workday entry for the same job. Foreman
   adjusts the delta. This is the primary fast-entry path when the crew hasn't changed.

Both mechanisms produce editable lines, not locked records. The foreman is always the one
who confirms and submits the final daily entry.

### Escalation flow (resolved 2026-03-18)
When a foreman flags a daily report entry as "extra work", it escalates to a PM for review.
The PM decides whether to create an EWO from it. The foreman does not create the EWO directly.

Implied model requirements:
- Daily report entries need an `extra_work_flag` boolean and an `escalated_to_pm_at` timestamp.
- A PM review queue or notification mechanism is needed (design TBD).
- Once the PM acts, the daily report entry should carry either a FK to the resulting
  `ExtraWorkOrder` (if approved) or a `dismissed_at` / `dismissed_by` record (if rejected).

### Open questions (resolve before implementation)
- Are daily report labor/equipment lines separate model records, or do they reuse `LaborLine`/`EquipmentLine`?
- Is the daily report a separate app or part of `ewo`?
- What happens to daily report records that are never flagged as extra — are they retained for payroll reference?
- How does the PM review queue surface — dashboard widget, email notification, or both?
- **"Copy from previous workday" UX — requires formal pros/cons review before implementation:**
  silent clone (lines appear pre-filled, foreman edits) vs. preview/diff view (foreman confirms
  what is being carried forward before lines are written). Do not implement without a decision.

### Links
- Related decisions: DEC-037, DEC-044

## DEC-044: Crew builder feature
- Status: deferred
- Milestone: post-v1
- Date proposed: 2026-03-18
- Date decided: TBD

### Context
Foremen work with largely consistent crews day to day. A Crew Builder would let them define a
named crew (a set of employees and equipment units) once, then apply that crew to a daily report
or EWO `WorkDay` to pre-populate the labor and equipment lines — reducing repetitive data entry.

### Deferred because
The core data entry workflow must be usable before optimizing it with crew shortcuts.
The right UX for applying a crew (replace all lines vs. append vs. diff) needs user testing.

### V1 model constraints to preserve this option
- `Employee` and `EquipmentUnit` in `resources` must be designed to support a future `Crew` M2M
  relationship. Do not add fields or constraints that would make a `Crew` → `Employee` through-table
  awkward (e.g. avoid composite unique constraints on employee fields that would conflict with
  crew membership).
- A `Crew` model will live in the `resources` app alongside `Employee` and `EquipmentUnit`.
- v1 should not hard-code "one employee, one trade" assumptions that would prevent a crew from
  carrying mixed-trade rosters.

### Clarifications (resolved 2026-03-18)
- **Purpose:** Crews are a population mechanism — a saved starting point, not a locked template.
  Applying a crew pre-fills the day's labor and equipment lines; the foreman then adds or removes
  what is different for that specific day. Speed of adjustment, not exact repeatability, is the goal.
- **Job association:** Crews are typically built around a specific job ("the usual crew for job 1886").
  A crew should carry a reference to the job it was built for, though applying it to a different
  job should not be blocked.
- **Who can build crews:** Both foreman and PM can create and edit crew definitions.
- **Apply behavior:** Applying a crew replaces the current empty day lines with the crew's roster
  as a starting point. If lines already exist, the UI should confirm before overwriting.
- **No schedule:** A crew is a membership list (employees + equipment units) with no date or
  schedule attached — it is purely a template for population.

### Open questions (resolve before implementation)
- Are crews job-specific (one crew per job) or can multiple named crews exist per job?
- Is the `Crew` model in `resources` or in the future `dailyreport` app?
- What happens to a crew definition when an employee leaves or equipment is retired?

### Links
- Related decisions: DEC-029, DEC-032, DEC-043
