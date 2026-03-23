# Session Summary — cp-project
**Date:** March 18, 2026  
**Machine:** RUSS-DELL-LAPTOP  
**Status:** cp-project not cloned on this machine — artifacts produced for manual commit

---

## What This Session Covered

1. Desktop Commander capability overview
2. CHARTER.md full revision — grounded in real EWO artifacts
3. Data model design — iterated to v3 ERD
4. Package and technology recommendations
5. Architectural decisions documented

All output files are in this conversation's download panel:
- `CHARTER.md` — full revised charter
- `cp_project_full_erd.html` — ERD v3, standalone, opens in any browser

---

## CHARTER.md — What Changed

The charter was rewritten from an engineering spec into a document that tells the
real story of the problem. Key additions:

**"The Immediate Value of a Unified Database" section (new)**
The database itself — before any features — solves the version control problem.
No more hunting for the current Excel file. One place, one version, visible to all.
This is day-one value before a single workflow feature is built.

**"The Current Process" section (new)**
Grounded in how EWOs actually get built today:
- Excel files, one per EWO, scattered across local machines / network drives / email
- No guarantee anyone is working from the same version
- People cross-check against external data points because they already know they
  can't trust the file
- Data entry is not unified and is repeated across multiple files

**Two EWO workflow types — explicitly named**
- Reactive T&M — work happens first, paperwork follows. Foreman often doesn't know
  it's T&M. Weeks later someone reconstructs from memory — "an act of creative
  writing fiction." This is the core failure mode.
- Proactive change order — quote first, approval, then work. Still manual and
  fragmented but more controlled.

**Problem statement — four risk areas**
Missed revenue, disputes (GC has leverage with weak records), slow billing,
no shared truth.

**"What the Data Model Must Capture" section (new)**
Grounded in the actual Excel EWO file (26E_T_M_3-6-26.xlsx) and the Caltrans
rate schedule (2025_2026.csv).

**Rate authority section — two distinct sources**
- Equipment rates: Caltrans published schedule, annual cycle, three rate components
  per record (rental, rw_delay, overtime)
- Labor rates: Union CBAs, negotiated independently per union on their own cycle
  (IUOE, LIUNA, OPCMIA, IBT)
- Both require versioning with effective dates and snapshotting at EWO submission

**Markup structure — from actual Excel EWO**
- Labor subtotal → +15% OH&P on labor
- Equipment + materials subtotal → +15% OH&P on equip/mat
- Bond: 1% optional, per EWO in v1, project-level in future
- 15% is the contractor law default — adjustable per EWO, applied rate stored
  on the record not derived at report time

**Guiding principles updated**
Added: "The database is the product" and "Build the model right, then populate it"

---

## Data Model — Full Decision Log

### ERD Version History
- v1 — initial model
- v2 — Django User + UserProfile, named vs generic labor, trade override
- v3 — EquipmentType/Unit split, ownership flag, MaterialCatalog with categories

### Auth — AppUser → Django User + UserProfile

**Decision:** No custom AppUser model. Extend Django's built-in User with a
one-to-one UserProfile.

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50)  # 'foreman', 'pm', 'office', 'admin'
    active = models.BooleanField(default=True)
```

`ExtraWorkOrder.created_by` points to `User` directly (Django convention).

---

### Labor — Named vs Generic

**Decision:** `LaborLine` supports two labor types via a `labor_type` field.

```python
NAMED   = 'named'   # specific employee — employee FK populated
GENERIC = 'generic' # placeholder for estimating — employee FK null
```

**One line per worker-day always** — no quantity field on labor lines.
Generic labor is used for estimating and T&M placeholders where the specific
crew member isn't known or recorded.

---

### Labor — Trade Classification Override

**Decision:** Lock to employee's default trade classification, but allow override
per line with a required reason.

`LaborLine` carries:
- `employee` FK (nullable — null for generic)
- `employee_default_trade` FK — snapshot of employee's trade at time of line
  creation (denormalized intentionally — protects against future employee record
  changes rewriting history)
- `trade_classification` FK — the trade actually billed (may differ from default)
- `trade_override_reason` — required when the two differ, blank otherwise

The `employee_default_trade` is set automatically on save from the employee record
when labor_type is named. The audit trail reads: "Person X normally runs as
Operator Foreman, billed as Superintendent this day — reason: acting super while
regular super was off site."

```python
@property
def is_trade_override(self):
    if self.labor_type == self.GENERIC:
        return False
    if not self.employee_default_trade:
        return False
    return self.employee_default_trade_id != self.trade_classification_id
```

---

### Rate Tables — Two Source Authorities

**Labor rates — Union CBAs**

`TradeClassification` is the permanent reference (name, union, abbreviation).
`LaborRate` is the versioned rate record — new row per CBA negotiation cycle,
never edit old rows.

```python
class LaborRate(models.Model):
    trade_classification = models.ForeignKey(TradeClassification, on_delete=models.PROTECT)
    rate_reg  = models.DecimalField(max_digits=8, decimal_places=2)
    rate_ot   = models.DecimalField(max_digits=8, decimal_places=2)
    rate_dt   = models.DecimalField(max_digits=8, decimal_places=2)
    effective_date = models.DateField()
    expiry_date    = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=200, blank=True)
```

Rate lookup pattern:
```python
def get_labor_rate(trade_classification, work_date):
    return LaborRate.objects.filter(
        trade_classification=trade_classification,
        effective_date__lte=work_date
    ).order_by('-effective_date').first()
```

**Equipment rates — Caltrans schedule**

`CaltransSchedule` — one row per annual publication (currently April expiry cycle).
`CaltransRateLine` — 2,164 records from 2025_2026.csv across 60 equipment classes
and 174 makes.

Three rate components per line (all potentially billable):
- `rental_rate` — standard operating rate (per hour)
- `rw_delay_rate` — right-of-way standby/delay rate (per hour)
- `overtime_rate` — overtime adder (per hour, added on top of rental rate — not
  a multiplier)

Import: annual re-import when Caltrans publishes. Composite natural key:
`schedule + class_code + make_code + model_code`. Old rate lines stay intact —
existing EWO snapshots are never touched.

---

### Equipment — EquipmentType / EquipmentUnit Split

**Decision:** Separate the rate reference from the individual fleet unit.

`EquipmentType` — maps a category of equipment to a Caltrans rate line.
Shared across all individual units of that type.
Example: "Ford F-250 Pickup" → Caltrans Code 06-12

`EquipmentUnit` — individual unit in CP's fleet. 30 trucks = 30 rows, all
pointing to the same EquipmentType.

**Ownership flag on EquipmentUnit:**
- `owned` — CP fleet
- `rented` — from a rental yard
- `outside` — subcontractor / third party

Ownership flag is **informational only** — not a billing mode switch.

**Billing logic:**
- All equipment on an `EquipmentLine` bills at Caltrans published rate regardless
  of ownership source
- Rented equipment where CP receives an invoice → goes to `MaterialLine`
  (not EquipmentLine) with the invoice cost as unit cost
- Outside/subcontractor equipment → also goes to `MaterialLine` as a
  subcontractor cost

**EWO equipment lines reference EquipmentType only** — no unit-level tracking
needed on the EWO. Unit registry exists for fleet management, not for billing.

---

### Equipment — Data Management

- **Employees:** One-time CSV seed, then CRUD only
- **Caltrans rates:** Annual CSV re-import (upsert by natural key)
- **EquipmentType / EquipmentUnit:** CRUD via admin

CP does not own every piece of equipment used. The fleet model needs to handle
all three ownership categories.

---

### Materials — MaterialCatalog

**Decision:** Company-wide price book that grows organically from field entries
and is maintained by office staff. Not per-job, but same-job items surface first
in the UI.

```python
class MaterialCategory(models.Model):
    name   = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)

class MaterialCatalog(models.Model):
    category       = models.ForeignKey(MaterialCategory, null=True, blank=True, ...)
    description    = models.CharField(max_length=200, unique=True)
    default_unit   = models.CharField(max_length=50)
    last_unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    last_cost_date = models.DateField(null=True, blank=True)
    use_count      = models.IntegerField(default=0)
    last_used      = models.DateField(null=True, blank=True)
    is_boilerplate = models.BooleanField(default=False)
    active         = models.BooleanField(default=True)
```

`is_boilerplate` distinguishes pre-seeded items from field-generated ones.
`last_cost_date` lets office staff see stale prices during catalog maintenance.

**Preferred that we know the real price.** The catalog is a price reference,
not just an autocomplete convenience. Office staff maintain it independently
of EWO entry.

**Boilerplate categories to seed at launch:**
- Bedding material (sand, gravel, crushed rock, import fill)
- Asphalt (3/4", 1/2", cold mix, tack coat)
- Concrete (ready-mix, slurry/CDF, flowable fill)
- Traffic control consumables (cones, delineators, no-parking signs, arrow board)
- Shoring / plating (trench plate, shoring box, hydraulic shores, plywood)

**Not pre-populated:** Pipe and fittings — these are typically owner-furnished
or contract-bid items. When they appear on a T&M EWO it's usually from an actual
invoice, so real cost is entered fresh.

**MaterialLine** carries `is_subcontractor` and `reference_number` to handle
outside equipment invoices and rental invoices that land in materials.

**Materials are added at the EWO level** — not pre-entered, not batch managed.
Previous and frequently used items are suggested from the catalog.

---

### EWO Cost Calculation — Architectural Decision

**Decision: Recalculate on status transition (option 3)**

Lines are editable while EWO is `open`. When EWO transitions to `submitted`:
1. `calculate_ewo_totals(ewo)` runs once
2. All snapshot values and computed totals are written to the EWO record
3. EWO locks — no further edits to lines or totals

After submission, stored values are the record. No recalculation ever touches
a submitted EWO. Rate changes, CBA negotiations, Caltrans updates — none of
these affect a submitted EWO.

All money math lives in `ewo/services.py`, never in views or serializers:

```python
# ewo/services.py
def get_labor_rate(trade_classification, work_date): ...
def get_equipment_rates(caltrans_rate_line, work_date): ...
def calculate_labor_line(hours, time_type, rate_snapshot): ...
def calculate_ewo_totals(ewo): ...
```

---

## Package Recommendations

### Full requirements list

```
# Core
Django>=4.2
psycopg2-binary
django-environ

# Money — non-negotiable, no floats on currency
django-money

# API
djangorestframework
djangorestframework-simplejwt
django-cors-headers
drf-spectacular

# Audit + history
django-simple-history

# Admin + data management
django-import-export
django-extensions
django-debug-toolbar

# Testing
pytest-django
model-bakery
freezegun
```

### Key package rationale

**`django-money`** — Exact decimal arithmetic on all currency fields. Python float
will corrupt calculations. Non-negotiable for a billing system.

**`django-simple-history`** — Add `HistoricalRecords()` to `ExtraWorkOrder`,
`LaborRate`, `CaltransRateLine`, `MaterialCatalog`. Every save gets a timestamped
history row. Dispute defense six months later requires showing exactly what the
record looked like at submission.

**`django-import-export`** — Admin-integrated CSV import with dry-run preview,
error reporting per row, and upsert via natural keys. Used for: Caltrans annual
re-import, one-time employee seed, one-time equipment seed.

**`drf-spectacular`** — Auto-generates OpenAPI schema from serializers. Worth
adding early when frontend and backend are built simultaneously.

**`freezegun`** — Freeze time for rate effective-date tests. Critical for testing
"given work_date=X, does the system pick the correct CBA rate?"

**`django-debug-toolbar`** — Shows SQL queries firing per request. Use to catch
N+1 issues on EWO load (labor lines + equipment lines + material lines all need
`select_related` / `prefetch_related`).

**`django.contrib.postgres`** — Already in Django, no extra install.
Use for: full-text search on material catalog autocomplete, `UniqueConstraint`
with conditions for Caltrans composite natural key.

### Not needed yet but plan for later

**`celery` + `redis`** (or `django-q2`) — Background task queue for PDF
generation. Don't build now but don't architect against it. Keep PDF generation
out of the request/response cycle.

---

## Build Order Recommendation

Start with rate foundation — everything downstream depends on it:

1. `TradeClassification`
2. `LaborRate`
3. `Employee`
4. `CaltransSchedule`
5. `CaltransRateLine` — import 2025_2026.csv immediately after
6. `EquipmentType`
7. `EquipmentUnit`
8. `MaterialCategory`
9. `MaterialCatalog` — seed boilerplate at this step
10. `Job`
11. `UserProfile` (on top of Django User)
12. `ExtraWorkOrder`
13. `LaborLine`
14. `EquipmentLine`
15. `MaterialLine`

Write and test `ewo/services.py` rate lookup logic (with freezegun tests)
before building any views or serializers.

---

## Files to Commit

These files were produced in this session and need to be committed to cp-project:

| File | Location | Action |
|------|----------|--------|
| `CHARTER.md` | repo root | Replace existing |
| `cp_project_full_erd.html` | `docs/` or `design/` | New file — v3 ERD |
| `SESSION_SUMMARY.md` | `docs/` | This file — archive then extract decisions |

Suggested commit message:
```
docs: charter revision + data model v3 ERD

- Rewrote CHARTER.md grounded in real EWO artifacts and Caltrans rate data
- Added unified database value proposition section
- Added current process narrative and two EWO workflow types
- Added full data model section: rate authorities, markup structure, GC ack
- ERD v3: Django User/UserProfile, named/generic labor, trade override,
  EquipmentType/Unit split, ownership flag, MaterialCatalog with categories
- Documented package recommendations and build order
```

---

## Open Questions / Next Session

These were not resolved and should be picked up next time:

- [ ] Confirm operating hours vs delay hours as separate inputs on EquipmentLine,
      or lump rate — the Caltrans rw_delay rate is real and billable
- [ ] Standard materials list confirmation — any pipe/fitting scenarios that
      should be in the catalog despite being typically contract items?
- [ ] Role definitions — what exactly can each role (foreman, pm, office, admin)
      see and do? Needed before building role-aware access
- [ ] EWO number format — is there a naming convention (job number + sequence,
      date-based, etc.)?
- [ ] GC acknowledgment workflow — is a digital signature needed in v1 or is
      "name + date + method" sufficient for now?

---

## Context for Next Session

- cp-project is cloned on the main dev machine, not on RUSS-DELL-LAPTOP
- GitHub is not accessible from the Claude sandbox environment — Git operations
  must be run from the local machine shell
- Desktop Commander is installed on RUSS-DELL-LAPTOP and can write files /
  run PowerShell commands locally
- Multi-machine dev workflow and GitHub Actions are already configured
- Config baseline is locked, infrastructure changes are paused
- Milestone 2 focus: backend models for Labor, Equipment, Materials
- This session's design work is the input for Milestone 2 model implementation
