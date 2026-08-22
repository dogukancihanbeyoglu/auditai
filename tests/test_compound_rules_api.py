import pytest

from app import create_app
from models import Alarm, AuditArea, AuditRule, DataSource, RuleExecution, db


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "AUTH_REQUIRED": False,
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'compound.db'}"})
    with application.app_context():
        area = AuditArea(name="HR Controls", description="Cross-system HR controls")
        people = DataSource(name="HR employees", audit_area=area, config={"records": [
            {"employee_id": "E1", "status": "active"},
            {"employee_id": "E2", "status": "active"},
        ]})
        access = DataSource(name="Badge logs", audit_area=area, config={"records": [
            {"employee_id": "E1", "inside": True},
        ]})
        db.session.add_all([area, people, access])
        db.session.commit()
        application.config["COMPOUND_TEST_IDS"] = (area.id, people.id, access.id)
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


def payload(app):
    area_id, people_id, access_id = app.config["COMPOUND_TEST_IDS"]
    return {
        "name": "Active employee missing badge record",
        "description": "Compares HR and access populations",
        "severity": "critical", "audit_area_id": area_id,
        "sources": [
            {"data_source_id": people_id, "alias": "hr"},
            {"data_source_id": access_id, "alias": "badge", "join_to_alias": "hr",
             "left_field": "employee_id", "right_field": "employee_id", "join_type": "left",
             "join_operator": "eq"},
        ],
        "definition": {"version": 1, "expression": {"all": [
            {"field": "hr.status", "operator": "eq", "value": "active"},
            {"field": "badge.employee_id", "operator": "is_null"},
        ]}},
    }


def test_preview_create_and_execute_multi_source_compound_control(client, app):
    with app.app_context():
        area_id, people_id, access_id = app.config["COMPOUND_TEST_IDS"]
        assert db.session.get(DataSource, people_id).audit_area_id == area_id
        assert db.session.get(DataSource, access_id).audit_area_id == area_id
    preview = client.post("/api/compound-rules/preview", json=payload(app))
    assert preview.status_code == 200, preview.get_json()
    assert preview.get_json()["source_record_counts"] == {"badge": 1, "hr": 2}
    assert preview.get_json()["joined_records"] == 2
    assert preview.get_json()["selected_records"] == 1
    assert preview.get_json()["evidence"][0]["hr.employee_id"] == "E2"

    created = client.post("/api/compound-rules", json=payload(app))
    assert created.status_code == 201
    body = created.get_json()
    assert len(body["sources"]) == 2
    assert body["definition"]["version"] == 1

    execution = client.post(f"/api/rules/{body['id']}/run")
    assert execution.status_code == 200
    assert execution.get_json()["matched_records"] == 1
    with app.app_context():
        rule = db.session.get(AuditRule, body["id"])
        assert rule.rule_type == "compound"
        assert len(rule.source_links) == 2
        assert RuleExecution.query.filter_by(rule_id=rule.id).one().status == "completed"
        alarm = Alarm.query.filter_by(rule_id=rule.id).one()
        assert alarm.affected_records[0]["badge.employee_id"] is None


def test_invalid_join_and_unsafe_definition_are_rejected(client, app):
    bad_join = payload(app)
    bad_join["sources"][1]["right_field"] = "missing"
    response = client.post("/api/compound-rules", json=bad_join)
    assert response.status_code == 400
    assert "right join field" in response.get_json()["error"]

    bad_rule = payload(app)
    bad_rule["definition"]["expression"] = {"field": "x", "operator": "exec", "value": "x"}
    response = client.post("/api/compound-rules/preview", json=bad_rule)
    assert response.status_code == 400
    assert "unsupported operator" in response.get_json()["error"]
