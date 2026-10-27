# Futbol Analiz

Maç öncesi ve canlı futbol analizi yapan küçük web uygulaması.

## Çalıştırma
```bash
pip install -r requirements.txt
python server.py            # http://localhost:8000  (demo veri)
APIFOOTBALL_KEY=xxxx python server.py   # api-football.com (istatistik, sakatlık, oran dahil)
FOOTBALL_DATA_KEY=xxxx python server.py # football-data.org (skor, puan durumu, H2H)
```

## Neler var
- **Canlı maçlar**: skor, dakika, şut/korner/topla oynama, kırmızı kart, 5 sn'de bir yenilenir
- **Canlı olasılıklar**: kalan süre + mevcut skor + kırmızı kart + isabetli şut baskısına göre 1-X-2, 2.5 üst/alt, KG var/yok, olası skorlar
- **Maç öncesi analiz**: takımların gol ortalaması ve formuna göre Poisson modeli, H2H geçmişi

- **Lig filtresi**: maç listesinde ligine göre süzme
- **Toplam gol daraltması**: 2.5 üst/alt ve KG, toplam beklenen golü lig ortalamasına çekerek hesaplanır (aşırı iddialılığı giderir)
- **Daraltma**: az maçla hesaplanan ortalamalar lig ortalamasına doğru çekilir (maç öncesi ve canlı model; backtest ile doğrulandı)
- **İç saha / deplasman ayrımı**: ev avantajı takımların kendi iç saha/deplasman gol ortalamalarından gelir
- **Sakatlıklar**: eksik forvet/orta saha/defans/kaleci modelin hücum-savunma gücünü düşürür (API-Football)
- **Oranlar**: bahisçi marjı çıkarılmış piyasa olasılığı ile model karşılaştırması (API-Football)

## Ücretsiz kullanım
**1) Hiçbir hesap olmadan:** `python server.py` demo veriyle çalışır; tarayıcı sürümü de ücretsizdir.

**2) Gerçek veri, ücretsiz planlarla**
- *API-Football* ücretsiz plan (api-football.com, kayıt gerekir): günde 100 istek. Tüm özellikler (istatistik, sakatlık, oran) bu kaynakta.
  Kotayı korumak için yanıtlar önbelleğe alınır; `CANLI_TTL=300 GUNLUK_LIMIT=90 APIFOOTBALL_KEY=... python server.py` önerilir.
- *football-data.org* ücretsiz plan: dakikada 10 istek, sınırlı lig seti; yalnızca skor, puan durumu ve H2H gelir.
- Hangi liglerin/sezonların ücretsiz planda açık olduğunu kendi hesabında kontrol et; planlar değişebilir.

**3) Ücretsiz barındırma (Render.com):** depo kökündeki `render.yaml` hazır.
Render'da hesap aç → *New → Blueprint* → bu depoyu seç → (isteğe bağlı) API anahtarını `APIFOOTBALL_KEY` olarak gir.
Anahtar girmezsen sunucu demo veriyle açılır. Ücretsiz örnek, bir süre kullanılmayınca uyur ve ilk açılış ~1 dk sürebilir.
Sunucu herkese açık olacağı için `GUNLUK_LIMIT` ayarı anahtarının kotasını korur.

## Backtest
```bash
python backtest.py --lig tr.1   # Süper Lig; veriyi indirir (github), BACKTEST_tr.1.md yazar
python backtest.py --lig eng.1  # diğer kodlar: de.1, es.1, it.1, fr.1, nl.1, pt.1 ...
```
2010-11 – 2023-24 sezonlarında walk-forward test. Sonuçlar: `BACKTEST_tr.1.md`, `BACKTEST_eng.1.md`, `BACKTEST_cok_lig.md`.
Özet: 1X2 ve 2.5 üst/alt tahmini 8 ligin hepsinde referansı geçiyor; karşılıklı gol (KG) tahmininde güvenilir sinyal yok.

## Dosyalar
- `analysis.py` – olasılık modeli
- `backtest.py` – geçmiş maç testi
- `provider.py` – veri kaynakları (demo + API-Football)
- `server.py` – HTTP sunucu, `static/index.html` – arayüz

Not: API-Football ve football-data.org bağlantıları gerçek anahtarla test edilmedi; model basit bir istatistik tahminidir.
