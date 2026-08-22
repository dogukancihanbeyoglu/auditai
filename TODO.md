# AuditAI Delivery Roadmap

This roadmap tracks the path from the functional portfolio prototype to a deployable automated-control platform. Items are considered complete only when implementation, validation, documentation and security checks are present.

## P0 — Functional foundation

- [x] Persistent SQLite domain model
- [x] Interactive rule creation and execution
- [x] Alert generation and lifecycle management
- [x] Health endpoint and integration tests
- [x] Python 3.11/3.12 continuous integration

## P1 — Data ingestion

- [ ] Upload CSV and Excel workbooks with file-size/type validation
- [ ] Preview sheets, columns, inferred types and sample rows
- [ ] Persist normalized source metadata without storing credentials in source control
- [ ] Connect to a local/approved SQL database through a restricted adapter
- [ ] Add schema and table discovery
- [ ] Map source columns to rule fields
- [ ] Record ingestion counts, timestamps, failures and validation errors
- [ ] Prevent formula injection, unsafe paths and uncontrolled queries

## P1 — Control engine

- [ ] Numeric comparison rules
- [ ] Text equality, containment and regular-expression rules
- [ ] Null/completeness rules
- [ ] Date-age and date-range rules
- [ ] Duplicate and composite-key rules
- [ ] Cross-field comparison rules
- [ ] Validate rule definitions before execution
- [ ] Cap affected-record samples while retaining total match counts
- [ ] Record execution duration, scanned rows, matches and errors

## P1 — Automation

- [ ] Manual and scheduled execution through the same service
- [ ] Hourly, daily and weekly schedules
- [ ] Disable, resume and inspect schedules
- [ ] Prevent overlapping executions of the same rule
- [ ] Persist last/next run and failure state
- [ ] Add retry and timeout policies

## P1 — Identity and accountability

- [ ] Secure login and logout
- [ ] Password hashing and minimum password policy
- [ ] Administrator, auditor and viewer roles
- [ ] Route- and action-level authorization
- [ ] Immutable audit events for security-sensitive actions
- [ ] Session-cookie and CSRF protection
- [ ] Safe bootstrap administrator flow

## P2 — Reporting and notifications

- [ ] Filterable execution and alert history
- [ ] CSV audit-evidence export
- [ ] Management summary report
- [ ] Notification abstraction with a local/log implementation
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
