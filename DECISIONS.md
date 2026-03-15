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
| DEC-003 | M2 | Source of truth and calculation boundary | proposed | TBD | TBD |
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
| DEC-018 | M2 | Web architecture boundary (DRF vs Inertia vs hybrid) | accepted | TBD | 2026-03-14 |

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
- Date decided: 2026-03-14

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
Use a v1 EWO lifecycle of `draft`, `submitted`, `approved/rejected`, and `billed`. Future support for cost analysis or estimate workflows can extend the broader product model later.

### Consequences
- Role and edit-lock rules can now be defined against concrete states.
- APIs and UI flows should reflect this state machine explicitly.
- Future document types should extend the workflow deliberately rather than overloading EWO status semantics.

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

## DEC-018: Web architecture boundary (DRF vs Inertia vs hybrid)
- Status: accepted
- Milestone: M2
- Owner: TBD
- Date proposed: 2026-03-14
- Date decided: 2026-03-14

### Context
Current milestones call for backend API endpoint implementation in M2, while recent research notes in `.github-copilot` evaluate an Inertia-style modern monolith approach that could reduce internal API boilerplate. We need a clear architecture boundary before deeper M2 implementation to avoid rework.

### Options considered
1. DRF/API-first for all web workflows.
   - Pros: Clean multi-client path for future mobile/integrations; explicit contracts; familiar Django ecosystem support.
   - Cons: More boilerplate and coordination overhead for internal web features.
2. Inertia-first for internal web UI, no DRF for internal flows.
   - Pros: Faster full-stack iteration; fewer duplicated contracts/state layers.
   - Cons: Higher coupling to server-rendered web patterns; weaker path for mobile/public API reuse.
3. Hybrid: API-first domain boundary, optional Inertia for selected internal/admin surfaces.
   - Pros: Preserves reusable API contracts while allowing faster delivery in selected UI surfaces.
   - Cons: Highest architecture discipline required; risk of inconsistent patterns without clear boundaries.

### Decision
Adopt a DRF/API-first architecture for product workflows, with a two-layer admin strategy:

- Keep Django Admin for superuser/emergency operations and internal maintenance.
- Continue delivering day-to-day product workflows in React against explicit Django API endpoints.
- Do not adopt an Inertia-first architecture for core workflow paths in v1/M2.

This preserves clear server-side boundaries for costing rules, lifecycle transitions, and auditability while keeping a practical admin surface for operations.

### Consequences
- `DEC-003`, `DEC-004`, and `DEC-005` should be finalized using an API-first boundary as the baseline.
- API contracts remain the primary integration surface for current web workflows and future client expansion.
- Admin modernization can proceed independently (for example, UI theming/enhancements) without changing core product architecture.
- Inertia is not blocked forever, but any future adoption should be scoped to a clearly bounded surface and documented as a new decision.

### Links
- Related milestone item: `MILESTONES.md`
- Related workflow/pipeline notes: `WORKFLOW.md`
- Related implementation PR(s): TBD

