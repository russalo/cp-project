# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Purpose

A full-stack web application for an underground wet utility pipeline contractor to manage Extra Work Orders (EWOs) — capturing, costing, reviewing, and billing work outside original job contracts. Replaces fragmented Excel files and email chains with a single source of truth.

**Target users:** Foremen/Superintendents, Project Managers, Office/Accounting staff

**Current status:** Milestone 1 in progress. CI is in place; core backend API surfaces and an initial Jobs UI page are implemented, with additional models and features still under active development.

## Commands

```bash
# Session management
make start-session          # Git sync + full dev-check
make stop-session MSG="..."  # Checkpoint commit + push

# Development servers
make backend-run            # Django dev server → localhost:8000
make frontend-dev           # Vite dev server → localhost:5173

# Verification (runs in CI)
make local-check              # backend-check + frontend lint/build
make backend-check          # manage.py check + migrate --check
make frontend-build         # npm ci + eslint + vite build

# Setup
make setup-online                  # Full bootstrap (runs setup.sh)
make setup-backend          # Backend only
make frontend-install       # npm ci only
```

**Backend commands (from `backend/`):**
```bash
source .venv/bin/activate
python manage.py check
python manage.py migrate
python manage.py shell
```

**Frontend commands (from `frontend/`):**
```bash
npm run lint
npm run build
npm run dev
```

## Architecture

**Stack:**
- Backend: Django 6.0.3 + PostgreSQL (psycopg3) — SQLite is explicitly excluded
- Frontend: React 19 + Vite 8 — TypeScript migration is a pending decision (DEC-008)
- Runtimes: Python 3.12, Node 22, PostgreSQL 14+

**Key layout:**
```
backend/
  config/settings.py    # All settings; loads from backend/.env via python-dotenv
  config/urls.py
  manage.py
  requirements.txt
frontend/
  src/                  # React app (scaffold only, features not yet built)
  vite.config.js
  eslint.config.js
```

**Environment:** `backend/.env` (gitignored); copy from `backend/.env.example`. Required vars: `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

## Domain Rules (from CHARTER.md and DECISIONS.md)

These rules govern the core EWO data model — implement them precisely:

- **Two EWO types:** T&M (time-and-materials, tracked in real-time) and Change Order/Quote (pre-approved estimate)
- **Cost components:** Labor (crew + trade + time-type + hours), Equipment (Caltrans rental rates), Materials (description + qty + cost)
- **Labor rates:** Sourced from union CBAs (IUOE, LIUNA, OPCMIA, IBT); versioned with effective dates (DEC-014)
- **Equipment rates:** Caltrans rental schedule identified by Class/Make/Model; three rate components per record: `Rental_Rate` (operating), `Rw_Delay` (standby), `Overtime` (adder); versioned by schedule period (DEC-021)
- **Rate snapshots:** All applicable rate components snapshotted at EWO submission — immutable for historical records (DEC-015, DEC-031)
- **Billing:** Labor subtotal + Labor OH&P (15%); Equipment+Materials combined subtotal + Equipment+Materials OH&P (15%); optional Bond (1%); all markup rates stored per-EWO at submission
- **GC acknowledgment** tracked per EWO: who, when, method (signature/email/verbal) — absence is itself recordable
- **Money calculations:** Server-side only in `ewo/services.py`, triggered on `open → submitted` transition; `decimal.ROUND_UP` to nearest cent at every calculation point — line totals, OH&P, bond, final total; never use float (DEC-003, DEC-023, DEC-031)
- **Tax:** Excluded entirely from the system — CP performs installed work, no sales tax on billings; receipts with embedded tax are entered as LS lines at full invoice cost (DEC-024)
- **EWO numbering:** `{job_number}-{3-digit sequence}` per job (e.g. `1886-003`); atomic increment; revisions use decimal suffix `1886-003.1` (DEC-018, DEC-027)
- **Job number formats:** Regular = `^\d+$`; small/misc = `^\d{2}[A-Z]+$` (DEC-019)
- **Labor model:** Single `LaborLine` per worker per day; fields `reg_hours`, `ot_hours`, `dt_hours` (half-hour increments, `DecimalField(decimal_places=1)`); named or generic (`labor_type`); trade classification override allowed with required reason (DEC-020, DEC-025, DEC-029, DEC-030)
- **Equipment usage:** Time-based only, no quantity field; `usage_type` = `operating` / `standby` / `overtime`; standby is a separate line record (DEC-021)
- **Material pricing:** Always `unit_cost × quantity`; lump-sum = `LS` unit type, qty `1`; no manual total override (DEC-022)
- **Auth model:** Django built-in `User` + one-to-one `UserProfile` (role, active); no custom `AUTH_USER_MODEL` (DEC-028)
- **EWO lifecycle:** `open → submitted → approved → sent → billed`; `rejected → open` for corrections; post-approval changes create a new revision record with `parent_ewo` FK (DEC-016, DEC-026, DEC-027)
- **Approval:** PM role only; single approval; "approved" = ready to send to GC — GC submission happens outside the system (DEC-026)

## Decision Log

Active decisions are tracked in `DECISIONS.md`. Check it before making architectural choices. Key accepted decisions:

- **DEC-001:** CI gates baseline (lint/build now; tests before M2 closeout)
- **DEC-002:** Pin Python 3.12.x, Node 22.x, PostgreSQL by major version; allow patch updates
- **DEC-010:** Dropbox integration deferred to M6 or post-v1
- **DEC-011:** v1 does NOT include full customer/job/site modeling
- **DEC-012:** People represented as name strings in v1, not a relational `Person` model
- **DEC-014:** Rate precedence and versioning required before M2 closes
- **DEC-016:** EWO lifecycle states with field-lock rules required before M2 closes

Pending decisions (DEC-003, 004, 005, 006, 007, 008, 009, 017) cover: calculation boundary, API contracts, idempotency, TypeScript migration, auth strategy, deployment, rollback, and document storage.

## CI / Branch Strategy

- CI runs backend (`manage.py check` + `migrate`) and frontend (`eslint` + `vite build`) in parallel
- Branches: `main` (production), `feature/<name>`, `fix/<name>`
- PRs require CI green + review before merge
- Production deploy to Hostinger VPS (Ubuntu 24.04) is manual-approval only

## Multi-Machine Continuity

This repo is designed for development across multiple machines. Before switching machines:
1. Update `DEV-SESSION.md` with current progress and decisions
2. Run `make stop-session MSG="..."` to commit and push
3. On next machine: `make start-session`

Homework batches (10-item work lists) are managed via `scripts/homework_rollover.py` and tracked in `HOMEWORK.md`.

## Pull Request Descriptions

**After every `git push`, always output a ready-to-paste PR title and body — without being asked.**

The PR description should cover all commits on the branch since it diverged from `main`. Use `git log main..HEAD --oneline` and `git diff main..HEAD --stat` to gather the full picture before writing.

Format:

```
**Title:**
<concise title, under 70 chars, conventional-commit style>

**Body:**
## What's in this PR
<1–3 sentence summary of the overall change>

### <Section per logical workstream, e.g. "Backend API", "Frontend", "Docs">
- Bullet points covering the key changes, decisions referenced where relevant

## Test plan
- [ ] Checklist items for verifying the PR works correctly
```

Rules:
- Title uses conventional-commit prefix (`feat`, `fix`, `docs`, `refactor`, `chore`) and a milestone/scope tag where useful, e.g. `feat(M2): …`
- Body sections match the logical workstreams in the PR — don't list every file, summarise what changed and why
- Test plan items should be concrete and runnable, not generic ("tests pass")
