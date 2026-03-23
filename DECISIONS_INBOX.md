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
