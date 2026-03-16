This is a list of target milestones for the project. These are not set in stone and may be adjusted as the project progresses, but they represent the current plan for how to break down the work into manageable pieces.

Decision rule for items marked "Decision": evaluate options, capture pros/cons, then record the chosen approach in `DECISIONS.md` before implementation.

## TODO Sync Convention (GitHub Issues)

Milestone items are project TODOs. To sync important items to GitHub Issues with clear flags, use metadata comments directly above the checklist item.

Template:

```markdown
<!-- TODO: <task text> -->
<!-- labels: todo, milestone:M#, area:<area>, type:<task|decision> -->
```

Policy for this repo:

- Top-level milestone items are TODO-synced by default.
- `Decision:` items are TODO-synced and labeled `type:decision`.
- Sub-items stay checklist-only unless explicitly promoted with TODO metadata comments.

<!-- TODO: Milestone 1 baseline complete (dev, CI, production, security, backup/restore) -->
<!-- labels: todo, milestone:M1, area:setup, type:task -->
- [ ] Milestone 1: Project Setup and Baseline
  - [ ] Dev machine setup (Fedora + PyCharm)
  - [ ] GitHub CI baseline with linting/build checks (initial), then backend/frontend test gates
  - [ ] Production VPS baseline with PostgreSQL and Django
  - [ ] Security baseline complete (SSH key-only auth, no root SSH, branch protections, secret handling)
  - [ ] Backup/restore baseline complete (PostgreSQL backup created and restore test documented)
  <!-- TODO: Decision needed for CI gate strategy (DEC-001 review alignment) -->
  <!-- labels: todo, milestone:M1, area:ci, type:decision -->
  - [ ] Decision: CI gate strategy (smoke checks only vs immediate backend/frontend tests) after pros/cons review
  <!-- TODO: Decision needed for production Python/runtime pinning strategy (DEC-002 review alignment) -->
  <!-- labels: todo, milestone:M1, area:runtime, type:decision -->
  - [ ] Decision: production Python/runtime pinning strategy (strict pin vs minor-range updates) after pros/cons review

<!-- TODO: Milestone 2 core backend complete (models, API, validation, lifecycle, audit) -->
<!-- labels: todo, milestone:M2, area:backend, type:task -->
- [ ] Milestone 2: Core Backend Functionality
    - [ ] Define Django project/app structure and settings (bear future growth in mind)
    - [ ] Define Django models for Labor, Equipment, Materials, and Extra Work Orders
    - [ ] Keep v1 context intentionally small: store the EWO job number now; defer full Customer/Job/JobSite/Location modeling
    - [ ] Keep application users and tracked labor as separate concepts in v1
    - [ ] Implement API endpoints for CRUD operations on these models
    - [ ] Add basic validation and error handling
    - [ ] Define money and costing rules (Decimal-only arithmetic, rounding policy, tax/overtime rules)
    - [ ] Design rate history handling for Equipment and LaborTrade records
    - [ ] Snapshot applied rates onto submitted EWO line items
    - [ ] Define Extra Work Order lifecycle states (draft, submitted, approved/rejected, billed) and field lock rules
    - [ ] Implement audit trail for critical record changes (who, when, what changed)
    <!-- TODO: Decision needed for source-of-truth and calculation boundary (DEC-003) -->
    <!-- labels: todo, milestone:M2, area:backend, type:decision -->
    - [ ] Decision: source of truth and calculation boundary (server-only calculations vs shared client/server logic) after pros/cons review
    <!-- TODO: Decision needed for API contract conventions (DEC-004) -->
    <!-- labels: todo, milestone:M2, area:api, type:decision -->
    - [ ] Decision: API contract conventions (error format, pagination pattern, filtering style, versioning policy) after pros/cons review
    <!-- TODO: Decision needed for duplicate-prevention/idempotency approach (DEC-005) -->
    <!-- labels: todo, milestone:M2, area:api, type:decision -->
    - [ ] Decision: duplicate-prevention/idempotency approach for EWO creation (client keys, server constraints, or hybrid) after pros/cons review

<!-- TODO: Milestone 3 frontend baseline complete (TypeScript setup and EWO management UI) -->
<!-- labels: todo, milestone:M3, area:frontend, type:task -->
- [ ] Milestone 3: Frontend Development
  - [ ] Set up React project with TypeScript
  - [ ] Create UI components for listing and managing Extra Work Orders
  - [ ] Integrate frontend with backend API
  <!-- TODO: Decision needed for TypeScript migration strategy (DEC-006) -->
  <!-- labels: todo, milestone:M3, area:frontend, type:decision -->
  - [ ] Decision: TypeScript migration strategy (big-bang migration vs incremental module-by-module) after pros/cons review

<!-- TODO: Milestone 4 auth and authorization complete -->
<!-- labels: todo, milestone:M4, area:auth, type:task -->
- [ ] Milestone 4: Authentication and Authorization
  - [ ] Implement user authentication (e.g., JWT or session-based)
  - [ ] Add role-based access control (e.g., admin vs regular user)
  - [ ] Define role matrix for EWO actions (create, submit, approve, reject, bill, edit after approval)
  <!-- TODO: Decision needed for auth architecture (DEC-007) -->
  <!-- labels: todo, milestone:M4, area:auth, type:decision -->
  - [ ] Decision: auth architecture (session-based vs token/JWT) after pros/cons review

<!-- TODO: Milestone 5 deployment and monitoring complete -->
<!-- labels: todo, milestone:M5, area:deploy, type:task -->
- [ ] Milestone 5: Deployment and Monitoring
  - [ ] Set up production deployment workflow (GitHub Actions + VPS)
  - [ ] Implement basic monitoring and logging for production environment
  - [ ] Add post-deploy health checks and rollback runbook validation
  <!-- TODO: Decision needed for deployment strategy (DEC-008) -->
  <!-- labels: todo, milestone:M5, area:deploy, type:decision -->
  - [ ] Decision: deployment strategy (git pull on host vs artifact/release deployment) after pros/cons review
  <!-- TODO: Decision needed for release rollback model (DEC-009) -->
  <!-- labels: todo, milestone:M5, area:deploy, type:decision -->
  - [ ] Decision: release rollback model (previous commit checkout vs release directories/symlink switch) after pros/cons review

<!-- TODO: Milestone 6 enhancements complete (documents, PDF flow, performance, optional Dropbox path) -->
<!-- labels: todo, milestone:M6, area:enhancements, type:task -->
- [ ] Milestone 6: Additional Features and Enhancements
  - [ ] Add support for uploading and attaching invoice/receipt PDFs to material-related records
  - [ ] Implement finished EWO PDF output with user-selectable document contents
  - [ ] Re-evaluate Dropbox integration only if post-v1 workflows justify it
  - [ ] Add frontend flows for attaching/reviewing material PDFs and downloading final EWO PDF packages
  - [ ] If selected later, add UI flow for linking/importing Dropbox files into material evidence attachments
  - [ ] Decide document storage strategy before implementing uploads
  <!-- TODO: Decision needed for PDF evidence policy -->
  <!-- labels: todo, milestone:M6, area:documents, type:decision -->
  - [ ] Decision: PDF evidence policy (required vs optional, allowed file types/sizes, storage/retention) after pros/cons review
  <!-- TODO: Decision needed for EWO PDF composition strategy -->
  <!-- labels: todo, milestone:M6, area:documents, type:decision -->
  - [ ] Decision: EWO PDF composition strategy (append originals vs merged package with cover/sections) after pros/cons review
  <!-- TODO: Decision needed for Dropbox integration strategy (DEC-010/DEC-017 alignment) -->
  <!-- labels: todo, milestone:M6, area:integrations, type:decision -->
  - [ ] Decision: Dropbox integration strategy (direct API, shared-folder workflow, or defer/no-sync) after pros/cons review
  - [ ] Implement search and filtering on the frontend
  - [ ] Optimize database queries and API performance
  - [ ] Implement pagination for large datasets
