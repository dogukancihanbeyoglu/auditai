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
    CREATE TABLE access_events(event_id TEXT PRIMARY KEY, employee_id TEXT, event_time TEXT,
      direction TEXT, gate_code TEXT, card_status TEXT, synthetic_flag INTEGER);
    CREATE TABLE attendance_compliance(control_id TEXT PRIMARY KEY, employee_id TEXT, work_date TEXT,
      first_entry TEXT, last_exit TEXT, core_absence_minutes INTEGER, leave_notification INTEGER,
      after_hours_minutes INTEGER, manager_overtime_approval INTEGER,
      unreported_core_absence INTEGER, unapproved_after_hours INTEGER, synthetic_flag INTEGER);
    CREATE TABLE leave_compliance(control_id TEXT PRIMARY KEY, employee_id TEXT, leave_year INTEGER,
      annual_entitlement REAL, used_days REAL, requested_days REAL, projected_balance REAL,
      negative_balance INTEGER, negative_balance_form_required INTEGER,
      negative_balance_form_delivered INTEGER, undocumented_negative_leave INTEGER, synthetic_flag INTEGER);
    CREATE TABLE promotion_eligibility(control_id TEXT PRIMARY KEY, employee_id TEXT, department TEXT,
      years_in_grade REAL, promotion_cycle_years REAL, performance_score REAL,
      disciplinary_action INTEGER, eligible_for_promotion INTEGER, promoted INTEGER,
      promotion_overdue INTEGER, synthetic_flag INTEGER);
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
    access_events, attendance, leave_rows, promotions = [], [], [], []
    for i, emp in enumerate(employees, 1):
        work_day = date.today() - timedelta(days=i % 25)
        entry_hour, exit_hour = 8 + (i % 3), 17 + (i % 4)
        core_absence = 0
        leave_notice, overtime_approval = 1, 1
        if i in {21, 121, 221, 321}: core_absence, leave_notice = 150, 0
        after_hours = max(0, (exit_hour - 18) * 60)
        if i in {42, 142, 242}: exit_hour, after_hours, overtime_approval = 23, 300, 0
        access_events.extend([
            (f"AE-{i:06d}-IN", emp[0], f"{iso(work_day)}T{entry_hour:02d}:05:00Z", "IN", "HQ-01", "active", 1),
            (f"AE-{i:06d}-OUT", emp[0], f"{iso(work_day)}T{exit_hour:02d}:10:00Z", "OUT", "HQ-01", "active", 1),
        ])
        attendance.append((f"AC{i:06d}", emp[0], iso(work_day), f"{entry_hour:02d}:05", f"{exit_hour:02d}:10",
            core_absence, leave_notice, after_hours, overtime_approval,
            int(core_absence > 60 and not leave_notice), int(after_hours > 120 and not overtime_approval), 1))
        entitlement, used, requested = 20.0, round(rng.uniform(2, 19), 1), round(rng.uniform(1, 5), 1)
        form_delivered = 1
        if i in {63, 163, 263}: used, requested, form_delivered = 20.0, 5.0, 0
        projected = round(entitlement - used - requested, 1)
        negative = int(projected < 0)
        leave_rows.append((f"LC{i:06d}", emp[0], date.today().year, entitlement, used, requested,
            projected, negative, negative, form_delivered, int(negative and not form_delivered), 1))
        years = round(rng.uniform(.5, 7), 1); score = round(rng.uniform(2.2, 5), 2)
        disciplinary = 0
        eligible = int(years >= 3 and score >= 4 and not disciplinary)
        promoted = eligible
        if i in {84, 184, 284, 384}:
            years, score, eligible, promoted = 5.5, 4.7, 1, 0
        promotions.append((f"PC{i:06d}", emp[0], emp[3], years, 3.0, score, disciplinary,
                           eligible, promoted, int(eligible and not promoted), 1))
    connection.executemany("INSERT INTO access_events VALUES(?,?,?,?,?,?,?)", access_events)
    connection.executemany("INSERT INTO attendance_compliance VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", attendance)
    connection.executemany("INSERT INTO leave_compliance VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", leave_rows)
    connection.executemany("INSERT INTO promotion_eligibility VALUES(?,?,?,?,?,?,?,?,?,?,?)", promotions)
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
    CREATE TABLE sat_requisitions(sat_number TEXT PRIMARY KEY, requester_id TEXT, company_code TEXT,
      cost_center TEXT, request_date TEXT, material_group TEXT, amount REAL, currency TEXT,
      budget_available INTEGER, manager_approved INTEGER, technical_spec_attached INTEGER,
      retroactive_request INTEGER, synthetic_flag INTEGER);
    CREATE TABLE sas_compliance(control_id TEXT PRIMARY KEY, sas_number TEXT, sat_number TEXT,
      vendor_id TEXT, buyer_id TEXT, order_date TEXT, amount REAL, approval_limit REAL,
      sat_exists INTEGER, approved_sat INTEGER, required_bid_count INTEGER, received_bid_count INTEGER,
      contract_exists INTEGER, approval_complete INTEGER, sas_without_sat INTEGER,
      insufficient_competition INTEGER, approval_limit_breach INTEGER, synthetic_flag INTEGER);
    CREATE TABLE receipt_compliance(control_id TEXT PRIMARY KEY, sas_number TEXT, invoice_id TEXT,
      receipt_date TEXT, invoice_date TEXT, ordered_quantity REAL, received_quantity REAL,
      invoiced_quantity REAL, service_acceptance_approved INTEGER, three_way_match_exception INTEGER,
      invoice_before_receipt INTEGER, synthetic_flag INTEGER);
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
    sats, sas_controls, receipts = [], [], []
    for i in range(1, 1501):
        po = orders[i-1]
        sat_number = f"SAT{i:08d}"
        sat_exists, sat_approved = 1, 1
        bids_required, bids_received = (3, 3) if po[6] >= 100_000 else (1, 1)
        contract_exists, approval_complete = 1, 1
        if i in {71, 471, 871}: sat_number, sat_exists, sat_approved = "", 0, 0
        if i in {95, 495, 895}: bids_required, bids_received = 3, 1
        if i in {117, 517}: approval_complete = 0
        sats.append((f"SAT{i:08d}", f"E{rng.randint(1,500):06d}", po[2], po[5], po[3],
            rng.choice(["IT", "OFİS", "DANIŞMANLIK", "BAKIM"]), po[6], "TRY", 1,
            sat_approved, 1, int(i in {233, 733}), 1))
        effective_limit = po[6] - 1 if i in {117, 517} else po[8]
        sas_controls.append((f"SC{i:08d}", po[0], sat_number, po[1], po[4], po[3], po[6], effective_limit,
            sat_exists, sat_approved, bids_required, bids_received, contract_exists, approval_complete,
            int(not sat_exists), int(bids_received < bids_required),
            int(po[6] > effective_limit and not approval_complete), 1))
    for i, invoice in enumerate(invoices, 1):
        ordered = float(rng.randint(1, 100)); received = ordered; invoiced = ordered
        accepted = 1
        if i in {211, 611, 1011}: received, invoiced = ordered * .7, ordered
        if i in {322, 722}: accepted = 0
        receipt_day = date.fromisoformat(invoice[4]) - timedelta(days=rng.randint(1, 8))
        if i in {433, 833, 1233}: receipt_day = date.fromisoformat(invoice[4]) + timedelta(days=4)
        receipts.append((f"RC{i:08d}", invoice[3], invoice[0], iso(receipt_day), invoice[4], ordered,
            received, invoiced, accepted, int(received != invoiced or not accepted),
            int(date.fromisoformat(invoice[4]) < receipt_day), 1))
    connection.executemany("INSERT INTO sat_requisitions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", sats)
    connection.executemany("INSERT INTO sas_compliance VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", sas_controls)
    connection.executemany("INSERT INTO receipt_compliance VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", receipts)
    connection.commit(); connection.close()


SOURCE_TABLES = {
    "İnsan Kaynakları": [("Kurumsal İK - Personel", "hr.db", "employees"),
                          ("Kurumsal İK - Bordro", "hr.db", "payroll"),
                          ("Kurumsal İK - Zaman Kayıtları", "hr.db", "time_entries"),
                          ("Kurumsal İK - Kart Geçişleri", "hr.db", "access_events"),
                          ("Kurumsal İK - Devam Kontrolleri", "hr.db", "attendance_compliance"),
                          ("Kurumsal İK - İzin Kontrolleri", "hr.db", "leave_compliance"),
                          ("Kurumsal İK - Terfi Uygunluğu", "hr.db", "promotion_eligibility")],
    "Finans ve Muhasebe": [("Kurumsal Finans - Yevmiye", "finance.db", "gl_journal"),
                            ("Kurumsal Finans - Ödemeler", "finance.db", "payments")],
    "Satın Alma ve Tedarik": [("Kurumsal Satın Alma - Tedarikçiler", "procurement.db", "vendors"),
                               ("Kurumsal Satın Alma - Siparişler", "procurement.db", "purchase_orders"),
                               ("Kurumsal Satın Alma - Faturalar", "procurement.db", "invoices"),
                               ("Kurumsal SAP - SAT Talepleri", "procurement.db", "sat_requisitions"),
                               ("Kurumsal SAP - SAS Kontrolleri", "procurement.db", "sas_compliance"),
                               ("Kurumsal SAP - Kabul ve Üçlü Eşleşme", "procurement.db", "receipt_compliance")],
}


RULES = [
    ("İnsan Kaynakları", "Kurumsal İK - Bordro", "Aşırı fazla mesai", "numeric", "overtime_hours", {"operator": ">", "value": 45}, "high"),
    ("İnsan Kaynakları", "Kurumsal İK - Bordro", "Dönem dışı bordro ödemesi", "numeric", "off_cycle", {"operator": ">", "value": 0}, "high"),
    ("Finans ve Muhasebe", "Kurumsal Finans - Yevmiye", "Yüksek tutarlı manuel kayıt", "numeric", "amount", {"operator": ">", "value": 1_000_000}, "critical"),
    ("Finans ve Muhasebe", "Kurumsal Finans - Ödemeler", "Görevler ayrılığı ihlali", "numeric", "same_user_created_approved", {"operator": ">", "value": 0}, "critical"),
    ("Satın Alma ve Tedarik", "Kurumsal Satın Alma - Faturalar", "Mükerrer fatura numarası", "duplicate", "invoice_number", {"fields": ["invoice_number"]}, "critical"),
    ("Satın Alma ve Tedarik", "Kurumsal Satın Alma - Faturalar", "Yüksek fatura fiyat farkı", "numeric", "price_variance", {"operator": ">", "value": .10}, "high"),
    ("İnsan Kaynakları", "Kurumsal İK - Devam Kontrolleri", "Çekirdek saatte izinsiz dışarıda", "numeric", "unreported_core_absence", {"operator": ">", "value": 0}, "high"),
    ("İnsan Kaynakları", "Kurumsal İK - Devam Kontrolleri", "Onaysız mesai dışı ofis kullanımı", "numeric", "unapproved_after_hours", {"operator": ">", "value": 0}, "high"),
    ("İnsan Kaynakları", "Kurumsal İK - İzin Kontrolleri", "Belgesiz eksi yıllık izin", "numeric", "undocumented_negative_leave", {"operator": ">", "value": 0}, "high"),
    ("İnsan Kaynakları", "Kurumsal İK - Terfi Uygunluğu", "Gecikmiş terfi adayı", "numeric", "promotion_overdue", {"operator": ">", "value": 0}, "medium"),
    ("Satın Alma ve Tedarik", "Kurumsal SAP - SAS Kontrolleri", "SAT olmadan SAS oluşturma", "numeric", "sas_without_sat", {"operator": ">", "value": 0}, "critical"),
    ("Satın Alma ve Tedarik", "Kurumsal SAP - SAS Kontrolleri", "Yetersiz teklif rekabeti", "numeric", "insufficient_competition", {"operator": ">", "value": 0}, "high"),
    ("Satın Alma ve Tedarik", "Kurumsal SAP - SAS Kontrolleri", "Onay limiti ihlal edilen SAS", "numeric", "approval_limit_breach", {"operator": ">", "value": 0}, "critical"),
    ("Satın Alma ve Tedarik", "Kurumsal SAP - Kabul ve Üçlü Eşleşme", "Üçlü eşleşme istisnası", "numeric", "three_way_match_exception", {"operator": ">", "value": 0}, "high"),
    ("Satın Alma ve Tedarik", "Kurumsal SAP - Kabul ve Üçlü Eşleşme", "Kabulden önce fatura kaydı", "numeric", "invoice_before_receipt", {"operator": ">", "value": 0}, "high"),
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


def reset_generated_evidence() -> None:
    """Keep reruns deterministic by clearing only evidence owned by this synthetic package."""
    rules = AuditRule.query.filter_by(description="Sentetik kurumsal denetim senaryosu").all()
    for rule in rules:
        for collection in (list(rule.alarms), list(rule.executions), list(rule.risk_scores)):
            for item in collection:
                db.session.delete(item)
        rule.trigger_count = 0
        rule.last_run_at = None
    db.session.flush()


def main() -> None:
    rng = random.Random(SEED)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for filename, creator in (("hr.db", create_hr), ("finance.db", create_finance),
                              ("procurement.db", create_procurement)):
        path = OUTPUT / filename
        if path.exists(): path.unlink()
        creator(path, rng)
    with app.app_context():
        source_map = register_sources(); reset_generated_evidence(); register_controls(source_map); db.session.commit()
        print(f"Generated 3 databases and registered {len(source_map)} AuditAI sources.")
        for name, source in source_map.items():
            print(f"- {name}: {len(source.config['records'])} records")


if __name__ == "__main__":
    main()
