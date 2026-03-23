# cp-project

> **cp-project** is a full-stack web application for an underground wet utility pipeline contractor.
> It manages **Extra Work Orders (EWOs)** — capturing, costing, reviewing, and billing work that
> falls outside original job contracts. Replaces fragmented Excel files and email chains with a
> single source of truth for Foremen, Project Managers, and Office/Accounting staff.
>
> Stack: Django 6 + PostgreSQL (backend) · React 19 + Vite (frontend) · Python 3.12 · Node 22

This repository is organized to support both software delivery and long-lived project knowledge.
For the documentation model and routing rules, start with `KNOWLEDGE-PIPELINE.md`.

## Start Session / Stop Session (Quick Card)

Pin this section for daily continuity.

> Maintenance rule: keep this quick card and the matching section in `CONTINUITY-CHECKLIST.md` identical. Update both in the same commit.

### Start Session (Terminal)

```bash
cd ~/Projects/cp-project
git switch main
git pull --rebase
make start-session
git switch -c feature/<short-name>
```

If continuing an existing branch:

```bash
cd ~/Projects/cp-project
git switch <existing-branch>
git pull --rebase
make continuity-status
```

### Stop Session (PyCharm + Terminal)

1. In PyCharm, update `DEV-SESSION.md` with what changed, next step, and blockers.
2. If you made a planning choice, update `DECISIONS.md` or `DECISIONS_INBOX.md` as appropriate.

Then in terminal:

```bash
cd ~/Projects/cp-project
make stop-session MSG="WIP: <short summary>"
```

What `make stop-session` does:

- runs homework rollover check (`scripts/homework_rollover.py`)
- prints a documentation change summary
- shows `git status`
- stages changes, commits (if any), and pushes current branch

### After PR Merge (Terminal)

```bash
cd ~/Projects/cp-project
git switch main
git pull --rebase
git branch -d <merged-branch>
```

---

## What this repo contains

- `backend/` — Django + PostgreSQL backend
- `frontend/` — React + Vite frontend
- `KNOWLEDGE-PIPELINE.md` — human-readable guide to the documentation system
- `ARCHITECTURE.md` — system shape, app structure, services layer overview
- `CHARTER.md` — project charter and domain rules
- `CONTRIBUTING.md` — branch naming, commit format, PR process
- `DECISIONS.md` — accepted and pending project decisions
- `DECISIONS_INBOX.md` — pending decisions waiting for review and promotion
- `DEV-SESSION.md` — running session notes and recent discoveries
- `INBOX.md` — raw capture layer for new ideas and notes
- `MILESTONES.md` — milestone breakdown and progress
- `MILESTONES_INBOX.md` — draft milestone sequencing waiting for review
- `TESTING.md` — how to run tests and test coverage policy
- `VISION.md` — long-horizon product scope and future direction
- `WORKFLOW.md` — branch / CI / deploy workflow
- `WORKFLOW-SETUP.md` — outstanding setup checklist
- `docs/archive/` — preserved historical and superseded documentation

## Runtime targets

These are the repository targets for parity with CI and production:

- Python `3.12`
- Node `22`
- PostgreSQL `14+`

Helpful version hint files are tracked in the repo:

- `.python-version`
- `.nvmrc`

If your current machine uses newer versions, the project may still run, but the target for consistency is the version above.

## Fresh machine quick start

Before starting, make sure the machine has these basic host tools:

- `git`
- `gh`
- `make`
- `sudo`

### 1) Clone the repo

```bash
cd ~/Projects
git clone https://github.com/russalo/cp-project cp-project
cd cp-project
```

### 2) Install runtime versions

If you use `pyenv` and `nvm`:

```bash
pyenv install -s "$(cat .python-version)"
pyenv local "$(cat .python-version)"
nvm install
nvm use
```

If you do not use `pyenv`/`nvm`, install Python 3.12, Node 22, and PostgreSQL with your package manager first.

### 3) Run the bootstrap

If this is the first run on a machine, or you need to download packages, connect to a network that allows package installs first.

Full stack bootstrap:

```bash
make setup-online
```

Backend-only bootstrap:

```bash
make setup-backend
```

What `make setup-online` does:

- creates `backend/.venv/` if missing
- installs Python dependencies from `backend/requirements.txt`
- installs frontend dependencies with `npm ci`
- creates `backend/.env` from `backend/.env.example` if needed
- installs PostgreSQL packages on Fedora/Ubuntu unless skipped
- attempts to create the PostgreSQL role/database from `backend/.env`
- runs Django checks and migrations

### 4) Verify the project is healthy

Local-only verification after dependencies are already installed:

```bash
make local-check
```

If you only want CI-parity checks and do not need pytest yet:

```bash
make dev-check
```

## Internet-sensitive vs local-only commands

Use these when your normal network blocks `apt`, `pip`, or `npm`.

Needs internet:

- `make setup-online`
- `make setup-backend`
- `make frontend-install`
- `make deps-refresh`

Local only after the machine is bootstrapped:

- `make db-check`
- `make backend-check`
- `make backend-test`
- `make frontend-build`
- `make local-check`
- `make backend-run`
- `make frontend-dev`
- `make continuity-status`

## Day-to-day development

Run the backend:

```bash
make backend-run
```

Run the frontend:

```bash
make frontend-dev
```

Check where you left off:

```bash
make continuity-status
```

That prints:

- current branch
- working tree status
- recent commits

## PyCharm setup on a new machine

1. Open the repo root: `cp-project`
2. Set the Python interpreter to **`backend/.venv/bin/python`**.
3. Let PyCharm detect the Django project from `backend/`.
4. Use the integrated terminal from the repo root for `make` commands.
5. Do **not** commit `.idea/` machine-specific state.

## Secrets and local machine data

Tracked in repo:

- `backend/.env.example`
- code, docs, scripts, decisions

Not tracked in repo:

- `backend/.env`
- `backend/.venv/`
- `.idea/`
- frontend build artifacts / `node_modules`

When moving to another machine, recreate `backend/.env` locally from the example and fill in real values.

## Continuity rules between machines

1. Work in short-lived branches such as `feature/<name>` or `fix/<name>`.
2. Push early and often so another machine can pick up where you left off.
3. Record important scope changes in `DECISIONS.md`.
4. Record session context in `DEV-SESSION.md` when stopping mid-stream.
5. Keep secrets out of Git and inside local env files or GitHub secrets.
6. Prefer repo commands (`make ...`) over ad-hoc machine-specific commands.

## Resume on another machine checklist

```bash
cd ~/Projects/cp-project
git pull
make continuity-status
make local-check
```

If `backend/.venv/` or frontend dependencies are missing, rerun:

```bash
make setup-online
```

---
