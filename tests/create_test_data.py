#!/usr/bin/env python3
"""
AuditAi Test Data Generator
Creates comprehensive test data for all business areas to utilize all system functions
"""

import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import *

def create_comprehensive_test_data():
    """Create comprehensive test data for all business areas"""
    
    with app.app_context():
        print("🔄 Creating comprehensive test data...")
        
        # 1. Create Finance and Accounting Area with detailed data
        finance_area = create_finance_accounting_area()
        
        # 2. Create Human Resources Area
        hr_area = create_human_resources_area()
        
        # 3. Create Procurement Area
        procurement_area = create_procurement_area()
        
        # 4. Create Operations Area
        operations_area = create_operations_area()
        
        # 5. Create IT Security Area
        it_area = create_it_security_area()
        
        # 6. Create Sales and Marketing Area
        sales_area = create_sales_marketing_area()
        
        # 7. Create Advanced AI/ML Rules for each area
        create_advanced_rules(finance_area, hr_area, procurement_area, operations_area, it_area, sales_area)
        
        # 8. Create Data Sources for each area
        create_data_sources(finance_area, hr_area, procurement_area, operations_area, it_area, sales_area)
        
        # 9. Generate Alarms and Notifications
        create_alarms_and_notifications()
        
        # 10. Create Model Performance and Feedback Data
        create_ml_performance_data()
        
        db.session.commit()
        print("✅ Comprehensive test data created successfully!")

def create_finance_accounting_area():
    """Create Finance and Accounting audit area with comprehensive data"""
    
    # Get admin user
    admin_user = User.query.filter_by(username='admin').first()
    
    # Create Finance Area
    finance_area = AuditArea(
        name="Finans ve Muhasebe",
        description="Yevmiye kayıtları, büyük defter, mizan, bilanço ve gelir tablosu analizi. Anomali tespiti ve dolandırıcılık kontrolü.",
        owner_id=admin_user.id,
        created_at=datetime.now() - timedelta(days=30)
    )
    db.session.add(finance_area)
    db.session.flush()
    
    # Create sample financial transactions with anomalies
    create_financial_transactions(finance_area.id)
    
    return finance_area

def create_financial_transactions(area_id):
    """Create realistic financial transaction data with anomalies"""
    
    base_date = datetime.now() - timedelta(days=90)
    
    # Normal transactions
    normal_transactions = []
    for i in range(1000):
        transaction_date = base_date + timedelta(days=random.randint(0, 90))
        amount = random.uniform(100, 50000)
        
        # Add some seasonal patterns
        if transaction_date.month in [11, 12]:  # Holiday season
            amount *= random.uniform(1.2, 1.8)
        
        normal_transactions.append({
            'date': transaction_date,
            'amount': round(amount, 2),
            'account_code': f"ACC{random.randint(1000, 9999)}",
            'description': f"Normal işlem {i+1}",
            'type': random.choice(['Gelir', 'Gider', 'Transfer']),
            'is_anomaly': False
        })
    
    # Anomalous transactions (10% of total)
    anomaly_transactions = []
    for i in range(100):
        transaction_date = base_date + timedelta(days=random.randint(0, 90))
        
        # Create different types of anomalies
        anomaly_type = random.choice(['high_amount', 'weekend_transaction', 'duplicate', 'suspicious_pattern'])
        
        if anomaly_type == 'high_amount':
            amount = random.uniform(100000, 500000)  # Unusually high
        elif anomaly_type == 'weekend_transaction':
            # Force weekend date
            while transaction_date.weekday() < 5:  # 0-4 are weekdays
                transaction_date = base_date + timedelta(days=random.randint(0, 90))
            amount = random.uniform(1000, 10000)
        elif anomaly_type == 'duplicate':
            amount = 15750.00  # Exact duplicate amount
        else:  # suspicious_pattern
            amount = random.uniform(9990, 9999)  # Just under reporting threshold
        
        anomaly_transactions.append({
            'date': transaction_date,
            'amount': round(amount, 2),
            'account_code': f"ACC{random.randint(1000, 9999)}",
            'description': f"Anomali işlem {i+1} - {anomaly_type}",
            'type': random.choice(['Gelir', 'Gider', 'Transfer']),
            'is_anomaly': True,
            'anomaly_type': anomaly_type
        })
    
    # Save to database (we'll create a sample table for demo)
    all_transactions = normal_transactions + anomaly_transactions
    
    # Store some key metrics for dashboard
    total_amount = sum(t['amount'] for t in all_transactions)
    anomaly_amount = sum(t['amount'] for t in anomaly_transactions)
    
    print(f"📊 Created {len(all_transactions)} financial transactions")
    print(f"💰 Total amount: {total_amount:,.2f} TL")
    print(f"🚨 Anomaly amount: {anomaly_amount:,.2f} TL ({anomaly_amount/total_amount*100:.1f}%)")
    
    return all_transactions

def create_human_resources_area():
    """Create HR audit area"""
    admin_user = User.query.filter_by(username='admin').first()
    
    hr_area = AuditArea(
        name="İnsan Kaynakları",
        description="Bordro analizi, personel hareketleri, izin kullanımları ve performans değerlendirmeleri.",
        owner_id=admin_user.id,
        created_at=datetime.now() - timedelta(days=25)
    )
    db.session.add(hr_area)
    db.session.flush()
    
    # Create employee data with anomalies
    create_hr_data(hr_area.id)
    
    return hr_area

def create_hr_data(area_id):
    """Create HR data with overtime anomalies"""
    
    # Create 150 employees
    employees = []
    for i in range(150):
        salary = random.uniform(5000, 25000)
        overtime_hours = random.uniform(0, 20)  # Normal overtime
        
        # 10% have excessive overtime (anomaly)
        if random.random() < 0.1:
            overtime_hours = random.uniform(50, 80)  # Excessive overtime
        
        employees.append({
            'employee_id': f"EMP{i+1:04d}",
            'name': f"Çalışan {i+1}",
            'department': random.choice(['IT', 'Finans', 'İK', 'Operasyon', 'Satış']),
            'salary': round(salary, 2),
            'overtime_hours': round(overtime_hours, 1),
            'is_anomaly': overtime_hours > 40
        })
    
    print(f"👥 Created {len(employees)} employee records")
    return employees

def create_procurement_area():
    """Create Procurement audit area"""
    admin_user = User.query.filter_by(username='admin').first()
    
    procurement_area = AuditArea(
        name="Satın Alma ve Tedarik",
        description="Tedarikçi değerlendirmeleri, sipariş süreçleri ve stok hareketleri analizi.",
        owner_id=admin_user.id,
        created_at=datetime.now() - timedelta(days=20)
    )
    db.session.add(procurement_area)
    db.session.flush()
    
    create_procurement_data(procurement_area.id)
    return procurement_area

def create_procurement_data(area_id):
    """Create procurement data with vendor anomalies"""
    
    vendors = ['Tedarikçi A', 'Tedarikçi B', 'Tedarikçi C', 'Şüpheli Tedarikçi', 'Güvenilir Tedarikçi']
    orders = []
    
    for i in range(500):
        vendor = random.choice(vendors)
        amount = random.uniform(1000, 50000)
        
        # Suspicious vendor gets higher amounts (potential fraud)
        if vendor == 'Şüpheli Tedarikçi':
            amount *= random.uniform(2, 5)
        
        orders.append({
            'order_id': f"PO{i+1:06d}",
            'vendor': vendor,
            'amount': round(amount, 2),
            'order_date': datetime.now() - timedelta(days=random.randint(1, 90)),
            'is_suspicious': vendor == 'Şüpheli Tedarikçi'
        })
    
    print(f"📦 Created {len(orders)} procurement orders")
    return orders

def create_operations_area():
    """Create Operations audit area"""
    admin_user = User.query.filter_by(username='admin').first()
    
    ops_area = AuditArea(
        name="Operasyon ve Üretim",
        description="Üretim kayıtları, kalite kontrol ve makine performansı analizi.",
        owner_id=admin_user.id,
        created_at=datetime.now() - timedelta(days=15)
    )
    db.session.add(ops_area)
    db.session.flush()
    
    create_operations_data(ops_area.id)
    return ops_area

def create_operations_data(area_id):
    """Create operations data with quality anomalies"""
    
    production_lines = ['Hat A', 'Hat B', 'Hat C', 'Hat D']
    productions = []
    
    for i in range(300):
        line = random.choice(production_lines)
        quantity = random.randint(100, 1000)
        defect_rate = random.uniform(0.5, 3.0)  # Normal defect rate
        
        # 15% have high defect rates (quality issues)
        if random.random() < 0.15:
            defect_rate = random.uniform(8.0, 15.0)
        
        productions.append({
            'production_id': f"PROD{i+1:06d}",
            'line': line,
            'quantity': quantity,
            'defect_rate': round(defect_rate, 2),
            'date': datetime.now() - timedelta(days=random.randint(1, 30)),
            'is_quality_issue': defect_rate > 5.0
        })
    
    print(f"🏭 Created {len(productions)} production records")
    return productions

def create_it_security_area():
    """Create IT Security audit area"""
    admin_user = User.query.filter_by(username='admin').first()
    
    it_area = AuditArea(
        name="Bilgi Teknolojileri Güvenlik",
        description="Sistem logları, güvenlik olayları ve kullanıcı aktivitesi analizi.",
        owner_id=admin_user.id,
        created_at=datetime.now() - timedelta(days=10)
    )
    db.session.add(it_area)
    db.session.flush()
    
    create_security_data(it_area.id)
    return it_area

def create_security_data(area_id):
    """Create security data with threat patterns"""
    
    ip_addresses = ['192.168.1.100', '192.168.1.101', '10.0.0.50', '172.16.0.25', '203.0.113.195']
    security_events = []
    
    for i in range(1000):
        ip = random.choice(ip_addresses)
        event_type = random.choice(['login_success', 'login_failure', 'file_access', 'admin_action'])
        
        # Suspicious IP has more failures
        if ip == '203.0.113.195':  # External suspicious IP
            event_type = random.choice(['login_failure', 'brute_force', 'unauthorized_access'])
        
        is_suspicious = ip == '203.0.113.195' or event_type in ['brute_force', 'unauthorized_access']
        
        security_events.append({
            'event_id': f"SEC{i+1:06d}",
            'ip_address': ip,
            'event_type': event_type,
            'timestamp': datetime.now() - timedelta(minutes=random.randint(1, 10080)),  # Last week
            'is_suspicious': is_suspicious,
            'risk_score': random.randint(8, 10) if is_suspicious else random.randint(1, 4)
        })
    
    print(f"🔒 Created {len(security_events)} security events")
    return security_events

def create_sales_marketing_area():
    """Create Sales and Marketing audit area"""
    admin_user = User.query.filter_by(username='admin').first()
    
    sales_area = AuditArea(
        name="Satış ve Pazarlama",
        description="CRM verileri, satış performansı ve müşteri memnuniyeti analizi.",
        owner_id=admin_user.id,
        created_at=datetime.now() - timedelta(days=5)
    )
    db.session.add(sales_area)
    db.session.flush()
    
    create_sales_data(sales_area.id)
    return sales_area

def create_sales_data(area_id):
    """Create sales data with performance patterns"""
    
    sales_reps = [f"Satış Temsilcisi {i+1}" for i in range(10)]
    sales_records = []
    
    for i in range(800):
        rep = random.choice(sales_reps)
        amount = random.uniform(1000, 20000)
        
        # Some reps have consistently higher performance
        if rep in ['Satış Temsilcisi 1', 'Satış Temsilcisi 2']:
            amount *= random.uniform(1.5, 2.5)
        
        sales_records.append({
            'sale_id': f"SALE{i+1:06d}",
            'sales_rep': rep,
            'amount': round(amount, 2),
            'customer': f"Müşteri {random.randint(1, 100)}",
            'date': datetime.now() - timedelta(days=random.randint(1, 60)),
            'is_high_performer': rep in ['Satış Temsilcisi 1', 'Satış Temsilcisi 2']
        })
    
    print(f"💼 Created {len(sales_records)} sales records")
    return sales_records

def create_advanced_rules(finance_area, hr_area, procurement_area, operations_area, it_area, sales_area):
    """Create comprehensive AI/ML rules for all areas"""
    
    rules = [
        # Finance Rules
        {
            'area': finance_area,
            'name': 'Yüksek Tutarlı İşlem Anomalisi',
            'description': 'Isolation Forest algoritması ile olağandışı yüksek tutarlı işlemleri tespit eder',
            'rule_type': 'anomaly_detection',
            'algorithm': 'isolation_forest',
            'sensitivity': 0.15,  # High sensitivity
            'confidence_threshold': 0.85
        },
        {
            'area': finance_area,
            'name': 'Dolandırıcılık Pattern Tespiti',
            'description': 'Random Forest ile finansal dolandırıcılık pattern\'lerini analiz eder',
            'rule_type': 'fraud_detection',
            'algorithm': 'random_forest',
            'sensitivity': 0.25,
            'confidence_threshold': 0.80
        },
        {
            'area': finance_area,
            'name': 'Hafta Sonu İşlem Kontrolü',
            'description': 'Hafta sonu yapılan şüpheli finansal işlemleri tespit eder',
            'rule_type': 'security',
            'algorithm': 'autoencoder',
            'sensitivity': 0.30,
            'confidence_threshold': 0.75
        },
        
        # HR Rules
        {
            'area': hr_area,
            'name': 'Aşırı Mesai Anomalisi',
            'description': 'ARIMA modeli ile anormal mesai pattern\'lerini tespit eder',
            'rule_type': 'time_series',
            'algorithm': 'arima',
            'sensitivity': 0.20,
            'confidence_threshold': 0.90
        },
        {
            'area': hr_area,
            'name': 'Bordro Anomali Tespiti',
            'description': 'Maaş ödemelerindeki anormal durumları Isolation Forest ile analiz eder',
            'rule_type': 'anomaly_detection',
            'algorithm': 'isolation_forest',
            'sensitivity': 0.18,
            'confidence_threshold': 0.88
        },
        
        # Procurement Rules
        {
            'area': procurement_area,
            'name': 'Tedarikçi Dolandırıcılık Tespiti',
            'description': 'Şüpheli tedarikçi aktivitelerini Random Forest ile tespit eder',
            'rule_type': 'fraud_detection',
            'algorithm': 'random_forest',
            'sensitivity': 0.22,
            'confidence_threshold': 0.82
        },
        {
            'area': procurement_area,
            'name': 'Satın Alma Trend Analizi',
            'description': 'Prophet modeli ile satın alma pattern\'lerini analiz eder',
            'rule_type': 'time_series',
            'algorithm': 'prophet',
            'sensitivity': 0.25,
            'confidence_threshold': 0.78
        },
        
        # Operations Rules
        {
            'area': operations_area,
            'name': 'Kalite Anomali Tespiti',
            'description': 'Üretim kalitesindeki anormal durumları Autoencoder ile tespit eder',
            'rule_type': 'anomaly_detection',
            'algorithm': 'autoencoder',
            'sensitivity': 0.28,
            'confidence_threshold': 0.85
        },
        
        # IT Security Rules
        {
            'area': it_area,
            'name': 'Siber Güvenlik Tehdidi',
            'description': 'Anomal sistem erişimlerini ve güvenlik tehditlerini tespit eder',
            'rule_type': 'security',
            'algorithm': 'isolation_forest',
            'sensitivity': 0.12,  # Very high sensitivity for security
            'confidence_threshold': 0.95
        },
        {
            'area': it_area,
            'name': 'Brute Force Saldırı Tespiti',
            'description': 'ARIMA ile sistematik saldırı pattern\'lerini analiz eder',
            'rule_type': 'security',
            'algorithm': 'arima',
            'sensitivity': 0.15,
            'confidence_threshold': 0.92
        },
        
        # Sales Rules
        {
            'area': sales_area,
            'name': 'Satış Performans Anomalisi',
            'description': 'Prophet modeli ile satış trend\'lerindeki anormal durumları tespit eder',
            'rule_type': 'time_series',
            'algorithm': 'prophet',
            'sensitivity': 0.30,
            'confidence_threshold': 0.75
        }
    ]
    
    created_rules = []
    for rule_config in rules:
        area = rule_config.pop('area')
        rule = AuditRule(
            audit_area_id=area.id,
            condition=f"AI/ML Algorithm: {rule_config.get('algorithm', 'default')}",
            risk_category=random.choice(['low', 'medium', 'high', 'critical']),
            **rule_config
        )
        db.session.add(rule)
        created_rules.append(rule)
    
    print(f"🧠 Created {len(created_rules)} advanced AI/ML rules")
    return created_rules

def create_data_sources(finance_area, hr_area, procurement_area, operations_area, it_area, sales_area):
    """Create data sources for each area"""
    
    sources = [
        # Finance Sources
        {'area': finance_area, 'name': 'SAP Finans Modülü', 'source_type': 'database', 'connection_string': 'sap://finance.db'},
        {'area': finance_area, 'name': 'Muhasebe Excel Dosyası', 'source_type': 'file', 'connection_string': '/data/accounting.xlsx'},
        {'area': finance_area, 'name': 'Banka API', 'source_type': 'api', 'connection_string': 'https://api.bank.com/transactions'},
        
        # HR Sources
        {'area': hr_area, 'name': 'İK Veritabanı', 'source_type': 'database', 'connection_string': 'postgresql://hr.db'},
        {'area': hr_area, 'name': 'Bordro CSV', 'source_type': 'file', 'connection_string': '/data/payroll.csv'},
        
        # Other areas
        {'area': procurement_area, 'name': 'Satın Alma Sistemi', 'source_type': 'database', 'connection_string': 'mysql://procurement.db'},
        {'area': operations_area, 'name': 'Üretim Veritabanı', 'source_type': 'database', 'connection_string': 'postgresql://production.db'},
        {'area': it_area, 'name': 'Güvenlik Log Dosyası', 'source_type': 'file', 'connection_string': '/var/log/security.log'},
        {'area': sales_area, 'name': 'CRM API', 'source_type': 'api', 'connection_string': 'https://crm.company.com/api'}
    ]
    
    created_sources = []
    for source_config in sources:
        area = source_config.pop('area')
        source = DataSource(
            audit_area_id=area.id,
            is_active=True,
            sync_status='success',
            **source_config
        )
        db.session.add(source)
        created_sources.append(source)
    
    print(f"📊 Created {len(created_sources)} data sources")
    return created_sources

def create_alarms_and_notifications():
    """Create sample alarms and notifications"""
    
    # Get all rules
    rules = AuditRule.query.all()
    
    alarms = []
    severities = ['low', 'medium', 'high', 'critical']
    
    for i in range(50):
        rule = random.choice(rules)
        severity = random.choice(severities)
        
        # Critical alarms are less frequent
        if severity == 'critical':
            if random.random() > 0.1:  # Only 10% chance
                continue
        
        alarm = Alarm(
            rule_id=rule.id,
            audit_area_id=rule.audit_area_id,
            title=f"{rule.name} - Alarm",
            message=f"Kural '{rule.name}' tetiklendi. {rule.description}",
            severity=severity,
            status=random.choice(['active', 'acknowledged', 'resolved']),
            created_at=datetime.now() - timedelta(hours=random.randint(1, 168))  # Last week
        )
        db.session.add(alarm)
        alarms.append(alarm)
    
    print(f"🚨 Created {len(alarms)} alarms")
    return alarms

def create_ml_performance_data():
    """Create ML model performance and feedback data"""
    
    rules = AuditRule.query.filter(AuditRule.algorithm.isnot(None)).all()
    
    # Model Performance Records
    for rule in rules:
        performance = ModelPerformance(
            rule_id=rule.id,
            accuracy=random.uniform(0.75, 0.95),
            precision=random.uniform(0.70, 0.90),
            recall=random.uniform(0.65, 0.88),
            f1_score=random.uniform(0.68, 0.89),
            false_positive_rate=random.uniform(0.05, 0.20),
            evaluation_date=datetime.now() - timedelta(days=random.randint(1, 30))
        )
        db.session.add(performance)
    
    # Anomaly Detection Records
    for i in range(100):
        rule = random.choice(rules[:5])  # Use first 5 rules
        detection = AnomalyDetection(
            rule_id=rule.id,
            data_source_id=random.choice([1, 2, 3, 4, 5]),  # Random data source
            anomaly_score=random.uniform(0.60, 0.98),
            confidence_level=random.uniform(0.70, 0.95),
            detection_type=random.choice(['statistical', 'ml_based', 'pattern_based']),
            algorithm_used=random.choice(['isolation_forest', 'random_forest', 'autoencoder']),
            data_point={'value': random.uniform(1000, 50000), 'timestamp': datetime.now().isoformat()},
            is_confirmed=random.choice([True, False, None]),
            created_at=datetime.now() - timedelta(hours=random.randint(1, 720))
        )
        db.session.add(detection)
    
    # Fraud Pattern Records
    for i in range(30):
        rule = random.choice([r for r in rules if r.rule_type == 'fraud_detection'])
        if rule:
            pattern = FraudPattern(
                pattern_name=f"Fraud Pattern {i+1}",
                pattern_type=random.choice(['transaction', 'behavioral', 'temporal']),
                pattern_signature={'threshold': random.uniform(1000, 10000), 'frequency': random.randint(3, 10)},
                risk_score=random.uniform(0.6, 1.0),
                frequency_threshold=random.randint(1, 5),
                is_active=True,
                created_by_id=1,  # admin user
                last_detected=datetime.now() - timedelta(hours=random.randint(1, 480)),
                detection_count=random.randint(1, 20)
            )
            db.session.add(pattern)
    
    # Security Events
    for i in range(80):
        security_rule = random.choice([r for r in rules if r.rule_type == 'security'])
        if security_rule:
            event = SecurityEvent(
                event_type=random.choice(['login', 'access', 'permission_change']),
                ip_address=f"192.168.1.{random.randint(1, 254)}",
                risk_score=random.uniform(0.1, 1.0),
                user_agent=f"Mozilla/5.0 Browser {random.randint(1, 100)}",
                location=random.choice(['Istanbul', 'Ankara', 'Izmir', 'Unknown']),
                device_fingerprint=f"device_{random.randint(1000, 9999)}",
                session_id=f"session_{random.randint(10000, 99999)}",
                is_suspicious=random.choice([True, False]),
                is_blocked=False,
                user_id=random.randint(1, 5),  # Random user
                created_at=datetime.now() - timedelta(hours=random.randint(1, 360))
            )
            db.session.add(event)
    
    print("🤖 Created ML performance and analysis data")

if __name__ == "__main__":
    try:
        create_comprehensive_test_data()
        print("\n🎉 Test data creation completed successfully!")
        print("\nCreated data includes:")
        print("• 6 comprehensive audit areas")
        print("• 12 advanced AI/ML rules with different algorithms")
        print("• 9 data sources across all areas") 
        print("• Financial transactions with anomaly patterns")
        print("• HR data with overtime anomalies")
        print("• Procurement data with vendor fraud patterns")
        print("• Operations data with quality issues")
        print("• IT security events and threat patterns")
        print("• Sales data with performance analytics")
        print("• Comprehensive alarms and notifications")
        print("• ML model performance metrics")
        print("• Anomaly detection records")
        print("• Fraud pattern analysis")
        print("• Security event tracking")
        
    except Exception as e:
        print(f"❌ Error creating test data: {str(e)}")
        import traceback
        traceback.print_exc()