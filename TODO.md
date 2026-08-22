# AuditAI Delivery Roadmap

This roadmap tracks the path from the functional portfolio prototype to a deployable automated-control platform. Items are considered complete only when implementation, validation, documentation and security checks are present.

## P0 — Functional foundation

- [x] Persistent SQLite domain model
- [x] Interactive rule creation and execution
- [x] Alert generation and lifecycle management
- [x] Health endpoint and integration tests
- [x] Python 3.11/3.12 continuous integration

## P1 — Data ingestion

- [x] Upload CSV and Excel workbooks with file-size/type validation
- [x] Preview sheets, columns, inferred types and sample rows
- [x] Persist normalized source metadata without storing credentials in source control
- [x] Connect to a local SQLite database through a read-only restricted adapter
- [x] Connect to named PostgreSQL source profiles through a read-only restricted adapter
- [x] Add SQLite schema and table discovery
- [x] Map discovered source columns to rule fields
- [x] Record ingestion counts, timestamps, failures and validation errors
- [x] Prevent unsafe paths and uncontrolled SQL identifiers

## P1 — Control engine

- [x] Numeric comparison rules
- [x] Text equality and containment rules
- [x] Null/completeness rules
- [x] Date-age and date comparison rules
- [x] Duplicate and composite-key rules
- [x] Cross-field comparison rules
- [x] Validate rule definitions before execution
- [x] Cap affected-record samples while retaining total match counts
- [x] Record execution timestamps, scanned rows, matches and errors

## P1 — Automation

- [x] Manual and scheduled execution through the same service
- [x] Interval-based schedules callable by cron/worker
- [x] Disable, resume and inspect schedules through the scheduler service
- [x] Prevent overlapping executions of the same rule
- [x] Persist last/next run and failure state
- [x] Add retry and timeout policies

## P1 — Identity and accountability

- [x] Secure login and logout
- [x] Password hashing and minimum password policy
- [x] Administrator, auditor and viewer roles
- [x] Route- and action-level authorization
- [x] Append-only audit events for security-sensitive actions
- [x] Secure session-cookie defaults
- [x] Safe CLI administrator bootstrap flow

## P2 — Reporting and notifications

- [x] Filterable execution and alert history
- [x] CSV audit-evidence export
- [x] Management summary report
- [x] Notification abstraction with a persistent in-app implementation
- [x] Email/webhook adapters configured only through environment secrets
- [x] Delivery status and retry tracking

## P2 — Production readiness

- [x] Database migrations
- [x] PostgreSQL deployment profile
- [x] Structured application logging
- [x] Rate limiting and request-size limits
- [x] Dependency and secret scanning
- [x] Backup and recovery runbook
- [x] Load and large-dataset tests
- [x] Container image and non-root runtime
- [ ] Hosted privacy-safe demonstration

## P0 — Yerel ürün tamamlama (aktif çalışma)

Uygulama sırası: **P0 veri sürekliliği → P0 alarm/bildirim operasyonları → P1 risk analitiği → P1 arayüz ve dil → P0 uçtan uca kabul testi**.

### Veri ve eşleme — sorumlu: data_ingestion

- [x] Kayıtlı alan eşlemelerini gerçek verilere uygulayan dönüşüm servisi
- [x] Eşleme önizlemesi ve satır/alan bazlı dönüşüm hata raporu
- [x] Kural motorunun standartlaştırılmış hedef alanları kullanması
- [x] CSV/XLSX kaynaklarını sürüm ve checksum ile güvenli biçimde yenileme
- [x] SQLite/PostgreSQL bağlantı testi, tablo seçimi ve önizleme akışının tamamlanması

### Kural ve otomasyon — sorumlu: rule_scheduler

- [x] Kuralları düzenleme, silme, etkinleştirme ve durdurma işlemleri
- [x] Zamanlama sıklığı ile son/sonraki çalışma bilgisinin yönetimi
- [x] Yerel scheduler/worker süreçlerini tek komutla başlatma
- [x] Çakışan çalışma, hata ve yeniden deneme durumlarının arayüze açılması

### Alarm, risk ve raporlama — sorumlu: security_reporting

- [x] Alarm sorumlusu, denetçi notları ve durum zaman çizelgesi
- [x] Alarm sorumlusu seçimi için rol kontrollü kullanıcı listesi
- [x] Önem seviyesi/kanal/alıcı bazlı bildirim politikaları ve test gönderimi
- [ ] Alarmdan ilgili kaynak, kural ve çalıştırmaya izlenebilir geçiş
- [x] Risk skoru bileşenleri ve dönemsel karşılaştırma verisi
- [x] Tarih/denetim alanı filtreli yönetim raporu ve denetim kanıt paketi

### Arayüz ve bütünleştirme — sorumlu: ana ajan

- [x] Veri bağlantısı, eşleme, kural, alarm ve rapor ekranlarını yönlendirmeli akışlara dönüştürme
- [x] Kalite kontrollerini düzenleme, silme ve devre dışı bırakma
- [x] Bildirim politikası ve test bildirimi ayar ekranı
- [x] Tüm statik/dinamik arayüz metinlerini Türkçeleştirme
- [x] Mobil görünüm, boş durumlar, hata mesajları ve erişilebilirlik kontrolü
- [x] Uçtan uca yerel senaryo: kaynak → eşleme → kalite → kural → çalışma → alarm → rapor

## Definition of done

Every completed capability must include automated tests, error handling, safe defaults, updated documentation and a reproducible local verification command. Production or confidential data must never be committed.

## Sentetik kurumsal veri ortamı

- [x] SAP benzeri şirket kodu, maliyet merkezi, belge, personel, tedarikçi ve sipariş ilişkileri
- [x] İK, finans ve satın alma için üç bağımsız SQLite veritabanı
- [x] Sekiz tabloyu AuditAI veri kaynağı olarak kaydetme
- [x] Kontrollü bordro, yevmiye, görevler ayrılığı, mükerrer fatura ve fiyat farkı senaryoları
- [x] Altı çalışabilir denetim kuralı ve üç veri kalitesi kontrolü
- [x] Sabit seed, sentetik veri işareti, veri sözlüğü ve otomatik üretici testleri
- [x] Kart geçişi, çekirdek saat izin uyumu ve mesai dışı çalışma onayı verileri
- [x] Yıllık izin eksi bakiye belgesi ve terfi uygunluğu kontrol verileri
- [x] SAP benzeri SAT/SAS, teklif, onay limiti, kabul ve üçlü eşleşme kontrol verileri
