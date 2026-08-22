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
- `POST /api/data-sources/<source_id>/mappings/preview`
- `PATCH|DELETE /api/mappings/<mapping_id>`

A mapping connects a discovered `source_column` to a stable `target_field`,
with an optional target type, transformation and required flag. Source columns
are validated against persisted schema metadata and record keys.

The preview endpoint accepts `{"limit": 25}` with a maximum of 100. It returns
raw fields plus mapped target fields, along with row/field-specific conversion
errors. Error values are bounded and at most 100 errors are returned. Supported
transformations are deliberately code-free: trim, lowercase, uppercase,
integer and finite-number conversion. Target types also support strict boolean,
ISO date and ISO datetime conversion.

Rule execution uses the same mapping service. Raw fields remain available for
backward compatibility, while canonical target fields can be selected by new
rules. If conversion fails for a field actually consumed by a rule (including
comparison, duplicate and anomaly fields), the execution fails explicitly
instead of silently reducing the audited population.

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
