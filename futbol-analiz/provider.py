"""Veri kaynakları: DemoProvider (anahtarsız) ve ApiFootballProvider (api-sports.io v3)."""
import time
import requests


class DemoProvider:
    """Gerçek API anahtarı olmadan arayüzü denemek için uydurma veri.
    Canlı maçlar saniyeyi dakika sayarak ilerler (1 sn = 1 dk)."""
    ad = "demo"

    TAKIMLAR = {
        "GS": {"ad": "Galatasaray", "atilan": 2.1, "yenilen": 0.8, "form": ["G", "G", "B", "G", "G"]},
        "FB": {"ad": "Fenerbahçe", "atilan": 2.0, "yenilen": 0.9, "form": ["G", "B", "G", "G", "M"]},
        "BJK": {"ad": "Beşiktaş", "atilan": 1.6, "yenilen": 1.2, "form": ["M", "G", "B", "G", "B"]},
        "TS": {"ad": "Trabzonspor", "atilan": 1.5, "yenilen": 1.3, "form": ["B", "M", "G", "B", "M"]},
        "BS": {"ad": "Başakşehir", "atilan": 1.3, "yenilen": 1.1, "form": ["G", "B", "B", "M", "G"]},
        "KON": {"ad": "Konyaspor", "atilan": 1.0, "yenilen": 1.6, "form": ["M", "M", "B", "G", "M"]},
    }
    MACLAR = [
        {"id": 1, "ev": "GS", "dep": "FB", "baslangic": 0, "olaylar": [(12, "ev"), (38, "dep"), (67, "ev")], "kirmizi": [(55, "dep")]},
        {"id": 2, "ev": "BJK", "dep": "TS", "baslangic": 30, "olaylar": [(30, "dep"), (71, "ev")], "kirmizi": []},
        {"id": 3, "ev": "BS", "dep": "KON", "baslangic": None, "olaylar": [], "kirmizi": []},
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
                "durum": durum, "dakika": min(d, 90) if d is not None else None, "skor": skor}

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
        return {"ozet": ozet, "ev": ev, "dep": dep, "istatistik": stat, "kirmizi": kirmizi, "h2h": h2h}


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
                "durum": durum, "dakika": f["fixture"]["status"].get("elapsed"),
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
        oynanan = max(1, st.get("fixtures", {}).get("played", {}).get("total") or 1)
        gol = st.get("goals", {})
        atilan = float(gol.get("for", {}).get("average", {}).get("total") or 1.3)
        yenilen = float(gol.get("against", {}).get("average", {}).get("total") or 1.3)
        form = [{"W": "G", "D": "B", "L": "M"}.get(c, "B") for c in (st.get("form") or "")[-5:]]
        return {"ad": ad, "atilan": atilan, "yenilen": yenilen, "form": form}

    def detay(self, mac_id):
        f = self._get("/fixtures", id=mac_id)[0]
        o = self._ozet(f)
        ev = self._takim(o["_ev_id"], o["_lig"], o["_sezon"], o["ev"])
        dep = self._takim(o["_dep_id"], o["_lig"], o["_sezon"], o["dep"])
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
                "ev": ev, "dep": dep, "istatistik": stat, "kirmizi": kirmizi, "h2h": h2h}
