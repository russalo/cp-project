# VISION.md
## Expanded Product Scope & Future Horizon

*This file captures the long-term vision and expanded scope for the cp-project. Ideas and architectural designs live here until they are sequenced into `MILESTONES.md` and constrained by `CHARTER.md`.*

### Layer 2: Contract & Delta Plan
* **Full Party Model**: Owner, GC, CM, Surety, Sub, Supplier with role-per-project join table.
* **Contract Model (Risk Terms)**: Notice windows, LD rate, LD cap, no-damage-for-delay clause, valid delay types, differing site conditions language, contract days, substantial completion date.
* **Contracting Positions**: Support all 5 configs (Sub, Prime GC, Sub-to-CMa, Sub-to-CMR, Sub in four-party structure).
* **Delta Plan Module**: Job, original drawing reference, field condition description, discovery date, delay days pending approval. Tracks relationship to multiple EWOs.

### Layer 3: Change Orders, Daily Reports & Delays
* **Change Order Lifecycle**: Unilateral, bilateral, force account / T&M, constructive change, cardinal change. RCO submissions tracking.
* **Daily Report Module**: Contemporaneous records of crew, equipment, conditions, work performed. Includes Inspector presence log and out-of-scope direction log.
* **Delay Log Module**: Delay event tracking, days claimed vs. approved, cost impacts, Eichleay formula inputs.

### Layer 4: Claims, Bonding & Scheduling
* **Bonding Tracker**: Open contract balances, bonding capacity (net worth × surety multiplier), bond type per job.
* **Stop Notice / Lien Module**: Stop payment notices, 20-day preliminary notice tracking, bond claim filing deadlines.
* **Claims Module**: Formal claim escalation, dispute resolution path, statute of limitations tracking.
* **Schedule Module**: Baseline schedule, as-built schedule, critical path tracking, time extension requests.
* **Agency Layer**: Multi-agency jobs, inspector authority tracking.

### Layer 5: Project Management
* **RFI & Submittals**: RFI to Delta Plan triggers, submittal logs, submittal delay tracking.
* **SOV and Progress Billing**: Schedule of values, progress pay apps, retainage tracking, GC back-charges.
* **PM Dashboard**: Budget vs. actual, schedule status, open RFIs, pending submittals, open EWOs, profit fade tracking.

### Layer 6: Field UI Module (Foreman Interface)
* **The General's Dilemma**: Resolves the tension between Efficiency vs. Billing.
* **Daily Nut Calculator**: Burdened Labor Rate + Equipment Rental/Fuel Rate. Shows cost burden before deployment.
* **Tachometer (Performance Grading)**: Visual A-F grade comparing Earned Value vs. Actual Cost.
* **Runway / LD Dual Gauge**: % of Contract Days elapsed vs. % of Contract Value earned.
* **Frictionless EWO Capture**: 3-tap rule. Photo + Voice-to-Text narration + GC Witness selection.
* **WitnessSelector**: Color-coded search by authority (Blue = CM Rep, Amber = GC Super).
* **Evidence Vault**: Auto-syncs photos to Dropbox job folders.
* **Threaded Path Algorithm**: UI prioritization based on efficiency, billing, and time metrics.
* **Dynamic Billing UI**: Strategy pattern in React adapting to Prime GC vs. Sub vs. Sub-to-CM.

### Field Workflows & AI Integration
* **NotebookLM Pre-Job Brief**: Generates foreman-facing brief from Geotech reports and specs before day one.
* **EWO Scenario Library**: 11 job-aware scenarios (e.g., Hard Rock, Unexpected Groundwater) that pre-load documentation checklists and notice windows.
* **EWO Flag System**: PM_REVIEW, LEGAL_RISK, AI_RESEARCH, NOTEBOOKLM, DISPUTED, STANDARD workflows.
* **The Foreman Dilemma**: System defaults to "Option 3" (Work around it, notify concurrently).
* **Standby Event Lifecycle**: Discovery -> Redirect -> Notice Sent -> Direction Received -> Cost Calculated. Notice email timestamp serves as the permanent legal timestamp.

### Data Model Extensions
* **UnrecognizedWork**: Auto-created when a DailyReport entry cannot map to a PayItem. Serves as the automated EWO trigger.
* **Burdened Rate**: Added to Employee model to drive the Daily Nut calculator and T&M estimates.
* **Earned Value Calculation**: Dictated by `PayItem.billing_type` (UNIT, LUMP_SUM, or TM).
