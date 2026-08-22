# Read-only PostgreSQL sources

PostgreSQL source credentials are supplied only through environment profiles.
For a profile named `finance`, configure `AUDITAI_SOURCE_FINANCE_DSN` in the
deployment secret manager. AuditAI stores only `finance`, the selected schema
and table, discovered metadata and the bounded imported snapshot. It never
stores or returns the DSN.

The database account must independently enforce read-only access with only the
minimum required `CONNECT`, `USAGE` and `SELECT` grants. The connector also
opens each session with `default_transaction_read_only=on`, applies a statement
timeout, queries only `information_schema`, and issues a quoted, bounded
`SELECT`. These application controls complement rather than replace database
permissions.

`AUDITAI_POSTGRES_SCHEMAS` is a comma-separated schema allowlist and defaults to
`public`. Discovery results form a second allowlist: arbitrary schema or table
text is never interpolated into SQL.

API flow:

1. `GET /api/connectors/postgresql/finance/tables`
2. `GET /api/connectors/postgresql/finance/columns?schema=public&table=invoices`
3. `POST /api/data-sources/postgresql` with `profile`, `schema`, `table`,
   `audit_area_id` and an optional `limit` (maximum 10,000)

Imports are snapshots. Re-import deliberately creates a new source version so
an audit run remains reproducible. For continuous high-volume operation, use a
dedicated worker and staging table rather than increasing the API limit.
