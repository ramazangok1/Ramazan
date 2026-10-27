"""Futbol analiz sunucusu. Çalıştır: python server.py  ->  http://localhost:8000"""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import analysis
import provider as provider_modul
from provider import DemoProvider, ApiFootballProvider, FootballDataProvider

if os.environ.get("APIFOOTBALL_KEY"):
    PROVIDER = ApiFootballProvider(os.environ["APIFOOTBALL_KEY"])
elif os.environ.get("FOOTBALL_DATA_KEY"):
    PROVIDER = FootballDataProvider(os.environ["FOOTBALL_DATA_KEY"])
else:
    PROVIDER = DemoProvider()
BASLANGIC = time.time()
SON_HATA = {"zaman": None, "yol": None, "mesaj": None}
STATIC = os.path.join(os.path.dirname(__file__), "static")


def ipuclari(son_hata, kaynak):
    h = []
    if kaynak == "demo":
        h.append("Anahtar tanımlı değil, örnek veri kullanılıyor. APIFOOTBALL_KEY veya FOOTBALL_DATA_KEY ayarla ve sunucuyu yeniden başlat.")
    m = (son_hata.get("mesaj") or "").lower()
    if "limit" in m or "429" in m or "requests" in m:
        h.append("Kota ya da hız sınırı dolmuş olabilir. Biraz bekle; CANLI_TTL değerini artırarak istek sayısını azaltabilirsin.")
    if "403" in m or "access" in m or "plan" in m:
        h.append("Planın bu isteğe izin vermiyor olabilir (lig, sezon ya da tarih kısıtı). Hesabındaki plan kapsamını kontrol et.")
    if "401" in m or "token" in m or "key" in m:
        h.append("Anahtar geçersiz görünüyor. Anahtarı kopyalarken boşluk kalmadığından emin ol.")
    if kaynak == "football-data.org":
        h.append("football-data.org ücretsiz planı sınırlı sayıda ligi kapsar (Türkiye Süper Lig'in olduğunu doğrulayamadım) ve skorlar gecikmeli gelir.")
    return h


def durum(test=False):
    p = PROVIDER
    d = {
        "kaynak": p.ad,
        "anahtar_tanimli": p.ad != "demo",
        "calisma_suresi_sn": int(time.time() - BASLANGIC),
        "sunucu_saati_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "ayarlar": {"CANLI_TTL": provider_modul.CANLI_TTL, "GUNLUK_LIMIT": provider_modul.GUNLUK_LIMIT},
        "api_istek_sayisi": getattr(p, "istek_sayisi", None),
        "bugun_harcanan": getattr(p, "_gun", (None, None))[1],
        "onbellekteki_kayit": len(getattr(p, "_c", {})),
        "son_hata": SON_HATA,
    }
    if test:  # gerçek bir istek harcar
        t0 = time.time()
        try:
            n = len(p.maclar("bugun"))
            d["test"] = {"durum": "ok", "bugunku_mac_sayisi": n, "sure_ms": int((time.time() - t0) * 1000)}
        except Exception as e:
            d["test"] = {"durum": "hata", "mesaj": str(e), "sure_ms": int((time.time() - t0) * 1000)}
            SON_HATA.update(zaman=time.strftime("%H:%M:%S"), yol="/api/durum?test=1", mesaj=str(e))
    d["ipuclari"] = ipuclari(SON_HATA, p.ad)
    d["kullanim"] = "Gerçek bir API isteği ile denemek için /api/durum?test=1 (1 istek harcar)."
    return d


def analiz_et(mac_id):
    d = PROVIDER.detay(mac_id)
    o = d["ozet"]
    cikti = {"ozet": o, "ev": d["ev"], "dep": d["dep"], "h2h": d["h2h"],
             "istatistik": d["istatistik"], "kirmizi": d["kirmizi"],
             "mac_oncesi": analysis.mac_oncesi(d["ev"], d["dep"])}
    pazar = analysis.piyasa(d.get("oranlar"))
    cikti["piyasa"] = pazar
    cikti["oranlar"] = d.get("oranlar")
    cikti["deger"] = analysis.deger(cikti["mac_oncesi"], pazar)
    if o["durum"] == "canli":
        cikti["canli"] = analysis.canli(d["ev"], d["dep"], o["dakika"] or 0,
                                        tuple(o["skor"]), tuple(d["kirmizi"]), d["istatistik"])
    return cikti


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, kod=200, girinti=None):
        b = json.dumps(obj, ensure_ascii=False, indent=girinti).encode()
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        try:
            if u.path == "/api/durum":
                return self._json(durum("test" in parse_qs(u.query)), girinti=2)
            if u.path == "/api/maclar":
                mod = parse_qs(u.query).get("mod", ["canli"])[0]
                return self._json({"kaynak": PROVIDER.ad, "maclar": PROVIDER.maclar(mod)})
            if u.path.startswith("/api/analiz/"):
                return self._json(analiz_et(int(u.path.rsplit("/", 1)[1])))
        except Exception as e:  # API hatalarını arayüze ilet
            SON_HATA.update(zaman=time.strftime("%H:%M:%S"), yol=self.path, mesaj=str(e))
            return self._json({"hata": str(e)}, 500)
        dosya = "index.html" if u.path == "/" else u.path.lstrip("/")
        yol = os.path.normpath(os.path.join(STATIC, dosya))
        if not yol.startswith(STATIC) or not os.path.isfile(yol):
            self.send_error(404)
            return
        b = open(yol, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8" if yol.endswith(".html") else "text/plain")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Kaynak: {PROVIDER.ad} | http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
