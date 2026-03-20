# WORKFLOW Setup Tracker (Outstanding Items)

This file tracks what is still outstanding to complete the baseline path:

**Dev machine -> GitHub CI -> Production VPS**

_Last updated: 2026-03-14_

## Milestone 1 Execution Order (Plan of Action)

Work these in order to complete `Milestone 1` from `MILESTONES.md` with minimal rework.

### Phase A - Repo and Continuity Baseline

- [x] Confirm local `main` tracks `origin/main` and working tree is clean.
- [x] Confirm multi-machine runbook is in place and usable: `CONTINUITY-CHECKLIST.md`.
- [x] Confirm baseline commit is pushed to GitHub before cross-machine setup.

Verification (Terminal, local):

```bash
cd ~/Projects/cp-project
git status -sb
git remote -v
make continuity-status
```

### Phase B - Dev Machine Baseline (Fedora + PyCharm)

- [x] Bootstrap with `make setup-online`.
- [x] Run `make local-check` and resolve failures before proceeding.
- [x] Confirm PyCharm interpreter points to `./backend/.venv/bin/python`.

Verification (Terminal, local):

```bash
cd ~/Projects/cp-project
make setup-online
make local-check
```

### Phase C - GitHub Baseline and CI

- [x] Verify `.github/workflows/ci.yml` runs on push/PR.
- [x] Enable branch protection for `main` (PR review + required status checks + no force push).
- [x] Add GitHub Environment `production` and seed required secrets.
- [x] Decision closeout: resolve `DEC-001` (CI gate strategy) and reflect it in docs.

Verification:

- GitHub site -> Actions: confirm latest workflow run status.
- GitHub site -> Settings -> Branches: confirm `main` protection rule exists.

### Phase D - Production VPS Baseline

- [ ] Access hardening complete (`deploy` key auth, no root SSH login, password auth disabled after verification).
- [ ] Runtime/services validated (Python/PostgreSQL/Nginx; Redis if needed).
- [ ] Create app DB role/database and verify Django DB connectivity.

Verification (Terminal, VPS):

```bash
whoami
sudo ufw status verbose
sudo systemctl is-active postgresql nginx
python3 --version
psql --version
sudo -u postgres psql -tAc "\du" | cat
sudo -u postgres psql -tAc "\l" | cat
```

### Phase E - Backup/Restore Proof (Required for Milestone 1)

- [ ] Create first PostgreSQL backup artifact.
- [ ] Execute one restore test and document exact commands/results.
- [ ] Keep backup/restore notes in `WORKFLOW-SETUP.md` or linked runbook.

### Phase F - Milestone 1 Closeout

- [ ] Mark complete items in `MILESTONES.md` only after command/UI verification.
- [ ] Confirm `DEC-002` is accepted and linked from milestone progress notes.
- [ ] Confirm Milestone 1 does not depend on post-v1 document/Dropbox features.

## 0) Critical Early Concerns (Must Be Correct Before Feature Scale)

- [ ] Money calculations are server-side and use `Decimal` only (no float arithmetic for costs).
- [ ] Rounding and rate rules are written down (labor, equipment, materials, tax/overtime if applicable).
- [ ] Extra Work Order lifecycle states are defined (`draft -> submitted -> approved/rejected -> billed`).
- [ ] Field edit/lock policy is defined per lifecycle state (especially after approval/billing).
- [ ] Audit trail requirement is set for critical changes (who, when, before/after values).
- [ ] Role matrix is drafted for key actions (create, submit, approve, reject, bill, override).
- [ ] Rate history strategy is defined for `Equipment` and `LaborTrade` records.
- [ ] Submitted EWO line items snapshot their applied rates so later global updates do not rewrite history.
- [ ] Backup and restore process is tested once against PostgreSQL (not backup-only; restore verified).
- [ ] Secrets and access baseline is enforced (SSH key-only, no root SSH login, protected `main`).
- [ ] v1 scope boundary is respected: no PDF upload pipeline or Dropbox dependency is required for baseline delivery.

## 0.1) Document Pipeline (Post-v1 Capability)

- [ ] Add backend file storage strategy for uploaded material PDFs (local-first or object storage) and document it.
- [ ] Define upload validation (PDF only, max size, malware scan policy if any).
- [ ] Define attachment linking model (material line item -> one or many supporting PDFs).
- [ ] Define EWO final PDF composition rules (cover summary + line items + appended supporting PDFs).
- [ ] Define download/access policy by role and EWO status.

Note: this section is intentionally not part of the baseline or v1 completion definition.

## 0.2) Dropbox Integration Investigation (Post-v1 Capability)

- [ ] Confirm business use case priority: intake only, export only, or two-way sync.
- [ ] Evaluate Dropbox integration options: direct API integration, shared-folder/manual ingest, or deferred v1.
- [ ] Define security requirements for Dropbox integration (OAuth scopes, token storage, audit logging).
- [ ] Define source-of-truth behavior when files exist in both app storage and Dropbox.
- [ ] Define v1 boundary so Dropbox does not block baseline EWO creation/PDF workflows.

## 1) Dev Baseline (Fedora + PyCharm)

- [ ] Confirm local `.env` exists at `backend/.env` (from `backend/.env.example`) with real values.
- [ ] Run backend baseline check with PostgreSQL env loaded:

```bash
cd ~/Projects/cp-project/backend
.venv/bin/python manage.py check
.venv/bin/python manage.py migrate
```

- [ ] Run frontend baseline check:

```bash
cd ~/Projects/cp-project/frontend
npm ci
npm run lint
npm run build
```

- [ ] Remove/replace any dev-only placeholder values in local env before staging/prod rollout.

## 2) GitHub Baseline

- [x] Push current branch with `.github/workflows/ci.yml` and verify green checks on PR and `main`.
- [x] Add required repository secrets for deployment (1 secret + 7 variables added to `production` environment):
  - `VPS_HOST`
  - `VPS_USER`
  - `VPS_SSH_KEY`
  - `SECRET_KEY`
  - `DB_NAME`
  - `DB_USER`
  - `DB_PASSWORD`
  - `DB_HOST`
  - `DB_PORT`
- [x] Enable branch protection on `main`:
  - Require PR reviews
  - Require status checks (backend + frontend CI jobs)
  - Block force pushes
- [x] Add GitHub Environment `production` with required approvals.

## 3) Production VPS Baseline

## 3.1 Server OS + Access

- [ ] Rebuild or migrate VPS to Ubuntu 24.04 LTS (WORKFLOW target).
- [ ] Ensure `deploy` uses SSH key auth (`~/.ssh/authorized_keys` exists).
- [ ] Disable SSH password auth after key login is confirmed.
- [ ] Keep `PermitRootLogin no` and verify SSH config validity.

Verification:

```bash
whoami
ls -la /home/deploy/.ssh
wc -l /home/deploy/.ssh/authorized_keys
sudo sshd -t
sudo grep -E '^(PermitRootLogin|PasswordAuthentication|PubkeyAuthentication)' /etc/ssh/sshd_config
```

## 3.2 Runtime + Services

- [ ] Install/verify runtime dependencies:
  - Python 3.12+
  - PostgreSQL
  - Nginx
  - Redis (if required by app features)
- [ ] Confirm services are enabled and active.

Verification:

```bash
python3 --version
psql --version
sudo systemctl is-enabled postgresql nginx
sudo systemctl is-active postgresql nginx
```

## 3.3 Database

- [ ] Create app DB role and database (currently only default postgres roles/dbs were observed).
- [ ] Apply least-privilege grants for app role.
- [ ] Validate app DB connectivity from Django.

Verification:

```bash
sudo -u postgres psql -tAc "\du" | cat
sudo -u postgres psql -tAc "\l" | cat
cd /srv/myproject/backend
../venv/bin/python manage.py check --database default
```

## 3.4 App Layout + Process Management

- [ ] Standardize deploy root path (`/srv/myproject` currently exists).
- [ ] Add systemd service for Django app process (gunicorn/uvicorn strategy).
- [ ] Add Nginx site config, enable it, and validate with `nginx -t`.
- [ ] Add HTTPS/TLS cert workflow (Let's Encrypt/Caddy) if public endpoint is live.

Verification:

```bash
sudo systemctl list-unit-files | grep -E 'myproject|gunicorn|nginx' | cat
sudo systemctl status nginx --no-pager -l | cat
sudo nginx -t
```

## 4) CD Workflow Outstanding

- [ ] Create `.github/workflows/deploy.yml` with manual approval and production environment gate.
- [ ] Deploy steps should include:
  - SSH to VPS as `deploy`
  - Pull repo / sync release
  - Install backend deps in venv
  - Run `manage.py migrate`
  - Restart app service
  - Optional health check endpoint call
- [ ] Add rollback notes (previous release or previous commit checkout).

## 5) Baseline Completion Definition

Baseline is complete when all are true:

- [ ] CI passes on backend + frontend for PR and `main`.
- [ ] `deploy` key-based SSH works; password auth disabled.
- [ ] PostgreSQL app DB/user exists and Django migrations run in production.
- [ ] App service and Nginx are enabled on boot and pass health checks.
- [ ] Production deploy can be executed from GitHub with approvals.
- [ ] Baseline does not depend on document uploads, final PDF packaging, or Dropbox integration.
