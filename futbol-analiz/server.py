"""Futbol analiz sunucusu. Çalıştır: python server.py  ->  http://localhost:8000"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import analysis
from provider import DemoProvider, ApiFootballProvider

ANAHTAR = os.environ.get("APIFOOTBALL_KEY")
PROVIDER = ApiFootballProvider(ANAHTAR) if ANAHTAR else DemoProvider()
STATIC = os.path.join(os.path.dirname(__file__), "static")


def analiz_et(mac_id):
    d = PROVIDER.detay(mac_id)
    o = d["ozet"]
    cikti = {"ozet": o, "ev": d["ev"], "dep": d["dep"], "h2h": d["h2h"],
             "istatistik": d["istatistik"], "kirmizi": d["kirmizi"],
             "mac_oncesi": analysis.mac_oncesi(d["ev"], d["dep"])}
    if o["durum"] == "canli":
        cikti["canli"] = analysis.canli(d["ev"], d["dep"], o["dakika"] or 0,
                                        tuple(o["skor"]), tuple(d["kirmizi"]), d["istatistik"])
    return cikti


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, kod=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        try:
            if u.path == "/api/maclar":
                mod = parse_qs(u.query).get("mod", ["canli"])[0]
                return self._json({"kaynak": PROVIDER.ad, "maclar": PROVIDER.maclar(mod)})
            if u.path.startswith("/api/analiz/"):
                return self._json(analiz_et(int(u.path.rsplit("/", 1)[1])))
        except Exception as e:  # API hatalarını arayüze ilet
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
