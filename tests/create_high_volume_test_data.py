#!/usr/bin/env python3
"""
Yüksek Hacimli ve Tutarlı Test Verisi Oluşturucu
Bu script gerçek iş senaryolarını simule eden büyük hacimli test verileri oluşturur.
"""

import random
import json
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
from app import app, db
from models import *

# Türkiye'deki şirket isimleri ve sektörler
COMPANY_NAMES = [
    "Arçelik A.Ş.", "Turkcell", "BIM Birleşik Mağazalar", "Akbank T.A.Ş.", "İş Bankası",
    "Garanti BBVA", "Yapı Kredi Bankası", "THY", "Petrol Ofisi", "Ülker Bisküvi",
    "Sabancı Holding", "Koç Holding", "Doğan Holding", "Borusan Holding", "Enka İnşaat",
    "TAV Havalimanları", "Migros", "CarrefourSA", "MediaMarkt", "Teknosa",
    "Halkbank", "Ziraat Bankası", "VakıfBank", "DenizBank", "HSBC Türkiye",
    "ING Bank", "QNB Finansbank", "Şekerbank", "TEB", "ICBC Turkey"
]

DEPARTMENTS = [
    "Muhasebe", "Finans", "İnsan Kaynakları", "Bilgi İşlem", "Satış", "Pazarlama",
    "Üretim", "Kalite Kontrol", "Ar-Ge", "Hukuk", "Güvenlik", "Lojistik",
    "Satın Alma", "İç Denetim", "Risk Yönetimi", "Operasyon", "Strateji"
]

TURKISH_NAMES = [
    "Ahmet Yılmaz", "Mehmet Demir", "Ayşe Kaya", "Fatma Çelik", "Mustafa Aydın",
    "Emine Öztürk", "Ali Arslan", "Hatice Doğan", "İbrahim Kılıç", "Zeynep Şahin",
    "Hüseyin Yıldız", "Zeliha Özkan", "Osman Polat", "Esra Güler", "Yaşar Bozkurt",
    "Sevgi Eren", "Kemal Toprak", "Nermin Bulut", "Recep Koçak", "Gülsüm Acar"
]

TRANSACTION_TYPES = [
    "Maaş Ödemesi", "Tedarikçi Ödemesi", "Vergi Ödemesi", "Sigorta Primi",
    "Kira Ödemesi", "Elektrik Faturası", "Telefon Faturası", "İnternet Faturası",
    "Benzin Gideri", "Yemek Gideri", "Ofis Malzeme", "Bilgisayar Donanımı",
    "Yazılım Lisansı", "Reklam Gideri", "Danışmanlık Ücreti", "Eğitim Gideri",
    "Seyahat Gideri", "Konaklama", "Ulaştırma", "Bakım Onarım"
]

def create_massive_financial_data():
    """50.000 adet finansal işlem verisi oluştur"""
    print("💰 50.000 finansal işlem verisi oluşturuluyor...")
    
    # Finans audit area'sını bul veya oluştur
    finance_area = AuditArea.query.filter_by(name='Finansal İşlemler').first()
    if not finance_area:
        finance_area = AuditArea(
            name='Finansal İşlemler',
            description='Yüksek hacimli finansal işlem verileri',
            owner_id=1  # Admin user
        )
        db.session.add(finance_area)
        db.session.flush()
    
    # 50.000 finansal işlem kaydı
    transactions = []
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(50000):
        # %5 oranında anomali oluştur
        is_anomaly = random.random() < 0.05
        
        # Normal işlem: 100-50.000 TL arası
        # Anomali işlem: 500.000-2.000.000 TL arası
        if is_anomaly:
            amount = random.uniform(500000, 2000000)
            # Anomali işlemleri genelde hafta sonu
            transaction_date = base_date + timedelta(
                days=random.randint(0, 365),
                hours=random.choice([0, 1, 22, 23])  # Gece saatleri
            )
            # Hafta sonu yapma ihtimali %70
            if random.random() < 0.7:
                # Cumartesi veya Pazar'a ayarla
                days_to_weekend = (5 - transaction_date.weekday()) % 7
                if days_to_weekend == 0:
                    days_to_weekend = 6
                transaction_date += timedelta(days=days_to_weekend)
        else:
            amount = random.uniform(100, 50000)
            # Normal işlem saatleri
            transaction_date = base_date + timedelta(
                days=random.randint(0, 365),
                hours=random.randint(8, 18)
            )
            # Hafta içi yap
            if transaction_date.weekday() >= 5:  # Hafta sonu ise
                transaction_date -= timedelta(days=transaction_date.weekday() - 4)
        
        transaction = {
            'id': f'TXN{i+1:06d}',
            'audit_area_id': finance_area.id,
            'company': random.choice(COMPANY_NAMES),
            'department': random.choice(DEPARTMENTS),
            'transaction_type': random.choice(TRANSACTION_TYPES),
            'amount': round(amount, 2),
            'currency': 'TRY',
            'description': f"{random.choice(TRANSACTION_TYPES)} - {random.choice(COMPANY_NAMES)}",
            'processed_by': random.choice(TURKISH_NAMES),
            'approved_by': random.choice(TURKISH_NAMES) if amount > 10000 else None,
            'transaction_date': transaction_date,
            'created_at': transaction_date + timedelta(minutes=random.randint(1, 60)),
            'is_anomaly': is_anomaly,
            'risk_score': random.uniform(0.8, 1.0) if is_anomaly else random.uniform(0.1, 0.3)
        }
        transactions.append(transaction)
        
        if i % 10000 == 0:
            print(f"  ✅ {i:,} işlem oluşturuldu...")
    
    # JSON formatında kaydet (simülasyon)
    print(f"💾 {len(transactions):,} finansal işlem hazırlandı")
    return transactions

def create_massive_hr_data():
    """20.000 adet İK verisi oluştur"""
    print("👥 20.000 İK verisi oluşturuluyor...")
    
    hr_area = AuditArea.query.filter_by(name='İnsan Kaynakları').first()
    if not hr_area:
        hr_area = AuditArea(
            name='İnsan Kaynakları',
            description='Yüksek hacimli İK verileri',
            owner_id=1  # Admin user
        )
        db.session.add(hr_area)
        db.session.flush()
    
    employees = []
    base_date = datetime.now() - timedelta(days=730)  # 2 yıl
    
    for i in range(20000):
        # %3 oranında anomali (fazla mesai, maaş anomalisi)
        is_anomaly = random.random() < 0.03
        
        # Normal maaş: 15.000-80.000 TL
        # Anomali maaş: 200.000-500.000 TL
        base_salary = random.uniform(200000, 500000) if is_anomaly else random.uniform(15000, 80000)
        
        # Fazla mesai anomalisi
        overtime_hours = random.randint(200, 400) if is_anomaly else random.randint(0, 50)
        
        employee = {
            'id': f'EMP{i+1:05d}',
            'audit_area_id': hr_area.id,
            'name': random.choice(TURKISH_NAMES),
            'department': random.choice(DEPARTMENTS),
            'position': random.choice(['Uzman', 'Kıdemli Uzman', 'Müdür', 'Müdür Yardımcısı', 'Direktör']),
            'hire_date': base_date + timedelta(days=random.randint(0, 700)),
            'base_salary': round(base_salary, 2),
            'overtime_hours': overtime_hours,
            'performance_score': random.uniform(1.0, 5.0),
            'department_budget': random.uniform(100000, 5000000),
            'employee_id': f'TR{random.randint(10000000000, 99999999999)}',
            'is_active': random.choice([True, True, True, False]),  # %25 pasif
            'is_anomaly': is_anomaly,
            'risk_score': random.uniform(0.7, 1.0) if is_anomaly else random.uniform(0.1, 0.4)
        }
        employees.append(employee)
        
        if i % 5000 == 0:
            print(f"  ✅ {i:,} çalışan oluşturuldu...")
    
    print(f"👤 {len(employees):,} İK verisi hazırlandı")
    return employees

def create_massive_security_data():
    """30.000 adet güvenlik verisi oluştur"""
    print("🔒 30.000 güvenlik olayı oluşturuluyor...")
    
    security_area = AuditArea.query.filter_by(name='BT Güvenlik').first()
    if not security_area:
        security_area = AuditArea(
            name='BT Güvenlik',
            description='Yüksek hacimli güvenlik verileri',
            owner_id=1  # Admin user
        )
        db.session.add(security_area)
        db.session.flush()
    
    # Şüpheli IP adresleri
    suspicious_ips = [
        '192.168.1.200', '10.0.0.250', '172.16.0.100', '203.0.113.50',
        '198.51.100.75', '91.198.174.192', '185.199.108.153'
    ]
    
    normal_ips = [
        '192.168.1.10', '192.168.1.15', '192.168.1.20', '10.0.0.5',
        '172.16.0.10', '172.16.0.15'
    ]
    
    security_events = []
    base_date = datetime.now() - timedelta(days=180)  # 6 ay
    
    for i in range(30000):
        # %8 oranında güvenlik anomalisi
        is_security_threat = random.random() < 0.08
        
        if is_security_threat:
            event_type = random.choice([
                'Şüpheli Giriş Denemesi', 'Brute Force Saldırısı', 'SQL Injection',
                'XSS Saldırısı', 'Yetkisiz Erişim', 'Malware Tespiti'
            ])
            ip_address = random.choice(suspicious_ips)
            attempt_count = random.randint(50, 500)
            risk_score = random.uniform(0.7, 1.0)
        else:
            event_type = random.choice([
                'Normal Giriş', 'Sistem Erişimi', 'Dosya İndirme',
                'Rapor Görüntüleme', 'Veri Sorgusu'
            ])
            ip_address = random.choice(normal_ips)
            attempt_count = random.randint(1, 5)
            risk_score = random.uniform(0.1, 0.3)
        
        event_date = base_date + timedelta(
            days=random.randint(0, 180),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        security_event = {
            'id': f'SEC{i+1:06d}',
            'audit_area_id': security_area.id,
            'event_type': event_type,
            'ip_address': ip_address,
            'user_agent': random.choice([
                'Mozilla/5.0 Chrome/91.0', 'curl/7.68.0', 'python-requests/2.25.1',
                'Mozilla/5.0 Firefox/89.0', 'Safari/14.1'
            ]),
            'user_name': random.choice(TURKISH_NAMES) if not is_security_threat else 'Unknown',
            'attempt_count': attempt_count,
            'success_count': random.randint(0, attempt_count),
            'country': random.choice(['Turkey', 'Russia', 'China', 'USA']) if is_security_threat else 'Turkey',
            'is_blocked': is_security_threat,
            'threat_level': 'critical' if is_security_threat else 'low',
            'event_date': event_date,
            'is_anomaly': is_security_threat,
            'risk_score': risk_score
        }
        security_events.append(security_event)
        
        if i % 10000 == 0:
            print(f"  ✅ {i:,} güvenlik olayı oluşturuldu...")
    
    print(f"🛡️ {len(security_events):,} güvenlik verisi hazırlandı")
    return security_events

def create_massive_procurement_data():
    """15.000 adet satın alma verisi oluştur"""
    print("🛒 15.000 satın alma verisi oluşturuluyor...")
    
    procurement_area = AuditArea.query.filter_by(name='Satın Alma').first()
    if not procurement_area:
        procurement_area = AuditArea(
            name='Satın Alma',
            description='Yüksek hacimli satın alma verileri',
            owner_id=1  # Admin user
        )
        db.session.add(procurement_area)
        db.session.flush()
    
    vendors = [
        'ABC Tedarik Ltd.', 'XYZ Malzeme A.Ş.', 'Güvenilir Tedarikçi', 'Hızlı Kargo',
        'Kaliteli Ürünler', 'Ekonomik Çözümler', 'Profesyonel Hizmet', 'İnovatif Teknoloji'
    ]
    
    # Şüpheli tedarikçiler (%10)
    suspicious_vendors = ['Şüpheli Firm Ltd.', 'Bilinmeyen Tedarik', 'Sahte Şirket A.Ş.']
    
    procurements = []
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(15000):
        # %7 oranında satın alma anomalisi
        is_fraud = random.random() < 0.07
        
        if is_fraud:
            vendor = random.choice(suspicious_vendors)
            unit_price = random.uniform(5000, 50000)  # Yüksek fiyat
            quantity = random.randint(100, 1000)
            discount = 0  # İndirim yok
        else:
            vendor = random.choice(vendors)
            unit_price = random.uniform(10, 5000)
            quantity = random.randint(1, 100)
            discount = random.uniform(0, 0.2)  # %0-20 indirim
        
        total_amount = unit_price * quantity * (1 - discount)
        
        procurement = {
            'id': f'PO{i+1:06d}',
            'audit_area_id': procurement_area.id,
            'vendor_name': vendor,
            'product_category': random.choice([
                'Bilgisayar Donanımı', 'Ofis Malzemeleri', 'Temizlik Ürünleri',
                'Yazılım Lisansı', 'Mobilya', 'Elektrikli Aletler'
            ]),
            'unit_price': round(unit_price, 2),
            'quantity': quantity,
            'discount_rate': discount,
            'total_amount': round(total_amount, 2),
            'order_date': base_date + timedelta(days=random.randint(0, 365)),
            'approved_by': random.choice(TURKISH_NAMES),
            'delivery_status': random.choice(['Teslim Edildi', 'Beklemede', 'İptal']),
            'payment_method': random.choice(['Kredi', 'Nakit', 'Havale']),
            'is_anomaly': is_fraud,
            'risk_score': random.uniform(0.8, 1.0) if is_fraud else random.uniform(0.1, 0.4)
        }
        procurements.append(procurement)
        
        if i % 5000 == 0:
            print(f"  ✅ {i:,} satın alma kaydı oluşturuldu...")
    
    print(f"📦 {len(procurements):,} satın alma verisi hazırlandı")
    return procurements

def create_high_volume_alarms(financial_data, hr_data, security_data, procurement_data):
    """Yüksek hacimli verilerden gerçekçi alarmlar oluştur"""
    print("🚨 Yüksek hacimli veri setinden alarmlar oluşturuluyor...")
    
    # Mevcut kuralları al
    rules = AuditRule.query.all()
    alarms = []
    
    # Finansal anomalilerden alarmlar
    financial_anomalies = [t for t in financial_data if t['is_anomaly']]
    for anomaly in financial_anomalies[:500]:  # İlk 500 anomali
        if rules:
            rule = random.choice([r for r in rules if r.rule_type in ['anomaly_detection', 'threshold']])
            if rule:
                alarm = Alarm(
                    rule_id=rule.id,
                    audit_area_id=anomaly['audit_area_id'],
                    title=f"Yüksek Tutarlı İşlem Tespit Edildi: {anomaly['amount']:,.2f} TL",
                    message=f"Şirket: {anomaly['company']}, İşlem Türü: {anomaly['transaction_type']}, Risk Skoru: {anomaly['risk_score']:.2%}",
                    severity='critical' if anomaly['amount'] > 1000000 else 'high',
                    status=random.choice(['open', 'acknowledged']),
                    data={
                        'transaction_data': anomaly,
                        'detection_type': 'financial_anomaly',
                        'algorithm': 'isolation_forest'
                    },
                    created_at=anomaly['transaction_date'] + timedelta(minutes=5)
                )
                alarms.append(alarm)
    
    # Güvenlik olaylarından alarmlar
    security_threats = [s for s in security_data if s['is_anomaly']]
    for threat in security_threats[:800]:  # İlk 800 tehdit
        if rules:
            rule = random.choice([r for r in rules if r.rule_type == 'security'])
            if rule:
                alarm = Alarm(
                    rule_id=rule.id,
                    audit_area_id=threat['audit_area_id'],
                    title=f"Güvenlik Tehdidi: {threat['event_type']}",
                    message=f"IP: {threat['ip_address']}, Deneme: {threat['attempt_count']}, Ülke: {threat['country']}",
                    severity='critical',
                    status=random.choice(['open', 'acknowledged', 'resolved']),
                    data={
                        'security_data': threat,
                        'detection_type': 'security_threat',
                        'algorithm': 'pattern_matching'
                    },
                    created_at=threat['event_date'] + timedelta(minutes=1)
                )
                alarms.append(alarm)
    
    # İK anomalilerinden alarmlar
    hr_anomalies = [h for h in hr_data if h['is_anomaly']]
    for anomaly in hr_anomalies[:200]:  # İlk 200 anomali
        if rules:
            rule = random.choice([r for r in rules if r.rule_type in ['anomaly_detection', 'fraud_detection']])
            if rule:
                alarm = Alarm(
                    rule_id=rule.id,
                    audit_area_id=anomaly['audit_area_id'],
                    title=f"İK Anomalisi: {anomaly['name']}",
                    message=f"Maaş: {anomaly['base_salary']:,.2f} TL, Fazla Mesai: {anomaly['overtime_hours']} saat",
                    severity='high',
                    status=random.choice(['open', 'acknowledged']),
                    data={
                        'hr_data': anomaly,
                        'detection_type': 'hr_anomaly',
                        'algorithm': 'statistical_anomaly'
                    },
                    created_at=datetime.now() - timedelta(days=random.randint(1, 30))
                )
                alarms.append(alarm)
    
    # Satın alma dolandırıcılıklarından alarmlar
    procurement_frauds = [p for p in procurement_data if p['is_anomaly']]
    for fraud in procurement_frauds[:300]:  # İlk 300 dolandırıcılık
        if rules:
            rule = random.choice([r for r in rules if r.rule_type == 'fraud_detection'])
            if rule:
                alarm = Alarm(
                    rule_id=rule.id,
                    audit_area_id=fraud['audit_area_id'],
                    title=f"Tedarikçi Dolandırıcılığı: {fraud['vendor_name']}",
                    message=f"Tutar: {fraud['total_amount']:,.2f} TL, Ürün: {fraud['product_category']}",
                    severity='high',
                    status=random.choice(['open', 'acknowledged']),
                    data={
                        'procurement_data': fraud,
                        'detection_type': 'vendor_fraud',
                        'algorithm': 'random_forest'
                    },
                    created_at=fraud['order_date'] + timedelta(hours=2)
                )
                alarms.append(alarm)
    
    # Alarmları veritabanına kaydet
    for alarm in alarms:
        db.session.add(alarm)
    
    print(f"🔔 {len(alarms):,} alarm oluşturuldu")
    return alarms

def main():
    """Ana fonksiyon - Yüksek hacimli test verisi oluştur"""
    with app.app_context():
        print("🚀 YÜKSEK HACİMLİ TEST VERİSİ OLUŞTURMA BAŞLADI")
        print("=" * 60)
        
        try:
            # 1. Finansal veriler (50.000 kayıt)
            financial_data = create_massive_financial_data()
            
            # 2. İK verileri (20.000 kayıt)
            hr_data = create_massive_hr_data()
            
            # 3. Güvenlik verileri (30.000 kayıt)
            security_data = create_massive_security_data()
            
            # 4. Satın alma verileri (15.000 kayıt)
            procurement_data = create_massive_procurement_data()
            
            # 5. Veritabanı değişikliklerini kaydet
            db.session.commit()
            print("💾 Audit area'lar veritabanına kaydedildi")
            
            # 6. Yüksek hacimli alarmlar oluştur
            alarms = create_high_volume_alarms(financial_data, hr_data, security_data, procurement_data)
            
            # 7. Tüm değişiklikleri kaydet
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("✅ YÜKSEK HACİMLİ TEST VERİSİ BAŞARIYLA OLUŞTURULDU!")
            print("=" * 60)
            print(f"📊 TOPLAM VERİ ÖZETİ:")
            print(f"   • Finansal İşlemler: {len(financial_data):,} kayıt")
            print(f"   • İK Verileri: {len(hr_data):,} kayıt")
            print(f"   • Güvenlik Olayları: {len(security_data):,} kayıt")
            print(f"   • Satın Alma: {len(procurement_data):,} kayıt")
            print(f"   • Alarmlar: {len(alarms):,} kayıt")
            print(f"   📈 TOPLAM: {len(financial_data) + len(hr_data) + len(security_data) + len(procurement_data):,} veri kaydı")
            print(f"   🚨 Anomali Oranı: ~%5-8 (gerçekçi seviyelerde)")
            print(f"   ⚡ Sistem artık yüksek hacimli verilerle test edilmeye hazır!")
            
        except Exception as e:
            print(f"❌ HATA: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()