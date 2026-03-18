# HOMEWORK BATCH 002 — ARCHIVE

Answered: 2026-03-18
Folded into DECISIONS.md: 2026-03-18 (DEC-018 through DEC-027)

---

1. **EWO numbering strategy:** should EWO IDs be sequential globally, per customer,
   or per job number?
   - Answer: EWO number = job number + zero-padded 3-digit sequence per job
     (e.g. `26E-001`, `1886-003`). Sequence is per-job, auto-incremented on creation,
     atomic to prevent race conditions when multiple PMs work the same job.
     Model also carries optional reference fields: `rfi_reference`, `addendum_ref`,
     `plan_revision`.
   - Decision: DEC-018

2. **Job number validation:** what format rules should v1 enforce for job number
   entry (required prefix/length/characters)?
   - Answer: Two job categories with distinct formats.
     Regular jobs: sequential integer, no padding (e.g. `1886`, `42`). Currently
     at 1886, started from 1 in the late 1950s.
     Small/misc jobs: 2-digit year + sequential letter(s) starting at A, continuing
     to AA, AB, AC etc. when year exceeds 26 (e.g. `26A`, `26AA`). Used for
     emergency repairs and one-off work.
     Validation regex: regular = `^\d+$`, small = `^\d{2}[A-Z]+$`.
   - Decision: DEC-019

3. **Labor unit policy:** should labor be captured in hours only, or support
   hour + minute precision in v1?
   - Answer: Half-hour increments only. Store as `DecimalField(decimal_places=1)`.
     Valid values are multiples of 0.5. Validate that `(value * 2) == int(value * 2)`.
   - Decision: DEC-020

4. **Equipment quantity model:** should equipment usage be time-based only,
   quantity-based only, or both with explicit unit types?
   - Answer: Time-based only — hours or days depending on the item. No quantity
     field on equipment lines. Standby/delay time is a separate `EquipmentLine`
     with `usage_type = 'standby'` rather than a field on the working line.
     `usage_type` choices: `operating` (rental_rate), `standby` (rw_delay_rate),
     `overtime` (rental_rate + ot_rate).
   - Decision: DEC-021

5. **Material pricing entry rule:** should materials default to unit cost × quantity,
   with optional manual total override?
   - Answer: Always `unit_cost × quantity`, no manual override. Lump sum is handled
     as unit type `LS` with quantity `1`. No special cases needed.
   - Decision: DEC-022

6. **Rounding policy detail:** where should rounding occur (line item, category
   subtotal, final total), and to how many decimals?
   - Answer: Round UP to the nearest cent (`ROUND_UP`) at every line where a
     calculation occurs — line totals, OH&P amounts, bond amount, final total.
     No fractional cents ever carry forward. Use `decimal.ROUND_UP` throughout
     `services.py`. Never use float arithmetic on currency.
   - Decision: DEC-023

7. **Tax policy boundary:** should tax be excluded from v1, optional per EWO,
   or required per material line category?
   - Answer: Tax excluded entirely. CP performs installed work, not product sales —
     no sales tax on billings. If a material receipt includes tax, the full invoice
     amount (tax included) is entered as the unit cost on an `LS` line. The system
     never acknowledges tax as a concept.
   - Decision: DEC-024

8. **Overtime modeling:** should overtime be represented as separate labor line
   types or a multiplier on standard labor lines?
   - Answer: Single `LaborLine` with three hour fields: `reg_hours`, `ot_hours`,
     `dt_hours`. Standard thresholds: OT after 8 reg hours, DT after 4 OT hours —
     but the system does NOT auto-calculate the split. The person entering labor
     knows where in the workday the extra work fell and enters the correct breakdown
     manually. Each time type is calculated independently and rounded per Q6, then
     summed to line total. Three rate snapshots stored: `rate_reg_snapshot`,
     `rate_ot_snapshot`, `rate_dt_snapshot`.
   - Decision: DEC-025

9. **Approval authority:** which role is allowed to approve/reject EWOs in v1,
   and is dual-approval needed?
   - Answer: PM role only. Single approval sufficient. No dual approval in v1.
     "Approved" means ready to send to the GC — not that the GC has accepted it.
     GC submission happens outside the system via email or GC's own system.
     Full lifecycle: `open → submitted → approved → sent → billed`, with
     `rejected → open` for corrections.
   - Decision: DEC-026

10. **Post-approval edits:** if an approved EWO must change, should it reopen,
    clone to revision, or require admin override with audit reason?
    - Answer: Revision iteration with decimal suffix — `1886-001.1`, `1886-001.2`.
      Original approved EWO is locked permanently, never edited. A revision is a
      new EWO record linked to its parent via `parent_ewo` FK, with all lines cloned
      as a starting point. `revision` field: 0 = original, 1 = first revision, etc.
      Revisions go through the full lifecycle same as originals.
    - Decision: DEC-027
