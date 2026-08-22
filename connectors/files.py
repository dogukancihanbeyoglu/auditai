"""Full-refresh adapter for versioned uploaded file artifacts."""

from connectors.base import FetchResult, SourceFetchError
from models import DataSourceArtifact, db


class ArtifactRefreshConnector:
    def fetch_full(self, source, max_records: int) -> FetchResult:
        artifact_id = (source.config or {}).get("active_artifact_id")
        artifact = db.session.get(DataSourceArtifact, artifact_id) if artifact_id else None
        if not artifact or artifact.data_source_id != source.id:
            raise SourceFetchError("source has no active versioned file artifact")
        try:
            # Imported lazily to keep the connector contract independent from Flask routes.
            from data_sources import parse_csv, parse_sqlite, parse_xlsx
            if source.source_type == "csv":
                records, columns = parse_csv(artifact.content, max_records, 100)
            elif source.source_type == "xlsx":
                records, columns, _ = parse_xlsx(
                    artifact.content, max_records, 100, (source.config or {}).get("sheet_name"))
            elif source.source_type == "sqlite":
                records, columns, _, _ = parse_sqlite(
                    artifact.content, (source.config or {}).get("table_name"), max_records, 100)
            else:
                raise SourceFetchError("artifact source type is not supported")
            return FetchResult(records=records, columns=columns)
        except SourceFetchError:
            raise
        except Exception as exc:
            raise SourceFetchError("versioned file artifact could not be refreshed") from exc
