# MILESTONES TODO

Auto-generated from unchecked checklist items in `MILESTONES.md`.
Generated at: `2026-03-15 17:51:42Z`

## Open milestone work

- TODO(milestone): Milestone 1: Project Setup and Baseline
- TODO(milestone): Milestone 1: Project Setup and Baseline > Dev machine setup (Fedora + PyCharm)
- TODO(milestone): Milestone 1: Project Setup and Baseline > GitHub CI baseline with linting/build checks (initial), then backend/frontend test gates
- TODO(milestone): Milestone 1: Project Setup and Baseline > Production VPS baseline with PostgreSQL and Django
- TODO(milestone): Milestone 1: Project Setup and Baseline > Security baseline complete (SSH key-only auth, no root SSH, branch protections, secret handling)
- TODO(milestone): Milestone 1: Project Setup and Baseline > Backup/restore baseline complete (PostgreSQL backup created and restore test documented)
- TODO(milestone): Milestone 1: Project Setup and Baseline > Decision: CI gate strategy (smoke checks only vs immediate backend/frontend tests) after pros/cons review
- TODO(milestone): Milestone 1: Project Setup and Baseline > Decision: production Python/runtime pinning strategy (strict pin vs minor-range updates) after pros/cons review
- TODO(milestone): Milestone 2: Core Backend Functionality
- TODO(milestone): Milestone 2: Core Backend Functionality > Define Django project/app structure and settings (bear future growth in mind)
- TODO(milestone): Milestone 2: Core Backend Functionality > Define Django models for Labor, Equipment, Materials, and Extra Work Orders
- TODO(milestone): Milestone 2: Core Backend Functionality > Keep v1 context intentionally small: store the EWO job number now; defer full Customer/Job/JobSite/Location modeling
- TODO(milestone): Milestone 2: Core Backend Functionality > Keep application users and tracked labor as separate concepts in v1
- TODO(milestone): Milestone 2: Core Backend Functionality > Implement API endpoints for CRUD operations on these models
- TODO(milestone): Milestone 2: Core Backend Functionality > Add basic validation and error handling
- TODO(milestone): Milestone 2: Core Backend Functionality > Define money and costing rules (Decimal-only arithmetic, rounding policy, tax/overtime rules)
- TODO(milestone): Milestone 2: Core Backend Functionality > Design rate history handling for Equipment and LaborTrade records
- TODO(milestone): Milestone 2: Core Backend Functionality > Snapshot applied rates onto submitted EWO line items
- TODO(milestone): Milestone 2: Core Backend Functionality > Define Extra Work Order lifecycle states (draft, submitted, approved/rejected, billed) and field lock rules
- TODO(milestone): Milestone 2: Core Backend Functionality > Implement audit trail for critical record changes (who, when, what changed)
- TODO(milestone): Milestone 2: Core Backend Functionality > Decision: source of truth and calculation boundary (server-only calculations vs shared client/server logic) after pros/cons review
- TODO(milestone): Milestone 2: Core Backend Functionality > Decision: API contract conventions (error format, pagination pattern, filtering style, versioning policy) after pros/cons review
- TODO(milestone): Milestone 2: Core Backend Functionality > Decision: duplicate-prevention/idempotency approach for EWO creation (client keys, server constraints, or hybrid) after pros/cons review
- TODO(milestone): Milestone 3: Frontend Development
- TODO(milestone): Milestone 3: Frontend Development > Set up React project with TypeScript
- TODO(milestone): Milestone 3: Frontend Development > Create UI components for listing and managing Extra Work Orders
- TODO(milestone): Milestone 3: Frontend Development > Integrate frontend with backend API
- TODO(milestone): Milestone 3: Frontend Development > Decision: TypeScript migration strategy (big-bang migration vs incremental module-by-module) after pros/cons review
- TODO(milestone): Milestone 4: Authentication and Authorization
- TODO(milestone): Milestone 4: Authentication and Authorization > Implement user authentication (e.g., JWT or session-based)
- TODO(milestone): Milestone 4: Authentication and Authorization > Add role-based access control (e.g., admin vs regular user)
- TODO(milestone): Milestone 4: Authentication and Authorization > Define role matrix for EWO actions (create, submit, approve, reject, bill, edit after approval)
- TODO(milestone): Milestone 4: Authentication and Authorization > Decision: auth architecture (session-based vs token/JWT) after pros/cons review
- TODO(milestone): Milestone 5: Deployment and Monitoring
- TODO(milestone): Milestone 5: Deployment and Monitoring > Set up production deployment workflow (GitHub Actions + VPS)
- TODO(milestone): Milestone 5: Deployment and Monitoring > Implement basic monitoring and logging for production environment
- TODO(milestone): Milestone 5: Deployment and Monitoring > Add post-deploy health checks and rollback runbook validation
- TODO(milestone): Milestone 5: Deployment and Monitoring > Decision: deployment strategy (git pull on host vs artifact/release deployment) after pros/cons review
- TODO(milestone): Milestone 5: Deployment and Monitoring > Decision: release rollback model (previous commit checkout vs release directories/symlink switch) after pros/cons review
- TODO(milestone): Milestone 6: Additional Features and Enhancements
- TODO(milestone): Milestone 6: Additional Features and Enhancements > Add support for uploading and attaching invoice/receipt PDFs to material-related records
- TODO(milestone): Milestone 6: Additional Features and Enhancements > Implement finished EWO PDF output with user-selectable document contents
- TODO(milestone): Milestone 6: Additional Features and Enhancements > Re-evaluate Dropbox integration only if post-v1 workflows justify it
- TODO(milestone): Milestone 6: Additional Features and Enhancements > Add frontend flows for attaching/reviewing material PDFs and downloading final EWO PDF packages
- TODO(milestone): Milestone 6: Additional Features and Enhancements > If selected later, add UI flow for linking/importing Dropbox files into material evidence attachments
- TODO(milestone): Milestone 6: Additional Features and Enhancements > Decide document storage strategy before implementing uploads
- TODO(milestone): Milestone 6: Additional Features and Enhancements > Decision: PDF evidence policy (required vs optional, allowed file types/sizes, storage/retention) after pros/cons review
- TODO(milestone): Milestone 6: Additional Features and Enhancements > Decision: EWO PDF composition strategy (append originals vs merged package with cover/sections) after pros/cons review
- TODO(milestone): Milestone 6: Additional Features and Enhancements > Decision: Dropbox integration strategy (direct API, shared-folder workflow, or defer/no-sync) after pros/cons review
- TODO(milestone): Milestone 6: Additional Features and Enhancements > Implement search and filtering on the frontend
- TODO(milestone): Milestone 6: Additional Features and Enhancements > Optimize database queries and API performance
- TODO(milestone): Milestone 6: Additional Features and Enhancements > Implement pagination for large datasets

## Notes
- Source: `MILESTONES.md`
- Update by running: `make milestones-sync`
