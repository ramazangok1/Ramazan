"""Dixon-Coles tarzi Poisson modeli: takim atak/savunma gucu + ic saha avantaji,
zaman agirlikli (yeni maclar daha onemli). Cikti: 1/X/2, toplam gol, KG var/yok."""
import numpy as np, pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

MAXG = 10

def yukle(yol):
    """football-data.co.uk (Date,HomeTeam,AwayTeam,FTHG,FTAG) ya da date,home,away,hg,ag."""
    df = pd.read_csv(yol)
    df = df.rename(columns={"Date": "date", "HomeTeam": "home", "AwayTeam": "away",
                            "FTHG": "hg", "FTAG": "ag"})
    df = df[["date", "home", "away", "hg", "ag"]].dropna()
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, format="mixed")
    return df.sort_values("date").reset_index(drop=True)

def _tau(x, y, lh, la, rho):
    t = np.ones_like(lh)
    t = np.where((x == 0) & (y == 0), 1 - lh * la * rho, t)
    t = np.where((x == 0) & (y == 1), 1 + lh * rho, t)
    t = np.where((x == 1) & (y == 0), 1 + la * rho, t)
    t = np.where((x == 1) & (y == 1), 1 - rho, t)
    return t

class DixonColes:
    def __init__(self, yarilanma_gun=365):
        self.xi = np.log(2) / yarilanma_gun

    def fit(self, df, bitis=None):
        bitis = bitis or df["date"].max()
        self.takimlar = sorted(set(df["home"]) | set(df["away"]))
        n = len(self.takimlar); idx = {t: i for i, t in enumerate(self.takimlar)}
        h = df["home"].map(idx).values; a = df["away"].map(idx).values
        x = df["hg"].values.astype(int); y = df["ag"].values.astype(int)
        w = np.exp(-self.xi * (bitis - df["date"]).dt.days.clip(lower=0).values)

        def nll(p):
            atk, dfn, ha, rho = p[:n], p[n:2*n], p[2*n], p[2*n+1]
            lh = np.exp(atk[h] + dfn[a] + ha); la = np.exp(atk[a] + dfn[h])
            ll = poisson.logpmf(x, lh) + poisson.logpmf(y, la) + np.log(np.maximum(_tau(x, y, lh, la, rho), 1e-9))
            pen = 1e-3 * (np.sum(atk**2) + np.sum(dfn**2))   # asiri ogrenmeyi onler
            return -(w * ll).sum() + pen
        p0 = np.concatenate([np.zeros(2*n), [0.25, -0.05]])
        cons = {"type": "eq", "fun": lambda p: p[:n].sum()}
        r = minimize(nll, p0, constraints=cons, method="SLSQP", options={"maxiter": 200})
        self.atk = dict(zip(self.takimlar, r.x[:n])); self.dfn = dict(zip(self.takimlar, r.x[n:2*n]))
        self.ha, self.rho = r.x[2*n], r.x[2*n+1]
        return self

    def matris(self, ev, dep):
        if ev not in self.atk or dep not in self.atk:
            raise KeyError(f"Bilinmeyen takim: {ev if ev not in self.atk else dep}")
        lh = np.exp(self.atk[ev] + self.dfn[dep] + self.ha); la = np.exp(self.atk[dep] + self.dfn[ev])
        g = np.arange(MAXG + 1)
        M = np.outer(poisson.pmf(g, lh), poisson.pmf(g, la))
        X, Y = np.meshgrid(g, g, indexing="ij")
        M = M * _tau(X, Y, lh, la, self.rho)
        return M / M.sum(), lh, la

    def tahmin(self, ev, dep):
        M, lh, la = self.matris(ev, dep)
        i, j = np.indices(M.shape)
        top = i + j
        return {
            "ev_beklenen_gol": lh, "dep_beklenen_gol": la,
            "ev_kazanir": M[i > j].sum(), "beraberlik": M[i == j].sum(), "dep_kazanir": M[i < j].sum(),
            "2.5_ust": M[top > 2.5].sum(), "2.5_alt": M[top < 2.5].sum(),
            "1.5_ust": M[top > 1.5].sum(), "3.5_ust": M[top > 3.5].sum(),
            "kg_var": M[(i > 0) & (j > 0)].sum(), "kg_yok": 1 - M[(i > 0) & (j > 0)].sum(),
            "en_olasi_skor": "%d-%d" % np.unravel_index(M.argmax(), M.shape),
            "en_olasi_skor_p": M.max(),
        }
