# AuditAI Delivery Roadmap

This roadmap tracks the path from the functional portfolio prototype to a deployable automated-control platform. Items are considered complete only when implementation, validation, documentation and security checks are present.

## P0 — Functional foundation

- [x] Persistent SQLite domain model
- [x] Interactive rule creation and execution
- [x] Alert generation and lifecycle management
- [x] Health endpoint and integration tests
- [x] Python 3.11/3.12 continuous integration

## P1 — Data ingestion

- [x] Upload CSV and Excel workbooks with file-size/type validation
- [x] Preview sheets, columns, inferred types and sample rows
- [x] Persist normalized source metadata without storing credentials in source control
- [x] Connect to a local SQLite database through a read-only restricted adapter
- [x] Add SQLite schema and table discovery
- [x] Map discovered source columns to rule fields
- [x] Record ingestion counts, timestamps, failures and validation errors
- [x] Prevent unsafe paths and uncontrolled SQL identifiers

## P1 — Control engine

- [x] Numeric comparison rules
- [x] Text equality and containment rules
- [x] Null/completeness rules
- [x] Date-age and date comparison rules
- [x] Duplicate and composite-key rules
- [x] Cross-field comparison rules
- [x] Validate rule definitions before execution
- [ ] Cap affected-record samples while retaining total match counts
- [x] Record execution timestamps, scanned rows, matches and errors

## P1 — Automation

- [x] Manual and scheduled execution through the same service
- [x] Interval-based schedules callable by cron/worker
- [ ] Disable, resume and inspect schedules
- [ ] Prevent overlapping executions of the same rule
- [x] Persist last/next run and failure state
- [ ] Add retry and timeout policies

## P1 — Identity and accountability

- [x] Secure login and logout
- [x] Password hashing and minimum password policy
- [x] Administrator, auditor and viewer roles
- [x] Route- and action-level authorization
- [x] Append-only audit events for security-sensitive actions
- [x] Secure session-cookie defaults
- [x] Safe CLI administrator bootstrap flow

## P2 — Reporting and notifications

- [ ] Filterable execution and alert history
- [x] CSV audit-evidence export
- [ ] Management summary report
- [x] Notification abstraction with a persistent in-app implementation
- [ ] Email/webhook adapters configured only through environment secrets
- [ ] Delivery status and retry tracking

## P2 — Production readiness

- [ ] Database migrations
- [ ] PostgreSQL deployment profile
- [ ] Structured application logging
- [ ] Rate limiting and request-size limits
- [ ] Dependency and secret scanning
- [ ] Backup and recovery runbook
- [ ] Load and large-dataset tests
- [ ] Container image and non-root runtime
- [ ] Hosted privacy-safe demonstration

## Definition of done

Every completed capability must include automated tests, error handling, safe defaults, updated documentation and a reproducible local verification command. Production or confidential data must never be committed.
