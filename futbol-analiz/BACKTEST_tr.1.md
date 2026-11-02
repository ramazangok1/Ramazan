# Backtest sonuçları: tr.1

Veri: tr.1, 2010-08-14 – 2024-05-26, 4582 maç. Değerlendirilen: 4046 maç (ısınma sonrası, her iki takımın en az 10 önceki maçı var). Walk-forward: her maç yalnızca öncesindeki verilerle tahmin edildi.

| Model | Doğruluk 1X2 | Log loss ↓ | Brier ↓ | RPS ↓ | 2.5 Üst doğr. | 2.5 Üst log loss ↓ | KG doğr. | KG log loss ↓ |
|---|---|---|---|---|---|---|---|---|
| 1) Taban: genel ortalama | 44.4% | 1.0909 | 0.6581 | 0.2341 | 52.1% | 0.7109 | 50.9% | 0.7077 |
| 2) + iç saha/deplasman | 49.4% | 1.0396 | 0.6201 | 0.2156 | 52.2% | 0.7257 | 49.5% | 0.7237 |
| 3) + form (mevcut üretim) | 49.3% | 1.0404 | 0.6201 | 0.2155 | 52.4% | 0.7269 | 49.7% | 0.7237 |
| 4) üretim + daraltma (k=10) | 50.0% | 1.0179 | 0.6086 | 0.2104 | 52.5% | 0.6978 | 52.2% | 0.6968 |
| 5) iç saha/dep. + daraltma, formsuz | 50.0% | 1.0207 | 0.6107 | 0.2115 | 52.3% | 0.6971 | 52.2% | 0.6975 |
| 6) üretim + toplam gol daraltması (β=0.4) | 50.0% | 1.0179 | 0.6086 | 0.2104 | 52.9% | 0.6897 | 53.1% | 0.6903 |
| R1) Lig sonuç frekansı | 46.0% | 1.0637 | 0.6423 | 0.2266 | 52.9% | 0.6917 | 54.7% | 0.6891 |

R1 referansı: o ana kadarki lig sonuç/2.5 üst/KG frekanslarını söyler. Bir model bu satırı geçmiyorsa o pazarda gerçek sinyali yoktur.

## Kalibrasyon: ev galibiyeti — 4) üretim + daraltma (k=10)

| Tahmin aralığı | Maç | Ortalama tahmin | Gerçekleşen |
|---|---|---|---|
| 10–20% | 98 | 16.7% | 25.5% |
| 20–30% | 425 | 26.0% | 22.4% |
| 30–40% | 914 | 35.6% | 36.1% |
| 40–50% | 1144 | 44.9% | 46.0% |
| 50–60% | 888 | 54.5% | 54.6% |
| 60–70% | 420 | 64.3% | 69.3% |
| 70–80% | 134 | 74.1% | 73.9% |
