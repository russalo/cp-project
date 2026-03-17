# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

A full-stack web application for an underground wet utility pipeline contractor to manage Extra Work Orders (EWOs) — capturing, costing, reviewing, and billing work outside original job contracts. Replaces fragmented Excel files and email chains with a single source of truth.

**Target users:** Foremen/Superintendents, Project Managers, Office/Accounting staff

**Current status:** Early Milestone 1 (project setup). CI is in place; backend models and frontend features not yet built.

## Commands

```bash
# Session management
make start-session          # Git sync + full dev-check
make stop-session MSG="..."  # Checkpoint commit + push

# Development servers
make backend-run            # Django dev server → localhost:8000
make frontend-dev           # Vite dev server → localhost:5173

# Verification (runs in CI)
make dev-check              # backend-check + frontend lint/build
make backend-check          # manage.py check + migrate --check
make frontend-build         # npm ci + eslint + vite build

# Setup
make setup                  # Full bootstrap (runs setup.sh)
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

## Domain Rules (from CHARTER.md)

These rules govern the core EWO data model — implement them precisely:

- **Two EWO types:** T&M (time-and-materials, tracked in real-time) and Change Order/Quote (pre-approved estimate)
- **Cost components:** Labor (crew + trade + time-type + hours), Equipment (Caltrans rental rates), Materials (description + qty + cost)
- **Labor rates:** Sourced from union CBAs (IUOE, LIUNA, OPCMIA, IBT); versioned with effective dates
- **Equipment rates:** Caltrans rental schedule identified by Class/Make/Model; three rate components per record: `Rental_Rate` (operating), `Rw_Delay` (standby), `Overtime` (adder); versioned by schedule period
- **Rate snapshots:** All applicable rate components snapshotted at EWO submission — immutable for historical records
- **Billing:** Labor subtotal + Labor OH&P (15%); Equipment+Materials combined subtotal + Equipment+Materials OH&P (15%); optional Bond (1%); all markup rates stored per-EWO at submission
- **GC acknowledgment** tracked per EWO: who, when, method (signature/email/verbal) — absence is itself recordable
- **Money calculations:** Server-side only, using decimal arithmetic (no floating point)
- **EWO lifecycle:** States with field-lock rules (specific states TBD in DEC-016)

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
