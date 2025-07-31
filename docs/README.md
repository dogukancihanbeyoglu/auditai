# AuditAI - Akıllı Denetim ve Uyumluluk Sistemi

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Latest-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AuditAI, kurumsal denetim süreçlerini otomatikleştirmek ve yapay zeka ile desteklemek için geliştirilmiş kapsamlı bir web uygulamasıdır.

## 🚀 Özellikler

- **Akıllı Denetim Yönetimi**: Otomatik denetim kuralları ve alarm sistemi
- **Yapay Zeka Entegrasyonu**: ML tabanlı anomali tespiti ve öngörü analizi
- **Çoklu Veri Kaynağı Desteği**: Farklı veri kaynaklarından otomatik veri çekme
- **Real-time Monitoring**: Gerçek zamanlı izleme ve alarm sistemi
- **Kapsamlı Raporlama**: Detaylı analiz ve raporlama araçları
- **Güvenli Kullanıcı Yönetimi**: Rol tabanlı erişim kontrolü

## 📋 Gereksinimler

- Python 3.8+
- Flask
- SQLAlchemy
- Pandas, NumPy (Veri analizi için)
- Scikit-learn (ML özellikleri için)

## 🛠️ Kurulum

1. Projeyi klonlayın:
```bash
git clone https://github.com/dogukancihanbeyoglu/auditai.git
cd auditai
```

2. Sanal ortam oluşturun ve aktifleştirin:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows
```

3. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
# veya
uv sync
```

4. Veritabanını başlatın:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

5. Uygulamayı çalıştırın:
```bash
python app.py
```

## 📊 Kullanım

1. Tarayıcınızda `http://localhost:5000` adresine gidin
2. İlk kullanım için admin hesabı oluşturun
3. Dashboard üzerinden denetim alanlarını ve kurallarını yapılandırın
4. Veri kaynaklarını bağlayın ve otomatik izleme başlatın

## 📁 Proje Yapısı

```
auditai/
├── src/                    # Ana kaynak kodlar
├── routes/                 # Flask route'ları
├── templates/              # HTML şablonları
├── static/                 # Statik dosyalar (CSS, JS)
├── tests/                  # Test dosyaları
├── docs/                   # Dokümantasyon
├── config/                 # Yapılandırma dosyaları
├── app.py                  # Ana uygulama dosyası
├── models.py               # Veritabanı modelleri
└── requirements.txt        # Python bağımlılıkları
```

## 🤖 Yapay Zeka Özellikleri

- **Anomali Tespiti**: Otomatik veri anomalisi tanımlama
- **Öngörü Analizi**: Gelecek trendler ve risk tahmini
- **Akıllı Kurallar**: Adaptif denetim kuralları
- **Otomatik Sınıflandırma**: Risk seviyesi belirleme

## 📖 Dokümantasyon

Detaylı kullanım kılavuzu ve teknik dokümantasyon için `/docs` klasörüne bakın:

- [Kapsamlı Kullanıcı Kılavuzu](docs/COMPLETE_USER_GUIDE.md)
- [Yapay Zeka Teknik Kılavuzu](docs/AI_ML_TECHNICAL_GUIDE.md)
- [Alarm Üretim Kılavuzu](docs/ALARM_GENERATION_GUIDE.md)

## 🧪 Test

Test çalıştırmak için:
```bash
python -m pytest tests/
```

Test verisi oluşturmak için:
```bash
python tests/create_test_data.py
```

## 🤝 Katkıda Bulunma

1. Bu projeyi fork edin
2. Özellik dalı oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Dalınıza push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 👨‍💻 Geliştirici

**Doğukan Cihan Beyoğlu**
- GitHub: [@dogukancihanbeyoglu](https://github.com/dogukancihanbeyoglu)
- LinkedIn: [Doğukan Cihanbeyoğlu](https://www.linkedin.com/in/dogukanc/)

## 📞 Destek

Herhangi bir sorun veya öneri için GitHub Issues kullanabilir veya doğrudan iletişime geçebilirsiniz.

---

⭐ Bu projeyi beğendiyseniz, lütfen yıldız verin!
