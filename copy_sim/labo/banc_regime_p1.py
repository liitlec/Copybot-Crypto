"""Lot B, piste 1 : modele de regime PROBABILISTE (chaine de Markov cachee gaussienne / Hamilton) ajuste EN LIGNE,
avec hysteresis, qui donne les poids des 6 familles du socle (regime_socle.py, inchange).

Idee : le marche de l'or alterne des regimes (agite / tendance contre calme / va-et-vient). Une chaine de Markov
cachee a 2 ou 3 etats, reestimee chaque mois sur les seules donnees deja connues, donne au debut de chaque jour J la
probabilite PREDITE de chaque etat (filtrage avant jusqu'au dernier jour complet avant J, puis une transition) ;
une hysteresis evite les bascules incessantes ; le regime retenu fixe les poids des familles.

Donnees (rien d'autre) : bougies H1 de l'or du courtier (banc_or.charge("xau_h1_50k"), meme source que OR_H1 du
socle, non coupee ; en pratique les H1 completes ne commencent que le 11/07/2022 : avant, bougies eparses, jours
ecartes) et P&L CONNU des familles (S.connu). Les premiers ajustements (08/2022 -> 01/2023) se font donc sur peu de
jours ; c'est la chauffe, avant tout hors echantillon.
Observations journalieres, une par jour serveur D ayant >= 6 bougies H1 :
  ret = somme des rendements log H1 de D (= log cloture derniere H1 de D / cloture derniere H1 avant D)   (Hamilton classique, 1 dimension)
  lrv = log de la somme des carres des rendements H1 de D (volatilite realisee)
  er  = |somme des rendements H1 de D| / somme des |rendements H1 de D|          (rendement d'efficience : tendance)
DECALAGES (verifies) : la derniere bougie du jour D commence a 23 h et ferme a minuit serveur = debut de D+1 ;
l'observation du jour D n'est donc utilisee que pour des jours J > D (on ne prend que les jours d'observation
strictement avant J). Les parametres du mois m sont estimes sur les observations des jours < m (fenetre EXPANSIVE
depuis le debut des donnees, centrage-reduction avec la moyenne / l'ecart-type de cette meme fenetre). Le filtrage est AVANT
uniquement (pas de lissage, pas de Viterbi) : prob. du jour J = filtre(dernier jour d'observation < J) x A.
Le P&L connu K = S.connu(cout) (valeur du jour D = ce qui est realise pendant D-1) est rattache au regime du jour
D-1 ; pour le mois m on n'utilise que K des jours D < m (donc connu au debut de m).

Calendrier : reestimation le 1er de chaque mois depuis 08/2022 (regimes calcules sur toute la periode JOURS) ;
evaluation par S.evalue (walk-forward 6 mois / 1 mois, exposition egale, White, spread reel et double).
Etats ranges a chaque reestimation par la moyenne de la 1re colonne (ret : par variance de ret) : le dernier etat =
« agite / tendance », le premier = « calme ». EM gaussien (covariance diagonale) ecrit ici en numpy, demarrage
par quantiles au 1er mois puis a chaud depuis le mois precedent, 300 / 60 iterations maximum.

GRILLE FIXEE D'AVANCE (36 reglages = 3 x 2 x 3 x 2), nom "obs/K/carte/hyst" :
  obs   : ret (1 dim) | lrv (1 dim) | er+lrv (2 dim)
  K     : 2 | 3 etats
  carte : fixe   = etat haut : bt_or_h1 x2, cassure_h1 x2, retour_h1 x0 ; etat bas : bt_or_h1 x0, cassure_h1 x0,
                   retour_h1 x2 ; etat du milieu (K=3) : tout x1 ; familles d'indices toujours x1
          inv    = l'inverse (haut <-> bas)
          appris = pour chaque etat et chaque famille, sur le P&L connu depuis 08/2022 jusqu'a la veille du mois :
                   x2 si la moyenne dans cet etat > 0, x0 sinon ; x1 si moins de 20 jours dans l'etat
  hyst  : non (etat = argmax de la prob. predite) | oui (on quitte l'etat courant seulement si sa prob. < 0,2 ou si
          un autre etat depasse 0,8 ; on va alors a l'etat le plus probable)
Aucun autre reglage ne sera essaye ; la periode reservee (>= 05/2026) n'a servi a rien regler.
VERDICT FIXE D'AVANCE : critere du socle (S.evalue) -- retenu seulement si, au spread reel, le walk-forward gagne en
P1 et P2, bat TOUT et SUIVRE5 en P1 et P2, p corrige de White < 0,05, et bat encore les deux au spread double.
Cache : donnees/regime_p1_cache.pkl (probabilites predites, independantes du cout). Usage : python3 banc_regime_p1.py
"""
import contextlib, io, os, pickle, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import regime_socle as S
    import banc_or as B

CACHE = os.path.join(S.DONL, "regime_p1_cache.pkl")
OBS = ("ret", "lrv", "er+lrv")
KS = (2, 3)
CARTES = ("fixe", "inv", "appris")
HYST = ("non", "oui")
HAUT, BAS = 0.8, 0.2
OR = ["bt_or_h1", "cassure_h1", "retour_h1"]


# ------------------------------------------------------------------------------------------------ observations
def observations():
    """Observations journalieres de l'or (index = jour serveur D ; connues au debut de D+1)."""
    d, _ = B.charge("xau_h1_50k")
    c = d["cloture"].astype(float)
    r = np.log(c).diff()                                        # rendement H1 (cloture a cloture, y compris le gap)
    jour = c.index.floor("D")
    g = pd.DataFrame({"r": r, "j": jour}).dropna().groupby("j")["r"]
    n = g.size()
    ret = g.sum(); rv = (g.apply(lambda x: (x ** 2).sum())); ab = g.apply(lambda x: x.abs().sum())
    X = pd.DataFrame({"ret": ret, "lrv": np.log(rv + 1e-12), "er": ret.abs() / ab.replace(0, np.nan)})
    return X[n >= 6].dropna()


# ------------------------------------------------------------------------------------------------ HMM gaussien
def _logdens(X, mu, var):
    # X (T,d), mu/var (K,d) -> log densite (T,K), covariance diagonale
    return -0.5 * (((X[:, None, :] - mu[None]) ** 2 / var[None]) + np.log(2 * np.pi * var[None])).sum(2)


def _forward(L, pi, A):
    """Filtrage avant normalise : alpha[t] = P(etat t | obs 0..t). Rend (alpha, log-vraisemblance)."""
    T, K = L.shape
    m = L.max(1, keepdims=True); E = np.exp(L - m)
    al = np.empty((T, K)); ll = 0.0
    a = pi * E[0]
    for t in range(T):
        if t:
            a = (al[t - 1] @ A) * E[t]
        s = a.sum(); al[t] = a / s; ll += np.log(s)
    return al, ll + m.sum()


def _backward(L, A, al):
    T, K = L.shape
    E = np.exp(L - L.max(1, keepdims=True))
    be = np.ones((T, K))
    for t in range(T - 2, -1, -1):
        b = A @ (E[t + 1] * be[t + 1]); be[t] = b / b.sum()
    return be, E


def em(X, K, init=None, iters=300, tol=1e-6, cle="moy"):
    """Baum-Welch gaussien diagonal. Le lissage (backward) ne sert QU'A l'estimation sur la fenetre d'apprentissage
    (donnees < mois m) ; les regimes utilises sont toujours issus du filtrage avant."""
    T, d = X.shape
    if init is None:
        o = np.argsort(np.abs(X[:, 0]) if cle == "var" else X[:, 0]); lab = np.empty(T, int); lab[o] = np.arange(T) * K // T
        mu = np.array([X[lab == k].mean(0) for k in range(K)])
        var = np.array([X[lab == k].var(0) + 1e-3 for k in range(K)])
        A = np.full((K, K), 0.05 / (K - 1)); np.fill_diagonal(A, 0.95); pi = np.full(K, 1.0 / K)
    else:
        pi, A, mu, var = [np.array(x, float) for x in init]
    prev = -np.inf
    for _ in range(iters):
        L = _logdens(X, mu, var)
        al, ll = _forward(L, pi, A)
        be, E = _backward(L, A, al)
        ga = al * be; ga /= ga.sum(1, keepdims=True)
        xi = (al[:-1, :, None] * A[None] * (E[1:] * be[1:])[:, None, :])
        xi /= xi.sum((1, 2), keepdims=True)
        pi = ga[0] * 0.98 + 0.02 / K
        A = xi.sum(0) + 1e-6; A /= A.sum(1, keepdims=True)
        w = ga.sum(0) + 1e-9
        mu = (ga.T @ X) / w[:, None]
        var = (ga.T @ X ** 2) / w[:, None] - mu ** 2 + 1e-3
        if ll - prev < tol * abs(ll):
            break
        prev = ll
    return pi, A, mu, var


def _range(par, cle):
    """Range les etats : cle = moyenne de la 1re colonne, ou variance de la 1re colonne (obs ret)."""
    pi, A, mu, var = par
    o = np.argsort(var[:, 0] if cle == "var" else mu[:, 0])
    return pi[o], A[np.ix_(o, o)], mu[o], var[o]


def probas(obs, K):
    """Prob. PREDITE de chaque etat au debut de chaque jour de S.JOURS (DataFrame JOURS x K), reestimation mensuelle."""
    X0 = observations()
    cols = {"ret": ["ret"], "lrv": ["lrv"], "er+lrv": ["er", "lrv"]}[obs]
    cle = "var" if obs == "ret" else "moy"
    X0 = X0[cols]
    out = pd.DataFrame(np.nan, index=S.JOURS, columns=range(K))
    par = None
    for m0 in pd.date_range(S.DEBUT, S.JOURS[-1], freq="MS"):
        app = X0[X0.index < m0]                                 # observations des jours < m (connues au debut de m)
        mu_n, sd_n = app.mean().values, app.std().values
        Xa = (app.values - mu_n) / sd_n
        par = _range(em(Xa, K, init=par, iters=300 if par is None else 60, cle=cle), cle)
        pi, A, mu, var = par
        jm = S.JOURS[(S.JOURS >= m0) & (S.JOURS < m0 + pd.offsets.MonthBegin(1))]
        if not len(jm):
            continue
        Xf = X0[X0.index < jm[-1]]                               # filtre sur les jours < dernier jour du mois
        al, _ = _forward(_logdens((Xf.values - mu_n) / sd_n, mu, var), pi, A)
        n = Xf.index.searchsorted(jm, side="left")               # nb d'observations de jours STRICTEMENT < J
        out.loc[jm] = al[n - 1] @ A                              # prediction d'un pas : P(etat J | obs < J)
    return out


def toutes_probas():
    if os.path.exists(CACHE):
        with open(CACHE, "rb") as f:
            P = pickle.load(f)
        if all((o, k) in P for o in OBS for k in KS) and P["_fin"] == S.JOURS[-1]:
            return P
    t0 = time.time(); P = {"_fin": S.JOURS[-1]}
    for o in OBS:
        for k in KS:
            P[(o, k)] = probas(o, k)
            print("  HMM %s K=%d ajuste (%.0f s)" % (o, k, time.time() - t0), flush=True)
    with open(CACHE, "wb") as f:
        pickle.dump(P, f)
    return P


# ------------------------------------------------------------------------------------------------ regimes -> poids
def etats(Pj, hyst):
    """Etat retenu chaque jour J (depend seulement des prob. predites jusqu'a J)."""
    p = Pj.values; s = np.empty(len(p), int); cur = int(np.argmax(p[0]))
    for t in range(len(p)):
        if hyst == "non":
            cur = int(np.argmax(p[t]))
        else:
            autre = [k for k in range(p.shape[1]) if k != cur and p[t, k] > HAUT]
            if p[t, cur] < BAS or autre:
                cur = int(np.argmax(p[t]))
        s[t] = cur
    return pd.Series(s, index=Pj.index)


def carte_fixe(K, inv):
    M = pd.DataFrame(1.0, index=range(K), columns=S.FAMS)
    haut, bas = (0, K - 1) if inv else (K - 1, 0)
    M.loc[haut, ["bt_or_h1", "cassure_h1", "retour_h1"]] = [2.0, 2.0, 0.0]
    M.loc[bas, ["bt_or_h1", "cassure_h1", "retour_h1"]] = [0.0, 0.0, 2.0]
    return M


_K = {}


def W_regle(obs, K, carte, hyst, cout):
    P = toutes_probas()
    s = etats(P[(obs, K)], hyst)
    if carte != "appris":
        M = carte_fixe(K, carte == "inv")
        return pd.DataFrame(M.loc[s.values].values, index=S.JOURS, columns=S.FAMS)
    if cout not in _K:
        _K[cout] = S.connu(cout)
    Kc = _K[cout]
    lab = s.shift(1)                                            # K du jour D = P&L realise pendant D-1 -> etat de D-1
    W = pd.DataFrame(1.0, index=S.JOURS, columns=S.FAMS)
    for m0 in pd.date_range(S.DEBUT, S.JOURS[-1], freq="MS"):
        jm = (S.JOURS >= m0) & (S.JOURS < m0 + pd.offsets.MonthBegin(1))
        k = (S.JOURS < m0) & lab.notna().values                 # seulement K des jours D < m : connu au debut de m
        M = pd.DataFrame(1.0, index=range(K), columns=S.FAMS)
        for e in range(K):
            ke = k & (lab.values == e)
            if ke.sum() >= 20:
                M.loc[e] = np.where(Kc[ke].mean().values > 0, 2.0, 0.0)
        W.loc[jm] = M.loc[s[jm].values].values
    return W


def grille():
    G = {}
    for o in OBS:
        for k in KS:
            for c in CARTES:
                for h in HYST:
                    G["%s/%d/%s/%s" % (o, k, c, h)] = (lambda cout, o=o, k=k, c=c, h=h: W_regle(o, k, c, h, cout))
    return G


if __name__ == "__main__":
    t0 = time.time()
    P = toutes_probas()
    for o in OBS:
        for k in KS:
            for h in HYST:
                s = etats(P[(o, k)], h); s = s[s.index >= S.OOS]
                print("  %-7s K=%d hyst=%-3s : part des etats %s, bascules/an %.1f" % (
                    o, k, h, np.round(s.value_counts(normalize=True).sort_index().values, 2),
                    (s.diff() != 0).sum() / (len(s) / 252)))
    G = grille()
    res = S.evalue("p1 HMM", G)
    S.ligne_csv("p1 HMM", res)
    print("  Choix mois par mois :", " ".join("%s:%s" % c for c in res[1.0]["choix"]))
    print("%.0f s" % (time.time() - t0))
