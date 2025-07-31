# Alarm Başlık ve Mesaj Oluşturma Rehberi

## Yeni Kural Oluşturduğunuzda Ne Olur?

Sistemde yeni bir kural oluşturduğunuzda, alarm başlık ve mesajları **kural türüne** göre otomatik oluşturulur:

## 1. Anomali Tespiti (anomaly_detection)

**Alarm Başlığı:**
```
"Anomali Tespit Edildi: [KURAL ADINIZ]"
```

**Alarm Mesajı:**
```
"Güven seviyesi: %XX, Anomali skoru: X.XXX"
```

**Örnek:**
- Kural Adı: "Yüksek Miktarlı İşlemler"
- Başlık: "Anomali Tespit Edildi: Yüksek Miktarlı İşlemler"
- Mesaj: "Güven seviyesi: %85, Anomali skoru: 0.842"

## 2. Dolandırıcılık Tespiti (fraud_detection)

**Alarm Başlığı:**
```
"Dolandırıcılık Tespit Edildi: [TESPIT EDİLEN PATTERN]"
```

**Alarm Mesajı:**
```
"Risk skoru: %XX"
```

**Örnek:**
- Kural Adı: "Tedarikçi Sahte Faturalar"
- Başlık: "Dolandırıcılık Tespit Edildi: Sahte Fatura Pattern"
- Mesaj: "Risk skoru: %92"

## 3. Güvenlik (security)

**Alarm Başlığı:**
```
"Güvenlik Olayı: [OLAY TÜRÜ]"
```

**Alarm Mesajı:**
```
"Risk skoru: %XX"
```

**Örneğimiz:**
- Başlık: "Güvenlik Olayı: Şüpheli Giriş Denemesi"
- Mesaj: "Bilinmeyen IP adresinden çoklu başarısız giriş"

## 4. Sistem İzleme (system_monitoring)

**CPU Kuralları:**
- Başlık: "Yüksek CPU Kullanımı: [KURAL ADI]"
- Mesaj: "CPU kullanımı %XX (Eşik: %YY)"

**Bellek Kuralları:**
- Başlık: "Yüksek Bellek Kullanımı: [KURAL ADI]"
- Mesaj: "Bellek kullanımı %XX (Eşik: %YY)"

**Genel Sistem:**
- Başlık: "Beklenmedik Sistem Yükü: [KURAL ADI]"
- Mesaj: "Sistem yükü %XX (CPU: %YY, RAM: %ZZ)"

## 5. Eşik Tabanlı (threshold)

**Alarm Başlığı:**
```
"Eşik Aşıldı: [KURAL ADINIZ]"
```

**Alarm Mesajı:**
```
"Değer: [BULUNAN_DEĞER], Eşik: [EŞİK_DEĞER]"
```

## 6. Uyumluluk (compliance)

**Alarm Başlığı:**
```
"Uyumluluk İhlali: [KURAL ADINIZ]"
```

**Alarm Mesajı:**
```
"[İHLAL_AÇIKLAMASI]"
```

## Yeni Veritabanı Bağladığınızda Ne Olur?

1. **Veri Kaynağı Oluşturulur**: Sistem yeni veritabanını data_sources tablosuna ekler
2. **Kural Oluştururken**: Yeni veri kaynağını seçebilirsiniz
3. **Scheduler Kontrolü**: Her 5 dakikada bir kuralınız çalıştırılır
4. **Veri Analizi**: AI/ML motorları verilerinizi analiz eder
5. **Alarm Üretimi**: Anomali tespit edilirse yukarıdaki formatlarda alarm oluşur

## Önemli Notlar

- **Dinamik İçerik**: Alarm mesajları statik değil, tespit edilen anomaliye göre dinamik oluşur
- **Risk Skorları**: AI/ML algoritmaları gerçek risk skorları hesaplar
- **Veri Detayları**: Her alarmın `data` alanında JSON formatında detaylı bilgi saklanır
- **Önem Seviyeleri**: Risk skoruna göre otomatik olarak critical/high/medium/low belirlenir

## Örnek Senaryo

**Diyelim ki "Hafta Sonu İşlemleri" adında bir kural oluşturdunuz:**

1. **Kural Türü**: anomaly_detection
2. **Koşul**: weekend_transaction = true AND amount > 50000
3. **Sistem çalıştırdığında**:
   - Başlık: "Anomali Tespit Edildi: Hafta Sonu İşlemleri"
   - Mesaj: "Güven seviyesi: %78, Anomali skoru: 0.654"
   - Önem: high
   - Veri: {"anomaly_data": {"confidence": 0.78, "score": 0.654, "data_point": {...}}}

Bu şekilde her yeni kural için sistem otomatik olarak uygun başlık ve mesajları üretir!