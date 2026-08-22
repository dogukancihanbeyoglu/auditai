# Full-refresh source synchronization

The source-sync package creates immutable snapshot metadata and persistent run
evidence while keeping the currently active records in `DataSource.config` for
compatibility with the existing rule and quality engines.

Register the independent blueprint in the application factory:

```python
from source_sync import source_sync_bp

app.register_blueprint(source_sync_bp)
```

Apply the schema revision before enabling the endpoints:

```bash
flask --app app db upgrade
```

## API

- `PATCH /api/data-sources/<id>/sync-policy` accepts `is_enabled`,
  `refresh_mode` (`full` only) and `max_records` (1–10,000).
- `POST /api/data-sources/<id>/sync` performs a bounded full refresh. Clients
  should send a stable `Idempotency-Key` for every logical request.
- `GET /api/data-sources/<id>/sync-runs` returns the latest 100 attempts.

Mutations require the auditor role and create audit events. A conditional,
expiring database lock permits only one refresh per source. The run is created
before external fetching; new records, schema, checksum, snapshot activation,
run completion and lock release are committed together only after a complete
fetch. On failure the previous records and active snapshot remain unchanged,
the run is marked failed with a redacted message, and the lock is released.

PostgreSQL sources are fetched again through their environment-only connection
profile. Synthetic and file/SQLite sources can currently be re-snapshotted from
their persisted records because original uploaded files are intentionally not
retained. A later file-object-store adapter can implement true file re-fetching
without changing the connector contract.
