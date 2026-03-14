# CHARTER

## Mission

Build a web application that helps the company capture, cost, review, and bill extra work that falls outside the original job contract.

The system should create a single source of truth so field, project, and office staff are working from the same data rather than disconnected notes, spreadsheets, or duplicated entries.

## Problem Statement

Extra work is often identified in field reports or daily job records, but the process of turning that information into a defensible, billable Extra Work Order can be inconsistent. That creates risk in three areas:

- missed revenue from untracked or under-tracked extra work
- disputes caused by unclear cost calculations or missing support
- duplicate or conflicting records across teams

## Product Goal

The product should make it easy to create an Extra Work Order from real job activity, calculate its cost consistently, preserve an audit trail, and support later billing and reporting.

## Core Cost Areas

The first version of the product centers on three primary cost categories:

1. Labor
2. Equipment
3. Materials

These same building blocks should support both:

- actual extra work tracking for billing and documentation
- projected cost building for estimating or forecasting

## Intended Users

- Field users entering or supporting daily extra work details
- Project managers or operations staff reviewing and pricing work
- Office/accounting/admin users finalizing records for billing and reporting

## In Scope For Early Versions

- Create and manage Extra Work Orders
- Track labor, equipment, and material cost components
- Start v1 with the minimum context needed to create an EWO, including a job-number reference
- Keep application users and tracked labor as separate concepts in v1
- Connect extra work records to field/daily job reporting inputs
- Calculate costs using consistent server-side rules
- Preserve rate history and snapshot submitted EWO pricing for auditability
- Maintain shared visibility through a unified database
- Support approval-ready and billing-ready workflows over time
- Evolve later into document-backed PDF workflows and evaluate Dropbox only if it adds clear business value

## Out of Scope For Initial Baseline

- full accounting system replacement
- full customer -> job -> job site -> location relationship modeling
- material PDF upload support and final EWO PDF package generation
- Dropbox integration
- advanced forecasting beyond core projected cost support
- broad reporting/analytics platform features before core workflow is stable

## Guiding Principles

- Accuracy over convenience
- Auditability by default
- One shared source of truth
- Security and backup discipline from the start
- Keep the first release focused on the core extra-work workflow

## Early Quality Commitments

The project should establish these foundations early:

- server-side cost calculations using predictable money rules
- clear Extra Work Order lifecycle states and edit/lock rules
- role-aware access to critical actions
- rate history and submitted-record pricing snapshots that support auditability
- document evidence integrity for uploaded PDFs (file type, size, ownership, and audit trail) before document features are implemented
- reliable backup and restore procedures
- production deployment with repeatable workflow and rollback path

## Success Indicators

The project is moving in the right direction when it can:

- capture extra work in a consistent structured format
- produce cost-backed Extra Work Orders from labor, equipment, and materials
- reduce ambiguity in review and approval
- improve confidence that valid extra work can be billed
- add document evidence and final PDF packaging later without undermining traceability or costing rules
- provide a foundation for future reporting, search, and performance improvements
