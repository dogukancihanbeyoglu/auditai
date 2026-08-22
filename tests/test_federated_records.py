import pytest
from flask import Flask
from sqlalchemy.exc import IntegrityError

from models import AuditArea, AuditRule, DataSource, FieldMapping, RuleDataSource, db
from services.federated_records import FederatedLoadError, load_federated_records
from services.rule_engine import evaluate_records


@pytest.fixture()
def app(tmp_path):
    application = Flask(__name__)
    application.config.update(TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'federated.db'}")
    db.init_app(application)
    with application.app_context():
        db.create_all()
        area = AuditArea(name="Procurement")
        invoices = DataSource(name="Invoices", audit_area=area, config={"records": [
            {"invoice_id": "I-1", "vendor_id": "V-1", "amount": 50},
            {"invoice_id": "I-2", "vendor_id": "v-2", "amount": 250},
            {"invoice_id": "I-3", "vendor_id": "V-404", "amount": 900},
        ]})
        vendors = DataSource(name="Vendors", audit_area=area, config={"records": [
            {"vendor_id": "v-1", "risk": "low"}, {"vendor_id": "V-2", "risk": "high"},
        ]})
        rule = AuditRule(name="High-risk large invoices", field_name="amount", operator=">",
            threshold_value=100, rule_type="numeric", parameters={"operator": ">", "value": 100},
            severity="high", audit_area=area, data_source=invoices)
        db.session.add_all([area, invoices, vendors, rule])
        db.session.flush()
        db.session.add_all([
            RuleDataSource(rule=rule, data_source=invoices, alias="invoice", priority=0),
            RuleDataSource(rule=rule, data_source=vendors, alias="vendor", priority=1,
                join_to_alias="invoice", left_field="vendor_id", right_field="vendor_id",
                join_type="inner", join_operator="casefold_eq"),
        ])
        db.session.commit()
    return application


def test_inner_join_produces_namespaced_fields_and_rule_ready_records(app):
    with app.app_context():
        result = load_federated_records(AuditRule.query.one())
        assert result.source_aliases == ["invoice", "vendor"]
        assert result.source_record_counts == {"invoice": 3, "vendor": 2}
        assert len(result.records) == 2
        assert result.records[1]["invoice.invoice_id"] == "I-2"
        assert result.records[1]["vendor.risk"] == "high"
        assert result.records[1]["amount"] == 250
        evaluated = evaluate_records(result.records, rule_type="text", field="vendor.risk",
                                     parameters={"operator": "equals", "value": "high"})
        assert evaluated.matched_records == 1


def test_left_join_retains_unmatched_primary_record(app):
    with app.app_context():
        link = RuleDataSource.query.filter_by(alias="vendor").one()
        link.join_type = "left"
        db.session.commit()
        result = load_federated_records(AuditRule.query.one())
        assert len(result.records) == 3
        unmatched = next(item for item in result.records if item["invoice.invoice_id"] == "I-3")
        assert unmatched["vendor.vendor_id"] is None
        assert unmatched["vendor.risk"] is None


def test_legacy_rule_without_links_uses_primary_source_unchanged(app):
    with app.app_context():
        rule = AuditRule.query.one()
        RuleDataSource.query.delete()
        db.session.commit()
        result = load_federated_records(rule)
        assert result.source_aliases == []
        assert result.source_record_counts == {"primary": 3}
        assert result.records[0] == {"invoice_id": "I-1", "vendor_id": "V-1", "amount": 50}


def test_source_mappings_are_applied_before_join(app):
    with app.app_context():
        vendors = DataSource.query.filter_by(name="Vendors").one()
        db.session.add(FieldMapping(data_source=vendors, source_column="vendor_id",
            target_field="canonical_vendor_id", target_type="string", transformation="lower"))
        link = RuleDataSource.query.filter_by(alias="vendor").one()
        link.right_field = "canonical_vendor_id"
        link.join_operator = "casefold_eq"
        db.session.commit()
        result = load_federated_records(AuditRule.query.one())
        assert result.records[0]["vendor.canonical_vendor_id"] == "v-1"


def test_rejects_unsafe_or_invalid_join_definitions(app):
    with app.app_context():
        link = RuleDataSource.query.filter_by(alias="vendor").one()
        link.alias = "vendor; DROP TABLE users"
        db.session.flush()
        with pytest.raises(FederatedLoadError, match="safe identifier"):
            load_federated_records(AuditRule.query.one())
        db.session.rollback()

        link = RuleDataSource.query.filter_by(alias="vendor").one()
        link.join_to_alias = "missing"
        db.session.flush()
        with pytest.raises(FederatedLoadError, match="earlier source"):
            load_federated_records(AuditRule.query.one())


def test_join_explosion_and_source_population_are_bounded(app):
    with app.app_context():
        vendors = DataSource.query.filter_by(name="Vendors").one()
        vendors.config = {"records": [{"vendor_id": "V-1", "risk": index} for index in range(5)]}
        db.session.commit()
        with pytest.raises(FederatedLoadError, match="output record limit"):
            load_federated_records(AuditRule.query.one(), max_output_records=2)
        with pytest.raises(FederatedLoadError, match="input record limit"):
            load_federated_records(AuditRule.query.one(), max_source_records=2)


def test_database_constraints_prevent_duplicate_alias(app):
    with app.app_context():
        rule = AuditRule.query.one()
        vendors = DataSource.query.filter_by(name="Vendors").one()
        extra = DataSource(name="Extra", audit_area=rule.audit_area, config={"records": []})
        db.session.add(extra)
        db.session.flush()
        db.session.add(RuleDataSource(rule=rule, data_source=extra, alias="vendor", priority=2,
            join_to_alias="invoice", left_field="vendor_id", right_field="vendor_id"))
        with pytest.raises(IntegrityError):
            db.session.commit()
