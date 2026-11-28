"""Banc Lot O (PRIORITES 28/11, Baptiste : « à partir de tant de % par jour, on coupe les paniers pour encaisser et on
rouvre directement »). CONTRAT FIGÉ ET POUSSÉ AVANT TOUT CALCUL.

CADRE : celui de banc_lotm_astra.py. Or M5 du courtier 06/08/2025 -> 11/11/2026 ; bt_or_plus v4 (moteur
banc_lotm_astra.simule) ; argent : 20 000 USC, base v3 0,05 x solde / 20 000, règles courtes (0,01 x solde / 20 000),
garde-fou −5 %/jour, arrêt −34 %, BUDGET DE RISQUE q = 1/2 (la v5) ; principal = jusqu'au 31/08/2026, réserve
01/09 -> 11/11/2026 ; spread réel puis doublé. Swap : non modélisé (aucune donnée de swap ; couper et rouvrir ne change
presque pas la durée tenue, donc l'effet est voisin pour toutes les variantes) — dit comme une limite.
RÉFÉRENCE = v4 + budget 1/2 (la v5), sans coupure.

DÉCLENCHEUR, évalué à chaque clôture M5 dans le moteur (qui suit son propre solde : base v3, règles courtes ajoutées
à leur sortie, journée = jour de Paris, référence = solde au début de la journée S0) :
  « compte » (C) : (solde + latent des paniers bt_or_plus) - S0 >= X % de S0 -> on ferme TOUS les paniers bt_or_plus
                   ouverts au prix de la bougie (bid achat, ask vente), on encaisse, et on rouvre aussitôt un panier
                   neuf dans le même sens à la même bougie (prix + spread), base v3 du nouveau solde, ATR du jour,
                   pyramide repartie de zéro (renforts, recul, paliers, point mort : règles v4 depuis ce nouveau départ) ;
  « panier » (P) : latent d'UN panier >= X % de S0 -> on ferme ce panier seulement et on le rouvre de même.
  X = 1 / 2 / 3 / 5 %. Mode « une fois » (U) : au plus une coupure par jour (par déclencheur) ; mode « palier » (K) :
  une coupure chaque fois que le seuil suivant (k x X %, k = 1, 2, 3…) est atteint dans la journée.
  16 VARIANTES : {C, P} x {1, 2, 3, 5 %} x {U, K}. Règles courtes inchangées, jamais coupées.
MESURES : rejeu historique en USC (budget 1/2 appliqué par la couche d'argent de banc_lotm_astra, comme la v5) :
  total, gain÷pire baisse et Sharpe journaliers (principal), total et gain÷pire baisse (réserve), total au spread
  doublé ; nombre de coupures ; gain moyen d'une coupure (encaissé) ; Monte-Carlo apparié (2 000 parcours de 12 mois,
  blocs de semaines, mêmes tirages que la référence) : P(arrêt −34 %), equity médiane, écarts avec IC 90 %.
PLACEBO (graine 2811, 200 tirages par variante) : autant de coupures-réouvertures (en espérance) à des clôtures M5
  tirées au hasard parmi celles où un panier est ouvert, même type (C : tous les paniers ; P : un panier) ;
  statistique = gain÷pire baisse du principal en USC ; p = part des placebos >= réel. Holm sur les 16.
ADOPTION : gain÷pire baisse ET Sharpe > RÉFÉRENCE (principal) ; total ET gain÷pire baisse > RÉFÉRENCE (réserve) ;
  total > RÉFÉRENCE au spread doublé ; P(arrêt) <= RÉFÉRENCE + 1 point ET médiane >= RÉFÉRENCE ; p Holm < 0,05.
SEMAINE DU 23-27/11 (descriptif) : le panier réel 25-27/11 (journal du robot réel, prix relevés dans les états du pont
  publiés sur la branche) : pour chaque X, heure et prix de la coupure et résultat, contre le réel (+4,72 USC).
Rien en réel sans accord écrit de Baptiste ; si une variante est adoptée : démo `_opt` d'abord.
Usage : python3 banc_loto.py
"""
import os, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_loth as H, banc_lotg as G, banc_lotl as LL, banc_lotj as LJ
import banc_lotm_astra as M

ICI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(2811)
FIN, R0 = M.FIN, M.R0
VARS = {"REF": None}
for typ in ("C", "P"):
    for x in (1, 2, 3, 5):
        for mode in ("U", "K"):
            VARS["%s%d%s" % (typ, x, mode)] = (typ, x / 100.0, mode)


def simule(d, span, heures, debut, C, trig=None, mult=1.0, plac=None, marque=12):
    """bt_or_plus v4 + coupure-réouverture. C : règles courtes (t, g à 0,01 lot). Rend (paniers, compteurs)."""
    c, hi, lo, t = (d[x].values for x in ("cloture", "haut", "bas", "heure"))
    sp = d["sp"].values * mult
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    ct, cg = C.t.values, C.g.values; oc = np.argsort(ct); ct, cg = ct[oc], cg[oc]; kc = 0
    P, ouvert = [], {}
    sol = M.DEPART; jp = -1; S0 = sol; nC = 0; nP = {}
    cpt = {"coupures": 0, "encaisse": 0.0, "barres_ouvertes": 0}

    def marq(s, i):
        return c[i] if s > 0 else c[i] + sp[i]

    def secours(p, s, niv):
        a = p["meilleur"] - s * 0.8333 * p["A"]; b = niv - s * 0.1667 * p["A"]
        return max(a, b) if s > 0 else min(a, b)

    def base_v3():
        return min(np.floor(0.05 * sol / M.DEPART / 0.01 + 1e-9) * 0.01, 0.05)

    def flottant(p, s, i):
        return sum(jb[0] * p["base"] * 100.0 * s * (marq(s, i) - jb[2]) for jb in p["jambes"] if jb[3] is None)

    def ouvre(s, i, coupe=False):
        A = atr[i]; x = c[i] + (sp[i] if s > 0 else -sp[i]); b = base_v3()
        if b < 0.01:
            return
        p = {"i": i, "e": [x], "w": [1.0], "meilleur": c[i], "A": A, "unite": 0.6667 * A, "pas": 0.25 * A,
             "prochain": c[i] + s * 0.25 * A, "jambes": [[1.0, t[i], x, None, None]], "heure": (int(hh[i]), int(mm[i])),
             "base": b, "rouvert": coupe}
        p["ev"] = [(t[i], "jambe", 0, x, c[i] - s * 0.8333 * A, marq(s, i))]
        ouvert[s] = p

    def ferme(s, i, px, raison):
        nonlocal sol
        p = ouvert.pop(s); usd = 0.0
        for jb in p["jambes"]:
            if jb[3] is None:
                jb[3], jb[4] = t[i], px
            usd += jb[0] * s * (jb[4] - jb[2])
        sol += usd * p["base"] * 100.0
        p["ev"].append((t[i], "fin", None, px))
        P.append(dict(t0=t[p["i"]], t1=t[i], s=s, g=usd / p["unite"], usd=usd, npos=len(p["e"]), A=p["A"], retire=False,
                      jambes=p["jambes"], ev=p["ev"], heure=p["heure"], mfe=0.0, raison=raison, rouvert=p["rouvert"]))
        return usd * p["base"] * 100.0

    for i in range(debut, len(c)):
        while kc < len(ct) and ct[kc] <= t[i]:                   # règles courtes sorties
            lot = max(np.floor(0.01 * sol / M.DEPART / 0.01 + 1e-9) * 0.01, 0.01); sol += cg[kc] * lot / 0.01; kc += 1
        dpj = (t[i] - 3600) // 86400
        if dpj != jp:
            jp, S0, nC, nP = dpj, sol, 0, {}
        for s in list(ouvert):
            p = ouvert[s]
            niv = LJ.niveau_sortie({"pal": (2, 4)}, s, p["meilleur"], p["e"], p["w"], p["A"], p["unite"], 0.0, sp[i])
            if len(p["e"]) >= 4:
                moyen = sum(w * e for w, e in zip(p["w"], p["e"])) / sum(p["w"])
                pm = moyen + s * sp[i]
                niv = max(niv, pm) if s > 0 else min(niv, pm)
            if (lo[i] <= niv) if s > 0 else (hi[i] + sp[i] >= niv):
                ferme(s, i, niv, "v4"); continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < 5 and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    x = c[i] + (sp[i] if s > 0 else -sp[i]); n = float(len(p["w"]) + 1)
                    p["e"].append(x); p["w"].append(n); p["jambes"].append([n, t[i], x, None, None])
                    p["ev"].append((t[i], "jambe", len(p["jambes"]) - 1, x, secours(p, s, niv), marq(s, i)))
                p["prochain"] += s * p["pas"]
            if (i - p["i"]) % marque == 0:
                p["ev"].append((t[i], "marque", None, marq(s, i), secours(p, s, niv)))
        # coupure (réelle ou placebo)
        if ouvert:
            cpt["barres_ouvertes"] += 1
        if ouvert and (trig is not None or plac is not None):
            a_couper = []
            if plac is not None:
                if rng.random() < plac["p"]:
                    a_couper = list(ouvert) if plac["typ"] == "C" else [list(ouvert)[rng.integers(len(ouvert))]]
            else:
                typ, X, mode = trig
                if typ == "C":
                    E = sol + sum(flottant(ouvert[s], s, i) for s in ouvert)
                    if (mode == "K" or nC == 0) and E - S0 >= X * S0 * (nC + 1 if mode == "K" else 1):
                        a_couper = list(ouvert); nC += 1
                else:
                    for s in list(ouvert):
                        k_ = nP.get(s, 0)
                        if (mode == "K" or k_ == 0) and flottant(ouvert[s], s, i) >= X * S0 * (k_ + 1 if mode == "K" else 1):
                            a_couper.append(s); nP[s] = k_ + 1
            for s in a_couper:
                cpt["encaisse"] += ferme(s, i, marq(s, i), "coupure"); cpt["coupures"] += 1
                ouvre(s, i, coupe=True)
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvre(s, i)
    P = pd.DataFrame(P)
    P["d0"] = pd.to_datetime(P.t0, unit="s"); P["d1"] = pd.to_datetime(P.t1, unit="s"); P["jour"] = P.d1.dt.floor("D")
    return P, cpt


def mes_hist(x):
    return M.mes_eq(x[:FIN]), M.mes_eq(x[R0 - pd.Timedelta(days=1):])


def etude(n_mc=2000, n_plac=200):
    t0 = time.time()
    d, k = G.jeu_m5(); k.pop("bars_h")
    C1, C2 = LL.courtes([]), LL.courtes([], mult=2.0)
    ref_sem = None; L = []; MC = {}
    for v, trig in VARS.items():
        P1, cpt = simule(d, C=C1, trig=trig, **k); P2, _ = simule(d, C=C2, trig=trig, mult=2.0, **k)
        sem, w0 = M.par_semaine(P1, C1); sem2, w02 = M.par_semaine(P2, C2)
        if ref_sem is None:
            ref_sem = (len(sem), w0); B = M.tirages(len(sem), n_mc)
        sem = [sem[w - w0] if 0 <= w - w0 < len(sem) else [] for w in range(ref_sem[1], ref_sem[1] + ref_sem[0])]
        MC[v] = M.mc_par(sem, P1, B, q=0.5)
        x1 = M.rejeu(sem, P1, ref_sem[1], q=0.5); x2 = M.rejeu(sem2, P2, w02, q=0.5)
        hp, hr = mes_hist(x1); h2 = M.mes_eq(x2[:FIN])
        row = dict(variante=v, coupures=cpt["coupures"], encaisse_moy=cpt["encaisse"] / max(cpt["coupures"], 1),
                   paniers=len(P1), total=hp["total"], g_creux=hp["g_creux"], sharpe=hp["sharpe"], res_total=hr["total"],
                   res_g_creux=hr["g_creux"], total_x2=h2["total"])
        if trig is not None:
            pl = {"typ": trig[0], "p": cpt["coupures"] / max(cpt["barres_ouvertes"], 1)}
            st = []
            for _ in range(n_plac):
                Pp, _ = simule(d, C=C1, plac=pl, **k); sp_, wp = M.par_semaine(Pp, C1)
                st.append(M.mes_eq(M.rejeu(sp_, Pp, wp, q=0.5)[:FIN])["g_creux"])
            row["placebo_p"] = float((np.array(st) >= hp["g_creux"]).mean()); row["placebo_med"] = float(np.median(st))
        L.append(row); print(v, "%.0f s" % (time.time() - t0), flush=True)
    T = pd.DataFrame(L).set_index("variante")
    a0, f0 = MC["REF"].arret.values.astype(float), MC["REF"].final.values
    for v in VARS:
        a, fv = MC[v].arret.values.astype(float), MC[v].final.values
        T.loc[v, "p_arret"] = a.mean(); T.loc[v, "d_arret"] = "%+.3f [%.3f ; %.3f]" % M.ic(a0, a, np.mean)
        T.loc[v, "final_med"] = np.median(fv); T.loc[v, "d_med"] = "%+.0f [%.0f ; %.0f]" % M.ic(f0, fv, np.median)
    idx = [v for v in VARS if v != "REF"]
    T.loc[idx, "p_holm"] = H.holm(T.loc[idx, "placebo_p"].values)
    r0 = T.loc["REF"]
    T["adoptee"] = [bool(v != "REF" and r.g_creux > r0.g_creux and r.sharpe > r0.sharpe and r.res_total > r0.res_total
                         and r.res_g_creux > r0.res_g_creux and r.total_x2 > r0.total_x2 and r.p_arret <= r0.p_arret + 0.01
                         and r.final_med >= r0.final_med and r.p_holm < 0.05) for v, r in T.iterrows()]
    return T


def semaine_reelle():
    """Panier réel 25-27/11 : prix relevés dans les états du pont publiés (historique git), coupure à X % du solde."""
    import subprocess, json
    out = subprocess.run(["git", "log", "--since=2026-11-24", "--until=2026-11-27 14:40", "--format=%H",
                          "--", "copy_sim/labo/mt5_reel/etat.json"], capture_output=True, text=True,
                         cwd=os.path.join(ICI, "..", "..")).stdout.split()
    pts = []
    for h in out:
        try:
            e = json.loads(subprocess.run(["git", "show", h + ":copy_sim/labo/mt5_reel/etat.json"], capture_output=True,
                                          text=True, cwd=os.path.join(ICI, "..", "..")).stdout)
            sy = list(e["symboles"].values())[0]
            pts.append((e["ecrit"], sy["bid"], e.get("solde")))
        except Exception:
            pass
    pts.sort()
    jambes = [(0.02, 3563.54, "2026-11-25"), (0.04, 3598.58, "2026-11-26"), (0.06, 3648.08, "2026-11-27T03"),
              (0.08, 3677.30, "2026-11-27T08")]
    return pts, jambes


if __name__ == "__main__":
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
    T = etude(); T.to_csv(os.path.join(ICI, "donnees", "loto.csv"))
    print(T.round(3).to_string())
