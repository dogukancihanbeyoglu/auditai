from pathlib import Path


TEMPLATE = Path(__file__).parents[1] / "templates" / "workspace.html"


def source():
    return TEMPLATE.read_text(encoding="utf-8")


def test_designer_contains_complete_guided_workflow():
    html = source()
    for text in (
        "Görsel Çoklu Kaynak Kontrol Tasarımcısı",
        "Kaynaklar ve alias’lar",
        "Join anahtarları",
        "Koşul ağacı",
        "Alarm davranışı",
        "Canlı JSON önizleme",
        "Test sonucu ve açıklayıcı kanıt",
    ):
        assert text in html
    assert 'data-tip="İki veya daha fazla kaynağı' in html
    assert "@media(max-width:900px)" in html
    assert ".compound-shell{display:grid" in html


def test_nested_boolean_builder_and_payload_contract_are_present():
    html = source()
    assert "compoundAddGroup([],\'AND\')" in html
    assert "compoundAddGroup([],\'OR\')" in html
    assert "compoundAddGroup([],\'NOT\')" in html
    assert 'condition:{type:"group",operator:"AND",children:[]}' in html
    assert "sources:compoundState.sources.map" in html
    assert "joins:compoundState.joins.map" in html
    assert 'definition:{version:1,alert_when:"condition_met"' in html
    assert "expression:compoundExpression(compoundState.condition)" in html
    assert 'match_threshold:{operator:">=",value:1,unit:"count"}' in html
    assert 'alert:{mode:$("compoundAlertMode").value' in html


def test_expected_api_contract_and_safe_rendering_are_used():
    html = source()
    assert 'api("/api/compound-rules/test",{method:"POST"' in html
    assert 'api("/api/compound-rules",{method:"POST"' in html
    assert "JSON.stringify(payload)" in html
    assert "esc(x.explanation||x.reason" in html
    assert "esc(JSON.stringify(x.record||x,null,2))" in html
    assert "evidence.slice(0,10)" in html


def test_source_schema_and_validation_guards_exist():
    html = source()
    assert "`/api/data-sources/${sourceId}/schema`" in html
    assert "En az iki kaynak seçin." in html
    assert "benzersiz bir alias" in html
    assert "En az bir join anahtarı" in html
    assert "Boş mantıksal grup bırakılamaz." in html
    assert "NOT grubu tam olarak bir" in html


def test_control_design_center_unifies_sources_governance_and_rules():
    html = source()
    assert 'data-nav="control-design">Kontrol Tasarım Merkezi' in html
    assert '<a href="/data-sources" data-nav="data-sources">' not in html
    assert '<a href="/data-governance" data-nav="data-governance">' not in html
    assert '<a href="/rules" data-nav="rules">' not in html
    for text in (
        "Kontrol Tasarım Merkezi sekmeleri",
        "Bağla ve incele",
        "Eşle ve doğrula",
        "Tasarla, test et, zamanla",
        "Yeni veri kaynağı bağla",
        "Kaynak kataloğu",
        "sourceRecordCount",
    ):
        assert text in html
    assert 'controlPages.includes(page)?\'control-design\':page' in html
