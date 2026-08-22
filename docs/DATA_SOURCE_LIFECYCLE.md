# Data source lifecycle

## Versioned CSV and XLSX files

`POST /api/data-sources/upload` validates and parses a bounded CSV/XLSX upload,
stores its bytes as a `DataSourceArtifact`, and activates version 1 of both the
artifact and snapshot metadata. Each artifact has a SHA-256 checksum, byte
size, media type and sanitized display filename. AuditAI never persists or
opens a user-supplied filesystem path.

`POST /api/data-sources/<id>/reload` accepts a replacement file of the same
type. It parses the complete bounded file before atomically creating the next
artifact and snapshot versions, superseding the previous snapshot and changing
the active records. Uploading identical bytes again is rejected by checksum.
The source-sync service reparses the active immutable artifact instead of
copying mutable JSON snapshot records.

## SQLite workflow

All SQLite operations accept an uploaded database file and open only a
temporary read-only connection. Table names must come from discovered user
tables and are quoted before use.

1. `POST /api/connectors/sqlite/test`
2. `POST /api/connectors/sqlite/tables`
3. `POST /api/connectors/sqlite/preview` with `table_name` and optional `limit`
4. `POST /api/data-sources/sqlite` with `audit_area_id`, `table_name` and file

## PostgreSQL workflow

Credentials remain in environment-only named profiles and are never returned
or persisted. Sessions are read-only with connection and statement timeouts;
schemas and tables are allowlisted and identifiers are quoted.

1. `GET /api/connectors/postgresql/<profile>/test`
2. `GET /api/connectors/postgresql/<profile>/tables`
3. `GET /api/connectors/postgresql/<profile>/columns?schema=...&table=...`
4. `GET /api/connectors/postgresql/<profile>/preview?schema=...&table=...&limit=...`
5. `POST /api/data-sources/postgresql`
