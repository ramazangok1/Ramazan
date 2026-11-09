"""Video'daki 'kod sifresi' yontemini sinar.

Kullanim:  python3 analiz.py maclar.csv
CSV'de ev_gol / dep_gol doldurulmus satirlar sinamaya girer.
Kod, 5 haneli STRING olmali (basindaki sifirlar korunur).
"""
import csv, sys
from math import comb

def tahmin(kod):
    """Videodaki kurallar. Kural disi ise None doner."""
    d = [int(c) for c in kod]
    if d.count(0) != 2:                     # Kural 1: tam iki sifir
        return None
    r = [x for x in d if x != 0]            # kalan 3 rakam
    tek = [x for x in r if x % 2]; cift = [x for x in r if x % 2 == 0]
    if len(tek) == 2 and len(cift) == 1:    # Kural 2-3
        return abs(tek[0] - tek[1]), cift[0]
    if len(cift) == 2 and len(tek) == 1:
        return tek[0], abs(cift[0] - cift[1])
    return None                             # 3 tek / 3 cift: kural disi

def sonuc(h, a): return (h > a) - (h < a)

def binom_p(k, n, p):                       # P(X >= k), tek yonlu
    return sum(comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))

def main(yol):
    rows = list(csv.DictReader(open(yol, encoding="utf-8")))
    gecen = [(r, tahmin(r["kod"])) for r in rows]
    gecen = [(r, t) for r, t in gecen if t]
    print(f"Toplam mac: {len(rows)} | kurali gecen: {len(gecen)}")
    print("\nKurali gecen maclar ve 'tahmin':")
    for r, (h, a) in gecen:
        sk = f" -> gercek {r['ev_gol']}-{r['dep_gol']}" if r["ev_gol"] != "" else ""
        print(f"  {r['kod']}  {r['ev']} - {r['deplasman']}: tahmin {h}-{a}{sk}")

    olcu = [(r, t) for r, t in gecen if r["ev_gol"] != "" and r["dep_gol"] != ""]
    tum = [r for r in rows if r["ev_gol"] != "" and r["dep_gol"] != ""]
    n = len(olcu)
    print(f"\nSkoru girilmis ve kurali gecen: n = {n}")
    if n == 0:
        print("Henuz sinanacak veri yok: ev_gol / dep_gol sutunlarini doldurun."); return
    if n < 30:
        print("UYARI: n < 30. Sonuc istatistiksel olarak anlamsizdir.")
    G = lambda r: (int(r["ev_gol"]), int(r["dep_gol"]))
    tam = sum(t == G(r) for r, t in olcu)
    snc = sum(sonuc(*t) == sonuc(*G(r)) for r, t in olcu)
    ust = sum((sum(t) > 2.5) == (sum(G(r)) > 2.5) for r, t in olcu)
    # Baseline: tum skorlu maclarda en iyi sabit tahmin orani
    ref = tum if tum else [r for r, _ in olcu]
    p_tam = max(sum(G(r) == s for r in ref) / len(ref) for s in {G(r) for r in ref})
    p_snc = max(sum(sonuc(*G(r)) == k for r in ref) / len(ref) for k in (-1, 0, 1))
    pu = sum(sum(G(r)) > 2.5 for r in ref) / len(ref); p_ust = max(pu, 1 - pu)
    print(f"\n{'Olcu':22}{'Isabet':>10}{'En iyi sabit tahmin':>22}{'p-degeri':>10}")
    for ad, k, p in [("Tam skor", tam, p_tam), ("Mac sonucu (1/X/2)", snc, p_snc), ("2,5 ust/alt", ust, p_ust)]:
        print(f"{ad:22}{f'{k}/{n}':>10}{p:>22.1%}{binom_p(k, n, p):>10.3f}")
    print("\np-degeri < 0.05 ve n yeterliyse yontem sanstan iyi demektir; aksi halde kanit yoktur.")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "maclar.csv")
