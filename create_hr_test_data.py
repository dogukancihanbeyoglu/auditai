#!/usr/bin/env python3
"""
İnsan Kaynakları (HR) test verisi oluşturma scripti
Bu script HR süreçleri için gerçekçi test verileri oluşturur
"""

import os
import sys
sys.path.append('.')

from app import app, db
from models import AuditArea, AuditRule, DataSource, Alarm
from flask_login import current_user
from datetime import datetime, timedelta
import random

# Demo kullanıcı ID'si (genelde 1)
DEMO_USER_ID = 1

def create_hr_audit_area():
    """İnsan Kaynakları audit alanı oluştur"""
    hr_area = AuditArea(
        name="İnsan Kaynakları",
        description="Personel yönetimi, bordro, izin ve performans süreçlerinin denetimi",
        owner_id=DEMO_USER_ID,
        is_active=True,
        created_at=datetime.now()
    )
    db.session.add(hr_area)
    db.session.commit()
    return hr_area

def create_hr_data_sources(audit_area_id):
    """HR veri kaynaklarını oluştur"""
    data_sources = [
        {
            'name': 'HRMS Veritabanı',
            'source_type': 'database',
            'connection_string': 'postgresql://hr_user:hr_pass@hr-db.company.com:5432/hrms',
            'table_name': 'employees',
            'description': 'Ana personel yönetim sistemi veritabanı'
        },
        {
            'name': 'Bordro Sistemi',
            'source_type': 'database',
            'connection_string': 'postgresql://payroll_user:payroll_pass@payroll-db.company.com:5432/payroll',
            'table_name': 'salary_payments',
            'description': 'Maaş ödemeleri ve bordro hesaplamaları'
        },
        {
            'name': 'İzin Takip Sistemi',
            'source_type': 'api',
            'connection_string': 'https://api.leave-management.company.com/v1',
            'table_name': 'leave_requests',
            'description': 'Personel izin talepleri ve onayları'
        },
        {
            'name': 'Performans Değerlendirme',
            'source_type': 'file',
            'connection_string': '/data/performance/monthly_reviews.xlsx',
            'table_name': 'performance_reviews',
            'description': 'Aylık performans değerlendirme raporları'
        },
        {
            'name': 'Eğitim Kayıtları',
            'source_type': 'database',
            'connection_string': 'postgresql://training_user:training_pass@training-db.company.com:5432/lms',
            'table_name': 'training_records',
            'description': 'Personel eğitim katılım ve tamamlama kayıtları'
        }
    ]
    
    created_sources = []
    for source_data in data_sources:
        data_source = DataSource(
            name=source_data['name'],
            source_type=source_data['source_type'],
            connection_string=source_data['connection_string'],
            audit_area_id=audit_area_id,
            is_active=True,
            last_sync=datetime.now() - timedelta(hours=random.randint(1, 24))
        )
        db.session.add(data_source)
        created_sources.append(data_source)
    
    db.session.commit()
    return created_sources

def create_hr_audit_rules(audit_area_id, data_sources):
    """HR audit kuralları oluştur"""
    
    rules_data = [
        {
            'name': 'Aşırı Mesai Anomali Tespiti',
            'description': 'Günlük 12 saatten fazla çalışan personeli tespit eder',
            'rule_type': 'anomaly_detection',
            'algorithm': 'isolation_forest',
            'condition': 'daily_hours > 12',
            'threshold_value': 12.0,
            'confidence_threshold': 0.85,
            'sensitivity': 0.7,
            'risk_category': 'medium',
            'data_source': 'HRMS Veritabanı'
        },
        {
            'name': 'Maaş Ödemesi Düzensizliği',
            'description': 'Normal maaş ödeme döngüsü dışındaki ödemeleri kontrol eder',
            'rule_type': 'fraud_detection',
            'algorithm': 'random_forest',
            'condition': 'payment_date NOT IN regular_payroll_dates',
            'threshold_value': None,
            'confidence_threshold': 0.9,
            'sensitivity': 0.8,
            'risk_category': 'high',
            'data_source': 'Bordro Sistemi'
        },
        {
            'name': 'İzin Bakiyesi Kontrolü',
            'description': 'Negatif izin bakiyesi olan personeli tespit eder',
            'rule_type': 'compliance',
            'algorithm': 'threshold',
            'condition': 'leave_balance < 0',
            'threshold_value': 0.0,
            'confidence_threshold': 1.0,
            'sensitivity': 1.0,
            'risk_category': 'medium',
            'data_source': 'İzin Takip Sistemi'
        },
        {
            'name': 'Performans Düşüklüğü Tespiti',
            'description': 'Üst üste düşük performans gösteren personeli tespit eder',
            'rule_type': 'anomaly_detection',
            'algorithm': 'statistical_analysis',
            'condition': 'performance_score < 2.5 AND consecutive_months >= 3',
            'threshold_value': 2.5,
            'confidence_threshold': 0.8,
            'sensitivity': 0.6,
            'risk_category': 'medium',
            'data_source': 'Performans Değerlendirme'
        },
        {
            'name': 'Zorunlu Eğitim Eksikliği',
            'description': 'Zorunlu eğitimleri tamamlamayan personeli tespit eder',
            'rule_type': 'compliance',
            'algorithm': 'threshold',
            'condition': 'mandatory_training_completion < 100%',
            'threshold_value': 100.0,
            'confidence_threshold': 1.0,
            'sensitivity': 1.0,
            'risk_category': 'high',
            'data_source': 'Eğitim Kayıtları'
        },
        {
            'name': 'Personel Devir Hızı Analizi',
            'description': 'Departman bazında yüksek personel devir hızını tespit eder',
            'rule_type': 'time_series',
            'algorithm': 'arima',
            'condition': 'monthly_turnover_rate > department_average * 1.5',
            'threshold_value': 1.5,
            'confidence_threshold': 0.75,
            'sensitivity': 0.7,
            'risk_category': 'medium',
            'data_source': 'HRMS Veritabanı'
        },
        {
            'name': 'Bordro Anomali Tespiti',
            'description': 'Beklenenden farklı maaş ödemelerini tespit eder',
            'rule_type': 'anomaly_detection',
            'algorithm': 'autoencoder',
            'condition': 'salary_deviation > 2 * standard_deviation',
            'threshold_value': 2.0,
            'confidence_threshold': 0.85,
            'sensitivity': 0.8,
            'risk_category': 'high',
            'data_source': 'Bordro Sistemi'
        },
        {
            'name': 'İşe Alım Süreci Kontrolü',
            'description': 'İşe alım sürecindeki gecikmeli onayları tespit eder',
            'rule_type': 'compliance',
            'algorithm': 'threshold',
            'condition': 'hiring_process_duration > 30 days',
            'threshold_value': 30.0,
            'confidence_threshold': 0.9,
            'sensitivity': 0.8,
            'risk_category': 'medium',
            'data_source': 'HRMS Veritabanı'
        },
        {
            'name': 'Çalışma Saatleri Uyumluluk',
            'description': 'İş kanununa aykırı çalışma saatlerini tespit eder',
            'rule_type': 'compliance',
            'algorithm': 'threshold',
            'condition': 'weekly_hours > 45 OR daily_break < 1 hour',
            'threshold_value': 45.0,
            'confidence_threshold': 1.0,
            'sensitivity': 1.0,
            'risk_category': 'high',
            'data_source': 'HRMS Veritabanı'
        },
        {
            'name': 'Eğitim Bütçesi Anomalisi',
            'description': 'Departman eğitim bütçesi kullanımındaki anormallikleri tespit eder',
            'rule_type': 'fraud_detection',
            'algorithm': 'isolation_forest',
            'condition': 'training_budget_usage deviation > threshold',
            'threshold_value': None,
            'confidence_threshold': 0.8,
            'sensitivity': 0.7,
            'risk_category': 'medium',
            'data_source': 'Eğitim Kayıtları'
        }
    ]
    
    created_rules = []
    for i, rule_data in enumerate(rules_data):
        # Veri kaynağını bul
        data_source = next((ds for ds in data_sources if ds.name == rule_data['data_source']), data_sources[0])
        
        rule = AuditRule(
            name=rule_data['name'],
            description=rule_data['description'],
            rule_type=rule_data['rule_type'],
            algorithm=rule_data['algorithm'],
            condition=rule_data['condition'],
            threshold_value=rule_data['threshold_value'],
            confidence_threshold=rule_data['confidence_threshold'],
            sensitivity=rule_data['sensitivity'],
            risk_category=rule_data['risk_category'],
            audit_area_id=audit_area_id,
            is_active=True,
            created_at=datetime.now(),
            last_triggered=datetime.now() - timedelta(days=random.randint(1, 30)),
            trigger_count=random.randint(5, 50)
        )
        
        db.session.add(rule)
        created_rules.append(rule)
    
    db.session.commit()
    return created_rules

def create_hr_alarms(rules):
    """HR kuralları için alarmlar oluştur"""
    
    alarm_templates = {
        'anomaly_detection': [
            'Personel {} için aşırı mesai tespit edildi: {} saat',
            'Departman {} için anormal çalışma paterni tespit edildi',
            'Personel {} için performans düşüklüğü tespit edildi'
        ],
        'fraud_detection': [
            'Personel {} için şüpheli maaş ödemesi tespit edildi: {} TL',
            'Departman {} için anormal bordro aktivitesi tespit edildi',
            'Eğitim bütçesi kullanımında anomali tespit edildi: {} TL'
        ],
        'compliance': [
            'Personel {} için izin bakiyesi negatif: {} gün',
            'Personel {} için zorunlu eğitim eksik: {}',
            'İşe alım süreci {} gün gecikti',
            'Personel {} için çalışma saatleri iş kanununa aykırı'
        ],
        'time_series': [
            'Departman {} için personel devir hızı ortalamanın üzerinde: %{}',
            'Aylık işten ayrılma oranı trend analizi uyarısı'
        ]
    }
    
    employee_names = [
        'Ahmet Yılmaz', 'Ayşe Kara', 'Mehmet Demir', 'Fatma Çelik', 'Ali Öz',
        'Zeynep Ak', 'Mustafa Şen', 'Elif Yıldız', 'Osman Taş', 'Merve Koç',
        'Hasan Eroğlu', 'Gül Arslan', 'İbrahim Doğan', 'Selin Türk', 'Emre Balcı'
    ]
    
    departments = ['İnsan Kaynakları', 'Bilgi İşlem', 'Muhasebe', 'Pazarlama', 'Satış', 'Üretim', 'Kalite']
    
    created_alarms = []
    
    for rule in rules:
        # Her kural için 2-8 alarm oluştur
        alarm_count = random.randint(2, 8)
        
        for _ in range(alarm_count):
            templates = alarm_templates.get(rule.rule_type, ['Genel HR uyarısı tespit edildi'])
            template = random.choice(templates)
            
            # Template'e göre mesaj oluştur
            if '{}' in template:
                if 'Personel' in template:
                    employee = random.choice(employee_names)
                    if 'saat' in template:
                        message = template.format(employee, random.randint(13, 18))
                    elif 'TL' in template:
                        amount = random.randint(5000, 50000)
                        message = template.format(employee, f'{amount:,}')
                    elif 'gün' in template:
                        days = random.randint(-15, -1)
                        message = template.format(employee, days)
                    elif 'eğitim' in template:
                        trainings = ['İş Güvenliği', 'KVKK', 'Yangın Güvenliği', 'İlk Yardım']
                        message = template.format(employee, random.choice(trainings))
                    else:
                        message = template.format(employee)
                elif 'Departman' in template:
                    dept = random.choice(departments)
                    if '%' in template:
                        rate = random.randint(15, 35)
                        message = template.format(dept, rate)
                    elif 'TL' in template:
                        amount = random.randint(10000, 100000)
                        message = template.format(dept, f'{amount:,}')
                    else:
                        message = template.format(dept)
                elif 'gün gecikti' in template:
                    days = random.randint(31, 60)
                    message = template.format(days)
                else:
                    message = template.format('bilinmeyen')
            else:
                message = template
            
            # Alarm seviyesini belirle
            if rule.risk_category == 'high':
                severity = random.choices(['critical', 'high', 'medium'], weights=[40, 40, 20])[0]
            elif rule.risk_category == 'medium':
                severity = random.choices(['high', 'medium', 'low'], weights=[20, 60, 20])[0]
            else:
                severity = random.choices(['medium', 'low'], weights=[30, 70])[0]
            
            alarm = Alarm(
                title=message[:128],  # title has max 256 chars
                message=message,
                severity=severity,
                rule_id=rule.id,
                audit_area_id=rule.audit_area_id,
                status='resolved' if random.choice([True, False]) else 'open',
                created_at=datetime.now() - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                ),
                resolved_at=datetime.now() - timedelta(days=random.randint(0, 10)) if random.choice([True, False]) else None
            )
            
            db.session.add(alarm)
            created_alarms.append(alarm)
    
    db.session.commit()
    return created_alarms

def main():
    with app.app_context():
        print("İnsan Kaynakları test verileri oluşturuluyor...")
        
        # Audit alanı oluştur
        print("1. İnsan Kaynakları audit alanı oluşturuluyor...")
        hr_area = create_hr_audit_area()
        print(f"   ✓ Audit alanı oluşturuldu: {hr_area.name}")
        
        # Veri kaynaklarını oluştur
        print("2. HR veri kaynakları oluşturuluyor...")
        data_sources = create_hr_data_sources(hr_area.id)
        print(f"   ✓ {len(data_sources)} veri kaynağı oluşturuldu")
        for ds in data_sources:
            print(f"     - {ds.name} ({ds.source_type})")
        
        # Audit kuralları oluştur
        print("3. HR audit kuralları oluşturuluyor...")
        rules = create_hr_audit_rules(hr_area.id, data_sources)
        print(f"   ✓ {len(rules)} audit kuralı oluşturuldu")
        for rule in rules:
            print(f"     - {rule.name} ({rule.rule_type} - {rule.algorithm})")
        
        # Alarmlar oluştur
        print("4. HR alarmları oluşturuluyor...")
        alarms = create_hr_alarms(rules)
        print(f"   ✓ {len(alarms)} alarm oluşturuldu")
        
        # Özet bilgiler
        critical_count = len([a for a in alarms if a.severity == 'critical'])
        high_count = len([a for a in alarms if a.severity == 'high'])
        medium_count = len([a for a in alarms if a.severity == 'medium'])
        low_count = len([a for a in alarms if a.severity == 'low'])
        
        print("\n" + "="*50)
        print("İNSAN KAYNAKLARI TEST VERİLERİ OLUŞTURULDU")
        print("="*50)
        print(f"Audit Alanı: {hr_area.name}")
        print(f"Veri Kaynakları: {len(data_sources)}")
        print(f"Audit Kuralları: {len(rules)}")
        print(f"Toplam Alarmlar: {len(alarms)}")
        print(f"  - Kritik: {critical_count}")
        print(f"  - Yüksek: {high_count}")
        print(f"  - Orta: {medium_count}")
        print(f"  - Düşük: {low_count}")
        print("="*50)
        
        print("\nKural türleri dağılımı:")
        rule_types = {}
        for rule in rules:
            rule_types[rule.rule_type] = rule_types.get(rule.rule_type, 0) + 1
        
        for rule_type, count in rule_types.items():
            print(f"  - {rule_type}: {count} kural")
        
        print("\nAlgoritma dağılımı:")  
        algorithms = {}
        for rule in rules:
            algorithms[rule.algorithm] = algorithms.get(rule.algorithm, 0) + 1
            
        for algorithm, count in algorithms.items():
            print(f"  - {algorithm}: {count} kural")

if __name__ == '__main__':
    main()