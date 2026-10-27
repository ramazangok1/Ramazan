# Backtest sonuçları

Veri: İngiltere Premier Lig, 2010-08-14 – 2020-07-26, 3800 maç. Değerlendirilen: 3344 maç (ısınma sonrası, her iki takımın en az 10 önceki maçı var). Walk-forward: her maç yalnızca öncesindeki verilerle tahmin edildi.

| Model | Doğruluk 1X2 | Log loss ↓ | Brier ↓ | RPS ↓ | 2.5 Üst doğr. | 2.5 Üst log loss ↓ | KG doğr. | KG log loss ↓ |
|---|---|---|---|---|---|---|---|---|
| 1) Taban: genel ortalama | 48.6% | 1.0518 | 0.6281 | 0.2232 | 53.2% | 0.7070 | 51.6% | 0.7043 |
| 2) + iç saha/deplasman | 52.5% | 1.0010 | 0.5933 | 0.2062 | 52.7% | 0.7257 | 50.6% | 0.7262 |
| 3) + form (mevcut üretim) | 52.7% | 1.0031 | 0.5938 | 0.2064 | 52.7% | 0.7276 | 50.9% | 0.7270 |
| 4) üretim + daraltma (k=10) | 52.8% | 0.9870 | 0.5870 | 0.2034 | 53.1% | 0.6967 | 51.1% | 0.7005 |
| 5) iç saha/dep. + daraltma, formsuz | 52.6% | 0.9902 | 0.5894 | 0.2045 | 53.3% | 0.6961 | 51.4% | 0.7006 |
| 6) üretim + toplam gol daraltması (β=0.4) | 52.8% | 0.9870 | 0.5870 | 0.2034 | 54.3% | 0.6882 | 52.4% | 0.6935 |
| R1) Lig sonuç frekansı | 45.7% | 1.0642 | 0.6429 | 0.2302 | 53.3% | 0.6914 | 51.3% | 0.6934 |

R1 referansı: o ana kadarki lig sonuç/2.5 üst/KG frekanslarını söyler. Bir model bu satırı geçmiyorsa o pazarda gerçek sinyali yoktur.

## Kalibrasyon: ev galibiyeti — 4) üretim + daraltma (k=10)

| Tahmin aralığı | Maç | Ortalama tahmin | Gerçekleşen |
|---|---|---|---|
| 10–20% | 124 | 16.5% | 25.8% |
| 20–30% | 417 | 25.4% | 20.9% |
| 30–40% | 744 | 35.3% | 34.0% |
| 40–50% | 802 | 44.9% | 44.8% |
| 50–60% | 648 | 54.6% | 53.9% |
| 60–70% | 377 | 64.5% | 70.8% |
| 70–80% | 185 | 74.0% | 79.5% |
| 80–90% | 41 | 83.5% | 85.4% |
