"""Kullanim:
  python3 tahmin.py veri.csv "Arsenal" "Chelsea"      # tek mac
  python3 tahmin.py veri.csv fikstur.csv              # fikstur.csv: home,away
"""
import sys, pandas as pd
from model import DixonColes, yukle

def yaz(ev, dep, t):
    print(f"\n{ev} - {dep}")
    print(f"  Beklenen gol: {t['ev_beklenen_gol']:.2f} - {t['dep_beklenen_gol']:.2f}")
    print(f"  1 / X / 2   : %{100*t['ev_kazanir']:.0f} / %{100*t['beraberlik']:.0f} / %{100*t['dep_kazanir']:.0f}")
    print(f"  Gol         : 1.5 ust %{100*t['1.5_ust']:.0f} | 2.5 ust %{100*t['2.5_ust']:.0f} | 3.5 ust %{100*t['3.5_ust']:.0f}")
    print(f"  Karsilikli gol: var %{100*t['kg_var']:.0f} / yok %{100*t['kg_yok']:.0f}")
    print(f"  En olasi skor: {t['en_olasi_skor']} (%{100*t['en_olasi_skor_p']:.0f})")

if __name__ == "__main__":
    m = DixonColes().fit(yukle(sys.argv[1]))
    if len(sys.argv) == 4:
        yaz(sys.argv[2], sys.argv[3], m.tahmin(sys.argv[2], sys.argv[3]))
    else:
        for _, r in pd.read_csv(sys.argv[2]).iterrows():
            try: yaz(r["home"], r["away"], m.tahmin(r["home"], r["away"]))
            except KeyError as e: print(f"\n{r['home']} - {r['away']}: {e}")
