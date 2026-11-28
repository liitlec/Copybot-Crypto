"""Banc Lot N (PRIORITES 27/11 13 h, demande écrite de Baptiste) : d'AUTRES stratégies à greffer à bt_or_plus.
CONTRAT FIGÉ ET POUSSÉ AVANT TOUT CALCUL DE CES CANDIDATS.

DONNÉES : or M5 du courtier xau_m5_90k (06/08/2025 -> 11/11/2026, spread réel par bougie). Heure serveur = New York
+ 7 h ; Londres, Shanghai et New York se déduisent par les fuseaux (changements d'heure compris). M15 = M5 regroupées.
PRINCIPAL = trades ENTRÉS du 06/08/2025 au 31/08/2026 ; RÉSERVE = 01/09 -> 11/11/2026 (gelée, lue une fois).
EXÉCUTION commune : entrée à l'OUVERTURE de la bougie qui suit le signal (achat à ouverture + spread, vente à
ouverture) ; stop / objectif vérifiés sur haut / bas (+ spread pour une vente) des bougies suivantes, le stop d'abord
si les deux sont touchés ; sortie au temps à la clôture (achat au bid, vente à l'ask). Gain en $ par once = USC à 0,01
lot cent ; 0,01 lot par trade. Puis spread doublé.

CANDIDATS (10 ; grille fixée ici, aucun autre réglage) :
 Jumeau « début de mouvement » sorti sur ESSOUFFLEMENT (demande 1) : entre en même temps, au même prix et dans le
 même sens que la 1re position de chaque panier bt_or_plus v4 (banc_lotm_astra.simule) ; stop de sécurité 0,6667 ATR
 jour sous l'entrée ; sortie au premier des signaux suivants, ou au plus tard à la sortie du panier bt_or_plus :
  J1 1re clôture M15 de l'autre côté de l'EMA 20 M15 ;
  J2 1re bougie M15 de rejet : mèche contre le sens >= 50 % de sa hauteur ET clôture dans la moitié défavorable ;
  J3 ralentissement : 1re clôture M15 sous le plus bas de la M15 précédente (au-dessus du plus haut en vente) une fois
     le trade en gain d'au moins 0,25 ATR (avant : stop de sécurité seulement) ;
  J4 objectif fixe à +1 ATR jour.
 Recherche large (demande 2 ; sources dans AVIS.md) :
  C1 « momentum de fin de Comex » (Gao-Han-Li-Zhou 2018 ; Baltussen-Da-Lammers-Martens 2021, 60 contrats à terme) :
     signe du rendement de 18 h 00 NY (veille, ouverture Globex) à 13 h 00 NY ; trade dans ce sens de 13 h 00 à 13 h 30
     NY (clôture Comex), lundi-vendredi.
  C2 « ouverture de Shanghai » (momentum de première demi-heure, littérature sur les contrats chinois or/argent) :
     signe du rendement 9 h 00 -> 9 h 30 heure de Pékin ; trade dans ce sens de 9 h 30 à 11 h 30 Pékin.
  C3 « trou du week-end » : écart entre la 1re ouverture de la semaine et la dernière clôture du vendredi >= 0,10 ATR
     jour ; à la 3e bougie, position contre l'écart, objectif = clôture du vendredi, stop = 1 ATR, au plus 12 h.
  C4 « retour en séance asiatique » (marché mince, Boyarchenko et al.) : de 1 h 00 à 6 h 00 Londres, clôture M5 hors
     EMA 20 M5 ± 2 écarts-types (20 bougies) -> position contre l'excès ; sortie au retour sur l'EMA 20, stop 0,5 ATR
     jour, au plus 6 h 30 Londres ; un trade à la fois.
  C5 « cassure de l'ouverture Comex » : fourchette 8 h 20 -> 8 h 50 NY ; 1re clôture M5 hors fourchette avant 11 h 00
     NY -> dans ce sens, stop de l'autre côté de la fourchette, sortie 13 h 30 NY ; un trade par jour.
  C6 « cassure de la séance asiatique à Londres » (version SUIVIE ; la version contrariante a échoué le 16/11) :
     fourchette 0 h 00 -> 7 h 00 Londres ; 1re clôture M5 hors fourchette entre 7 h 00 et 12 h 00 Londres -> dans ce
     sens, stop au milieu de la fourchette, sortie 16 h 30 Londres ; un trade par jour.
 Écartés d'avance (déjà testés sans succès, AVIS « Tout ce qui a été testé ») : nuit contre jour / saisonnalités
 horaires, ratio or/argent, bt_or sur l'argent, suite après annonces CPI/emploi, momentum croisé, COT, autres marchés
 qui annoncent l'or, compression-cassure, Silver Bullet. Pré-FOMC : trop peu de réunions sur 15 mois (non testé).

MESURES (principal, réserve, spread doublé) : trades, total $ (0,01 lot), $ par trade, t de Student, part gagnante ;
  corrélation HEBDOMADAIRE avec bt_or_plus v4 (USD par lot de base) et gain moyen du candidat les semaines où bt_or_plus
  perd ; effet sur le compte réel : candidat ajouté aux règles courtes (0,01 x solde / 20 000, au moins 0,01) dans le
  Monte-Carlo apparié de banc_lotm_astra (2 000 parcours, v4 base 0,05) -> P(arrêt -34 %) et equity médiane.
  Jumeaux : en plus, « miser plus sur bt_or » : à écart-type journalier égal (principal, USC), gain÷pire baisse de
  bt_or_plus (base 0,05) + jumeau contre bt_or_plus seul agrandi.
PLACEBOS (graine 2711_13, 2 000 tirages ; p = part >= réel, total du principal) : C1-C6 : mêmes trades, sens tiré au
  hasard ; J1-J4 : mêmes entrées, durées de détention des trades permutées au hasard (sortie à la clôture M5 après la
  durée tirée, bornée par le stop et la sortie du panier). Correction de Holm sur les 10.
« TIENT » si : total principal > 0 au spread réel ET doublé ; total réserve > 0 ; p Holm < 0,05 ; P(arrêt) pas plus
  de 1 point au-dessus de v4 ; jumeaux : en plus, battre « miser plus sur bt_or ». « PRESQUE » : tout sauf Holm (p brut
  < 0,05). Ce qui tient -> variante démo `_opt` hors totaux (version démo suivante), JAMAIS en réel sans accord écrit.
Usage : python3 banc_lotn.py
"""
import os, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_loth as H, banc_lotg as G, banc_lotl as LL
import banc_lotm_astra as M

ICI = os.path.dirname(os.path.abspath(__file__))
GRAINE = 271113
rng = np.random.default_rng(GRAINE)
FIN, R0 = M.FIN, M.R0


class Jeu:
    def __init__(self, mult=1.0):
        d, k = G.jeu_m5(); k.pop("bars_h"); self.d, self.k = d, k
        self.t = d.heure.values; self.o, self.h, self.l, self.c = (d[x].values for x in ("ouverture", "haut", "bas", "cloture"))
        self.sp = d.sp.values * mult; self.n = len(self.c)
        srv = pd.to_datetime(self.t, unit="s")
        ny = pd.DatetimeIndex(srv - pd.Timedelta(hours=7)).tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
        self.ny, self.lon, self.sha = ny, ny.tz_convert("Europe/London"), ny.tz_convert("Asia/Shanghai")
        jour = self.t // 86400
        j = pd.DataFrame({"jour": jour, "h": self.h, "l": self.l, "c": self.c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
        tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
        self.atr = tr.rolling(20).mean().shift(1).reindex(jour).values
        # M15 (fin de tranche = dernière M5 de la tranche serveur de 15 min)
        g15 = self.t // 900
        self.fin15 = np.r_[g15[1:] != g15[:-1], True]
        D = pd.DataFrame({"g": g15, "o": self.o, "h": self.h, "l": self.l, "c": self.c})
        A = D.groupby("g").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
        A["ema"] = A.c.ewm(span=20, min_periods=20).mean(); A["hp"] = A.h.shift(1); A["lp"] = A.l.shift(1)
        self.m15 = A.reindex(g15).values      # colonnes o h l c ema hp lp, alignées sur chaque M5
        self.ema20 = pd.Series(self.c).ewm(span=20, min_periods=20).mean().values
        self.sd20 = pd.Series(self.c).rolling(20).std().values

    def trade(self, i, s, stop=None, cible=None, jmax=None, sortie=None, px=None, i0=None):
        """Entrée à l'ouverture de i (ou au prix px, surveillance depuis i0). Rend (t entrée, t sortie, s, g, i, j)."""
        o, h, l, c, sp = self.o, self.h, self.l, self.c, self.sp
        if px is None:
            e = o[i] + sp[i] if s > 0 else o[i]; deb = i
        else:
            e = px; deb = i0
        jmax = min(self.n - 1, jmax if jmax is not None else self.n - 1)
        for j in range(deb, jmax + 1):
            if stop is not None and ((l[j] <= stop) if s > 0 else (h[j] + sp[j] >= stop)):
                return (self.t[i], self.t[j], s, s * (stop - e), i, j)
            if cible is not None and ((h[j] >= cible) if s > 0 else (l[j] + sp[j] <= cible)):
                return (self.t[i], self.t[j], s, s * (cible - e), i, j)
            if j == jmax or (sortie is not None and sortie(j)):
                x = c[j] if s > 0 else c[j] + sp[j]
                return (self.t[i], self.t[j], s, s * (x - e), i, j)
        return None


def jumeaux(J, P, regle, plac_durees=None):
    out = []
    srv0 = {t: i for i, t in enumerate(J.t)}
    for q, r in enumerate(P.itertuples()):
        i0 = srv0[r.t0]; s = r.s; A = r.A; jb = r.jambes[0]; e = jb[2]
        i1 = srv0[r.t1]; stop = e - s * 0.6667 * A
        m = J.m15; c = J.c
        if plac_durees is not None:
            jm = min(i1 - 1, i0 + plac_durees[q]); sortie = None; cible = None
        else:
            jm = i1 - 1; cible = e + s * A if regle == "J4" else None
            if regle == "J1":
                sortie = lambda j: J.fin15[j] and m[j, 4] == m[j, 4] and s * (m[j, 3] - m[j, 4]) < 0
            elif regle == "J2":
                def sortie(j):
                    if not J.fin15[j]:
                        return False
                    o_, h_, l_, c_ = m[j, :4]; rg = h_ - l_
                    if rg <= 0:
                        return False
                    meche = (h_ - max(o_, c_)) if s > 0 else (min(o_, c_) - l_)
                    return meche >= 0.5 * rg and (c_ < (h_ + l_) / 2 if s > 0 else c_ > (h_ + l_) / 2)
            elif regle == "J3":
                arme = [False]
                def sortie(j):
                    if s * (c[j] - e) >= 0.25 * A:
                        arme[0] = True
                    return arme[0] and J.fin15[j] and m[j, 6] == m[j, 6] and ((m[j, 3] < m[j, 6]) if s > 0 else (m[j, 3] > m[j, 5]))
            else:
                sortie = None
        if i0 + 1 > jm:
            out.append((J.t[i0], r.t1, s, s * (jb[4] - e), i0, i1)); continue
        x = J.trade(i0, s, stop=stop, cible=cible, jmax=jm, sortie=sortie, px=e, i0=i0 + 1)
        if x is not None and x[5] < jm:
            out.append(x)
        elif x is not None and plac_durees is not None and jm < i1 - 1:
            out.append(x)
        else:                                   # rien avant : sortie avec le panier, à son prix
            out.append((J.t[i0], r.t1, s, s * (jb[4] - e), i0, i1))
    return out


def candidat(J, nom):
    out = []; ny, lon, sha = J.ny, J.lon, J.sha
    hm = lambda z: z.hour * 60 + z.minute
    nyhm = np.array([hm(z) if z is not pd.NaT else -1 for z in ny]); lonhm = np.array([hm(z) if z is not pd.NaT else -1 for z in lon])
    shahm = np.array([hm(z) if z is not pd.NaT else -1 for z in sha])
    nyd = np.array([z.date() if z is not pd.NaT else None for z in ny]); lond = np.array([z.date() if z is not pd.NaT else None for z in lon])
    shad = np.array([z.date() if z is not pd.NaT else None for z in sha])
    if nom == "C1":
        glob = {}                                       # ouverture Globex 18 h NY -> séance du lendemain
        for i in range(J.n):
            if nyhm[i] >= 18 * 60 and (i == 0 or nyhm[i - 1] < 18 * 60 or nyd[i - 1] != nyd[i]):
                glob[nyd[i]] = J.o[i]
        prev = None
        for i in range(1, J.n - 6):
            if nyhm[i] == 12 * 60 + 55 and ny[i].weekday() < 5 and nyhm[i + 1] == 13 * 60:
                cles = [k_ for k_ in glob if k_ < nyd[i]]
                if not cles:
                    continue
                r_ = J.c[i] - glob[max(cles)]
                if r_ == 0:
                    continue
                jm = i + 6
                if nyhm[jm] != 13 * 60 + 25:
                    continue
                out.append(J.trade(i + 1, np.sign(r_), jmax=jm))
    elif nom == "C2":
        for i in range(J.n - 30):
            if shahm[i] == 9 * 60 and sha[i].weekday() < 5:
                k5 = i + 5
                if shahm[k5] != 9 * 60 + 25:
                    continue
                r_ = J.c[k5] - J.o[i]
                fin = [j for j in range(k5 + 1, min(J.n, k5 + 40)) if shahm[j] == 11 * 60 + 25]
                if r_ == 0 or not fin:
                    continue
                out.append(J.trade(k5 + 1, np.sign(r_), jmax=fin[0]))
    elif nom == "C3":
        for i in range(1, J.n - 150):
            if J.t[i] - J.t[i - 1] > 24 * 3600 and J.atr[i] == J.atr[i]:
                gap = J.o[i] - J.c[i - 1]
                if abs(gap) >= 0.10 * J.atr[i]:
                    s = -np.sign(gap); e_i = i + 2
                    ent = J.o[e_i] + (J.sp[e_i] if s > 0 else 0)
                    out.append(J.trade(e_i, s, stop=ent - s * J.atr[i], cible=J.c[i - 1], jmax=e_i + 143))
    elif nom == "C4":
        i = 0
        while i < J.n - 2:
            if 60 <= lonhm[i] < 360 and J.sd20[i] == J.sd20[i] and J.atr[i] == J.atr[i]:
                ex = J.c[i] - J.ema20[i]
                if abs(ex) > 2 * J.sd20[i]:
                    s = -np.sign(ex); e_i = i + 1
                    fin = [j for j in range(e_i, min(J.n, e_i + 80)) if lonhm[j] == 6 * 60 + 25]
                    if not fin:
                        i += 1; continue
                    ent = J.o[e_i] + (J.sp[e_i] if s > 0 else 0)
                    x = J.trade(e_i, s, stop=ent - s * 0.5 * J.atr[i], jmax=fin[0],
                                sortie=lambda j, s=s: s * (J.c[j] - J.ema20[j]) >= 0)
                    out.append(x); i = x[5] + 1; continue
            i += 1
    elif nom in ("C5", "C6"):
        if nom == "C5":
            hmv, dv, r0, r1, f0, f1, fin_ = nyhm, nyd, 8 * 60 + 20, 8 * 60 + 50, 8 * 60 + 50, 11 * 60, 13 * 60 + 25
        else:
            hmv, dv, r0, r1, f0, f1, fin_ = lonhm, lond, 0, 7 * 60, 7 * 60, 12 * 60, 16 * 60 + 25
        jours = pd.Series(np.arange(J.n)).groupby(pd.Series(dv)).apply(list)
        for dd_, idx in jours.items():
            if dd_ is None or pd.Timestamp(dd_).weekday() >= 5:
                continue
            idx = np.array(idx); hh_ = hmv[idx]
            rg = idx[(hh_ >= r0) & (hh_ < r1)]; fe = idx[(hh_ >= f0) & (hh_ < f1)]; ff = idx[hh_ == fin_]
            if len(rg) < (5 if nom == "C5" else 60) or not len(fe) or not len(ff):
                continue
            hi_, lo_ = J.h[rg].max(), J.l[rg].min()
            for i in fe:
                s = 1 if J.c[i] > hi_ else (-1 if J.c[i] < lo_ else 0)
                if s and i + 1 < ff[0]:
                    stop = (lo_ if s > 0 else hi_) if nom == "C5" else (hi_ + lo_) / 2
                    out.append(J.trade(i + 1, s, stop=stop, jmax=ff[0])); break
    return [x for x in out if x is not None]


def table(L):
    T = pd.DataFrame(L, columns=["t0", "t1", "s", "g", "i", "j"])
    T["d0"] = pd.to_datetime(T.t0, unit="s"); T["d1"] = pd.to_datetime(T.t1, unit="s")
    return T


def stats(x):
    n = len(x)
    return dict(n=n, total=x.sum(), moy=x.mean() if n else 0, t=x.mean() / x.std() * np.sqrt(n) if n > 1 and x.std() > 0 else 0,
                gagnants=(x > 0).mean() if n else 0)


NOMS = ["J1", "J2", "J3", "J4", "C1", "C2", "C3", "C4", "C5", "C6"]


def produit(J, P, nom, **kw):
    return table(jumeaux(J, P, nom, **kw) if nom.startswith("J") else candidat(J, nom))


def hebdo(t, v):
    w = (np.asarray(t) - M.SEM0) // 604800
    return pd.Series(np.asarray(v, float)).groupby(w).sum()


def mes_j(x):
    eq = x.cumsum(); dd = (eq - eq.cummax()).min()
    return x.sum() / -dd if dd < 0 else np.inf


def etude(n_plac=2000, n_mc=2000):
    t0 = time.time()
    J1_, J2_ = Jeu(), Jeu(mult=2.0)
    P1, _ = M.simule(J1_.d, **J1_.k); P2, _ = M.simule(J2_.d, mult=2.0, **J2_.k)
    C1 = LL.courtes([])
    sem0, w0 = M.par_semaine(P1, C1); B = M.tirages(len(sem0), n_mc)
    base = M.mc_par(sem0, P1, B); a0, f0 = base.arret.values.astype(float), base.final.values
    btw = hebdo(P1[P1.d1 <= FIN].t1, P1[P1.d1 <= FIN].usd)
    jr = pd.date_range("2025-08-06", "2026-08-31")
    bt_j = (P1[P1.d1 <= FIN].usd * 0.05 * 100).groupby(P1[P1.d1 <= FIN].d1.dt.floor("D")).sum().reindex(jr, fill_value=0)
    L = []
    for nom in NOMS:
        T = produit(J1_, P1, nom); T2 = produit(J2_, P2, nom)
        pr, rs, pr2 = T[T.d0 <= FIN], T[T.d0 >= R0], T2[T2.d0 <= FIN]
        sp_, sr_, s2_ = stats(pr.g.values), stats(rs.g.values), stats(pr2.g.values)
        row = dict(candidat=nom, trades=sp_["n"], total=sp_["total"], par_trade=sp_["moy"], t=sp_["t"], gagnants=sp_["gagnants"],
                   total_x2=s2_["total"], res_trades=sr_["n"], res_total=sr_["total"], res_t=sr_["t"])
        # placebo
        if nom.startswith("J"):
            dur = (T.j - T.i).values; obs = pr.g.sum(); st = []
            for _ in range(n_plac):
                Tp = table(jumeaux(J1_, P1, nom, plac_durees=rng.permutation(dur))); st.append(Tp[Tp.d0 <= FIN].g.sum())
        else:
            g = pr.g.values; obs = g.sum()
            st = [(g * rng.choice((-1, 1), len(g))).sum() for _ in range(n_plac)]
        row["placebo_p"] = float((np.array(st) >= obs).mean())
        # corrélation hebdomadaire et semaines où bt_or_plus perd
        cw = hebdo(pr.t1, pr.g).reindex(btw.index, fill_value=0)
        row["corr_hebdo"] = np.corrcoef(cw.values, btw.values)[0, 1]
        row["moy_sem_bt_perd"] = cw[btw < 0].mean(); row["moy_sem_bt_gagne"] = cw[btw > 0].mean()
        # compte réel : Monte-Carlo apparié
        Cx = pd.concat([C1[["t", "g"]], pd.DataFrame({"t": T.t1.values, "g": T.g.values})], ignore_index=True)
        sem, _ = M.par_semaine(P1, Cx)
        if len(sem) != len(sem0):
            row["p_arret"] = np.nan
        else:
            R = M.mc_par(sem, P1, B); a = R.arret.values.astype(float)
            row["p_arret"] = a.mean(); row["d_arret"] = "%+.3f [%.3f ; %.3f]" % M.ic(a0, a, np.mean)
            row["d_med"] = "%+.0f [%.0f ; %.0f]" % M.ic(f0, R.final.values, np.median)
        if nom.startswith("J"):
            jj = pr.g.groupby(pr.d1.dt.floor("D")).sum().reindex(jr, fill_value=0)
            row["gc_combo"] = mes_j(bt_j + jj); row["gc_bt_seul"] = mes_j(bt_j)
        L.append(row); print(nom, "%.0f s" % (time.time() - t0), flush=True)
    T = pd.DataFrame(L).set_index("candidat")
    T["p_holm"] = H.holm(T.placebo_p.values); T.loc["V4", "p_arret"] = a0.mean()
    ok = lambda r: (r.total > 0 and r.total_x2 > 0 and r.res_total > 0 and r.p_arret <= a0.mean() + 0.01
                    and (not str(r.name).startswith("J") or r.gc_combo > r.gc_bt_seul))
    T["verdict"] = ["" if v == "V4" else ("tient" if ok(r) and r.p_holm < 0.05 else ("presque" if ok(r) and r.placebo_p < 0.05 else "non"))
                    for v, r in T.iterrows()]
    return T


if __name__ == "__main__":
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
    T = etude(); T.to_csv(os.path.join(ICI, "donnees", "lotn.csv"))
    print(T.round(3).to_string())
