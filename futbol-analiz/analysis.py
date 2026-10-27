"""Poisson tabanlı maç öncesi ve canlı analiz hesapları."""
from math import exp, factorial

MAX_GOALS = 10
LIG_ORT_EV = 1.45     # lig ortalaması: ev sahibi gol
LIG_ORT_DEP = 1.15    # lig ortalaması: deplasman gol


def pmf(k, lam):
    return exp(-lam) * lam**k / factorial(k)


ROL_ETKISI = {  # (kendi hücumu, kendi savunması: yenilen gol çarpanı)
    "forvet": (0.93, 1.0), "ortasaha": (0.97, 1.03),
    "defans": (1.0, 1.06), "kaleci": (1.0, 1.15),
}


def sakatlik_carpani(sakatlar):
    """sakatlar: [{'oyuncu':..,'rol':'forvet|ortasaha|defans|kaleci'}] -> (hücum, yenilen) çarpanı."""
    hucum = yenilen = 1.0
    for s in sakatlar or []:
        h, y = ROL_ETKISI.get(s.get("rol"), (1.0, 1.0))
        hucum *= h
        yenilen *= y
    return max(hucum, 0.75), min(yenilen, 1.3)


def _sayi(takim, ic_saha, tur):
    """İç saha/deplasman ayrı ortalaması varsa onu, yoksa genel ortalamayı kullanır."""
    ozel = takim.get(("ev_" if ic_saha else "dep_") + tur)
    return ozel if ozel else takim[tur]


def beklenen_goller(ev, dep, lig=None):
    """ev/dep: {'atilan', 'yenilen'} (+ isteğe bağlı 'ev_atilan','ev_yenilen','dep_atilan',
    'dep_yenilen' ve 'sakat'). Ev avantajı, iç saha/deplasman ayrı ortalamalarından
    ve lig iç saha/deplasman gol ortalamalarından gelir."""
    lig_ev, lig_dep = lig or (LIG_ORT_EV, LIG_ORT_DEP)
    e_h, e_y = sakatlik_carpani(ev.get("sakat"))
    d_h, d_y = sakatlik_carpani(dep.get("sakat"))
    ev_hucum = _sayi(ev, True, "atilan") * e_h / lig_ev
    dep_savunma = _sayi(dep, False, "yenilen") * d_y / lig_ev
    dep_hucum = _sayi(dep, False, "atilan") * d_h / lig_dep
    ev_savunma = _sayi(ev, True, "yenilen") * e_y / lig_dep
    return (ev_hucum * dep_savunma * lig_ev,
            dep_hucum * ev_savunma * lig_dep)


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


def mac_oncesi(ev, dep, lig=None):
    lam_ev, lam_dep = beklenen_goller(ev, dep, lig)
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


def piyasa(oranlar):
    """Ondalık oranlardan marjı arındırılmış olasılıklar. oranlar={'ev':1.9,'ber':3.4,'dep':4.2}"""
    if not oranlar:
        return None
    ters = {k: 1 / v for k, v in oranlar.items() if v}
    if len(ters) < 3:
        return None
    t = sum(ters.values())
    return {"ev": ters["ev"] / t, "beraberlik": ters["ber"] / t, "dep": ters["dep"] / t, "marj": t - 1}


def deger(model, pazar):
    """Model olasılığı - piyasa olasılığı. Pozitif ve büyükse model, piyasadan daha iyimser."""
    if not pazar:
        return None
    return {k: model[k] - pazar[k] for k in ("ev", "beraberlik", "dep")}
