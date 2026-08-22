# AuditAI

**Data-driven internal audit and compliance analytics platform**

AuditAI is a Flask-based prototype for managing audit areas, connecting structured data sources, defining control rules and generating risk-focused alerts. The project explores how audit expertise, data analytics and automation can work together in a privacy-safe portfolio application.

> Project status: active prototype. Use synthetic or anonymized data only.

## Why AuditAI?

Traditional audit testing often depends on manual sampling. AuditAI is designed to support broader and more repeatable testing through:

- Configurable audit areas and control rules
- Structured data-source management
- Exception and threshold-based testing
- Alert generation and follow-up workflows
- Role-based access for administrators and auditors
- Exportable audit evidence and management reporting
- Foundations for statistical analysis and anomaly detection

## Technology

- Python 3.11+
- Flask, Flask-SQLAlchemy and Flask-Login
- SQLAlchemy with SQLite for local development
- PostgreSQL-compatible production configuration
- pandas and openpyxl for analytical workflows
- ReportLab and python-docx for document output
- pytest-based test utilities

## Project Structure

    auditai/
    ├── app.py                  # Application bootstrap and configuration
    ├── models.py               # Database models
    ├── forms.py                # Form validation
    ├── src/                    # Application source modules
    ├── templates/              # User-interface templates
    ├── tests/                  # Test and synthetic-data utilities
    ├── docs/                   # Technical and user documentation
    ├── pyproject.toml          # Project metadata and dependencies
    └── requirements.txt        # pip-compatible dependencies

## Quick Start

### 1. Clone and create an environment

    git clone https://github.com/dogukancihanbeyoglu/auditai.git
    cd auditai
    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

On Windows, activate the environment with .venv\Scripts\activate.

### 2. Configure required environment variables

    export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
    export DATABASE_URL="sqlite:///auditai.db"
    export ADMIN_EMAIL="admin@example.com"
    export ADMIN_PASSWORD="replace-with-a-strong-password"
    export ADMIN_USERNAME="admin"

SESSION_SECRET is mandatory. An initial administrator is created only when both ADMIN_EMAIL and ADMIN_PASSWORD are provided. Never commit real credentials.

### 3. Run the application

    python app.py

Open http://localhost:5000.

## Testing

    python -m pytest tests/

The test utilities are intended to use synthetic data. Review generated files before sharing them publicly.

## Security and Privacy

- No default password or fallback session secret is included.
- Debug mode is disabled unless explicitly enabled through FLASK_DEBUG.
- Production credentials must be supplied through environment variables or a secret manager.
- Corporate, personal and confidential audit data must never be committed.
- Public demonstrations should use synthetic or irreversibly anonymized datasets.

## Documentation

Additional technical notes and usage guides are available in the [docs](docs/) directory.

## Roadmap

- [ ] Add repeatable automated tests to CI
- [ ] Separate application factory and configuration layers
- [ ] Add reproducible synthetic audit datasets
- [ ] Document rule evaluation with worked examples
- [ ] Add model-performance and explainability reporting
- [ ] Publish a privacy-safe demonstration environment

## License

Licensed under the MIT License. See [docs/LICENSE](docs/LICENSE).

## Author

**Doğukan Cihanbeyoğlu**  
Senior Internal Auditor | Audit Analytics | Data Analytics

[LinkedIn](https://www.linkedin.com/in/dogukanc/) · [GitHub](https://github.com/dogukancihanbeyoglu)
