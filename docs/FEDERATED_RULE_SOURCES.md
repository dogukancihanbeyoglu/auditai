# Federated rule sources

`RuleDataSource` adds ordered, aliased sources to an existing `AuditRule` while
preserving the legacy `AuditRule.data_source_id` primary source. Rules without
links continue to load that source unchanged.

The first link must reference the legacy primary source and has no join
definition. Every later link identifies an earlier alias, a field on that
source, a field on the new source, and one of the bounded safe joins:

- join type: `inner` or `left`
- operator: `eq`, `casefold_eq` or `numeric_eq`

Aliases are identifier-shaped and unique per rule. Sources must belong to the
same audit area. No SQL fragment, expression or callable is accepted.

`services.federated_records.load_federated_records` applies each source's
registered mappings, validates fields and joins records in memory. Primary
fields remain unqualified for backward-compatible rules; every source field is
also available as `<alias>.<field>`. Input and output populations default to
10,000 records. A source over the input bound, a many-to-many join over the
output bound, or a mapping conversion error aborts the load instead of silently
auditing a partial population.

To activate federation in the execution layer, call the loader before rule
evaluation when `rule.source_links` is non-empty. Keep the current mapping path
for rules without links, or use the loader's unchanged legacy result and avoid
applying the primary mappings twice.
