"""Banc Lot M-Astra (PRIORITES 27/11, « Lot M : trois règles d'Astra », étude astra_protocole/Etude_bt_or_plus_2711.pdf).
CONTRAT FIGÉ ET POUSSÉ AVANT TOUT RÉSULTAT (la réserve n'a jamais été calculée pour ces règles).

CADRE. Or M5 du courtier 06/08/2025 -> 11/11/2026 (90 000 bougies, banc_lotg.jeu_m5). Moteur = banc_lotm.simule k=0,
c.-à-d. bt_or_plus v4 réel (sens EMA 576, heures 03:05 08:00 08:30 12:00 15:45 16:00 16:30 serveur, renforts 1-2-3-4-5
tous les 0,25 ATR, recul 0,6667 ATR, paliers 0,5 / 0,35 ATR à +2 / +4 R, point mort dès 4 positions) ; il rend 388,25 R
sur la période principale, comme le banc d'Astra. Principal = paniers fermés 06/08/2025 -> 31/08/2026 ; RÉSERVE =
01/09 -> 11/11/2026, calculée en même temps que le reste et lue une seule fois ; spread réel puis doublé.

VARIANTES (6), règles du PDF d'Astra, p. 2-3 :
  Z15, Z25  « zone » : après un panier fermé en perte (USD < 0) avec UNE seule position, mémoriser par sens son prix
            initial P, son ATR A et l'heure de sortie ; pendant 6 h, à chaque heure d'entrée v4, sauter l'entrée du même
            sens si |prix d'exécution théorique - P| <= w x A (w = 0,15 / 0,25). Un saut ne prolonge pas les 6 h ; une
            nouvelle perte admissible remplace la précédente.
  R2, R3    « rejet » : dès 4 positions (pyramide virtuelle), ancre A0 = prix exécuté du dernier renfort ; ATR du panier.
            Achat : compter les clôtures M5 (bid) < A0 - 0,05 ATR ; vente : clôtures ask (clôture + spread) > A0 +
            0,05 ATR ; compteur remis à zéro si la clôture repasse le seuil ou si un renfort entre. À 2 / 3 clôtures
            consécutives, si le panier (positions réelles) est net positif à cette clôture, la jambe la plus récente
            sort à l'ouverture suivante (bid / ask), une fois par panier ; si la sortie v4 est touchée sur cette bougie
            (écart), la sortie v4 a priorité pour tout. On garde la pyramide v4 VIRTUELLE (jambe retirée comprise) pour
            les seuils, le prix moyen (donc le point mort) et la taille des renforts suivants, comme écrit dans le PDF
            (la fiche PRIORITES dit « point mort recalculé sur le reste » : le PDF, texte complet, fait foi).
  B33, B50  « budget de risque » (règle d'argent, jugée seulement en argent) : avant chaque entrée ou renfort bt_or_plus,
            D = equity - 0,66 x plus haut d'equity (USC, equity = solde + flottant) ; recul = somme, sur les jambes
            ouvertes bt_or_plus ET l'ordre envisagé, de lots x 100 x distance du prix de sortie courant (bid achat, ask
            vente ; prix d'exécution pour l'ordre envisagé) au stop de secours de son panier (le plus protecteur de
            meilleur - 0,8333 ATR et sortie v4 - 0,1667 ATR, comme bt_or.py) ; autorisé si recul <= q x D (q = 1/3,
            1/2). Entrée : base v3 descendue au pas de 0,01 jusqu'au premier volume admissible, sinon panier sauté ;
            base figée à l'ouverture. Renfort inabordable sauté pour toujours (la grille virtuelle continue ; le suivant
            est examiné à son tour). Règles courtes hors calcul du recul (positions courtes, sans stop de secours connu).

ARGENT (pour toutes : V4, V4 base 0,03, les 6 variantes). 20 000 USC ; base v3 = b x solde / 20 000 au pas 0,01 vers
  le bas, au plus b (b = 0,05 ; référence additionnelle b = 0,03), figée à l'ouverture du panier ; jambe = rang x base
  (<= 0,25 lot) ; au plus 10 positions bt_or_plus ; les 5 règles courtes (banc_lotl.courtes, 0,01 x solde / 20 000, au
  moins 0,01) ; USC = USD par lot x 100 x lots. Equity flottante marquée à chaque ordre, sortie et à chaque heure.
  Garde-fou du pont : plus d'ouverture ni de renfort jusqu'au lendemain si equity < 95 % de l'equity du début du jour.
  Arrêt définitif si equity <= 66 % du plus haut d'equity (tout est fermé à ce prix).
  Monte-Carlo : 2 000 parcours de 12 mois par blocs de semaines (longueur moyenne 4 semaines, comme le lot I) ; un panier
  appartient à la semaine de son ouverture et garde ses heures relatives ; MÊMES tirages de blocs pour toutes les
  variantes (apparié). Rapport : P(arrêt), equity finale médiane et 10e centile ; écart à V4 avec intervalle à 90 %
  (bootstrap des parcours, 1 000 tirages). Rejeu historique en argent du 06/08/2025 (principal puis réserve à la suite).

MESURES DE JUGEMENT.
  Z/R : en R, à risque égal (même écart-type journalier que V4 sur le principal, facteur appliqué partout) : gain÷pire
        baisse et Sharpe (principal), total et gain÷pire baisse (réserve), total au spread doublé (principal).
  B   : sur le rejeu historique en USC (sans remise à risque égal, la règle étant une règle de taille) : mêmes mesures
        sur les variations journalières d'equity, spread doublé compris.
PLACEBOS (graine figée 27112026), Holm sur les 6 :
  Z : mêmes conditions sauf la distance : on saute, au hasard, des entrées admissibles (même sens, dans les 6 h après une
      perte à une seule position), avec par (sens, heure d'entrée) la fréquence des sauts réels ; 200 tirages ;
      p = part des placebos au gain÷pire baisse (risque égal, principal) >= réel.
  R : même nombre attendu de jambes retirées, à des clôtures tirées au hasard parmi celles où le panier a >= 4 positions
      virtuelles, est net positif et n'a pas encore été allégé ; 200 tirages ; même statistique.
  B : à chaque ordre d'un parcours Monte-Carlo, réduction ou saut au hasard avec, par rang (et par heure pour les
      entrées), la fréquence et l'ampleur des réductions réelles ; 100 tirages de 400 parcours (mêmes 400 parcours que
      la variante réelle) ; p = part des placebos avec P(arrêt) <= réel.
ADOPTION (toutes les conditions) : P(arrêt) < V4 ET equity médiane >= V4 (Monte-Carlo, b = 0,05) ; gain÷pire baisse
  ET Sharpe > V4 (principal) ; total ET gain÷pire baisse > V4 (réserve) ; total > V4 au spread doublé ; p Holm < 0,05 ;
  jamais plus de 10 positions bt_or_plus.
RAPPORTÉ AUSSI : V4 à 0,03 ; les 5 plus grands paniers gagnants de V4 et ce qu'ils deviennent ; les paniers V4 de >= 4
  positions finis entre -0,25 et +0,25 R ; les ordres refusés (par rang, 5es positions refusées et gain V4 de leur
  panier témoin) ; H1 2022-24 / 2024-26 (gain÷pire baisse, Z et R) en information.
Si une variante est ADOPTÉE : préparer la v5 réelle SANS la publier ; accord écrit de Baptiste avant toute installation.
Usage : python3 banc_lotm_astra.py
"""
import os, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_loth as H, banc_lotj as LJ, banc_lotg as G, banc_lotl as LL

ICI = os.path.dirname(os.path.abspath(__file__))
GRAINE = 27112026
rng = np.random.default_rng(GRAINE)
DEPART, ARRET, GARDE = 20000.0, 0.34, 0.05
SEM0 = 345600                      # lundi 05/01/1970 00:00 UTC
FIN, R0 = LJ.FIN_PRINC, LJ.RES0
SOURCES = {"V4": (None, None), "Z15": ("zone", 0.15), "Z25": ("zone", 0.25), "R2": ("rejet", 2), "R3": ("rejet", 3)}


# ------------------------------------------------------------------------------------------------ moteur
def simule(d, span, heures, debut, mode=None, prm=None, mult=1.0, plac=None, marque=12, plancher=None):
    """bt_or_plus v4 (banc_lotm k=0) + zone / rejet. plac : placebo (dict de probabilités). Rend (paniers, compteurs).
    Chaque panier garde ses jambes et ses marques (heure, prix de sortie courant, stop de secours) pour l'argent."""
    c, o, hi, lo, t = (d[x].values for x in ("cloture", "ouverture", "haut", "bas", "heure"))
    sp = d["sp"].values * mult
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    P, ouvert, mem = [], {}, {}
    cpt = {"elig_z": {}, "saut_z": {}, "elig_r": 0, "retraits": 0, "ajouts": 0}

    def marq(s, i):
        return c[i] if s > 0 else c[i] + sp[i]

    def secours(p, s, niv):
        a = p["meilleur"] - s * 0.8333 * p["A"]; b = niv - s * 0.1667 * p["A"]
        return max(a, b) if s > 0 else min(a, b)

    for i in range(debut, len(c)):
        for s in list(ouvert):
            p = ouvert[s]
            niv = LJ.niveau_sortie({"pal": (2, 4)}, s, p["meilleur"], p["e"], p["w"], p["A"], p["unite"], 0.0, sp[i])
            if len(p["e"]) >= 4:
                moyen = sum(w * e for w, e in zip(p["w"], p["e"])) / sum(p["w"])
                pm = moyen + s * (sp[i] + (plancher[1] * p["A"] if plancher and plancher[0] == "F" else 0.0))
                niv = max(niv, pm) if s > 0 else min(niv, pm)
                if plancher and plancher[0] == "G" and p["gmax"] >= 3 * p["unite"]:
                    vv = [jb for jb in p["jambes"] if jb[3] is None]; Wr = sum(jb[0] for jb in vv)
                    lv = sum(jb[0] * jb[2] for jb in vv) / Wr + s * plancher[1] * p["gmax"] / Wr
                    niv = max(niv, lv) if s > 0 else min(niv, lv)
            touche = (lo[i] <= niv) if s > 0 else (hi[i] + sp[i] >= niv)
            if p["retrait"] is not None and not touche:          # rejet : jambe récente sortie à l'ouverture
                x = o[i] if s > 0 else o[i] + sp[i]
                jb = p["jambes"][p["retrait"]]; jb[3], jb[4] = t[i], x
                p["ev"].append((t[i], "sort", p["retrait"], x)); p["retire"] = True; p["retrait"] = None
                cpt["retraits"] += 1
            p["retrait"] = None
            if touche:
                usd = 0.0
                for jb in p["jambes"]:
                    if jb[3] is None:
                        jb[3], jb[4] = t[i], niv
                    usd += jb[0] * s * (jb[4] - jb[2])
                p["ev"].append((t[i], "fin", None, niv))
                P.append(dict(t0=t[p["i"]], t1=t[i], s=s, g=usd / p["unite"], usd=usd, npos=len(p["e"]), A=p["A"],
                              retire=p["retire"], jambes=p["jambes"], ev=p["ev"], heure=p["heure"], mfe=p["gmax"] / p["unite"]))
                if (mode == "zone" or (plac and "zone" in plac)) and len(p["e"]) == 1 and usd < 0:   # corrigé : le placebo mémorise aussi
                    mem[s] = (p["e"][0], p["A"], t[i])
                del ouvert[s]
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < 5 and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    x = c[i] + (sp[i] if s > 0 else -sp[i]); n = float(len(p["w"]) + 1)
                    p["e"].append(x); p["w"].append(n)
                    p["jambes"].append([n, t[i], x, None, None])
                    p["ev"].append((t[i], "jambe", len(p["jambes"]) - 1, x, secours(p, s, niv), marq(s, i)))
                    p["compte"] = 0
                p["prochain"] += s * p["pas"]
            if mode == "rejet" or (plac and "rejet" in plac):
                if len(p["e"]) >= 4 and not p["retire"]:
                    reel = sum(jb[0] * s * (marq(s, i) - jb[2]) for jb in p["jambes"] if jb[3] is None)
                    if plac is None:
                        A0 = p["jambes"][-1][2]; seuil = A0 - s * 0.05 * p["A"]
                        au_dela = (c[i] < seuil) if s > 0 else (c[i] + sp[i] > seuil)
                        p["compte"] = p["compte"] + 1 if au_dela else 0
                        if reel > 0:
                            cpt["elig_r"] += 1
                        if p["compte"] >= prm and reel > 0 and i + 1 < len(c):
                            p["retrait"] = len(p["jambes"]) - 1
                    elif reel > 0:
                        if rng.random() < plac["rejet"] and i + 1 < len(c):
                            p["retrait"] = len(p["jambes"]) - 1
            p["gmax"] = max(p["gmax"], sum(jb[0] * s * (marq(s, i) - jb[2]) for jb in p["jambes"] if jb[3] is None))
            if (i - p["i"]) % marque == 0:
                p["ev"].append((t[i], "marque", None, marq(s, i), secours(p, s, niv)))
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                x = c[i] + (sp[i] if s > 0 else -sp[i])
                if s in mem and t[i] - mem[s][2] <= 6 * 3600:
                    cel = (s, int(hh[i]), int(mm[i]))
                    cpt["elig_z"][cel] = cpt["elig_z"].get(cel, 0) + 1
                    if mode == "zone" and plac is None:
                        saute = abs(x - mem[s][0]) <= prm * mem[s][1] + 1e-9
                    elif plac and "zone" in plac:
                        saute = rng.random() < plac["zone"].get(cel, 0.0)
                    else:
                        saute = False
                    if saute:
                        cpt["saut_z"][cel] = cpt["saut_z"].get(cel, 0) + 1
                        continue
                A = atr[i]
                p = {"i": i, "e": [x], "w": [1.0], "meilleur": c[i], "A": A, "unite": 0.6667 * A, "pas": 0.25 * A,
                     "prochain": c[i] + s * 0.25 * A, "jambes": [[1.0, t[i], x, None, None]], "compte": 0,
                     "retrait": None, "retire": False, "heure": (int(hh[i]), int(mm[i])), "gmax": 0.0}
                p["ev"] = [(t[i], "jambe", 0, x, c[i] - s * 0.8333 * A, marq(s, i))]
                ouvert[s] = p
    P = pd.DataFrame(P)
    P["d0"] = pd.to_datetime(P.t0, unit="s"); P["d1"] = pd.to_datetime(P.t1, unit="s"); P["jour"] = P.d1.dt.floor("D")
    return P, cpt


# ------------------------------------------------------------------------------------------------ argent
def par_semaine(P, C):
    """Semaines (index relatif) -> liste triée d'évènements (t relatif, ordre, type, données)."""
    W = {}
    for k, r in enumerate(P.itertuples()):
        w = (r.t0 - SEM0) // 604800; base = SEM0 + w * 604800
        for e in r.ev:
            ty = e[1]
            o = {"jambe": 1, "sort": 0, "fin": 0, "marque": 2}[ty]
            W.setdefault(w, []).append((e[0] - base, o, ty, k, e))
    for r in C.itertuples():
        w = (r.t - SEM0) // 604800
        W.setdefault(w, []).append((r.t - SEM0 - w * 604800, 3, "c", r.g, None))
    w0, w1 = min(W), max(W)
    return [sorted(W.get(w, []), key=lambda x: (x[0], x[1])) for w in range(w0, w1 + 1)], w0


def chemin(semaines, blocs, P, b=0.05, q=None, plac=None, arret=True, journal=None, compte=None):
    """Un parcours : blocs = indices de semaines. Mise v3, garde-fou -5 %/jour, arrêt -34 % (equity flottante).
    q : budget de risque (1/3, 1/2). plac : placebo du budget {(rang, heure): (p_saut, p_reduc, [facteurs])}."""
    s_ = P.s.values; jambes = P.jambes.values; heure = P.heure.values
    solde = DEPART; haut = DEPART; ouv = {}; jour = -1; e_jour = DEPART; bloque = False
    fin_t = len(blocs) * 604800
    def equity():
        f = 0.0
        for st in ouv.values():
            f += sum(l * 100.0 * st["s"] * (st["m"] - px) for l, px in st["lots"].values())
        return solde + f
    def recul():
        return sum(sum(l * 100.0 * max(st["s"] * (st["m"] - st["sec"]), 0.0) for l, _ in st["lots"].values()) for st in ouv.values())
    npos = 0
    for kb, wi in enumerate(blocs):
        off = kb * 604800
        for tr, _, ty, k, e in semaines[wi]:
            T = off + tr
            if T >= fin_t:
                continue
            dj = T // 86400
            E = equity()
            if dj != jour:
                jour, e_jour, bloque = dj, E, False
            if ty == "c":
                lot = max(np.floor(0.01 * solde / DEPART / 0.01 + 1e-9) * 0.01, 0.01)
                solde += k * lot / 0.01
            else:
                cle = (kb, k); s = s_[k]
                if ty == "jambe":
                    _, _, j, px, sec, mk = e
                    rang = int(jambes[k][j][0])
                    if j == 0:
                        if cle in ouv:
                            continue
                        base = min(np.floor(b * solde / DEPART / 0.01 + 1e-9) * 0.01, b)
                        st = {"s": s, "m": mk, "sec": sec, "lots": {}, "base": base, "k": k}
                    else:
                        st = ouv.get(cle)
                        if st is None:
                            continue
                        st["m"], st["sec"] = mk, sec
                        base = st["base"]
                    if bloque or E < (1 - GARDE) * e_jour:
                        bloque = True
                        if compte is not None:
                            compte.append((rang, heure[k], "garde", base, 0.0, k))
                        continue
                    if npos >= 10 or base < 0.01:
                        continue
                    lots = round(rang * base, 2)
                    if q is not None:
                        D = E - (1 - ARRET) * haut; R0_ = recul()
                        unit = 100.0 * max(s * (px - sec), 0.0)
                        if j == 0:
                            bb = base
                            while bb >= 0.01 - 1e-9 and R0_ + round(rang * bb, 2) * unit > q * D:
                                bb = round(bb - 0.01, 2)
                            if bb < 0.01 - 1e-9:
                                if compte is not None:
                                    compte.append((rang, heure[k], "saut", base, 0.0, k))
                                continue
                            if compte is not None:
                                compte.append((rang, heure[k], "reduit" if bb < base else "ok", base, bb, k))
                            base = bb; st["base"] = bb; lots = round(rang * bb, 2)
                        elif R0_ + lots * unit > q * D:
                            if compte is not None:
                                compte.append((rang, heure[k], "saut", base, 0.0, k))
                            continue
                        elif compte is not None:
                            compte.append((rang, heure[k], "ok", base, base, k))
                    elif plac is not None:
                        cel = (rang, heure[k] if j == 0 else None)
                        ps, pr, fac = plac.get(cel, (0.0, 0.0, [1.0]))
                        u = rng.random()
                        if u < ps:
                            continue
                        if j == 0 and u < ps + pr:
                            bb = max(np.floor(base * fac[rng.integers(len(fac))] / 0.01 + 1e-9) * 0.01, 0.01)
                            base = bb; st["base"] = bb; lots = round(rang * bb, 2)
                    if j == 0:
                        ouv[cle] = st
                    st["lots"][j] = (lots, px); npos += 1
                else:
                    st = ouv.get(cle)
                    if st is None:
                        continue
                    if ty == "marque":
                        st["m"], st["sec"] = e[3], e[4]
                    elif ty == "sort":
                        j, px = e[2], e[3]
                        if j in st["lots"]:
                            l, pe = st["lots"].pop(j); solde += l * 100.0 * s * (px - pe); npos -= 1
                        st["m"] = px
                    else:
                        px = e[3]
                        for l, pe in st["lots"].values():
                            solde += l * 100.0 * s * (px - pe)
                        npos -= len(st["lots"]); del ouv[cle]
            E = equity(); haut = max(haut, E)
            if journal is not None:
                journal.append((T, E))
            if arret and E <= (1 - ARRET) * haut:
                return dict(final=E, arret=True)
    return dict(final=equity(), arret=False)


def tirages(nsem, n, mois=12, graine=GRAINE + 1):
    g = np.random.default_rng(graine); Hn = int(round(mois * 4.33)); out = []
    for _ in range(n):
        i = g.integers(nsem); L = []
        for _ in range(Hn):
            if g.random() < 0.25:
                i = g.integers(nsem)
            L.append(i % nsem); i += 1
        out.append(L)
    return out


def mc(sem, P, B, **kw):
    return pd.DataFrame([chemin(sem, bl, P, **kw) for bl in B])


def rejeu(sem, P, w0, **kw):
    """Rejeu historique continu (sans arrêt) : série journalière d'equity datée."""
    J = []; chemin(sem, list(range(len(sem))), P, arret=False, journal=J, **kw)
    x = pd.Series([e for _, e in J], index=pd.to_datetime([SEM0 + w0 * 604800 + t for t, _ in J], unit="s"))
    x = x.groupby(x.index.floor("D")).last()
    return x.reindex(pd.date_range(x.index.min(), x.index.max(), freq="D")).ffill()


# ------------------------------------------------------------------------------------------------ parallèle
_J = {}


def _bout(args):
    i0, i1, graine = args
    global rng
    rng = np.random.default_rng(graine)
    sem, P, B, kw = _J["sem"], _J["P"], _J["B"], _J["kw"]
    return [chemin(sem, B[i], P, **kw) for i in range(i0, i1)]


def mc_par(sem, P, B, graine=GRAINE + 7, **kw):
    import multiprocessing as mp
    _J.update(sem=sem, P=P, B=B, kw=kw)
    n = len(B); m = 4; pas = (n + m - 1) // m
    with mp.get_context("fork").Pool(m) as pool:
        R = pool.map(_bout, [(a, min(a + pas, n), graine + a) for a in range(0, n, pas)])
    return pd.DataFrame([x for r in R for x in r])


def ic(a, b, f, n=1000, g=None):
    g = g or np.random.default_rng(GRAINE + 3); m = len(a); out = []
    for _ in range(n):
        ix = g.integers(m, size=m); out.append(f(b[ix]) - f(a[ix]))
    return f(b) - f(a), np.quantile(out, 0.05), np.quantile(out, 0.95)


def mes_eq(x):
    """Mesures sur une série journalière d'equity (USC)."""
    dx = x.diff().dropna(); eq = dx.cumsum(); dd = (eq - eq.cummax()).min()
    return dict(total=dx.sum(), g_creux=dx.sum() / -dd if dd < 0 else np.inf,
                sharpe=dx.mean() / dx.std() * np.sqrt(252) if dx.std() > 0 else 0.0)


# ------------------------------------------------------------------------------------------------ étude
def etude(n_mc=2000, n_plac=200, n_plac_b=100, n_b=400):
    t0 = time.time()
    d, k = G.jeu_m5(); k.pop("bars_h")
    E1 = {v: simule(d, mode=m, prm=x, **k) for v, (m, x) in SOURCES.items()}
    E2 = {v: simule(d, mode=m, prm=x, mult=2.0, **k) for v, (m, x) in SOURCES.items()}
    C1, C2 = LL.courtes([]), LL.courtes([], mult=2.0)
    princ = lambda P: P[P.d1 <= FIN]
    sd = lambda P: princ(P).groupby("jour").g.sum().reindex(pd.date_range("2025-08-06", "2026-08-31"), fill_value=0).std()
    ref = E1["V4"][0]; s_ref = sd(ref)
    lig = {}
    # --- Z / R en R, à risque égal
    for v in ("V4", "Z15", "Z25", "R2", "R3"):
        P, cpt = E1[v]; f = s_ref / sd(P); Q = P.assign(g=P.g * f)
        mp_, mr = H.mesures(princ(Q)), H.mesures(Q[Q.d1 >= R0])
        row = dict(variante=v, total_brut=princ(P).g.sum(), facteur=f, g_creux=mp_["g_creux"], sharpe=mp_["sharpe"],
                   res_total=mr["total"], res_g_creux=mr["g_creux"], total_x2=princ(E2[v][0]).g.sum() * f,
                   paniers=len(princ(P)), sauts_zone=sum(cpt["saut_z"].values()), retraits=cpt["retraits"])
        if v != "V4":
            m_, x_ = SOURCES[v]
            if m_ == "zone":
                pl = {"zone": {c_: cpt["saut_z"].get(c_, 0) / n_ for c_, n_ in cpt["elig_z"].items()}}
            else:
                pl = {"rejet": cpt["retraits"] / max(cpt["elig_r"], 1)}
            st = []
            for _ in range(n_plac):
                Pp, _ = simule(d, plac=pl, **k); fp = s_ref / sd(Pp)
                st.append(H.mesures(princ(Pp.assign(g=Pp.g * fp)))["g_creux"])
            row["placebo_p"] = float((np.array(st) >= mp_["g_creux"]).mean()); row["placebo_med"] = float(np.median(st))
        lig[v] = row
    print("R fait %.0f s" % (time.time() - t0), flush=True)
    # --- argent : Monte-Carlo apparié
    S1 = {v: par_semaine(E1[v][0], C1) for v in E1}
    S2 = {v: par_semaine(E2[v][0], C2) for v in E2}
    nsem = len(S1["V4"][0]); B = tirages(nsem, n_mc)
    CONF = {"V4": ("V4", {}), "V4_003": ("V4", {"b": 0.03}), "Z15": ("Z15", {}), "Z25": ("Z25", {}), "R2": ("R2", {}),
            "R3": ("R3", {}), "B33": ("V4", {"q": 1 / 3}), "B50": ("V4", {"q": 0.5})}
    MC, HIS = {}, {}
    for v, (src, kw) in CONF.items():
        sem, w0 = S1[src]; assert len(sem) == nsem
        MC[v] = mc_par(sem, E1[src][0], B, **kw)
        x1 = rejeu(sem, E1[src][0], w0, **kw); x2 = rejeu(S2[src][0], E2[src][0], S2[src][1], **kw)
        HIS[v] = (x1, x2)
        print(v, "MC fait %.0f s" % (time.time() - t0), flush=True)
    a0 = MC["V4"].arret.values.astype(float); f0 = MC["V4"].final.values
    ARG = []
    for v in CONF:
        a = MC[v].arret.values.astype(float); fv = MC[v].final.values
        da = ic(a0, a, np.mean); dm = ic(f0, fv, np.median)
        x1, x2 = HIS[v]
        hp, hr, h2 = mes_eq(x1[:FIN]), mes_eq(x1[R0 - pd.Timedelta(days=1):]), mes_eq(x2[:FIN])
        ARG.append(dict(variante=v, p_arret=a.mean(), d_arret=da[0], d_arret_ic="[%.3f ; %.3f]" % da[1:],
                        final_med=np.median(fv), d_med=dm[0], d_med_ic="[%.0f ; %.0f]" % dm[1:], final_p10=np.quantile(fv, 0.1),
                        his_total=hp["total"], his_g_creux=hp["g_creux"], his_sharpe=hp["sharpe"], his_res_total=hr["total"],
                        his_res_g_creux=hr["g_creux"], his_x2=h2["total"], his_final=x1.iloc[-1]))
    A = pd.DataFrame(ARG).set_index("variante")
    # --- placebos du budget
    sem, w0 = S1["V4"]; P4 = E1["V4"][0]; Bp = B[:n_b]
    for v, q in (("B33", 1 / 3), ("B50", 0.5)):
        cpt = []; reel = []
        global rng
        for bl in Bp:
            reel.append(chemin(sem, bl, P4, q=q, compte=cpt))
        ar = np.mean([r["arret"] for r in reel])
        D = pd.DataFrame(cpt, columns=["rang", "heure", "type", "base", "bb", "k"])
        D = D[D.type != "garde"]; D["cel"] = [(r, h if r == 1 else None) for r, h in zip(D.rang, D.heure)]
        pl = {}
        for c_, g_ in D.groupby("cel"):
            n_ = len(g_); red = g_[g_.type == "reduit"]
            pl[c_] = ((g_.type == "saut").sum() / n_, len(red) / n_, list((red.bb / red.base).values) or [1.0])
        st = []
        for i in range(n_plac_b):
            Rr = mc_par(sem, P4, Bp, graine=GRAINE + 1000 * (i + 1), plac=pl); st.append(Rr.arret.mean())
        lig[v] = dict(variante=v, placebo_p=float((np.array(st) <= ar).mean()), placebo_med=float(np.median(st)),
                      arret_400=ar, refus=D.type.value_counts().to_dict())
        print(v, "placebo fait %.0f s" % (time.time() - t0), flush=True)
    T = pd.DataFrame([lig[v] for v in ("V4", "Z15", "Z25", "R2", "R3", "B33", "B50")]).set_index("variante")
    six = ["Z15", "Z25", "R2", "R3", "B33", "B50"]
    T.loc[six, "p_holm"] = H.holm(T.loc[six, "placebo_p"].values)
    T = T.join(A, how="outer")
    r0 = T.loc["V4"]; ad = {}
    for v in six:
        r = T.loc[v]
        if v.startswith("B"):
            perf = (r.his_g_creux > r0.his_g_creux and r.his_sharpe > r0.his_sharpe and r.his_res_total > r0.his_res_total
                    and r.his_res_g_creux > r0.his_res_g_creux and r.his_x2 > r0.his_x2)
        else:
            perf = (r.g_creux > r0.g_creux and r.sharpe > r0.sharpe and r.res_total > r0.res_total
                    and r.res_g_creux > r0.res_g_creux and r.total_x2 > r0.total_x2)
        ad[v] = bool(r.p_arret < r0.p_arret and r.final_med >= r0.final_med and perf and r.p_holm < 0.05)
    T["adoptee"] = pd.Series(ad)
    return T, E1, S1, B


def details(E1, S1):
    """Grands gagnants, paniers proches de zéro, ordres refusés (rejeu historique), H1 en information."""
    out = []
    ref = E1["V4"][0]; pr = ref[ref.d1 <= FIN]
    top = pr.nlargest(5, "g")[["t0", "d0", "g", "npos"]]
    zero = pr[(pr.npos >= 4) & (pr.g.abs() <= 0.25)]
    for v in ("Z15", "Z25", "R2", "R3"):
        P = E1[v][0].set_index("t0").g
        out.append(dict(variante=v, top5_v4=top.g.sum(), top5_var=P.reindex(top.t0).fillna(0).sum(),
                        top5_absents=int(P.reindex(top.t0).isna().sum()), zero_n=len(zero), zero_v4=zero.g.sum(),
                        zero_var=P.reindex(zero.t0).fillna(0).sum()))
    sem, w0 = S1["V4"]; Pv = E1["V4"][0]
    ref_s = []
    for v, q in (("B33", 1 / 3), ("B50", 0.5)):
        cpt = []; chemin(sem, list(range(len(sem))), Pv, q=q, arret=False, compte=cpt)
        D = pd.DataFrame(cpt, columns=["rang", "heure", "type", "base", "bb", "k"])
        cinq = D[(D.rang == 5) & (D.type == "saut")]
        topk = set(Pv.index[Pv.t0.isin(top.t0)])
        ref_s.append(dict(variante=v, ordres=len(D), sautes=int((D.type == "saut").sum()), reduits=int((D.type == "reduit").sum()),
                          garde=int((D.type == "garde").sum()), sautes_par_rang=D[D.type == "saut"].rang.value_counts().sort_index().to_dict(),
                          cinquiemes_refusees=len(cinq), gain_v4_de_leurs_paniers=Pv.g.reindex(cinq.k).sum(),
                          top5_jambes_refusees=int(D[(D.type == "saut") & D.k.isin(topk)].shape[0])))
    dh, kh = G.jeu_h1(); kh.pop("bars_h")
    h1 = []
    for v, (m_, x_) in SOURCES.items():
        P, _ = simule(dh, mode=m_, prm=x_, marque=1, **kh)
        h1.append(dict(variante=v, H1_22_24=H.mesures(P[P.jour <= H.B1F])["g_creux"], H1_24_26=H.mesures(P[P.jour >= H.B2_0])["g_creux"]))
    return pd.DataFrame(out), pd.DataFrame(ref_s), pd.DataFrame(h1), top


if __name__ == "__main__":
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 50)
    T, E1, S1, B = etude()
    T.to_csv(os.path.join(ICI, "donnees", "lotm_astra.csv"))
    print(T.round(3).to_string())
    D1, D2, D3, top = details(E1, S1)
    for x in (D1, D2, D3, top):
        print(x.round(3).to_string(index=False))


def placebo_zone(n_plac=200):
    """Placebo de la zone relancé après correction (le 1er passage ne mémorisait pas les pertes en mode placebo)."""
    d, k = G.jeu_m5(); k.pop("bars_h")
    princ = lambda P: P[P.d1 <= FIN]
    sd = lambda P: princ(P).groupby("jour").g.sum().reindex(pd.date_range("2025-08-06", "2026-08-31"), fill_value=0).std()
    s_ref = sd(simule(d, **k)[0]); out = []
    for v in ("Z15", "Z25"):
        P, cpt = simule(d, mode="zone", prm=SOURCES[v][1], **k)
        reel = H.mesures(princ(P.assign(g=P.g * s_ref / sd(P))))["g_creux"]
        pl = {"zone": {c_: cpt["saut_z"].get(c_, 0) / n_ for c_, n_ in cpt["elig_z"].items()}}
        st, ns = [], []
        for _ in range(n_plac):
            Pp, cp = simule(d, plac=pl, **k); st.append(H.mesures(princ(Pp.assign(g=Pp.g * s_ref / sd(Pp))))["g_creux"])
            ns.append(sum(cp["saut_z"].values()))
        out.append(dict(variante=v, reel=reel, sauts_reels=sum(cpt["saut_z"].values()), sauts_placebo_moy=np.mean(ns),
                        placebo_med=np.median(st), placebo_p=float((np.array(st) >= reel).mean())))
    return pd.DataFrame(out)
