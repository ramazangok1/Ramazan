"""BIST günlük aday hisse tarayıcısı.

Kullanım:
    pip install yfinance pandas numpy
    python bist_tarayici.py              # varsayılan: 1000 TL, ilk 5 aday
    python bist_tarayici.py --sermaye 1000 --adet 5

Bu bir karar destek aracıdır, yatırım tavsiyesi değildir. Kâr garantisi yoktur.
"""
import argparse
import math

import numpy as np
import pandas as pd

# BIST 30 benzeri likit hisseler. Endeks bileşimi değişir; listeyi düzenleyebilirsin.
HISSELER = [
    "AKBNK", "AKSEN", "ARCLK", "ASELS", "BIMAS", "EKGYO", "ENKAI", "EREGL",
    "FROTO", "GARAN", "GUBRF", "HEKTS", "ISCTR", "KCHOL", "KRDMD", "MGROS",
    "ODAS", "PETKM", "PGSUS", "SAHOL", "SASA", "SISE", "TCELL", "THYAO",
    "TOASO", "TTKOM", "TUPRS", "VAKBN", "YKBNK",
]

KOMISYON = 0.001  # tek yön yaklaşık binde 1; kendi kurumuna göre değiştir
HEDEF_ATR_CARPAN = 1.0  # kâr hedefi = 1 x ATR
STOP_ATR_CARPAN = 1.0   # zarar durdur = 1 x ATR


def rsi(kapanis: pd.Series, n: int = 14) -> pd.Series:
    fark = kapanis.diff()
    kazanc = fark.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    kayip = (-fark.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = kazanc / kayip.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    onceki = df["Close"].shift()
    tr = pd.concat(
        [df["High"] - df["Low"], (df["High"] - onceki).abs(), (df["Low"] - onceki).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def analiz_et(sembol: str, df: pd.DataFrame, sermaye: float):
    """Tek hisse için puan ve işlem planı üretir; yetersiz veri varsa None döner."""
    df = df.dropna()
    if len(df) < 60:
        return None

    k = df["Close"]
    son = float(k.iloc[-1])
    sma20, sma50 = k.rolling(20).mean().iloc[-1], k.rolling(50).mean().iloc[-1]
    r = float(rsi(k).iloc[-1])
    a = float(atr(df).iloc[-1])
    hacim_orani = float(df["Volume"].iloc[-1] / df["Volume"].rolling(20).mean().iloc[-1])
    yuksek20 = float(df["High"].iloc[-21:-1].max())

    puan = 0
    nedenler = []
    if son > sma20 > sma50:
        puan += 2
        nedenler.append("yükseliş trendi (Fiyat > SMA20 > SMA50)")
    if 45 <= r <= 68:
        puan += 1
        nedenler.append(f"RSI sağlıklı bölgede ({r:.0f})")
    if hacim_orani >= 1.5:
        puan += 2
        nedenler.append(f"hacim ortalamanın {hacim_orani:.1f} katı")
    if son >= yuksek20:
        puan += 2
        nedenler.append("20 günlük zirve kırılımı")
    if r > 75:
        puan -= 2
        nedenler.append(f"aşırı alım riski (RSI {r:.0f})")

    lot = math.floor(sermaye / son)
    if lot < 1:
        return None

    hedef = son + HEDEF_ATR_CARPAN * a
    stop = son - STOP_ATR_CARPAN * a
    maliyet = lot * son
    net_kar = lot * (hedef - son) - maliyet * KOMISYON - lot * hedef * KOMISYON
    net_zarar = lot * (son - stop) + maliyet * KOMISYON + lot * stop * KOMISYON

    return {
        "sembol": sembol, "puan": puan, "fiyat": son, "lot": lot, "maliyet": maliyet,
        "hedef": hedef, "stop": stop, "net_kar": net_kar, "net_zarar": net_zarar,
        "rsi": r, "nedenler": nedenler,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sermaye", type=float, default=1000.0)
    ap.add_argument("--adet", type=int, default=5)
    args = ap.parse_args()

    import yfinance as yf

    sonuclar = []
    for s in HISSELER:
        df = yf.download(f"{s}.IS", period="6mo", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty:
            print(f"! {s}: veri alınamadı")
            continue
        sonuc = analiz_et(s, df, args.sermaye)
        if sonuc:
            sonuclar.append(sonuc)

    sonuclar.sort(key=lambda x: x["puan"], reverse=True)
    print(f"\nEn iyi {args.adet} aday (sermaye: {args.sermaye:.0f} TL)\n" + "-" * 60)
    for x in sonuclar[: args.adet]:
        print(f"{x['sembol']:6} puan={x['puan']}  fiyat={x['fiyat']:.2f}  {x['lot']} lot "
              f"({x['maliyet']:.0f} TL)")
        print(f"       hedef={x['hedef']:.2f} (net ~{x['net_kar']:+.1f} TL)  "
              f"stop={x['stop']:.2f} (net ~{-x['net_zarar']:.1f} TL)")
        print(f"       neden: {'; '.join(x['nedenler']) or '-'}")
    print("\nUyarı: Kâr garantisi yoktur. Stop-loss koymadan işlem yapma.")


if __name__ == "__main__":
    main()
