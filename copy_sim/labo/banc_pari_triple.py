"""Banc AP bis : poche pari « triple ou rien » (PRIORITES 17/11 17 h 20). Reprend banc_pari.py (memes trades reels,
memes tailles du courtier, meme liquidation, jours tires par blocs de 20).
Regle de la poche : on s'arrete des que le compte atteint l'objectif (x3, variante x5) ou passe sous le seuil de ruine
(20 % du depart). Monte-Carlo de 10 000 parcours jusqu'a 5 ans au plus : chance d'atteindre l'objectif AVANT la ruine,
chance de ruine, chance de n'avoir rien atteint en 5 ans, duree mediane (jours de bourse) jusqu'a l'arret.
Scenario unique (prudent) : avantage divise par 2. Departs 100 et 500 (dollars du compte, = euros a peu pres).
Montages : repli S&P + Russell (pari_opt actuel), contre-pied du Nasdaq, les deux, bt_or (or, 4 ans) ;
mises : lot mini, 1, 2, 3 Kelly (Kelly mesure sur les trades a avantage / 2).
Reperes : sans avantage et sans frais, la chance de x3 avant la ruine a 20 % est (1 - 0,2) / (3 - 0,2) = 29 % ;
de x5 : 0,8 / 4,8 = 17 %. Choix fixe d'avance : le montage x mise qui maximise la chance de x3 a 100 $.
Usage : python3 banc_pari_triple.py"""
import os, sys, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
with contextlib.redirect_stdout(io.StringIO()):
    import banc_pari as P

rng = np.random.default_rng(1720)
NPAR, JMAX, BLOC = 10000, 1260, 20


def premier_passage(tabs, fs, depart, objectif, src_n):
    E = np.full(NPAR, depart)
    fini = np.zeros(NPAR, bool); gagne = np.zeros(NPAR, bool); duree = np.full(NPAR, JMAX)
    pos = rng.integers(src_n, size=NPAR)
    for t in range(JMAX):
        if t % BLOC == 0:
            pos = rng.integers(src_n, size=NPAR)
        k = (pos + t % BLOC) % src_n
        tot = np.zeros(NPAR); adv = np.zeros(NPAR); mg = np.zeros(NPAR)
        for (pnl, risk, mae, marge), f in zip(tabs, fs):
            p, r, a, m = pnl[k], risk[k], mae[k], marge[k]
            actif = r > 0
            u = np.ones_like(p) if f is None else np.maximum(1.0, np.floor(f * E[:, None] / np.where(actif, r, 1.0)))
            u = np.where(actif, u, 0.0)
            tot += (u * p).sum(1); adv += (u * a).sum(1); mg += (u * m).sum(1)
        liq = (E - adv) < 0.5 * mg
        E = np.where(fini, E, np.maximum(0.0, np.where(liq, np.minimum(E, 0.5 * mg), E + tot)))
        g = ~fini & (E >= objectif * depart)
        perdu = ~fini & (E < 0.2 * depart)
        gagne |= g
        duree[g | perdu] = t + 1
        fini |= g | perdu
        if fini.all():
            break
    return gagne.mean(), (fini & ~gagne).mean(), (~fini).mean(), int(np.median(duree))


if __name__ == "__main__":
    reb, rep, bth = P.trades_rebond(), P.trades_repli(), P.trades_bt()
    rep = rep[rep.marche.isin(["sp", "us2000"])]
    c = P.d1("nas").index
    def moitie(T, col):
        T = T.copy(); T[col] = T[col] - 0.5 * T[col].mean()
        if col == "R":
            T["usd"] = T.R * T.risque
        return T
    reb2, rep2, bt2 = moitie(reb, "r"), moitie(rep, "r"), moitie(bth, "R")
    MONT = {"repli S&P + Russell": ([(rep2, "ind")], c[c >= "2020-09-15"]),
            "contre-pied Nasdaq": ([(reb2, "ind")], c[c >= reb.jour.min()]),
            "les deux": ([(reb2, "ind"), (rep2, "ind")], c[c >= "2020-09-15"]),
            "bt_or (or)": ([(bt2, "bt")], c[c >= "2022-08-01"])}
    lignes = []
    for nom, (pieces, C) in MONT.items():
        tabs = [P.jours_tableau(T[T.jour >= C[0]], C, kd) for T, kd in pieces]
        kel = [P.kelly(T.R.values if kd == "bt" else T.r.values) for T, kd in pieces]
        for mnom, mult in (("lot mini", None), ("1 Kelly", 1.0), ("2 Kelly", 2.0), ("3 Kelly", 3.0)):
            fs = [None if mult is None else mult * k for k in kel]
            for dep in (100.0, 500.0):
                for obj in (3, 5):
                    g, r, rien, d = premier_passage(tabs, fs, dep, obj, len(C))
                    lignes.append(dict(montage=nom, mise=mnom, depart=int(dep), objectif="x%d" % obj, gagne=round(100 * g),
                                       ruine=round(100 * r), rien_en_5_ans=round(100 * rien), duree_mediane_jours=d))
    T = pd.DataFrame(lignes)
    pd.set_option("display.width", 220); pd.set_option("display.max_rows", 200)
    print("Avantage / 2 ; % des 10 000 parcours ; duree en jours de bourse (252 = 1 an) :")
    print(T.to_string(index=False))
    T.to_csv(os.path.join(ICI, "donnees", "pari_triple.csv"), index=False)
    b = T[(T.depart == 100) & (T.objectif == "x3")].sort_values("gagne", ascending=False).iloc[0]
    print("\nChoix fixe d'avance (max chance de x3 a 100) :", dict(b))
