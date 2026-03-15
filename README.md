# cp-project

This repository is being prepared so you can open it on another machine, bootstrap it quickly, and keep continuity between development environments.

## What this repo contains

- `backend/` — Django + PostgreSQL backend
- `frontend/` — React + Vite frontend
- `DECISIONS.md` — accepted and pending project decisions
- `DEV-SESSION.md` — running session notes and recent discoveries
- `WORKFLOW.md` — branch / CI / deploy workflow
- `WORKFLOW-SETUP.md` — outstanding setup checklist

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
- `make`
- `sudo`

### 1) Clone the repo

```bash
cd ~/Projects
git clone <your-repo-url> cp-project
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

Full stack bootstrap:

```bash
make setup
```

Backend-only bootstrap:

```bash
make setup-backend
```

What `make setup` does:

- creates `backend/.venv/` if missing
- installs Python dependencies from `backend/requirements.txt`
- installs frontend dependencies with `npm ci`
- creates `backend/.env` from `backend/.env.example` if needed
- installs PostgreSQL packages on Fedora/Ubuntu unless skipped
- attempts to create the PostgreSQL role/database from `backend/.env`
- runs Django checks and migrations

### 4) Verify the project is healthy

```bash
make dev-check
```

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

Sync open decision items into a PyCharm TODO-friendly file:

```bash
make decisions-sync
```

Sync open milestone checklist items into a PyCharm TODO-friendly file:

```bash
make milestones-sync
```

That prints:

- current branch
- working tree status
- recent commits

Decision sync outputs:

- `DECISIONS-TODO.md` with `TODO(decision): ...` lines for `proposed` and `deferred` items in `DECISIONS.md`
- `MILESTONES-TODO.md` with `TODO(milestone): ...` lines for unchecked checklist items in `MILESTONES.md`
- optional GitHub issue sync via `make decisions-sync-github` (requires `GITHUB_TOKEN` in environment)

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
make dev-check
```

If `backend/.venv/` or frontend dependencies are missing, rerun:

```bash
make setup
```

---

