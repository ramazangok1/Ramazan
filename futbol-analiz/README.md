# Futbol Analiz

Maç öncesi ve canlı futbol analizi yapan küçük web uygulaması.

## Çalıştırma
```bash
pip install -r requirements.txt
python server.py            # http://localhost:8000  (demo veri)
APIFOOTBALL_KEY=xxxx python server.py   # gerçek veri (api-football.com)
```

## Neler var
- **Canlı maçlar**: skor, dakika, şut/korner/topla oynama, kırmızı kart, 5 sn'de bir yenilenir
- **Canlı olasılıklar**: kalan süre + mevcut skor + kırmızı kart + isabetli şut baskısına göre 1-X-2, 2.5 üst/alt, KG var/yok, olası skorlar
- **Maç öncesi analiz**: takımların gol ortalaması ve formuna göre Poisson modeli, H2H geçmişi

## Dosyalar
- `analysis.py` – olasılık modeli
- `provider.py` – veri kaynakları (demo + API-Football)
- `server.py` – HTTP sunucu, `static/index.html` – arayüz

Not: API-Football bağlantısı gerçek anahtarla test edilmedi; model basit bir istatistik tahminidir.
