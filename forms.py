from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, BooleanField, PasswordField, FloatField, HiddenField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
from wtforms.widgets import TextArea
from models import Role, AuditArea

class LoginForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired(message='Kullanıcı adı gereklidir')])
    password = PasswordField('Şifre', validators=[DataRequired(message='Şifre gereklidir')])

class RegisterForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[
        DataRequired(message='Kullanıcı adı gereklidir'),
        Length(min=3, max=64, message='Kullanıcı adı 3-64 karakter arasında olmalıdır')
    ])
    email = StringField('E-posta', validators=[
        DataRequired(message='E-posta gereklidir'),
        Email(message='Geçerli bir e-posta adresi giriniz')
    ])
    first_name = StringField('Ad', validators=[
        DataRequired(message='Ad gereklidir'),
        Length(max=64)
    ])
    last_name = StringField('Soyad', validators=[
        DataRequired(message='Soyad gereklidir'),
        Length(max=64)
    ])
    password = PasswordField('Şifre', validators=[
        DataRequired(message='Şifre gereklidir'),
        Length(min=6, message='Şifre en az 6 karakter olmalıdır')
    ])
    password2 = PasswordField('Şifre Tekrar', validators=[
        DataRequired(message='Şifre tekrarı gereklidir'),
        EqualTo('password', message='Şifreler eşleşmiyor')
    ])
    role_id = SelectField('Rol', coerce=int, validators=[DataRequired(message='Rol seçimi gereklidir')])

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.role_id.choices = [(r.id, r.description) for r in Role.query.all()]

class AuditAreaForm(FlaskForm):
    name = StringField('Alan Adı', validators=[
        DataRequired(message='Alan adı gereklidir'),
        Length(max=128, message='Alan adı 128 karakterden fazla olamaz')
    ])
    description = TextAreaField('Açıklama', validators=[Optional()])
    is_active = BooleanField('Aktif', default=True)

class DataSourceForm(FlaskForm):
    name = StringField('Veri Kaynağı Adı', validators=[
        DataRequired(message='Veri kaynağı adı gereklidir'),
        Length(max=128)
    ])
    source_type = SelectField('Kaynak Türü', choices=[
        ('database', 'Veritabanı'),
        ('file', 'Dosya'),
        ('api', 'API'),
        ('sap', 'SAP')
    ], validators=[DataRequired(message='Kaynak türü seçimi gereklidir')])
    connection_string = TextAreaField('Bağlantı Bilgisi', validators=[Optional()])
    audit_area_id = SelectField('Audit Alanı', coerce=int, validators=[DataRequired(message='Audit alanı seçimi gereklidir')])

    def __init__(self, *args, **kwargs):
        super(DataSourceForm, self).__init__(*args, **kwargs)
        self.audit_area_id.choices = [(a.id, a.name) for a in AuditArea.query.filter_by(is_active=True).all()]

class DataMappingForm(FlaskForm):
    source_field = StringField('Kaynak Alan', validators=[
        DataRequired(message='Kaynak alan gereklidir'),
        Length(max=128)
    ])
    target_field = StringField('Hedef Alan', validators=[
        DataRequired(message='Hedef alan gereklidir'),
        Length(max=128)
    ])
    field_type = SelectField('Alan Türü', choices=[
        ('string', 'Metin'),
        ('integer', 'Tam Sayı'),
        ('float', 'Ondalık Sayı'),
        ('date', 'Tarih'),
        ('datetime', 'Tarih-Saat'),
        ('boolean', 'Boolean'),
        ('text', 'Uzun Metin')
    ], validators=[DataRequired(message='Alan türü seçimi gereklidir')])
    is_required = BooleanField('Zorunlu Alan', default=False)
    submit = SubmitField('Eşleştirme Oluştur')

class AuditRuleForm(FlaskForm):
    name = StringField('Kural Adı', validators=[
        DataRequired(message='Kural adı gereklidir'),
        Length(max=128)
    ])
    description = TextAreaField('Açıklama', validators=[Optional()])
    rule_type = SelectField('Kural Türü', choices=[
        ('threshold', 'Eşik Değer Kontrolü'),
        ('anomaly', 'Anomali Tespiti'),
        ('fraud_detection', 'Dolandırıcılık Tespiti'),
        ('time_series', 'Zaman Serisi Analizi'),
        ('security', 'Güvenlik Kontrolü'),
        ('compliance', 'Uyumluluk Kontrolü'),
        ('system_monitoring', 'Sistem İzleme')
    ], validators=[DataRequired(message='Kural türü seçimi gereklidir')])
    algorithm = SelectField('Algoritma', choices=[
        ('', 'Algoritma Seçin (İsteğe Bağlı)'),
        ('isolation_forest', 'Isolation Forest (Anomali)'),
        ('autoencoder', 'Autoencoder (Anomali)'),
        ('one_class_svm', 'One-Class SVM (Anomali)'),
        ('random_forest', 'Random Forest (Sınıflandırma)'),
        ('gradient_boosting', 'Gradient Boosting (Sınıflandırma)'),
        ('statistical_anomaly', 'İstatistiksel Anomali'),
        ('pattern_matching', 'Pattern Eşleştirme'),
        ('prophet', 'Prophet (Zaman Serisi)'),
        ('arima', 'ARIMA (Zaman Serisi)'),
        ('lstm', 'LSTM (Zaman Serisi)')
    ])
    condition = TextAreaField('Koşul', validators=[
        DataRequired(message='Koşul gereklidir')
    ], render_kw={'placeholder': 'Örnek: amount > 1000 veya user_count < 5'})
    threshold_value = FloatField('Eşik Değeri', validators=[Optional()])
    sensitivity = FloatField('Hassasiyet (0.0-1.0)', default=0.5, 
                            render_kw={'min': '0', 'max': '1', 'step': '0.1'})
    confidence_threshold = FloatField('Güven Eşiği (0.0-1.0)', default=0.8,
                                     render_kw={'min': '0', 'max': '1', 'step': '0.1'})
    risk_category = SelectField('Risk Kategorisi', choices=[
        ('', 'Kategori Seçin (İsteğe Bağlı)'),
        ('financial', 'Finansal'),
        ('security', 'Güvenlik'),
        ('operational', 'Operasyonel'),
        ('compliance', 'Uyumluluk')
    ])
    execution_frequency = SelectField('Çalışma Sıklığı', choices=[
        ('real_time', 'Gerçek Zamanlı'),
        ('hourly', 'Saatlik'),
        ('daily', 'Günlük'),
        ('weekly', 'Haftalık')
    ], default='hourly', validators=[DataRequired()])
    training_data_range = IntegerField('Eğitim Veri Aralığı (Gün)', default=30,
                                      render_kw={'min': '7', 'max': '365'})
    severity = SelectField('Önem Derecesi', choices=[
        ('low', 'Düşük'),
        ('medium', 'Orta'),
        ('high', 'Yüksek'),
        ('critical', 'Kritik')
    ], default='medium')
    audit_area_id = SelectField('Audit Alanı', coerce=int, validators=[DataRequired(message='Audit alanı seçimi gereklidir')])
    primary_data_source_id = SelectField('Ana Veri Kaynağı', coerce=int, validators=[Optional()])
    data_source_ids = SelectMultipleField('Veri Kaynakları (Çoklu Seçim)', coerce=int, validators=[Optional()])
    is_active = BooleanField('Aktif', default=True)
    submit = SubmitField('Kural Oluştur')

    def __init__(self, *args, **kwargs):
        super(AuditRuleForm, self).__init__(*args, **kwargs)
        self.audit_area_id.choices = [(a.id, a.name) for a in AuditArea.query.filter_by(is_active=True).all()]
        # Primary data source choices will be populated dynamically via AJAX
