"""Veri kaynakları: DemoProvider (anahtarsız) ve ApiFootballProvider (api-sports.io v3)."""
import os
import time
import requests

import analysis

# Ücretsiz API planlarında günlük/dakikalık istek sınırı vardır; yanıtlar bu sürelerle (sn) önbelleğe alınır.
# Canlı veri için CANLI_TTL ortam değişkeniyle süre uzatılabilir (API-Football ücretsiz planı: günde 100 istek -> 300 önerilir).
CANLI_TTL = int(os.environ.get("CANLI_TTL", "60"))
# Günde API'ye gidecek en fazla istek (0 = sınırsız). Herkese açık sunucuda ücretsiz kotanın tükenmesini önler.
GUNLUK_LIMIT = int(os.environ.get("GUNLUK_LIMIT", "0"))


class _Onbellekli:
    """Aynı istek TTL süresi içinde tekrarlanırsa API'ye gitmeden önceki yanıtı döner."""

    def _init_onbellek(self):
        self._c = {}
        self.istek_sayisi = 0   # gerçekten API'ye giden istekler
        self._gun = (time.strftime("%Y-%m-%d"), 0)

    def _ttl(self, yol, params):
        raise NotImplementedError

    def _al(self, yol, params):
        raise NotImplementedError

    def _get(self, yol, **params):
        anahtar = (yol, tuple(sorted(params.items())))
        simdi = time.time()
        hit = self._c.get(anahtar)
        if hit and simdi - hit[0] < self._ttl(yol, params):
            return hit[1]
        bugun, adet = self._gun
        if bugun != time.strftime("%Y-%m-%d"):
            bugun, adet = time.strftime("%Y-%m-%d"), 0
        if GUNLUK_LIMIT and adet >= GUNLUK_LIMIT:
            raise RuntimeError(f"Günlük istek limiti ({GUNLUK_LIMIT}) doldu; yarın tekrar dene ya da önbellekteki veriyle devam et.")
        veri = self._al(yol, params)
        self._gun = (bugun, adet + 1)
        self.istek_sayisi += 1
        self._c[anahtar] = (simdi, veri)
        return veri


def _t(ad, a, y, form, sakat=None):
    """Demo takımı: genel ortalamadan iç saha/deplasman ortalamalarını türetir."""
    t = {"ad": ad, "atilan": a, "yenilen": y, "n": 30, "ev_n": 15, "dep_n": 15,
         "ev_atilan": round(a * 1.1, 2), "ev_yenilen": round(y * 0.85, 2),
         "dep_atilan": round(a * 0.9, 2), "dep_yenilen": round(y * 1.15, 2),
         "form": [{"G": "G", "B": "B", "M": "M"}[c] for c in form]}
    if sakat:
        t["sakat"] = sakat
    return t


def _m(id, lig, ev, dep, bas, olaylar, kirmizi, oran):
    """olaylar/kirmizi: [(dakika, 0=ev | 1=deplasman)]"""
    taraf = lambda l: [(d, "ev" if k == 0 else "dep") for d, k in l]
    return {"id": id, "lig": lig, "ev": ev, "dep": dep, "baslangic": bas, "olaylar": taraf(olaylar), "kirmizi": taraf(kirmizi),
            "oranlar": {"ev": oran[0], "ber": oran[1], "dep": oran[2]}}


class DemoProvider:
    """Gerçek API anahtarı olmadan arayüzü denemek için uydurma veri.
    Canlı maçlar saniyeyi dakika sayarak ilerler (1 sn = 1 dk)."""
    ad = "demo"

    TAKIMLAR = {
        "GS": {"n": 30, "ev_n": 15, "dep_n": 15, "ad": "Galatasaray", "atilan": 2.1, "yenilen": 0.8, "ev_atilan": 2.4, "ev_yenilen": 0.6, "dep_atilan": 1.8, "dep_yenilen": 1.0, "form": ["G", "G", "B", "G", "G"]},
        "FB": {"n": 30, "ev_n": 15, "dep_n": 15, "ad": "Fenerbahçe", "atilan": 2.0, "yenilen": 0.9, "ev_atilan": 2.3, "ev_yenilen": 0.7, "dep_atilan": 1.7, "dep_yenilen": 1.1, "form": ["G", "B", "G", "G", "M"],
               "sakat": [{"oyuncu": "Forvet A", "rol": "forvet"}, {"oyuncu": "Defans B", "rol": "defans"}]},
        "BJK": _t("Beşiktaş", 1.6, 1.2, "MGBGB"),
        "TS": _t("Trabzonspor", 1.5, 1.3, "BMGBM"),
        "BS": _t("Başakşehir", 1.3, 1.1, "GBBMG"),
        "KON": _t("Konyaspor", 1.0, 1.6, "MMBGM"),
        "MCI": _t("Manchester City", 2.3, 0.8, "GGGBG"), "ARS": _t("Arsenal", 2.0, 0.8, "GBGGG"),
        "LIV": _t("Liverpool", 2.1, 1.0, "GGMGB"), "CHE": _t("Chelsea", 1.6, 1.2, "BGMBG"),
        "RMA": _t("Real Madrid", 2.2, 0.9, "GGBGG"), "BAR": _t("Barcelona", 2.3, 1.0, "GMGGB"),
        "ATM": _t("Atlético Madrid", 1.6, 0.8, "GBGBG"), "SEV": _t("Sevilla", 1.2, 1.4, "MBMGB"),
        "FCB": _t("Bayern Münih", 2.8, 1.0, "GGGBG", [{"oyuncu": "Kaleci C", "rol": "kaleci"}]), "BVB": _t("Dortmund", 2.0, 1.4, "GMGBG"),
        "B04": _t("Leverkusen", 2.2, 1.0, "GGBGG"), "RBL": _t("Leipzig", 1.9, 1.1, "BGGMB"),
        "INT": _t("Inter", 2.0, 0.8, "GGBGG"), "MIL": _t("Milan", 1.6, 1.0, "BGGMB"),
        "JUV": _t("Juventus", 1.4, 0.8, "BBGBG"), "NAP": _t("Napoli", 1.7, 1.1, "GMBGG"),
        "PSG": _t("Paris SG", 2.4, 0.9, "GGGGB"), "OM": _t("Marseille", 1.7, 1.2, "MGBGM"),
        "SCP": _t("Sporting", 2.2, 0.8, "GGGBG"), "BEN": _t("Benfica", 2.1, 0.9, "GBGGM"),
    }
    # Ligin maç başı ortalama gol (ev, deplasman). Örnek değerlerdir.
    LIG_ORT = {"Süper Lig": (1.55, 1.22), "1. Lig": (1.45, 1.15), "Premier League": (1.55, 1.25),
               "La Liga": (1.40, 1.05), "Bundesliga": (1.75, 1.40), "Serie A": (1.45, 1.15),
               "Ligue 1": (1.50, 1.20), "Liga Portugal": (1.45, 1.10)}
    MACLAR = [
        _m(1, "Süper Lig", "GS", "FB", 0, [(12, 0), (38, 1), (67, 0)], [(55, 1)], (2.30, 3.40, 3.00)),
        _m(2, "Süper Lig", "BJK", "TS", 30, [(30, 1), (71, 0)], [], (2.10, 3.50, 3.40)),
        _m(3, "1. Lig", "BS", "KON", None, [], [], (1.80, 3.60, 4.50)),
        _m(4, "Premier League", "MCI", "ARS", 10, [(23, 0), (80, 1)], [], (2.10, 3.60, 3.40)),
        _m(5, "Premier League", "LIV", "CHE", None, [], [], (1.75, 3.90, 4.40)),
        _m(6, "La Liga", "RMA", "BAR", 40, [(9, 1), (51, 0), (88, 0)], [(70, 1)], (2.30, 3.70, 2.95)),
        _m(7, "La Liga", "ATM", "SEV", 70, [(33, 0)], [], (1.60, 3.80, 5.50)),
        _m(8, "Bundesliga", "FCB", "BVB", 20, [(5, 0), (18, 0), (60, 1)], [], (1.40, 5.00, 6.50)),
        _m(9, "Bundesliga", "B04", "RBL", None, [], [], (1.95, 3.90, 3.50)),
        _m(10, "Serie A", "INT", "MIL", 50, [(44, 1), (75, 0)], [], (1.85, 3.50, 4.30)),
        _m(11, "Serie A", "JUV", "NAP", None, [], [], (2.50, 3.10, 3.00)),
        _m(12, "Ligue 1", "PSG", "OM", 60, [(14, 0), (30, 0)], [], (1.35, 5.00, 7.50)),
        _m(13, "Liga Portugal", "SCP", "BEN", 85, [(40, 1)], [], (1.85, 3.60, 4.10)),
    ]
    H2H = {frozenset(["GS", "FB"]): ["GS 2-1", "FB 1-1", "FB 3-2", "GS 0-0", "GS 3-1"]}

    def _dakika(self, m):
        if m["baslangic"] is None:
            return None
        gecen = (time.time() % 130) - m["baslangic"]
        return int(gecen) if 0 <= gecen <= 95 else None

    def maclar(self, mod):
        sonuc = []
        for m in self.MACLAR:
            d = self._dakika(m)
            durum = "canli" if d is not None else ("planli" if m["baslangic"] is None else "bitti")
            if mod == "canli" and durum != "canli":
                continue
            sonuc.append(self._ozet(m, d, durum))
        return sonuc

    def _ozet(self, m, d, durum):
        skor = [0, 0]
        if d is not None:
            for dk, kim in m["olaylar"]:
                if dk <= d: skor[0 if kim == "ev" else 1] += 1
        return {"id": m["id"], "ev": self.TAKIMLAR[m["ev"]]["ad"], "dep": self.TAKIMLAR[m["dep"]]["ad"],
                "lig": m["lig"], "durum": durum, "dakika": min(d, 90) if d is not None else None, "skor": skor}

    def detay(self, mac_id):
        m = next(x for x in self.MACLAR if x["id"] == mac_id)
        d = self._dakika(m)
        ev, dep = self.TAKIMLAR[m["ev"]], self.TAKIMLAR[m["dep"]]
        ozet = self._ozet(m, d, "canli" if d is not None else "planli")
        stat = None
        kirmizi = (0, 0)
        if d is not None:
            ev_sut = int(d * 0.14 + (3 if m["ev"] == "GS" else 0))
            dep_sut = int(d * 0.10)
            stat = {"isabetli_ev": ev_sut // 2, "isabetli_dep": dep_sut // 2,
                    "sut_ev": ev_sut, "sut_dep": dep_sut,
                    "topla_oynama_ev": 54, "korner_ev": d // 12, "korner_dep": d // 15}
            kirmizi = (sum(1 for dk, k in m["kirmizi"] if dk <= d and k == "ev"),
                       sum(1 for dk, k in m["kirmizi"] if dk <= d and k == "dep"))
        h2h = self.H2H.get(frozenset([m["ev"], m["dep"]]), [])
        return {"ozet": ozet, "ev": ev, "dep": dep, "istatistik": stat, "kirmizi": kirmizi, "h2h": h2h,
                "oranlar": m["oranlar"], "lig_ort": self.LIG_ORT[m["lig"]]}


class ApiFootballProvider(_Onbellekli):
    """https://www.api-football.com (v3). Anahtar: APIFOOTBALL_KEY ortam değişkeni.
    NOT: Gerçek API ile henüz test edilmedi; alan adları dokümana göre yazıldı."""
    ad = "api-football"
    BASE = "https://v3.football.api-sports.io"

    def __init__(self, anahtar):
        self.s = requests.Session()
        self.s.headers["x-apisports-key"] = anahtar
        self._init_onbellek()

    def _ttl(self, yol, params):
        if yol == "/fixtures":
            return CANLI_TTL if ("live" in params or "id" in params) else 300
        return {"/fixtures/statistics": CANLI_TTL, "/teams/statistics": 43200, "/injuries": 1800,
                "/odds": 900, "/fixtures/headtohead": 86400, "/standings": 43200}.get(yol, 300)

    def _al(self, yol, params):
        r = self.s.get(self.BASE + yol, params=params, timeout=15)
        r.raise_for_status()
        j = r.json()
        if j.get("errors"):  # API 200 döner ama kota/anahtar hatasını burada bildirir
            raise RuntimeError("API-Football: " + str(j["errors"]))
        return j.get("response", [])

    def _ozet(self, f):
        kisa = f["fixture"]["status"]["short"]
        durum = "canli" if kisa in ("1H", "2H", "HT", "ET", "LIVE") else ("bitti" if kisa in ("FT", "AET", "PEN") else "planli")
        return {"id": f["fixture"]["id"], "ev": f["teams"]["home"]["name"], "dep": f["teams"]["away"]["name"],
                "lig": f["league"]["name"], "durum": durum, "dakika": f["fixture"]["status"].get("elapsed"),
                "skor": [f["goals"]["home"] or 0, f["goals"]["away"] or 0],
                "_ev_id": f["teams"]["home"]["id"], "_dep_id": f["teams"]["away"]["id"],
                "_lig": f["league"]["id"], "_sezon": f["league"]["season"]}

    def maclar(self, mod):
        if mod == "canli":
            veri = self._get("/fixtures", live="all")
        else:
            veri = self._get("/fixtures", date=time.strftime("%Y-%m-%d"))
        return [{k: v for k, v in self._ozet(f).items() if not k.startswith("_")} for f in veri]

    def _takim(self, takim_id, lig, sezon, ad):
        st = self._get("/teams/statistics", team=takim_id, league=lig, season=sezon)
        if isinstance(st, list):  # bazı yanıtlarda dict döner
            st = st[0] if st else {}
        oyn = st.get("fixtures", {}).get("played", {})
        oynanan = oyn.get("total") or 0
        gol = st.get("goals", {})
        atilan = float(gol.get("for", {}).get("average", {}).get("total") or 1.3)
        yenilen = float(gol.get("against", {}).get("average", {}).get("total") or 1.3)
        form = [{"W": "G", "D": "B", "L": "M"}.get(c, "B") for c in (st.get("form") or "")[-5:]]

        def ort(taraf, yon):
            v = gol.get(yon, {}).get("average", {}).get(taraf)
            return float(v) if v else None
        return {"ad": ad, "atilan": atilan, "yenilen": yenilen, "form": form, "n": oynanan,
                "ev_atilan": ort("home", "for"), "ev_yenilen": ort("home", "against"), "ev_n": oyn.get("home") or 0,
                "dep_atilan": ort("away", "for"), "dep_yenilen": ort("away", "against"), "dep_n": oyn.get("away") or 0}

    def _lig_ort(self, lig, sezon):
        """Puan durumundan ligin maç başı ev/deplasman gol ortalaması."""
        try:
            veri = self._get("/standings", league=lig, season=sezon)
            eg = em = dg = dm = 0
            for grup in veri[0]["league"]["standings"]:
                for r in grup:
                    eg += r["home"]["goals"]["for"] or 0; em += r["home"]["played"] or 0
                    dg += r["away"]["goals"]["for"] or 0; dm += r["away"]["played"] or 0
            return analysis.lig_ortalama(eg, em, dg, dm)
        except Exception:
            return None  # puan durumu yoksa (ör. kupa) model varsayılan ortalamayı kullanır

    ROLLER = {"Attacker": "forvet", "Midfielder": "ortasaha", "Defender": "defans", "Goalkeeper": "kaleci"}

    def _sakatlar(self, mac_id, takim_id):
        """Yalnızca bu maç için 'Missing Fixture' durumundaki oyuncular."""
        try:
            liste = self._get("/injuries", fixture=mac_id)
        except Exception:
            return []
        return [{"oyuncu": x["player"]["name"], "rol": self.ROLLER.get(x["player"].get("position"), "ortasaha")}
                for x in liste if x["team"]["id"] == takim_id and x["player"].get("type") == "Missing Fixture"]

    def _oranlar(self, mac_id):
        try:
            for y in self._get("/odds", fixture=mac_id):
                for bm in y.get("bookmakers", []):
                    for bahis in bm.get("bets", []):
                        if bahis["name"] == "Match Winner":
                            v = {x["value"]: float(x["odd"]) for x in bahis["values"]}
                            return {"ev": v["Home"], "ber": v["Draw"], "dep": v["Away"]}
        except Exception:
            pass
        return None

    def detay(self, mac_id):
        f = self._get("/fixtures", id=mac_id)[0]
        o = self._ozet(f)
        ev = self._takim(o["_ev_id"], o["_lig"], o["_sezon"], o["ev"])
        dep = self._takim(o["_dep_id"], o["_lig"], o["_sezon"], o["dep"])
        ev["sakat"] = self._sakatlar(mac_id, o["_ev_id"])
        dep["sakat"] = self._sakatlar(mac_id, o["_dep_id"])
        stat, kirmizi = None, (0, 0)
        if o["durum"] == "canli":
            def al(takim_blok, tur):
                for x in takim_blok["statistics"]:
                    if x["type"] == tur:
                        return int(str(x["value"] or 0).replace("%", ""))
                return 0
            bloklar = self._get("/fixtures/statistics", fixture=mac_id)
            if len(bloklar) == 2:
                e, d = bloklar
                stat = {"isabetli_ev": al(e, "Shots on Goal"), "isabetli_dep": al(d, "Shots on Goal"),
                        "sut_ev": al(e, "Total Shots"), "sut_dep": al(d, "Total Shots"),
                        "topla_oynama_ev": al(e, "Ball Possession"),
                        "korner_ev": al(e, "Corner Kicks"), "korner_dep": al(d, "Corner Kicks")}
                kirmizi = (al(e, "Red Cards"), al(d, "Red Cards"))
        h2h = []
        for x in self._get("/fixtures/headtohead", h2h=f"{o['_ev_id']}-{o['_dep_id']}", last=5):
            h2h.append(f"{x['teams']['home']['name']} {x['goals']['home']}-{x['goals']['away']} {x['teams']['away']['name']}")
        return {"ozet": {k: v for k, v in o.items() if not k.startswith("_")},
                "ev": ev, "dep": dep, "istatistik": stat, "kirmizi": kirmizi, "h2h": h2h,
                "oranlar": self._oranlar(mac_id), "lig_ort": self._lig_ort(o["_lig"], o["_sezon"])}


class FootballDataProvider(_Onbellekli):
    """https://www.football-data.org (v4). Anahtar: FOOTBALL_DATA_KEY ortam değişkeni.
    Ücretsiz planda canlı istatistik, sakatlık ve oran yoktur; skor, dakika'sız durum,
    puan durumundan gol ortalamaları ve H2H gelir. Gerçek API ile test edilmedi."""
    ad = "football-data.org"
    BASE = "https://api.football-data.org/v4"
    CANLI = ("IN_PLAY", "PAUSED", "LIVE")

    def __init__(self, anahtar):
        self.s = requests.Session()
        self.s.headers["X-Auth-Token"] = anahtar
        self._init_onbellek()

    def _ttl(self, yol, params):
        if "/standings" in yol:
            return 3600
        return 86400 if "head2head" in yol else CANLI_TTL

    def _al(self, yol, params):
        r = self.s.get(self.BASE + yol, params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    def _ozet(self, m):
        d = "canli" if m["status"] in self.CANLI else ("bitti" if m["status"] == "FINISHED" else "planli")
        ft = m["score"]["fullTime"]
        return {"id": m["id"], "ev": m["homeTeam"]["name"], "dep": m["awayTeam"]["name"],
                "lig": m["competition"]["name"], "durum": d,
                "dakika": m.get("minute"), "skor": [ft.get("home") or 0, ft.get("away") or 0]}

    def maclar(self, mod):
        veri = self._get("/matches")["matches"]
        o = [self._ozet(m) for m in veri]
        return [m for m in o if m["durum"] == "canli"] if mod == "canli" else o

    def _puan_durumu(self, kod):
        satirlar = {}
        for blok in self._get(f"/competitions/{kod}/standings")["standings"]:
            satirlar.setdefault(blok["type"], {}).update({r["team"]["id"]: r for r in blok["table"]})
        return satirlar

    def _takim(self, tid, kod, ic_saha, ad):
        t = self._puan_durumu(kod)
        def ort(tip):
            r = t.get(tip, {}).get(tid)
            if not r or not r["playedGames"]:
                return None
            return r["goalsFor"] / r["playedGames"], r["goalsAgainst"] / r["playedGames"], r["playedGames"]
        genel = ort("TOTAL") or (1.3, 1.3, 0)
        ozel = ort("HOME" if ic_saha else "AWAY")
        ek = {}
        if ozel:
            onek = "ev_" if ic_saha else "dep_"
            ek = {onek + "atilan": ozel[0], onek + "yenilen": ozel[1], onek + "n": ozel[2]}
        satir = t.get("TOTAL", {}).get(tid, {})
        form = [{"W": "G", "D": "B", "L": "M"}.get(c, "B") for c in (satir.get("form") or "").split(",") if c][-5:]
        return {"ad": ad, "atilan": genel[0], "yenilen": genel[1], "n": genel[2], "form": form, **ek}

    def detay(self, mac_id):
        m = self._get(f"/matches/{mac_id}")
        o = self._ozet(m)
        kod = m["competition"]["code"]
        ev = self._takim(m["homeTeam"]["id"], kod, True, o["ev"])
        dep = self._takim(m["awayTeam"]["id"], kod, False, o["dep"])
        h2h = []
        try:
            for x in self._get(f"/matches/{mac_id}/head2head", limit=5)["matches"]:
                ft = x["score"]["fullTime"]
                h2h.append(f"{x['homeTeam']['name']} {ft['home']}-{ft['away']} {x['awayTeam']['name']}")
        except Exception:
            pass
        t = self._puan_durumu(kod)
        ev_s, dep_s = t.get("HOME", {}).values(), t.get("AWAY", {}).values()
        lig_ort = analysis.lig_ortalama(sum(r["goalsFor"] for r in ev_s), sum(r["playedGames"] for r in ev_s),
                                        sum(r["goalsFor"] for r in dep_s), sum(r["playedGames"] for r in dep_s))
        return {"ozet": o, "ev": ev, "dep": dep, "istatistik": None, "kirmizi": (0, 0), "h2h": h2h,
                "oranlar": None, "lig_ort": lig_ort}
