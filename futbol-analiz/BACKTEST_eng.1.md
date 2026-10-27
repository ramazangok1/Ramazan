# Backtest sonuçları: eng.1

Veri: eng.1, 2010-08-14 – 2024-05-19, 5320 maç. Değerlendirilen: 4824 maç (ısınma sonrası, her iki takımın en az 10 önceki maçı var). Walk-forward: her maç yalnızca öncesindeki verilerle tahmin edildi.

| Model | Doğruluk 1X2 | Log loss ↓ | Brier ↓ | RPS ↓ | 2.5 Üst doğr. | 2.5 Üst log loss ↓ | KG doğr. | KG log loss ↓ |
|---|---|---|---|---|---|---|---|---|
| 1) Taban: genel ortalama | 49.5% | 1.0462 | 0.6243 | 0.2223 | 54.1% | 0.7026 | 52.6% | 0.7003 |
| 2) + iç saha/deplasman | 52.3% | 1.0027 | 0.5943 | 0.2077 | 53.3% | 0.7216 | 51.7% | 0.7223 |
| 3) + form (mevcut üretim) | 52.4% | 1.0047 | 0.5948 | 0.2078 | 53.5% | 0.7236 | 51.6% | 0.7236 |
| 4) üretim + daraltma (k=10) | 53.2% | 0.9862 | 0.5865 | 0.2042 | 53.9% | 0.6940 | 51.4% | 0.6986 |
| 5) iç saha/dep. + daraltma, formsuz | 52.8% | 0.9896 | 0.5890 | 0.2054 | 53.7% | 0.6935 | 51.6% | 0.6984 |
| 6) üretim + toplam gol daraltması (β=0.4) | 53.2% | 0.9862 | 0.5865 | 0.2042 | 54.9% | 0.6864 | 53.0% | 0.6927 |
| R1) Lig sonuç frekansı | 45.2% | 1.0646 | 0.6435 | 0.2318 | 53.9% | 0.6904 | 51.9% | 0.6928 |

R1 referansı: o ana kadarki lig sonuç/2.5 üst/KG frekanslarını söyler. Bir model bu satırı geçmiyorsa o pazarda gerçek sinyali yoktur.

## Kalibrasyon: ev galibiyeti — 4) üretim + daraltma (k=10)

| Tahmin aralığı | Maç | Ortalama tahmin | Gerçekleşen |
|---|---|---|---|
| 10–20% | 228 | 16.4% | 20.2% |
| 20–30% | 647 | 25.4% | 20.9% |
| 30–40% | 1071 | 35.3% | 34.9% |
| 40–50% | 1132 | 44.9% | 45.5% |
| 50–60% | 882 | 54.6% | 54.6% |
| 60–70% | 537 | 64.5% | 69.8% |
| 70–80% | 254 | 74.1% | 79.9% |
| 80–90% | 61 | 83.5% | 83.6% |
