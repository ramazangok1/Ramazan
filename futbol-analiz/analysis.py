"""Poisson tabanlı maç öncesi ve canlı analiz hesapları."""
from math import exp, factorial

MAX_GOALS = 10
LIG_ORT_EV = 1.45     # lig ortalaması: ev sahibi gol
LIG_ORT_DEP = 1.15    # lig ortalaması: deplasman gol
TOPLAM_BETA = 0.4     # 2.5 üst/alt ve KG için: toplam beklenen golün lig ortalamasından sapmasının tutulan oranı
DARALT_K = 10         # daraltma gücü: k kadar "hayali" lig ortalaması maçı eklenir (backtest ile seçildi)


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


def _sayi(takim, ic_saha, tur, lig):
    """İç saha/deplasman ayrı ortalaması varsa onu, yoksa genel ortalamayı kullanır.

    Takımda örneklem büyüklüğü varsa ('n', 'ev_n', 'dep_n') ortalama lig ortalamasına doğru
    daraltılır: (n*ort + k*lig) / (n + k). Az maçla hesaplanmış uç değerleri yumuşatır.
    Örneklem yoksa değer olduğu gibi kullanılır.
    """
    lig_ev, lig_dep = lig
    onek = "ev_" if ic_saha else "dep_"
    deger = takim.get(onek + tur)
    if deger:
        n = takim.get(onek + "n")
        # ev_atilan / dep_yenilen lig ev golüne, dep_atilan / ev_yenilen lig dep golüne yakınsar
        hedef = lig_ev if (ic_saha == (tur == "atilan")) else lig_dep
    else:
        deger, n, hedef = takim[tur], takim.get("n"), (lig_ev + lig_dep) / 2
    if n is None:
        return deger
    return (n * deger + DARALT_K * hedef) / (n + DARALT_K)


def beklenen_goller(ev, dep, lig=None):
    """ev/dep: {'atilan', 'yenilen'} (+ isteğe bağlı 'ev_atilan','ev_yenilen','dep_atilan',
    'dep_yenilen', örneklem için 'n','ev_n','dep_n' ve 'sakat'). Ev avantajı, iç saha/deplasman ayrı ortalamalarından
    ve lig iç saha/deplasman gol ortalamalarından gelir."""
    lig_ev, lig_dep = lig or (LIG_ORT_EV, LIG_ORT_DEP)
    e_h, e_y = sakatlik_carpani(ev.get("sakat"))
    d_h, d_y = sakatlik_carpani(dep.get("sakat"))
    lig = (lig_ev, lig_dep)
    ev_hucum = _sayi(ev, True, "atilan", lig) * e_h / lig_ev
    dep_savunma = _sayi(dep, False, "yenilen", lig) * d_y / lig_ev
    dep_hucum = _sayi(dep, False, "atilan", lig) * d_h / lig_dep
    ev_savunma = _sayi(ev, True, "yenilen", lig) * e_y / lig_dep
    return (ev_hucum * dep_savunma * lig_ev,
            dep_hucum * ev_savunma * lig_dep)


def _matris(lam_ev, lam_dep, skor):
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
    t = ev_kazanir + beraberlik + dep_kazanir
    return {
        "ev": ev_kazanir / t, "beraberlik": beraberlik / t, "dep": dep_kazanir / t,
        "ust25": ust25 / t, "alt25": 1 - ust25 / t,
        "kg_var": kg_var / t, "kg_yok": 1 - kg_var / t,
        "skorlar": [{"skor": s, "olasilik": p / t} for s, p in skorlar[:5]],
    }


def toplam_lam(lam_ev, lam_dep, lig=None, beta=None):
    """2.5 üst/alt ve KG için beklenen golleri, toplamı lig ortalamasına doğru çekerek döndürür.

    Backtest: ham modelin takımlar arası toplam gol farkını olduğundan büyük tahmin ettiği
    görüldü (aşırı iddialı). Toplamın lig ortalamasından sapması beta oranında tutulur;
    ev/deplasman oranı korunur."""
    lig_ev, lig_dep = lig or (LIG_ORT_EV, LIG_ORT_DEP)
    beta = TOPLAM_BETA if beta is None else beta
    t = lam_ev + lam_dep
    if t <= 0:
        return lam_ev, lam_dep
    mu = lig_ev + lig_dep
    s = (mu + beta * (t - mu)) / t
    return lam_ev * s, lam_dep * s


def olasiliklar(lam_ev, lam_dep, skor=(0, 0), ou_lam=None):
    """Kalan süre için beklenen goller verilir; mevcut skor üstüne eklenir.

    ou_lam=(ev, dep) verilirse 2.5 üst/alt ve KG bu (toplam_lam ile daraltılmış)
    değerlerden hesaplanır; 1X2 ve skorlar lam_ev/lam_dep'ten gelir."""
    sonuc = _matris(lam_ev, lam_dep, skor)
    if ou_lam:
        o = _matris(ou_lam[0], ou_lam[1], skor)
        for k in ("ust25", "alt25", "kg_var", "kg_yok"):
            sonuc[k] = o[k]
    return sonuc


def form_puani(son_maclar):
    """['G','B','M',...] -> 0..1 arası (son maçlara daha çok ağırlık)."""
    if not son_maclar:
        return 0.5
    puan = {"G": 1.0, "B": 0.4, "M": 0.0}
    agirlik = [1 + 0.15 * i for i in range(len(son_maclar))][::-1]
    return sum(puan[r] * w for r, w in zip(son_maclar, agirlik)) / sum(agirlik)


def mac_oncesi(ev, dep, lig=None, beta=None):
    lam_ev, lam_dep = beklenen_goller(ev, dep, lig)
    ou_ev, ou_dep = toplam_lam(lam_ev, lam_dep, lig, beta)
    # Form etkisi: en fazla ±%10
    f_ev = 1 + 0.2 * (form_puani(ev["form"]) - 0.5)
    f_dep = 1 + 0.2 * (form_puani(dep["form"]) - 0.5)
    lam_ev, lam_dep = lam_ev * f_ev, lam_dep * f_dep
    sonuc = olasiliklar(lam_ev, lam_dep, ou_lam=(ou_ev * f_ev, ou_dep * f_dep))
    sonuc.update(beklenen_ev=lam_ev, beklenen_dep=lam_dep,
                 form_ev=form_puani(ev["form"]), form_dep=form_puani(dep["form"]))
    return sonuc


def canli(ev, dep, dakika, skor, kirmizi=(0, 0), istatistik=None, lig=None, beta=None):
    """Kalan süreye göre güncel olasılıklar.

    Kırmızı kart: kartı gören takımın hücumu x0.75, rakibin x1.2.
    Şut baskısı: isabetli şut farkı beklenen golleri en fazla ±%15 kaydırır.
    Üst/alt ve KG için takım gücü toplam_lam ile daraltılır; maç içi düzeltmeler
    (kalan süre, kart, şut baskısı) her iki hesaba da aynen uygulanır."""
    lam_ev, lam_dep = beklenen_goller(ev, dep, lig)
    ou_ev, ou_dep = toplam_lam(lam_ev, lam_dep, lig, beta)
    c_ev = c_dep = max(0.0, (90 - dakika)) / 90
    for _ in range(kirmizi[0]): c_ev *= 0.75; c_dep *= 1.2
    for _ in range(kirmizi[1]): c_dep *= 0.75; c_ev *= 1.2
    if istatistik:
        fark = istatistik["isabetli_ev"] - istatistik["isabetli_dep"]
        toplam = istatistik["isabetli_ev"] + istatistik["isabetli_dep"]
        if toplam >= 4:
            kayma = max(-0.15, min(0.15, 0.15 * fark / toplam))
            c_ev *= 1 + kayma
            c_dep *= 1 - kayma
    lam_ev, lam_dep, ou_ev, ou_dep = lam_ev * c_ev, lam_dep * c_dep, ou_ev * c_ev, ou_dep * c_dep
    sonuc = olasiliklar(lam_ev, lam_dep, skor, ou_lam=(ou_ev, ou_dep))
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
