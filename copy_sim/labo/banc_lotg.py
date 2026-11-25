"""Banc Lot G (PRIORITES 25/11 22 h, demande ecrite de Baptiste) : ameliorer ce qu'on garde en v28.
CONTRAT FIGE ET POUSSE AVANT TOUT RESULTAT.

DONNEES (courtier, spread reel de chaque bougie ; stress = spread x 2) :
  M5  xau_m5_90k 08/2025 -> 11/2026 (15 mois) ; M15 xau_m15_50k sur la meme periode ; M1 xau_m1_90k (3 mois seulement,
  08 -> 11/2026 : exces_m1 jugee sur 3 mois, dit comme tel) ; H1 xau_h1_50k 08/2022 -> 11/2026 (4 ans, blocs
  B1 = 08/2022-09/2024 et B2 = 10/2024-11/2026). Heures serveur = Paris + 1 h.

PARTIE 1 — SORTIES DE bt_or_plus (mecanique du robot : entrees bt_or aux heures fixes, sens EMA 2 jours, renforts tous
  les 0,25 ATR de taille 1, 2, 3, 4, 5, 5 positions au plus, recul de 0,6667 ATR depuis le meilleur prix ; gain en R
  de la position de base : 1 R = perte d'une position de taille 1 au stop initial). M5 : span 576, heures bt_or M5 ;
  H1 : span 48, heures H1 du socle. Convention de BR.simule (achat a cloture + spread, sortie au niveau, vente
  declenchee par haut + spread). Variantes (11, grille fixee) :
    REF      bt_or_plus tel quel
    a35, a50 les 2 derniers renforts (positions 4 et 5) sortent seuls a un recul de 0,35 / 0,50 ATR depuis le meilleur
             prix (le reste du panier garde 0,6667) ; pas de remise.
    b36, b24 paliers : recul 0,6667 -> 0,5 -> 0,35 ATR quand le meilleur prix depasse +3 / +6 R (b36) ou +2 / +4 R (b24)
             depuis la 1re entree.
    c05, c10 chaque renfort (positions 2 a 5) encaisse a +0,5 / +1,0 ATR de son entree (ordre limite au niveau).
    d        stop au point mort du panier (prix moyen pondere) des que la 4e position est ouverte (3e renfort).
    e4, e8   sortie de tout le panier a la cloture qui repasse du mauvais cote de la moyenne mobile exponentielle de
             4 h / 8 h (M5 : 48 / 96 bougies ; H1 : 4 / 8).
    serre    temoin bt_or_serre (deja perdant en direct) : au-dela de +3 R, recul 0,5 R (= 0,333 ATR).
  Mesures par jeu : paniers, total R, pire baisse (cumul des paniers par jour de sortie), gain/pire baisse, Sharpe
  journalier (par jour de sortie, x racine 252), « gain rendu » moyen par panier = latent max (aux clotures) - gain
  ferme, « grands paniers coupes » = paniers de REF a >= +5 R dont le panier de meme ouverture de la variante fait moins
  de la moitie. Appariement des paniers par bougie d'ouverture.
  Tests : placebo = changement de signe au hasard des differences appariees variante - REF (2000 tirages) sur M5 et
  sur H1 ; reality check de White (bootstrap stationnaire par paniers, blocs moyens 5) sur les 10 variantes ->
  p corrige. Walk-forward (M5 6 -> 1 mois ; H1 12 -> 3 mois) : variante au meilleur gain/pire baisse d'apprentissage.
  RETENUE si : gain/pire baisse ET Sharpe > REF sur M5, sur H1 B1 ET sur H1 B2 ; p corrige < 0,05 sur un jeu et
  < 0,15 sur l'autre ; walk-forward >= REF sur les deux jeux ; encore > REF au spread double.

PARTIE 2 — REGLES COURTES (trades non chevauchants, decision a la cloture i, entree a l'ouverture i+1, sortie a la
  cloture i+h, stop eventuel en ATR jour 20 j touche dans la bougie = sortie au niveau ; gain en $ pour 0,01 lot).
  Regle telle quelle (REF) = celle du robot. Grilles (fixees) :
    elan_m15    : recul k {8, 12, 16} bougies x tenue h {8, 12, 16}                     (REF k 12, h 12)
    cassure_m15 : fourchette k {32, 48, 64} x tenue h {8, 12, 16}                         (REF 48, 12)
    exces_m5    : seuil z {2,5 ; 3 ; 3,5} x tenue h {2, 3, 6}, on suit                    (REF 3, 3)
    exces_m1    : seuil z {2,5 ; 3 ; 3,5} x tenue h {6, 12, 20}, on contre                (REF 3, 12)
    retour_court_ar (M15) : ecart z {2 ; 2,5 ; 3} x tenue {8, 12}, objectif milieu du range du jour, stop court
                  (extreme des 2 dernieres bougies + 0,5 $)                               (REF 2,5, 12)
    x stop {aucun, 0,5 ATR} (sauf retour_court_ar : son stop court) x heures {toutes, sans 10, 16, 17, 22 h serveur =
    9, 15-16, 21 h Paris} x lien bt_or {aucun ; tendances (elan, cassure, exces_m5) seulement dans le sens du panier
    bt_or_plus ouvert, contre-tendances (exces_m1, retour_court_ar) seulement a l'oppose ; sans panier ouvert : pas de
    trade}. Filtres heures et lien appliques a la liste de trades du reglage.
  Walk-forward glissant 6 -> 1 mois (reglage au meilleur t d'apprentissage ; M1 : 1 -> 1 mois). Placebo : memes
  reglages mais filtres heures et lien remplaces par un tri au hasard de meme taux de garde par mois (500 tirages) ;
  p = part des placebos au total walk-forward >= reel. Controle H1 4 ans (elan, cassure, retour) : le reglage le plus
  choisi, transpose en H1 (k et h divises par 4), contre la regle telle quelle transposee, en B1 et B2.
  RETENU si : walk-forward > REF dans chaque moitie de la periode de test ET placebo p < 0,05 ET > REF au spread
  double ET (regles M15) controle H1 > REF en B1 et B2.

PARTIE 3 — ENSEMBLE en $ (0,01 lot de base) : bt_or_plus REF + regles telles quelles, contre bt_or_plus (variante
  retenue s'il y en a) + regles en walk-forward ; a risque egal (meme ecart-type journalier) : total, pire baisse,
  part des semaines perdantes, sur les deux moities de la periode M5.
PARTIE 4 — variante demo `_opt` (v29) seulement pour ce qui est RETENU. Resultats en tete d'AVIS.md.
Usage : python3 banc_lotg.py
"""
import os, sys, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR
import banc_or as B

ICI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(25)
H1H = {(2, 0), (7, 0), (11, 0), (14, 0), (15, 0)}
VARS = {"REF": {}, "a35": {"a": 0.35}, "a50": {"a": 0.50}, "b36": {"b": (3, 6)}, "b24": {"b": (2, 4)},
        "c05": {"c": 0.5}, "c10": {"c": 1.0}, "d": {"d": 1}, "e4": {"e": 4}, "e8": {"e": 8}, "serre": {"serre": 1}}
B1F, B2_0 = pd.Timestamp("2024-09-30 23:59"), pd.Timestamp("2024-10-01")


def plus(d, v, span, heures, debut, bars_h, mult=1.0):
    """bt_or_plus avec une variante de sortie. Rend un DataFrame de paniers (i0, i1, t1, s, g en R, mfe en R)."""
    c, hi, lo, t = (d[x].values for x in ("cloture", "haut", "bas", "heure"))
    sp = d["sp"].values * mult
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    em = d["cloture"].ewm(span=v["e"] * bars_h, min_periods=v["e"] * bars_h).mean().values if "e" in v else None
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    P, ouvert = [], {}

    def sortie_pos(p, k, x):
        p["real"] += p["w"][k] * p["s"] * (x - p["e"][k]); p["vivant"][k] = False

    def ferme(p, i, x):
        for k in range(len(p["e"])):
            if p["vivant"][k]:
                sortie_pos(p, k, x)
        P.append((p["i"], i, t[i], p["s"], p["real"] / p["stop"], p["mfe"], p["stop"]))

    for i in range(debut, len(c)):
        for s in list(ouvert):
            p = ouvert[s]; A = p["stop"] / 0.6667
            gR = s * (p["meilleur"] - p["e"][0]) / p["stop"]
            dist = p["stop"]
            if "b" in v:
                dist = 0.35 * A if gR >= v["b"][1] else (0.5 * A if gR >= v["b"][0] else dist)
            if "serre" in v and gR >= 3:
                dist = 0.5 * p["stop"]
            niveau = p["meilleur"] - s * dist
            if "d" in v and len(p["e"]) >= 4:
                viv = [k for k in range(len(p["e"])) if p["vivant"][k]]
                moy = sum(p["w"][k] * p["e"][k] for k in viv) / sum(p["w"][k] for k in viv)
                niveau = max(niveau, moy) if s > 0 else min(niveau, moy)
            touche = (lo[i] <= niveau) if s > 0 else (hi[i] + sp[i] >= niveau)
            if touche:
                ferme(p, i, niveau); del ouvert[s]; continue
            if "a" in v:                                   # positions 4 et 5 : recul serre a part
                nv = p["meilleur"] - s * v["a"] * A
                if ((lo[i] <= nv) if s > 0 else (hi[i] + sp[i] >= nv)):
                    for k in (3, 4):
                        if k < len(p["e"]) and p["vivant"][k]:
                            sortie_pos(p, k, nv)
            if "c" in v:                                   # renforts encaisses a +x ATR
                for k in range(1, len(p["e"])):
                    if p["vivant"][k]:
                        obj = p["e"][k] + s * v["c"] * A
                        if (hi[i] >= obj) if s > 0 else (lo[i] + sp[i] <= obj):
                            sortie_pos(p, k, obj)
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            x = c[i] if s > 0 else c[i] + sp[i]
            if "e" in v and em[i] == em[i] and s * (c[i] - em[i]) < 0:
                ferme(p, i, x); del ouvert[s]; continue
            while len(p["e"]) < 5 and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i])); p["w"].append(float(len(p["e"]))); p["vivant"].append(True)
                p["prochain"] += s * p["pas"]
            lat = p["real"] + sum(p["w"][k] * s * (x - p["e"][k]) for k in range(len(p["e"])) if p["vivant"][k])
            p["mfe"] = max(p["mfe"], lat / p["stop"])
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "s": s, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "w": [1.0], "vivant": [True],
                             "meilleur": c[i], "stop": BR.STOP * atr[i], "pas": BR.PAS * atr[i],
                             "prochain": c[i] + s * BR.PAS * atr[i], "real": 0.0, "mfe": 0.0, "usd": c[i]}
    P = pd.DataFrame(P, columns=["i0", "i1", "t1", "s", "g", "mfe", "stop"])
    P["t0"] = t[P.i0.values] if len(P) else []
    P["jour"] = pd.to_datetime(P.t1, unit="s").dt.floor("D")
    return P


def jeu_m5():
    d = BR.charge("xau_m5_90k"); return d, dict(span=576, heures=BR.H_M5, debut=600, bars_h=12)


def jeu_h1():
    d = BR.charge("xau_h1_50k"); d = d[d.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    return d, dict(span=48, heures=H1H, debut=60, bars_h=1)


def mesures(P, ref=None):
    x = P.groupby("jour").g.sum(); eq = x.cumsum(); dd = (eq - eq.cummax()).min()
    out = dict(paniers=len(P), total=P.g.sum(), creux=dd, g_creux=P.g.sum() / -dd if dd < 0 else np.inf,
               sharpe=x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0, rendu=(P.mfe - P.g).mean())
    if ref is not None:
        m = ref.merge(P, on="i0", suffixes=("_r", "_v"))
        grands = m[m.g_r >= 5]
        out["grands_coupes"] = "%d/%d" % ((grands.g_v < 0.5 * grands.g_r).sum(), len(grands))
    return out


def apparie(ref, P):
    m = ref.merge(P, on="i0", suffixes=("_r", "_v"))
    return (m.g_v - m.g_r).values


def signe_placebo(dif, n=2000):
    obs = dif.sum()
    return (np.array([(dif * rng.choice((-1, 1), len(dif))).sum() for _ in range(n)]) >= obs).mean()


def partie1():
    print("PARTIE 1 : sorties de bt_or_plus")
    R = {}
    for nom_j, f in (("M5", jeu_m5), ("H1", jeu_h1)):
        d, kw = f()
        for mult in (1.0, 2.0):
            R[(nom_j, mult)] = {v: plus(d, prm, mult=mult, **kw) for v, prm in VARS.items()}
    lignes = []
    for nom_j in ("M5", "H1"):
        Rj, Rj2 = R[(nom_j, 1.0)], R[(nom_j, 2.0)]
        ref = Rj["REF"]
        difs = {v: apparie(ref, Rj[v]) for v in VARS if v != "REF"}
        n = min(len(x) for x in difs.values())
        Dm = np.column_stack([difs[v][:n] for v in difs])
        _, pw = BR.white(Dm)
        for v in VARS:
            P = Rj[v]; m = mesures(P, ref if v != "REF" else None)
            row = dict(jeu=nom_j, variante=v, **m)
            if nom_j == "H1":
                for bn, msk in (("B1", P.jour <= B1F), ("B2", P.jour >= B2_0)):
                    mb = mesures(P[msk].reset_index(drop=True)); row[bn + "_gc"] = mb["g_creux"]; row[bn + "_sh"] = mb["sharpe"]
            m2 = mesures(R[(nom_j, 2.0)][v]); row["total_x2"] = m2["total"]; row["gc_x2"] = m2["g_creux"]
            if v != "REF":
                row["placebo_p"] = signe_placebo(difs[v]); row["white_p"] = pw
            lignes.append(row)
    T = pd.DataFrame(lignes)
    # walk-forward
    for nom_j, (app, tst) in (("M5", (6, 1)), ("H1", (12, 3))):
        Rj = R[(nom_j, 1.0)]
        mois = sorted(set(Rj["REF"].jour.dt.to_period("M")))
        wf, rf, choix = [], [], []
        for k in range(app, len(mois), tst):
            tr, te = mois[k - app:k], mois[k:k + tst]
            def gc(P, ms):
                x = P[P.jour.dt.to_period("M").isin(ms)]; mm = mesures(x) if len(x) > 2 else {"g_creux": -9}
                return mm["g_creux"] if np.isfinite(mm["g_creux"]) else 99
            best = max(VARS, key=lambda v: gc(Rj[v], tr)); choix.append(best)
            wf.append(Rj[best][Rj[best].jour.dt.to_period("M").isin(te)].g.sum())
            rf.append(Rj["REF"][Rj["REF"].jour.dt.to_period("M").isin(te)].g.sum())
        T.loc[T.jeu == nom_j, "wf_total"] = sum(wf); T.loc[T.jeu == nom_j, "wf_ref"] = sum(rf)
        print("  walk-forward %s : %+.1f R contre REF %+.1f R ; choix %s" % (nom_j, sum(wf), sum(rf), pd.Series(choix).value_counts().to_dict()))
    ref_ = {j: T[(T.jeu == j) & (T.variante == "REF")].iloc[0] for j in ("M5", "H1")}
    def retenue(r):
        if r.variante == "REF": return False
        m5 = T[(T.jeu == "M5") & (T.variante == r.variante)].iloc[0]; h1 = T[(T.jeu == "H1") & (T.variante == r.variante)].iloc[0]
        ok = (m5.g_creux > ref_["M5"].g_creux and m5.sharpe > ref_["M5"].sharpe and h1.B1_gc > ref_["H1"].B1_gc and h1.B1_sh > ref_["H1"].B1_sh
              and h1.B2_gc > ref_["H1"].B2_gc and h1.B2_sh > ref_["H1"].B2_sh)
        ps = sorted([m5.white_p, h1.white_p]); ok = ok and ps[0] < 0.05 and ps[1] < 0.15
        ok = ok and m5.wf_total >= m5.wf_ref and h1.wf_total >= h1.wf_ref
        return bool(ok and m5.total_x2 > ref_["M5"].total_x2 and h1.total_x2 > ref_["H1"].total_x2)
    T["retenue"] = T.apply(retenue, axis=1)
    T.to_csv(os.path.join(ICI, "donnees", "lotg_sorties.csv"), index=False)
    pd.set_option("display.width", 300)
    print(T.drop(columns=["wf_total", "wf_ref"]).round(2).to_string(index=False))
    return R


# ------------------------------------------------------------------------------------------------ partie 2
COUPE = {10, 16, 17, 22}
TEND = {"elan_m15", "cassure_m15", "exces_m5"}


def charge_tf(ident, debut):
    d, _ = B.charge(ident); d = d[~d.index.duplicated()].sort_index()
    return d[d.index >= debut]


def atr_jour(d):
    j = d.groupby(d.index.floor("D")).agg(h=("haut", "max"), l=("bas", "min"), c=("cloture", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift()).abs(), (j.l - j.c.shift()).abs()))
    return tr.rolling(20).mean().shift(1).reindex(d.index.floor("D")).values


def signal(d, regle, k):
    c = d["cloture"]
    if regle == "elan":
        lr = np.log(c); return np.sign(lr - lr.shift(k)).fillna(0).values
    if regle == "cassure":
        ha, ba = d["haut"].shift(1).rolling(k).max(), d["bas"].shift(1).rolling(k).min()
        return ((c > ha).astype(float) - (c < ba).astype(float)).values
    if regle in ("exces_suit", "exces_contre"):
        r = np.log(c).diff(); z = r / r.rolling(100).std().shift(1)
        s = ((z > k).astype(float) - (z < -k).astype(float)).values
        return s if regle == "exces_suit" else -s
    if regle == "retour":
        m, e = c.shift(1).rolling(20).mean(), c.shift(1).rolling(20).std()
        s = np.where((c - m).abs() > k * e, -np.sign(c - m), 0.0)
        jour = d.index.floor("D")
        hj = d["haut"].groupby(jour).cummax().shift(2); bj = d["bas"].groupby(jour).cummin().shift(2)
        meme = pd.Series(jour, index=d.index).shift(2).values == jour.values
        hp, bp = d["haut"].shift(1), d["bas"].shift(1)
        fb = np.where(meme & (hp > hj) & (c < hj), -1.0, np.where(meme & (bp < bj) & (c > bj), 1.0, 0.0))
        return np.where(s != 0, s, np.nan_to_num(fb))
    raise ValueError(regle)


def joue(d, sig, h, stop_atr=None, retour=False, mult=1.0):
    o, hi, lo, c = (d[x].values for x in ("ouverture", "haut", "bas", "cloture")); sp = d["sp"].values * mult
    atr = atr_jour(d); idx = d.index; jour = idx.floor("D")
    out, i, n = [], 0, len(c)
    while i < n - h - 1:
        s = sig[i]
        if not s or (stop_atr and not atr[i] == atr[i]):
            i += 1; continue
        e = i + 1; ent = o[e] + (sp[e] if s > 0 else 0.0)
        stop = obj = None
        if stop_atr:
            stop = ent - s * stop_atr * atr[i]
        if retour:
            auj = slice(np.searchsorted(jour.values, jour.values[i]), i + 1)
            mil = (hi[auj].max() + lo[auj].min()) / 2
            obj = mil if s * (mil - ent) > sp[i] else None
            ext = hi[i - 1:i + 1].max() + 0.5 if s < 0 else lo[i - 1:i + 1].min() - 0.5
            stop = ext
        x, prix = e + h - 1, None
        for j in range(e, e + h):
            if stop is not None and ((lo[j] <= stop) if s > 0 else (hi[j] + sp[j] >= stop)):
                x, prix = j, stop; break
            if obj is not None and ((hi[j] >= obj) if s > 0 else (lo[j] + sp[j] <= obj)):
                x, prix = j, obj; break
        if prix is None:
            prix = c[x] if s > 0 else c[x] + sp[x]
        out.append((idx[i], s, s * (prix - ent) if s > 0 else (ent - prix)))
        i = x
    T = pd.DataFrame(out, columns=["t", "s", "g"])
    return T


def direction_bt(P, d_m5):
    """Sens du panier bt_or_plus ouvert (dernier ouvert) a chaque instant : serie en escalier sur les heures M5."""
    ev = []
    for r in P.itertuples():
        ev.append((r.t0, r.s, 1)); ev.append((r.t1, r.s, -1))
    ev.sort()
    ouverts, pts = [], []
    for t, s, k in ev:
        if k > 0: ouverts.append(s)
        elif s in ouverts: ouverts.remove(s)
        pts.append((t, ouverts[-1] if ouverts else 0))
    sr = pd.Series([p[1] for p in pts], index=pd.to_datetime([p[0] for p in pts], unit="s"))
    return sr[~sr.index.duplicated(keep="last")].sort_index()


REGLES = {  # nom : (fichier, regle, grille des seuils, grille des tenues, REF (seuil, tenue), contre-tendance)
    "elan_m15": ("xau_m15_50k", "elan", (8, 12, 16), (8, 12, 16), (12, 12)),
    "cassure_m15": ("xau_m15_50k", "cassure", (32, 48, 64), (8, 12, 16), (48, 12)),
    "exces_m5": ("xau_m5_90k", "exces_suit", (2.5, 3, 3.5), (2, 3, 6), (3, 3)),
    "exces_m1": ("xau_m1_90k", "exces_contre", (2.5, 3, 3.5), (6, 12, 20), (3, 12)),
    "retour_court_ar": ("xau_m15_50k", "retour", (2, 2.5, 3), (8, 12), (2.5, 12)),
}


def configs(nom, d, dirbt, mult):
    fic, regle, ks, hs, ref = REGLES[nom]
    stops = (None,) if regle == "retour" else (None, 0.5)
    C = {}
    for k in ks:
        sig = signal(d, regle, k)
        for h in hs:
            for st in stops:
                T = joue(d, sig, h, st, retour=(regle == "retour"), mult=mult)
                hr = T.t.dt.hour; dirr = dirbt.reindex(dirbt.index.union(T.t)).ffill().reindex(T.t).fillna(0).values
                lien = (T.s.values == dirr) if nom in TEND else (T.s.values == -dirr)
                for fh in (False, True):
                    for fl in (False, True):
                        m = np.ones(len(T), bool)
                        if fh: m &= ~hr.isin(COUPE).values
                        if fl: m &= lien
                        C[(k, h, st, fh, fl)] = T.assign(garde=m)
    return C


def wf(C, mois, app, ref_cle, masques=None):
    tot, rf, choix, par_mois = 0.0, 0.0, [], {}
    for k in range(app, len(mois)):
        tr, te = mois[app and k - app:k], mois[k]
        def tt(cle):
            T = C[cle]; m = T.garde.values if masques is None else masques[cle]
            x = T.g.values[m & T.mois.isin(tr).values]
            return x.mean() / x.std() * np.sqrt(len(x)) if len(x) >= 10 and x.std() > 0 else -9
        best = max(C, key=tt); choix.append(best)
        T = C[best]; m = T.garde.values if masques is None else masques[best]
        g = T.g.values[m & (T.mois == te).values].sum(); tot += g; par_mois[te] = g
        R = C[ref_cle]; rf += R.g.values[(R.mois == te).values].sum()
    return tot, rf, choix, par_mois


def prep(C):
    for T in C.values():
        T["mois"] = T.t.dt.to_period("M")
    return C


def partie2(dir_m5, dir_h1, n_plac=500):
    print("\nPARTIE 2 : regles courtes (walk-forward, $ pour 0,01 lot)")
    debut = pd.Timestamp("2025-08-06")
    lignes, series = [], {}
    for nom, (fic, regle, ks, hs, ref) in REGLES.items():
        t0 = time.time()
        d = charge_tf(fic, debut)
        C = prep(configs(nom, d, dir_m5, 1.0)); C2 = prep(configs(nom, d, dir_m5, 2.0))
        ref_cle = (ref[0], ref[1], None, False, False)
        mois = sorted(set(d.index.to_period("M")))[1:-0 or None]
        app = 1 if nom == "exces_m1" else 6
        tot, rf, choix, pm = wf(C, mois, app, ref_cle)
        tot2, rf2, _, _ = wf(C2, mois, app, ref_cle)
        tm = mois[app:]; h1_, h2_ = tm[:len(tm) // 2], tm[len(tm) // 2:]
        R = C[ref_cle]
        ref_m = {m: R.g.values[(R.mois == m).values].sum() for m in tm}
        m1 = sum(pm[m] for m in h1_) - sum(ref_m[m] for m in h1_); m2 = sum(pm[m] for m in h2_) - sum(ref_m[m] for m in h2_)
        # placebo : filtres remplaces par un tri au hasard de meme taux de garde par mois
        taux = {cle: T.groupby("mois").garde.mean() for cle, T in C.items()}
        pl = []
        for _ in range(n_plac):
            mq = {}
            for cle, T in C.items():
                if not (cle[3] or cle[4]):
                    mq[cle] = np.ones(len(T), bool); continue
                p = taux[cle].reindex(T.mois).values
                mq[cle] = rng.random(len(T)) < p
            pl.append(wf(C, mois, app, ref_cle, mq)[0])
        pp = (np.array(pl) >= tot).mean()
        top = pd.Series([str(c) for c in choix]).value_counts()
        cle_top = choix[[str(c) for c in choix].index(top.index[0])]
        # controle H1 (regles M15)
        h1b1 = h1b2 = None
        if fic == "xau_m15_50k":
            dh = charge_tf("xau_h1_50k", pd.Timestamp("2022-08-01"))
            def h1(cle):
                k, h, st, fh, fl = cle
                kk = k if regle == "retour" else max(1, round(k / 4)); hh_ = max(1, round(h / 4))
                T = joue(dh, signal(dh, regle, kk), hh_, st, retour=(regle == "retour"))
                hr = T.t.dt.hour; dr = dir_h1.reindex(dir_h1.index.union(T.t)).ffill().reindex(T.t).fillna(0).values
                m = np.ones(len(T), bool)
                if fh: m &= ~hr.isin(COUPE).values
                if fl: m &= (T.s.values == dr) if nom in TEND else (T.s.values == -dr)
                T = T[m]; return T.g[T.t <= B1F].sum(), T.g[T.t >= B2_0].sum()
            a1, a2 = h1(cle_top); r1, r2 = h1(ref_cle); h1b1, h1b2 = a1 - r1, a2 - r2
        retenu = m1 > 0 and m2 > 0 and pp < 0.05 and tot2 > rf2 and (h1b1 is None or (h1b1 > 0 and h1b2 > 0))
        lignes.append(dict(regle=nom, mois_test=len(tm), ref_total=rf, wf_total=tot, gain_moitie1=m1, gain_moitie2=m2,
                           placebo_p=pp, wf_x2=tot2, ref_x2=rf2, reglage_le_plus_choisi=str(cle_top), part=top.iloc[0] / len(choix),
                           h1_B1=h1b1, h1_B2=h1b2, retenu=retenu))
        series[nom] = (pd.Series(pm), pd.Series(ref_m), C, ref_cle, choix, tm)
        print("  %-16s fait en %.0f s" % (nom, time.time() - t0))
    T = pd.DataFrame(lignes)
    T.to_csv(os.path.join(ICI, "donnees", "lotg_regles.csv"), index=False)
    pd.set_option("display.width", 300)
    print(T.round(2).to_string(index=False))
    # quelques constats bruts sur la regle telle quelle (heures, lien)
    for nom, (_, _, C, ref_cle, _, tm) in series.items():
        R = C[ref_cle]; Rt = R[R.mois.isin(tm)]
        hc = Rt.t.dt.hour.isin(COUPE)
        k, h = ref_cle[0], ref_cle[1]
        lien = C[(k, h, None, False, True)]; lt = lien[lien.mois.isin(tm)]
        print("  %-16s REF test : %d trades %+.0f $ ; aux heures coupees %+.0f $ (%d) ; avec lien bt_or %+.0f $ (%d gardes) / sans lien %+.0f $" % (
            nom, len(Rt), Rt.g.sum(), Rt.g[hc].sum(), hc.sum(), lt.g[lt.garde].sum(), lt.garde.sum(), lt.g[~lt.garde].sum()))
    return T, series


def partie3(R1, series):
    print("\nPARTIE 3 : ensemble en $ (0,01 lot de base), periode de test des regles")
    P = R1[("M5", 1.0)]["REF"]
    bt = (P.g * P.stop).groupby(P.jour).sum()
    deb = min(min(s[5]) for s in series.values()).start_time
    idx = pd.date_range(deb, P.jour.max(), freq="D"); idx = idx[idx.dayofweek < 5]
    def jour(nom, wfmode):
        pm, refm, C, ref_cle, choix, tm = series[nom]
        if not wfmode:
            T = C[ref_cle]; T = T[T.mois.isin(tm)]; return T.groupby(T.t.dt.floor("D")).g.sum()
        parts = []
        for m, cle in zip(tm, choix):
            T = C[cle]; T = T[(T.mois == m) & T.garde]; parts.append(T.groupby(T.t.dt.floor("D")).g.sum())
        return pd.concat(parts) if parts else pd.Series(dtype=float)
    A = bt.reindex(idx, fill_value=0) + sum(jour(n, False).reindex(idx, fill_value=0) for n in series)
    Bx = bt.reindex(idx, fill_value=0) + sum(jour(n, True).reindex(idx, fill_value=0) for n in series)
    Z = bt.reindex(idx, fill_value=0)
    mi = idx[len(idx) // 2]
    for nom, x in (("bt_or_plus seul", Z), ("bt_or_plus + regles telles quelles", A), ("bt_or_plus + regles optimisees (WF)", Bx)):
        xe = x * A.std() / x.std() if x.std() > 0 else x
        eq = xe.cumsum(); w = xe.groupby(xe.index.to_period("W")).sum()
        print("  %-38s total %+7.0f $ (risque egal %+7.0f) ; moities %+6.0f / %+6.0f ; pire baisse %+6.0f ; semaines perdantes %.0f %%" % (
            nom, x.sum(), xe.sum(), xe[xe.index < mi].sum(), xe[xe.index >= mi].sum(), (eq - eq.cummax()).min(), 100 * (w < 0).mean()))


if __name__ == "__main__":
    R1 = partie1()
    d5, kw5 = jeu_m5(); dh, kwh = jeu_h1()
    dir5 = direction_bt(R1[("M5", 1.0)]["REF"], d5); dirh = direction_bt(R1[("H1", 1.0)]["REF"], dh)
    T2, S2 = partie2(dir5, dirh)
    partie3(R1, S2)
