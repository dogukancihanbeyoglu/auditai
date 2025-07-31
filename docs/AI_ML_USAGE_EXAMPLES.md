# AuditAI Yapay Zeka Sistemi - Pratik Kullanım Örnekleri

## İçindekiler
1. [Adım Adım Kural Oluşturma](#adım-adım-kural-oluşturma)
2. [Gerçek Senaryo Örnekleri](#gerçek-senaryo-örnekleri)
3. [Alarm Yönetimi](#alarm-yönetimi)
4. [Performans Optimizasyonu](#performans-optimizasyonu)
5. [API Kullanım Örnekleri](#api-kullanım-örnekleri)

---

## Adım Adım Kural Oluşturma

### Örnek 1: Finansal Anomali Tespiti

**Hedef**: Hafta sonu yapılan yüksek tutarlı işlemleri tespit etmek

#### Adım 1: Web Arayüzüne Erişim
```
1. http://localhost:5000 adresine gidin
2. Admin hesabı ile giriş yapın (admin/admin123)
3. Sol menüden "Audit Areas" → "Rules" seçin
4. "Create New Rule" butonuna tıklayın
```

#### Adım 2: Temel Bilgiler
```
Kural Adı: Hafta Sonu Yüksek Tutar Anomalisi
Açıklama: Cumartesi-Pazar günleri 100.000 TL üzeri işlemleri analiz eder
Audit Area: Finansal İşlemler
Kural Türü: Anomaly Detection (Anomali Tespiti)
```

#### Adım 3: Yapay Zeka Konfigürasyonu
```
Algoritma: Isolation Forest
Hassasiyet: 0.8 (Yüksek)
Güven Eşiği: 0.85 (%85)
Risk Kategorisi: Yüksek
```

#### Adım 4: Veri Konfigürasyonu
```json
{
    "data_source": "financial_transactions",
    "target_fields": ["amount", "transaction_date", "day_of_week"],
    "filters": {
        "amount": {"operator": ">", "value": 100000},
        "day_of_week": {"operator": "in", "value": [6, 7]}
    },
    "feature_engineering": {
        "normalize_amount": true,
        "extract_hour": true,
        "weekend_flag": true
    }
}
```

#### Adım 5: Alarm Ayarları
```
Önem Seviyesi: Critical (Kritik)
Bildirim: Anında
Otomatik Eylem: Alarm Oluştur + E-posta Gönder
Aktiflik: Etkin
```

#### Beklenen Sonuç
```json
{
    "alarm_example": {
        "title": "Hafta Sonu Yüksek Tutar Anomalisi",
        "message": "Cumartesi günü 750,000 TL tutarında transfer işlemi tespit edildi",
        "severity": "critical",
        "data": {
            "amount": 750000,
            "day": "Cumartesi",
            "time": "14:30",
            "anomaly_score": 0.92,
            "similar_cases": 2
        }
    }
}
```

---

### Örnek 2: İnsan Kaynakları Anomali Analizi

**Hedef**: Çalışanların olağandışı fazla mesai yapma durumlarını tespit etmek

#### Web Arayüzü Adımları
```
1. Rules → Create New Rule
2. Kural Adı: "Fazla Mesai Anomali Tespiti"
3. Kural Türü: "Anomaly Detection"
4. Algoritma: "Statistical Anomaly"
```

#### Detaylı Konfigürasyon
```json
{
    "rule_config": {
        "name": "Fazla Mesai Anomali Tespiti",
        "algorithm": "statistical_anomaly",
        "data_source": "hr_data",
        "analysis_fields": {
            "primary": "overtime_hours",
            "context": ["department", "position", "base_salary"],
            "time_period": "monthly"
        },
        "thresholds": {
            "statistical_threshold": 3.0,  // 3 standart sapma
            "minimum_hours": 50,           // Minimum 50 saat fazla mesai
            "department_comparison": true   // Departman ortalaması ile karşılaştır
        }
    }
}
```

#### Pratik Test Senaryosu
```python
# Test verisi oluşturma
test_employee_data = {
    "employee_id": "EMP001",
    "name": "Ahmet Yılmaz",
    "department": "Muhasebe",
    "normal_overtime": 45,      # Normal aylık fazla mesai
    "anomaly_overtime": 315,    # Anormal aylık fazla mesai
    "department_average": 52    # Departman ortalaması
}

# Beklenen alarm
expected_alarm = {
    "title": "Fazla Mesai Anomalisi: Ahmet Yılmaz",
    "message": "315 saat fazla mesai (departman ort: 52 saat) - %504 artış",
    "severity": "high",
    "recommendations": [
        "İş yükü dağılımını gözden geçirin",
        "Ek personel ihtiyacını değerlendirin",
        "Çalışan sağlığını kontrol edin"
    ]
}
```

---

### Örnek 3: Güvenlik Tehdit Analizi

**Hedef**: Şüpheli IP adreslerinden gelen saldırıları tespit etmek

#### Kural Oluşturma Süreci
```
1. Rules → Create New Rule
2. Kural Adı: "Brute Force Saldırı Tespiti"  
3. Kural Türü: "Security"
4. Algoritma: "Pattern Matching"
```

#### Gelişmiş Güvenlik Konfigürasyonu
```json
{
    "security_rule": {
        "name": "Brute Force Saldırı Tespiti",
        "algorithm": "pattern_matching",
        "detection_patterns": {
            "failed_login_threshold": 15,
            "time_window_minutes": 5,
            "unique_username_attempts": 5,
            "success_rate_threshold": 0.1
        },
        "ip_reputation": {
            "check_blacklist": true,
            "geo_location_risk": true,
            "previous_incidents": true
        },
        "auto_actions": {
            "block_ip": true,
            "alert_security_team": true,
            "log_incident": true
        }
    }
}
```

#### Real-time Test Simülasyonu
```bash
# Test saldırısı simülasyonu (sadece test ortamında)
for i in {1..20}; do
    curl -X POST http://localhost:5000/auth/login \
         -d "username=admin&password=wrong_password" \
         -H "X-Forwarded-For: 192.168.1.200"
    sleep 2
done

# Beklenen sistem tepkisi
echo "IP 192.168.1.200 otomatik olarak engellenecek"
echo "Güvenlik alarmı oluşturulacak"
echo "Admin bilgilendirme e-postası gönderilecek"
```

---

## Gerçek Senaryo Örnekleri

### Senaryo 1: Bankacılık Sektörü - Dolandırıcılık Tespiti

**Durum**: Bir bankada müşteri hesaplarında şüpheli para transferleri tespit edilmek isteniyor.

#### Sistem Konfigürasyonu
```json
{
    "banking_fraud_detection": {
        "rule_name": "Müşteri Hesap Dolandırıcılık Tespiti",
        "algorithm": "random_forest",
        "features": [
            "transfer_amount",
            "recipient_bank",
            "transaction_hour", 
            "customer_location",
            "device_fingerprint",
            "transaction_frequency"
        ],
        "risk_factors": {
            "high_amount": "> 500,000 TL",
            "unusual_time": "22:00-06:00",
            "new_recipient": "< 30 gün",
            "location_mismatch": "farklı şehir",
            "device_change": "yeni cihaz"
        }
    }
}
```

#### Web Arayüzü Adımları
```
1. Audit Areas → "Bankacılık İşlemleri" oluştur
2. Data Sources → "Müşteri İşlemleri Veritabanı" bağla
3. Rules → Create New Rule:
   - Kural Türü: Fraud Detection
   - Algoritma: Random Forest
   - Hassasiyet: 0.9 (Çok Yüksek)
   - Real-time analiz: Etkin
```

#### Pratik Sonuç
```json
{
    "fraud_alert": {
        "title": "Müşteri Dolandırıcılık Riski Yüksek",
        "customer_id": "CUST_789456",
        "transaction_id": "TXN_987654321",
        "amount": "1,250,000 TL",
        "risk_score": 0.94,
        "risk_factors": [
            "Gece saatlerinde işlem (02:15)",
            "Yeni alıcı hesabı (5 günlük)",
            "Müşteri lokasyonu farklı (İstanbul → Ankara)",
            "Yüksek tutar (ortalama işlemin %1200'ü)"
        ],
        "recommended_actions": [
            "İşlemi durdur",
            "Müşteriyi ara ve doğrula", 
            "Güvenlik birimini bilgilendir"
        ]
    }
}
```

---

### Senaryo 2: E-ticaret - Satış Trend Analizi

**Durum**: Online mağazada ani satış düşüşlerini önceden tespit etmek.

#### Zaman Serisi Analizi Konfigürasyonu
```json
{
    "ecommerce_trend_analysis": {
        "rule_name": "Günlük Satış Trend Analizi",
        "algorithm": "prophet",
        "time_series_config": {
            "frequency": "daily",
            "forecast_periods": 30,
            "confidence_interval": 0.95,
            "seasonality": {
                "yearly": true,
                "weekly": true,
                "monthly": true,
                "holiday_effects": true
            }
        },
        "anomaly_detection": {
            "method": "confidence_interval",
            "deviation_threshold": 2.5,
            "consecutive_days": 3
        }
    }
}
```

#### Adım Adım Uygulama
```
1. Data Sources → "Satış Veritabanı" bağlantısı kur
2. Veri Mapping:
   - Tarih alanı: sale_date
   - Değer alanı: daily_revenue
   - Kategori: product_category
3. Rules → Time Series Rule oluştur:
   - Prophet algoritması seç
   - 30 günlük tahmin penceresi
   - Haftalık ve yıllık mevsimsellik etkin
```

#### Görsel Dashboard Sonucu
```
📈 SATIŞ TREND ANALİZİ RAPORU
════════════════════════════════════

Güncel Durum: 🔴 Anomali Tespit Edildi
Son 3 gün ortalama: 85,000 TL (Beklenen: 125,000 TL)
Sapma oranı: -32%

📊 Trend Analizi:
┌────────────┬─────────────┬─────────────┬──────────────┐
│    Tarih   │   Gerçek    │  Tahmin     │    Sapma     │
├────────────┼─────────────┼─────────────┼──────────────┤
│ 24.01.2025 │   68,500 TL │  122,000 TL │     -44%     │
│ 25.01.2025 │   79,200 TL │  118,500 TL │     -33%     │
│ 26.01.2025 │  108,300 TL │  125,800 TL │     -14%     │
└────────────┴─────────────┴─────────────┴──────────────┘

🔍 Olası Nedenler:
• Rekabet artışı
• Kampanya sonu etkisi  
• Mevsimsel değişim
• Teknik sorunlar

💡 Öneriler:
• Acil pazarlama kampanyası
• Müşteri geri bildirim analizi
• Rakip fiyat araştırması
```

---

## Alarm Yönetimi

### Alarm Onaylama ve Red İşlemleri

#### Web Arayüzünde Alarm Yönetimi
```
1. Dashboard → "Alarms" sekmesi
2. Alarm listesinde ilgili kaydı seç
3. Alarm detaylarını incele:
   - Risk skoru
   - Tespit algoritması
   - Veri kanıtları
   - Geçmiş benzer durumlar
4. Eylem seç:
   - ✅ Onayla (Acknowledge)
   - ❌ Reddet (Dismiss)  
   - 🔄 Araştır (Investigate)
   - ✔️ Çözüldü (Resolve)
```

#### API ile Toplu Alarm İşleme
```python
import requests

# Kritik alarmları toplu onayla
def acknowledge_critical_alarms():
    # Kritik alarmları getir
    response = requests.get('/api/alarms?severity=critical&status=open')
    alarms = response.json()
    
    for alarm in alarms:
        # Her alarmı incele ve onayla
        ack_data = {
            "status": "acknowledged",
            "notes": "Otomatik onay - güvenlik ekibi bilgilendirildi",
            "acknowledged_by": "security_admin"
        }
        
        requests.put(f'/api/alarms/{alarm["id"]}/acknowledge', json=ack_data)
        print(f"Alarm {alarm['id']} onaylandı: {alarm['title']}")

# Kullanım
acknowledge_critical_alarms()
```

### Alarm Filtreleme ve Arama
```python
# Gelişmiş alarm sorgulama
def advanced_alarm_search():
    search_params = {
        "date_range": {
            "start": "2025-01-01",
            "end": "2025-01-26"
        },
        "severity": ["critical", "high"],
        "algorithm": ["isolation_forest", "random_forest"],
        "status": ["open", "acknowledged"],
        "rule_type": ["anomaly_detection", "fraud_detection"],
        "risk_score": {"min": 0.8, "max": 1.0}
    }
    
    response = requests.post('/api/alarms/search', json=search_params)
    return response.json()

# Sonuç formatı
{
    "total_count": 156,
    "filtered_count": 23,
    "alarms": [
        {
            "id": "ALARM_001",
            "title": "Yüksek Tutarlı İşlem Anomalisi",
            "severity": "critical",
            "risk_score": 0.94,
            "algorithm": "isolation_forest",
            "created_at": "2025-01-26T10:30:00Z"
        }
    ]
}
```

---

## Performans Optimizasyonu

### Model Performans İzleme

#### Dashboard Metrikleri
```
📊 MODEL PERFORMANS RAPORU
═══════════════════════════════════

🤖 Isolation Forest (Finansal Anomali)
├── Accuracy: 94.2%     ├── Precision: 89.7%
├── Recall: 91.8%       ├── F1-Score: 90.7%
├── İşlem Süresi: 145ms ├── Son Eğitim: 2 gün önce
└── Durum: ✅ Sağlıklı   └── Drift: ⚠️ Hafif

🔍 Random Forest (Dolandırıcılık)
├── Accuracy: 91.5%     ├── Precision: 93.2%
├── Recall: 88.9%       ├── F1-Score: 91.0%
├── İşlem Süresi: 89ms  ├── Son Eğitim: 1 gün önce
└── Durum: ✅ Sağlıklı   └── Drift: ✅ Stabil

📈 Prophet (Trend Analizi)
├── MAPE: 8.7%          ├── MAE: 12,450 TL
├── RMSE: 18,900 TL     ├── Coverage: 94.1%
├── İşlem Süresi: 2.3s  ├── Son Eğitim: 3 gün önce
└── Durum: ✅ Sağlıklı   └── Seasonality: ✅ Aktif
```

#### Otomatik Model Güncelleme
```python
class ModelMaintenanceSystem:
    def __init__(self):
        self.performance_threshold = 0.85
        self.drift_threshold = 0.1
        
    def daily_model_check(self):
        """Günlük model kontrol ve bakım"""
        models = self.get_all_models()
        
        for model in models:
            # Performans kontrolü
            current_performance = self.evaluate_model(model)
            
            if current_performance < self.performance_threshold:
                print(f"⚠️ Model {model.name} performansı düşük: {current_performance:.2%}")
                self.schedule_retraining(model)
            
            # Drift tespiti
            drift_score = self.detect_drift(model)
            
            if drift_score > self.drift_threshold:
                print(f"🔄 Model {model.name} drift tespit edildi: {drift_score:.3f}")
                self.retrain_model(model)
            
            # Kaynak kullanımı optimizasyonu
            self.optimize_resources(model)
    
    def optimize_resources(self, model):
        """Kaynak kullanımı optimizasyonu"""
        # Memory cleanup
        if model.memory_usage > 500:  # MB
            model.clear_cache()
            
        # Batch size optimization
        if model.avg_processing_time > 200:  # ms
            model.batch_size = min(model.batch_size * 0.8, 500)
            
        # Feature selection optimization
        unused_features = model.get_unused_features()
        if len(unused_features) > 5:
            model.remove_features(unused_features)
```

---

## API Kullanım Örnekleri

### RESTful API Endpoint'leri

#### 1. Kural Yönetimi API
```python
import requests
import json

# Base URL
API_BASE = "http://localhost:5000/api"

# 1. Yeni AI kuralı oluştur
def create_ai_rule():
    rule_data = {
        "name": "API Test Anomali Kuralı",
        "rule_type": "anomaly_detection",
        "algorithm": "isolation_forest",
        "audit_area_id": 1,
        "sensitivity": 0.8,
        "confidence_threshold": 0.85,
        "conditions": {
            "amount": {"operator": ">", "value": 100000},
            "time_filter": {"operator": "weekend", "value": true}
        },
        "alert_settings": {
            "severity": "high",
            "notification": "immediate",
            "auto_action": "create_alarm"
        }
    }
    
    response = requests.post(f"{API_BASE}/rules", 
                           json=rule_data, 
                           headers={"Content-Type": "application/json"})
    
    if response.status_code == 201:
        rule = response.json()
        print(f"✅ Kural başarıyla oluşturuldu: {rule['id']}")
        return rule['id']
    else:
        print(f"❌ Hata: {response.json()}")

# 2. Kural performansını sorgula
def get_rule_performance(rule_id):
    response = requests.get(f"{API_BASE}/rules/{rule_id}/performance")
    
    if response.status_code == 200:
        perf = response.json()
        print(f"""
📊 KURAL PERFORMANSI: {rule_id}
═══════════════════════════════════
Accuracy: {perf['accuracy']:.2%}
Precision: {perf['precision']:.2%}
Recall: {perf['recall']:.2%}
F1-Score: {perf['f1_score']:.2%}
Toplam Çalıştırma: {perf['total_executions']}
Üretilen Alarm: {perf['alarms_generated']}
Ortalama İşlem Süresi: {perf['avg_processing_time']:.0f}ms
        """)
        return perf
```

#### 2. Alarm Yönetimi API
```python
# Alarm listesi getir
def get_alarms(filters=None):
    params = filters or {}
    response = requests.get(f"{API_BASE}/alarms", params=params)
    
    if response.status_code == 200:
        alarms = response.json()
        print(f"📋 Toplam {len(alarms)} alarm bulundu")
        
        for alarm in alarms[:5]:  # İlk 5 alarm
            print(f"""
🚨 {alarm['title']}
   Önem: {alarm['severity'].upper()}
   Durum: {alarm['status']}
   Tarih: {alarm['created_at']}
   Risk Skoru: {alarm.get('risk_score', 'N/A')}
            """)
        return alarms

# Alarm detaylarını getir
def get_alarm_details(alarm_id):
    response = requests.get(f"{API_BASE}/alarms/{alarm_id}")
    
    if response.status_code == 200:
        alarm = response.json()
        print(f"""
🔍 ALARM DETAYI: {alarm_id}
═══════════════════════════════════
Başlık: {alarm['title']}
Mesaj: {alarm['message']}
Önem: {alarm['severity']}
Durum: {alarm['status']}
Kural: {alarm['rule_name']}
Algoritma: {alarm['detection_algorithm']}
Risk Skoru: {alarm['risk_score']:.2%}
Oluşturma: {alarm['created_at']}

📊 VERİ ANALİZİ:
{json.dumps(alarm['analysis_data'], indent=2, ensure_ascii=False)}
        """)
        return alarm

# Alarm durumunu güncelle
def update_alarm_status(alarm_id, status, notes=""):
    update_data = {
        "status": status,
        "notes": notes,
        "updated_by": "api_user"
    }
    
    response = requests.put(f"{API_BASE}/alarms/{alarm_id}/status", 
                          json=update_data)
    
    if response.status_code == 200:
        print(f"✅ Alarm {alarm_id} durumu '{status}' olarak güncellendi")
        return True
    else:
        print(f"❌ Güncelleme hatası: {response.json()}")
        return False
```

#### 3. Analiz ve Raporlama API
```python
# Sistem sağlık raporu
def get_system_health():
    response = requests.get(f"{API_BASE}/system/health")
    health = response.json()
    
    print(f"""
🏥 SİSTEM SAĞLIK RAPORU
═══════════════════════════════════
Sistem Durumu: {'🟢 Sağlıklı' if health['status'] == 'healthy' else '🔴 Problem'}
CPU Kullanımı: {health['cpu_usage']:.1f}%
Memory Kullanımı: {health['memory_usage']:.1f}%
Aktif Kural Sayısı: {health['active_rules']}
Günlük İşlem Sayısı: {health['daily_processed']:,}
Ortalama Yanıt Süresi: {health['avg_response_time']:.0f}ms

🤖 AI/ML MODEL DURUMU:
""")
    
    for model in health['models']:
        status_icon = '🟢' if model['status'] == 'healthy' else '🟡' if model['status'] == 'warning' else '🔴'
        print(f"{status_icon} {model['name']}: {model['performance']:.1%} accuracy")

# Trend analizi raporu
def get_trend_analysis(days=30):
    params = {"days": days}
    response = requests.get(f"{API_BASE}/analytics/trends", params=params)
    trends = response.json()
    
    print(f"""
📈 TREND ANALİZ RAPORU ({days} gün)
═══════════════════════════════════
Toplam Alarm: {trends['total_alarms']:,}
Günlük Ortalama: {trends['daily_average']:.1f}
Trend Yönü: {'📈 Artış' if trends['trend_direction'] > 0 else '📉 Azalış'}
Değişim Oranı: {trends['change_percentage']:+.1f}%

📊 ÖNEMLİ SEVİYE DAĞILIMI:
""")
    
    for severity, count in trends['severity_distribution'].items():
        percentage = (count / trends['total_alarms']) * 100
        bar = '█' * int(percentage / 5)
        print(f"{severity.ljust(8)}: {bar} {count:,} ({percentage:.1f}%)")

# Kullanım örneği
if __name__ == "__main__":
    # 1. Yeni kural oluştur
    rule_id = create_ai_rule()
    
    # 2. Alarmları listele
    recent_alarms = get_alarms({
        "severity": "critical",
        "status": "open",
        "limit": 10
    })
    
    # 3. İlk alarmın detayını getir
    if recent_alarms:
        get_alarm_details(recent_alarms[0]['id'])
    
    # 4. Sistem sağlığını kontrol et
    get_system_health()
    
    # 5. Trend analizi yap
    get_trend_analysis(30)
```

---

## Sonuç ve Best Practices

### Başarılı AI/ML Kural Oluşturma İpuçları

1. **Veri Kalitesi**: Temiz, tutarlı ve anlamlı veri kullanın
2. **Parametre Ayarları**: Başlangıçta düşük hassasiyet, sonra artırın
3. **Test ve Doğrulama**: Kuralları canlıya almadan önce test edin
4. **Sürekli İzleme**: Model performansını düzenli kontrol edin
5. **Geri Bildirim**: False positive/negative'leri sisteme bildirin

### Yaygın Hatalar ve Çözümleri

- **Yüksek False Positive**: Hassasiyeti düşürün, eşik değerlerini artırın
- **Düşük Tespit Oranı**: Veri özelliklerini artırın, algoritma değiştirin
- **Yavaş İşlem**: Batch size'ı artırın, feature selection yapın
- **Model Degradation**: Düzenli retraining planlayın

### Destek ve Yardım

Bu örnekler AuditAI sisteminin temel kullanımını kapsar. Daha detaylı bilgi ve özel durumlar için sistem dokümantasyonunu inceleyin veya teknik destek ekibi ile iletişime geçin.

---

*Son güncelleme: Ocak 2025 - AuditAI v2.0*