#!/usr/bin/env python3
"""Generate privacy-safe SAP-like enterprise databases and register audit sources."""

from __future__ import annotations

import hashlib
import json
import random
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app
from models import AuditArea, AuditRule, DataSource, DataSnapshot, QualityCheck, db, utcnow


SEED = 20260822
OUTPUT = Path(app.instance_path) / "synthetic_enterprise"
COMPANY_CODES = ["1000", "1100", "1200"]
COST_CENTERS = [f"CC-{n:04d}" for n in range(100, 130)]
DEPARTMENTS = ["Finans", "İnsan Kaynakları", "Satın Alma", "Bilgi Teknolojileri", "Operasyon", "Satış"]
FIRST_NAMES = ["Deniz", "Ece", "Can", "Derya", "Mert", "Selin", "Emre", "İpek", "Burak", "Aslı"]
LAST_NAMES = ["Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Aydın", "Arslan", "Koç", "Kurt", "Özdemir"]


def iso(day: date) -> str:
    return day.isoformat()


def columns(connection: sqlite3.Connection, table: str) -> list[dict]:
    rows = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
    mapping = {"INTEGER": "integer", "REAL": "number"}
    return [{"name": row[1], "type": mapping.get(row[2].upper(), "string"),
             "nullable": not bool(row[3])} for row in rows]


def records(connection: sqlite3.Connection, table: str) -> list[dict]:
    connection.row_factory = sqlite3.Row
    return [dict(row) for row in connection.execute(f'SELECT * FROM "{table}"')]


def create_hr(path: Path, rng: random.Random) -> None:
    connection = sqlite3.connect(path)
    connection.executescript("""
    CREATE TABLE employees(employee_id TEXT PRIMARY KEY, company_code TEXT, full_name TEXT,
      department TEXT, cost_center TEXT, manager_id TEXT, hire_date TEXT, termination_date TEXT,
      employment_status TEXT, annual_salary REAL, bank_account TEXT, synthetic_flag INTEGER);
    CREATE TABLE payroll(payroll_id TEXT PRIMARY KEY, employee_id TEXT, period TEXT, gross_pay REAL,
      net_pay REAL, overtime_hours REAL, overtime_pay REAL, payment_date TEXT, bank_account TEXT,
      off_cycle INTEGER, synthetic_flag INTEGER);
    CREATE TABLE time_entries(entry_id TEXT PRIMARY KEY, employee_id TEXT, work_date TEXT,
      hours REAL, weekend_entry INTEGER, approval_status TEXT, synthetic_flag INTEGER);
    """)
    employees = []
    for i in range(1, 501):
        employee_id = f"E{i:06d}"
        status = "inactive" if i in {77, 188, 366} else "active"
        termination = iso(date.today() - timedelta(days=30 + i % 80)) if status == "inactive" else None
        account = f"TR{(i * 7919) % 10**12:012d}"
        if i in {91, 92}: account = "TR000000777777"  # controlled shared-account anomaly
        employees.append((employee_id, rng.choice(COMPANY_CODES),
            f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)} S{i:03d}", rng.choice(DEPARTMENTS),
            rng.choice(COST_CENTERS), f"E{max(1, i // 12):06d}" if i > 12 else None,
            iso(date.today() - timedelta(days=rng.randint(60, 5000))), termination, status,
            round(rng.uniform(420_000, 1_800_000), 2), account, 1))
    connection.executemany("INSERT INTO employees VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", employees)
    payroll = []
    for month_offset in range(6):
        period_day = date.today().replace(day=1) - timedelta(days=month_offset * 30)
        period = period_day.strftime("%Y-%m")
        for i, emp in enumerate(employees, 1):
            gross = round(emp[9] / 12, 2)
            overtime = round(rng.uniform(0, 18), 1)
            off_cycle = 0
            if i in {33, 144, 401} and month_offset == 0:
                overtime, off_cycle = 74.0, 1
            net = round(gross * .71 + overtime * gross / 180 * 1.5, 2)
            if emp[8] == "inactive" and month_offset == 0: net = round(gross * .71, 2)  # terminated paid
            payroll.append((f"PY-{period}-{i:06d}", emp[0], period, gross, net,
                            overtime, round(overtime * gross / 180 * 1.5, 2),
                            iso(period_day + timedelta(days=27)), emp[10], off_cycle, 1))
    connection.executemany("INSERT INTO payroll VALUES(?,?,?,?,?,?,?,?,?,?,?)", payroll)
    entries = []
    for i in range(1, 5001):
        work_day = date.today() - timedelta(days=rng.randint(0, 120))
        hours = round(rng.uniform(6.5, 9.5), 1)
        if i in {101, 202, 303}: hours = 16.0
        entries.append((f"TE{i:08d}", f"E{rng.randint(1,500):06d}", iso(work_day), hours,
                        int(work_day.weekday() >= 5), rng.choice(["approved", "approved", "pending"]), 1))
    connection.executemany("INSERT INTO time_entries VALUES(?,?,?,?,?,?,?)", entries)
    connection.commit(); connection.close()


def create_finance(path: Path, rng: random.Random) -> None:
    connection = sqlite3.connect(path)
    connection.executescript("""
    CREATE TABLE gl_journal(document_id TEXT, line_no INTEGER, company_code TEXT, fiscal_year INTEGER,
      posting_date TEXT, document_type TEXT, account_code TEXT, cost_center TEXT, amount REAL,
      currency TEXT, debit_credit TEXT, entered_by TEXT, entry_timestamp TEXT, manual_entry INTEGER,
      weekend_posting INTEGER, description TEXT, synthetic_flag INTEGER,
      PRIMARY KEY(document_id,line_no));
    CREATE TABLE payments(payment_id TEXT PRIMARY KEY, document_id TEXT, vendor_id TEXT,
      payment_date TEXT, amount REAL, currency TEXT, bank_account TEXT, payment_method TEXT,
      approver_id TEXT, same_user_created_approved INTEGER, synthetic_flag INTEGER);
    """)
    journals = []
    for i in range(1, 3001):
        day = date.today() - timedelta(days=rng.randint(0, 365))
        amount = round(rng.lognormvariate(8.6, 1.05), 2)
        manual = int(rng.random() < .12)
        if i in {444, 1444, 2444}: amount, manual = 4_750_000.0, 1
        user = f"U{rng.randint(1,80):04d}"
        for line, sign in ((1, "D"), (2, "C")):
            journals.append((f"FI-{day.year}-{i:08d}", line, rng.choice(COMPANY_CODES), day.year,
                iso(day), "SA" if manual else "KR", f"{rng.randint(100000,799999)}",
                rng.choice(COST_CENTERS), amount, "TRY", sign, user,
                f"{iso(day)}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:00Z", manual,
                int(day.weekday() >= 5), "Sentetik kurumsal yevmiye kaydı", 1))
    connection.executemany("INSERT INTO gl_journal VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", journals)
    payments = []
    for i in range(1, 1201):
        creator = f"U{rng.randint(1,80):04d}"
        sod = int(i in {88, 488, 888})
        payments.append((f"PAY{i:08d}", f"FI-{date.today().year}-{rng.randint(1,3000):08d}",
            f"V{rng.randint(1,400):06d}", iso(date.today()-timedelta(days=rng.randint(0,180))),
            round(rng.uniform(5_000, 900_000),2), "TRY", f"BANK-{rng.randint(1,20):03d}",
            rng.choice(["EFT","HAVALE"]), creator if sod else f"U{rng.randint(1,80):04d}", sod, 1))
    connection.executemany("INSERT INTO payments VALUES(?,?,?,?,?,?,?,?,?,?,?)", payments)
    connection.commit(); connection.close()


def create_procurement(path: Path, rng: random.Random) -> None:
    connection = sqlite3.connect(path)
    connection.executescript("""
    CREATE TABLE vendors(vendor_id TEXT PRIMARY KEY, vendor_name TEXT, tax_country TEXT,
      bank_account TEXT, created_by TEXT, created_date TEXT, blocked INTEGER, related_employee_id TEXT,
      risk_rating TEXT, synthetic_flag INTEGER);
    CREATE TABLE purchase_orders(po_number TEXT PRIMARY KEY, vendor_id TEXT, company_code TEXT,
      order_date TEXT, buyer_id TEXT, cost_center TEXT, amount REAL, currency TEXT, approval_limit REAL,
      approval_status TEXT, split_order_group TEXT, synthetic_flag INTEGER);
    CREATE TABLE invoices(invoice_id TEXT PRIMARY KEY, invoice_number TEXT, vendor_id TEXT,
      po_number TEXT, invoice_date TEXT, posting_date TEXT, amount REAL, po_amount REAL, currency TEXT,
      quantity_variance REAL, price_variance REAL, duplicate_marker INTEGER, synthetic_flag INTEGER);
    """)
    vendors = []
    for i in range(1, 401):
        employee_link = f"E{i:06d}" if i in {51, 151} else None
        vendors.append((f"V{i:06d}", f"Sentetik Tedarikçi {i:04d} A.Ş.", rng.choice(["TR","TR","DE","NL"]),
          f"VBANK-{i:06d}", f"U{rng.randint(1,80):04d}", iso(date.today()-timedelta(days=rng.randint(30,2500))),
          0, employee_link, "high" if employee_link else rng.choice(["low","low","medium"]), 1))
    connection.executemany("INSERT INTO vendors VALUES(?,?,?,?,?,?,?,?,?,?)", vendors)
    orders=[]
    for i in range(1, 1501):
        amount=round(rng.uniform(5_000,450_000),2); group=None
        if i in {601,602,603}: amount,group=99_500.0,"SPLIT-001"
        orders.append((f"PO{i:08d}",f"V{rng.randint(1,400):06d}",rng.choice(COMPANY_CODES),
          iso(date.today()-timedelta(days=rng.randint(0,240))),f"U{rng.randint(1,80):04d}",rng.choice(COST_CENTERS),
          amount,"TRY",100_000.0,"approved",group,1))
    connection.executemany("INSERT INTO purchase_orders VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",orders)
    invoices=[]
    for i in range(1,1801):
        po=orders[rng.randint(0,len(orders)-1)]; amount=round(po[6]*rng.uniform(.97,1.03),2)
        inv_no=f"INV-{i:08d}"; duplicate=0
        if i in {1001,1002}: inv_no,amount,duplicate="DUP-778899",245_000.0,1
        if i in {1301,1302}: amount=round(po[6]*1.35,2)
        day=date.today()-timedelta(days=rng.randint(0,200))
        invoices.append((f"IV{i:08d}",inv_no,po[1],po[0],iso(day),iso(day+timedelta(days=rng.randint(0,5))),
          amount,po[6],"TRY",round(rng.uniform(-.03,.03),4),round((amount-po[6])/po[6],4),duplicate,1))
    connection.executemany("INSERT INTO invoices VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",invoices)
    connection.commit(); connection.close()


SOURCE_TABLES = {
    "İnsan Kaynakları": [("Kurumsal İK - Personel", "hr.db", "employees"),
                          ("Kurumsal İK - Bordro", "hr.db", "payroll"),
                          ("Kurumsal İK - Zaman Kayıtları", "hr.db", "time_entries")],
    "Finans ve Muhasebe": [("Kurumsal Finans - Yevmiye", "finance.db", "gl_journal"),
                            ("Kurumsal Finans - Ödemeler", "finance.db", "payments")],
    "Satın Alma ve Tedarik": [("Kurumsal Satın Alma - Tedarikçiler", "procurement.db", "vendors"),
                               ("Kurumsal Satın Alma - Siparişler", "procurement.db", "purchase_orders"),
                               ("Kurumsal Satın Alma - Faturalar", "procurement.db", "invoices")],
}


RULES = [
    ("İnsan Kaynakları", "Kurumsal İK - Bordro", "Aşırı fazla mesai", "numeric", "overtime_hours", {"operator": ">", "value": 45}, "high"),
    ("İnsan Kaynakları", "Kurumsal İK - Bordro", "Dönem dışı bordro ödemesi", "numeric", "off_cycle", {"operator": ">", "value": 0}, "high"),
    ("Finans ve Muhasebe", "Kurumsal Finans - Yevmiye", "Yüksek tutarlı manuel kayıt", "numeric", "amount", {"operator": ">", "value": 1_000_000}, "critical"),
    ("Finans ve Muhasebe", "Kurumsal Finans - Ödemeler", "Görevler ayrılığı ihlali", "numeric", "same_user_created_approved", {"operator": ">", "value": 0}, "critical"),
    ("Satın Alma ve Tedarik", "Kurumsal Satın Alma - Faturalar", "Mükerrer fatura numarası", "duplicate", "invoice_number", {"fields": ["invoice_number"]}, "critical"),
    ("Satın Alma ve Tedarik", "Kurumsal Satın Alma - Faturalar", "Yüksek fatura fiyat farkı", "numeric", "price_variance", {"operator": ">", "value": .10}, "high"),
]


def register_sources() -> dict[str, DataSource]:
    source_map = {}
    for area_name, specs in SOURCE_TABLES.items():
        area = AuditArea.query.filter_by(name=area_name).first()
        if not area:
            area = AuditArea(name=area_name, description=f"Tamamen sentetik {area_name.lower()} denetim evreni")
            db.session.add(area); db.session.flush()
        for source_name, filename, table in specs:
            source = DataSource.query.filter_by(name=source_name).first()
            connection = sqlite3.connect(OUTPUT / filename)
            table_records, table_columns = records(connection, table), columns(connection, table)
            connection.close()
            checksum = hashlib.sha256(json.dumps(table_records, sort_keys=True).encode()).hexdigest()
            config = {"records": table_records, "columns": table_columns, "database_file": filename,
                      "table_name": table, "synthetic": True, "generator_seed": SEED}
            if not source:
                source = DataSource(name=source_name, source_type="synthetic_sqlite", audit_area=area,
                                    config=config, last_sync=utcnow())
                db.session.add(source); db.session.flush()
                db.session.add(DataSnapshot(data_source=source, version=1, status="active",
                    row_count=len(table_records), schema_json=table_columns, content_checksum=checksum))
            else:
                source.config, source.last_sync = config, utcnow()
            source_map[source_name] = source
    db.session.flush()
    return source_map


def register_controls(source_map: dict[str, DataSource]) -> None:
    superseded = AuditRule.query.filter_by(name="Sipariş tutarını aşan fatura").first()
    if superseded:
        superseded.is_active = False
        superseded.schedule_enabled = False
    for area_name, source_name, name, rule_type, field, parameters, severity in RULES:
        if AuditRule.query.filter_by(name=name).first(): continue
        source = source_map[source_name]
        db.session.add(AuditRule(name=name, description="Sentetik kurumsal denetim senaryosu",
            rule_type=rule_type, field_name=field, parameters=parameters,
            operator=parameters.get("operator", "=="), threshold_value=float(parameters.get("value", 0)),
            severity=severity, audit_area=source.audit_area, data_source=source))
    for source_name, field in [("Kurumsal İK - Personel", "employee_id"),
                               ("Kurumsal Finans - Yevmiye", "document_id"),
                               ("Kurumsal Satın Alma - Faturalar", "invoice_id")]:
        source = source_map[source_name]
        name = f"{source_name} anahtar zorunluluğu"
        if not QualityCheck.query.filter_by(data_source_id=source.id, name=name).first():
            db.session.add(QualityCheck(data_source=source, name=name, check_type="not_null",
                                       field_name=field, parameters={}))


def main() -> None:
    rng = random.Random(SEED)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for filename, creator in (("hr.db", create_hr), ("finance.db", create_finance),
                              ("procurement.db", create_procurement)):
        path = OUTPUT / filename
        if path.exists(): path.unlink()
        creator(path, rng)
    with app.app_context():
        source_map = register_sources(); register_controls(source_map); db.session.commit()
        print(f"Generated 3 databases and registered {len(source_map)} AuditAI sources.")
        for name, source in source_map.items():
            print(f"- {name}: {len(source.config['records'])} records")


if __name__ == "__main__":
    main()
