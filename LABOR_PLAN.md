# LABOR PLAN

## Purpose

This document defines the design and implementation plan for the Labor module of the cp-project.
It covers data models, API endpoints, frontend features, and key considerations for robust labor
and rate tracking functionality. It is intended to serve as the authoritative reference for
contributors building or reviewing labor-related work.

---

## Alignment with Project Decisions

The following accepted decisions directly govern Labor module design.
All choices made in this document must remain consistent with them.

| Decision | Effect on Labor |
|---|---|
| **DEC-012** – People model boundary | Application users and tracked labor are separate concepts. No entanglement between auth and costing. |
| **DEC-014** – Rate precedence and history | Latest rate entry is active. Historical rates are preserved, not overwritten. |
| **DEC-015** – Submitted EWO rate snapshot | When an EWO is submitted, applied rates are snapshotted. Later rate changes do not alter submitted records. |
| **DEC-016** – v1 EWO lifecycle | Draft → submitted → approved/rejected → billed governs when labor line items can be edited or locked. |

---

## Data Models

### LaborTrade

Represents a labor classification or trade used on job sites. Stores the current rates
used for new work. Historical rate changes are tracked separately in `LaborRateHistory`.

| Field | Type | Notes |
|---|---|---|
| `id` | Auto PK | |
| `trade_name` | CharField(100), unique | e.g. "Carpenter", "Electrician", "General Laborer" |
| `current_base_rate` | DecimalField(10,2) | Hourly straight-time rate |
| `current_overtime_rate` | DecimalField(10,2) | Hourly overtime rate |
| `current_double_time_rate` | DecimalField(10,2) | Hourly double-time rate |
| `is_active` | BooleanField | Soft-delete flag; inactive trades cannot be assigned to new employees |
| `created_at` | DateTimeField(auto_now_add) | |
| `updated_at` | DateTimeField(auto_now) | |

**Rules:**
- `trade_name` must be unique and may not be blank.
- Rates must use `Decimal`-only arithmetic per the project's money rules.
- Deactivating a trade does not delete historical records or rate history.
- When rates change, a `LaborRateHistory` entry must be created **before** updating the current rates on the trade.

---

### Employee

Represents a person whose labor is tracked on Extra Work Orders. This is not an application user.
See DEC-012.

| Field | Type | Notes |
|---|---|---|
| `id` | Auto PK | |
| `employee_code` | CharField(20), unique | Short identifier used in field entry (e.g. "JD-001") |
| `employee_name` | CharField(200) | Full display name |
| `labor_trade` | ForeignKey(LaborTrade) | Determines applicable rates |
| `is_active` | BooleanField | Soft-delete flag; inactive employees cannot be added to new EWO labor lines |
| `created_at` | DateTimeField(auto_now_add) | |
| `updated_at` | DateTimeField(auto_now) | |

**Rules:**
- `employee_code` must be unique, case-insensitive enforced at the database level.
- `labor_trade` may not be null; every employee must be associated with a trade.
- Reassigning a trade to an employee does not retroactively alter submitted EWO snapshots.

---

### LaborRateHistory

Tracks every rate change for a `LaborTrade` over time. Supports both standard
rate adjustments (e.g. annual increase) and situational alternate rates
(e.g. project override, holiday, emergency work).

| Field | Type | Notes |
|---|---|---|
| `id` | Auto PK | |
| `labor_trade` | ForeignKey(LaborTrade, related_name="rate_history") | |
| `effective_date` | DateField | Date from which this rate applies |
| `base_rate` | DecimalField(10,2) | Straight-time rate at this point in history |
| `overtime_rate` | DecimalField(10,2) | Overtime rate at this point in history |
| `double_time_rate` | DecimalField(10,2) | Double-time rate at this point in history |
| `rate_context` | CharField(50), nullable | Context type for situational rates (see context constants below) |
| `reason` | CharField(255), nullable | Optional notes explaining the rate change or alternate application |
| `created_by` | ForeignKey(User) | Application user who recorded this entry |
| `created_at` | DateTimeField(auto_now_add) | |

**Rate Context Constants:**

| Constant | Description |
|---|---|
| `STANDARD` | Normal rate adjustment (default; null is treated as standard) |
| `PROJECT_OVERRIDE` | Rate applies only in context of a specific project or EWO |
| `HOLIDAY` | Holiday premium rate |
| `EMERGENCY` | Emergency or after-hours escalation rate |
| `PREVAILING_WAGE` | Government-contract or prevailing-wage requirement |

**Rules:**
- Every rate update to a `LaborTrade` must produce a `LaborRateHistory` entry with the old values and an `effective_date`.
- The current active rate for a trade is the entry with the latest `effective_date` and `rate_context = STANDARD` (or null).
- Situational rates are identified by a non-null, non-STANDARD `rate_context` and do not replace the standard active rate.
- Rates must be positive Decimal values; zero-rate entries are permitted only with an explicit `reason`.
- All entries are append-only; no historical rate record may be deleted or overwritten after creation.

---

### EWOLaborLine (summary definition)

This model will be defined in the EWO plan. It is described here only to clarify
what rate data is snapshotted per DEC-015.

At the time an EWO is submitted, each labor line item must record:

| Snapshot Field | Source |
|---|---|
| `snapshotted_base_rate` | `LaborTrade.current_base_rate` at submission time |
| `snapshotted_overtime_rate` | `LaborTrade.current_overtime_rate` at submission time |
| `snapshotted_double_time_rate` | `LaborTrade.current_double_time_rate` at submission time |
| `snapshotted_trade_name` | `LaborTrade.trade_name` at submission time |

Once snapshotted, these values may not be changed regardless of later trade rate updates.

---

## API Endpoints

All endpoints require authentication. Error responses follow the project's standard API contract
(to be defined in DEC-004).

### LaborTrade Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/labor/trades/` | List all active labor trades; support filter by `is_active` |
| `POST` | `/api/labor/trades/` | Create a new labor trade |
| `GET` | `/api/labor/trades/{id}/` | Retrieve a specific labor trade with current rates |
| `PUT` | `/api/labor/trades/{id}/` | Update a labor trade; triggers rate history creation if rates change |
| `PATCH` | `/api/labor/trades/{id}/` | Partial update (e.g., activate/deactivate) |
| `GET` | `/api/labor/trades/{id}/rate-history/` | List all rate history entries for a trade, sorted by `effective_date` descending |

**Notes:**
- `DELETE` is not supported. Trades are deactivated with `is_active=false`.
- A rate change via `PUT` or `PATCH` must create a `LaborRateHistory` record automatically in the same transaction.
- The list endpoint should include a read-only `current_rate_effective_since` field derived from the latest standard history entry.

### Employee Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/labor/employees/` | List all employees; support filter by `is_active`, `labor_trade`, and search by `employee_code` or `employee_name` |
| `POST` | `/api/labor/employees/` | Create a new employee |
| `GET` | `/api/labor/employees/{id}/` | Retrieve a specific employee with trade details |
| `PUT` | `/api/labor/employees/{id}/` | Update employee details |
| `PATCH` | `/api/labor/employees/{id}/` | Partial update (e.g., activate/deactivate, reassign trade) |

**Notes:**
- `DELETE` is not supported. Employees are deactivated with `is_active=false`.
- Search must be case-insensitive across `employee_code` and `employee_name`.
- Response should include current trade rates inline for quick consumption in field-entry forms.

### LaborRateHistory Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/labor/trades/{id}/rate-history/` | List all rate history entries for a specific trade |
| `POST` | `/api/labor/trades/{id}/rate-history/` | Manually add a situational or historical rate entry |
| `GET` | `/api/labor/rate-history/{id}/` | Retrieve a specific history entry |

**Notes:**
- `PUT`, `PATCH`, and `DELETE` are not permitted on history records (append-only).
- The `POST` endpoint is used for recording situational alternate rates. Standard rate changes
  should be applied through the trade `PUT`/`PATCH` endpoint, which creates history automatically.
- List response should include a `is_current_standard` read-only flag indicating whether each
  entry is the currently active standard rate.

---

## Frontend Features

### Labor Trade Management

- **Trade List View**
  - Tabular list of all labor trades with current base rate, overtime rate, and double-time rate.
  - Column for `is_active` status with a filter toggle.
  - Action buttons: View, Edit, Deactivate (no delete).
  - Pagination and sorting by `trade_name` or current base rate.

- **Trade Detail View**
  - Displays current rates and an expandable rate history panel.
  - Rate history panel shows a table of all past standard and situational rates with `effective_date`, rates, context type, and reason.
  - Badge or indicator clearly marking which entry is the current active standard rate.

- **Create/Edit Trade Form**
  - Required fields: `trade_name`, `current_base_rate`, `current_overtime_rate`, `current_double_time_rate`.
  - On edit, if any rate field is changed, a confirmation prompt and a required `reason` field appear
    before saving (the reason is written to `LaborRateHistory`).
  - Inline validation: no blank trade name, no negative or non-decimal rates.

- **Add Situational Rate Form**
  - Accessible from the Trade Detail View.
  - Fields: `effective_date`, `base_rate`, `overtime_rate`, `double_time_rate`, `rate_context` (dropdown), `reason`.
  - This is used to record project overrides, holiday premiums, or emergency escalation rates
    without changing the standard active rate.

### Employee Management

- **Employee List View**
  - Tabular list with columns: employee code, name, trade, current base rate, status.
  - Filter by trade, status, and text search (code or name).
  - Action buttons: View, Edit, Deactivate.
  - Pagination and sorting.

- **Employee Detail View**
  - Displays all employee fields with associated trade name and current rates.

- **Create/Edit Employee Form**
  - Required fields: `employee_code`, `employee_name`, `labor_trade` (dropdown, active trades only).
  - Trade dropdown includes current base rate for reference.
  - Unique employee code validation with clear error messaging.

---

## Rate Querying and Resolution

This section defines how the correct rate is determined at any point in the system.

### Active Standard Rate

```
SELECT * FROM labor_rate_history
WHERE labor_trade_id = <id>
  AND (rate_context IS NULL OR rate_context = 'STANDARD')
ORDER BY effective_date DESC
LIMIT 1
```

This is also exposed as `LaborTrade.current_base_rate` (denormalized for read performance)
and kept in sync via the update transaction.

### Situational Rate Lookup

When an EWO or labor line is associated with a known context (e.g., a holiday or prevailing-wage
project), the system looks up the most recent active situational rate for that context:

```
SELECT * FROM labor_rate_history
WHERE labor_trade_id = <id>
  AND rate_context = '<context>'
  AND effective_date <= <work_date>
ORDER BY effective_date DESC
LIMIT 1
```

If no situational rate exists for the given context, fall back to the active standard rate.

### Submission Snapshot

When an EWO moves from `draft` to `submitted`:

1. For each labor line, read the current `LaborTrade` rates.
2. Write those values to the snapshot fields on the labor line.
3. The snapshot is immutable from this point forward regardless of future rate changes.

---

## Validation and Business Rules

- All money values (rates, calculated totals) use `DecimalField` with two decimal places.
- No floating-point arithmetic anywhere in the rate or costing pipeline.
- Negative rates are invalid. Zero-rate entries require a non-blank `reason`.
- Rates must use the same currency; no multi-currency support in v1.
- If an employee's trade is changed, prior EWO snapshots are unaffected.
- Inactive employees and inactive trades may not be added to new EWO labor lines but remain queryable for historical reporting.
- Rate history is append-only. No update or delete on `LaborRateHistory`.
- All rate history writes must be transactional with the triggering trade update.

---

## Audit Trail

Consistent with the project's audit commitments:

- Every `LaborRateHistory` entry captures `created_by` (the application user who made the change)
  and `created_at`.
- `LaborTrade` and `Employee` models record `created_at` and `updated_at`.
- All EWO labor line rate snapshots are preserved permanently as described in DEC-015.
- A future audit log feature should be able to reconstruct what rates applied to any labor line
  at any point in time using `LaborRateHistory` plus the submitted EWO snapshots.

---

## Security

- All Labor API endpoints require a logged-in application user.
- Rate history write operations (creating new rates, recording changes) should be restricted to
  users with an admin or office role once role-based access control is introduced in Milestone 4.
- Standard CSRF, SQL injection, and XSS protections are enforced by Django defaults.
- No labor or rate data is exposed in unauthenticated responses.

---

## Data Prepopulation and Testing

- A Django management command (`load_labor_trades`) should load initial trade definitions
  and starting rates for development and staging environments.
- Test fixtures should include at least:
  - Two or more active trades with rate history (at least two historical standard entries each)
  - One trade with a situational alternate rate entry
  - One inactive trade
  - A set of active and inactive employees across different trades
- Unit tests should cover rate resolution logic (active standard, situational fallback, snapshot behavior).

---

## Future Considerations

The following are intentionally deferred from v1 but should influence design decisions now so they
can be added cleanly later.

| Topic | Notes |
|---|---|
| **Estimating** | The rate model is designed to support projected-cost labor estimates; snapshot rules and rate resolution should apply equally to estimates when implemented. |
| **Field Reporting** | Daily labor entry forms will need quick lookup by employee code and trade, resolving current rates automatically. |
| **Overtime Rules** | Hours-threshold-based overtime calculation (e.g. OT after 8 hours daily or 40 weekly) is not in v1 but rate fields are pre-built to support it. |
| **Prevailing Wage** | `PREVAILING_WAGE` context exists in the rate history model so government-contract job requirements can be layered in without schema changes. |
| **Customer/Job Context** | When DEC-011 is expanded to add richer Job/Customer modeling, situational `PROJECT_OVERRIDE` rates can be linked to specific jobs. |
| **Rate Import** | A bulk CSV or import flow for updating many trade rates at once would reduce manual entry burden; this is a natural addition after the single-trade edit flow is stable. |

---

## Related Documents

- `CHARTER.md` – Mission, scope, and guiding principles
- `DECISIONS.md` – DEC-012, DEC-014, DEC-015, DEC-016
- `MILESTONES.md` – Milestone 2: Core Backend Functionality
