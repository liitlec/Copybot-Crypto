"""Lot B, piste 4 : ponderation EN LIGNE de type bandit entre les 6 familles du socle (regime_socle.py), avec plancher.

Idee : plutot que de deviner le type de marche, laisser un algorithme d'apprentissage en ligne deplacer le poids vers
les familles qui gagnent recemment, sans jamais en couper une completement (plancher). Trois algorithmes :
  hedge    : poids exponentiels, p_f ~ exp(eta x G_f), G_f = somme (avec oubli gamma) des gains CONNUS de la famille.
  exp3     : version bandit (on n'observe que la famille tiree au sort, graine fixe 4) ; gain ramene a [0, 1] par
             (clip(k, -3, 3) + 3) / 6, estimateur pondere par l'inverse de la probabilite, poids exponentiels eta.
  thompson : gain moyen de chaque famille ~ normale (moyenne G_f / (n_f + 1), ecart-type 1 / racine(n_f + 1), n_f =
             nombre de jours avec oubli gamma, a priori 0 avec 1 jour fictif) ; p_f = part des 500 tirages (graine
             fixe 4) ou la famille est la meilleure.
Plancher : p = (1 - 6 x plancher) x p_algo + plancher (chaque famille garde au moins « plancher » du poids total).
Poids du jour : W = 6 x p (somme = 6 familles), borne a 2 ; l'excedent est redistribue aux familles non bornees au
prorata de leur poids (iteratif), la somme reste 6.

Calendrier / information : mise a jour quotidienne avec S.connu(cout) UNIQUEMENT (P&L poids 1 connu au debut de J :
trades sortis avant J, positions journalieres jusqu'a J-1). Les poids du jour J utilisent les lignes de connu() jusqu'a
J inclus (comme SUIVRE5 du socle), jamais pnl_fams. Exp3 : le tirage du jour J est recompense par l'increment connu
au jour suivant. Accumulation depuis le 01/08/2022 (chauffe comprise, connue). Echelle u du socle (1 u = 1 ecart-type
journalier de la famille en chauffe).

Grille FIXEE D'AVANCE (28 reglages ; rien n'est regle sur la periode reservee >= 05/2026) :
  hedge    : eta in {0,02 ; 0,05 ; 0,1} x oubli gamma in {1 (aucun) ; 0,99 ; 0,97} x plancher in {5 % ; 10 %}  -> 18
  exp3     : eta = 0,05 x oubli in {1 ; 0,98} x plancher in {5 % ; 10 %}                                         ->  4
  thompson : oubli in {1 ; 0,99 ; 0,97} x plancher in {5 % ; 10 %}                                              ->  6
Evaluation : S.evalue (walk-forward 6 mois / 1 mois au meilleur t, exposition egale a TOUT, White sur 28 + wf,
spread reel et double), puis S.ligne_csv.
Verdict fixe d'avance = critere du socle (PRIORITES 23/11) : RETENU si, au spread reel, le walk-forward gagne en P1 ET
P2, bat TOUT et SUIVRE5 en P1 ET P2, p corrige (White) < 0,05, et bat encore les deux references en P1 et P2 au
spread double ; sinon « ne tient pas ». Usage : python3 banc_regime_p4.py"""
import time
import numpy as np, pandas as pd
import regime_socle as S

JOURS, FAMS = S.JOURS, S.FAMS
NF = len(FAMS)
_K = {}


def K_connu(cout):
    if cout not in _K:
        _K[cout] = S.connu(cout).reindex(index=JOURS, columns=FAMS).fillna(0.0).values
    return _K[cout]


def borne(p, cap=2.0):
    """W = NF x p, borne a cap, excedent redistribue au prorata des non bornes (somme conservee = NF)."""
    w = NF * p
    for _ in range(NF):
        haut = w > cap + 1e-12
        if not haut.any():
            break
        exc = (w[haut] - cap).sum(); w[haut] = cap
        libre = w < cap - 1e-12
        if not libre.any():
            break
        w[libre] += exc * w[libre] / w[libre].sum()
    return np.minimum(w, cap)


def plancher(p, x):
    return (1 - NF * x) * p + x


def softmax(z):
    z = z - z.max(); e = np.exp(z)
    return e / e.sum()


def hedge(eta, gam, x):
    def f(cout):
        K = K_connu(cout); G = np.zeros(NF); W = np.empty_like(K)
        for j in range(len(K)):
            G = gam * G + K[j]                              # connu au debut de J
            W[j] = borne(plancher(softmax(eta * G), x))
        return pd.DataFrame(W, index=JOURS, columns=FAMS)
    return f


def exp3(eta, gam, x):
    def f(cout):
        K = K_connu(cout); rng = np.random.default_rng(4)
        L = np.zeros(NF); W = np.empty_like(K); prec = None
        for j in range(len(K)):
            L = gam * L
            if prec is not None:                            # recompense du tirage d'hier = increment connu aujourd'hui
                a, pa = prec
                r = (np.clip(K[j, a], -3, 3) + 3) / 6
                L[a] += eta * r / pa
            p = plancher(softmax(L), x)
            W[j] = borne(p.copy())
            a = rng.choice(NF, p=p / p.sum()); prec = (a, p[a])
        return pd.DataFrame(W, index=JOURS, columns=FAMS)
    return f


def thompson(gam, x, M=500):
    def f(cout):
        K = K_connu(cout); rng = np.random.default_rng(4)
        G = np.zeros(NF); n = 0.0; W = np.empty_like(K)
        for j in range(len(K)):
            G = gam * G + K[j]; n = gam * n + 1
            mu, sd = G / (n + 1), 1 / np.sqrt(n + 1)
            tir = mu + sd * rng.standard_normal((M, NF))
            p = np.bincount(tir.argmax(1), minlength=NF) / M
            W[j] = borne(plancher(p, x))
        return pd.DataFrame(W, index=JOURS, columns=FAMS)
    return f


GRILLE = {}
for eta in (0.02, 0.05, 0.1):
    for gam in (1.0, 0.99, 0.97):
        for x in (0.05, 0.10):
            GRILLE["hedge e%g g%g p%g" % (eta, gam, x)] = hedge(eta, gam, x)
for gam in (1.0, 0.98):
    for x in (0.05, 0.10):
        GRILLE["exp3 e0.05 g%g p%g" % (gam, x)] = exp3(0.05, gam, x)
for gam in (1.0, 0.99, 0.97):
    for x in (0.05, 0.10):
        GRILLE["thompson g%g p%g" % (gam, x)] = thompson(gam, x)

if __name__ == "__main__":
    t0 = time.time()
    assert 10 <= len(GRILLE) <= 40
    res = S.evalue("p4 bandit", GRILLE)
    S.ligne_csv("p4 bandit", res)
    print("  Choix par mois (spread reel) :", "; ".join("%s %s" % mc for mc in res[1.0]["choix"]))
    print("%.0f s" % (time.time() - t0))
