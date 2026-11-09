"""Test icin yapay lig verisi uretir (gercek veri DEGIL)."""
import numpy as np, pandas as pd
rng = np.random.default_rng(0)
T = [f"Takim{i:02d}" for i in range(16)]
atk = dict(zip(T, rng.normal(0, .25, 16))); dfn = dict(zip(T, rng.normal(0, .2, 16)))
rows, d = [], pd.Timestamp("2024-08-01")
for tur in range(60):
    sirali = rng.permutation(T)
    for i in range(0, 16, 2):
        h, a = sirali[i], sirali[i+1]
        rows.append((d.strftime("%d/%m/%Y"), h, a,
                     rng.poisson(np.exp(.1 + .25 + atk[h] + dfn[a])), rng.poisson(np.exp(.1 + atk[a] + dfn[h]))))
    d += pd.Timedelta(days=4)
pd.DataFrame(rows, columns=["Date","HomeTeam","AwayTeam","FTHG","FTAG"]).to_csv("sentetik.csv", index=False)
