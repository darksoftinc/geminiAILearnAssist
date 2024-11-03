# EğitimAI Platform

AI destekli eğitim platformu, Flask ve Gemini AI kullanılarak geliştirilmiştir.

## Özellikler

- 🤖 Gemini AI ile otomatik müfredat oluşturma
- 📚 Quiz yönetimi ve otomatik soru oluşturma
- 📊 Detaylı öğrenci performans analizi
- 🔔 Gerçek zamanlı bildirimler
- 📱 Responsive tasarım

## Kurulum

1. Repository'yi klonlayın
```bash
git clone https://github.com/KULLANICI_ADI/REPO_ADI.git
```

2. Gerekli paketleri yükleyin
```bash
pip install -r requirements.txt
```

3. .env dosyasını oluşturun ve gerekli API anahtarlarını ekleyin
4. Uygulamayı başlatın
```bash
python main.py
```

## Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun
3. Değişikliklerinizi commit edin
4. Branch'inizi push edin
5. Pull Request açın

## Gerekli API Anahtarları

Aşağıdaki API anahtarlarını `.env` dosyasına eklemelisiniz:

- `GEMINI_API_KEY`: Google Gemini AI API anahtarı
- `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_OAUTH_CLIENT_SECRET`: Google OAuth client secret
- `FLASK_SECRET_KEY`: Flask güvenlik anahtarı
- `DATABASE_URL`: PostgreSQL veritabanı bağlantı URL'i
