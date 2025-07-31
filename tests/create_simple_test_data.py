#!/usr/bin/env python3
"""
Simple Test Data Generator for AuditAi
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import *

def create_basic_test_data():
    """Create basic test data for all business areas"""
    
    with app.app_context():
        print("🔄 Creating basic test data...")
        
        # Get admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ Admin user not found")
            return
        
        # 1. Create Finance Area
        finance_area = AuditArea(
            name="Finans ve Muhasebe",
            description="Finansal işlemler, yevmiye kayıtları ve anomali tespiti",
            owner_id=admin_user.id
        )
        db.session.add(finance_area)
        db.session.flush()
        
        # 2. Create HR Area
        hr_area = AuditArea(
            name="İnsan Kaynakları",
            description="Bordro, personel hareketleri ve performans analizi",
            owner_id=admin_user.id
        )
        db.session.add(hr_area)
        db.session.flush()
        
        # 3. Create Procurement Area
        procurement_area = AuditArea(
            name="Satın Alma ve Tedarik",
            description="Tedarikçi değerlendirme ve sipariş süreçleri",
            owner_id=admin_user.id
        )
        db.session.add(procurement_area)
        db.session.flush()
        
        # 4. Create Operations Area
        operations_area = AuditArea(
            name="Operasyon ve Üretim",
            description="Üretim verileri ve kalite kontrol",
            owner_id=admin_user.id
        )
        db.session.add(operations_area)
        db.session.flush()
        
        # 5. Create IT Security Area
        it_area = AuditArea(
            name="Bilgi Teknolojileri",
            description="Sistem güvenliği ve erişim kontrolü",
            owner_id=admin_user.id
        )
        db.session.add(it_area)
        db.session.flush()
        
        # 6. Create Sales Area
        sales_area = AuditArea(
            name="Satış ve Pazarlama",
            description="Satış performansı ve müşteri analizi",
            owner_id=admin_user.id
        )
        db.session.add(sales_area)
        db.session.flush()
        
        print(f"✅ Created 6 audit areas")
        
        # Create AI/ML Rules
        rules_data = [
            {
                'area': finance_area,
                'name': 'Finansal Anomali Tespiti',
                'description': 'Yüksek tutarlı işlemleri Isolation Forest ile tespit eder',
                'condition': 'amount > threshold AND algorithm = isolation_forest',
                'rule_type': 'anomaly_detection',
                'algorithm': 'isolation_forest',
                'sensitivity': 0.2,
                'confidence_threshold': 0.85
            },
            {
                'area': finance_area,
                'name': 'Dolandırıcılık Tespiti',
                'description': 'Şüpheli finansal pattern\'leri Random Forest ile analiz eder',
                'condition': 'pattern_detected = true AND confidence > 0.8',
                'rule_type': 'fraud_detection',
                'algorithm': 'random_forest',
                'sensitivity': 0.25,
                'confidence_threshold': 0.80
            },
            {
                'area': hr_area,
                'name': 'Bordro Anomali Kontrolü',
                'description': 'Maaş ödemelerindeki anormal durumları tespit eder',
                'condition': 'salary_deviation > 2*std_dev',
                'rule_type': 'anomaly_detection',
                'algorithm': 'isolation_forest',
                'sensitivity': 0.18,
                'confidence_threshold': 0.88
            },
            {
                'area': procurement_area,
                'name': 'Tedarikçi Risk Analizi',
                'description': 'Şüpheli tedarikçi aktivitelerini tespit eder',
                'condition': 'vendor_risk_score > 0.7',
                'rule_type': 'fraud_detection',
                'algorithm': 'random_forest',
                'sensitivity': 0.22,
                'confidence_threshold': 0.82
            },
            {
                'area': operations_area,
                'name': 'Üretim Kalite Kontrolü',
                'description': 'Kalite metriklerindeki anormal değişimleri tespit eder',
                'condition': 'defect_rate > normal_range',
                'rule_type': 'anomaly_detection',
                'algorithm': 'autoencoder',
                'sensitivity': 0.28,
                'confidence_threshold': 0.85
            },
            {
                'area': it_area,
                'name': 'Güvenlik Tehdidi Tespiti',
                'description': 'Anormal sistem erişimlerini ve güvenlik tehditlerini tespit eder',
                'condition': 'suspicious_activity = true',
                'rule_type': 'security',
                'algorithm': 'isolation_forest',
                'sensitivity': 0.12,
                'confidence_threshold': 0.95
            },
            {
                'area': sales_area,
                'name': 'Satış Trend Analizi',
                'description': 'Satış verilerindeki anormal trend\'leri Prophet ile tespit eder',
                'condition': 'trend_deviation > threshold',
                'rule_type': 'time_series',
                'algorithm': 'prophet',
                'sensitivity': 0.30,
                'confidence_threshold': 0.75
            }
        ]
        
        created_rules = []
        for rule_data in rules_data:
            area = rule_data.pop('area')
            rule = AuditRule(
                audit_area_id=area.id,
                risk_category=random.choice(['medium', 'high']),
                **rule_data
            )
            db.session.add(rule)
            created_rules.append(rule)
        
        db.session.flush()
        print(f"✅ Created {len(created_rules)} AI/ML rules")
        
        # Create Data Sources
        sources_data = [
            {'area': finance_area, 'name': 'SAP Finans Modülü', 'source_type': 'database', 'connection_string': 'sap://finance.company.com'},
            {'area': finance_area, 'name': 'Banka API', 'source_type': 'api', 'connection_string': 'https://api.bank.com/v1'},
            {'area': hr_area, 'name': 'İK Veritabanı', 'source_type': 'database', 'connection_string': 'postgresql://hr.internal'},
            {'area': procurement_area, 'name': 'Satın Alma Sistemi', 'source_type': 'database', 'connection_string': 'mysql://procurement.db'},
            {'area': operations_area, 'name': 'Üretim Veritabanı', 'source_type': 'database', 'connection_string': 'postgresql://production.db'},
            {'area': it_area, 'name': 'Güvenlik Log Sistemi', 'source_type': 'file', 'connection_string': '/var/log/security.log'},
            {'area': sales_area, 'name': 'CRM Sistemi', 'source_type': 'api', 'connection_string': 'https://crm.company.com/api/v2'}
        ]
        
        for source_data in sources_data:
            area = source_data.pop('area')
            source = DataSource(
                audit_area_id=area.id,
                is_active=True,
                sync_status='success',
                last_sync=datetime.now() - timedelta(hours=random.randint(1, 24)),
                **source_data
            )
            db.session.add(source)
        
        print(f"✅ Created {len(sources_data)} data sources")
        
        # Create Sample Alarms
        for i, rule in enumerate(created_rules):
            # Create 2-3 alarms per rule
            for j in range(random.randint(2, 4)):
                alarm = Alarm(
                    rule_id=rule.id,
                    audit_area_id=rule.audit_area_id,
                    title=f"{rule.name} Tetiklendi",
                    message=f"Kural '{rule.name}' anomali tespit etti. Detaylı inceleme gerekli.",
                    severity=random.choice(['low', 'medium', 'high', 'critical']),
                    status=random.choice(['active', 'acknowledged', 'resolved']),
                    created_at=datetime.now() - timedelta(hours=random.randint(1, 720))
                )
                db.session.add(alarm)
        
        print(f"✅ Created sample alarms")
        
        # Commit all changes
        db.session.commit()
        print("✅ All test data committed successfully!")
        
        # Verify data
        areas_count = AuditArea.query.count()
        rules_count = AuditRule.query.count()
        sources_count = DataSource.query.count()
        alarms_count = Alarm.query.count()
        
        print(f"\n📊 Test Data Summary:")
        print(f"• Audit Areas: {areas_count}")
        print(f"• Rules: {rules_count}")
        print(f"• Data Sources: {sources_count}")
        print(f"• Alarms: {alarms_count}")

if __name__ == "__main__":
    try:
        create_basic_test_data()
        print("\n🎉 Test data creation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error creating test data: {str(e)}")
        import traceback
        traceback.print_exc()