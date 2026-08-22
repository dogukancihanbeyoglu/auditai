# AuditAI

**Privacy-safe internal audit and compliance analytics portfolio prototype**

AuditAI explores how internal-audit expertise, structured data testing and responsible automation can work together. The current version provides a functional Flask application, persistent audit-domain models, a deterministic rule engine, synthetic records, alert workflows and automated tests.

> **Status:** portfolio prototype. Use synthetic or irreversibly anonymized data only.

## What the project demonstrates

- Translating audit requirements into configurable control concepts
- Exception and threshold-based testing workflows
- Risk-focused alert and follow-up design
- Role and audit-domain data modelling
- Foundations for statistical analysis and explainable anomaly detection
- Privacy, credential and public-repository hygiene

## Functional workflow

1. Review the seeded audit area and synthetic invoice ledger.
2. Create threshold-based control rules from the dashboard.
3. Run a control against the stored source records.
4. Inspect affected records in each generated alert.
5. Acknowledge and resolve alerts while dashboard metrics update.

The application persists state in SQLite and exposes the same workflow through JSON endpoints under `/api`. Authentication, scheduled execution and live enterprise integrations remain roadmap items and are not presented as completed features.

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
python app.py
```

On Windows, activate the environment with `.venv\Scripts\activate`.

Open [http://localhost:5000](http://localhost:5000). The health endpoint is available at [http://localhost:5000/health](http://localhost:5000/health).

## Validation

```bash
python -m compileall app.py src
python -m pytest tests/
```

The integration suite verifies the dashboard, health check, rule creation, rule execution, alert creation, affected records and alert resolution. Some additional files in `tests/` are synthetic-data generators rather than automated assertions.

## Security and privacy

- No production credentials or default administrator password are included.
- Debug mode is disabled unless explicitly enabled with `FLASK_DEBUG`.
- Real corporate, personal and confidential audit data must never be committed.
- Public demonstrations should use synthetic or irreversibly anonymized datasets.
- See [SECURITY.md](../SECURITY.md) for responsible disclosure guidance.

## Roadmap

- [ ] Convert domain models into versioned database migrations
- [ ] Implement authenticated blueprints and authorization tests
- [ ] Add repeatable unit and integration tests to CI
- [ ] Publish reproducible synthetic audit datasets
- [ ] Document rule evaluation with worked examples
- [ ] Add model-performance and explainability reporting
- [ ] Publish a privacy-safe hosted demonstration

## Author

**Doğukan Cihanbeyoğlu**  
Senior Internal Auditor | Audit Analytics | Data Analytics

[LinkedIn](https://www.linkedin.com/in/dogukanc/) · [GitHub](https://github.com/dogukancihanbeyoglu)
