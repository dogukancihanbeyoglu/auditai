# AuditAI Yapay Zeka ve Makine Öğrenmesi Teknik Kullanım Kılavuzu

## İçindekiler
1. [Sistem Genel Bakış](#sistem-genel-bakış)
2. [AI/ML Motor Mimarisi](#aiml-motor-mimarisi)
3. [Anomali Tespit Algoritmaları](#anomali-tespit-algoritmaları)
4. [Dolandırıcılık Tespit Sistemi](#dolandırıcılık-tespit-sistemi)
5. [Güvenlik Tehdit Analizi](#güvenlik-tehdit-analizi)
6. [Zaman Serisi Analizi](#zaman-serisi-analizi)
7. [Kural Oluşturma ve Yönetimi](#kural-oluşturma-ve-yönetimi)
8. [Performans İzleme](#performans-İzleme)
9. [Pratik Örnekler](#pratik-örnekler)
10. [Sorun Giderme](#sorun-giderme)

---

## Sistem Genel Bakış

AuditAI, gerçek zamanlı veri analizi için 7 farklı makine öğrenmesi algoritması kullanan entegre bir yapay zeka sistemidir. Sistem, 1390+ satır kod ile tamamen gömülü olarak çalışır ve dış bağımlılık gerektirmez.

### Temel Özellikler
- **Gerçek Zamanlı Analiz**: 5 dakika içinde otomatik anomali tespiti
- **Çok Algoritmalı Yaklaşım**: 7 farklı ML algoritması
- **Otomatik Öğrenme**: Sürekli model güncelleme
- **Türkçe Arayüz**: Yönetici dostu açıklamalar
- **Yüksek Performans**: 100,000+ kayıt analiz kapasitesi

---

## AI/ML Motor Mimarisi

### Ana Bileşenler

#### 1. AI Rule Engine (`services/ai_rule_engine.py`)
```python
# Temel yapı
class AIRuleEngine:
    - anomaly_detection()      # Isolation Forest + Autoencoder
    - fraud_detection()        # Random Forest + Pattern Analysis  
    - security_analysis()      # Behavioral Analysis
    - time_series_analysis()   # Prophet + ARIMA
    - statistical_analysis()   # Statistical Methods
```

#### 2. Data Processor (`services/data_processor.py`)
- Veri ön işleme ve temizlik
- Feature engineering
- Normalizasyon ve ölçeklendirme
- Eksik veri yönetimi

#### 3. Scheduler (`services/scheduler.py`)
- Otomatik model eğitimi
- Periyodik analiz çalıştırma
- Performans metrik güncelleme

---

## Anomali Tespit Algoritmaları

### 1. Isolation Forest

**Kullanım Alanı**: Finansal işlem anomalileri, yüksek tutarlı işlemler

**Algoritma Özellikleri**:
- Ensemble method
- Outlier detection için optimize edilmiş
- Yüksek boyutlu veriler için uygun

**Parametre Ayarları**:
```python
isolation_forest_params = {
    'n_estimators': 100,        # Ağaç sayısı
    'contamination': 'auto',    # Anomali oranı
    'random_state': 42,         # Tekrarlanabilirlik
    'max_samples': 'auto'       # Örneklem boyutu
}
```

**Örnek Kullanım**:
```sql
-- Yüksek tutarlı işlem anomalisi kuralı
INSERT INTO audit_rules (
    name, rule_type, algorithm, 
    sensitivity, confidence_threshold
) VALUES (
    'Yüksek Tutarlı İşlem Tespiti',
    'anomaly_detection',
    'isolation_forest',
    0.8,  -- Yüksek hassasiyet
    0.85  -- %85 güven eşiği
);
```

### 2. Autoencoder Neural Network

**Kullanım Alanı**: Karmaşık veri desenlerinde anomali tespiti

**Algoritma Özellikleri**:
- Deep learning yaklaşımı
- Reconstruction error analizi
- Çok boyutlu anomali tespiti

**Ağ Mimarisi**:
```python
# Encoder-Decoder yapısı
input_layer -> [64] -> [32] -> [16] -> [32] -> [64] -> output_layer

# Aktivasyon fonksiyonları
hidden_layers: ReLU
output_layer: Linear
loss_function: Mean Squared Error
```

**Parametre Ayarları**:
```python
autoencoder_params = {
    'epochs': 100,
    'batch_size': 32,
    'learning_rate': 0.001,
    'threshold_percentile': 95  # Anomali eşiği
}
```

---

## Dolandırıcılık Tespit Sistemi

### Random Forest Classifier

**Özellik Mühendisliği**:
```python
features = [
    'transaction_amount',      # İşlem tutarı
    'hour_of_day',            # Gün içi saat
    'day_of_week',            # Haftanın günü
    'merchant_risk_score',    # Satıcı risk skoru
    'user_behavior_score',    # Kullanıcı davranış skoru
    'location_risk',          # Lokasyon riski
    'transaction_frequency'   # İşlem sıklığı
]
```

**Model Eğitimi**:
```python
rf_params = {
    'n_estimators': 200,      # Ağaç sayısı
    'max_depth': 10,          # Maksimum derinlik
    'min_samples_split': 5,   # Minimum bölme örneklem
    'min_samples_leaf': 2,    # Minimum yaprak örneklem
    'class_weight': 'balanced' # Sınıf dengeleme
}
```

### Kullanım Örneği

**1. Tedarikçi Dolandırıcılık Kuralı**:
```python
# Web arayüzünden kural oluşturma
Kural Adı: "Şüpheli Tedarikçi Analizi"
Kural Türü: Dolandırıcılık Tespiti
Algoritma: Random Forest
Hassasiyet: 0.9 (Çok Yüksek)
Güven Eşiği: 0.8

# Kontrol edilecek alanlar:
- Tedarikçi geçmişi
- Fiyat karşılaştırması  
- Ödeme desenleri
- Fatura düzenliliği
```

**2. Otomatik Alarm Üretimi**:
```json
{
    "alarm_type": "fraud_detection",
    "title": "Tedarikçi Dolandırıcılığı Tespit Edildi",
    "message": "ABC Tedarik Ltd. şirketi olağandışı yüksek fiyat teklifi verdi",
    "severity": "critical",
    "risk_score": 0.92,
    "evidence": {
        "price_deviation": "450% ortalamanın üstü",
        "vendor_history": "3 aylık geçmiş",
        "similar_cases": 5
    }
}
```

---

## Güvenlik Tehdit Analizi

### Behavioral Pattern Analysis

**Analiz Edilen Davranışlar**:
```python
security_features = {
    'login_frequency': 'Giriş sıklığı',
    'failed_attempts': 'Başarısız deneme sayısı', 
    'ip_reputation': 'IP itibar skoru',
    'geo_location': 'Coğrafi konum',
    'user_agent': 'Tarayıcı/Cihaz bilgisi',
    'session_duration': 'Oturum süresi',
    'accessed_resources': 'Erişilen kaynaklar'
}
```

### Tehdit Kategorileri

**1. Brute Force Saldırıları**:
```python
# Algılama kriterleri
brute_force_detection = {
    'failed_attempts_threshold': 10,    # 10+ başarısız deneme
    'time_window': 300,                 # 5 dakika içinde
    'ip_based_tracking': True,          # IP bazlı takip
    'progressive_delay': True           # Artan gecikme
}
```

**2. SQL Injection Tespiti**:
```python
# Pattern matching
sql_injection_patterns = [
    r"union\s+select",
    r"or\s+1\s*=\s*1",
    r"drop\s+table",
    r"exec\s*\(\s*",
    r"script\s*>",
    r"<\s*iframe"
]
```

**Örnek Güvenlik Kuralı**:
```sql
INSERT INTO audit_rules (
    name, rule_type, algorithm,
    conditions, alert_threshold
) VALUES (
    'Şüpheli IP Aktivitesi',
    'security',
    'pattern_matching',
    '{"ip_attempts": ">50", "success_rate": "<0.1"}',
    'immediate'
);
```

---

## Zaman Serisi Analizi

### Prophet Algoritması

**Kullanım Alanları**:
- Satış trend analizi
- Sistem kaynak kullanımı
- Kullanıcı aktivite desenleri
- Finansal metrik tahminleri

**Model Parametreleri**:
```python
prophet_params = {
    'yearly_seasonality': True,     # Yıllık mevsimsellik
    'weekly_seasonality': True,     # Haftalık mevsimsellik
    'daily_seasonality': False,     # Günlük mevsimsellik (devre dışı)
    'changepoint_prior_scale': 0.05, # Trend değişim hassasiyeti
    'seasonality_prior_scale': 10    # Mevsimsellik hassasiyeti
}
```

**Örnek Kullanım**:
```python
# Satış trendi analizi
trend_rule = {
    'name': 'Satış Trend Anomalisi',
    'rule_type': 'time_series',
    'algorithm': 'prophet',
    'data_column': 'daily_sales',
    'forecast_period': 30,  # 30 gün tahmin
    'anomaly_threshold': 2.0  # 2 standart sapma
}
```

### ARIMA Modeli

**Auto ARIMA Kullanımı**:
```python
# Otomatik parametre seçimi
arima_config = {
    'seasonal': True,           # Mevsimsel model
    'stepwise': True,          # Hızlı parametre tarama
    'suppress_warnings': True,  # Uyarıları gizle
    'error_action': 'ignore',  # Hata durumunda devam et
    'max_order': 5             # Maksimum model karmaşıklığı
}
```

---

## Kural Oluşturma ve Yönetimi

### Web Arayüzü Kullanımı

**1. Kural Oluşturma Süreci**:
```
Audit Areas → Rules → Create New Rule
│
├── Basic Information
│   ├── Rule Name: "Yüksek Tutarlı İşlem Analizi"
│   ├── Description: "100.000 TL üzeri işlemleri analiz eder"
│   └── Rule Type: "Anomaly Detection"
│
├── Algorithm Selection
│   ├── Primary: "Isolation Forest"
│   ├── Sensitivity: 0.8 (High)
│   └── Confidence: 0.85 (85%)
│
├── Data Configuration
│   ├── Data Source: "Financial Transactions"
│   ├── Target Column: "amount"
│   └── Filter Conditions: "amount > 10000"
│
└── Alert Settings
    ├── Severity: "High"
    ├── Notification: "Immediate"
    └── Auto-Action: "Create Alarm"
```

**2. Gelişmiş Kural Yapılandırması**:
```json
{
    "rule_id": "RULE_001",
    "ai_config": {
        "algorithm": "isolation_forest",
        "hyperparameters": {
            "n_estimators": 100,
            "contamination": 0.1,
            "max_samples": 256
        },
        "feature_engineering": {
            "normalize": true,
            "handle_missing": "median",
            "encoding": "label"
        },
        "retraining": {
            "frequency": "weekly",
            "trigger_threshold": 0.1,
            "validation_split": 0.2
        }
    }
}
```

### API Kullanımı

**Kural Oluşturma API**:
```python
import requests

# Yeni AI kuralı oluştur
rule_data = {
    "name": "ML Fraud Detection",
    "rule_type": "fraud_detection", 
    "algorithm": "random_forest",
    "sensitivity": 0.9,
    "confidence_threshold": 0.8,
    "conditions": {
        "amount": {"operator": ">", "value": 50000},
        "time_filter": {"operator": "outside_hours", "value": "09:00-17:00"}
    }
}

response = requests.post('/api/rules', json=rule_data)
```

**Kural Performans Sorgulama**:
```python
# Kural performansını sorgula
rule_id = "RULE_001"
performance = requests.get(f'/api/rules/{rule_id}/performance')

print(f"Accuracy: {performance.json()['accuracy']}")
print(f"Precision: {performance.json()['precision']}")  
print(f"Recall: {performance.json()['recall']}")
print(f"F1-Score: {performance.json()['f1_score']}")
```

---

## Performans İzleme

### Model Metrikleri

**1. Anomali Tespit Metrikleri**:
```python
anomaly_metrics = {
    'true_positives': 156,      # Doğru pozitif
    'false_positives': 23,      # Yanlış pozitif  
    'true_negatives': 2847,     # Doğru negatif
    'false_negatives': 12,      # Yanlış negatif
    'precision': 0.871,         # Kesinlik
    'recall': 0.929,            # Duyarlılık
    'f1_score': 0.899,          # F1 Skoru
    'auc_roc': 0.945            # ROC AUC
}
```

**2. Model Drift Tespiti**:
```python
# Veri kayması kontrolü
drift_detection = {
    'statistical_tests': [
        ('kolmogorov_smirnov', 0.05),
        ('chi_square', 0.01),
        ('population_stability_index', 0.1)
    ],
    'performance_degradation': {
        'accuracy_threshold': 0.1,    # %10 düşüş
        'alert_frequency': 'daily'
    }
}
```

### Dashboard Görünümü

**Admin Reports Erişimi**:
```
http://localhost:5000/admin/reports

├── System Performance Overview
│   ├── Total Rules: 11
│   ├── Active Algorithms: 7
│   ├── Daily Processed Records: 15,432
│   └── Alert Generation Rate: 2.3%
│
├── Algorithm Performance
│   ├── Isolation Forest: 94.5% accuracy
│   ├── Random Forest: 91.2% accuracy
│   ├── Prophet: 89.7% MAPE
│   └── Autoencoder: 96.1% reconstruction accuracy
│
└── Model Health Status
    ├── Last Retrain: 2 days ago
    ├── Data Quality Score: 98.2%
    ├── Feature Stability: Good
    └── Prediction Latency: 150ms avg
```

---

## Pratik Örnekler

### Örnek 1: Finansal Anomali Tespiti

**Senaryo**: Hafta sonu yüksek tutarlı işlem tespiti

```python
# 1. Kural Tanımı
financial_anomaly_rule = {
    "name": "Hafta Sonu Yüksek Tutar Anomalisi",
    "rule_type": "anomaly_detection",
    "algorithm": "isolation_forest",
    "data_source": "financial_transactions",
    "features": ["amount", "hour", "day_of_week", "merchant_type"],
    "sensitivity": 0.85,
    "confidence_threshold": 0.8
}

# 2. Beklenen Çıktı
expected_alerts = [
    {
        "title": "Yüksek Tutarlı Hafta Sonu İşlemi",
        "message": "Cumartesi günü 850,000 TL transfer işlemi",
        "severity": "critical",
        "risk_score": 0.92,
        "timestamp": "2025-01-26 14:30:00"
    }
]
```

### Örnek 2: İK Fazla Mesai Anomalisi

**Senaryo**: Çalışan fazla mesai pattern analizi

```python
# Web arayüzünden kural oluşturma adımları:
"""
1. Rules → Create New Rule
2. Rule Name: "Fazla Mesai Anomali Tespiti"
3. Rule Type: "Anomaly Detection" 
4. Algorithm: "Statistical Anomaly"
5. Data Source: "HR Data"
6. Target Metrics:
   - overtime_hours
   - performance_score  
   - department_average
7. Sensitivity: 0.7 (High)
8. Alert Threshold: "Immediate"
"""

# Otomatik üretilen alarm örneği:
hr_alarm_example = {
    "title": "Fazla Mesai Anomalisi: Ahmet Yılmaz",
    "message": "315 saat fazla mesai (ortalama: 45 saat) - %600 artış",
    "severity": "high", 
    "department": "Muhasebe",
    "recommendation": "Çalışan iş yükü kontrolü önerilir"
}
```

### Örnek 3: Güvenlik Tehdit Analizi

**Senaryo**: Brute force saldırı tespiti

```python
# Güvenlik kuralı konfigürasyon
security_rule_config = {
    "name": "Brute Force Saldırı Tespiti",
    "rule_type": "security",
    "algorithm": "pattern_matching",
    "detection_window": 300,  # 5 dakika
    "thresholds": {
        "failed_attempts": 15,
        "unique_usernames": 5, 
        "success_rate": 0.1
    },
    "auto_actions": ["block_ip", "create_alarm", "notify_admin"]
}

# Real-time alarm örneği:
security_alarm = {
    "title": "Brute Force Saldırısı Tespit Edildi",
    "message": "IP 192.168.1.200: 47 başarısız giriş, 12 farklı kullanıcı",
    "severity": "critical",
    "source_ip": "192.168.1.200",
    "attack_duration": "8 dakika",
    "blocked_status": "Otomatik engellendi"
}
```

### Örnek 4: Zaman Serisi Trend Analizi

**Senaryo**: Satış trend anomalisi

```python
# Prophet modeli konfigürasyonu
sales_trend_config = {
    "name": "Günlük Satış Trend Analizi", 
    "rule_type": "time_series",
    "algorithm": "prophet",
    "data_frequency": "daily",
    "forecast_horizon": 30,
    "seasonal_components": {
        "yearly": True,
        "weekly": True, 
        "daily": False
    },
    "anomaly_detection": {
        "method": "confidence_interval",
        "confidence_level": 0.95,
        "threshold": 2.0  # 2 std deviations
    }
}

# Trend anomali alarm örneği:
trend_alarm = {
    "title": "Satış Trend Anomalisi",
    "message": "Günlük satış %45 beklenen değerin altında (Beklenen: 125K TL, Gerçek: 68K TL)",
    "severity": "medium",
    "trend_direction": "downward",
    "deviation_percentage": -45.6,
    "forecast_next_week": "Düşüş trendi devam edebilir"
}
```

---

## Sorun Giderme

### Yaygın Problemler ve Çözümleri

**1. Model Performans Düşüklüğü**
```python
# Problem: Accuracy %80'in altına düştü
# Çözüm:
def retrain_model(rule_id):
    """Model yeniden eğitimi"""
    rule = AuditRule.query.get(rule_id)
    
    # Yeni veri ile eğitim
    fresh_data = get_latest_training_data(days=90)
    model = train_model(rule.algorithm, fresh_data)
    
    # Performans testi
    test_accuracy = evaluate_model(model, test_data)
    
    if test_accuracy > 0.85:
        save_model(rule_id, model)
        return "Model başarıyla güncellendi"
    else:
        return "Model performansı yetersiz, hyperparameter tuning gerekli"
```

**2. Yüksek False Positive Oranı**
```python
# Problem: Çok fazla yanlış alarm
# Çözüm: Sensitivity ayarı
def adjust_sensitivity(rule_id, target_precision=0.9):
    """Hassasiyet otomatik ayarlama"""
    rule = AuditRule.query.get(rule_id)
    
    # Son 30 gün alarm verileri
    recent_alarms = get_alarm_history(rule_id, days=30)
    
    # Precision hesaplama
    current_precision = calculate_precision(recent_alarms)
    
    if current_precision < target_precision:
        # Sensitivity düşür (daha az hassas)
        new_sensitivity = rule.sensitivity * 0.9
        rule.sensitivity = max(0.3, new_sensitivity)
        db.session.commit()
        
        return f"Sensitivity {new_sensitivity:.2f} olarak güncellendi"
```

**3. Sistem Performans Optimizasyonu**
```python
# Problem: Yavaş analiz süreleri
# Çözüm: Batch processing ve caching

class PerformanceOptimizer:
    def __init__(self):
        self.batch_size = 1000
        self.cache_ttl = 3600  # 1 saat
    
    def optimize_analysis(self, data):
        """Analiz sürecini optimize et"""
        # Batch işleme
        results = []
        for batch in self.chunk_data(data, self.batch_size):
            batch_result = self.process_batch(batch)
            results.extend(batch_result)
        
        # Cache sonuçları
        self.cache_results(results)
        return results
    
    def process_batch(self, batch):
        """Batch veri işleme"""
        # Paralel işleme
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self.analyze_record, record) 
                      for record in batch]
            return [f.result() for f in futures]
```

### Debug ve Monitoring

**1. Log Analizi**
```bash
# AI/ML engine logları
tail -f logs/ai_engine.log | grep "ERROR\|WARNING"

# Model performance logları  
grep "accuracy\|precision\|recall" logs/model_performance.log

# System resource monitoring
htop -p `pgrep -f "python.*ai_rule_engine"`
```

**2. Database Query Optimization**
```sql
-- Slow query analizi
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE query LIKE '%alarms%' 
ORDER BY mean_time DESC;

-- Index optimizasyonu
CREATE INDEX CONCURRENTLY idx_alarms_created_severity 
ON alarms(created_at, severity) 
WHERE status = 'open';
```

**3. Memory Usage Monitoring**
```python
import psutil
import gc

def monitor_memory_usage():
    """Memory kullanım takibi"""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    print(f"RSS Memory: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS Memory: {memory_info.vms / 1024 / 1024:.2f} MB")
    
    # Garbage collection
    collected = gc.collect()
    print(f"GC collected {collected} objects")
```

---

## Güvenlik ve Compliance

### Veri Güvenliği
- Model parametreleri şifrelenmiş saklama
- GDPR uyumlu veri işleme
- Audit log kayıtları
- Role-based access control

### Model Governance
- Model versiyonlama
- A/B testing capability
- Rollback mechanisms
- Performance monitoring alerts

---

## Sonuç

AuditAI AI/ML sistemi, 7 farklı algoritma ile kapsamlı veri analizi sunar. Sistem otomatik öğrenme, gerçek zamanlı tespit ve yüksek performans özellikleri ile kurumsal denetim süreçlerini otomatikleştirir.

### İletişim ve Destek
- Teknik destek için sistem yöneticisine başvurun
- Yeni algoritma istekleri için geliştirme takımı ile iletişime geçin
- Performans optimizasyonu için sistem metriklerini düzenli takip edin

---

*Bu kılavuz AuditAI v2.0 için hazırlanmıştır. Son güncelleme: Ocak 2025*