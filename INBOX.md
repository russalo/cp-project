# INBOX.md
## Purpose
Raw capture file. Dump ideas here during any session.
The nightly local LLM job processes and routes items.
Never delete directly - items are cleared by the processing script.

## Unprocessed Items

### 2026-04-17 — Fleetlocate GPS integration (equipment ground truth)

CP subscribes to Fleetlocate for equipment GPS tracking. Sample CSV export
dropped in scratch (`Assets 2026-04-17 06-48-33.csv`) shows a point-in-time
snapshot of 109 tracked assets with these relevant columns:

- `Name` — CP fleet number + model (e.g. "B-27 446B" = backhoe #27, CAT
  446B). This is the key users already know by heart.
- `Serial Number` — Fleetlocate tracker device ID (AS7214… pattern).
- `Asset Type` — Equipment (67), Vehicle-Medium Duty (22), Vehicle-Light
  Duty (10), Vehicle-Heavy Duty (9), Trailer (1).
- `Address` / `Location` — free-text; the `Location` field carries a
  useful "cp geo- ADDRESS" prefix suggesting CP has geofences defined.
- `Latitude` / `Longitude` — populated on 108/109.
- `Engine Hours` — lifetime meter (populated on 103/109). **This is the
  highest-value field** for auto-populating WorkDay equipment hours via
  day-over-day deltas.
- `Last Report Date` / `Reporting Status` — 13 assets not reporting.
- `Odometer / Total Mileage` — for vehicles.

**Use cases this unlocks:**
1. **EquipmentUnit population** — the dormant `EquipmentUnit` model
   (DEC-069) is now meaningful. `EquipmentUnit.internal_code` = CP fleet
   number ("B-27"), linked to `EquipmentType` (CAT 446B backhoe catalog
   entry). Each EquipmentUnit gets a `fleetlocate_serial` mapping so
   follow-on syncs can update engine hours and location by device ID.
2. **Auto-populate WorkDay equipment** — "Fleetlocate shows these 6
   units were at this jobsite on this date; one tap each to add to the
   WorkDay with suggested hours from the engine-hour delta."
3. **Integrity check** — flag EquipmentLines where FL says the unit was
   not on-site during the claimed hours.
4. **Catch missed bills** — surface equipment that was on a jobsite but
   never got logged on an EWO.
5. **Time-on-site evidence** for challenged claims.

**Scoping questions to answer before designing a model:**
- CSV export frequency — is this a manual download or can it be
  scheduled? Does FL offer a REST API?
- Historical trip data — does FL retain GPS tracks back months, or
  does the portal only show recent reporting? (The asset CSV is
  point-in-time; trip history is a separate export.)
- Geofence model — are the "cp geo-" entries defined once per jobsite
  address, or per-project? How do they change over a job's life?
- Rented vs owned — are rented/short-term units in FL at all, or only
  CP-owned?
- Sync cadence — how stale can data be and still be useful? Nightly is
  probably enough; real-time is overkill.

**The compounding evidentiary value** (2026-04-17 brainstorm): GPS
lat/lon answers "was the machine there"; engine-hour deltas answer "was
it actually running, and for how long." Combined, an EWO claim is
backed by timestamped, tamper-resistant business records — admissible
under federal / most-state rules of evidence. The practical effect is a
**flipped burden of proof**: today CP has to justify a contested EWO;
with GPS + engine-hour records, the GC has to explain any discrepancy.
Secondary wins: standby-vs-operating proof from whether the engine ever
turned over, foreman protection when memory fails, reconstruction
for late-notice claims.

**Mechanic's roster (`scratch/equipment roster  9-29-23 (1) (1).xlsx`)**:
User's internal equipment-tracking spreadsheet. Nine sheets, 483 rows
on the main `Equipment Roster` tab, plus overlays for AQMD, tier status,
fuel pins, market value, etc. Shares the A-/B-prefix fleet-number
convention with Fleetlocate — key insight for reconciliation.

**Reconciliation prerequisite** (user-stated, 2026-04-17): *"1st order
of business would be to reconcile our mechanic's equipment list,
Fleetlocate's list with ours and Caltrans."* Do NOT start building the
ingest or auto-populate before this reconciliation exists as a
single-source-of-truth table showing every unit across all four
sources with match status + discrepancy flags. Building on mismatched
catalogs creates silent bugs.

**Design constraint** (user, 2026-04-17): *"we'd have to add these
things so that they are easily added, retrievable but not hold up
actual use."* Any FL/mechanic-list integration must be additive — new
fields are nullable, never required; enrichment appears as overlay
context in the UI, never in the hot path. See the
`feedback_additive_not_blocking` memory entry for application rules.

**Quick next step (Phase 5-ish, no specific DEC yet):** a read-only
reconciliation report (`manage.py reconcile_equipment`) that takes the
three CSV/XLSX sources and produces one merged sheet for the user to
eyeball. Once that sheet is clean, a second command populates
`EquipmentUnit` records from the reconciled data. Only then does an FL
ingest or auto-populate UI become worth wiring.

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
- **Quote-mode field applicability** (user, 2026-04-17): on a quote,
  `work_date` and `weather` don't apply — you're pricing future work
  that hasn't happened. Two plausible model shapes:
    * quote-type EWO has WorkDays with nullable `work_date` +
      "Day N of N" label until promoted (Q14 option (a) from the
      original design session)
    * quote-type EWO has no WorkDays; line items live directly on the
      EWO; promoting to actual structures them into WorkDays
      (Q14 option (b))
  This needs the bigger Sandbox/EWE/EWO call to settle first.

Captured 2026-04-17 during the Phase 3 iPad/phone walkthrough.
