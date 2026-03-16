This is a list of target milestones for the project. These are not set in stone and may be adjusted as the project progresses, but they represent the current plan for how to break down the work into manageable pieces.

Decision rule for items marked "Decision": evaluate options, capture pros/cons, then record the chosen approach in `DECISIONS.md` before implementation.

Issue sync note:

- GitHub TODO issue automation uses `PROJECT_TODOS.py` as the canonical source for synced TODO items.
- Keep this file planning-first and human-readable.

- [ ] Milestone 1: Project Setup and Baseline
  - [ ] Dev machine setup (Fedora + PyCharm)
  - [ ] GitHub CI baseline with linting/build checks (initial), then backend/frontend test gates
  - [ ] Production VPS baseline with PostgreSQL and Django
  - [ ] Security baseline complete (SSH key-only auth, no root SSH, branch protections, secret handling)
  - [ ] Backup/restore baseline complete (PostgreSQL backup created and restore test documented)
  - [ ] Decision: CI gate strategy (smoke checks only vs immediate backend/frontend tests) after pros/cons review
  - [ ] Decision: production Python/runtime pinning strategy (strict pin vs minor-range updates) after pros/cons review
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
    - [ ] Decision: source of truth and calculation boundary (server-only calculations vs shared client/server logic) after pros/cons review
    - [ ] Decision: API contract conventions (error format, pagination pattern, filtering style, versioning policy) after pros/cons review
    - [ ] Decision: duplicate-prevention/idempotency approach for EWO creation (client keys, server constraints, or hybrid) after pros/cons review
- [ ] Milestone 3: Frontend Development
  - [ ] Set up React project with TypeScript
  - [ ] Create UI components for listing and managing Extra Work Orders
  - [ ] Integrate frontend with backend API
  - [ ] Decision: TypeScript migration strategy (big-bang migration vs incremental module-by-module) after pros/cons review
- [ ] Milestone 4: Authentication and Authorization
  - [ ] Implement user authentication (e.g., JWT or session-based)
  - [ ] Add role-based access control (e.g., admin vs regular user)
  - [ ] Define role matrix for EWO actions (create, submit, approve, reject, bill, edit after approval)
  - [ ] Decision: auth architecture (session-based vs token/JWT) after pros/cons review
- [ ] Milestone 5: Deployment and Monitoring
  - [ ] Set up production deployment workflow (GitHub Actions + VPS)
  - [ ] Implement basic monitoring and logging for production environment
  - [ ] Add post-deploy health checks and rollback runbook validation
  - [ ] Decision: deployment strategy (git pull on host vs artifact/release deployment) after pros/cons review
  - [ ] Decision: release rollback model (previous commit checkout vs release directories/symlink switch) after pros/cons review
- [ ] Milestone 6: Additional Features and Enhancements
  - [ ] Add support for uploading and attaching invoice/receipt PDFs to material-related records
  - [ ] Implement finished EWO PDF output with user-selectable document contents
  - [ ] Re-evaluate Dropbox integration only if post-v1 workflows justify it
  - [ ] Add frontend flows for attaching/reviewing material PDFs and downloading final EWO PDF packages
  - [ ] If selected later, add UI flow for linking/importing Dropbox files into material evidence attachments
  - [ ] Decide document storage strategy before implementing uploads
  - [ ] Decision: PDF evidence policy (required vs optional, allowed file types/sizes, storage/retention) after pros/cons review
  - [ ] Decision: EWO PDF composition strategy (append originals vs merged package with cover/sections) after pros/cons review
  - [ ] Decision: Dropbox integration strategy (direct API, shared-folder workflow, or defer/no-sync) after pros/cons review
  - [ ] Implement search and filtering on the frontend
  - [ ] Optimize database queries and API performance
  - [ ] Implement pagination for large datasets
