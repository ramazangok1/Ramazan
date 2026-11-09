"""Modeli gecmise karsi sinar: her maci SADECE o gune kadar olan veriyle tahmin eder.
Kiyas: ligin ortalama oranlarini kullanan basit tahmin. Metrik: log-loss (dusuk iyi)."""
import sys, numpy as np
from model import DixonColes, yukle

def main(yol, son=150, adim=25):
    df = yukle(yol); test = df.iloc[-son:]; e = []
    for s in range(0, len(test), adim):
        parca = test.iloc[s:s+adim]
        egitim = df[df["date"] < parca["date"].min()]
        m = DixonColes().fit(egitim)
        for _, r in parca.iterrows():
            try: t = m.tahmin(r["home"], r["away"])
            except KeyError: continue
            e.append((t, int(r["hg"]), int(r["ag"])))
    pr = lambda p: np.clip(p, 1e-6, 1)
    def ll(ps, k): return -np.log(pr(ps[k]))
    cm = lambda hg, ag: 0 if hg > ag else (1 if hg == ag else 2)
    # baseline: egitim verisindeki oranlar
    g = df.iloc[:-son]; base = [np.mean(g.hg > g.ag), np.mean(g.hg == g.ag), np.mean(g.hg < g.ag)]
    bo = np.mean(g.hg + g.ag > 2.5); bk = np.mean((g.hg > 0) & (g.ag > 0))
    m1 = [ll([t["ev_kazanir"], t["beraberlik"], t["dep_kazanir"]], cm(h, a)) for t, h, a in e]
    b1 = [ll(base, cm(h, a)) for _, h, a in e]
    m2 = [-np.log(pr(t["2.5_ust"] if h + a > 2.5 else t["2.5_alt"])) for t, h, a in e]
    b2 = [-np.log(pr(bo if h + a > 2.5 else 1 - bo)) for _, h, a in e]
    m3 = [-np.log(pr(t["kg_var"] if h > 0 and a > 0 else t["kg_yok"])) for t, h, a in e]
    b3 = [-np.log(pr(bk if h > 0 and a > 0 else 1 - bk)) for _, h, a in e]
    acc = np.mean([np.argmax([t["ev_kazanir"], t["beraberlik"], t["dep_kazanir"]]) == cm(h, a) for t, h, a in e])
    print(f"Test maci: {len(e)}")
    print(f"{'Pazar':14}{'Model':>9}{'Basit':>9}   (log-loss, dusuk iyi)")
    for ad, a, b in [("1/X/2", m1, b1), ("2.5 ust/alt", m2, b2), ("Karsilikli gol", m3, b3)]:
        print(f"{ad:14}{np.mean(a):>9.4f}{np.mean(b):>9.4f}")
    print(f"En olasi sonucu secme isabeti (1/X/2): %{100*acc:.1f}")

if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 150)
