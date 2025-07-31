# Yeni Veritabanı Bağlama ve Test Verisi Temizleme Senaryosu

## Test Verilerini Temizlediğinizde Ne Olur?

### 1. Başlangıç Durumu (Şu anda):
- ✅ Audit Areas: 6 adet
- ✅ Rules: 11 adet 
- ✅ Data Sources: 7 adet
- ❌ Alarms: 0 adet (TEMİZLENDİ)

### 2. Sistem Nasıl Davranır?

#### A) Scheduler Çalışmaya Devam Eder:
```
Her 5 dakikada:  Aktif kuralları kontrol eder
Her 10 dakikada: Sistem performansını izler
Her gün:         Veri kalitesi kontrolleri
Her hafta:       Sistem temizliği
```

#### B) Kurallar Çalışır Ama Alarm Üretmez:
- Aktif 11 kural çalışmaya devam eder
- Veri yok olduğu için anomali tespit edemez
- AI/ML algoritmaları boş sonuç döner
- Sadece sistem izleme alarmları üretilir

#### C) Sistem İzleme Alarmları Devam Eder:
- CPU kullanımı > %80
- Bellek kullanımı > %85  
- Disk kullanımı > %90
- Genel sistem yükü > %75

## Yeni Veritabanı Bağladığınızda Ne Olur?

### 1. Yeni Veri Kaynağı Oluşturma:
```python
# Örnek yeni veritabanı
new_source = DataSource(
    name='Şirket ERP Sistemi',
    source_type='database',
    connection_string='postgresql://erp.company.com:5432/main_db'
)
```

### 2. Bağlantı Testi:
- Sistem otomatik bağlantı testi yapar
- PostgreSQL/MySQL/SQLite desteklenir
- Hata durumunda `sync_status='error'` olur

### 3. Veri Senkronizasyonu:
- **Her 5 dakikada** scheduler veri çeker
- Başarılı ise `sync_status='success'`
- `last_sync` zamanı güncellenir

### 4. Kural Çalıştırma:
```python
# Yeni kural oluşturduğunuzda
new_rule = AuditRule(
    name='Yüksek Tutarlı İşlemler',
    condition='amount > 100000',
    rule_type='threshold'
)
```

### 5. AI/ML Motoru Devreye Girer:
- Gerçek verilerinizi analiz eder
- Anomali tespit algoritmaları çalışır
- Risk skorlarına göre alarmlar üretir

## Sistemin Davranış Döngüsü:

### 1. Veri Yok Durumu (Şu anda):
```
Scheduler → Kuralları çek → Veri yok → Alarm yok
```

### 2. Yeni Veri Geldiğinde:
```
Scheduler → Kuralları çek → Veritabanından veri al → AI analizi → Gerçek alarmlar!
```

## Örnek Yeni Veritabanı Senaryosu:

### Adım 1: Veri Kaynağı Ekle
- ERP sisteminizi bağlayın
- Finansal işlem tablosunu seçin

### Adım 2: Kural Oluşturun
```
Kural Adı: "Büyük İşlem Kontrolü"
Tür: anomaly_detection
Algoritma: isolation_forest
Koşul: amount > 50000
```

### Adım 3: 5 Dakika Bekleyin
- Scheduler otomatik çalışır
- ERP'den veri çeker
- AI algoritması analiz eder

### Adım 4: Gerçek Alarmlar Üretilir
```
Başlık: "Anomali Tespit Edildi: Büyük İşlem Kontrolü"
Mesaj: "Güven seviyesi: %87, Anomali skoru: 0.923"
Severity: high (risk skoruna göre)
Data: {gerçek_işlem_detayları}
```

## Önemli Notlar:

### ✅ Çalışmaya Devam Edenler:
- Scheduler sistemleri
- Sistem izleme alarmları
- Mevcut kurallar (veri geldiğinde çalışır)
- AI/ML motorları

### ❌ Durmuş Olanlar:
- Veri tabanlı alarmlar (veri yok)
- Anomali tespitleri (analiz edilecek veri yok)
- Test alarm mesajları

### 🔄 Yeniden Başlayanlar:
- Gerçek veri geldiğinde tüm AI/ML algoritmaları
- Risk skorlaması sistemi
- Otomatik alarm üretimi

**Sonuç:** Sistem temiz durumda çalışır, yeni verinizi beklemeye geçer. Veri geldiğinde otomatik olarak gerçek analizler yapmaya başlar!