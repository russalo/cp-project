# CHARTER

## Mission

Build a web application that helps an underground wet utility pipeline contractor
capture, cost, review, and bill extra work that falls outside the original job contract.

The system should create a single source of truth so field, project, and office staff
are working from the same data — rather than disconnected Excel files, email chains,
and paper forms that cannot be reconciled when it matters most.

---

## The Immediate Value of a Unified Database

Before a single workflow feature is built, moving to a web application solves a
foundational problem: there is currently no single version of an EWO that anyone
can trust.

Today, EWOs live as individual Excel files — on local machines, shared network
drives, and email attachments. When someone needs the current state of a job's
extra work, they search recent folders, ask around, and cross-check against
external data points just to have confidence in what they're looking at. That
cross-checking is the symptom: people already know they can't fully trust the file.
Data entry is not unified and is repeated across multiple files by multiple people
with no guarantee they're using the same rates, the same format, or the same numbers.

A shared database eliminates this immediately. From day one of deployment — before
advanced workflows, before PDF generation, before any reporting — the team has one
place where an EWO exists, one version, visible to everyone with access. That alone
is a meaningful improvement over the current state.

---

## The Current Process (And Where It Breaks)

### How EWOs Get Built Today

Extra Work Orders are currently built in Excel. Each EWO is a separate file with
no connection to any other. Field, project, and office staff work from their own
copies, and there is no mechanism to ensure anyone is working from correct or
current data.

### Two EWO Scenarios — Each With Its Own Failure Mode

**Reactive T&M — work first, paperwork later**

The most common situation: something unexpected happens in the field — a utility
conflict, a differing site condition, a directive from the GC rep on-site. Work
starts immediately because it has to.

The deeper problem is that the foreman often does not know the work was T&M in the
first place. No one flags it. Work gets logged in the daily report as part of the
normal day. Weeks or months later, someone in the office realizes it should have
been an EWO. At that point, reconstructing what happened — who was on site, what
equipment was running, what materials were used — becomes an act of creative writing
fiction.

When the GC disputes the amount — or disputes that the work was extra at all — the
contractor is left digging through paper forms, texts, and spreadsheets trying to
build a case from memory. Sometimes it holds. Sometimes revenue walks.

**Proactive change order — quote first, then work**

When there is lead time, the process is more controlled: the GC identifies
out-of-scope work, the contractor prepares an estimate, and if approved, it becomes
a contract change order before work begins. But even here, the process is manual —
quotes built in spreadsheets, approvals tracked via email, and final cost
reconciliation done by someone in the office pulling from multiple sources.

### The Common Thread

In both cases, the company depends on discipline and memory to connect field
activity to a billable, defensible document. When that chain breaks — and it does —
the result is missed revenue, slow billing, or disputes that could have been avoided
with better records captured closer to when the work happened.

---

## Problem Statement

The process of turning field activity into a defensible, billable Extra Work Order
is inconsistent, manual, and fragmented across disconnected Excel files. That creates
risk in four areas:

- **Missed revenue** — extra work not flagged at the time, reconstructed from memory
  too late, or not captured in enough detail to bill at full value
- **Disputes** — weak records give the GC leverage to reduce or reject EWOs that
  should have been paid in full
- **Slow billing** — office staff reconciling disconnected files from multiple people,
  none of whom can guarantee they have the current version
- **No shared truth** — field, PM, and office working from different files, with no
  way to know whose numbers are right

---

## Product Goal

Build a system that captures extra work at the source — in the field, close to when
it happens — and makes it straightforward to turn that raw activity into a cost-backed,
audit-ready Extra Work Order that can be reviewed, approved, and billed with confidence.

The core value proposition: close the gap between "work happened" and "defensible
record exists." The further that gap stretches in time, the more it costs.

---

## Two EWO Workflows

The product must support both scenarios without forcing one into the other's mold.

**T&M tracking** — Field work is flagged and captured in real time or same-day.
Labor, equipment, and materials are logged against an open EWO. A GC signature or
acknowledgment is captured if available, but the record stands on its own
documentation regardless.

**Change order / quote** — A cost estimate is built from labor, equipment, and
material components before work begins. If approved, it converts into an active EWO.
Actual costs can be tracked against the approved amount.

---

## Core Cost Areas

Both workflows are built on the same three cost components:

1. **Labor** — crew members, trade classifications, hours worked, time type
2. **Equipment** — equipment on site, hours running, applicable rates
3. **Materials** — items used, quantities, unit costs

These components support both actual cost tracking for billing and projected cost
building for estimates and quotes.

---

## What the Data Model Must Capture

The following reflects the actual structure of current EWO practice, extracted from
real field documents. It defines what the system must be able to represent.

### EWO Header

- Company reference
- Job number and job name / location
- Work date(s)
- Description of work performed
- EWO type: T&M field capture vs. pre-approved change order
- Lifecycle status (open, submitted, approved, billed, etc.)
- GC acknowledgment: who, when, method (signature, email, verbal noted) — the
  absence of acknowledgment is itself meaningful and must be recordable

### Labor Lines

Each labor line captures:

- Employee reference — code and name, kept separate from app login in v1
- Trade classification: Superintendent, Operator Foreman, Operator, Laborer Foreman,
  Laborer, Laborer Pipelayer, CM Foreman, Cement Mason, Teamster, Mechanic, Welder,
  and others as needed
- Time type: Regular (REG), Overtime (OT), or Double Time (DT)
- Hours worked
- Hourly rate — looked up from the rate table at time of entry, snapshotted at
  submission so the record is immutable after billing

### Equipment Lines

Each equipment line captures:

- Equipment identifier and description
- Equipment code (reference to rate schedule)
- Hours on site
- Unit of measure — most equipment is per hour; some items are per day
- Hourly / daily rate — from rate table, snapshotted at submission
- Calculated line total

### Materials Lines

Each material line captures:

- Description
- Quantity (number of units)
- Unit cost
- Calculated line total

### Rate Tables — Two Distinct Source Authorities

Equipment rates and labor rates come from entirely different governing sources,
versioned independently, and must be treated as separate systems in the data model.

**Equipment rates — Caltrans published schedule**

Equipment rental rates are sourced from the California Department of Transportation
(Caltrans) rental rate schedule, published and updated on a regular cycle (currently
expiring 3/31/2026). Each equipment record is identified by three fields:

- `Class` — equipment category code (e.g. HCECL = Hydraulic Cranes & Excavators,
  Crawler Mounted; TRDMP = Trucks, Dump, On-Highway; TRACC = Tractors, Crawler)
- `Make` — manufacturer code (e.g. CAT, DEER, PETE)
- `Model` — specific model code within that make

Each record carries three rate components, all of which may be billable:

- `Rental_Rate` — standard operating rate (per hour, while equipment is working)
- `Rw_Delay` — right-of-way delay rate (per hour, while equipment is on site but
  not operating — standby time)
- `Overtime` — overtime rate adder (per hour, applied on top of rental rate for
  overtime hours)

The Caltrans schedule contains approximately 2,100+ individual equipment records
across 60 equipment classes and 174 makes. The company uses a subset of these
relevant to underground wet utility pipeline work.

The data model must:
- Store the full Caltrans schedule as a versioned rate table with effective and
  expiration dates per schedule period
- Allow company equipment to be mapped to Caltrans Class/Make/Model records
- Track all three rate components (operating, delay, overtime) per equipment record
- Snapshot all applicable rates at EWO submission time

**Labor rates — Union collective bargaining agreements**

Labor rates are governed by the collective bargaining agreement (CBA) of each
individual trade union. The company is a union contractor. Trade classifications
and their governing unions include:

- Operating Engineers (IUOE) — Operators, Operator Foremen, Superintendents
- Laborers (LIUNA) — Laborers, Laborer Pipelayers, Laborer Foremen
- Cement Masons (OPCMIA) — Cement Masons, CM Foremen
- Teamsters (IBT) — Teamsters
- Other trades as applicable

Each trade classification carries three rate tiers:
- Regular time (REG)
- Overtime (OT)
- Double time (DT)

CBA rates are negotiated on union contract cycles and updated independently of the
Caltrans equipment schedule. The data model must store rate history per trade
classification with effective dates, and snapshot the applicable rate at EWO
submission time.

**Rate versioning and snapshotting**

Both rate sources share the same requirement: the rate that was in effect when work
was performed must be preserved in the EWO record permanently. A submitted EWO must
reflect exactly what was billed — future rate updates, schedule changes, or CBA
negotiations must never alter a historical record. This applies to all three
equipment rate components and all three labor time types.

### Cost Summary and Markup

The billing structure follows California contractor law and must be calculated
server-side using consistent money rules. All calculations use the rates and
markup percentages that were in effect at the time of submission.

The standard structure:

1. Labor subtotal — sum of all labor line totals
2. Labor OH&P — markup applied to labor subtotal (default 15%)
3. Equipment and materials subtotal — sum of all equipment and material line totals
4. Equipment and materials OH&P — markup applied to that subtotal (default 15%)
5. Bond — percentage applied to the EWO total when required (default 1%, optional)
6. EWO total

Markup percentages default to the contractor law standard (15% OH&P) but can be
adjusted per EWO when circumstances require. The applied rate must be stored as
part of the EWO record — not derived from a current default at report time — so
that the record accurately reflects what was billed.

The bond add-on is tracked per EWO in v1 and will become a project-level default
in a future version.

---

## Intended Users

- **Foreman / Superintendent** — initiating EWOs, logging field activity, capturing
  GC acknowledgment in the field
- **Project Manager** — reviewing costs, building quotes, managing EWO status
- **Office / Admin / Accounting** — finalizing records, supporting billing, reporting

---

## In Scope For Early Versions

- Create and manage Extra Work Orders across both T&M and change order workflows
- Track labor, equipment, and material cost components per EWO
- Minimum context to create an EWO: job number reference and work type
- Keep application users and tracked labor as separate concepts in v1
- Connect extra work records to field / daily job reporting inputs
- Calculate costs server-side using consistent money rules
- Apply and store OH&P markup and bond per EWO with snapshotted rates
- Preserve rate history and snapshot submitted EWO pricing for auditability
- Maintain shared visibility through a unified database — one version, visible to all
- Support approval-ready and billing-ready workflows over time
- Evolve later into document-backed PDF workflows

---

## Out of Scope For Initial Baseline

- Full accounting system replacement
- Full customer → job → job site → location relationship modeling
- Material PDF upload support and final EWO PDF package generation
- Dropbox integration
- Advanced forecasting beyond core projected cost support
- Project-level bond and markup defaults (v1 tracks per EWO)
- Broad reporting / analytics before core workflow is stable

---

## Guiding Principles

- **Capture it close to when it happens** — the further from the work, the less
  reliable the record, and the more it costs
- **One version, visible to all** — no more asking around to find the current file
- **Accuracy over convenience** — the record has to hold up if challenged
- **Auditability by default** — every EWO should be able to tell its own story,
  including what rates and markups were applied and when
- **The database is the product** — shared data is valuable before features are
  complete
- **Build the model right, then populate it** — rate and equipment data will be
  entered clean once the structure is correct
- **Security and backup discipline from the start**
- **Keep the first release focused on the core extra-work workflow**

---

## Early Quality Commitments

- Server-side cost calculations using predictable money rules (no floating point
  errors on currency)
- Markup rates stored per EWO record, not derived at report time
- Clear EWO lifecycle states and edit / lock rules
- Role-aware access to critical actions
- Rate history with effective dates and submission-time snapshots
- Equipment rate records with status tracking (active, deprecated, pending)
- Reliable backup and restore procedures
- Production deployment with repeatable workflow and rollback path

---

## Success Indicators

The project is moving in the right direction when it can:

- Give the whole team one place to look for EWO data — no version hunting
- Flag and capture extra work the day it happens, not weeks later
- Produce cost-backed EWOs from labor, equipment, and materials consistently
- Apply and record markup correctly per the billing structure, with the applied
  rates stored in the record
- Give PM and office a record they trust without chasing the field or the server
- Reduce ambiguity in review and approval
- Improve confidence that valid extra work gets billed — and can be defended if
  disputed
- Add document evidence and PDF packaging later without undermining the core record

---

## Active Scope Constraints (v1 Explicit Rules)

* **CP Role Assumption**: CP operates as a subcontractor on all v1 EWOs. The contracting party is always a GC or CM-at-risk.
* **Public Works Toggle**: The `is_public_works` boolean on the Job record is a threshold field that determines the entire claims workflow (lien vs. stop notice, Miller Act vs. Little Miller Act).
* **Money Calculation Rule**: All money calculations use Python `Decimal` only. No float exceptions.
* **Rate Snapshot Rule**: Rates snapshot at EWO submission. This covers equipment rates and labor rates, and includes the CBA effective date and Caltrans rate schedule version.
* **GC Acknowledgment**: The absence of GC acknowledgment is itself a recordable fact, not just a gap in the data.
* **Role Association**: `cp_role` belongs on the Contract, not the Job. A single job can have multiple contracts.
* **Billing Structures**: v1 supports `UNIT`, `LUMP_SUM`, and `TM` via the `billing_type` field, even if SOV import happens in a later milestone.
* **Role Semantics**: `cp_role` changes the semantics of who receives notice and whose signature validates an EWO. It does not fork the data schema.
* **Field UI Boundary**: The foreman-facing mobile interface (Tachometer, Daily Nut) is a separate future module. The current EWO API is the data layer it will eventually sit on top of.
* **User Interactions**: Individual crew members do not interact with the system. Data enters via foreman selection.
* **Offline Requirement**: Any field-facing screen must capture locally and sync when signal returns. This is a non-negotiable architectural constraint.
