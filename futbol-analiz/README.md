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

## Backtest
```bash
python backtest.py      # veriyi indirir (github), BACKTEST.md yazar
```
Premier Lig 2010-2020 (3800 maç) üzerinde walk-forward test; sonuçlar `BACKTEST.md` içinde.

## Dosyalar
- `analysis.py` – olasılık modeli
- `backtest.py` – geçmiş maç testi
- `provider.py` – veri kaynakları (demo + API-Football)
- `server.py` – HTTP sunucu, `static/index.html` – arayüz

Not: API-Football ve football-data.org bağlantıları gerçek anahtarla test edilmedi; model basit bir istatistik tahminidir.
