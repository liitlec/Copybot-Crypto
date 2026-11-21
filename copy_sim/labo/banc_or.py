"""Banc D : scalp sur l'or (XAUUSD) avec les VRAIES bougies et spreads du courtier (pont MT5, dossier mt5/donnees).
1) Cout : spread reel rapporte au mouvement d'une bougie, par symbole, par periode, par heure.
2) Scalp : familles de regles simples, cout = spread reel de la bougie d'entree/sortie (x MULT pour le glissement),
   reglage sur les 60 % premiers, verdict sur les 40 % derniers, compare a des entrees au hasard de meme frequence.
Les bougies MT5 sont des prix vendeur (bid) : un achat entre a bid + spread et sort a bid ; une vente entre a bid et
sort a bid + spread.
Usage : python3 banc_or.py [fichier_or.csv.gz ...]"""
import os, sys, json
import numpy as np, pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
DON = os.path.join(ICI, "mt5", "donnees")
MULT = 1.0          # multiplicateur du spread (1,5 = spread + 50 % de glissement)


def charge(ident):
    d = pd.read_csv(os.path.join(DON, ident + ".csv.gz"))
    d.index = pd.to_datetime(d["heure"], unit="s")          # horloge du serveur du courtier
    dec = max(len(("%.5f" % v).rstrip("0").split(".")[1]) for v in d["cloture"].iloc[:2000])
    d["sp"] = d["spread_points"] * 10.0 ** (-dec)            # spread en prix
    return d, dec


def tableau_couts(idents):
    print("== 1) Cout reel : spread du courtier contre mouvement d'une bougie ==")
    print("%-12s %7s %9s | spread bp : med  moy   p95 | |cloture-ouverture| med bp | amplitude med bp | spread/mouvement" % ("fichier", "bougies", "jours"))
    for i in idents:
        d, dec = charge(i)
        bp = 1e4 / d["cloture"]
        s = d["sp"] * bp
        m = (d["cloture"] - d["ouverture"]).abs() * bp
        a = (d["haut"] - d["bas"]) * bp
        print("%-12s %7d %9.0f |            %5.2f %5.2f %5.2f | %25.2f | %16.2f | %5.0f %%" % (
            i, len(d), (d.index[-1] - d.index[0]).days, s.median(), s.mean(), s.quantile(.95), m.median(), a.median(),
            100 * s.median() / m.median()))


def par_heure(ident):
    d, _ = charge(ident)
    bp = 1e4 / d["cloture"]
    g = pd.DataFrame({"spread": d["sp"] * bp, "mouv": (d["cloture"] - d["ouverture"]).abs() * bp}).groupby(d.index.hour)
    t = g.agg(spread_med=("spread", "median"), spread_p95=("spread", lambda x: x.quantile(.95)), mouv_med=("mouv", "median"))
    t["ratio_%"] = 100 * t.spread_med / t.mouv_med
    print("== Par heure (horloge du serveur) : %s ==" % ident)
    print(t.round(2).T.to_string())


# ---------------------------------------------------------------- scalp
def signaux(d):
    """Dictionnaire nom -> (serie de signaux -1/0/+1 decides a la cloture de la bougie, tenue h)."""
    c = d["cloture"]
    lr = np.log(c)
    out = {}
    for k in (1, 3, 12):
        for h in (1, 3, 12):
            s = np.sign(lr - lr.shift(k))
            out["elan k%d h%d" % (k, h)] = (s, h)
            out["retour k%d h%d" % (k, h)] = (-s, h)
    for n in (12, 48):
        haut, bas = d["haut"].shift(1).rolling(n).max(), d["bas"].shift(1).rolling(n).min()
        s = (c > haut).astype(int) - (c < bas).astype(int)
        for h in (3, 12):
            out["cassure n%d h%d" % (n, h)] = (s, h)
            out["fausse cassure n%d h%d" % (n, h)] = (-s, h)
    r = lr.diff()
    z = r / r.rolling(100).std().shift(1)
    s = (z > 3).astype(int) - (z < -3).astype(int)
    for h in (3, 12):
        out["exces suivi h%d" % h] = (s, h)
        out["exces contre h%d" % h] = (-s, h)
    return out


def trades(d, s, h, mult=MULT):
    """Trades non chevauchants : decision a la cloture i, entree a l'ouverture i+1, sortie a la cloture i+h. En bp."""
    o, c, sp = d["ouverture"].values, d["cloture"].values, d["sp"].values * mult
    s = np.nan_to_num(s.values)
    res, idx, i, n = [], [], 0, len(c)
    while i < n - h - 1:
        if s[i] != 0:
            e, x = i + 1, i + h
            if s[i] > 0:
                g = (c[x] - (o[e] + sp[e])) / o[e]
            else:
                g = (o[e] - (c[x] + sp[x])) / o[e]
            brut = s[i] * (c[x] - o[e]) / o[e]
            res.append((g * 1e4, brut * 1e4)); idx.append(i)
            i = x
        else:
            i += 1
    return np.array(res).reshape(-1, 2), np.array(idx)


def t_stat(x):
    return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 20 and x.std() > 0 else np.nan


def banc_scalp(ident):
    d, _ = charge(ident)
    m = int(len(d) * 0.6)
    d1, d2 = d.iloc[:m], d.iloc[m:]
    print("\n== 2) Scalp sur %s : %d bougies, reglage %s -> %s, verdict -> %s ==" % (ident, len(d), d.index[0], d.index[m], d.index[-1]))
    s1, s2 = signaux(d1), signaux(d2)
    lignes = []
    for nom in s1:
        a, _ = trades(d1, *s1[nom])
        b, _ = trades(d2, *s2[nom])
        if len(a) < 30 or len(b) < 30:
            continue
        lignes.append((a[:, 0].mean(), nom, len(a), a[:, 1].mean(), t_stat(a[:, 0]), len(b), b[:, 1].mean(), b[:, 0].mean(), t_stat(b[:, 0])))
    lignes.sort(reverse=True)
    print("%-22s | reglage : trades brut  net   t   | verdict : trades  brut   net    t" % "regle (%d essayees)" % len(lignes))
    for net1, nom, n1, b1, t1, n2, b2, net2, t2 in lignes:
        print("%-22s | %7d %+6.2f %+6.2f %+5.1f | %7d %+6.2f %+6.2f %+5.1f" % (nom, n1, b1, net1, t1, n2, b2, net2, t2))
    pos = [l for l in lignes if l[0] > 0]
    print("Regles gagnantes nettes au reglage : %d sur %d ; parmi elles, gagnantes au verdict : %d" % (
        len(pos), len(lignes), sum(1 for l in pos if l[7] > 0)))
    best = lignes[0]
    print("Meilleure au reglage : %s -> verdict net %+.2f bp/trade (t=%+.1f, %d trades)" % (best[1], best[7], best[8], best[5]))
    # hasard de meme frequence que la meilleure regle, sur la partie verdict
    s, h = s2[best[1]]
    rng = np.random.default_rng(5)
    freq = (np.nan_to_num(s.values) != 0).mean()
    tir = []
    for _ in range(100):
        al = pd.Series(rng.choice([-1, 0, 1], len(d2), p=[freq / 2, 1 - freq, freq / 2]), index=d2.index)
        x, _ = trades(d2, al, h)
        tir.append(x[:, 0].mean())
    print("Hasard meme frequence (100 tirages, verdict) : net moyen %+.2f bp, 95e centile %+.2f bp" % (np.mean(tir), np.percentile(tir, 95)))
    return len(lignes)


if __name__ == "__main__":
    idx = json.load(open(os.path.join(DON, "index.json")))
    ok = [k for k, v in idx.items() if "fichier" in v]
    tableau_couts(ok)
    for i in ok:
        if "m1" in i or "m5" in i:
            par_heure(i)
    n = 0
    for i in (sys.argv[1:] or [k for k in ok if k.startswith("xau")]):
        n += banc_scalp(i)
    print("\nEssais de ce banc :", n)
