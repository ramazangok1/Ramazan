"""Veri kaynakları: DemoProvider (anahtarsız) ve ApiFootballProvider (api-sports.io v3)."""
import time
import requests


class DemoProvider:
    """Gerçek API anahtarı olmadan arayüzü denemek için uydurma veri.
    Canlı maçlar saniyeyi dakika sayarak ilerler (1 sn = 1 dk)."""
    ad = "demo"

    TAKIMLAR = {
        "GS": {"n": 30, "ev_n": 15, "dep_n": 15, "ad": "Galatasaray", "atilan": 2.1, "yenilen": 0.8, "ev_atilan": 2.4, "ev_yenilen": 0.6, "dep_atilan": 1.8, "dep_yenilen": 1.0, "form": ["G", "G", "B", "G", "G"]},
        "FB": {"n": 30, "ev_n": 15, "dep_n": 15, "ad": "Fenerbahçe", "atilan": 2.0, "yenilen": 0.9, "ev_atilan": 2.3, "ev_yenilen": 0.7, "dep_atilan": 1.7, "dep_yenilen": 1.1, "form": ["G", "B", "G", "G", "M"],
               "sakat": [{"oyuncu": "Forvet A", "rol": "forvet"}, {"oyuncu": "Defans B", "rol": "defans"}]},
        "BJK": {"n": 30, "ev_n": 15, "dep_n": 15, "ad": "Beşiktaş", "atilan": 1.6, "yenilen": 1.2, "form": ["M", "G", "B", "G", "B"]},
        "TS": {"n": 30, "ev_n": 15, "dep_n": 15, "ad": "Trabzonspor", "atilan": 1.5, "yenilen": 1.3, "form": ["B", "M", "G", "B", "M"]},
        "BS": {"n": 30, "ev_n": 15, "dep_n": 15, "ad": "Başakşehir", "atilan": 1.3, "yenilen": 1.1, "form": ["G", "B", "B", "M", "G"]},
        "KON": {"n": 30, "ev_n": 15, "dep_n": 15, "ad": "Konyaspor", "atilan": 1.0, "yenilen": 1.6, "form": ["M", "M", "B", "G", "M"]},
    }
    MACLAR = [
        {"id": 1, "lig": "Süper Lig", "oranlar": {"ev": 2.30, "ber": 3.40, "dep": 3.00}, "ev": "GS", "dep": "FB", "baslangic": 0, "olaylar": [(12, "ev"), (38, "dep"), (67, "ev")], "kirmizi": [(55, "dep")]},
        {"id": 2, "lig": "Süper Lig", "oranlar": {"ev": 2.10, "ber": 3.50, "dep": 3.40}, "ev": "BJK", "dep": "TS", "baslangic": 30, "olaylar": [(30, "dep"), (71, "ev")], "kirmizi": []},
        {"id": 3, "lig": "1. Lig", "oranlar": {"ev": 1.80, "ber": 3.60, "dep": 4.50}, "ev": "BS", "dep": "KON", "baslangic": None, "olaylar": [], "kirmizi": []},
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
                "oranlar": m["oranlar"]}


class ApiFootballProvider:
    """https://www.api-football.com (v3). Anahtar: APIFOOTBALL_KEY ortam değişkeni.
    NOT: Gerçek API ile henüz test edilmedi; alan adları dokümana göre yazıldı."""
    ad = "api-football"
    BASE = "https://v3.football.api-sports.io"

    def __init__(self, anahtar):
        self.s = requests.Session()
        self.s.headers["x-apisports-key"] = anahtar

    def _get(self, yol, **params):
        r = self.s.get(self.BASE + yol, params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("response", [])

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
                "oranlar": self._oranlar(mac_id)}


class FootballDataProvider:
    """https://www.football-data.org (v4). Anahtar: FOOTBALL_DATA_KEY ortam değişkeni.
    Ücretsiz planda canlı istatistik, sakatlık ve oran yoktur; skor, dakika'sız durum,
    puan durumundan gol ortalamaları ve H2H gelir. Gerçek API ile test edilmedi."""
    ad = "football-data.org"
    BASE = "https://api.football-data.org/v4"
    CANLI = ("IN_PLAY", "PAUSED", "LIVE")

    def __init__(self, anahtar):
        self.s = requests.Session()
        self.s.headers["X-Auth-Token"] = anahtar
        self._tablo = {}

    def _get(self, yol, **params):
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
        if kod not in self._tablo:
            satirlar = {}
            for blok in self._get(f"/competitions/{kod}/standings")["standings"]:
                satirlar.setdefault(blok["type"], {}).update({r["team"]["id"]: r for r in blok["table"]})
            self._tablo[kod] = satirlar
        return self._tablo[kod]

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
        return {"ozet": o, "ev": ev, "dep": dep, "istatistik": None, "kirmizi": (0, 0), "h2h": h2h, "oranlar": None}
