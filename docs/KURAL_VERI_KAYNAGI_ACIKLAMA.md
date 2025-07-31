# Kuralların Veri Kaynağını Belirleme Sistemi

## 🔍 Mevcut Durum Analizi

### Şu Anki Mantık:
1. **Hiyerarşik Yapı**: Kural → Audit Area → Veri Kaynakları
2. **Otomatik Seçim**: Kural, bulunduğu audit area'nın TÜM veri kaynaklarını kullanır
3. **Sınırlama**: Spesifik veri kaynağı seçimi mümkün değil

### Örnek Durum:
```
Finans ve Muhasebe Audit Alanı:
├── SAP Finans Modülü (Veritabanı)
├── Banka API (Harici API)
└── Excel Raporları (Dosya)

Kurallar:
├── "Yüksek Tutarlı İşlemler" → 3 veri kaynağından da arar
├── "Şüpheli Transferler" → 3 veri kaynağından da arar
└── "Bütçe Aşımları" → 3 veri kaynağından da arar
```

## 🚀 Geliştirilmiş Sistem

### Yeni Özellikler:

#### 1. **Ana Veri Kaynağı Seçimi**
- Her kural için **primary_data_source_id** alanı eklendi
- Kural oluştururken spesifik veri kaynağı seçilebilir
- Boş bırakılırsa tüm veri kaynaklarını kullanır (eski davranış)

#### 2. **Akıllı Kural Oluşturma**
```
Yeni Kural Formu:
┌─────────────────────────────────┐
│ Kural Adı: [_______________]    │
│ Audit Alanı: [Finans ▼]        │
│ Ana Veri Kaynağı: [SAP ▼]      │  ← YENİ!
│ Kural Türü: [Anomali ▼]        │
└─────────────────────────────────┘
```

#### 3. **Dinamik Veri Kaynağı Seçimi**
- Audit area seçildikten sonra o alanın veri kaynakları yüklenir
- JavaScript ile dinamik form güncellemesi
- "Tüm Veri Kaynakları" seçeneği de mevcut

## 💡 Kullanım Senaryoları

### Senaryo 1: Spesifik Kaynak
```
Kural: "Banka Hesap Anomalisi"
Ana Veri Kaynağı: "Banka API"
Sonuç: Sadece banka verilerini kontrol eder
```

### Senaryo 2: Çoklu Kaynak
```
Kural: "Genel Mali Kontrol"
Ana Veri Kaynağı: "Tüm Kaynaklar"
Sonuç: SAP + Banka + Excel dosyalarını kontrol eder
```

### Senaryo 3: Dosya Bazlı
```
Kural: "Excel Rapor Kontrolü"
Ana Veri Kaynağı: "Excel Raporları"
Sonuç: Sadece Excel dosyalarını analiz eder
```

## 🔧 Teknik Implementasyon

### Model Değişiklikleri:
```sql
ALTER TABLE audit_rules ADD COLUMN primary_data_source_id INTEGER;
ALTER TABLE audit_rules ADD FOREIGN KEY (primary_data_source_id) 
    REFERENCES data_sources(id);
```

### Form Geliştirmeleri:
- Cascade dropdown: Audit Area → Veri Kaynakları
- AJAX ile dinamik yükleme
- Kullanıcı dostu interface

### Backend Logic:
```python
def get_rule_data_sources(rule):
    if rule.primary_data_source_id:
        return [rule.primary_data_source]
    else:
        return rule.audit_area.data_sources.all()
```

## 🔄 Çoklu Veri Kaynağı Desteği 

### Çoklu Veri Kaynağı Desteği Tamamlandı! ✅

#### Yeni Özellikler:
- **Çoklu Seçim**: Artık bir kural için birden fazla veri kaynağı seçilebilir
- **Öncelik Sistemi**: Seçilen veri kaynakları öncelik sırasına göre işlenir
- **AI/ML Uyumluluğu**: Algoritmaların her veri kaynağı tipiyle uyumlu çalışması sağlandı
- **Akıllı Preprocessing**: Her veri kaynağı için algoritma tipine göre özel veri işleme

#### Algoritma Uyumluluğu:

##### Isolation Forest & Autoencoder:
- Numerik veriler otomatik normalize edilir
- Farklı veri kaynaklarından gelen numerik alanlar birleştirilir
- Z-score normalizasyonu ile outlier detection optimize edilir

##### Random Forest & Gradient Boosting:
- Kategorik veriler otomatik encode edilir
- String değerler label encoding ile sayısal hale getirilir
- Mixed data types desteklenir

##### Time Series (ARIMA, Prophet):
- Zaman damgası olan veriler otomatik sıralanır
- Farklı kaynaklardan gelen tarihli veriler birleştirilir
- Trend ve sezonalite analizi çoklu kaynak üzerinde yapılır

##### Statistical Analysis:
- Z-score ve IQR methodları çoklu veri için optimize edildi
- Cross-source anomaly detection
- Kaynak bazlı statistical profiling

#### Teknik Implementasyon:

```python
# AI Rule Engine'de çoklu veri kaynağı desteği
def get_rule_data_sources(self, rule: AuditRule) -> List[DataSource]:
    # Öncelik sırasında çoklu kaynaklar
    multi_sources = RuleDataSource.query.filter_by(
        rule_id=rule.id, is_active=True
    ).order_by(RuleDataSource.priority).all()
    
    if multi_sources:
        return [rds.data_source for rds in multi_sources]
    # Legacy support...

# Her algoritma için özel preprocessing
def _preprocess_source_data(self, source, rule):
    if rule.algorithm in ['isolation_forest', 'autoencoder']:
        return self._normalize_numeric_data(raw_data)
    elif rule.algorithm in ['random_forest', 'gradient_boosting']:
        return self._encode_categorical_data(raw_data)
    # ...
```

#### Database Schema:
```sql
-- Çoklu veri kaynağı junction table
CREATE TABLE rule_data_sources (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES audit_rules(id),
    data_source_id INTEGER REFERENCES data_sources(id),
    priority INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Kullanım Senaryoları:

##### Senaryo 1: Finans + HR Entegrasyonu
```
Kural: "Departman Bazlı Harcama Anomalisi"
Veri Kaynakları: 
  1. SAP Finansal (Priority 1)
  2. HR Management System (Priority 2)
Algoritma: Random Forest
Sonuç: Çalışan sayısı vs harcama korelasyonu analizi
```

##### Senaryo 2: Çoklu Database Fraud Detection
```
Kural: "Çapraz Sistem Dolandırıcılık Tespiti"
Veri Kaynakları:
  1. Ana Transaction DB (Priority 1)
  2. User Behavior Analytics (Priority 2) 
  3. Payment Gateway Logs (Priority 3)
Algoritma: Isolation Forest
Sonuç: Cross-platform fraud pattern detection
```

##### Senaryo 3: Time Series Multi-Source
```
Kural: "Satış Trend Anomalisi"
Veri Kaynakları:
  1. Sales Database (Priority 1)
  2. Marketing Campaign Data (Priority 2)
  3. External Market Data API (Priority 3)
Algoritma: Prophet
Sonuç: Multi-factor time series forecasting
```

#### Performans Optimizasyonları:
- **Lazy Loading**: Sadece gerekli olan veri kaynakları yüklenir
- **Parallel Processing**: Veri kaynakları paralel olarak işlenir
- **Smart Caching**: Frequently used combinations cached edilir
- **Memory Management**: Large datasets için chunked processing

#### Geriye Uyumluluk:
- Mevcut `primary_data_source_id` alanı korundu
- Eski kurallar çalışmaya devam eder
- Yeni özellik optional olarak devreye alınabilirm veri kaynakları kullanılır

### Gelecek Geliştirmeler:
```sql
-- Çoklu veri kaynağı için junction table
CREATE TABLE rule_data_sources (
    rule_id INTEGER REFERENCES audit_rules(id),
    data_source_id INTEGER REFERENCES data_sources(id),
    priority INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (rule_id, data_source_id)
);
```

### Çoklu Seçim Avantajları:
- **Esnek analiz**: Kural birden fazla kaynağı birleştirebilir
- **Öncelik sistemi**: Veri kaynaklarına öncelik atanabilir  
- **Dinamik seçim**: Farklı koşullarda farklı kaynaklar aktif olabilir

### Örnek Çoklu Kullanım:
```
"Mali Uyumluluk Kuralı":
├── Ana: SAP Finans (Öncelik: 1)
├── Destekleyici: Banka API (Öncelik: 2)  
└── Kontrol: Excel Raporları (Öncelik: 3)
```

## 📈 Faydalar

### Kullanıcı Açısından:
- **Daha hızlı çalışma**: Gereksiz veri kaynakları taranmaz
- **Net sonuçlar**: Spesifik kaynaktan gelen sonuçlar
- **Kolay yönetim**: Hangi kuralın hangi veriyi kullandığı belli
- **Gelecekte çoklu seçim**: Birden fazla kaynak kombinasyonu

### Sistem Açısından:
- **Performans**: Daha az veri işleme
- **Kaynak tasarrufu**: CPU ve bellek optimizasyonu
- **Hata azaltma**: Yanlış veri kaynağından analiz yapılmaz
- **Ölçeklenebilirlik**: Çoklu kaynak desteği için hazır

### Örnek Performans Artışı:
```
Eski Sistem:
"Banka Anomalisi" kuralı → 3 veri kaynağını tara → 15 saniye

Yeni Sistem:
"Banka Anomalisi" kuralı → Sadece Banka API → 3 saniye
```

## 🎯 Sonuç

Bu geliştirme ile:
- ✅ Kurallar artık spesifik veri kaynağı seçebilir
- ✅ Performans önemli ölçüde artar
- ✅ Kullanıcı deneyimi iyileşir
- ✅ Sistem daha esnek hale gelir
- ✅ Geriye uyumluluk korunur (eski kurallar çalışmaya devam eder)

**Kurallara veri kaynağı seçme yeteneği kazandırılmıştır!**