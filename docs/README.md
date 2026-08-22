# AuditAI

**Privacy-safe internal audit and compliance analytics portfolio prototype**

AuditAI explores how internal-audit expertise, structured data testing and responsible automation can work together. It provides a functional Flask application with authenticated roles, bounded tabular-data ingestion, a deterministic rule engine, execution history, scheduled-run support, alert workflows, audit events and automated tests.

> **Status:** portfolio prototype. Use synthetic or irreversibly anonymized data only.

## What the project demonstrates

- Translating audit requirements into configurable control concepts
- Exception and threshold-based testing workflows
- Risk-focused alert and follow-up design
- Role and audit-domain data modelling
- Foundations for statistical analysis and explainable anomaly detection
- Privacy, credential and public-repository hygiene

## Functional workflow

1. Create an administrator and sign in as an authorized user.
2. Upload a bounded CSV/XLSX file, read a local SQLite table or import a bounded snapshot through a named read-only PostgreSQL profile.
3. Inspect discovered columns, types and sample records.
4. Create numeric, text, date, null, duplicate or cross-field controls.
5. Run controls manually or invoke the deterministic scheduled-run command.
6. Inspect execution evidence and affected records.
7. Acknowledge or resolve alerts, review management summaries and export alert evidence as CSV.
8. Deliver notification outbox items through environment-configured SMTP or webhook adapters.

The application persists local state in SQLite, supports PostgreSQL for production persistence and exposes the workflow through JSON endpoints under `/api`. Database credentials are resolved only from environment profiles. Production deployment remains an operator-controlled step and is not represented as completed.

## Technology

- Python 3.11+
- Flask
- SQLAlchemy and Flask-SQLAlchemy
- pytest integration tests
- Bootstrap 5

## Project structure

```text
auditai/
├── app.py              # Flask application factory and health endpoint
├── models.py           # Audit-domain data models
├── data_sources.py     # Bounded CSV/XLSX/SQLite ingestion
├── security.py         # Authentication, RBAC and audit events
├── reporting.py        # Evidence exports and notification APIs
├── postgres_connector.py # Read-only PostgreSQL source adapter
├── notification_worker.py # Durable outbox delivery worker
├── worker.py           # Scheduled control worker
├── ops/                # Readiness, backup and recovery tools
├── services/           # Rule evaluation, execution and scheduling
├── src/                # Alternative application entrypoint
├── templates/          # Portfolio demonstration interface
├── tests/              # Tests and synthetic-data generators
├── docs/               # Technical and usage documentation
├── SECURITY.md         # Responsible disclosure guidance
└── pyproject.toml      # Package metadata and dependencies
```

## Quick start

```bash
git clone https://github.com/dogukancihanbeyoglu/auditai.git
cd auditai
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
flask --app app create-admin
python app.py
```

On Windows, activate the environment with `.venv\Scripts\activate`.

Open [http://localhost:5000](http://localhost:5000). The health endpoint is available at [http://localhost:5000/health](http://localhost:5000/health).

Run due scheduled controls once from cron or a worker:

```bash
flask --app app run-scheduled
```

For continuous local scheduling, run the dedicated worker as a separate process:

```bash
python worker.py --poll-seconds 30
```

The worker is the single scheduler process; do not start one scheduler inside
each Flask/Gunicorn web worker. Stop it with `Ctrl+C`. Use `python worker.py
--once` for a one-cycle smoke test. Schedule state, last execution and next run
are available through `GET /api/rules/<id>/schedule` and rule detail responses.

Production deployments use versioned database migrations and the hardened WSGI entry point:

```bash
flask --app app db upgrade
gunicorn production:app
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for PostgreSQL, Render, migration and environment requirements. A non-root `Dockerfile` is included for container deployments.

Additional operational references:

- [POSTGRES_SOURCES.md](POSTGRES_SOURCES.md) — named, read-only PostgreSQL source profiles
- [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) — backup, restore, readiness and worker operations
- `python -m tools.performance_check` — deterministic 100,000-record performance budget

## Validation

```bash
python -m compileall app.py src
python -m pytest tests/
```

The test suite covers authentication and roles, audit events, CSV/XLSX/SQLite/PostgreSQL ingestion, schema discovery, safe source limits, six rule families, bounded evidence, manual and scheduled execution, overlap locks, retry/timeout policies, migrations, production security, backup/restore, readiness, management reporting, notification delivery and CSV reporting. CI runs on Python 3.11 and 3.12; a separate security workflow audits dependencies, scans secrets and builds the container.

## Security and privacy

- No production credentials or default administrator password are included.
- Debug mode is disabled unless explicitly enabled with `FLASK_DEBUG`.
- Real corporate, personal and confidential audit data must never be committed.
- Public demonstrations should use synthetic or irreversibly anonymized datasets.
- See [SECURITY.md](../SECURITY.md) for responsible disclosure guidance.

## Roadmap

See [TODO.md](../TODO.md) for completed capabilities, remaining production work and the definition of done.

## Author

**Doğukan Cihanbeyoğlu**  
Senior Internal Auditor | Audit Analytics | Data Analytics

[LinkedIn](https://www.linkedin.com/in/dogukanc/) · [GitHub](https://github.com/dogukancihanbeyoglu)
