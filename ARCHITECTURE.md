# ARCHITECTURE

## What This App Does

cp-project is a full-stack web application for managing Extra Work Orders (EWOs) — work performed
outside the original job contract by an underground wet utility pipeline contractor. It replaces
Excel spreadsheets and email chains with a structured workflow: capture → cost → review → bill.

---

## Backend: Django App Structure

The backend is a single Django project (`backend/config/`) split into four apps (DEC-032):

```
backend/
  config/
    settings.py       # All configuration; loaded from backend/.env via python-dotenv
    urls.py           # Root URL conf: admin, OpenAPI schema, debug toolbar
  accounts/           # App users and roles
  jobs/               # Job reference data
  ewo/                # Core EWO domain: models, services, lifecycle
  resources/          # Reference data: rates, equipment, employees, materials
  manage.py
  requirements.txt
```

### `accounts` app

Manages application users. Extends Django's built-in `User` with a one-to-one `UserProfile`
model (DEC-028). No custom `AUTH_USER_MODEL`.

```python
class UserProfile(models.Model):
    user   = OneToOneField(User)
    role   = CharField(max_length=50)   # 'foreman', 'pm', 'office', 'admin'
    active = BooleanField(default=True)
```

Role permissions matrix defined in DEC-033. Auth mechanism (session vs JWT) deferred to M4
(DEC-007).

### `jobs` app

Lightweight job reference model (DEC-011). Stores `job_number` and a name. Full
customer/job-site hierarchy is deferred to post-v1. Two job number formats accepted: plain
integer (e.g. `1886`) or two-digit year + letters (e.g. `26A`) — validated per DEC-019.

### `ewo` app

The core domain. Contains:

- **`models.py`** — `ExtraWorkOrder`, `WorkDay`, `LaborLine`, `EquipmentLine`, `MaterialLine`
- **`services.py`** — the only file that performs currency arithmetic (DEC-003)

### `resources` app

Reference data that drives rate lookups:

- `TradeClassification` + `LaborRate` — union CBA rates versioned by effective date (DEC-014)
- `CaltransSchedule` + `CaltransRateLine` — equipment rental rates (three components per line: rental, standby, overtime) (DEC-021)
- `EquipmentType` + `EquipmentUnit` — fleet catalog; units linked to Caltrans rate lines
- `Employee` — field crew; separate from app users (DEC-012)
- `MaterialCatalog` + `MaterialCategory` — optional company price book

---

## EWO Domain Models

### `ExtraWorkOrder`

Central record. Key fields:

| Field | Type | Notes |
|---|---|---|
| `ewo_number` | CharField (unique) | `{job_number}-{3-digit-seq}`; revisions: `1886-003.1` (DEC-018, DEC-027) |
| `job` | FK → Job | |
| `ewo_type` | CharField | `tm` (time-and-materials) or `change_order` |
| `status` | CharField | Lifecycle state (see below) |
| `revision` | IntegerField | 0 = original; 1+ = post-approval revision |
| `parent_ewo` | FK → self (nullable) | Set on revisions; original is NULL |
| Markup rates | DecimalFields | `labor_ohp_pct`, `equip_mat_ohp_pct`, `bond_pct`, `bond_required` — snapshotted at submission |
| Subtotals/totals | DecimalFields | NULL until submission; written atomically by `services.py` |
| Sent fields | Various | `sent_date`, `sent_by`, `sent_method`, `sent_reference` (DEC-034) |
| GC ack fields | Various | `gc_acknowledged_by/at/method` — absence is recordable (DEC-035) |
| Billed fields | Various | `billed_date`, `billed_by`, `pay_app_reference` (DEC-036) |

History tracked via `django-simple-history`.

### `LaborLine`

One record per worker per day (DEC-025). Supports named (Employee FK) or generic (labor type
string) labor (DEC-029).

Key fields: `work_date`, `employee` (nullable FK), `labor_type`, `trade_classification` (FK,
overridable with reason per DEC-030), `reg_hours`, `ot_hours`, `dt_hours`
(`DecimalField(decimal_places=1)`, half-hour increments per DEC-020), rate snapshot fields
(null until submission), `line_total` (null until submission).

### `EquipmentLine`

Time-based only, no quantity field (DEC-021). `usage_type` = `operating` / `standby` / `overtime`
determines which Caltrans rate component is applied. All three rate components are snapshotted
at submission regardless of usage type.

### `MaterialLine`

Total always = `unit_cost × quantity` (DEC-022). Lump-sum: unit type `LS`, quantity `1`. No
manual total override. Optional FK to `MaterialCatalog`.

---

## EWO Lifecycle

```
open → submitted → approved → sent → billed
         ↑                ↓
         └── rejected ←───┘
```

(DEC-016)

- **open**: editable; totals not yet calculated
- **submitted**: calculation runs and results are locked; PM reviews
- **approved**: PM approved (DEC-026); EWO ready to send to GC
- **rejected**: PM rejected; returns to open for correction
- **sent**: transmitted to GC; sent metadata recorded (DEC-034)
- **billed**: included in a pay application (DEC-036)

Post-approval edits create a new revision (DEC-027): original is locked permanently; revision
is a new `ExtraWorkOrder` with `parent_ewo` FK and `revision = 1`.

---

## Services Layer (`ewo/services.py`)

This is the **only file** that performs currency arithmetic (DEC-003). Views, serializers, and
the frontend must never calculate money.

### Why it exists

All EWO cost calculations must be server-side, deterministic, and produce an immutable audit
record (DEC-031). Centralizing this in one module enforces the boundary and makes the rounding
policy (DEC-023) easy to audit.

### What it contains

**Rate lookup functions:**

- `get_labor_rate(trade_classification, work_date)` — returns the `LaborRate` row with the
  latest `effective_date` on or before `work_date` (DEC-014)
- `get_equipment_rates(equipment_type, work_date)` — returns the `CaltransRateLine` from the
  schedule period that covers `work_date`

**Line calculators** (each rounds to nearest cent with `ROUND_UP` per DEC-023):

- `calculate_labor_line(line)` — snapshots all three rate tiers (reg/OT/DT) and computes
  `line_total = (reg_hours × rate_reg) + (ot_hours × rate_ot) + (dt_hours × rate_dt)`
- `calculate_equipment_line(line)` — snapshots all three Caltrans components; applies the
  correct one for the `usage_type`; saves `line_total`
- `calculate_material_line(line)` — `unit_cost × quantity`; optionally updates `MaterialCatalog`
  usage stats

**EWO-level aggregation:**

```
calculate_ewo_totals(ewo)
  ├── sum LaborLine.line_total         → labor_subtotal
  ├── labor_subtotal × labor_ohp_pct   → labor_ohp_amount
  ├── sum Equipment + Material totals  → equip_mat_subtotal
  ├── equip_mat_subtotal × ohp_pct     → equip_mat_ohp_amount
  ├── (if bond_required) subtotal × bond_pct → bond_amount
  └── sum all                          → total
```

**State transition:**

```
submit_ewo(ewo)
  └── transaction.atomic() + select_for_update()
        ├── assert status == 'open'
        ├── calculate_ewo_totals(ewo)
        └── set status = 'submitted', submitted_at = now()
```

### Rounding rule

`decimal.ROUND_UP` to the nearest cent at every calculation point — line totals, OH&P amounts,
bond, and final total. Fractional cents never carry forward. Never use `float` for money.
(DEC-023, DEC-031)

---

## Calculation Flow (Request → Database)

```
HTTP POST /api/ewos/{id}/submit/
  ↓
View validates user role and EWO ownership
  ↓
services.submit_ewo(ewo)
  ├── transaction.atomic() + select_for_update()  ← prevents concurrent submission
  ├── for each LaborLine:
  │     get_labor_rate(trade, work_date)
  │     calculate_labor_line(line)         ← snapshots rates, rounds, saves line_total
  ├── for each EquipmentLine:
  │     get_equipment_rates(equipment_type, work_date)
  │     calculate_equipment_line(line)     ← snapshots rates, rounds, saves line_total
  ├── for each MaterialLine:
  │     calculate_material_line(line)      ← rounds, saves line_total
  ├── calculate_ewo_totals(ewo)            ← aggregates, applies OH&P + bond, saves to EWO
  └── set status = 'submitted', submitted_at = now()
  ↓
Response: serialized EWO with totals
```

---

## URL Structure (Current)

```
/cp-admin/          → Django admin
/api/schema/        → OpenAPI schema (drf-spectacular)
/api/docs/          → Swagger UI
/__debug__/         → Django debug toolbar (DEBUG=True only)
```

Feature API endpoints are not yet wired (M2 work).

---

## Key Architectural Decisions

| Decision | Summary |
|---|---|
| DEC-003 | Server-only calculations in `ewo/services.py` |
| DEC-011 | v1 stores job number only; no full job hierarchy |
| DEC-012 | Field crew are name strings / Employee records, not app users |
| DEC-015 | Rates snapshotted at submission; immutable thereafter |
| DEC-016 | EWO lifecycle: open→submitted→approved→sent→billed |
| DEC-023 | `ROUND_UP` to nearest cent everywhere; no float |
| DEC-027 | Post-approval edits create a new revision record |
| DEC-028 | Django User + UserProfile; no custom AUTH_USER_MODEL |
| DEC-032 | Four apps: accounts, jobs, ewo, resources |

See `DECISIONS.md` for the full log.
