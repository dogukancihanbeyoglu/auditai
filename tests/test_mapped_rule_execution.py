import pytest

from app import create_app
from models import Alarm, AuditArea, AuditRule, DataSource, FieldMapping, RuleExecution, db
from services.execution import run_rule


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "AUTH_REQUIRED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'mapped-rules.db'}"})
    with application.app_context():
        area = AuditArea(name="Finance")
        source = DataSource(name="Ledger", audit_area=area, config={"records": [
            {"id": 1, "amount_text": "50"}, {"id": 2, "amount_text": "250"}]})
        mapping = FieldMapping(data_source=source, source_column="amount_text",
                               target_field="canonical_amount", target_type="number",
                               transformation="to_number", is_required=True)
        rule = AuditRule(name="Large mapped amount", field_name="canonical_amount", operator=">",
                         threshold_value=100, rule_type="numeric",
                         parameters={"operator": ">", "value": 100}, severity="high",
                         audit_area=area, data_source=source)
        db.session.add_all([area, source, mapping, rule])
        db.session.commit()
    return application


def test_rule_engine_uses_mapped_target_fields(app):
    with app.app_context():
        execution = run_rule(AuditRule.query.one())
        assert execution.status == "completed"
        assert execution.scanned_records == 2
        assert execution.matched_records == 1
        evidence = Alarm.query.one().affected_records[0]
        assert evidence["id"] == 2
        assert evidence["canonical_amount"] == 250.0
        assert evidence["amount_text"] == "250"


def test_relevant_mapping_failure_fails_rule_instead_of_silently_skipping(app):
    with app.app_context():
        source = DataSource.query.one()
        source.config = {"records": [{"id": 1, "amount_text": "invalid"}]}
        db.session.commit()
        execution = run_rule(AuditRule.query.one())
        assert execution.status == "failed"
        assert "mapping failed for rule field canonical_amount at row 0" in execution.error_message
        assert RuleExecution.query.count() == 1
        assert Alarm.query.count() == 0
