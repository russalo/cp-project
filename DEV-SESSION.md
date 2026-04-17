# DEV SESSION - 2026-04-16

## Goal For Today

Use the real CP EWO workbook to drive a cohesive master-data + schema + UI
refresh. Walk through the spreadsheet, translate its structure into the
Django models, get it usable in a browser on the tailnet so the foreman /
field view can be assessed on a phone.

## Key Accomplishments

- **Phase 1 (#88, squash `7e00610`)** — master-data schema + Excel ingest.
  CaltransRateLine switched to factor storage (DEC-059); EquipmentType gained
  authoritative rates, nullable CT FK, `ct_match_quality` enum, and
  `fuel_surcharge_eligible` flag (DEC-060/061/062a). New
  `ingest_ewo_workbook` command loaded 2150 Caltrans rows, 11 trades +
  rates, 51 employees, 122 equipment types into the local dev DB.
- **Phase 2 (#89, squash `eea4cf4`)** — WorkDay + per-day math. Added
  `WorkDay` child model (DEC-065), re-parented Labor/Equipment/Material
  lines from `ewo` → `work_day`, changed equipment line shape to
  `qty + reg_hours + ot_hours + standby_hours` (DEC-066). Added
  `fuel_surcharge_pct` + `fuel_subtotal` on EWO (DEC-062b/c). Job gained
  `labor_ohp_pct`, `equip_mat_ohp_pct`, `bond_pct`, `cp_role`
  (DEC-063/068). ewo_number format `EWO-{job}-{nnn}` (DEC-067).
  Per-WorkDay math uses **chain B** (fuel enters equip+mat OH&P base —
  DEC-062d / DEC-064). Dropped `(ewo, work_date)` uniqueness so two
  foremen can run parallel crews on the same day under one EWO.
- **Phase 3 (#90, squash `f9a4214`)** — navigable UI. Added
  `react-router-dom`; built JobDetail / EwoDetail / WorkDayDetail /
  creation pages. Line items can be added + deleted inline on a WorkDay.
  Two-stage equipment picker (category → equipment). Inline-edit pencil
  on WorkDay + EWO header fields. CP brand retheme using the palette +
  fonts extracted from the workbook. Responsive line-form grid for
  phone / tablet.
- **Dev server on tailnet** — `http://origin-core:5174/` serving the live
  React UI; Django on `:8000`. Vite config allowlists `origin-core` +
  tailnet FQDN.
- **DECISIONS_INBOX** extended with DEC-059 through DEC-071 capturing the
  Phase 1–3 design choices, plus the Sandbox/EWE/EWO three-artifact
  earmark.
- **INBOX** — captured the "draft / in-progress / final" state concept
  bundled with DEC-071.

## Current Branch

`main` — clean; three PRs merged (admin squash), local branches deleted.

## Still Open / Next Session

User will do a full-EWO walkthrough from the desktop tomorrow to surface
whatever else needs tightening. Known rough edges flagged:

- **Totals show `—` until submit** — no Submit-EWO UI yet; totals compute
  on transition per DEC-031.
- **Line items aren't editable** — delete + re-add works. Parallel to the
  header inline-edit that shipped; wire the same pattern.
- **Material catalog empty** — type freehand for now; a separate ingest
  would populate it.
- **Line tables show `#id` for some fields** — employee / trade / equipment
  now resolved in WorkDay view via the reference-data maps, but other
  views may need the same treatment.
- **Caltrans auto-link (Phase 1.5)** — 87 exact/close EquipmentTypes have
  `rate_ot` and `rate_standby` at zero because the Caltrans FK wasn't
  wired during ingest. A pass that parses the Excel "CT Code" column
  would populate 87 rows' OT/standby rates automatically.
- **Mobile hardening list**: tables → cards on phone, ≥44pt tap targets,
  sticky totals bar on WorkDay page.
- **Submit EWO action + status transitions** — wait; bundled with DEC-071.

Dev servers are left running for tomorrow (backend pid 2959209, frontend
pid 2959258).

## Notes

- Excel workbook (`scratch/EWOexample.xlsx`) is gitignored and contains
  real CP names/amounts — do not commit its row content anywhere.
- `CLAUDE.md` domain rules are unchanged; all the new structure lives in
  DECISIONS_INBOX / INBOX.
- User preferences locked in memory: mobile-first (phone always
  available, iPad maybe, desktop = office), a/b/c decision pacing with
  concerns bundled where they overlap, and admin-squash merge style with
  all PR bot comments addressed first.

---

# DEV SESSION - 2026-03-23

## Goal For Today

Implement the documentation knowledge-pipeline baseline, archive superseded planning notes, align
AI guidance, and add audit/session scripts that keep the structure organized over time.

## Key Accomplishments

- Added active pipeline docs: `INBOX.md`, `VISION.md`, `DECISIONS_INBOX.md`,
  `MILESTONES_INBOX.md`, and `KNOWLEDGE-PIPELINE.md`.
- Added canonical AI guidance at `docs/reference/ai-guidance.md`.
- Aligned AI note files around the same documentation structure and added supported tool mirrors
  for Gemini and GitHub Copilot.
- Created `docs/archive/` structure and moved historical planning/session artifacts out of the root.
- Added documentation audit and session-feedback scripts plus Make targets.
- Updated root, backend, and frontend documentation to reflect the new routing model.

## Current Branch

`codex/main` — sandbox prevented local branch creation, so work proceeded in-place.

## Still Open / Next Session

- Decide whether `HOMEWORK.md` remains an active planning mechanism or is retired into archive.
- Expand docs audit heuristics if the first pass surfaces low-signal warnings.
- If desired later, add stronger CI enforcement for documentation drift checks.

## Notes

- `KNOWLEDGE-PIPELINE.md` is the human-readable guide to the documentation system.
- `docs/reference/ai-guidance.md` is the canonical shared AI documentation policy source.

---

# DEV SESSION - 2026-03-18

## Goal For Today

Integrate off-machine planning artifacts from the 2026-03-18 session on RUSS-DELL-LAPTOP into the project's canonical documentation.

## Key Accomplishments

- Integrated `CHARTER.md` revision — rewritten from engineering spec into a document grounded in real EWO artifacts, with new sections: Immediate Value of a Unified Database, Current Process narrative, two EWO workflow types, and a full What the Data Model Must Capture section covering rate authorities and markup structure.
- Added `cp_project_full_erd.html` (ERD v3) to `docs/` — standalone HTML, opens in any browser. ERD v3 covers: Django User/UserProfile, named/generic labor, trade override, EquipmentType/Unit split, ownership flag, MaterialCatalog with categories.
- Folded Homework Batch 002 answers into `DECISIONS.md` — all 10 items answered and recorded as DEC-018 through DEC-027.
- Added DEC-028 through DEC-031 from `docs/archive/session-notes/SESSION_SUMMARY.md` planning decisions (auth model, named/generic labor, trade override, calculation timing and lock).
- Updated DEC-003 (calculation boundary) to accepted: recalculate on `open → submitted` transition in `ewo/services.py`.
- Updated DEC-016 (lifecycle) to reflect confirmed states: `open → submitted → approved → sent → billed`, `rejected → open`; added revision model detail.
- Updated `CLAUDE.md` Domain Rules section to reflect all accepted decisions.
- Archived Homework Batch 002 to `docs/archive/homework/HOMEWORK-002.md`; Batch 003 is now the active batch.

## Current Branch

`main` — clean at session start; all changes committed in this session.

## Still Open / Next Session

- Homework Batch 003 (10 questions) fully unanswered — answer before triggering rollover.
  - Key items: role permissions matrix, sent-status tracking, GC response tracking, billed status definition, multi-date EWOs, seed data formats, job CRUD ownership, EWO description structure, audit log visibility.
- DEC-004 (API contract conventions) and DEC-005 (idempotency) still proposed — both gate M2.
- Build order from the session summary is the M2 implementation roadmap (see `docs/archive/session-notes/SESSION_SUMMARY.md`).
- Production server outstanding items still open (authorized_keys, DB role, gunicorn, nginx vhost).

## Notes

- `docs/archive/session-notes/SESSION_SUMMARY.md` is retained as an archive of the off-machine planning session. Extract decisions to `DECISIONS.md` before starting M2 implementation.
- Package recommendations from `docs/archive/session-notes/SESSION_SUMMARY.md` (django-money, django-simple-history, drf-spectacular, etc.) are not yet recorded as a decision — add DEC-032 when package selection is confirmed.

---

# DEV SESSION - 2026-03-17

## Goal For Today

Finish TODO-to-GitHub Issues workflow wiring (labels, PyCharm sync, node deprecation fix), verify CI is clean, and surface any remaining M1 configuration gaps.

## Key Accomplishments

- Fixed TODO-to-Issue GitHub Actions workflow to auto-create required labels before `alstr/todo-to-issue-action` runs — resolves label-missing failures.
- Upgraded `actions/checkout` to `v4` (pinned to SHA) to clear Node.js 20 deprecation annotation; workflow now runs clean with no warnings.
- Verified PyCharm TODO tool window and GitHub Issues reflect the same canonical set from `PROJECT_TODOS.py`.
- Confirmed branch protection is working correctly — direct pushes to `main` are blocked; all changes go through PR + CI.
- Added `CLAUDE.md` to repo root (AI assistant guidance file for this project).
- Identified that `fix/todo-workflow-label-bootstrap` has one unpushed commit (charter update); included in this stop-session push.

## Current Branch

`fix/todo-workflow-label-bootstrap` — ahead of origin by 1 commit; stop-session will push and create a PR.

## Still Open / Next Session

- Homework Batch 002 remains fully unanswered — answer those before triggering rollover.
- Start first-pass backend model design (M2 prep): EWO, LaborLine, EquipmentLine, MaterialLine, rate snapshot approach.
- Decide DEC-003 (calculation boundary) and DEC-004 (API contract) — both gate M2.
- Production server still needs: authorized_keys hardening, DB role + database creation, gunicorn service, nginx vhost wiring.
- WORKFLOW-SETUP.md VPS checklist items are still open.

## Notes

- `CLAUDE.md` is the guidance file for AI assistants working in this repo (mirrors key CHARTER/DECISIONS context).
- All TODOs in `PROJECT_TODOS.py` are the single source of truth for GitHub Issues sync — do not scatter TODO comments across other files.

---

# DEV SESSION - 2026-03-13

## Goal For Today

Capture project setup progress, tighten workflow/planning docs, and prevent loss of discovery notes gathered from existing Excel tools.

## Key Discoveries

- The legacy Excel files are useful discovery inputs, but are not clean enough to mirror directly into final models.
- Relationship design matters more than preserving spreadsheet column layout.
- Core context is broader than EWO line items: customer -> job -> job site -> specific location.
- Many spreadsheet fields are redundant or mixed-purpose and should be normalized over time.
- Equipment rates are influenced by Caltrans equipment rental references (`.github-copilot/USEFUL-URLS.md`).
- Labor rates are union-driven internally and should not be modeled as Caltrans labor rates.
- New required capability: upload invoice/receipt PDFs for materials evidence.
- New required capability: produce a finished EWO PDF that includes supporting material PDFs.
- New required investigation: Dropbox integration options for document intake/sharing/export workflows.

## Documentation Updated Today

- `WORKFLOW.md`
  - Converted to an operational workflow baseline (CI/CD, branch policy, secrets, rollback, verification).
  - Added decision-record usage and test-gate reality notes.
- `WORKFLOW-SETUP.md`
  - Added outstanding setup checklist for dev, GitHub, and VPS.
  - Added critical early concerns and document pipeline baseline tasks.
- `MILESTONES.md`
  - Added critical early concerns and decision checkpoints.
  - Added PDF upload and final EWO PDF package requirements.
- `DECISIONS.md`
  - Added decision index/template and initial records.
  - `DEC-002` accepted: runtime baseline uses Ubuntu 24.04 + Python 3.12 + Node 22 line with controlled patch updates.
- `CHARTER.md`
  - Tightened mission/scope/principles/success indicators.
  - Added scope commitments for material PDF evidence and final EWO PDF packages.

## VPS/Infra Status Snapshot (as observed today)

- SSH to production host is working with `deploy` user.
- UFW active; `nginx` and `postgresql` running.
- Missing/unfinished at time of check:
  - `deploy` `authorized_keys` setup needed before disabling password auth.
  - App DB role/database creation still pending.
  - Full deploy workflow and service wiring still pending.

## Current Direction Summary

- Build relationship-first domain design and iterate.
- Keep initial model set focused; defer non-essential complexity.
- Enforce server-side money rules and auditability.
- Treat spreadsheet formulas as policy clues, then formalize them as explicit backend rules.
- Keep deployment and security baseline moving in parallel with core backend design.

## Open Threads For Next Session

- Write the exact field edit/lock policy for each EWO lifecycle state.
- Start the first-pass model map based on relationships rather than spreadsheet tabs.
- Define the backend shape for rate history and submission-time rate snapshots.
- Leave document storage strategy open until a later pros/cons review is completed.
- Revisit Dropbox only if a concrete post-v1 use case emerges.

## 2026-03-14 Homework Follow-up

The homework answers were completed and folded into `DECISIONS.md`.

### Resolved Today

- v1 EWO creation only needs a job-number reference; the full customer/job/job site/location model is deferred.
- People are split into separate concepts: application users, tracked labor, and later customer contacts.
- Material evidence is optional when document support is eventually added.
- PDF upload support and finished EWO PDF packaging are not required in v1.
- Dropbox integration is not part of v1 and should only be revisited if later workflows justify it.
- The latest rate entry is the active rate for new work, while historical rates should be preserved for `Equipment` and `LaborTrade`.
- Submitted EWOs should snapshot their applied rates so later global changes do not rewrite historical pricing.
- v1 should use the lifecycle `draft -> submitted -> approved/rejected -> billed`.

### Still Open

- Document storage strategy remains undecided pending a later pros/cons review.
- Full edit/lock policy by lifecycle state still needs to be written down explicitly.
- The broader future model for cost analysis and estimate outputs still needs a later design pass.

## 2026-03-14 Multi-Machine Continuity Work

- Added a root `README.md` with fresh-machine bootstrap, PyCharm setup, and resume-on-another-machine steps.
- Added `.python-version` and `.nvmrc` so local machines can align more easily with CI/production targets.
- Expanded `setup.sh` to support clearer usage, Python detection, frontend dependency install, and optional skip flags.
- Expanded `Makefile` with setup, run, verification, and `continuity-status` targets.
- Replaced the placeholder `frontend/README.md` and refreshed `backend/README.md` to match the new onboarding path.
- Updated `WORKFLOW.md` to include explicit multi-machine continuity expectations.
