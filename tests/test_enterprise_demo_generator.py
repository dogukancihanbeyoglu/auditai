import random
import sqlite3

from tools.generate_enterprise_demo import SEED, create_finance, create_hr, create_procurement


def scalar(path, sql):
    connection = sqlite3.connect(path)
    try:
        return connection.execute(sql).fetchone()[0]
    finally:
        connection.close()


def test_enterprise_generators_create_expected_volumes_and_controlled_anomalies(tmp_path):
    rng = random.Random(SEED)
    hr, finance, procurement = tmp_path / "hr.db", tmp_path / "finance.db", tmp_path / "procurement.db"
    create_hr(hr, rng)
    create_finance(finance, rng)
    create_procurement(procurement, rng)

    assert scalar(hr, "SELECT count(*) FROM employees") == 500
    assert scalar(hr, "SELECT count(*) FROM payroll") == 3000
    assert scalar(hr, "SELECT count(*) FROM payroll WHERE overtime_hours > 45") == 3
    assert scalar(finance, "SELECT count(*) FROM gl_journal") == 6000
    assert scalar(finance, "SELECT count(*) FROM payments WHERE same_user_created_approved = 1") == 3
    assert scalar(procurement, "SELECT count(*) FROM invoices") == 1800
    assert scalar(procurement, "SELECT count(*) FROM invoices WHERE duplicate_marker = 1") == 2
    assert scalar(procurement, "SELECT count(*) FROM vendors WHERE related_employee_id IS NOT NULL") == 2


def test_every_enterprise_table_is_explicitly_marked_synthetic(tmp_path):
    rng = random.Random(SEED)
    databases = [(tmp_path / "hr.db", create_hr), (tmp_path / "finance.db", create_finance),
                 (tmp_path / "procurement.db", create_procurement)]
    for path, creator in databases:
        creator(path, rng)
        connection = sqlite3.connect(path)
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        for table in tables:
            assert connection.execute(f'SELECT min(synthetic_flag) FROM "{table}"').fetchone()[0] == 1
        connection.close()
