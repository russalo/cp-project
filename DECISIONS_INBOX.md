# DECISIONS_INBOX.md
## Pending Design Decisions for Review

*Review these items. If approved, move to `DECISIONS.md`. If rejected or requiring modification, edit before moving.*

### Gate M2 Decisions
* **DEC-004**: API contract conventions (Pending resolution).
* **DEC-005**: Idempotency strategy (Pending resolution).
* **DEC-045**: `cp_role` placement. **Proposed:** Add `cp_role` to the `Contract` model, not `Job`, because a job can have multiple contracts. Enforce sub-only in v1 logic.
* **DEC-046**: Public Works indicator. **Proposed:** Add `is_public_works` boolean to `Job`. This is a threshold field determining the entire claims workflow.
* **DEC-047**: Contracting Party model. **Proposed:** Create a minimal `Party` model (id, name, party_type, license_number) rather than a plain text field on Contract.
* **DEC-048**: CM Presence. **Proposed:** Add `cm_present` and `cm_authority_delegated` booleans to `Contract` to drive authorization warnings.
* **DEC-049**: Authorization Gap. **Proposed:** Add `authorization_gap` boolean to `EWO`, auto-set when CM signature is present but GC directive is absent.
* **DEC-050**: Notice Tracking. **Proposed:** Add `notice_given_date` and `notice_given_to` (FK to Party) to `EWO`.
* **DEC-051**: Legal Weight computation. **Proposed:** `legal_weight` on Party should be a computed property based on `Party.role` + `Contract.cp_role`, not a stored integer.
* **DEC-052**: EWO Witness. **Proposed:** `witness` on `EWO` must be a FK to `Party`, not a name string.
* **DEC-053**: PayItem association. **Proposed:** `PayItem` should be `ForeignKey(Contract)`, not `Job`, gating the SOV importer.
* **DEC-054**: Billing Types in v1. **Proposed:** Support UNIT, LUMP_SUM, and TM on `PayItem` from day one via a `billing_type` field to prevent migration issues later.

### Future Workflow Decisions
* **DEC-055**: EWO Scenarios. **Proposed:** `EWOScenario` should be a database model (job-aware, extensible), not a hardcoded enum.
* **DEC-056**: Standby Events. **Proposed:** `StandbyEvent` should be a standalone model, completely separate from the `ExtraWorkOrder` lifecycle.
* **DEC-057**: Notice Auto-Generation. **Proposed:** Use a one-tap review and send draft, rather than a fully automatic silent send.
* **DEC-058**: Notice Email Origin. **Proposed:** All written field notices are sent from `ewo@cp.construction` via the Fedora comms server.

### EWO Build Refinements (2026-04-16 design session)
*Captured from the April 16 Excel-workbook walkthrough. These refine the existing M2 EWO schema to match the real T&M workflow and the Caltrans rental-rate methodology as practiced. Most are additive/corrective to the shipped model rather than new features.*

* **DEC-059**: Caltrans rate storage. **Proposed:** `CaltransRateLine` stores `rental_rate` + `rw_delay_factor` + `ot_factor` (source data is factors, 0.0–1.0). Standby and OT dollar rates are derived on demand. Migration: backfill factors from the currently-stored computed rates; no data loss.
* **DEC-060**: EquipmentType authoritative rates. **Proposed:** Add `rate_reg`, `rate_ot`, `rate_standby` to `EquipmentType` as the billable rates of record. `EquipmentType.caltrans_rate_line` FK becomes **nullable** — ~28% of CP's fleet has no matching Caltrans line (in-house, retired CT code, or above the largest listed model). When the CT FK is present, the ingest step copies or computes rates from the factor; when absent, rates are entered manually (in-house / Fair Market Value).
* **DEC-061**: CT match quality. **Proposed:** Add `EquipmentType.ct_match_quality` enum: `EXACT | CLOSE | NONE | RETIRED | FMV`. Documents rate provenance for claims defense — inspectors and CMs challenge equipment rates based on the quality of the Caltrans link.
* **DEC-062**: Fuel surcharge model. **Proposed:** (a) `EquipmentType.fuel_surcharge_eligible: bool` — some items don't burn fuel (attachments, hand tools, trailers). (b) `ExtraWorkOrder.fuel_surcharge_pct: Decimal` — per-EWO, situational (accounts for bid-time vs current fuel prices); default is `0` or last-used on the same Job, not a contract-level value. (c) `WorkDay.fuel_amount` computed per day as `Σ(eligible equipment line totals on that day) × EWO.fuel_surcharge_pct`. (d) **Chain B** for the billing sequence: fuel is equipment-related, so it enters the Equipment+Materials OH&P base — `OH&P_EM = (equip + mat + fuel) × equip_mat_ohp_pct`. Bond applies on top of everything.
* **DEC-063**: Job-level OH&P and bond defaults. **Proposed:** Add `Job.labor_ohp_pct` (default `0.15`), `Job.equip_mat_ohp_pct` (default `0.15`), `Job.bond_pct` (default `0.015`) — model-field defaults, editable per-Job. Snapshot onto EWO at creation (preserves history if Job defaults change later). Contract-level defaults deferred per DEC-045; interim home is `Job`.
* **DEC-064**: Per-WorkDay daily math. **Proposed:** OH&P (labor), OH&P (equip+mat), fuel surcharge, and bond dollar amounts are computed **per WorkDay** using the EWO-level percentages. `EWO.total = Σ WorkDay.day_total`. Matches current spreadsheet behavior (each daily T&M sheet rolls itself up, Summary tab sums daily totals).
* **DEC-065**: `WorkDay` child model. **Proposed:** An EWO is a single event that spans **1..N work days**. Introduce `WorkDay` with FK to `ExtraWorkOrder`. Re-parent `LaborLine`, `EquipmentLine`, `MaterialLine` from `ExtraWorkOrder` → `WorkDay`. `ExtraWorkOrder.work_date` goes away (or becomes a computed range). WorkDay fields: `work_date`, `location` (CharField, initialized from `Job.location`), `weather`, `description`, `foreman_name`, `superintendent_name`. Foreman/Supt are plain `CharField` for now; FK to `Party` deferred per DEC-047. Aligns with ARCHITECTURE.md's documented-but-unbuilt `WorkDay` and with DEC-043's `WorkDay` field-naming constraint.
* **DEC-066**: Equipment line shape. **Proposed:** `EquipmentLine` (now per-`WorkDay`) gets `qty` (PositiveSmallInteger, default 1), `reg_hours`, `ot_hours`, `standby_hours` (per-unit Decimals). `line_total = qty × (reg_hrs × rate_reg + ot_hrs × rate_ot + standby_hrs × rate_standby)`. Multiple identical units worked same hours collapse to one line (qty=3, reg=8 → "3 × 8h = 24h"); units with different hours split into separate lines. **Any equipment can log standby** — no eligibility flag needed (standby is situational: X & Y machines work the EWO, Z is idled by the EWO so Z stands by).
* **DEC-067**: EWO numbering format. **Proposed:** `ewo_number` = `"EWO-{job_number}-{nnn}"`, zero-padded 3-digit job-scoped serial. `ewo_sequence` stores the integer portion for sort/filter. Matches how the number is written on paper today.
* **DEC-068**: `cp_role` interim placement. **Proposed:** Park `cp_role` as plain `CharField(blank=True)` on `Job` until `Contract` model lands. Interim pragmatic choice that conflicts with DEC-045 (Contract-level placement). Resolution: DEC-045 supersedes DEC-068 when the `Contract` model is built; data migration at that time. Enum values TBD by user.
* **DEC-069**: `EquipmentUnit` dormancy. **Proposed:** Keep `EquipmentUnit` in the schema but leave it optional — `EquipmentLine.equipment_unit` FK remains nullable, not enforced. Revisit when ownership-based billing (pass-through on rented units vs. Caltrans rate on owned) or unit-level maintenance tracking is genuinely in scope.
* **DEC-070**: Signature capture shape (future). **Proposed:** When inspector/witness/directive capture is built, use a single `Signature` child model polymorphic across `WorkDay` and `ExtraWorkOrder` (0..N per parent). Fields: `name`, `organization`, `role`, `act_type` (`witnessed | directed | authorized | acknowledged`), `signed_date`, `method` (in-person/email/phone/digital), `notes`. Existing `gc_ack_*` fields on `ExtraWorkOrder` migrate into the table at that time. Deferred from initial build per user decision.
* **DEC-071**: Sandbox / EWE / EWO artifacts. **Status: EARMARKED — deferred.** Surfaced during walkthrough as three distinct concepts sharing shape but differing in audience and lifecycle:
    * **PM Sandbox** — internal working space, throwaway-friendly, not customer-facing; multiple what-if scenarios per Job
    * **EWE (Extra Work Estimate)** — finalized customer-facing pre-work estimate; may be approved, denied, or expire unused
    * **EWO** — actual-work claim, built from daily reports (can start directly, without an EWE)

    Three candidate model shapes:
    * **(a)** One `ExtraWorkOrder` model with a status enum that includes `SANDBOX | EWE | OPEN | …`. Single table, lines persist through transitions. Simplest schema; muddies queries and audit.
    * **(b)** Three separate models; lines snapshotted at each promotion. Cleanest audit (EWE is frozen at send, EWO may drift). More tables, more code.
    * **(c)** Shared `LineSet` referenced by thin per-stage shells; promotion forks the LineSet. Fewer tables than (b) with careful fork logic.

    Clarifying questions to resolve before choosing:
    1. Can one Job have multiple active Sandboxes simultaneously?
    2. Does an EWE always start from a Sandbox, or can a PM skip the Sandbox?
    3. Is an EWO always linked to its originating EWE when one exists (so "approved vs actual" delta is visible)?
    4. Once an EWE is sent to the customer, is it frozen forever (revisions = new EWE), or mutable?

    Simple initial build ships with a single `ExtraWorkOrder` model; this decision shapes later phases.
