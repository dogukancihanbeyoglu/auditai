from app import create_app
from models import Alarm, AuditArea, AuditRule, DataSource, db
from services.execution import run_rule


def test_anomaly_rule_runs_real_detector_and_persists_evidence(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'anomaly.db'}"})
    with app.app_context():
        area = AuditArea(name="Payments")
        records = [{"id": index, "amount": 10 + (index % 2)} for index in range(20)]
        records.append({"id": 99, "amount": 10_000})
        source = DataSource(name="Ledger", audit_area=area, config={"records": records})
        rule = AuditRule(
            name="Payment outliers", field_name="amount", operator=">", threshold_value=0,
            rule_type="anomaly", parameters={"detector": "statistical_zscore", "fields": ["amount"],
                                             "sensitivity": 0.5, "confidence_threshold": 0.8},
            severity="high", audit_area=area, data_source=source,
        )
        db.session.add_all([area, source, rule])
        db.session.commit()

        execution = run_rule(rule)

        assert execution.status == "completed"
        assert execution.scanned_records == 21
        assert execution.matched_records == 1
        evidence = Alarm.query.one().affected_records
        assert evidence[0]["record_id"] == 99
        assert evidence[0]["contributing_fields"]["amount"] > 4


def test_anomaly_rule_reports_unsupported_detector_as_failed(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'unsupported.db'}"})
    with app.app_context():
        area = AuditArea(name="Payments")
        source = DataSource(name="Ledger", audit_area=area, config={"records": [{"amount": 1}]})
        rule = AuditRule(
            name="Unknown detector", field_name="amount", operator=">", threshold_value=0,
            rule_type="anomaly", parameters={"detector": "made_up", "fields": ["amount"]},
            severity="high", audit_area=area, data_source=source,
        )
        db.session.add_all([area, source, rule])
        db.session.commit()

        execution = run_rule(rule)

        assert execution.status == "failed"
        assert "unsupported detector" in execution.error_message
