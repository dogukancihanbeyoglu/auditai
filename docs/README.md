# AuditAI

**Privacy-safe internal audit and compliance analytics portfolio prototype**

AuditAI explores how internal-audit expertise, structured data testing and responsible automation can work together. The current version provides a lightweight Flask demonstration, a health endpoint, domain models, form definitions, synthetic-data utilities and detailed concept documentation.

> **Status:** portfolio prototype. Use synthetic or irreversibly anonymized data only.

## What the project demonstrates

- Translating audit requirements into configurable control concepts
- Exception and threshold-based testing workflows
- Risk-focused alert and follow-up design
- Role and audit-domain data modelling
- Foundations for statistical analysis and explainable anomaly detection
- Privacy, credential and public-repository hygiene

## Current scope

The executable application is intentionally lightweight: it serves a professional concept page and a machine-readable health endpoint. The broader workflow documents, models and test-data generators are architectural assets for the next implementation phase. Production authentication, route modules and live enterprise integrations are not represented as complete features.

## Technology

- Python 3.11+
- Flask
- SQLAlchemy and Flask-SQLAlchemy
- pandas and openpyxl
- pytest utilities
- Bootstrap 5

## Project structure

```text
auditai/
├── app.py              # Flask application factory and health endpoint
├── models.py           # Audit-domain data models
├── forms.py            # Form and validation definitions
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

Some files in `tests/` are data-generation utilities rather than automated assertions. Review generated artifacts before publishing them.

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
