# AuditAI Kapsamlı Kullanıcı Kılavuzu

## İçindekiler
1. [Giriş ve Sistem Genel Bakış](#giriş-ve-sistem-genel-bakış)
2. [İlk Kurulum ve Giriş](#ilk-kurulum-ve-giriş)
3. [Ana Dashboard](#ana-dashboard)
4. [Audit Areas (Denetim Alanları) Yönetimi](#audit-areas-yönetimi)
5. [Data Sources (Veri Kaynakları) Yönetimi](#data-sources-yönetimi)
6. [Rules (Kurallar) Yönetimi](#rules-yönetimi)
7. [Alarms (Alarmlar) Sistemi](#alarms-sistemi)
8. [Admin Panel ve Raporlama](#admin-panel-ve-raporlama)
9. [Kullanıcı Profili ve Ayarları](#kullanıcı-profili-ve-ayarları)
10. [Yapay Zeka ve Makine Öğrenmesi Özellikleri](#yapay-zeka-ve-makine-öğrenmesi-özellikleri)
11. [Pratik Örnekler ve Senaryolar](#pratik-örnekler-ve-senaryolar)
12. [Sorun Giderme](#sorun-giderme)

---

## Giriş ve Sistem Genel Bakış

AuditAI, işletmelerin denetim süreçlerini otomatikleştiren, yapay zeka destekli bir sürekli denetim platformudur. Sistem, çeşitli veri kaynaklarından bilgi toplayarak gerçek zamanlı analiz yapar ve anormallikleri tespit eder.

### Temel Özellikler
- **Gerçek Zamanlı Analiz**: 7/24 sürekli veri analizi
- **Yapay Zeka Destekli**: 7 farklı makine öğrenmesi algoritması
- **Çoklu Veri Kaynağı**: Veritabanı, dosya ve API entegrasyonu
- **Otomatik Alarm Sistemi**: Anında uyarı ve bildirimler
- **Kapsamlı Raporlama**: Detaylı analiz ve görselleştirme
- **Türkçe Arayüz**: Tam Türkçe dil desteği

### Sistem Mimarisi
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Veri Kaynakları  │ -> │  AuditAI Platform  │ -> │   Alarmlar ve    │
│                 │    │                  │    │    Raporlar     │
│ • Veritabanları │    │ • AI/ML Motor    │    │ • Gerçek Zamanlı │
│ • CSV/Excel     │    │ • Kural Motoru   │    │ • E-posta        │
│ • API'ler       │    │ • Scheduler      │    │ • Dashboard      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## İlk Kurulum ve Giriş

### Sisteme İlk Erişim

**1. Web Tarayıcısı ile Erişim**
```
Adres: http://localhost:5000
Varsayılan Admin: admin / admin123
```

**2. İlk Giriş Adımları**
```
1. Tarayıcınızda http://localhost:5000 adresine gidin
2. "Giriş Yap" butonuna tıklayın
3. Kullanıcı adı: admin
4. Şifre: admin123
5. "Giriş" butonuna tıklayın
```

### Yeni Kullanıcı Kaydı

**Kayıt Olma Süreci:**
```
1. Ana sayfada "Kayıt Ol" linkine tıklayın
2. Gerekli bilgileri doldurun:
   - Kullanıcı Adı (benzersiz olmalı)
   - E-posta Adresi
   - Şifre (minimum 8 karakter)
   - Şifre Tekrarı
3. "Kayıt Ol" butonuna tıklayın
4. Sistem otomatik olarak giriş yapacak
```

**Örnek Kayıt Formu:**
```
Kullanıcı Adı: mehmet.yilmaz
E-posta: mehmet@firma.com
Şifre: GuvenlıSıfre123
Şifre Tekrarı: GuvenlıSıfre123
```

---

## Ana Dashboard

### Dashboard Genel Görünüm

Ana dashboard, sistemin merkezi kontrol paneli olarak çalışır ve tüm kritik bilgileri tek bakışta sunar.

**Dashboard Bileşenleri:**
```
┌─────────────────────────────────────────────────────────────┐
│                    AuditAI Dashboard                        │
├─────────────────────────────────────────────────────────────┤
│ 📊 Özet Kartlar                                            │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│ │ Toplam Alan │ │ Aktif Kural │ │ Açık Alarm  │ │ Veri    │ │
│ │     12      │ │     45      │ │     8       │ │ Kaynağı │ │
│ │             │ │             │ │             │ │   23    │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
├─────────────────────────────────────────────────────────────┤
│ 🚨 Son Alarmlar                                            │
│ • Yüksek Tutarlı İşlem (Kritik) - 2 dakika önce           │
│ • Güvenlik Tehdidi (Yüksek) - 15 dakika önce              │
│ • Fazla Mesai Anomalisi (Orta) - 1 saat önce              │
├─────────────────────────────────────────────────────────────┤
│ 📈 Sistem Performansı                                      │
│ CPU: ██████░░░░ 60%  Memory: ████████░░ 80%               │
│ Günlük İşlem: 15,432  Ortalama Yanıt: 150ms               │
└─────────────────────────────────────────────────────────────┘
```

### Dashboard Özet Kartları

**1. Toplam Audit Area Kartı**
- **Gösterilen Bilgi**: Tanımlı denetim alanı sayısı
- **Tıklama Eylemi**: Audit Areas sayfasına yönlendirir
- **Örnek Görünüm**: "12 Denetim Alanı"

**2. Aktif Rules Kartı**
- **Gösterilen Bilgi**: Çalışan kural sayısı
- **Tıklama Eylemi**: Rules sayfasına yönlendirir
- **Örnek Görünüm**: "45 Aktif Kural"

**3. Open Alarms Kartı**
- **Gösterilen Bilgi**: Açık alarm sayısı
- **Renk Kodlaması**: 
  - Yeşil: 0-5 alarm
  - Sarı: 6-15 alarm
  - Kırmızı: 16+ alarm
- **Tıklama Eylemi**: Alarms sayfasına yönlendirir

**4. Data Sources Kartı**
- **Gösterilen Bilgi**: Bağlı veri kaynağı sayısı
- **Tıklama Eylemi**: Data Sources sayfasına yönlendirir

### Son Alarmlar Bölümü

Dashboard'da son 10 alarm görüntülenir:

**Alarm Gösterim Formatı:**
```
🔴 [Önem Seviyesi] Alarm Başlığı - [Zaman]
   └─ Kısa açıklama ve ana sebep
```

**Örnek Alarm Listesi:**
```
🔴 Kritik: Hafta Sonu Yüksek Tutar İşlemi - 3 dakika önce
   └─ 750,000 TL Cumartesi transferi tespit edildi

🟠 Yüksek: Brute Force Saldırı Denemesi - 12 dakika önce  
   └─ IP 192.168.1.200'den 47 başarısız giriş

🟡 Orta: Çalışan Fazla Mesai Anomalisi - 1.5 saat önce
   └─ Ahmet Yılmaz 315 saat fazla mesai yaptı
```

### Sistem Performans Göstergeleri

**Gerçek Zamanlı Metrikler:**
- **CPU Kullanımı**: Sunucu işlemci yükü
- **Memory Kullanımı**: RAM kullanım oranı
- **Günlük İşlem Sayısı**: 24 saatte işlenen kayıt
- **Ortalama Yanıt Süresi**: Sistem tepki süresi

**Performans Uyarı Seviyeleri:**
```
CPU Kullanımı:
├─ 0-70%: 🟢 Normal
├─ 71-85%: 🟡 Dikkat
└─ 86-100%: 🔴 Kritik

Memory Kullanımı:
├─ 0-75%: 🟢 Normal  
├─ 76-90%: 🟡 Dikkat
└─ 91-100%: 🔴 Kritik
```

---

## Audit Areas (Denetim Alanları) Yönetimi

Audit Areas, denetim süreçlerinizi organize etmek için kullanılan ana kategorilerdir. Her denetim alanı, belirli bir iş sürecini veya departmanı temsil eder.

### Audit Area Listesi Görünümü

**Sol Menüden Erişim:**
```
Ana Menü → Audit Areas
```

**Liste Ekranı Bileşenleri:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Denetim Alanları                         │
├─────────────────────────────────────────────────────────────┤
│ [+ Yeni Alan Oluştur]                        [🔍 Ara...]   │
├─────────────────────────────────────────────────────────────┤
│ │ Alan Adı        │ Açıklama      │ Durumu │ Son Güncelleme │
│ ├─────────────────┼───────────────┼────────┼────────────────┤
│ │ Finansal İşlemler│ Mali işlemler │ Aktif  │ 2 saat önce    │
│ │ İnsan Kaynakları │ İK süreçleri  │ Aktif  │ 1 gün önce     │
│ │ BT Güvenlik     │ Siber güvenlik │ Aktif  │ 3 saat önce    │
│ │ Satın Alma      │ Tedarik zinciri│ Pasif  │ 1 hafta önce   │
└─────────────────────────────────────────────────────────────┘
```

### Yeni Audit Area Oluşturma

**Adım 1: Oluşturma Sayfasına Erişim**
```
1. Audit Areas sayfasında "Yeni Alan Oluştur" butonuna tıklayın
2. Açılan formda gerekli bilgileri doldurun
```

**Adım 2: Form Doldurma**
```
┌─────────────────────────────────────────────┐
│           Yeni Denetim Alanı Oluştur        │
├─────────────────────────────────────────────┤
│ Alan Adı*: [________________]               │
│ Açıklama:  [________________]               │
│           [________________]                │
│           [________________]                │
│                                             │
│ ☑ Aktif durumda başlat                     │
│                                             │
│ [İptal]              [Oluştur]             │
└─────────────────────────────────────────────┘
```

**Örnek Doldurulmuş Form:**
```
Alan Adı: Muhasebe Süreçleri
Açıklama: Şirketin tüm muhasebe işlemleri, mali raporlama 
         ve finansal kontrolleri kapsar. Gelir-gider 
         takibi, bütçe kontrolleri ve vergi uyumluluğu 
         dahildir.
         
☑ Aktif durumda başlat
```

### Audit Area Detay Sayfası

**Detay Sayfasına Erişim:**
- Liste ekranında alan adına tıklayın

**Detay Sayfası İçeriği:**
```
┌─────────────────────────────────────────────────────────────┐
│                 Muhasebe Süreçleri - Detay                  │
├─────────────────────────────────────────────────────────────┤
│ 📊 Genel Bilgiler                                          │
│ Oluşturulma: 15.01.2025 14:30                             │
│ Son Güncelleme: 26.01.2025 10:15                          │
│ Durum: ✅ Aktif                                            │
│ Sahip: admin                                               │
├─────────────────────────────────────────────────────────────┤
│ 📋 Bağlı Kaynaklar                                         │
│ • Muhasebe Veritabanı (MySQL)                             │
│ • Excel Raporları (/data/accounting/)                      │
│ • SAP API Bağlantısı                                       │
├─────────────────────────────────────────────────────────────┤
│ 🔧 Aktif Kurallar (8)                                      │
│ • Yüksek Tutarlı İşlem Kontrolü                           │
│ • Hafta Sonu İşlem Anomalisi                              │
│ • Duplicate Payment Tespiti                                │
│ • Budget Overflow Uyarısı                                  │
│ [Tümünü Görüntüle...]                                     │
├─────────────────────────────────────────────────────────────┤
│ 🚨 Son Alarmlar (5)                                        │
│ • 750K TL Cumartesi Transferi - 2 saat önce               │
│ • Çift Ödeme Tespit Edildi - 4 saat önce                  │
│ [Tümünü Görüntüle...]                                     │
└─────────────────────────────────────────────────────────────┘
```

### Audit Area Düzenleme

**Düzenleme Sayfasına Erişim:**
```
Detay Sayfası → "Düzenle" butonu
```

**Düzenlenebilir Alanlar:**
- Alan adı
- Açıklama
- Aktif/Pasif durumu
- Sahiplik bilgisi

**Örnek Düzenleme:**
```
Eski Bilgiler:
─────────────
Alan Adı: Muhasebe Süreçleri
Açıklama: Şirketin tüm muhasebe işlemleri...

Yeni Bilgiler:  
─────────────
Alan Adı: Mali İşlemler ve Muhasebe
Açıklama: Şirketin tüm mali işlemleri, muhasebe süreçleri,
         finansal raporlama ve vergi uyumluluğu kapsar.
         Bütçe kontrolleri ve maliyet analizi dahildir.
```

---

## Data Sources (Veri Kaynakları) Yönetimi

Data Sources, AuditAI sisteminin analiz edeceği veri kaynaklarını tanımladığınız bölümdür. Sistem çeşitli veri türlerini destekler.

### Desteklenen Veri Kaynağı Türleri

**1. Veritabanı Bağlantıları**
```
• MySQL
• PostgreSQL  
• SQL Server
• Oracle
• SQLite
```

**2. Dosya Bazlı Kaynaklar**
```
• CSV dosyaları
• Excel dosyaları (.xlsx, .xls)
• JSON dosyaları
• XML dosyaları
```

**3. API Bağlantıları**
```
• REST API'ler
• SOAP servisleri
• Web service'ler
• Custom API entegrasyonları
```

### Data Sources Liste Görünümü

**Erişim:**
```
Ana Menü → Data Sources
```

**Liste Ekranı:**
```
┌─────────────────────────────────────────────────────────────┐
│                     Veri Kaynakları                         │
├─────────────────────────────────────────────────────────────┤
│ [+ Yeni Kaynak Ekle]                       [🔍 Filtrele]   │
├─────────────────────────────────────────────────────────────┤
│ │ Kaynak Adı      │ Türü     │ Durum  │ Son Senkronizasyon │
│ ├─────────────────┼──────────┼────────┼───────────────────┤
│ │ Muhasebe DB     │ MySQL    │ 🟢 Aktif│ 5 dakika önce     │
│ │ HR Excel Files  │ Excel    │ 🟢 Aktif│ 1 saat önce       │
│ │ CRM API         │ REST API │ 🟡 Uyarı│ 30 dakika önce    │
│ │ Eski Sistem     │ Oracle   │ 🔴 Hata │ 2 gün önce        │
└─────────────────────────────────────────────────────────────┘
```

### Yeni Veri Kaynağı Ekleme

**Adım 1: Kaynak Türü Seçimi**
```
┌─────────────────────────────────────────────┐
│          Veri Kaynağı Türü Seçin            │
├─────────────────────────────────────────────┤
│                                             │
│  🗄️  [Veritabanı]      📁 [Dosya]          │
│                                             │
│  🌐  [API/Web Servis]  ⚙️  [Özel]          │
│                                             │
└─────────────────────────────────────────────┘
```

**Adım 2: Veritabanı Konfigürasyonu (Örnek)**
```
┌─────────────────────────────────────────────┐
│         Veritabanı Bağlantı Ayarları        │
├─────────────────────────────────────────────┤
│ Kaynak Adı*: [Muhasebe Veritabanı_____]    │
│ Veritabanı Türü: [MySQL ▼]                 │
│ Sunucu Adresi*: [192.168.1.100_______]     │
│ Port: [3306]                                │
│ Veritabanı Adı*: [accounting_db_______]     │
│ Kullanıcı Adı*: [audit_user__________]      │
│ Şifre*: [●●●●●●●●●●●●●●●●●●●●●●●●●●●●]      │
│                                             │
│ ☑ SSL kullan                                │
│ ☑ Bağlantıyı test et                        │
│                                             │
│ [Test Et] [İptal]        [Kaydet]          │
└─────────────────────────────────────────────┘
```

**Adım 3: Excel/CSV Konfigürasyonu (Örnek)**
```
┌─────────────────────────────────────────────┐
│           Dosya Kaynağı Ayarları            │
├─────────────────────────────────────────────┤
│ Kaynak Adı*: [İK Raporları____________]     │
│ Dosya Türü: [Excel (.xlsx) ▼]              │
│ Dosya Yolu*: [/data/hr/reports/______]      │
│ Şablon Dosyası: [hr_template.xlsx____]      │
│                                             │
│ 📋 Sütun Yapılandırması:                   │
│ ├─ A sütunu: Çalışan ID                    │
│ ├─ B sütunu: Ad Soyad                      │
│ ├─ C sütunu: Departman                     │
│ ├─ D sütunu: Maaş                          │
│ └─ E sütunu: Fazla Mesai                   │
│                                             │
│ ☑ İlk satır başlık                         │
│ ☑ Otomatik güncelleme (saatlik)            │
│                                             │
│ [Önizleme] [İptal]       [Kaydet]          │
└─────────────────────────────────────────────┘
```

### Veri Kaynağı Detay ve Yönetimi

**Detay Sayfası:**
```
┌─────────────────────────────────────────────────────────────┐
│              Muhasebe Veritabanı - Detaylar                 │
├─────────────────────────────────────────────────────────────┤
│ 📊 Bağlantı Bilgileri                                      │
│ Tür: MySQL Database                                        │
│ Sunucu: 192.168.1.100:3306                               │
│ Veritabanı: accounting_db                                  │
│ Durum: 🟢 Bağlı ve Aktif                                   │
│ Son Test: 26.01.2025 14:30 ✅                            │
├─────────────────────────────────────────────────────────────┤
│ 📈 Senkronizasyon İstatistikleri                          │
│ Son Senkronizasyon: 5 dakika önce                         │
│ Başarılı Senkronizasyon: 1,247                           │
│ Başarısız Senkronizasyon: 3                               │
│ İşlenen Kayıt: 45,629                                     │
│ Ortalama Süre: 2.3 saniye                                 │
├─────────────────────────────────────────────────────────────┤
│ 🗂️ Tablolar ve Alanlar                                    │
│ ┌─ transactions (32,150 kayıt)                            │
│ │  ├─ id (INT, Primary Key)                               │
│ │  ├─ amount (DECIMAL)                                    │
│ │  ├─ transaction_date (DATETIME)                         │
│ │  ├─ description (VARCHAR)                               │
│ │  └─ user_id (INT, Foreign Key)                          │
│ ├─ users (1,250 kayıt)                                    │
│ │  ├─ id (INT, Primary Key)                              │
│ │  ├─ username (VARCHAR)                                  │
│ │  └─ department (VARCHAR)                                │
│ └─ accounts (45 kayıt)                                     │
├─────────────────────────────────────────────────────────────┤
│ ⚙️ Eylemler                                                │
│ [Bağlantıyı Test Et] [Şimdi Senkronize Et]                │
│ [Düzenle] [Veri Önizleme] [Kaldır]                        │
└─────────────────────────────────────────────────────────────┘
```

### Veri Mapping (Alan Eşleştirme)

**Mapping Sayfasına Erişim:**
```
Data Source Detay → "Add Mapping" butonu
```

**Drag & Drop Mapping Arayüzü:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Veri Alan Eşleştirme                     │
├─────────────────────────────────────────────────────────────┤
│ Sol: Kaynak Alanları        │  Sağ: Hedef Alanlar          │
├─────────────────────────────┼─────────────────────────────────┤
│ 📊 transactions tablosu     │  🎯 AuditAI Standart Alanlar  │
│                             │                               │
│ 🔘 id ──────────────────────┼─→ ⭕ transaction_id           │
│ 🔘 amount ──────────────────┼─→ ⭕ amount                    │
│ 🔘 transaction_date ────────┼─→ ⭕ date                      │
│ 🔘 description ─────────────┼─→ ⭕ description               │
│ 🔘 user_id ─────────────────┼─→ ⭕ user_identifier           │
│                             │                               │
│ 🔍 [Alanları Filtrele...]   │  🔍 [Hedef Alanları Ara...]   │
│                             │                               │
│ ✅ Eşleştirme Tamamlandı: 5/8 alan                         │
│                                                             │
│ [Önizleme] [Sıfırla]              [Kaydet ve Uygula]      │
└─────────────────────────────────────────────────────────────┘
```

**Mapping Önizleme:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Veri Önizleme (İlk 5 Kayıt)             │
├─────────────────────────────────────────────────────────────┤
│ transaction_id │ amount    │ date       │ description        │
│ ───────────────┼───────────┼────────────┼──────────────────  │
│ TXN001         │ 15,450.00 │ 2025-01-26 │ Maaş ödemesi      │
│ TXN002         │ 2,300.50  │ 2025-01-26 │ Ofis malzemeleri   │
│ TXN003         │ 85,000.00 │ 2025-01-25 │ Tedarikçi ödemesi  │
│ TXN004         │ 1,200.00  │ 2025-01-25 │ Elektrik faturası  │
│ TXN005         │ 750,000.00│ 2025-01-25 │ Yatırım transferi  │
└─────────────────────────────────────────────────────────────┘

✅ Mapping başarılı - 5 kayıt eşleştirildi
⚠️ 2 kayıtta tarih formatı uyarısı
🔄 Otomatik dönüştürme uygulanacak
```

---

## Rules (Kurallar) Yönetimi

Rules, AuditAI sisteminin beyni olan bölümdür. Burada çeşitli algoritma ve koşullarla otomatik denetim kuralları oluşturursunuz.

### Kural Türleri

**1. Anomaly Detection (Anomali Tespiti)**
```
• Isolation Forest algoritması
• Autoencoder neural networks
• Statistical anomaly detection
• Kullanım: Olağandışı veri desenlerini tespit
```

**2. Fraud Detection (Dolandırıcılık Tespiti)**
```
• Random Forest classifier
• Pattern matching algorithms
• Behavioral analysis
• Kullanım: Hileli işlemleri tespit
```

**3. Threshold Rules (Eşik Kuralları)**
```
• Basit matematiksel karşılaştırmalar
• Minimum/maksimum değer kontrolleri
• Yüzde bazlı analizler
• Kullanım: Bütçe aşımları, limit kontrolleri
```

**4. Time Series Analysis (Zaman Serisi Analizi)**
```
• Prophet forecasting
• ARIMA modeling
• Trend analysis
• Kullanım: Tahmin ve trend sapmaları
```

**5. Security Rules (Güvenlik Kuralları)**
```
• Brute force detection
• SQL injection patterns
• Suspicious IP monitoring
• Kullanım: Siber güvenlik tehditleri
```

**6. Compliance Rules (Uyumluluk Kuralları)**
```
• Regulatory compliance checks
• Policy violation detection
• Approval workflow monitoring
• Kullanım: Yasal ve kurumsal uyumluluk
```

### Rules Liste Görünümü

**Erişim:**
```
Ana Menü → Rules
```

**Liste Ekranı:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Denetim Kuralları                        │
├─────────────────────────────────────────────────────────────┤
│ [+ Yeni Kural Oluştur]  [📊 Performans] [🔍 Filtrele]     │
├─────────────────────────────────────────────────────────────┤
│ │ Kural Adı           │ Tür        │ Durum  │ Son Çalışma    │
│ ├─────────────────────┼────────────┼────────┼────────────────┤
│ │ Yüksek Tutar Anomali│ 🤖 Anomali │ 🟢 Aktif│ 3 dakika önce  │
│ │ Hafta Sonu İşlemleri│ 📊 Eşik    │ 🟢 Aktif│ 15 dakika önce │
│ │ Brute Force Tespit  │ 🛡️ Güvenlik│ 🟢 Aktif│ 1 dakika önce  │
│ │ Duplicate Payments  │ 🔍 Fraud   │ 🟡 Uyarı│ 2 saat önce    │
│ │ Budget Overflow     │ 📊 Eşik    │ 🔴 Hata │ 1 gün önce     │
└─────────────────────────────────────────────────────────────┘
```

### Yeni Kural Oluşturma - Adım Adım

**Adım 1: Temel Bilgiler**
```
┌─────────────────────────────────────────────┐
│              Kural Temel Bilgileri           │
├─────────────────────────────────────────────┤
│ Kural Adı*: [Yüksek Tutarlı İşlem Kontrolü] │
│                                             │
│ Açıklama: [100.000 TL üzeri işlemleri      │
│           [analiz eder ve anormallik        │
│           [tespiti yapar                    │
│                                             │
│ Denetim Alanı*: [Finansal İşlemler ▼]      │
│                                             │
│ Kural Türü*: [Anomaly Detection ▼]         │
│                                             │
│ [Geri] [İptal]              [İleri →]      │
└─────────────────────────────────────────────┘
```

**Adım 2: Algoritma Seçimi ve Yapılandırma**
```
┌─────────────────────────────────────────────┐
│             Algoritma Yapılandırması        │
├─────────────────────────────────────────────┤
│ 🤖 Algoritma: [Isolation Forest ▼]         │
│                                             │
│ ⚡ Hassasiyet: [●●●●●○○○○○] 0.8 (Yüksek)    │
│                                             │
│ 🎯 Güven Eşiği: [●●●●●●●●○○] 0.85 (%85)     │
│                                             │
│ 🏷️ Risk Kategorisi: [Yüksek ▼]             │
│                                             │
│ 📊 Gelişmiş Ayarlar:                       │
│ ☑ Otomatik model güncelleme                │
│ ☑ Geçmiş verilerle karşılaştır             │
│ ☐ Mevsimsel ayarlama uygula                │
│                                             │
│ [← Geri] [İptal]           [İleri →]       │
└─────────────────────────────────────────────┘
```

**Adım 3: Veri Konfigürasyonu**
```
┌─────────────────────────────────────────────┐
│              Veri Konfigürasyonu            │
├─────────────────────────────────────────────┤
│ 📂 Veri Kaynağı: [Muhasebe DB ▼]           │
│                                             │
│ 🎯 Hedef Alanlar:                          │
│ ☑ amount (Tutar)                           │
│ ☑ transaction_date (Tarih)                 │
│ ☑ day_of_week (Haftanın Günü)             │
│ ☐ merchant_id (Satıcı ID)                  │
│ ☐ user_location (Kullanıcı Konumu)        │
│                                             │
│ 🔍 Filtre Koşulları:                       │
│ amount > [100000] TL                       │
│ transaction_date >= [Son 90 gün]           │
│                                             │
│ [← Geri] [İptal]           [İleri →]       │
└─────────────────────────────────────────────┘
```

**Adım 4: Alarm ve Bildirim Ayarları**
```
┌─────────────────────────────────────────────┐
│            Alarm ve Bildirim Ayarları       │
├─────────────────────────────────────────────┤
│ 🚨 Alarm Önem Seviyesi:                    │
│ ● Kritik   ○ Yüksek   ○ Orta   ○ Düşük     │
│                                             │
│ 📬 Bildirim Türü:                          │
│ ☑ Sistem içi alarm oluştur                │
│ ☑ E-posta bildirimi gönder                │
│ ☐ SMS bildirimi gönder                    │
│ ☐ Webhook tetikle                         │
│                                             │
│ 📧 E-posta Alıcıları:                      │
│ [admin@firma.com; muhasebe@firma.com]      │
│                                             │
│ ⏰ Bildirim Sıklığı:                       │
│ ● Anında  ○ 15 dk'da bir  ○ Saatlik        │
│                                             │
│ [← Geri] [İptal]           [Oluştur]       │
└─────────────────────────────────────────────┘
```

### Kural Detay Sayfası

**Detay Görünümü:**
```
┌─────────────────────────────────────────────────────────────┐
│          Yüksek Tutarlı İşlem Kontrolü - Detaylar           │
├─────────────────────────────────────────────────────────────┤
│ 📊 Genel Bilgiler                                          │
│ Durum: 🟢 Aktif                                            │
│ Oluşturulma: 20.01.2025 09:15                             │
│ Son Güncelleme: 25.01.2025 14:30                          │
│ Algoritma: 🤖 Isolation Forest                             │
│ Hassasiyet: ●●●●●○○○○○ 0.8                                │
├─────────────────────────────────────────────────────────────┤
│ 📈 Performans Metrikleri                                   │
│ ┌─────────────┬─────────────┬─────────────┬─────────────┐   │
│ │   Accuracy  │  Precision  │   Recall    │  F1-Score   │   │
│ │    94.2%    │    89.7%    │    91.8%    │    90.7%    │   │
│ └─────────────┴─────────────┴─────────────┴─────────────┘   │
│                                                             │
│ Son 30 gün: 156 çalıştırma, 23 alarm üretildi             │
│ Ortalama İşlem Süresi: 145ms                               │
├─────────────────────────────────────────────────────────────┤
│ 🚨 Son Alarmlar                                            │
│ • 26.01.2025 14:30 - 750,000 TL Cumartesi transferi       │
│ • 25.01.2025 22:15 - 425,000 TL gece saati işlemi         │
│ • 24.01.2025 16:45 - 680,000 TL tekrarlayan ödeme         │
│ [Tüm Alarmları Görüntüle...]                              │
├─────────────────────────────────────────────────────────────┤
│ ⚙️ Eylemler                                                │
│ [Düzenle] [Kopyala] [Test Et] [Devre Dışı Bırak]          │
│ [Performans Raporu] [Alarm Geçmişi] [Sil]                 │
└─────────────────────────────────────────────────────────────┘
```

### Gelişmiş Kural Örnekleri

**Örnek 1: İK Fazla Mesai Anomalisi**
```json
{
    "rule_name": "Çalışan Fazla Mesai Anomali Tespiti",
    "rule_type": "anomaly_detection",
    "algorithm": "statistical_anomaly",
    "configuration": {
        "data_source": "hr_database",
        "target_field": "overtime_hours",
        "context_fields": ["department", "position", "base_salary"],
        "time_window": "monthly",
        "threshold": 3.0,  // 3 standart sapma
        "minimum_overtime": 50  // Minimum 50 saat
    },
    "alerts": {
        "severity": "high",
        "notification": "immediate",
        "recipients": ["hr@firma.com", "manager@firma.com"]
    }
}
```

**Örnek 2: Tedarikçi Dolandırıcılık Tespiti**
```json
{
    "rule_name": "Şüpheli Tedarikçi Dolandırıcılık Analizi",
    "rule_type": "fraud_detection", 
    "algorithm": "random_forest",
    "configuration": {
        "features": [
            "vendor_history_days",
            "price_deviation_percentage", 
            "payment_method_risk",
            "invoice_regularity_score",
            "similar_vendor_comparison"
        ],
        "training_period": "last_2_years",
        "confidence_threshold": 0.8,
        "risk_factors": {
            "new_vendor": "< 90 days",
            "high_price": "> 200% of average",
            "cash_payment": "risk_multiplier: 2.0"
        }
    }
}
```

**Örnek 3: Güvenlik Brute Force Tespiti**
```json
{
    "rule_name": "Brute Force Saldırı Tespiti",
    "rule_type": "security",
    "algorithm": "pattern_matching",
    "configuration": {
        "time_window": 300,  // 5 dakika
        "thresholds": {
            "failed_attempts": 15,
            "unique_usernames": 5,
            "success_rate": 0.1,
            "ip_reputation_check": true
        },
        "auto_actions": {
            "block_ip": true,
            "alert_security_team": true,
            "log_incident": true
        }
    },
    "response": {
        "immediate_block": true,
        "escalation_time": 60,  // saniye
        "notification_channels": ["email", "sms", "webhook"]
    }
}
```

---

## Alarms (Alarmlar) Sistemi

Alarms, kurallarınızın tetiklendiği durumları gösteren bildirim sistemidir. Her alarm, tespit edilen anomali veya ihlal hakkında detaylı bilgi içerir.

### Alarms Liste Görünümü

**Erişim:**
```
Ana Menü → Alarms
```

**Liste Ekranı:**
```
┌─────────────────────────────────────────────────────────────┐
│                        Alarmlar                             │
├─────────────────────────────────────────────────────────────┤
│ [📊 Özet] [🔍 Filtrele] [📅 Tarih] [⬇️ Dışa Aktar]        │
├─────────────────────────────────────────────────────────────┤
│ 🔴 Kritik (15) │ 🟠 Yüksek (42) │ 🟡 Orta (28) │ 🟢 Düşük (8) │
├─────────────────────────────────────────────────────────────┤
│ │Önem│ Başlık                    │ Durum    │ Tarih/Saat    │
│ ├───┼─────────────────────────────┼──────────┼───────────────┤
│ │🔴 │ Yüksek Tutarlı Hafta Sonu   │ 🟢 Açık   │ 26.01 14:30   │
│ │   │ İşlemi: 750,000 TL transfer │          │               │
│ ├───┼─────────────────────────────┼──────────┼───────────────┤
│ │🟠 │ Brute Force Saldırısı:      │ 🟡 Kabul  │ 26.01 14:15   │
│ │   │ IP 192.168.1.200            │          │               │
│ ├───┼─────────────────────────────┼──────────┼───────────────┤
│ │🟡 │ Fazla Mesai Anomalisi:      │ 🔵 Çözüldü│ 26.01 12:45   │
│ │   │ Ahmet Yılmaz (315 saat)     │          │               │
└─────────────────────────────────────────────────────────────┘
```

### Alarm Durumları

**Durum Türleri:**
```
🟢 Open (Açık)        - Yeni tespit edilen alarm
🟡 Acknowledged (Kabul)- İncelenmekte olan alarm  
🔵 Resolved (Çözüldü) - Çözümlenmiş alarm
🔴 Dismissed (Ret)    - False positive olarak işaretlenen
```

**Durum Değiştirme:**
```
Alarm Satırı → Durum Sütunu → Dropdown Menü
├─ Acknowledge (Kabul Et)
├─ Resolve (Çözüldü Olarak İşaretle)
├─ Dismiss (Reddet - False Positive)
└─ Reopen (Yeniden Aç)
```

### Alarm Detay Sayfası

**Detay Görünümü:**
```
┌─────────────────────────────────────────────────────────────┐
│              Yüksek Tutarlı Hafta Sonu İşlemi               │
│                      Alarm Detayları                        │
├─────────────────────────────────────────────────────────────┤
│ 🔴 Kritik Öncelik                    📅 26.01.2025 14:30   │
│ 🟢 Durum: Açık                       👤 Atanan: -          │
│ 🤖 Algoritma: Isolation Forest       🎯 Risk Skoru: 92%    │
├─────────────────────────────────────────────────────────────┤
│ 📋 Alarm Mesajı                                            │
│ Cumartesi günü 750,000 TL tutarında transfer işlemi tespit │
│ edildi. Bu tutar, normal hafta içi işlemlerinin %340'ı     │
│ büyüklüğünde ve hafta sonu için olağandışı.               │
├─────────────────────────────────────────────────────────────┤
│ 📊 Analiz Verileri                                         │
│ ┌─────────────────┬─────────────────────────────────────┐   │
│ │ İşlem Tutarı    │ 750,000.00 TL                       │   │
│ │ İşlem Zamanı    │ 26.01.2025 Cumartesi 14:30         │   │
│ │ Kullanıcı       │ mehmet.finans                       │   │
│ │ Alıcı Hesap     │ TR33 0006 1005 1978 6457 8413 26   │   │
│ │ İşlem Türü      │ EFT Transfer                        │   │
│ │ Açıklama        │ Yatırım transferi                   │   │
│ └─────────────────┴─────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ 🔍 Anomali Analizi                                         │
│ • Normal hafta içi ortalama: 220,000 TL                   │
│ • Hafta sonu işlem geçmişi: Son 6 ayda 2 işlem           │
│ • Benzer kullanıcı davranışı: %15 match                   │
│ • Risk faktörleri: Yüksek tutar + Hafta sonu + Nadir işlem │
├─────────────────────────────────────────────────────────────┤
│ 💬 Yorumlar ve Notlar                                      │
│ [Yorum Ekle...]                                            │
│                                                             │
│ 📝 26.01.2025 14:35 - system                              │
│ Otomatik alarm oluşturuldu. İnceleme gerekli.             │
├─────────────────────────────────────────────────────────────┤
│ ⚙️ Eylemler                                                │
│ [✅ Kabul Et] [✖️ Reddet] [🔄 Yeniden Analiz Et]          │
│ [👤 Ata] [📧 Bildir] [📋 Rapor Et] [🔗 Benzer Alarmlar]   │
└─────────────────────────────────────────────────────────────┘
```

### Alarm Filtreleme ve Arama

**Filtre Seçenekleri:**
```
┌─────────────────────────────────────────────┐
│              Alarm Filtreleri               │
├─────────────────────────────────────────────┤
│ 📅 Tarih Aralığı:                          │
│ Başlangıç: [26.01.2025] Bitiş: [26.01.2025] │
│                                             │
│ 🎯 Önem Seviyesi:                          │
│ ☑ Kritik  ☑ Yüksek  ☐ Orta  ☐ Düşük        │
│                                             │
│ 📊 Durum:                                   │
│ ☑ Açık  ☐ Kabul Edildi  ☐ Çözüldü  ☐ Ret   │
│                                             │
│ 🤖 Algoritma:                              │
│ ☑ Isolation Forest  ☐ Random Forest        │ 
│ ☐ Prophet  ☐ Pattern Matching              │
│                                             │
│ 🏢 Denetim Alanı:                          │
│ [Finansal İşlemler ▼]                      │
│                                             │
│ 🔍 Arama Metni:                            │
│ [transfer, yüksek tutar...]                │
│                                             │
│ [Temizle]              [Filtrele]          │
└─────────────────────────────────────────────┘
```

### Toplu Alarm İşlemleri

**Toplu Seçim ve İşlem:**
```
┌─────────────────────────────────────────────────────────────┐
│ ☑ Tümünü Seç    Seçilen: 5 alarm                          │
├─────────────────────────────────────────────────────────────┤
│ ☑ │🔴│ Yüksek Tutarlı Hafta Sonu İşlemi    │ Açık    │14:30│
│ ☑ │🟠│ Brute Force Saldırısı IP 192.168... │ Açık    │14:15│
│ ☐ │🟡│ Fazla Mesai Anomalisi Ahmet Y.      │ Çözüldü │12:45│
│ ☑ │🔴│ Şüpheli Tedarikçi Ödemesi          │ Açık    │11:30│
│ ☑ │🟠│ Sistem Performans Uyarısı          │ Açık    │10:15│
├─────────────────────────────────────────────────────────────┤
│ Toplu İşlemler:                                             │
│ [Tümünü Kabul Et] [Tümünü Çözüldü İşaretle] [Toplu Sil]   │
│ [E-posta Gönder] [PDF Rapor] [CSV Dışa Aktar]             │
└─────────────────────────────────────────────────────────────┘
```

---

## Admin Panel ve Raporlama

Admin Panel, sistem yöneticileri için gelişmiş yönetim araçları ve kapsamlı raporlama özellikleri sunar.

### Admin Dashboard

**Erişim:**
```
Ana Menü → Admin (Sadece admin kullanıcıları)
```

**Admin Dashboard Genel Görünüm:**
```
┌─────────────────────────────────────────────────────────────┐
│                     Admin Dashboard                         │
├─────────────────────────────────────────────────────────────┤
│ 📊 Sistem Genel Durumu                                     │
│ ┌─────────────┬───────────────┬────────────┬─────────────┐   │
│ │ Toplam      │ Aktif         │ Günlük     │ Sistem      │   │
│ │ Kullanıcı   │ Kural         │ İşlem      │ Sağlık      │   │
│ │    28       │     45        │  15,432    │   🟢 İyi    │   │
│ └─────────────┴───────────────┴────────────┴─────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ 🚨 Anomali Tespit Özeti (Son 24 Saat)                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🔴 Kritik: 8    🟠 Yüksek: 15   🟡 Orta: 23   🟢 Düşük: 4│ │
│ │ 📈 Trend: %12 artış (önceki güne göre)                 │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ 🤖 AI/ML Model Performansı                                │
│ ┌─ Isolation Forest: 94.2% accuracy (↑ 1.2%)             │ │
│ ├─ Random Forest: 91.5% accuracy (→ stabil)              │ │
│ ├─ Prophet: 8.7% MAPE (↓ 0.3% - iyileşme)               │ │
│ └─ Autoencoder: 96.1% reconstruction (↑ 2.1%)            │ │
├─────────────────────────────────────────────────────────────┤
│ 📈 Sistem Performans Metrikleri                           │
│ CPU: ████████░░ 80%    Memory: ██████░░░░ 60%            │
│ Disk: ███░░░░░░░ 30%   Network: ██░░░░░░░░ 20%           │
│ Ortalama Yanıt: 150ms  Günlük Uptime: 99.8%              │
└─────────────────────────────────────────────────────────────┘
```

### Sistem Sağlık Raporu

**System Health Sayfası:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Sistem Sağlık Raporu                     │
├─────────────────────────────────────────────────────────────┤
│ 🖥️ Sunucu Durumu                                           │
│ ┌─ İşletim Sistemi: Ubuntu 20.04 LTS                      │ │
│ ├─ Python Versiyonu: 3.11.0                               │ │
│ ├─ Flask Versiyonu: 2.3.3                                 │ │
│ ├─ Veritabanı: PostgreSQL 13.8                           │ │
│ └─ Uptime: 15 gün 8 saat 23 dakika                       │ │
├─────────────────────────────────────────────────────────────┤
│ 💾 Veritabanı İstatistikleri                              │
│ ┌─ Toplam Tablo: 15                                       │ │
│ ├─ Toplam Kayıt: 2,847,392                               │ │
│ ├─ Veritabanı Boyutu: 1.2 GB                             │ │
│ ├─ Günlük Büyüme: 45 MB                                  │ │
│ └─ Sorgu Performansı: Ortalama 23ms                      │ │
├─────────────────────────────────────────────────────────────┤
│ 🔄 Background İşlemler                                     │
│ ┌─ Scheduler Durumu: 🟢 Çalışıyor                         │ │
│ ├─ Son Kural Çalıştırma: 2 dakika önce                   │ │
│ ├─ Bekleyen İş: 3 kural                                   │ │
│ ├─ Başarılı İş: 1,247 (24 saat)                          │ │
│ └─ Başarısız İş: 2 (24 saat)                             │ │
├─────────────────────────────────────────────────────────────┤
│ ⚠️ Sistem Uyarıları                                       │
│ • Memory kullanımı %80'i geçti - İzlenmeli               │
│ • 3 kuralla performans düşüklüğü tespit edildi           │
│ • Disk alanı 1 ay içinde dolabilir                       │
│                                                             │
│ 💡 Öneriler                                               │
│ • Weekly database maintenance planlanmalı                  │
│ • Log rotation ayarları güncellenebilir                   │
│ • Memory optimization gerekebilir                         │
└─────────────────────────────────────────────────────────────┘
```

### Kullanıcı Yönetimi

**Users Sayfası:**
```
┌─────────────────────────────────────────────────────────────┐
│                      Kullanıcı Yönetimi                     │
├─────────────────────────────────────────────────────────────┤
│ [+ Yeni Kullanıcı]  [📊 İstatistikler]  [🔍 Ara]          │
├─────────────────────────────────────────────────────────────┤
│ │ Kullanıcı       │ E-posta          │ Rol    │ Son Giriş  │
│ ├─────────────────┼──────────────────┼────────┼────────────┤
│ │ admin           │ admin@sistem.com │ Admin  │ Şimdi      │
│ │ mehmet.finans   │ mf@firma.com     │ User   │ 2 saat önce│
│ │ ayse.muhasebe   │ am@firma.com     │ User   │ 1 gün önce │
│ │ ali.denetim     │ ad@firma.com     │ Admin  │ 3 gün önce │
│ │ fatma.ik        │ fik@firma.com    │ User   │ 1 hafta    │
└─────────────────────────────────────────────────────────────┘
```

**Yeni Kullanıcı Oluşturma:**
```
┌─────────────────────────────────────────────┐
│              Yeni Kullanıcı Ekle            │
├─────────────────────────────────────────────┤
│ Kullanıcı Adı*: [____________]              │
│ E-posta*: [____________]                    │
│ Ad Soyad: [____________]                    │
│ Şifre*: [●●●●●●●●●●●●]                      │
│ Şifre Tekrar*: [●●●●●●●●●●●●]               │
│                                             │
│ Rol:                                        │
│ ● Admin (Tüm yetkiler)                     │
│ ○ User (Sınırlı yetkiler)                  │
│                                             │
│ İzinler:                                    │
│ ☑ Audit Areas görüntüle/düzenle           │
│ ☑ Rules oluştur/düzenle                   │
│ ☑ Alarms görüntüle/yönet                  │
│ ☐ Admin panel erişimi                     │
│ ☐ Kullanıcı yönetimi                      │                              
│                                             │
│ [İptal]              [Kullanıcı Oluştur]   │
└─────────────────────────────────────────────┘
```

### Anomali Detayları Sayfası

**Anomaly Details Sayfası:**
```
┌─────────────────────────────────────────────────────────────┐
│                   Anomali Analiz Detayları                  │
├─────────────────────────────────────────────────────────────┤
│ 📊 Anomali Türü: Finansal İşlem Anomalisi                  │
│ 🤖 Algoritma: Isolation Forest                             │
│ 📅 Analiz Dönemi: Son 30 gün                              │
│ 🎯 Risk Eşiği: %85                                        │
├─────────────────────────────────────────────────────────────┤
│ 📈 İstatistiksel Analiz                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Toplam İşlem: 15,847                                   │ │
│ │ Anomali Tespit: 156 (%0.98)                           │ │
│ │ True Positive: 142 (%91.0)                             │ │
│ │ False Positive: 14 (%9.0)                              │ │
│ │ Ortalama Risk Skoru: %73.2                             │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ 🔍 Anomali Kategorileri                                   │
│ ┌─ Yüksek Tutar: 89 anomali (%57.1)                      │ │
│ ├─ Hafta Sonu İşlem: 34 anomali (%21.8)                  │ │
│ ├─ Gece Saati İşlem: 23 anomali (%14.7)                  │ │
│ └─ Nadir Lokasyon: 10 anomali (%6.4)                     │ │
├─────────────────────────────────────────────────────────────┤
│ 💰 Tutar Dağılım Analizi                                  │
│ ┌─ 100K-500K TL: ████████████ 72 anomali                │ │
│ ├─ 500K-1M TL:  ████████░░░░ 48 anomali                 │ │
│ ├─ 1M-2M TL:    ████░░░░░░░░ 26 anomali                 │ │
│ └─ 2M+ TL:      ██░░░░░░░░░░ 10 anomali                 │ │
├─────────────────────────────────────────────────────────────┤
│ ⏰ Zaman Dağılım Analizi                                  │
│ 00-06: ██░░░░░░░░ 12    12-18: ████████░░ 45              │
│ 06-12: ████░░░░░░ 23    18-24: ██████░░░░ 34              │
│                                                             │
│ 📅 Günlük Dağılım:                                        │
│ Pzt: ████░░░░░░ 18   Cmt: ████████░░ 42                   │
│ Sal: ███░░░░░░░ 15   Paz: █████░░░░░ 25                   │
│ Çar: ████░░░░░░ 19   ...                                  │
└─────────────────────────────────────────────────────────────┘
```

### Sistem Raporları

**Reports Sayfası Ana Görünüm:**
```
┌─────────────────────────────────────────────────────────────┐
│                     Sistem Raporları                        │
├─────────────────────────────────────────────────────────────┤
│ 📊 Hazır Raporlar                                          │
│ ┌─ 📈 Performans Özet Raporu                              │ │
│ ├─ 🚨 Anomali Tespit Raporu                               │ │
│ ├─ 🤖 AI/ML Model Performans Raporu                       │ │
│ ├─ 🛡️ Güvenlik Olay Raporu                               │ │
│ ├─ 👥 Kullanıcı Aktivite Raporu                           │ │
│ └─ 📋 Kural Çalıştırma Raporu                             │ │
├─────────────────────────────────────────────────────────────┤
│ 🎯 Özel Rapor Oluştur                                     │
│ Tarih Aralığı: [01.01.2025] - [26.01.2025]               │
│ Rapor Türü: [Anomali Analizi ▼]                          │
│ Denetim Alanı: [Tümü ▼]                                   │
│ Format: ● PDF  ○ Excel  ○ CSV                             │
│ [Rapor Oluştur]                                           │
├─────────────────────────────────────────────────────────────┤
│ 📥 Son Rapor İndirmeleri                                  │
│ • Anomali_Raporu_26012025.pdf - 2 saat önce              │
│ • Performans_Ozet_25012025.xlsx - 1 gün önce             │
│ • Guvenlik_Raporu_24012025.pdf - 2 gün önce              │
└─────────────────────────────────────────────────────────────┘
```

**PDF Rapor Örneği (Özet):**
```
┌─────────────────────────────────────────────────────────────┐
│                     AuditAI Anomali Raporu                  │
│                        26 Ocak 2025                         │
├─────────────────────────────────────────────────────────────┤
│ 📊 YÖNETİCİ ÖZETİ                                          │
│                                                             │
│ Son 30 günde sistemimiz toplam 45,629 işlemi analiz etti  │
│ ve 156 adet anormal durum tespit etti. Bu anomalilerin     │
│ %91'i gerçek risk teşkil ederken, %9'u yanlış pozitif     │
│ olarak değerlendirildi.                                     │
│                                                             │
│ 🔴 KRİTİK BULGULAR:                                        │
│ • 89 adet yüksek tutarlı işlem anomalisi                  │
│ • 34 adet hafta sonu işlem anomalisi                      │
│ • 23 adet gece saati işlem anomalisi                      │
│                                                             │
│ 💼 İŞ ETKİSİ ANALİZİ:                                      │
│ • Potansiyel dolandırıcılık önlendi: ~2.3M TL            │
│ • Erken tespit ile zaman tasarrufu: 45 saat              │
│ • Uyumluluk riski azaltıması: %78                         │
│                                                             │
│ 🎯 ÖNERİLER:                                              │
│ • Hafta sonu işlem onay prosedürü güçlendirilmeli        │
│ • Yüksek tutarlı işlemlerde çift onay sistemi kurulmalı  │
│ • Gece saati işlem limitleri gözden geçirilmeli          │
├─────────────────────────────────────────────────────────────┤
│ [Detaylı Analiz - Sayfa 2'de devam...]                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Kullanıcı Profili ve Ayarları

### Profil Sayfası

**Erişim:**
```
Ana Menü → Sağ Üst Kullanıcı Adı → Profil
```

**Profil Ayarları:**
```
┌─────────────────────────────────────────────┐
│              Kullanıcı Profili              │
├─────────────────────────────────────────────┤
│ 👤 Kişisel Bilgiler                        │
│ Kullanıcı Adı: [mehmet.yilmaz_______]      │
│ E-posta: [mehmet@firma.com_______]          │
│ Ad Soyad: [Mehmet Yılmaz_________]          │
│ Departman: [Finans_______________]          │
│                                             │
│ 🔒 Güvenlik Ayarları                       │
│ Mevcut Şifre: [●●●●●●●●●●●●]                │
│ Yeni Şifre: [●●●●●●●●●●●●]                  │
│ Şifre Tekrar: [●●●●●●●●●●●●]                │
│                                             │
│ 📧 Bildirim Ayarları                       │
│ ☑ E-posta bildirimleri al                  │
│ ☑ Kritik alarmlar                          │
│ ☐ Yüksek önem alarmları                    │
│ ☐ Haftalık özet raporu                     │
│                                             │
│ 🌐 Dil ve Görünüm                          │
│ Dil: [Türkçe ▼]                            │
│ Tema: [Açık ▼] (● Açık ○ Koyu)             │
│ Tarih Formatı: [DD.MM.YYYY ▼]              │
│                                             │
│ [Ayarları Kaydet]      [İptal]             │
└─────────────────────────────────────────────┘
```

### Bildirim Tercihleri

**Detaylı Bildirim Ayarları:**
```
┌─────────────────────────────────────────────┐
│            Bildirim Tercihleri              │
├─────────────────────────────────────────────┤
│ 📧 E-posta Bildirimleri                    │
│ ☑ Anında bildirim (kritik alarmlar)        │
│ ☑ 15 dakikalık özet (yüksek alarmlar)      │
│ ☐ Saatlik özet (orta alarmlar)             │
│ ☐ Günlük özet (düşük alarmlar)             │
│                                             │
│ 📱 Sistem İçi Bildirim                     │
│ ☑ Dashboard popup                          │
│ ☑ Tarayıcı bildirimi                       │
│ ☑ Ses uyarısı                              │
│                                             │
│ 📅 Rapor Gönderimi                         │
│ ☑ Haftalık anomali özeti (Pazartesi)       │
│ ☐ Aylık performans raporu                  │
│ ☐ Özel olaylar için anında rapor           │
│                                             │
│ ⏰ Çalışma Saatleri                        │
│ Başlangıç: [09:00] Bitiş: [18:00]          │
│ ☑ Sadece çalışma saatlerinde bildir        │
│ ☐ Hafta sonları bildirim gönder            │
│                                             │
│ [Kaydet ve Test Et]    [Varsayılan]        │
└─────────────────────────────────────────────┘
```

---

## Yapay Zeka ve Makine Öğrenmesi Özellikleri

### AI/ML Algoritmaları Detaylı Açıklaması

**1. Isolation Forest (Anomali Tespiti)**
```
🎯 Kullanım Alanı: Finansal anomaliler, olağandışı davranışlar
📊 Güçlü Olduğu Durumlar:
   • Yüksek boyutlu veriler
   • Az sayıda anomali içeren büyük veri setleri
   • Gerçek zamanlı tespit gereksinimi

⚙️ Parametre Ayarları:
   Contamination: 0.1 (Normal veri %90)
   n_estimators: 100 (Ağaç sayısı)
   max_samples: 256 (Örnek büyüklüğü)

📈 Örnek Sonuç:
   Normal İşlem: Score 0.65 (Normal aralık)
   Anomali İşlem: Score -0.23 (Anomali eşiği)
```

**2. Random Forest (Dolandırıcılık Tespiti)**
```
🎯 Kullanım Alanı: Dolandırıcılık tespiti, sınıflandırma
📊 Güçlü Olduğu Durumlar:
   • Çok değişkenli sınıflandırma
   • Feature importance analizi
   • Dengesiz veri setleri

⚙️ Parametre Ayarları:
   n_estimators: 200 (Ağaç sayısı)
   max_depth: 10 (Maksimum derinlik)
   min_samples_split: 5 (Bölme için minimum örnek)

📈 Örnek Sonuç:
   Fraud Probability: %87 (Yüksek risk)
   Feature Importance: amount (0.45), time (0.23), location (0.18)
```

**3. Prophet (Zaman Serisi Tahmini)**
```
🎯 Kullanım Alanı: Trend analizi, sezonluk tahminler
📊 Güçlü Olduğu Durumlar:
   • Eksik verili zaman serileri
   • Tatil etkilerinin olduğu veriler
   • Uzun vadeli tahminler

⚙️ Parametre Ayarları:
   Seasonality: 'auto' (Otomatik sezonluk tespit)
   Holidays: Turkey holidays (Türkiye resmi tatilleri)
   Growth: 'linear' (Doğrusal büyüme)

📈 Örnek Sonuç:
   Tahmin: 1,234,567 TL (Gelecek ay işlem hacmi)
   Güven Aralığı: [1,156,789 - 1,312,345] TL
   Trend: %5.2 artış
```

**4. ARIMA (Zaman Serisi Modelleme)**
```
🎯 Kullanım Alanı: Kısa vadeli tahmin, trend analizi
📊 Güçlü Olduğu Durumlar:
   • Durağan zaman serileri
   • Kısa vadeli tahminler
   • Matematiksel kesinlik gereksinimi

⚙️ Parametre Ayarları:
   p (AR): 2 (Otoregresif derecesi)
   d (I): 1 (Diferans derecesi)
   q (MA): 1 (Hareketli ortalama derecesi)

📈 Örnek Sonuç:
   Model: ARIMA(2,1,1)
   AIC Score: 1,234.56 (Düşük = İyi)
   Tahmin Hatası: ±5.2%
```

**5. Autoencoder (Derin Anomali Tespiti)**
```
🎯 Kullanım Alanı: Karmaşık anomali tespiti, boyut azaltma
📊 Güçlü Olduğu Durumlar:
   • Yüksek boyutlu veriler
   • Nonlinear anomaliler
   • Gürültülü veriler

⚙️ Parametre Ayarları:
   Encoder: [50, 25, 10] (Katman boyutları)
   Decoder: [10, 25, 50] (Çıkış katmanları)
   Activation: 'relu' (Aktivasyon fonksiyonu)

📈 Örnek Sonuç:
   Reconstruction Error: 0.0234 (Düşük = Normal)
   Threshold: 0.05 (Anomali eşiği)
   Anomaly Score: 0.087 (Yüksek = Anomali)
```

### AI/ML Model Performans İzleme

**Model Metrikleri Dashboard:**
```
┌─────────────────────────────────────────────────────────────┐
│                    AI/ML Model Performansı                  │
├─────────────────────────────────────────────────────────────┤
│ 🤖 Isolation Forest (Anomali Tespiti)                      │
│ ┌─ Accuracy: ████████████████████▌ 94.2%                  │ │
│ ├─ Precision: ████████████████████ 89.7%                  │ │
│ ├─ Recall: ██████████████████████▌ 91.8%                  │ │
│ ├─ F1-Score: █████████████████████ 90.7%                  │ │
│ └─ Trend: ↗ %1.2 artış (son hafta)                       │ │
├─────────────────────────────────────────────────────────────┤
│ 🌲 Random Forest (Dolandırıcılık)                         │
│ ┌─ Accuracy: ███████████████████ 91.5%                    │ │
│ ├─ Precision: ██████████████████ 88.3%                    │ │
│ ├─ Recall: ████████████████████ 93.1%                     │ │
│ ├─ AUC-ROC: ████████████████████▌ 0.952                   │ │
│ └─ Trend: → Stabil                                        │ │
├─────────────────────────────────────────────────────────────┤
│ 📈 Prophet (Zaman Serisi)                                 │
│ ┌─ MAPE: ████████▌ 8.7% (Düşük = İyi)                    │ │
│ ├─ MAE: 1,234 TL                                          │ │
│ ├─ MASE: 0.87                                             │ │
│ └─ Trend: ↘ %0.3 iyileşme                                │ │
├─────────────────────────────────────────────────────────────┤
│ 🧠 Autoencoder (Derin Anomali)                            │
│ ┌─ Reconstruction Accuracy: ████████████████████████▌ 96.1%│ │
│ ├─ Loss: 0.0045 (Düşük = İyi)                            │ │
│ ├─ Validation Loss: 0.0052                                │ │
│ └─ Trend: ↗ %2.1 iyileşme                                │ │
└─────────────────────────────────────────────────────────────┘
```

**Model Drift Tespiti:**
```
┌─────────────────────────────────────────────┐
│            Model Drift Analizi             │
├─────────────────────────────────────────────┤
│ 📊 Data Drift Tespiti                      │
│ Population Stability Index: 0.12            │
│ Durum: 🟡 Dikkat (>0.1)                     │
│                                             │
│ 🧠 Model Drift Tespiti                     │
│ Performance Decline: -%2.3                 │
│ Durum: 🟢 Stabil (<5%)                      │
│                                             │
│ 🔄 Son Model Güncelleme                    │
│ Tarih: 20.01.2025                          │
│ Gelecek Güncelleme: 27.01.2025             │
│                                             │
│ ⚠️ Öneriler                                │
│ • Model retraining önerilir                │
│ • Feature distribution değişti              │
│ • Yeni data pattern'leri tespit edildi     │
│                                             │
│ [Model Güncelle] [Detaylı Analiz]          │
└─────────────────────────────────────────────┘
```

---

## Pratik Örnekler ve Senaryolar

### Senaryo 1: Finansal Anomali Tespiti

**Problem:** Muhasebe departmanında yüksek tutarlı hafta sonu işlemlerini tespit etmek istiyoruz.

**Çözüm Adımları:**
```
1️⃣ Audit Area Oluşturma
   - Alan Adı: "Mali İşlemler Kontrolü"
   - Açıklama: "Hafta sonu ve yüksek tutarlı işlem tespiti"

2️⃣ Data Source Ekleme
   - Tür: MySQL Database
   - Tablo: transactions
   - Alanlar: amount, date, user_id, description

3️⃣ Rule Oluşturma
   - Tür: Anomaly Detection
   - Algoritma: Isolation Forest
   - Hedef Alanlar: amount, day_of_week, hour_of_day
   - Eşik: %85 güven seviyesi

4️⃣ Alarm Ayarları
   - Önem: Kritik
   - Bildirim: Anında e-posta
   - Alıcılar: mali@firma.com, mudur@firma.com
```

**Beklenen Sonuç:**
```
🚨 ALARM ÖRNEĞI:
Tarih: 26.01.2025 Cumartesi 14:30
Mesaj: 750,000 TL tutarında hafta sonu transferi tespit edildi
Risk Skoru: %92
Eylem: Anında bildirim gönderildi
```

### Senaryo 2: İK Fazla Mesai Anomalisi

**Problem:** Çalışanların anormal fazla mesai yapmasını önlemek istiyoruz.

**Çözüm:**
```
1️⃣ Veri Kaynağı: HR Excel Files
   - Dosya: /data/hr/monthly_overtime.xlsx
   - Sütunlar: employee_id, overtime_hours, base_salary, department

2️⃣ Kural Tanımı:
   - Tür: Statistical Anomaly
   - Metrik: Z-Score > 3.0
   - Karşılaştırma: Departman bazında

3️⃣ Sonuç:
   Ahmet Yılmaz (Finans): 315 saat fazla mesai
   Departman Ortalaması: 45 saat
   Z-Score: 4.2 (Yüksek Reward)
```

### Senaryo 3: Tedarikçi Dolandırıcılık Tespiti

**Problem:** Sahte tedarikçiler ve şüpheli ödemeleri tespit etmek.

**Çözüm:**
```
1️⃣ Data Sources:
   - vendor_master (Tedarikçi ana bilgileri)
   - purchase_orders (Satın alma siparişleri)
   - payments (Ödeme bilgileri)

2️⃣ Rule Configuration:
   - Algoritma: Random Forest
   - Features:
     * vendor_age_days (Tedarikçi yaşı)
     * price_vs_market_avg (Piyasa ortalama karşılaştırması)
     * payment_method_risk (Ödeme yöntemi riski)
     * invoice_pattern_score (Fatura düzen skoru)

3️⃣ Alarm Örneği:
   Tedarikçi: "ABC Teknik Ltd."
   Risk Faktörleri:
   - Yeni tedarikçi (45 gün)
   - Piyasa ortalamasının %340'ı fiyat
   - Nakit ödeme talebi
   - Düzensiz fatura formatı
   Fraud Probability: %94
```

### Senaryo 4: Güvenlik Tehdidi Tespiti

**Problem:** Brute force saldırıları ve şüpheli IP aktivitelerini tespit etmek.

**Çözüm:**
```
1️⃣ Veri Kaynağı: Security Logs
   - login_attempts
   - ip_address
   - timestamp
   - success/failure

2️⃣ Pattern Matching Rule:
   - 5 dakika içinde 15+ başarısız giriş
   - Aynı IP'den farklı kullanıcı adları
   - Gece saatleri aktivite (00:00-06:00)

3️⃣ Otomatik Eylem:
   - IP blokla
   - Security team'e bildir
   - Incident log oluştur

4️⃣ Alarm Örneği:
   IP: 192.168.1.200
   47 başarısız giriş (5 dakika)
   15 farklı kullanıcı adı denendi
   Otomatik bloklandı: ✅
```

---

## Sorun Giderme

### Yaygın Problemler ve Çözümleri

**1. Veri Kaynağı Bağlantı Hatası**
```
❌ Problem: "Database connection failed"
✅ Çözüm:
   1. Bağlantı bilgilerini kontrol edin
   2. Sunucu erişimini test edin: ping [IP]
   3. Port açık mı kontrol edin: telnet [IP] [PORT]
   4. Kullanıcı izinlerini doğrulayın
   5. SSL ayarlarını kontrol edin

🔍 Debug Adımları:
   - Admin → System Health → Database Status
   - Connection Test butonunu kullanın
   - Log dosyalarını inceleyin
```

**2. Kural Çalışmıyor**
```
❌ Problem: Rule hiç tetiklenmiyor veya hatalı sonuç veriyor
✅ Çözüm:
   1. Rule durumunu kontrol edin (Active/Inactive)
   2. Veri mapping'lerini doğrulayın
   3. Threshold değerlerini gözden geçirin
   4. Test data ile manuel çalıştırın

🔍 Debug Adımları:
   - Rule Detail → Test Run
   - Veri önizlemesini kontrol edin
   - Rule execution logs'ları inceleyin
```

**3. AI Model Performans Düşüklüğü**
```
❌ Problem: Model accuracy %70'in altına düştü
✅ Çözüm:
   1. Model drift analizi yapın
   2. Training data'yı güncelleyin
   3. Feature engineering gözden geçirin
   4. Hyperparameter tuning yapın

🔍 Debug Adımları:
   - Admin → AI/ML Performance
   - Model retraining başlatın
   - Data distribution changes kontrol edin
```

**4. Alarm Bildirimleri Gelmiyor**
```
❌ Problem: E-posta bildirimleri gönderilmiyor
✅ Çözüm:
   1. SMTP ayarlarını kontrol edin
   2. Kullanıcı bildirim tercihlerini doğrulayın
   3. Spam klasörünü kontrol edin
   4. E-posta sunucu loglarını inceleyin

🔍 Debug Adımları:
   - Profile → Notification Settings
   - Test e-mail gönder
   - System → Email Logs kontrol et
```

**5. Sistem Performans Problemleri**
```
❌ Problem: Dashboard yavaş yükleniyor, timeout hataları
✅ Çözüm:
   1. CPU/Memory kullanımını kontrol edin
   2. Database query performansını optimize edin
   3. Background job'ları yeniden başlatın
   4. Log dosyalarını temizleyin

🔍 Debug Adımları:
   - Admin → System Health
   - Database → Query Performance
   - Background scheduler durumunu kontrol et
```

### Log Dosyaları ve İzleme

**Log Lokasyonları:**
```
📁 /logs/
├── application.log      (Genel uygulama logları)
├── scheduler.log        (Background job logları)
├── rule_execution.log   (Kural çalıştırma logları)
├── ai_ml.log           (AI/ML model logları)
├── security.log        (Güvenlik olayları)
└── error.log           (Hata logları)
```

**Log Seviyesi Ayarlama:**
```python
# development: DEBUG seviyesi
# production: INFO seviyesi
# critical systems: ERROR seviyesi

LOG_LEVEL = "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

**Önemli Log Mesajları:**
```
🟢 INFO: Rule executed successfully - duration: 2.3s
🟡 WARNING: High CPU usage detected - 85%
🔴 ERROR: Database connection timeout
🔵 DEBUG: AI model prediction - confidence: 0.87
```

### Performans Optimizasyonu

**Database Optimizasyonu:**
```
1. Index Tanımları:
   CREATE INDEX idx_transactions_date ON transactions(transaction_date);
   CREATE INDEX idx_alarms_severity ON alarms(severity);

2. Query Optimization:
   - LIMIT kullanın büyük sonuç setlerinde
   - WHERE clause'larda index'li alanları kullanın
   - JOIN'lerde PRIMARY KEY kullanın

3. Connection Pooling:
   - Min pool size: 5
   - Max pool size: 20
   - Idle timeout: 300 seconds
```

**Memory Optimizasyonu:**
```
1. Python Memory Settings:
   - Garbage collection tuning
   - Memory profiling aktivasyon
   - Large dataset'lerde chunking kullanın

2. Cache Optimization:
   - Redis cache for session data
   - Database query result caching
   - Static file caching
```

**AI/ML Model Optimizasyonu:**
```
1. Model Size Reduction:
   - Feature selection
   - Model pruning
   - Quantization

2. Batch Processing:
   - Large dataset'lerde chunk processing
   - Asynchronous model execution
   - Result caching
```

---

## İletişim ve Destek

### Sistem Yöneticisi İletişim
```
📧 E-posta: admin@auditai.com
📞 Telefon: +90 (212) 555-0100
🕐 Çalışma Saatleri: 09:00-18:00 (Hafta içi)
🆘 Acil Durum: 7/24 on-call support
```

### Dokümantasyon Kaynakları
```
📚 Teknik Dokümantasyon: /docs/technical/
📖 Kullanıcı Kılavuzları: /docs/user-guides/
🤖 AI/ML Dokümantasyonu: /docs/ai-ml/
🔧 API Dokümantasyonu: /docs/api/
```

### Güncellemeler ve Bakım
```
🔄 Sistem Güncellemeleri: Aylık 1. Pazar günü
⏰ Bakım Penceresi: 02:00-04:00 (Gece)
📢 Duyurular: Dashboard üzerinden bildirilir
📋 Değişiklik Geçmişi: CHANGELOG.md dosyası
```

---

**Son Güncelleme:** 26 Ocak 2025  
**Versiyon:** 2.1.0  
**Hazırlayan:** AuditAI Development Team

---

*Bu kılavuz, AuditAI sisteminin tüm özelliklerini kapsamaktadır. Herhangi bir sorunuz veya öneriniz için sistem yöneticinizle iletişime geçebilirsiniz.*
