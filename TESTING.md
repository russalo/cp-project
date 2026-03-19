# TESTING

## Running Tests Locally

From the repo root:

```bash
cd backend
source .venv/bin/activate
pytest
```

Or with verbose output:

```bash
pytest -v
```

Or from the repo root without activating the venv:

```bash
backend/.venv/bin/pytest backend/
```

**CI parity command:**

```bash
make backend-check         # manage.py check + migrate --check (not the test suite)
cd backend && pytest       # run the test suite
```

> Note: `make backend-check` runs Django system checks and migration checks but does NOT run
> pytest. Run pytest separately to execute the test suite.

---

## Test Configuration

- Framework: `pytest` + `pytest-django`
- Fixtures: `model_bakery` (factory-style object creation without fixtures)
- Time freezing: `freezegun` (for rate effective-date lookups)
- Config: `backend/pytest.ini`
- Database: uses the Django test runner's temporary database; requires a running PostgreSQL
  instance configured via `backend/.env`

All monetary assertions use `Decimal`, never `float`. Example:

```python
assert line.line_total == Decimal('123.46')   # correct
assert line.line_total == 123.46               # WRONG — never do this
```

---

## Current Test Coverage

### What is covered (`backend/ewo/tests.py` — 41 tests)

The test suite covers the services layer (`ewo/services.py`) — the calculation boundary
established in DEC-003.

| Category | What is tested |
|---|---|
| `get_labor_rate` | Returns correct rate for a given trade and date; raises error when no rate exists; respects effective-date precedence (DEC-014) |
| `get_equipment_rates` | Returns correct Caltrans rate line for equipment type and date; fallback path; raises error when no rate line covers the date |
| `calculate_labor_line` | All three time-type paths (reg/OT/DT); `ROUND_UP` per component; snapshot fields populated; `line_total` saved to DB (DEC-020, DEC-023, DEC-025) |
| `calculate_equipment_line` | All three `usage_type` paths (operating/standby/overtime); all three Caltrans components snapshotted regardless of usage type; `line_total` saved (DEC-021) |
| `calculate_material_line` | `unit_cost × quantity` calculation; `ROUND_UP` applied; `MaterialCatalog` stats updated when FK present; no-catalog path (DEC-022, DEC-023) |
| `calculate_ewo_totals` | OH&P applied correctly; bond on/off; return dict matches saved EWO fields (DEC-031) |
| `submit_ewo` | `open → submitted` transition; `submitted_at` timestamp set; rejects non-open EWOs; atomic with `select_for_update` (DEC-016, DEC-031) |

### What is NOT yet covered

| Area | Reason |
|---|---|
| `accounts` models / UserProfile | API endpoints not yet built (M2/M4 work) |
| `jobs` models | Lightweight model; no business logic yet |
| `resources` models | Reference data models; import logic not yet built |
| API endpoints (serializers, views) | Not yet wired; to be added alongside endpoint implementation |
| Frontend | No test suite yet; `vitest` planned for M3 |

---

## Test Policy for Pull Requests

### Required: add or update tests when…

- Modifying any function in `ewo/services.py`
- Adding a new service function to `ewo/services.py`
- Adding a new model with domain logic (validation, computed fields, state transitions)
- Fixing a bug that was triggered by a missing test case — add the regression test

### Not required (but welcome) when…

- Adding a pure Django model field (covered by `python manage.py check` + CI migration check)
- Updating documentation or configuration files
- Adding a migration (the migration check in CI covers correctness)

### If you cannot add a test

State the reason in the PR description and add a follow-up task in `PROJECT_TODOS.py`.

---

## Adding New Tests

Tests live alongside their app in `<app>/tests.py`. For larger test suites, convert to a
`tests/` package within the app directory.

Use `model_bakery.baker.make()` for test object creation:

```python
from model_bakery import baker

def test_something():
    ewo = baker.make('ewo.ExtraWorkOrder', status='open')
    labor_line = baker.make('ewo.LaborLine', ewo=ewo, reg_hours=Decimal('8.0'))
    # ...
```

Use `freezegun` when testing rate lookups that depend on `work_date`:

```python
from freezegun import freeze_time

@freeze_time('2026-03-01')
def test_labor_rate_lookup():
    # rate effective 2026-01-01 should be returned for 2026-03-01
```

---

## CI Integration

The CI backend job currently runs:

```yaml
- python manage.py check
- python manage.py migrate --noinput
```

Adding `pytest` to CI is tracked as M2 work (DEC-001 follow-up). Until then, run `pytest`
locally before opening a PR.
