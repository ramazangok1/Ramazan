"""Milli takim maclari icin tahmin. Veri: uluslararasi.csv (martj42/international_results).
Kullanim: python3 ulus.py            -> asagidaki FIKSTUR icin tahmin
          python3 ulus.py backtest   -> son maclar uzerinde sinama"""
import sys, pandas as pd
from model import DixonColes, yukle
import backtest
from tahmin import yaz

BASLANGIC = "2022-01-01"          # eski maclar alakasiz
FIKSTUR = [("Turkey","Belgium"),("Italy","France"),("England","Croatia"),("Czech Republic","Spain"),
           ("San Marino","Belarus"),("Albania","Finland"),("Armenia","Cyprus"),("Montenegro","Latvia")]

def veri():
    df = yukle("uluslararasi.csv")
    df = df[df["date"] >= BASLANGIC]
    n = pd.concat([df["home"], df["away"]]).value_counts()
    return df[(df["home"].map(n) >= 6) & (df["away"].map(n) >= 6)].reset_index(drop=True)

if __name__ == "__main__":
    df = veri()
    if len(sys.argv) > 1 and sys.argv[1] == "backtest":
        df.to_csv("_ulus_gecici.csv", index=False)
        backtest.main("_ulus_gecici.csv", 200, 50)
    else:
        m = DixonColes(yarilanma_gun=730).fit(df)
        print(f"Egitim: {len(df)} mac, {len(m.takimlar)} takim, son veri {df['date'].max().date()}")
        for e, d in FIKSTUR:
            try: yaz(e, d, m.tahmin(e, d))
            except KeyError as x: print(f"\n{e} - {d}: {x}")
