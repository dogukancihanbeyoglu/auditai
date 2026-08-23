import pytest

from app import create_app
from models import AuditArea, AuditRule, DataSource, db


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "AUTH_REQUIRED": False,
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"})
    with application.app_context():
        area = AuditArea(name="Payments", description="Payment controls")
        source = DataSource(name="Test ledger", audit_area=area,
                            config={"records": [{"id": 1, "amount": 50}, {"id": 2, "amount": 250}]})
        db.session.add_all([area, source])
        db.session.commit()
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


def test_health_and_dashboard(client):
    assert client.get("/health").get_json()["status"] == "ok"
    page = client.get("/")
    assert page.status_code == 200
    assert "Sürekli denetim ve kontrol izleme özeti".encode() in page.data
    assert "Veri Kaynakları".encode() in page.data
    assert b"dashboardExecutiveMetrics" in page.data
    assert "Word yönetici raporunu indir".encode() in page.data


def test_workspace_includes_accessible_rule_editor_and_module_overviews(client):
    page = client.get("/rules")
    assert page.status_code == 200
    assert b'id="ruleEditDialog"' in page.data
    assert b'id="ruleEditForm"' in page.data
    assert "Kontrol bilgilerini düzenle".encode() in page.data
    assert b"openRuleEditor" in page.data
    assert b"professionalizePage" in page.data


def test_dashboard_insights_and_source_overview_contract(client):
    insights = client.get("/api/dashboard/insights")
    assert insights.status_code == 200
    payload = insights.get_json()
    assert len(payload["daily_alarms"]) == 14
    assert payload["source_types"] == {"synthetic": 1}
    assert payload["total_records"] == 2
    assert payload["source_summary"]["coverage_rate"] == 100.0
    assert payload["execution_summary"]["success_rate"] == 100.0
    assert len(payload["execution_daily"]) == 14
    assert {item["href"] for item in payload["action_queue"]} >= {"/alerts", "/rules"}
    assert payload["top_areas"][0]["name"] == "Payments"
    source = client.get("/api/data-sources").get_json()[0]
    assert source["audit_area_name"] == "Payments"
    assert source["mapping_count"] == 0
    assert source["quality_check_count"] == 0


def test_workspace_pages_are_available(client):
    for path, heading in {
        "/data-sources": "Kontrollü veri kümelerini yükleyin ve inceleyin".encode(),
        "/audit-areas": "Denetim evrenini yapılandırın ve yönetin".encode(),
        "/data-governance": "Alanları eşleyin ve kalıcı veri kalitesi kontrolleri çalıştırın".encode(),
        "/rules": "Denetim kontrollerini yapılandırın ve çalıştırın".encode(),
        "/executions": "Değiştirilemez kontrol çalışma geçmişini inceleyin".encode(),
        "/alerts": "İstisnaları yönetin, kanıtları inceleyin ve toplu işlem yapın".encode(),
        "/risk-scores": "Kalıcı kontrol kanıtlarından açıklanabilir risk hesaplayın".encode(),
        "/reports": "Yönetim düzeyinde kontrol analitiği".encode(),
        "/notifications": "Bildirim gönderim durumlarını izleyin".encode(),
        "/audit-logs": "Güvenlik ve iş olaylarını inceleyin".encode(),
        "/settings": "Yerel çalışma alanını yönetin".encode(),
    }.items():
        response = client.get(path)
        assert response.status_code == 200
        assert heading in response.data


def test_create_run_and_resolve_rule(client):
    area = client.get("/api/audit-areas").get_json()[0]
    source = client.get("/api/data-sources").get_json()[0]
    response = client.post("/api/rules", json={"name": "Large payment", "field_name": "amount",
        "operator": ">", "threshold_value": 100, "severity": "high",
        "audit_area_id": area["id"], "data_source_id": source["id"]})
    assert response.status_code == 201
    rule = response.get_json()

    result = client.post(f"/api/rules/{rule['id']}/run").get_json()
    assert result["scanned_records"] == 2
    assert result["matched_records"] == 1
    assert result["alarm_id"] is not None

    alarms = client.get("/api/alarms").get_json()
    assert alarms[0]["affected_records"][0]["id"] == 2
    updated = client.patch(f"/api/alarms/{alarms[0]['id']}/status", json={"status": "resolved"})
    assert updated.status_code == 200
    assert updated.get_json()["status"] == "resolved"


def test_rule_validation(client):
    response = client.post("/api/rules", json={"name": "Incomplete"})
    assert response.status_code == 400
    assert "required" in response.get_json()["error"]


def test_advanced_rule_api_records_execution_history(client):
    area = client.get("/api/audit-areas").get_json()[0]
    source = client.get("/api/data-sources").get_json()[0]
    response = client.post("/api/rules", json={
        "name": "Amount is present", "field_name": "amount", "rule_type": "null",
        "parameters": {"operator": "not_null"}, "severity": "medium",
        "audit_area_id": area["id"], "data_source_id": source["id"],
        "schedule_interval_minutes": 60,
    })
    assert response.status_code == 201
    rule = response.get_json()
    assert rule["rule_type"] == "null"
    assert rule["schedule_interval_minutes"] == 60

    result = client.post(f"/api/rules/{rule['id']}/run").get_json()
    assert result["status"] == "completed"
    assert result["matched_records"] == 2
    history = client.get("/api/rule-executions").get_json()
    assert history[0]["id"] == result["execution_id"]
    assert history[0]["rule_name"] == "Amount is present"

    disabled = client.patch(f"/api/rules/{rule['id']}/schedule", json={"enabled": False})
    assert disabled.status_code == 200
    assert disabled.get_json()["enabled"] is False
    resumed = client.patch(f"/api/rules/{rule['id']}/schedule",
                           json={"enabled": True, "interval_minutes": 30})
    assert resumed.status_code == 200
    assert resumed.get_json()["interval_minutes"] == 30
