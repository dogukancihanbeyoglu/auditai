# Database and deployment

AuditAI uses Alembic through Flask-Migrate. Schema changes must be committed as
versioned migrations; production startup never creates tables implicitly.

## Local migration workflow

```bash
uv sync
flask --app app db upgrade
flask --app app run
```

After changing a model, generate and review a revision before committing it:

```bash
flask --app app db migrate -m "describe the schema change"
flask --app app db upgrade
flask --app app db downgrade
flask --app app db upgrade
```

## PostgreSQL production profile

`render.yaml` provisions a PostgreSQL service, runs `flask --app app db upgrade`
before deployment and starts Gunicorn. The application refuses to start in
production unless all of these conditions are met:

- `AUDITAI_ENV=production`
- `DATABASE_URL` is a PostgreSQL URL
- `SESSION_SECRET` contains at least 32 characters
- `COOKIE_SECURE=true`

Provider-style `postgres://` and `postgresql://` URLs are normalized to the
SQLAlchemy psycopg 3 dialect. Never put a real URL or secret in `.env.example`,
source control, logs, screenshots or support tickets.

Back up the database and test both upgrade and downgrade paths in a staging
environment before applying a migration to production.
