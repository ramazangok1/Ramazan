"""Geçmiş maçlarla walk-forward backtest.

Her maç yalnızca o tarihten ÖNCE oynanmış maçlarla tahmin edilir (veri sızıntısı yok).
Veri: github.com/footballcsv/england (sonuçlar; oran içermez).
Çalıştır: python backtest.py [--sezonlar 2010-11,2011-12,...] [--yaz BACKTEST.md]
"""
import argparse
import csv
import io
import os
from collections import defaultdict
from datetime import datetime
from math import log

import requests

import analysis

URL = "https://raw.githubusercontent.com/footballcsv/england/master/{on}/{sezon}/eng.1.csv"
SEZONLAR = [f"{y}-{str(y + 1)[2:]}" for y in range(2010, 2021)]
ONBELLEK = os.path.join(os.path.dirname(__file__), "veri_onbellek")
PENCERE, PENCERE_IC, MIN_MAC, ISINMA_LIG = 30, 15, 10, 300
EPS = 1e-9


def indir(sezon):
    os.makedirs(ONBELLEK, exist_ok=True)
    yol = os.path.join(ONBELLEK, f"eng1_{sezon}.csv")
    if not os.path.exists(yol):
        on = "2020s" if int(sezon[:4]) >= 2020 else "2010s"
        r = requests.get(URL.format(on=on, sezon=sezon), timeout=30)
        if r.status_code != 200:
            return None
        open(yol, "w", encoding="utf-8").write(r.text)
    return open(yol, encoding="utf-8").read()


def maclari_oku(sezonlar):
    maclar = []
    for s in sezonlar:
        metin = indir(s)
        if not metin:
            print(f"uyarı: {s} indirilemedi, atlandı")
            continue
        for r in csv.DictReader(io.StringIO(metin)):
            try:
                eg, dg = map(int, r["FT"].strip().split("-"))
                tarih = datetime.strptime(r["Date"].strip(), "%a %b %d %Y")
            except (ValueError, KeyError):
                continue
            maclar.append((tarih, r["Team 1"], r["Team 2"], eg, dg))
    maclar.sort(key=lambda m: m[0])
    return maclar


def ort(liste, i):
    return sum(x[i] for x in liste) / len(liste)


def takim_istatistik(gecmis, lig, ayar):
    """gecmis: [(ic_saha_mi, atilan, yenilen, sonuc)] eskiden yeniye."""
    son = gecmis[-PENCERE:]
    n = len(son)
    t = {"atilan": ort(son, 1), "yenilen": ort(son, 2), "form": [x[3] for x in son[-5:]]}
    if ayar.get("daralt"):
        t["n"] = n  # daraltmayı analysis.py uygular (üretimle aynı kod)
    if ayar.get("bol"):
        for ic, onek in ((True, "ev_"), (False, "dep_")):
            alt = [x for x in gecmis if x[0] == ic][-PENCERE_IC:]
            if len(alt) >= 5:
                m = len(alt)
                t[onek + "atilan"] = ort(alt, 1)
                t[onek + "yenilen"] = ort(alt, 2)
                if ayar.get("daralt"):
                    t[onek + "n"] = m
    return t


AYARLAR = {
    "1) Taban: genel ortalama": {"bol": False, "form": False, "daralt": False},
    "2) + iç saha/deplasman": {"bol": True, "form": False, "daralt": False},
    "3) + form (mevcut üretim)": {"bol": True, "form": True, "daralt": False},
    "4) üretim + daraltma (k=10)": {"bol": True, "form": True, "daralt": True},
    "5) iç saha/dep. + daraltma, formsuz": {"bol": True, "form": False, "daralt": True},
}


def tahmin(ev_t, dep_t, lig, ayar):
    if ayar["form"]:
        return analysis.mac_oncesi(ev_t, dep_t, lig)
    lam_e, lam_d = analysis.beklenen_goller(ev_t, dep_t, lig)
    return analysis.olasiliklar(lam_e, lam_d)


def sonuc_idx(eg, dg):
    return 0 if eg > dg else (1 if eg == dg else 2)


def metrikler(kayitlar):
    n = len(kayitlar)
    m = defaultdict(float)
    for p, (eg, dg) in kayitlar:
        pv = [p["ev"], p["beraberlik"], p["dep"]]
        y = sonuc_idx(eg, dg)
        m["ll"] -= log(max(pv[y], EPS))
        m["brier"] += sum((pv[i] - (i == y)) ** 2 for i in range(3))
        c1, c2 = pv[0], pv[0] + pv[1]
        o1, o2 = float(y == 0), float(y <= 1)
        m["rps"] += ((c1 - o1) ** 2 + (c2 - o2) ** 2) / 2
        m["acc"] += pv.index(max(pv)) == y
        u = float(eg + dg > 2)
        m["u_ll"] -= log(max(p["ust25"] if u else 1 - p["ust25"], EPS))
        m["u_acc"] += (p["ust25"] > 0.5) == bool(u)
        b = float(eg > 0 and dg > 0)
        m["b_ll"] -= log(max(p["kg_var"] if b else 1 - p["kg_var"], EPS))
        m["b_acc"] += (p["kg_var"] > 0.5) == bool(b)
    return {k: v / n for k, v in m.items()} | {"n": n}


def calistir(maclar):
    gecmis = defaultdict(list)
    lig_toplam = [0, 0, 0]  # ev golü, dep golü, maç sayısı
    sonuc_sayac = [0, 0, 0]
    kayit = defaultdict(list)
    for tarih, ev, dep, eg, dg in maclar:
        n_lig = lig_toplam[2]
        if (n_lig >= ISINMA_LIG and len(gecmis[ev]) >= MIN_MAC and len(gecmis[dep]) >= MIN_MAC):
            lig = (lig_toplam[0] / n_lig, lig_toplam[1] / n_lig)
            for ad, ayar in AYARLAR.items():
                kayit[ad].append((tahmin(takim_istatistik(gecmis[ev], lig, ayar),
                                         takim_istatistik(gecmis[dep], lig, ayar), lig, ayar), (eg, dg)))
            # Referans 1: lig frekansı. Referans 2: hep ev sahibi
            f = [c / n_lig for c in sonuc_sayac]
            kayit["R1) Lig sonuç frekansı"].append(
                ({"ev": f[0], "beraberlik": f[1], "dep": f[2], "ust25": 0.5, "kg_var": 0.5}, (eg, dg)))
        # sonra geçmişe ekle
        r = sonuc_idx(eg, dg)
        gecmis[ev].append((True, eg, dg, "GBM"[r]))
        gecmis[dep].append((False, dg, eg, "GBM"[2 - r]))
        lig_toplam[0] += eg
        lig_toplam[1] += dg
        lig_toplam[2] += 1
        sonuc_sayac[r] += 1
    return kayit


def kalibrasyon(kayitlar, anahtar="ev"):
    kovalar = defaultdict(lambda: [0, 0.0, 0])
    for p, (eg, dg) in kayitlar:
        k = min(int(p[anahtar] * 10), 9)
        kovalar[k][0] += 1
        kovalar[k][1] += p[anahtar]
        kovalar[k][2] += (eg > dg) if anahtar == "ev" else 0
    return [(k, v[0], v[1] / v[0], v[2] / v[0]) for k, v in sorted(kovalar.items()) if v[0] >= 20]


def rapor(maclar, kayit):
    s = [f"# Backtest sonuçları\n", f"Veri: İngiltere Premier Lig, {maclar[0][0]:%Y-%m-%d} – {maclar[-1][0]:%Y-%m-%d}, "
         f"{len(maclar)} maç. Değerlendirilen: {len(next(iter(kayit.values())))} maç (ısınma sonrası, her iki takımın en az "
         f"{MIN_MAC} önceki maçı var). Walk-forward: her maç yalnızca öncesindeki verilerle tahmin edildi.\n",
         "| Model | Doğruluk 1X2 | Log loss ↓ | Brier ↓ | RPS ↓ | 2.5 Üst doğr. | 2.5 Üst log loss ↓ | KG doğr. | KG log loss ↓ |",
         "|---|---|---|---|---|---|---|---|---|"]
    for ad in sorted(kayit):
        m = metrikler(kayit[ad])
        s.append(f"| {ad} | {m['acc']:.1%} | {m['ll']:.4f} | {m['brier']:.4f} | {m['rps']:.4f} | "
                 f"{m['u_acc']:.1%} | {m['u_ll']:.4f} | {m['b_acc']:.1%} | {m['b_ll']:.4f} |")
    s.append("\nR1'in 2.5 Üst ve KG değerleri sabit %50 tahmindir (yalnızca karşılaştırma içindir).\n")
    en_iyi = min((a for a in kayit if a[0].isdigit()), key=lambda a: metrikler(kayit[a])["rps"])
    s.append(f"## Kalibrasyon: ev galibiyeti — {en_iyi}\n\n| Tahmin aralığı | Maç | Ortalama tahmin | Gerçekleşen |\n|---|---|---|---|")
    for k, n, tah, ger in kalibrasyon(kayit[en_iyi]):
        s.append(f"| {k * 10}–{k * 10 + 10}% | {n} | {tah:.1%} | {ger:.1%} |")
    return "\n".join(s) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sezonlar", default=",".join(SEZONLAR))
    ap.add_argument("--yaz", default="BACKTEST.md")
    a = ap.parse_args()
    maclar = maclari_oku(a.sezonlar.split(","))
    metin = rapor(maclar, calistir(maclar))
    print(metin)
    open(a.yaz, "w", encoding="utf-8").write(metin)
