"""Banc AK : regle de retrait avec interets composes (PRIORITES 18/11, 14 h 15 ; voir PLAN_REEL.md).
Memes donnees et meme plan que banc_plan_cent.py : melange bt_or + rebonds d'indices (parite de risque), levier L du
plan -30 % (90 % des trajectoires PRUDENTES a pire baisse < 30 % sur 12 mois), mise recalculee chaque semaine.
Monte-Carlo : bootstrap stationnaire (blocs 20 j) des rendements joints, 24 mois, 5000 tirages ; scenarios mesure,
prudent (avantage / 2) et nul. Retraits faits en fin de mois (toutes les 52/12 semaines), compte en unites de mise
de depart (1 = 100 EUR ou 500 EUR : tout est proportionnel, hors arrondi des lots).
Regles : (a) aucun retrait ; (b) retirer la mise de depart (1) des que le compte >= 2, puis rien ;
(c25, c50) (b), puis chaque mois retirer 25 % / 50 % du gain au-dessus du plus haut de fin de mois deja atteint ;
(d1, d1.5, d2) chaque mois retirer tout ce qui depasse un plafond de 1 / 1,5 / 2 fois la mise.
Mesures a 12 et 24 mois : retire (mediane), chance d'avoir recupere la mise (retire >= 1), compte (mediane),
total = retire + compte (mediane, moyenne), chance que le total soit sous la mise de depart, sous la moitie.
Usage : python3 banc_retrait.py"""
import contextlib, io, os
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_plan_cent as PC
ICI = os.path.dirname(os.path.abspath(__file__))
NPAR, MOIS, SEMJ, BLOC = 5000, 24, 5, 20.0
NSEM = 104
rng = np.random.default_rng(20261118)


def tirages(n, T):
    neuf = rng.random((NPAR, T)) < 1 / BLOC; neuf[:, 0] = True
    deb = np.maximum.accumulate(np.where(neuf, np.arange(T), 0), axis=1)
    start = np.take_along_axis(rng.integers(n, size=(NPAR, T)), deb, axis=1)
    return (start + np.arange(T) - deb) % n


def simule(G, regle):
    """G : facteurs hebdomadaires (tirages x semaines). Rend retire et compte a 12 et 24 mois."""
    n = G.shape[0]
    A = np.ones(n); R = np.zeros(n); fait = np.zeros(n, bool); H = np.ones(n)
    fins = {int(round(k * 52 / 12)) - 1: k for k in range(1, MOIS + 1)}
    out = {}
    for s in range(NSEM):
        A = A * G[:, s]
        if s in fins:
            if regle in ("b", "c25", "c50"):
                x = (~fait) & (A >= 2)
                apres = fait.copy()                       # la part (c) ne commence que le mois suivant le retrait de la mise
                R = R + x; A = A - x; fait = fait | x
                H = np.where(x, A, H)
                if regle != "b":
                    f = 0.25 if regle == "c25" else 0.50
                    w = np.where(apres, f * np.maximum(A - H, 0), 0.0)
                    R = R + w; A = A - w
                    H = np.where(apres, np.maximum(H, A), H)
            elif regle.startswith("d"):
                cap = float(regle[1:])
                w = np.maximum(A - cap, 0); R = R + w; A = A - w
            if fins[s] in (12, 24):
                out[fins[s]] = (R.copy(), A.copy())
    return out


if __name__ == "__main__":
    X, _ = PC.series()
    cols = list(X.columns); w = PC.parite(X[cols])
    P12 = (PC.ampute(X[cols], 0.5).values @ w)[PC.tirages(len(X))]
    L = PC.calibre(P12, 0.30)
    print("Melange %s, poids %s ; levier du plan -30 %% : L = %.2f (controle banc_plan_cent : 7,5)" % (
        cols, np.round(w, 3), L))
    I = tirages(len(X), NSEM * SEMJ)
    REG = ["a", "b", "c25", "c50", "d1", "d1.5", "d2"]
    rows = []
    for sc, part in (("mesure", 0.0), ("prudent", 0.5), ("nul", 1.0)):
        p = (PC.ampute(X[cols], part).values @ w)[I]
        G = np.maximum(1 + L * p.reshape(NPAR, NSEM, SEMJ).sum(2), 0.0)
        print("\n=== scenario %s (en fois la mise de depart ; x100 ou x500 pour des euros)" % sc)
        print("  %-5s %4s | %7s %7s | %7s | %7s %7s | %7s %7s" % (
            "regle", "mois", "ret.med", "P(ret>=1)", "cpt.med", "tot.med", "tot.moy", "P(tot<1)", "P(tot<0,5)"))
        for r in REG:
            for m, (Rm, Am) in simule(G, r).items():
                T = Rm + Am
                d = dict(scenario=sc, regle=r, mois=m, retire_med=np.median(Rm), p_mise_recup=(Rm >= 1 - 1e-9).mean(),
                         compte_med=np.median(Am), total_med=np.median(T), total_moy=T.mean(),
                         p_total_sous_mise=(T < 1).mean(), p_total_sous_moitie=(T < 0.5).mean(),
                         total_q10=np.quantile(T, 0.10))
                rows.append(d)
                print("  %-5s %4d | %7.2f %7.0f %% | %7.2f | %7.2f %7.2f | %6.0f %% %6.0f %%" % (
                    r, m, d["retire_med"], 100 * d["p_mise_recup"], d["compte_med"], d["total_med"], d["total_moy"],
                    100 * d["p_total_sous_mise"], 100 * d["p_total_sous_moitie"]))
    pd.DataFrame(rows).round(4).to_csv(os.path.join(ICI, "donnees", "retrait.csv"), index=False)
