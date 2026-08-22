# Data mapping and quality API

The `data_governance` blueprint adds persistent source-column mappings and
repeatable quality checks over the records stored in each `DataSource.config`.
It intentionally does not register itself in the application factory so this
backend package can be integrated alongside the workspace UI change without a
shared-file conflict.

Register it once in `create_app`:

```python
from data_governance import data_governance_bp

app.register_blueprint(data_governance_bp)
```

Then apply the schema revision with `flask --app app db upgrade`.

## Mapping endpoints

- `GET|POST /api/data-sources/<source_id>/mappings`
- `PATCH|DELETE /api/mappings/<mapping_id>`

A mapping connects a discovered `source_column` to a stable `target_field`,
with an optional target type, transformation and required flag. Source columns
are validated against persisted schema metadata and record keys.

## Quality endpoints

- `GET|POST /api/data-sources/<source_id>/quality-checks`
- `PATCH|DELETE /api/quality-checks/<check_id>`
- `POST /api/quality-checks/<check_id>/run`
- `GET /api/quality-checks/<check_id>/runs`

Supported checks are `not_null`, `unique`, `numeric_range` and
`accepted_values`. Every execution scans the source's persisted records and
writes immutable evidence including counts, pass rate and a failure sample
capped at 100 rows. Mutation and execution endpoints require the `auditor`
role; read endpoints accept any authenticated role.
