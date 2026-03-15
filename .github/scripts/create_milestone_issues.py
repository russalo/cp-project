#!/usr/bin/env python3
"""
Idempotent script to create GitHub labels, milestones, and issues from
MILESTONES.md. Run via the 'Create Issues from MILESTONES.md' workflow.

Usage (requires GH_TOKEN and REPO env vars set by GitHub Actions):
    python3 create_milestone_issues.py
"""

import json
import os
import subprocess
import sys

REPO = os.environ["REPO"]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _run(*args):
    return subprocess.run(list(args), capture_output=True, text=True)


def _run_json(*args):
    result = _run(*args)
    if result.returncode != 0:
        print(f"WARN: command failed: {' '.join(args)}\n  {result.stderr.strip()}", file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Labels
# ─────────────────────────────────────────────────────────────────────────────

LABELS = [
    ("setup",          "0075ca", "Development environment setup"),
    ("ci",             "e4e669", "CI/CD configuration and pipeline"),
    ("infrastructure", "D93F0B", "Infrastructure, VPS, and deployment"),
    ("security",       "B60205", "Security-related tasks"),
    ("backend",        "006B75", "Backend / Django work"),
    ("frontend",       "84b6eb", "Frontend / React work"),
    ("decision",       "e99695", "Requires pros/cons review and DECISIONS.md entry"),
    ("enhancement",    "a2eeef", "New feature or enhancement"),
]


def ensure_labels():
    print("\n── Labels ──")
    for name, color, description in LABELS:
        result = _run(
            "gh", "label", "create", name,
            "--color", color,
            "--description", description,
            "--repo", REPO,
            "--force",
        )
        if result.returncode == 0:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}: {result.stderr.strip()}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
# Milestones
# ─────────────────────────────────────────────────────────────────────────────

MILESTONE_TITLES = [
    "Milestone 1: Project Setup and Baseline",
    "Milestone 2: Core Backend Functionality",
    "Milestone 3: Frontend Development",
    "Milestone 4: Authentication and Authorization",
    "Milestone 5: Deployment and Monitoring",
    "Milestone 6: Additional Features and Enhancements",
]


def ensure_milestones():
    """Create any missing milestones and return a title→number dict."""
    print("\n── GitHub Milestones ──")

    existing_raw = _run("gh", "api", f"repos/{REPO}/milestones", "--paginate")
    existing_list = json.loads(existing_raw.stdout) if existing_raw.returncode == 0 else []
    by_title = {m["title"]: m["number"] for m in existing_list}

    for title in MILESTONE_TITLES:
        if title in by_title:
            print(f"  – {title} (already exists #{by_title[title]})")
        else:
            result = _run_json(
                "gh", "api", f"repos/{REPO}/milestones",
                "-f", f"title={title}",
                "-f", "state=open",
            )
            if result and "number" in result:
                by_title[title] = result["number"]
                print(f"  ✓ {title} (created #{result['number']})")
            else:
                print(f"  ✗ {title}: failed to create", file=sys.stderr)

    return by_title


# ─────────────────────────────────────────────────────────────────────────────
# Issues
# ─────────────────────────────────────────────────────────────────────────────

DECISION_NOTE = (
    "\n\n---\n"
    "> **Decision required:** Evaluate the options, document pros/cons, "
    "and record the chosen approach in `DECISIONS.md` before implementation."
)


def _issues_spec(ms):
    """Return the full list of (title, body, labels, milestone_title) tuples."""
    M1, M2, M3, M4, M5, M6 = (
        "Milestone 1: Project Setup and Baseline",
        "Milestone 2: Core Backend Functionality",
        "Milestone 3: Frontend Development",
        "Milestone 4: Authentication and Authorization",
        "Milestone 5: Deployment and Monitoring",
        "Milestone 6: Additional Features and Enhancements",
    )

    return [
        # ── Milestone 1 ──────────────────────────────────────────────────────
        (
            "Set up development environment (Fedora + PyCharm)",
            "Configure the primary development machine using **Fedora** as the OS "
            "and **PyCharm** as the IDE.\n\nPart of **Milestone 1: Project Setup and Baseline**.",
            ["setup"],
            M1,
        ),
        (
            "Establish GitHub Actions CI for linting and build checks",
            "Set up the initial GitHub Actions CI pipeline with linting and build "
            "checks for both backend and frontend.\n\n"
            "Part of **Milestone 1: Project Setup and Baseline**.",
            ["ci"],
            M1,
        ),
        (
            "Add backend and frontend test gates to GitHub Actions CI",
            "Extend the GitHub Actions CI pipeline to include backend (Django) and "
            "frontend (React) test gates.\n\n"
            "Part of **Milestone 1: Project Setup and Baseline**.",
            ["ci"],
            M1,
        ),
        (
            "Set up production VPS baseline with PostgreSQL and Django",
            "Provision and configure the production VPS with **PostgreSQL** and "
            "**Django** as the baseline stack.\n\n"
            "Part of **Milestone 1: Project Setup and Baseline**.",
            ["infrastructure"],
            M1,
        ),
        (
            "Implement security baseline (SSH key-only auth, no root SSH, branch protections, secret handling)",
            "Harden the environment:\n"
            "- Enable SSH key-only authentication and disable root SSH login\n"
            "- Apply branch protection rules\n"
            "- Set up secret/credential management\n\n"
            "Part of **Milestone 1: Project Setup and Baseline**.",
            ["security"],
            M1,
        ),
        (
            "Create PostgreSQL backup and document restore process",
            "Create a repeatable PostgreSQL backup artifact and document a tested "
            "restore procedure.\n\n"
            "Part of **Milestone 1: Project Setup and Baseline**.",
            ["infrastructure"],
            M1,
        ),
        (
            "Decision: CI gate strategy (smoke checks only vs full backend/frontend tests)",
            "Evaluate the tradeoffs between running only smoke/lint checks in CI "
            "vs running full backend and frontend test suites on every PR."
            + DECISION_NOTE + "\n\nPart of **Milestone 1: Project Setup and Baseline**.",
            ["decision", "ci"],
            M1,
        ),
        (
            "Decision: production Python/runtime pinning strategy (strict pin vs minor-range updates)",
            "Evaluate whether to pin Python and runtime dependencies to an exact "
            "version or allow minor-range updates."
            + DECISION_NOTE + "\n\nPart of **Milestone 1: Project Setup and Baseline**.",
            ["decision", "infrastructure"],
            M1,
        ),

        # ── Milestone 2 ──────────────────────────────────────────────────────
        (
            "Define Django project/app structure and settings",
            "Design the Django project layout and app structure with future growth "
            "in mind. Define settings for dev, test, and production environments.\n\n"
            "Part of **Milestone 2: Core Backend Functionality**.",
            ["backend"],
            M2,
        ),
        (
            "Define Django models for Labor, Equipment, Materials, and Extra Work Orders (EWOs)",
            "Create the core Django data models:\n"
            "- **Labor** – tracked labor entries\n"
            "- **Equipment** – equipment used on a job\n"
            "- **Materials** – materials consumed\n"
            "- **Extra Work Order (EWO)** – the primary billing document\n\n"
            "Part of **Milestone 2: Core Backend Functionality**.",
            ["backend"],
            M2,
        ),
        (
            "Store EWO job number; defer full Customer/Job/JobSite/Location modeling to post-v1",
            "Keep v1 EWO context intentionally small: store the job number on the EWO "
            "and defer the full Customer → Job → JobSite → Location hierarchy until "
            "post-v1.\n\n"
            "Part of **Milestone 2: Core Backend Functionality**.",
            ["backend"],
            M2,
        ),
        (
            "Keep application users and tracked labor as separate concepts in v1",
            "Ensure that **application users** (who log in) and **tracked labor** "
            "(workers recorded on an EWO) remain distinct database/model concepts "
            "in v1, even if the same person appears in both.\n\n"
            "Part of **Milestone 2: Core Backend Functionality**.",
            ["backend"],
            M2,
        ),
        (
            "Implement API endpoints for CRUD operations on Labor, Equipment, Materials, and EWOs",
            "Build RESTful API endpoints supporting create, read, update, and delete "
            "for all core models.\n\n"
            "Part of **Milestone 2: Core Backend Functionality**.",
            ["backend"],
            M2,
        ),
        (
            "Add basic validation and error handling to APIs",
            "Implement input validation and consistent error responses across all "
            "API endpoints.\n\n"
            "Part of **Milestone 2: Core Backend Functionality**.",
            ["backend"],
            M2,
        ),
        (
            "Define and implement money and costing rules (Decimal-only arithmetic, rounding, tax/overtime)",
            "Establish and enforce project-wide costing rules:\n"
            "- Use `Decimal` (never `float`) for all monetary values\n"
            "- Define rounding policy\n"
            "- Implement tax and overtime calculation rules\n\n"
            "Part of **Milestone 2: Core Backend Functionality**.",
            ["backend"],
            M2,
        ),
        (
            "Design rate history handling for Equipment and LaborTrade records",
            "Design how rate changes are tracked over time for Equipment and LaborTrade "
            "records so that historical EWOs reflect the rates that were in effect at "
            "the time of the work.\n\n"
            "Part of **Milestone 2: Core Backend Functionality**.",
            ["backend"],
            M2,
        ),
        (
            "Snapshot applied rates onto submitted EWO line items",
            "When an EWO is submitted, snapshot the current rates onto each line item "
            "so the record is immutable and auditable regardless of future rate changes.\n\n"
            "Part of **Milestone 2: Core Backend Functionality**.",
            ["backend"],
            M2,
        ),
        (
            "Define EWO lifecycle states (draft, submitted, approved/rejected, billed) and field lock rules",
            "Define and implement the full EWO state machine:\n"
            "- **Draft** → **Submitted** → **Approved** or **Rejected** → **Billed**\n"
            "- Specify which fields are locked/editable at each state\n\n"
            "Part of **Milestone 2: Core Backend Functionality**.",
            ["backend"],
            M2,
        ),
        (
            "Implement audit trail for critical record changes (who, when, what changed)",
            "Record an immutable audit log for all significant changes to EWOs and "
            "related records, capturing who made the change, when, and what changed.\n\n"
            "Part of **Milestone 2: Core Backend Functionality**.",
            ["backend"],
            M2,
        ),
        (
            "Decision: source of truth and calculation boundary (server-only vs shared client/server logic)",
            "Determine where financial calculations are performed and enforced — "
            "server-only (authoritative) or duplicated on both client and server."
            + DECISION_NOTE + "\n\nPart of **Milestone 2: Core Backend Functionality**.",
            ["decision", "backend"],
            M2,
        ),
        (
            "Decision: API contract conventions (error format, pagination, filtering, versioning)",
            "Standardize the API contract before building out endpoints:\n"
            "- Error response format\n"
            "- Pagination pattern\n"
            "- Filtering/query style\n"
            "- Versioning policy"
            + DECISION_NOTE + "\n\nPart of **Milestone 2: Core Backend Functionality**.",
            ["decision", "backend"],
            M2,
        ),
        (
            "Decision: duplicate-prevention/idempotency approach for EWO creation",
            "Evaluate approaches to prevent duplicate EWO submissions:\n"
            "- Client-side idempotency keys\n"
            "- Server-side unique constraints\n"
            "- Hybrid approach"
            + DECISION_NOTE + "\n\nPart of **Milestone 2: Core Backend Functionality**.",
            ["decision", "backend"],
            M2,
        ),

        # ── Milestone 3 ──────────────────────────────────────────────────────
        (
            "Set up React project with TypeScript",
            "Scaffold the frontend application using **React** and **TypeScript**, "
            "including build tooling, linting, and project structure.\n\n"
            "Part of **Milestone 3: Frontend Development**.",
            ["frontend"],
            M3,
        ),
        (
            "Create UI components for listing and managing Extra Work Orders (EWOs)",
            "Build the core frontend components for:\n"
            "- Listing EWOs\n"
            "- Creating/editing an EWO\n"
            "- Viewing EWO detail and status\n\n"
            "Part of **Milestone 3: Frontend Development**.",
            ["frontend"],
            M3,
        ),
        (
            "Integrate frontend with backend API",
            "Wire the React frontend to the Django backend REST API for all core "
            "workflows (EWOs, Labor, Equipment, Materials).\n\n"
            "Part of **Milestone 3: Frontend Development**.",
            ["frontend"],
            M3,
        ),
        (
            "Decision: TypeScript migration strategy (big-bang vs incremental module-by-module)",
            "Decide whether to adopt TypeScript all at once or incrementally migrate "
            "module by module."
            + DECISION_NOTE + "\n\nPart of **Milestone 3: Frontend Development**.",
            ["decision", "frontend"],
            M3,
        ),

        # ── Milestone 4 ──────────────────────────────────────────────────────
        (
            "Implement user authentication (JWT or session-based)",
            "Build the authentication system for the application. The exact mechanism "
            "(JWT vs session-based) is subject to the auth architecture decision.\n\n"
            "Part of **Milestone 4: Authentication and Authorization**.",
            ["backend", "security"],
            M4,
        ),
        (
            "Add role-based access control (admin vs regular user)",
            "Implement RBAC so that different user roles have appropriate permissions "
            "within the application.\n\n"
            "Part of **Milestone 4: Authentication and Authorization**.",
            ["backend", "security"],
            M4,
        ),
        (
            "Define role matrix for EWO actions (create, submit, approve, reject, bill, edit after approval)",
            "Specify which roles are permitted to perform each EWO lifecycle action:\n"
            "- Create, Submit, Approve, Reject, Bill, Edit after approval\n\n"
            "Part of **Milestone 4: Authentication and Authorization**.",
            ["backend", "security"],
            M4,
        ),
        (
            "Decision: authentication architecture (session-based vs token/JWT)",
            "Evaluate session-based authentication vs token/JWT for this application's "
            "use case, considering the frontend SPA, API-first design, and mobile "
            "access requirements."
            + DECISION_NOTE + "\n\nPart of **Milestone 4: Authentication and Authorization**.",
            ["decision", "security"],
            M4,
        ),

        # ── Milestone 5 ──────────────────────────────────────────────────────
        (
            "Set up production deployment workflow (GitHub Actions + VPS)",
            "Create a reliable, repeatable production deployment pipeline using "
            "**GitHub Actions** targeting the production VPS.\n\n"
            "Part of **Milestone 5: Deployment and Monitoring**.",
            ["infrastructure", "ci"],
            M5,
        ),
        (
            "Implement basic monitoring and logging for production environment",
            "Set up application-level logging and basic infrastructure monitoring "
            "so that errors and performance issues are visible in production.\n\n"
            "Part of **Milestone 5: Deployment and Monitoring**.",
            ["infrastructure"],
            M5,
        ),
        (
            "Add post-deploy health checks and validate rollback runbook",
            "Define and automate post-deployment health checks. Document and test "
            "the rollback runbook to ensure it works before it is needed.\n\n"
            "Part of **Milestone 5: Deployment and Monitoring**.",
            ["infrastructure"],
            M5,
        ),
        (
            "Decision: deployment strategy (git pull on host vs artifact/release deployment)",
            "Evaluate deployment approaches:\n"
            "- Direct `git pull` on the host\n"
            "- Artifact/release-based deployment (tarball, container, etc.)"
            + DECISION_NOTE + "\n\nPart of **Milestone 5: Deployment and Monitoring**.",
            ["decision", "infrastructure"],
            M5,
        ),
        (
            "Decision: release rollback model (previous commit checkout vs release directories/symlink switch)",
            "Decide how rollbacks are performed in production:\n"
            "- Check out the previous commit\n"
            "- Maintain versioned release directories with a symlink switch"
            + DECISION_NOTE + "\n\nPart of **Milestone 5: Deployment and Monitoring**.",
            ["decision", "infrastructure"],
            M5,
        ),

        # ── Milestone 6 ──────────────────────────────────────────────────────
        (
            "Add support for uploading and attaching invoice/receipt PDFs to material records",
            "Allow users to upload invoice and receipt PDFs and attach them as "
            "evidence to material line items on an EWO.\n\n"
            "Part of **Milestone 6: Additional Features and Enhancements**.",
            ["enhancement", "backend"],
            M6,
        ),
        (
            "Implement finished EWO PDF output with user-selectable document contents",
            "Generate a polished, printable PDF version of a completed EWO, allowing "
            "the user to choose which sections and attachments to include.\n\n"
            "Part of **Milestone 6: Additional Features and Enhancements**.",
            ["enhancement", "backend"],
            M6,
        ),
        (
            "Evaluate Dropbox integration for post-v1 workflows",
            "Re-evaluate whether integrating with Dropbox makes sense after v1 "
            "workflows are established. Only pursue if it genuinely improves the "
            "field/office workflow.\n\n"
            "Part of **Milestone 6: Additional Features and Enhancements**.",
            ["enhancement"],
            M6,
        ),
        (
            "Add frontend flows for attaching/reviewing material PDFs and downloading EWO PDF packages",
            "Build the frontend UI for:\n"
            "- Uploading and attaching material PDFs\n"
            "- Reviewing attached evidence\n"
            "- Downloading the final EWO PDF package\n\n"
            "Part of **Milestone 6: Additional Features and Enhancements**.",
            ["enhancement", "frontend"],
            M6,
        ),
        (
            "Add UI flow for linking/importing Dropbox files into material evidence attachments",
            "If Dropbox integration is selected, build the frontend flow for browsing "
            "and importing files from Dropbox as material evidence.\n\n"
            "Part of **Milestone 6: Additional Features and Enhancements**.",
            ["enhancement", "frontend"],
            M6,
        ),
        (
            "Decision: document storage strategy (local disk, object storage, or third-party)",
            "Decide where uploaded files (PDFs, receipts) will be stored before "
            "implementing any upload functionality."
            + DECISION_NOTE + "\n\nPart of **Milestone 6: Additional Features and Enhancements**.",
            ["decision", "enhancement"],
            M6,
        ),
        (
            "Decision: PDF evidence policy (required vs optional, allowed file types/sizes, storage/retention)",
            "Define the rules governing PDF evidence on EWOs:\n"
            "- Required or optional per line item?\n"
            "- Allowed file types and maximum sizes\n"
            "- Storage and retention policy"
            + DECISION_NOTE + "\n\nPart of **Milestone 6: Additional Features and Enhancements**.",
            ["decision", "enhancement"],
            M6,
        ),
        (
            "Decision: EWO PDF composition strategy (append originals vs merged package with cover/sections)",
            "Decide how the final EWO PDF is assembled:\n"
            "- Append original attachment PDFs as-is\n"
            "- Generate a merged, structured package with cover page and sections"
            + DECISION_NOTE + "\n\nPart of **Milestone 6: Additional Features and Enhancements**.",
            ["decision", "enhancement"],
            M6,
        ),
        (
            "Decision: Dropbox integration strategy (direct API vs shared-folder workflow vs defer/no-sync)",
            "Evaluate Dropbox integration options:\n"
            "- Direct Dropbox API integration\n"
            "- Shared-folder workflow (no direct API)\n"
            "- Defer or skip Dropbox integration entirely"
            + DECISION_NOTE + "\n\nPart of **Milestone 6: Additional Features and Enhancements**.",
            ["decision", "enhancement"],
            M6,
        ),
        (
            "Implement search and filtering on the frontend",
            "Add search and filter capabilities to the EWO list and related views "
            "so users can quickly find the records they need.\n\n"
            "Part of **Milestone 6: Additional Features and Enhancements**.",
            ["enhancement", "frontend"],
            M6,
        ),
        (
            "Optimize database queries and API performance",
            "Profile and optimize slow database queries and API endpoints to ensure "
            "acceptable performance under realistic data volumes.\n\n"
            "Part of **Milestone 6: Additional Features and Enhancements**.",
            ["enhancement", "backend"],
            M6,
        ),
        (
            "Implement pagination for large datasets",
            "Add cursor- or page-based pagination to API endpoints and corresponding "
            "frontend components to handle large numbers of records gracefully.\n\n"
            "Part of **Milestone 6: Additional Features and Enhancements**.",
            ["enhancement", "backend"],
            M6,
        ),
    ]


def get_existing_issue_titles():
    """Return a set of existing open issue titles."""
    result = _run(
        "gh", "issue", "list",
        "--repo", REPO,
        "--state", "all",
        "--limit", "1000",
        "--json", "title",
    )
    if result.returncode != 0:
        print(f"WARN: could not list issues: {result.stderr.strip()}", file=sys.stderr)
        return set()
    try:
        data = json.loads(result.stdout)
        return {item["title"] for item in data}
    except (json.JSONDecodeError, KeyError):
        return set()


def ensure_issues(milestone_by_title):
    print("\n── Issues ──")
    existing = get_existing_issue_titles()
    issues = _issues_spec(milestone_by_title)

    created = 0
    skipped = 0
    failed = 0

    for title, body, labels, milestone_title in issues:
        if title in existing:
            print(f"  – (exists) {title}")
            skipped += 1
            continue

        milestone_number = milestone_by_title.get(milestone_title)
        args = [
            "gh", "issue", "create",
            "--repo", REPO,
            "--title", title,
            "--body", body,
        ]
        for label in labels:
            args += ["--label", label]
        if milestone_number:
            # gh issue create --milestone expects the milestone title, not the numeric ID
            args += ["--milestone", milestone_title]

        result = _run(*args)
        if result.returncode == 0:
            url = result.stdout.strip()
            print(f"  ✓ {title}\n    {url}")
            created += 1
        else:
            print(f"  ✗ {title}: {result.stderr.strip()}", file=sys.stderr)
            failed += 1

    print(f"\nIssues: {created} created, {skipped} skipped (already exist), {failed} failed.")
    return failed == 0


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"Repository: {REPO}")

    ensure_labels()
    milestone_by_title = ensure_milestones()
    success = ensure_issues(milestone_by_title)

    print("\nDone.")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
