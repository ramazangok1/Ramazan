"""Poisson tabanlı maç öncesi ve canlı analiz hesapları."""
from math import exp, factorial

MAX_GOALS = 10
LIG_ORT_EV = 1.45     # lig ortalaması: ev sahibi gol
LIG_ORT_DEP = 1.15    # lig ortalaması: deplasman gol


def pmf(k, lam):
    return exp(-lam) * lam**k / factorial(k)


def beklenen_goller(ev, dep):
    """ev/dep: {'atilan': maç başı atılan gol, 'yenilen': maç başı yenilen gol}"""
    ev_hucum = ev["atilan"] / LIG_ORT_EV
    dep_savunma = dep["yenilen"] / LIG_ORT_EV
    dep_hucum = dep["atilan"] / LIG_ORT_DEP
    ev_savunma = ev["yenilen"] / LIG_ORT_DEP
    return (ev_hucum * dep_savunma * LIG_ORT_EV,
            dep_hucum * ev_savunma * LIG_ORT_DEP)


def olasiliklar(lam_ev, lam_dep, skor=(0, 0)):
    """Kalan süre için beklenen goller verilir; mevcut skor üstüne eklenir."""
    ms = skor[0] - skor[1]
    ev_kazanir = beraberlik = dep_kazanir = 0.0
    ust25 = kg_var = 0.0
    skorlar = []
    for h in range(MAX_GOALS + 1):
        ph = pmf(h, lam_ev)
        for a in range(MAX_GOALS + 1):
            p = ph * pmf(a, lam_dep)
            fh, fa = skor[0] + h, skor[1] + a
            if fh > fa: ev_kazanir += p
            elif fh == fa: beraberlik += p
            else: dep_kazanir += p
            if fh + fa > 2: ust25 += p
            if fh > 0 and fa > 0: kg_var += p
            skorlar.append((f"{fh}-{fa}", p))
    skorlar.sort(key=lambda x: -x[1])
    toplam = ev_kazanir + beraberlik + dep_kazanir
    return {
        "ev": ev_kazanir / toplam, "beraberlik": beraberlik / toplam,
        "dep": dep_kazanir / toplam,
        "ust25": ust25 / toplam, "alt25": 1 - ust25 / toplam,
        "kg_var": kg_var / toplam, "kg_yok": 1 - kg_var / toplam,
        "skorlar": [{"skor": s, "olasilik": p / toplam} for s, p in skorlar[:5]],
    }


def form_puani(son_maclar):
    """['G','B','M',...] -> 0..1 arası (son maçlara daha çok ağırlık)."""
    if not son_maclar:
        return 0.5
    puan = {"G": 1.0, "B": 0.4, "M": 0.0}
    agirlik = [1 + 0.15 * i for i in range(len(son_maclar))][::-1]
    return sum(puan[r] * w for r, w in zip(son_maclar, agirlik)) / sum(agirlik)


def mac_oncesi(ev, dep):
    lam_ev, lam_dep = beklenen_goller(ev, dep)
    # Form etkisi: en fazla ±%10
    lam_ev *= 1 + 0.2 * (form_puani(ev["form"]) - 0.5)
    lam_dep *= 1 + 0.2 * (form_puani(dep["form"]) - 0.5)
    sonuc = olasiliklar(lam_ev, lam_dep)
    sonuc.update(beklenen_ev=lam_ev, beklenen_dep=lam_dep,
                 form_ev=form_puani(ev["form"]), form_dep=form_puani(dep["form"]))
    return sonuc


def canli(ev, dep, dakika, skor, kirmizi=(0, 0), istatistik=None):
    """Kalan süreye göre güncel olasılıklar.

    Kırmızı kart: kartı gören takımın hücumu x0.75, rakibin x1.2.
    Şut baskısı: isabetli şut farkı beklenen golleri en fazla ±%15 kaydırır.
    """
    lam_ev, lam_dep = beklenen_goller(ev, dep)
    kalan = max(0.0, (90 - dakika)) / 90
    lam_ev *= kalan
    lam_dep *= kalan
    for _ in range(kirmizi[0]): lam_ev *= 0.75; lam_dep *= 1.2
    for _ in range(kirmizi[1]): lam_dep *= 0.75; lam_ev *= 1.2
    if istatistik:
        fark = istatistik["isabetli_ev"] - istatistik["isabetli_dep"]
        toplam = istatistik["isabetli_ev"] + istatistik["isabetli_dep"]
        if toplam >= 4:
            kayma = max(-0.15, min(0.15, 0.15 * fark / toplam))
            lam_ev *= 1 + kayma
            lam_dep *= 1 - kayma
    sonuc = olasiliklar(lam_ev, lam_dep, skor)
    sonuc.update(kalan_beklenen_ev=lam_ev, kalan_beklenen_dep=lam_dep)
    return sonuc
