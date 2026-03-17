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
