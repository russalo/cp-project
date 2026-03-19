# CONTRIBUTING

## Branch Naming

| Type | Pattern | Example |
|---|---|---|
| New feature | `feature/<short-name>` | `feature/labor-line-api` |
| Bug fix | `fix/<short-name>` | `fix/ewo-submit-race` |
| Documentation | `docs/<short-name>` | `docs/testing-guide` |
| Refactor | `refactor/<short-name>` | `refactor/services-split` |

Keep branch names lowercase with hyphens. Delete branches after merging.

---

## Commit Message Format

```
<type>: <short description>

<optional body — explain why, not what>

Decision IDs if applicable: DEC-003, DEC-031
```

**Types:**

| Type | When to use |
|---|---|
| `feat` | New feature or model |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change with no behavior change |
| `test` | Adding or updating tests |
| `chore` | Dependency update, config change, tooling |
| `migration` | Django migration (auto-generated is fine, but label it) |

**Examples:**

```
feat: add LaborLine model with reg/OT/DT hour fields (DEC-020, DEC-025)

fix: round equipment line total with ROUND_UP not ROUND_HALF_UP (DEC-023)

docs: add ARCHITECTURE.md explaining services layer and calculation flow

test: add submit_ewo concurrent-submission test case
```

Reference decision IDs in commit messages when the commit implements or is directly governed
by an accepted decision. This creates a navigable trail between the decision log and the code.

---

## Decision Workflow

When a PR introduces an architectural choice:

1. **Before implementing:** add the decision to `DECISIONS.md` with at least two options and
   pros/cons. Mark it `proposed`.
2. **In the PR:** link the decision ID in the PR description. Discuss if the options need review.
3. **On merge:** update the decision status to `accepted` (or `deferred`/`rejected`) and add
   the `Date decided` field. Reference the PR.

The milestone items marked `Decision:` in `MILESTONES.md` call this out explicitly. Do not
implement those items without a recorded decision.

See `DECISIONS.md` for the full log and template.

---

## MILESTONES.md vs PROJECT_TODOS.py

These two files serve different purposes and must be kept in sync in the same commit when both
need updating.

| File | Purpose | Edit when… |
|---|---|---|
| `MILESTONES.md` | Human-readable planning document; milestone breakdown and progress notes | Planning scope changes, adding progress notes, marking items complete |
| `PROJECT_TODOS.py` | Python file with TODO comment markers for PyCharm's TODO view and GitHub issue sync automation | Adding or removing a TODO item that should appear as a GitHub issue |

**Rule of thumb:** if you are updating the delivery plan, edit `MILESTONES.md`. If you are
adding a new trackable task to the GitHub issue board, also add it to `PROJECT_TODOS.py` in
the same commit. Never edit `PROJECT_TODOS.py` alone for scope or planning changes — those
belong in `MILESTONES.md`.

---

## PR Checklist

Use the PR template (`.github/pull_request_template.md`) for every PR. Key points:

- Run `make dev-check` (or at minimum `make backend-check` + `pytest backend/`) before opening
- Reference any decision IDs in the PR description and commit messages
- Update `DECISIONS.md` if a new architectural choice was made
- Update `DEV-SESSION.md` if the PR changes ongoing context for multi-machine continuity
- Add or update tests for any changes to `ewo/services.py` or domain model logic (see `TESTING.md`)

---

## Setup and Environment

See `README.md` for machine setup and `WORKFLOW.md` for the branch/CI/deploy workflow.

Required tools: `git`, `make`, `python 3.12`, `node 22`, `postgresql 14+`.

```bash
make setup       # full bootstrap (venv, deps, db, migrations)
make dev-check   # CI parity check (lint + build)
pytest backend/  # run backend test suite
```
