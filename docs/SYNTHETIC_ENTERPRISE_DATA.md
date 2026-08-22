# Sentetik Kurumsal Veri Ortamı

Bu paket yalnızca geliştirme ve denetim demosu içindir. Tüm çalışanlar, tedarikçiler,
hesaplar ve işlemler deterministik olarak üretilir; gerçek kişi veya şirket verisi içermez.
Her tabloda `synthetic_flag=1` alanı bulunur.

## Veritabanları

| Dosya | Tablolar | Yaklaşık hacim | Ana ilişkiler |
|---|---|---:|---|
| `hr.db` | personel, bordro, zaman, kart geçişi, devam, izin, terfi | 11.000 | `employee_id`, şirket kodu, maliyet merkezi |
| `finance.db` | `gl_journal`, `payments` | 7.200 | belge no, tedarikçi, kullanıcı, şirket kodu |
| `procurement.db` | tedarikçi, SAT, SAS, sipariş, fatura, kabul/eşleşme | 8.500 | tedarikçi → SAT → SAS → kabul → fatura |

Dosyalar çalıştırma sırasında `instance/synthetic_enterprise/` altında üretilir ve on beş
ayrı AuditAI veri kaynağı olarak kaydedilir.

## Kontrollü denetim senaryoları

- Aynı banka hesabını kullanan çalışanlar
- İşten ayrılmış personele bordro ödemesi
- Aşırı fazla mesai ve dönem dışı bordro
- Çekirdek saatte kartla çıkıp izin bildirimi yapmama
- Mesai dışında ofiste kalıp yönetici onay belgesi oluşturmama
- Eksi yıllık izin bakiyesi formunu teslim etmeme
- Süresi ve performansı uygun olduğu halde terfi ettirilmeme
- Yüksek tutarlı manuel yevmiye ve hafta sonu kaydı
- Ödemeyi oluşturan ve onaylayan kullanıcının aynı olması
- Çalışanla ilişkili tedarikçi banka hesabı
- Onay limitinin hemen altında bölünmüş siparişler
- SAT olmadan SAS oluşturma ve geriye dönük SAT
- Zorunlu teklif sayısının altında satın alma
- Eksik SAS onayı ve onay limiti ihlali
- Mal/hizmet kabulü olmadan fatura ve üçlü eşleşme farkı
- Mükerrer fatura numarası
- Sipariş tutarını aşan fatura

Senaryolar `is_anomaly` gibi sonucu doğrudan ele veren bir alan yerine denetlenebilir iş
alanlarıyla temsil edilir. `synthetic_flag` yalnız veri kökenini açıkça belirtir.

## Yeniden üretme

```bash
python tools/generate_enterprise_demo.py
```

Üretici sabit seed kullanır. Aynı kod sürümünde aynı veri elde edilir. Mevcut gerçek veya
kullanıcı kaynaklarına dokunmaz; yalnız `Kurumsal ...` adlı sentetik kaynakları oluşturur
ya da günceller.
