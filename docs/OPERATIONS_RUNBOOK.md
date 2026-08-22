# Operations runbook

This runbook targets the privacy-safe hosted demo. It is not a substitute for
an organisation-specific disaster recovery and security assessment.

## Backup and recovery

Never place production backups in the repository. For the local SQLite profile:

```bash
python -m ops.backup backup \
  --database instance/auditai.db \
  --output-dir /secure/auditai-backups
```

Each backup is made with SQLite's online backup API, checked with
`PRAGMA integrity_check`, assigned mode `0600`, and accompanied by a SHA-256
manifest. Copy both files to encrypted storage with a separate retention policy.

Recovery requires the exact resolved target path. An existing database is first
copied to `<database>.pre-restore`, making rollback possible:

```bash
python -m ops.backup restore \
  --backup /secure/auditai-backups/auditai-YYYYMMDDTHHMMSSZ.sqlite3 \
  --manifest /secure/auditai-backups/auditai-YYYYMMDDTHHMMSSZ.json \
  --database instance/auditai.db \
  --confirm-target "$(pwd)/instance/auditai.db"
```

Stop web and worker processes before recovery. After recovery, run `/ready`,
log in, execute a synthetic control, and retain the manifest and recovery log.
Test recovery quarterly in an isolated environment. Hosted PostgreSQL backups
must use the provider's encrypted snapshot/PITR facility; do not pass database
passwords on a command line.

For hosted PostgreSQL, enable automated snapshots and point-in-time recovery in
the provider control plane. Before a release, record the latest restorable point.
To recover: stop the worker, restore into a **new** database, run migrations and
`/ready` against that database, perform synthetic smoke tests, then switch the web
and worker connection secret. Keep the former database read-only until acceptance
is signed off. Never overwrite the only hosted database during a recovery drill.

## Hosted demo process profile

- Web: `gunicorn --workers=2 --threads=4 production:app`
- Worker: `python worker.py --poll-seconds 30`
- Migration release phase: `flask --app app db upgrade`
- Liveness: `GET /health` (process only)
- Readiness: `GET /ready` (database and required schema)

Use separate web and worker processes. Never run an in-process scheduler in
multiple Gunicorn workers. The worker uses database leases to prevent overlapping
control executions and handles `SIGTERM` for hosted-platform shutdown.

Only synthetic or irreversibly anonymised records belong in the public demo.
Disable file/database connectors by default, use a dedicated least-privilege
database, rotate secrets, and set an automatic demo-data expiry policy.

## Performance budget

The offline check is deterministic and sends no data over the network:

```bash
python -m tools.performance_check \
  --records 100000 --budget-ms 2000 --memory-mb 256
```

The command exits non-zero when either budget is exceeded. The default budget is
a CI regression guard for the in-memory engine, not a production capacity claim.
Run representative source and database tests in staging before increasing volume.
