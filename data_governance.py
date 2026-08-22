"""Data mapping and persistent data-quality APIs."""

from __future__ import annotations

from collections import Counter
from typing import Any

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from models import DataSource, FieldMapping, QualityCheck, QualityCheckRun, db, utcnow
from security import require_role
from services.mapping import MappingApplicationError, apply_mappings


data_governance_bp = Blueprint("data_governance", __name__)
TARGET_TYPES = {"string", "integer", "number", "boolean", "date", "datetime"}
TRANSFORMATIONS = {"none", "trim", "lower", "upper", "to_integer", "to_number"}
CHECK_TYPES = {"not_null", "unique", "numeric_range", "accepted_values"}


def _source_fields(source: DataSource) -> set[str]:
    config = source.config or {}
    fields = {str(item.get("name")) for item in config.get("columns", []) if item.get("name")}
    for record in config.get("records", []):
        fields.update(str(key) for key in record)
    return fields


def _mapping_json(mapping: FieldMapping) -> dict[str, Any]:
    return {"id": mapping.id, "data_source_id": mapping.data_source_id,
            "source_column": mapping.source_column, "target_field": mapping.target_field,
            "target_type": mapping.target_type, "transformation": mapping.transformation,
            "is_required": mapping.is_required,
            "created_at": mapping.created_at.isoformat(), "updated_at": mapping.updated_at.isoformat()}


def _check_json(check: QualityCheck) -> dict[str, Any]:
    return {"id": check.id, "data_source_id": check.data_source_id, "name": check.name,
            "check_type": check.check_type, "field_name": check.field_name,
            "parameters": check.parameters or {}, "is_active": check.is_active,
            "last_run_at": check.last_run_at.isoformat() if check.last_run_at else None}


def _run_json(run: QualityCheckRun) -> dict[str, Any]:
    return {"id": run.id, "quality_check_id": run.quality_check_id, "status": run.status,
            "scanned_records": run.scanned_records, "failed_records": run.failed_records,
            "pass_rate": run.pass_rate, "failure_sample": run.failure_sample,
            "error_message": run.error_message,
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None}


def _validate_mapping(source: DataSource, payload: dict, partial: bool = False) -> dict:
    result = {}
    for field in ("source_column", "target_field"):
        if field in payload:
            value = str(payload[field]).strip()
            if not value or len(value) > 128:
                raise ValueError(f"{field} must contain 1-128 characters")
            result[field] = value
        elif not partial:
            raise ValueError(f"{field} is required")
    source_column = result.get("source_column")
    if source_column and source_column not in _source_fields(source):
        raise ValueError("source_column does not exist in the persisted source schema")
    if "target_type" in payload or not partial:
        target_type = str(payload.get("target_type", "string"))
        if target_type not in TARGET_TYPES:
            raise ValueError("invalid target_type")
        result["target_type"] = target_type
    if "transformation" in payload or not partial:
        transformation = str(payload.get("transformation", "none"))
        if transformation not in TRANSFORMATIONS:
            raise ValueError("invalid transformation")
        result["transformation"] = transformation
    if "is_required" in payload:
        if not isinstance(payload["is_required"], bool):
            raise ValueError("is_required must be boolean")
        result["is_required"] = payload["is_required"]
    return result


def _validate_check(source: DataSource, payload: dict, partial: bool = False) -> dict:
    result = {}
    if "name" in payload:
        name = str(payload["name"]).strip()
        if not name or len(name) > 128:
            raise ValueError("name must contain 1-128 characters")
        result["name"] = name
    elif not partial:
        raise ValueError("name is required")
    if "check_type" in payload:
        check_type = str(payload["check_type"])
        if check_type not in CHECK_TYPES:
            raise ValueError("invalid check_type")
        result["check_type"] = check_type
    elif not partial:
        raise ValueError("check_type is required")
    if "field_name" in payload:
        field_name = str(payload["field_name"]).strip()
        if field_name not in _source_fields(source):
            raise ValueError("field_name does not exist in the persisted source schema")
        result["field_name"] = field_name
    elif not partial:
        raise ValueError("field_name is required")
    if "parameters" in payload or not partial:
        parameters = payload.get("parameters", {})
        if not isinstance(parameters, dict):
            raise ValueError("parameters must be an object")
        result["parameters"] = parameters
    if "is_active" in payload:
        if not isinstance(payload["is_active"], bool):
            raise ValueError("is_active must be boolean")
        result["is_active"] = payload["is_active"]
    return result


def _validate_check_parameters(check_type: str, parameters: dict) -> None:
    if check_type == "numeric_range":
        if parameters.get("min") is None and parameters.get("max") is None:
            raise ValueError("numeric_range requires min and/or max")
        for name in ("min", "max"):
            if parameters.get(name) is not None:
                try:
                    float(parameters[name])
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"{name} must be numeric") from exc
    elif check_type == "accepted_values":
        if not isinstance(parameters.get("values"), list) or not parameters["values"]:
            raise ValueError("accepted_values requires a non-empty values list")
        if len(parameters["values"]) > 1_000:
            raise ValueError("accepted_values supports at most 1000 values")


def execute_quality_check(check: QualityCheck) -> QualityCheckRun:
    records = list((check.data_source.config or {}).get("records", []))
    started = utcnow()
    failures: list[dict[str, Any]] = []
    field = check.field_name
    parameters = check.parameters or {}
    counts = Counter(_stable_value(record.get(field)) for record in records
                     if record.get(field) not in (None, "")) if check.check_type == "unique" else Counter()
    accepted = {_stable_value(item) for item in parameters.get("values", [])}

    for index, record in enumerate(records):
        value = record.get(field)
        failed = False
        if check.check_type == "not_null":
            failed = value is None or (isinstance(value, str) and not value.strip())
        elif check.check_type == "unique":
            failed = value not in (None, "") and counts[_stable_value(value)] > 1
        elif check.check_type == "numeric_range":
            try:
                number = float(value)
                failed = ((parameters.get("min") is not None and number < float(parameters["min"])) or
                          (parameters.get("max") is not None and number > float(parameters["max"])))
            except (TypeError, ValueError):
                failed = True
        elif check.check_type == "accepted_values":
            failed = _stable_value(value) not in accepted
        if failed:
            failures.append({"row_index": index, "value": value})

    scanned = len(records)
    failed_count = len(failures)
    run = QualityCheckRun(quality_check=check, status="passed" if failed_count == 0 else "failed",
                          scanned_records=scanned, failed_records=failed_count,
                          pass_rate=round(((scanned - failed_count) / scanned * 100), 2) if scanned else 100.0,
                          failure_sample=failures[:100], started_at=started, finished_at=utcnow())
    check.last_run_at = run.finished_at
    db.session.add(run)
    db.session.commit()
    return run


def _stable_value(value: Any) -> str:
    return f"{type(value).__name__}:{value!r}"


@data_governance_bp.get("/api/data-sources/<int:source_id>/mappings")
@require_role()
def list_mappings(source_id):
    source = db.get_or_404(DataSource, source_id)
    return jsonify([_mapping_json(item) for item in source.field_mappings])


@data_governance_bp.post("/api/data-sources/<int:source_id>/mappings")
@require_role("auditor")
def create_mapping(source_id):
    source = db.get_or_404(DataSource, source_id)
    try:
        values = _validate_mapping(source, request.get_json(silent=True) or {})
        mapping = FieldMapping(data_source=source, **values)
        db.session.add(mapping)
        db.session.commit()
        return jsonify(_mapping_json(mapping)), 201
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="mapping already exists"), 409


@data_governance_bp.patch("/api/mappings/<int:mapping_id>")
@require_role("auditor")
def update_mapping(mapping_id):
    mapping = db.get_or_404(FieldMapping, mapping_id)
    try:
        values = _validate_mapping(mapping.data_source, request.get_json(silent=True) or {}, partial=True)
        for key, value in values.items():
            setattr(mapping, key, value)
        db.session.commit()
        return jsonify(_mapping_json(mapping))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="mapping already exists"), 409


@data_governance_bp.delete("/api/mappings/<int:mapping_id>")
@require_role("auditor")
def delete_mapping(mapping_id):
    mapping = db.get_or_404(FieldMapping, mapping_id)
    db.session.delete(mapping)
    db.session.commit()
    return "", 204


@data_governance_bp.post("/api/data-sources/<int:source_id>/mappings/preview")
@require_role()
def preview_mappings(source_id):
    source = db.get_or_404(DataSource, source_id)
    payload = request.get_json(silent=True) or {}
    try:
        limit = int(payload.get("limit", 25))
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        result = apply_mappings((source.config or {}).get("records", []),
                                list(source.field_mappings), limit=limit)
        return jsonify(records=result.records, errors=[item.to_dict() for item in result.errors],
                       total_errors=result.total_errors, errors_truncated=result.total_errors > len(result.errors),
                       input_record_count=result.input_record_count,
                       output_record_count=len(result.records), truncated=result.truncated)
    except (MappingApplicationError, TypeError, ValueError) as exc:
        return jsonify(error=str(exc)), 400


@data_governance_bp.get("/api/data-sources/<int:source_id>/quality-checks")
@require_role()
def list_checks(source_id):
    source = db.get_or_404(DataSource, source_id)
    return jsonify([_check_json(item) for item in source.quality_checks])


@data_governance_bp.post("/api/data-sources/<int:source_id>/quality-checks")
@require_role("auditor")
def create_check(source_id):
    source = db.get_or_404(DataSource, source_id)
    try:
        values = _validate_check(source, request.get_json(silent=True) or {})
        _validate_check_parameters(values["check_type"], values["parameters"])
        check = QualityCheck(data_source=source, **values)
        db.session.add(check)
        db.session.commit()
        return jsonify(_check_json(check)), 201
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="quality check name already exists for this source"), 409


@data_governance_bp.patch("/api/quality-checks/<int:check_id>")
@require_role("auditor")
def update_check(check_id):
    check = db.get_or_404(QualityCheck, check_id)
    try:
        values = _validate_check(check.data_source, request.get_json(silent=True) or {}, partial=True)
        candidate_type = values.get("check_type", check.check_type)
        candidate_parameters = values.get("parameters", check.parameters or {})
        _validate_check_parameters(candidate_type, candidate_parameters)
        for key, value in values.items():
            setattr(check, key, value)
        db.session.commit()
        return jsonify(_check_json(check))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="quality check name already exists for this source"), 409


@data_governance_bp.delete("/api/quality-checks/<int:check_id>")
@require_role("auditor")
def delete_check(check_id):
    check = db.get_or_404(QualityCheck, check_id)
    db.session.delete(check)
    db.session.commit()
    return "", 204


@data_governance_bp.post("/api/quality-checks/<int:check_id>/run")
@require_role("auditor")
def run_check(check_id):
    check = db.get_or_404(QualityCheck, check_id)
    if not check.is_active:
        return jsonify(error="quality check is inactive"), 409
    return jsonify(_run_json(execute_quality_check(check))), 201


@data_governance_bp.get("/api/quality-checks/<int:check_id>/runs")
@require_role()
def list_check_runs(check_id):
    check = db.get_or_404(QualityCheck, check_id)
    runs = QualityCheckRun.query.filter_by(quality_check_id=check.id).order_by(
        QualityCheckRun.started_at.desc()).limit(100).all()
    return jsonify([_run_json(item) for item in runs])
