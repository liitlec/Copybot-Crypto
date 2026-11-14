"""Banc O : que faudrait-il pour « 1 % par jour » avec les deux candidats, et a quel risque ?
A partir de leurs trades au banc (15 mois, or), on rejoue 5 000 annees possibles en tirant des blocs de trades
consecutifs (pour garder les series de pertes), a taille proportionnelle au compte. Pour chaque niveau de risque :
gain median sur un an, pire baisse mediane, chances de perdre 50 % du compte en cours d'annee, chances de finir
l'annee en perte. Hypothese genereuse : le futur ressemble aux 15 mois du banc. Usage : python3 banc_objectif.py"""
import numpy as np, pandas as pd
import banc_grille as G, banc_blocktrend as BT, banc_plateau as P


def annees(gains, par_an, risque, tirages=5000, bloc=10, graine=1):
    """gains : resultat par trade en unites de risque (R). risque : part du compte risquee par R."""
    rng = np.random.default_rng(graine)
    n = len(gains); k = int(par_an)
    fin, creux, ruine = [], [], 0
    for _ in range(tirages):
        idx = np.concatenate([np.arange(s, s + bloc) % n for s in rng.integers(0, n, k // bloc + 1)])[:k]
        c = np.cumprod(np.maximum(1 + risque * gains[idx], 1e-6))
        dd = (c / np.maximum.accumulate(np.maximum(c, 1.0)) - 1).min()
        fin.append(c[-1]); creux.append(dd); ruine += dd <= -0.5
    fin = np.array(fin)
    return np.median(fin) - 1, np.median(creux), ruine / tirages, (fin < 1).mean()


def tableau(nom, gains, par_an, niveaux):
    jours = 252
    par_jour = gains.mean() * par_an / jours
    print("\n%s : %d trades au banc, %.0f par an, moyenne %+.3f R par trade, soit %+.3f R par jour de bourse" % (nom, len(gains), par_an, gains.mean(), par_jour))
    print("  pour 1 %% par jour en moyenne il faudrait risquer %.1f %% du compte par R" % (1.0 / par_jour))
    print("  %-22s %14s %14s %22s %18s" % ("risque par R", "gain median/an", "pire baisse", "perdre 50 % dans l'an", "finir en perte"))
    for r in niveaux:
        g, dd, ru, pe = annees(gains, par_an, r / 100)
        print("  %-22s %+13.0f%% %+13.0f%% %21.0f%% %17.0f%%" % ("%.2f %% (≈ %.2f %%/jour)" % (r, r * par_jour), 100 * g, 100 * dd, 100 * ru, 100 * pe))


if __name__ == "__main__":
    d = G.charge("xau_m5_90k")
    ans = (d["heure"].iloc[-1] - d["heure"].iloc[0]) / 86400 / 365.25
    bt = np.array([p[3] for p in BT.simule(d, 0.25, 0.6667, 3)])
    tableau("Mecanique BlockTrend sur l'or (3 positions au plus)", bt, len(bt) / ans, (0.25, 0.5, 1.0, 2.0, round(1 / (bt.mean() * len(bt) / ans / 252), 1)))
    i, g = P.gains(d, 20, 2.0, 3, P.FENETRES["12-15h"])
    keep, last = [], -99
    for k, ii in enumerate(i):
        if ii - last >= 3:
            keep.append(k); last = ii
    g = g[keep]
    R = 20.0                                   # 1 R = 20 bp de mouvement contre soi (stop de secours type)
    midi = g / R
    tableau("Retour de midi sur l'or (1 R = 20 bp, une position a la fois)", midi, len(midi) / ans, (0.5, 1.0, 2.0, 5.0, round(1 / (midi.mean() * len(midi) / ans / 252), 1)))
