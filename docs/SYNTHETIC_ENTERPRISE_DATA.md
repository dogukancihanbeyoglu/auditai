# Sentetik Kurumsal Veri Ortamı

Bu paket yalnızca geliştirme ve denetim demosu içindir. Tüm çalışanlar, tedarikçiler,
hesaplar ve işlemler deterministik olarak üretilir; gerçek kişi veya şirket verisi içermez.
Her tabloda `synthetic_flag=1` alanı bulunur.

## Veritabanları

| Dosya | Tablolar | Yaklaşık hacim | Ana ilişkiler |
|---|---|---:|---|
| `hr.db` | `employees`, `payroll`, `time_entries` | 8.500 | `employee_id`, şirket kodu, maliyet merkezi |
| `finance.db` | `gl_journal`, `payments` | 7.200 | belge no, tedarikçi, kullanıcı, şirket kodu |
| `procurement.db` | `vendors`, `purchase_orders`, `invoices` | 3.700 | tedarikçi → sipariş → fatura |

Dosyalar çalıştırma sırasında `instance/synthetic_enterprise/` altında üretilir ve sekiz
ayrı AuditAI veri kaynağı olarak kaydedilir.

## Kontrollü denetim senaryoları

- Aynı banka hesabını kullanan çalışanlar
- İşten ayrılmış personele bordro ödemesi
- Aşırı fazla mesai ve dönem dışı bordro
- Yüksek tutarlı manuel yevmiye ve hafta sonu kaydı
- Ödemeyi oluşturan ve onaylayan kullanıcının aynı olması
- Çalışanla ilişkili tedarikçi banka hesabı
- Onay limitinin hemen altında bölünmüş siparişler
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
