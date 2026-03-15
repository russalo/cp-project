# WORKFLOW

## Scope

This document defines the baseline delivery workflow from local development to GitHub CI and production deployment.

## Environments

- Development: Fedora Workstation + PyCharm
- Source control and CI/CD: GitHub
- Production host: Hostinger KVM VPS (`187.124.155.131`)
- Production OS/runtime target: Ubuntu Server 24.04 LTS, Python 3.12+, Django 6.0.3, PostgreSQL, React
- Frontend language path: current React JavaScript scaffold; migrate to TypeScript in Milestone 3
- Canonical app path on VPS: `/srv/myproject`

## Branch Strategy

- `main` is the production branch.
- All changes land through PRs (no direct pushes to `main`).
- Feature work uses short-lived branches: `feature/<name>` or `fix/<name>`.
- `main` branch protection rules:
  - Require PR review before merge
  - Require CI checks to pass
  - Disable force push

## Multi-Machine Development Continuity

- Use repo-tracked setup files for parity: `README.md`, `.python-version`, `.nvmrc`, `backend/.env.example`, `Makefile`, and `setup.sh`.
- Keep machine-specific state out of Git: `.idea/`, `backend/.venv/`, `backend/.env`, and frontend build artifacts.
- Use `make continuity-status` when resuming work on another machine.
- Push active branches frequently so another machine can immediately continue from GitHub.
- Capture important scope or architecture changes in `DECISIONS.md` and session context in `DEV-SESSION.md`.
- Use `CONTINUITY-CHECKLIST.md` as the step-by-step start/stop runbook.

## Decision Records

- Decision items are tracked in `DECISIONS.md`.
- For milestone tasks marked `Decision:`, document options and pros/cons before implementation.
- When a decision is accepted, reference its ID in the PR that applies the change.

## CI Gates (GitHub Actions)

Workflow file: `.github/workflows/ci.yml`

Backend required checks:
- Install `backend/requirements.txt`
- Run `python manage.py check`
- Run `python manage.py migrate --noinput`

Frontend required checks:
- Install dependencies with `npm ci`
- Run `npm run lint`
- Run `npm run build`

Test gate alignment:
- Milestone 1 calls for linting and tests.
- Current state: CI has lint/build/check gates and no test suite yet.
- Target state: require backend tests (for example `pytest`) and frontend tests (for example `vitest`) once test scaffolding is added.

Local parity commands:

```bash
cd /home/russellp/Projects/cp-project
make backend-check
make frontend-build
```

## CD Policy (Production)

- Production deploy is gated by GitHub Environment `production` with manual approval.
- Deploy user on VPS: `deploy` (SSH key auth only).
- Deploy steps (target state):
  - Connect to VPS over SSH
  - Update app code in `/srv/myproject`
  - Install backend dependencies in venv
  - Run database migrations
  - Restart app service
  - Run post-deploy health checks

## Secrets Inventory

GitHub repository/environment secrets (for deploy workflow):

- `VPS_HOST`
- `VPS_USER`
- `VPS_SSH_KEY`
- `SECRET_KEY`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `ALLOWED_HOSTS`
- `DEBUG` (use `False` in production)

Note: `backend/config/settings.py` requires `DB_NAME`, `DB_USER`, and `DB_PASSWORD`.

## Production Service Layout

- Reverse proxy: `nginx`
- Database: `postgresql`
- Cache/message broker (if used): `redis`
- Django app process: systemd-managed service (gunicorn/uvicorn strategy)

## Monitoring And Logging (Milestone 5 Target)

- Centralize app logs via `journalctl` for the Django service.
- Configure Nginx access/error logs and basic log retention.
- Add a lightweight health endpoint and post-deploy health check.
- Optional next step: uptime alerting (for example Uptime Kuma or external monitor).

## Rollback

Minimum rollback procedure:

1. Checkout previous known-good commit/release on VPS.
2. Reinstall dependencies if needed.
3. Restart app service.
4. Verify health endpoint and logs.

If a schema migration is not backward compatible, use DB backup restore plan before rollback.

## Verification Checklist

Server baseline:

```bash
sudo ufw status verbose
sudo systemctl is-active postgresql nginx
python3 --version
psql --version
```

SSH hardening:

```bash
ls -la /home/deploy/.ssh
wc -l /home/deploy/.ssh/authorized_keys
sudo grep -E '^(PermitRootLogin|PasswordAuthentication|PubkeyAuthentication)' /etc/ssh/sshd_config
sudo sshd -t
```

Database readiness:

```bash
sudo -u postgres psql -tAc "\\du" | cat
sudo -u postgres psql -tAc "\\l" | cat
```

For remaining implementation tasks, track progress in `WORKFLOW-SETUP.md`.
