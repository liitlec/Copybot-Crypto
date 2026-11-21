"""Banc E : recherche massive de scalps par grille, sur les bougies et spreads du courtier (mt5/donnees).
Grille par fichier : 18 signaux x 2 sens (suivre / contrer) x 7 tenues x 9 filtres d'heure x 3 filtres de volatilite
= 6 804 combinaisons. Entree a l'ouverture de la bougie suivante, sortie a la cloture h bougies plus tard, spread reel
de la bougie d'entree paye. Les trades se chevauchent : le t est divise par racine(h) (prudent).
Garde-fous : reglage sur les 60 % premiers, verdict sur les 40 % derniers ; le meilleur de N est compare au meilleur
de N obtenu avec les MEMES entrees mais un sens tire a pile ou face (ce que le hasard donne apres autant d'essais).
Usage : python3 banc_grille.py [ident ...]"""
import os, sys, json
import numpy as np, pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
DON = os.path.join(ICI, "mt5", "donnees")
TENUES = (1, 3, 5, 10, 15, 30, 60)
MIN_TRADES = 300


def charge(ident):
    d = pd.read_csv(os.path.join(DON, ident + ".csv.gz"))
    dec = max(len(("%.5f" % v).rstrip("0").split(".")[1]) for v in d["cloture"].iloc[:2000])
    d["sp"] = d["spread_points"] * 10.0 ** (-dec)
    d["h"] = (d["heure"] // 3600) % 24
    return d


def signaux(d):
    c, lr = d["cloture"], np.log(d["cloture"])
    out = {}
    for k in (1, 2, 3, 5, 10, 20, 60):
        out["elan%d" % k] = np.sign(lr - lr.shift(k))
    for n in (10, 20, 48, 120, 240):
        ha, ba = d["haut"].shift(1).rolling(n).max(), d["bas"].shift(1).rolling(n).min()
        out["cassure%d" % n] = (c > ha).astype(float) - (c < ba).astype(float)
    r = lr.diff()
    z = r / r.rolling(100).std().shift(1)
    for s in (2, 3, 4):
        out["exces%d" % s] = (z > s).astype(float) - (z < -s).astype(float)
    for n in (20, 60, 240):
        e = (c - c.rolling(n).mean()) / c.rolling(n).std()
        out["ecart%d" % n] = (e > 2).astype(float) - (e < -2).astype(float)
    return {k: v.fillna(0).values.astype(np.float32) for k, v in out.items()}


def masques(d):
    n = len(d)
    m, noms = [np.ones(n, bool)], ["toutes heures"]
    for b in range(8):
        m.append((d["h"].values // 3) == b); noms.append("%02d-%02dh serveur" % (3 * b, 3 * b + 3))
    a = np.log(d["cloture"]).diff().abs().rolling(60).mean()
    med = a.rolling(1440, min_periods=300).median()
    vols = [(np.ones(n, bool), "toute vol."), ((a > med).values, "vol. haute"), ((a <= med).values, "vol. basse")]
    M, N = [], []
    for mh, nh in zip(m, noms):
        for mv, nv in vols:
            M.append(mh & mv); N.append((nh, nv))
    return np.array(M, dtype=np.float32), N


def grille(d, S, M, coupe, alea=None):
    """Rend un tableau (config) x [n1, moy1, t1, n2, moy2, t2] en bp nets, et la liste des configs."""
    o, c, sp = d["ouverture"].values, d["cloture"].values, d["sp"].values
    n = len(c)
    res, cfg = [], []
    seg = [np.arange(n) < coupe, np.arange(n) >= coupe]
    for nom, s in S.items():
        if alea is not None:
            s = np.abs(s) * alea.choice(np.array([-1, 1], np.float32), n)
        for h in TENUES:
            ent = np.roll(o, -1); sor = np.roll(c, -h); spe = np.roll(sp, -1)
            ok = np.ones(n, bool); ok[n - h - 1:] = False
            brut = np.where(ok, (sor - ent) / ent * 1e4, 0).astype(np.float32)
            cout = np.where(ok, spe / ent * 1e4, 0).astype(np.float32)
            actif = ((s != 0) & ok).astype(np.float32)
            for sens, ns in ((1, "suivre"), (-1, "contrer")):
                g = (sens * s * brut - cout) * actif
                ligne = []
                for sg in seg:
                    Ms = M * sg.astype(np.float32)
                    cnt = Ms @ actif
                    som = Ms @ g
                    sq = Ms @ (g * g)
                    moy = som / np.maximum(cnt, 1)
                    var = np.maximum(sq / np.maximum(cnt, 1) - moy ** 2, 1e-12)
                    t = moy / np.sqrt(var) * np.sqrt(np.maximum(cnt, 1) / h)
                    ligne += [cnt, moy, t]
                res.append(np.array(ligne).T)
                cfg += [(nom, ns, h, i) for i in range(M.shape[0])]
    return np.concatenate(res), cfg


def etude(ident, tirages=5):
    d = charge(ident)
    S, (M, noms) = signaux(d), masques(d)
    coupe = int(len(d) * 0.6)
    R, cfg = grille(d, S, M, coupe)
    ok = (R[:, 0] >= MIN_TRADES) & (R[:, 3] >= MIN_TRADES * 0.5)
    R1 = R[ok]; C1 = [c for c, k in zip(cfg, ok) if k]
    print("\n===== %s : %d bougies, %d combinaisons dont %d avec assez de trades =====" % (ident, len(d), len(R), len(R1)))
    pos = R1[:, 1] > 0
    fort = R1[:, 2] > 2
    print("Reglage : %d nettes positives (%.1f %%), %d avec t > 2. Meilleur t au reglage : %.2f" % (
        pos.sum(), 100 * pos.mean(), fort.sum(), R1[:, 2].max()))
    print("Verdict : des %d positives au reglage, %d le restent (%.0f %%) ; des %d a t > 2, %d restent positives, %d ont t > 2 au verdict" % (
        pos.sum(), (R1[pos, 4] > 0).sum(), 100 * (R1[pos, 4] > 0).mean() if pos.any() else 0,
        fort.sum(), (R1[fort, 4] > 0).sum(), (R1[fort, 5] > 2).sum()))
    print("Toutes periodes : part des combinaisons positives au verdict = %.1f %%" % (100 * (R1[:, 4] > 0).mean()))
    rng = np.random.default_rng(11)
    mx = []
    for _ in range(tirages):
        Ra, _ = grille(d, S, M, coupe, alea=rng)
        mx.append(Ra[ok, 2].max())
    print("Hasard (memes entrees, sens a pile ou face, %d tirages) : meilleur t au reglage = %s" % (tirages, " ".join("%.2f" % x for x in mx)))
    ordre = np.argsort(-R1[:, 2])[:12]
    print("Les 12 meilleures au reglage -> verdict (bp nets par trade) :")
    for i in ordre:
        nom, ns, h, im = C1[i]
        print("  %-10s %-7s h=%-2d %-16s %-10s | regl. n=%6d %+6.2f t=%+5.2f | verdict n=%6d %+6.2f t=%+5.2f" % (
            nom, ns, h, noms[im][0], noms[im][1], R1[i, 0], R1[i, 1], R1[i, 2], R1[i, 3], R1[i, 4], R1[i, 5]))
    return len(R), R1, C1, noms


if __name__ == "__main__":
    idx = json.load(open(os.path.join(DON, "index.json")))
    ids = sys.argv[1:] or ["xau_m1_90k", "xau_m5_90k", "xag_m1_90k", "nas_m1_90k", "sp_m1_90k", "ger_m1_90k"]
    tot = 0
    for i in ids:
        if "fichier" in idx.get(i, {}):
            tot += etude(i)[0]
    print("\nTotal des combinaisons de ce banc :", tot)
