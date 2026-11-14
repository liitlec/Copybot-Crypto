"""Banc L : concepts « liquidite » des scalpeurs sur l'or (M5 du courtier, 15 mois, spread reel).
Entree au marche a l'ouverture de la bougie suivante, sortie au temps (h bougies M5), spread de l'entree paye.
  A. Chasse aux stops : meche au-dela du haut/bas de la seance d'Asie (1 h - 9 h serveur) ou de la veille, cloture
     revenue a l'interieur -> on contre (« sweep »). Variante : cloture au-dela -> on suit (cassure).
  B. Niveaux ronds (multiples de 10 $ et de 50 $) : franchissement a la cloture -> on suit ou on contre.
  C. Ecart de juste valeur (« fair value gap ») : trou entre la bougie i-2 et i ; quand le prix revient dans le trou
     (24 bougies au plus) -> on repart dans le sens du trou.
  D. Retour vers le VWAP de la seance : ecart au VWAP > 2 ecarts-types de la seance -> on contre.
Reglage sur 60 %, verdict sur 40 %. bp nets par trade. Usage : python3 banc_liquidite.py"""
import numpy as np, pandas as pd
import banc_grille as G

TENUES = (3, 6, 12, 24)


def evalue(d, signaux, nom, lignes):
    """signaux : liste (indice de la bougie de decision, sens)."""
    o, c, sp = d["ouverture"].values, d["cloture"].values, d["sp"].values
    n = len(c); coupe = int(n * 0.6)
    if not signaux:
        return
    i = np.array([s[0] for s in signaux]); sens = np.array([s[1] for s in signaux], float)
    for h in TENUES:
        ok = i + h < n - 1
        ii, ss = i[ok], sens[ok]
        e = o[ii + 1]
        g = (ss * (c[ii + h] - e) - sp[ii + 1]) / e * 1e4
        for lab, sg in (("", 1.0), (" (inverse)", -1.0)):
            gg = (sg * ss * (c[ii + h] - e) - sp[ii + 1]) / e * 1e4
            a, b = gg[ii < coupe], gg[ii >= coupe]
            t = lambda v: v.mean() / v.std() * np.sqrt(len(v)) if len(v) > 20 and v.std() > 0 else float("nan")
            lignes.append((nom + lab, h, len(a), a.mean() if len(a) else np.nan, t(a), len(b), b.mean() if len(b) else np.nan, t(b)))


if __name__ == "__main__":
    d = G.charge("xau_m5_90k")
    d["jour"] = (d["heure"] - 3600) // 86400          # journee de marche : de 1 h a 1 h serveur
    d["mn"] = d["h"] * 60 + (d["heure"] // 60) % 60
    hi, lo, c, o, vol = (d[x].values for x in ("haut", "bas", "cloture", "ouverture", "volume_ticks"))
    lignes = []
    asia_s, asia_b, veille_s, veille_b, vwap_s = [], [], [], [], []
    prec = None
    for jour, x in d.groupby("jour"):
        idx = x.index.values
        mn = x["mn"].values
        asie = idx[(mn >= 60) & (mn < 540)]
        apres = idx[(mn >= 540) & (mn < 1200)]
        if len(asie) > 50 and len(apres) > 20:
            H, L = hi[asie].max(), lo[asie].min()
            for niveaux, sweep, casse in (((H, L), asia_s, asia_b),) + ((((prec[0], prec[1]), veille_s, veille_b),) if prec else ()):
                NH, NL = niveaux
                fait = set()
                for k in (idx[(mn >= 540) & (mn < 1200)] if niveaux == (H, L) else idx[(mn >= 120) & (mn < 1200)]):
                    if "sh" not in fait and hi[k] > NH and c[k] < NH:
                        sweep.append((k, -1)); fait.add("sh")
                    if "sl" not in fait and lo[k] < NL and c[k] > NL:
                        sweep.append((k, 1)); fait.add("sl")
                    if "bh" not in fait and c[k] > NH:
                        casse.append((k, 1)); fait.add("bh")
                    if "bl" not in fait and c[k] < NL:
                        casse.append((k, -1)); fait.add("bl")
        if len(idx) > 100:
            prec = (hi[idx].max(), lo[idx].min())
            tp = (hi[idx] + lo[idx] + c[idx]) / 3
            vw = np.cumsum(tp * vol[idx]) / np.maximum(np.cumsum(vol[idx]), 1)
            ec = c[idx] - vw
            sd = pd.Series(ec).expanding(36).std().shift(1).values
            dern = -99
            for q in range(36, len(idx)):
                if sd[q] > 0 and abs(ec[q]) > 2 * sd[q] and q - dern >= 6 and 120 <= mn[q] < 1320:
                    vwap_s.append((idx[q], -int(np.sign(ec[q])))); dern = q
    evalue(d, asia_s, "A. chasse aux stops, Asie : contrer", lignes)
    evalue(d, asia_b, "A. cassure du range d'Asie : suivre", lignes)
    evalue(d, veille_s, "A. chasse aux stops, veille : contrer", lignes)
    evalue(d, veille_b, "A. cassure haut/bas de veille : suivre", lignes)
    for pas in (10, 50):
        niv_avant, niv_apres = np.floor(c[:-1] / pas), np.floor(c[1:] / pas)
        k = np.where(niv_avant != niv_apres)[0] + 1
        evalue(d, [(q, int(np.sign(c[q] - c[q - 1]))) for q in k], "B. niveau rond de %d $ franchi : suivre" % pas, lignes)
    sp = d["sp"].values
    fvg = []
    for q in range(2, len(c) - 30):
        if lo[q] - hi[q - 2] > 3 * sp[q]:                 # trou haussier
            z = np.where(lo[q + 1:q + 25] <= lo[q])[0]
            if len(z):
                fvg.append((q + 1 + z[0], 1))
        elif lo[q - 2] - hi[q] > 3 * sp[q]:               # trou baissier
            z = np.where(hi[q + 1:q + 25] >= hi[q])[0]
            if len(z):
                fvg.append((q + 1 + z[0], -1))
    evalue(d, fvg, "C. ecart de juste valeur comble : repartir", lignes)
    evalue(d, vwap_s, "D. retour vers le VWAP (> 2 ecarts-types)", lignes)
    print("XAUUSD M5, %d bougies. Par ligne : trades et bp nets au reglage (60 %%) puis au verdict (40 %%)" % len(d))
    print("%-52s %3s | %6s %7s %6s | %6s %7s %6s" % ("idee", "h", "n", "regl.", "t", "n", "verdict", "t"))
    for l in lignes:
        print("%-52s %3d | %6d %+7.2f %+6.1f | %6d %+7.2f %+6.1f" % l)
    pos = [l for l in lignes if l[3] > 0 and l[4] > 1]
    print("\n%d essais ; t > 1 au reglage : %d ; parmi eux positifs au verdict : %d ; t > 2 au verdict : %d" % (
        len(lignes), len(pos), sum(l[6] > 0 for l in pos), sum(l[7] > 2 for l in pos)))
    for l in sorted(pos, key=lambda l: -l[7])[:8]:
        print("  %-52s h=%-2d regl. %+6.2f (t=%+.1f, %d) -> verdict %+6.2f (t=%+.1f, %d)" % (l[0], l[1], l[3], l[4], l[2], l[6], l[7], l[5]))
