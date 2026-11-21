"""Banc AB : la bonne famille de regles au bon moment (PRIORITES 17/11 10 h 15). Or, bougies du courtier, 15 mois,
spread reel, une position a la fois par regle, $ a 0,01 lot (1 bp = 0,40 $), pause au calme comme la v11
(jour precedent sous la mediane d'amplitude de 60 jours : pas de trade ; connu la veille).
Famille TENDANCE : elan_m15 (sens des 3 dernieres heures, tenue 3 h), cassure_m15 (sortie de la fourchette de 12 h,
tenue 3 h). Famille RETOUR (equivalents M5 des regles M1 du robot, qui n'ont que 3 mois d'historique) :
fcassure_m5 (on contre la sortie de la fourchette d'1 h, tenue 15 min), contre_exces_m5 (on contre une bougie M5 de
plus de 3 ecarts-types, tenue 15 min).
Piste 1 « le marche choisit » : a chaque sortie de la fourchette de 12 h (M15), on regarde 1 h apres : si le prix
  est revenu dans la fourchette -> mode RETOUR, s'il tient au-dela -> mode TENDANCE ; le mode dure jusqu'a la
  prochaine sortie jugee. Resultat de chaque famille selon le mode a l'entree.
Piste 2 « suivre ce qui marche » : poids 1,5 / 0,5 de chaque famille selon son resultat des N derniers jours.
Piste 3 « les deux a la fois » : correlation par jour, melange a risque egal.
Piste 4 « filtre de direction » : la tendance n'entre que dans le sens du fond (moyenne 2 jours et moyenne 20 h) et
  pas deja au bout de la fourchette du jour (dernier cinquieme).
Reglage = 1re moitie, verdict = 2de moitie. Usage : python3 banc_famille.py"""
import numpy as np, pandas as pd
import banc_or as B

USD = 0.40
m15, _ = B.charge("xau_m15_50k"); m5, _ = B.charge("xau_m5_90k")
m15 = m15[m15.index >= m5.index[0]]
jour = lambda d: d.index.floor("D")
D = m5.groupby(jour(m5)).agg(h=("haut", "max"), b=("bas", "min"), o=("cloture", "first"))
rg = (D.h - D.b) / D.o
calme_v = (rg.shift(1) < rg.shift(1).rolling(60, min_periods=20).median()).fillna(False)   # connu la veille


def tr(d, s, h, filtre=None):
    """Trades d'une regle : DataFrame (heure d'entree, gain $), pause au calme appliquee."""
    s = s.copy()
    s[calme_v.reindex(jour(d)).fillna(False).values] = 0
    if filtre is not None:
        s[~filtre] = 0
    x, i = B.trades(d, s, h)
    return pd.DataFrame({"g": x[:, 0] * USD, "s": np.sign(s.values[i])}, index=d.index[i])


lr = np.log(m15["cloture"])
s_elan = np.sign(lr - lr.shift(12))
ha, ba = m15["haut"].shift(1).rolling(48).max(), m15["bas"].shift(1).rolling(48).min()
s_cass = (m15["cloture"] > ha).astype(float) - (m15["cloture"] < ba).astype(float)
h5, b5 = m5["haut"].shift(1).rolling(12).max(), m5["bas"].shift(1).rolling(12).min()
s_fc = (m5["cloture"] < b5).astype(float) - (m5["cloture"] > h5).astype(float)
r = np.log(m5["cloture"]).diff(); z = r / r.rolling(100).std().shift(1)
s_cx = (z < -3).astype(float) - (z > 3).astype(float)
REGLES = {"elan_m15": (m15, s_elan, 12, "T"), "cassure_m15": (m15, s_cass, 12, "T"),
          "fcassure_m5": (m5, s_fc, 3, "R"), "contre_exces_m5": (m5, s_cx, 3, "R")}
T = {n: tr(d, s, h) for n, (d, s, h, _) in REGLES.items()}
mil = m5.index[len(m5) // 2]


def st(x):
    x = np.asarray(x, float)
    if len(x) < 10:
        return "%5d tr      -       " % len(x)
    return "%5d tr %+5.2f $ (t %+.1f)" % (len(x), x.mean(), x.mean() / x.std() * np.sqrt(len(x)))


def deux(x):
    return "%s | %s" % (st(x.g[x.index < mil]), st(x.g[x.index >= mil]))


def bilan(nom, x):
    """x = gains par jour."""
    x = x[x.index.dayofweek < 5]
    c = x.cumsum(); m = x.groupby(x.index.to_period("M")).sum()
    a, b = x[x.index < mil].sum(), x[x.index >= mil].sum()
    print("  %-52s total %+7.0f $ (1re moitie %+6.0f, 2de %+6.0f)  mois<0 %2d/%d  pire creux %+6.0f $" % (nom, x.sum(), a, b, (m < 0).sum(), len(m), (c - c.cummax()).min()))


pj = lambda x: x.g.groupby(x.index.floor("D")).sum()
print("0) Les regles seules (reglage | verdict)")
for n, x in T.items():
    print("  %-18s %s" % (n, deux(x)))

print("\n1) Le marche choisit : mode d'apres la derniere sortie de la fourchette de 12 h, jugee 1 h apres")
c = m15["cloture"].values
ev = np.flatnonzero(s_cass.values != 0)
mode = pd.Series(np.nan, index=m15.index)
dern = -10
for i in ev:
    if i - dern < 4 or i + 4 >= len(c):
        continue
    dern = i
    niv = ha.values[i] if s_cass.values[i] > 0 else ba.values[i]
    tient = (c[i + 4] - niv) * s_cass.values[i] > 0
    mode.iloc[i + 4] = 1.0 if tient else -1.0          # connu a la cloture de la 4e bougie
mode = mode.ffill()
print("  sorties jugees : %d ; tiennent %.0f %% ; temps passe en mode tendance %.0f %%" % (mode.diff().ne(0).sum(), 100 * (mode.dropna().iloc[np.flatnonzero(mode.dropna().diff().ne(0).values)] > 0).mean(), 100 * (mode > 0).mean()))
for n, x in T.items():
    mo = mode.reindex(x.index, method="ffill")
    print("  %-18s mode tendance : %s || mode retour : %s" % (n, deux(x[mo > 0]), deux(x[mo < 0])))
sel = {}
for n, x in T.items():
    mo = mode.reindex(x.index, method="ffill")
    sel[n] = x[(mo > 0) if REGLES[n][3] == "T" else (mo < 0)]

print("\n4) Filtre de direction sur la famille tendance (reglage | verdict)")
ema2j = m15["cloture"].ewm(span=192).mean(); mm20h = m15["cloture"].rolling(80).mean()
fond = np.sign(m15["cloture"] - ema2j); fond20 = np.sign(m15["cloture"] - mm20h)
jh = m15["haut"].groupby(jour(m15)).cummax(); jb = m15["bas"].groupby(jour(m15)).cummin()
pos = ((m15["cloture"] - jb) / (jh - jb).replace(0, np.nan)).fillna(0.5)
F = {}
for n, s in (("elan_m15", s_elan), ("cassure_m15", s_cass)):
    bout = ((s > 0) & (pos > 0.8)) | ((s < 0) & (pos < 0.2))
    for nomf, f in (("fond 2 j", s == fond), ("fond 2 j et 20 h", (s == fond) & (s == fond20)), ("pas au bout du jour", ~bout),
                    ("fond 2 j + 20 h + pas au bout", (s == fond) & (s == fond20) & ~bout), ("CONTRE le fond 2 j", s == -fond)):
        x = tr(m15, s, 12, f.values)
        F[(n, nomf)] = x
        print("  %-12s %-30s %s" % (n, nomf, deux(x)))

print("\n3) Les deux familles par jour")
JT = pj(T["elan_m15"]).add(pj(T["cassure_m15"]), fill_value=0)
JR = pj(T["fcassure_m5"]).add(pj(T["contre_exces_m5"]), fill_value=0)
idx = D.index[D.index.dayofweek < 5]
JT, JR = JT.reindex(idx).fillna(0), JR.reindex(idx).fillna(0)
print("  correlation par jour tendance / retour : %+.2f (1re moitie %+.2f, 2de %+.2f) ; jours ou les deux perdent : %.0f %%, ou l'une compense l'autre : %.0f %%"
      % (JT.corr(JR), JT[JT.index < mil].corr(JR[JR.index < mil]), JT[JT.index >= mil].corr(JR[JR.index >= mil]),
         100 * ((JT < 0) & (JR < 0)).mean(), 100 * (((JT < 0) & (JR > 0)) | ((JT > 0) & (JR < 0))).mean()))
bilan("tendance seule (elan + cassure)", JT)
bilan("tendance sans elan_m15 (cassure seule)", pj(T["cassure_m15"]).reindex(idx).fillna(0))
bilan("retour seul (fcassure_m5 + contre_exces_m5)", JR)
k = JT[JT.index < mil].std() / max(JR[JR.index < mil].std(), 1e-9)
bilan("les deux a risque egal (poids regle sur la 1re moitie)", (JT + k * JR) / 2)

print("\n2) Suivre ce qui marche : poids 1,5 si la famille a gagne sur les N derniers jours, 0,5 sinon (meme exposition moyenne)")
for N in (1, 3, 5, 10):
    for nom, J in (("tendance", JT), ("retour", JR)):
        w = np.where(J.shift(1).rolling(N).sum() > 0, 1.5, 0.5); w = w / w.mean()
        bilan("%s, N = %2d jours" % (nom, N), J * w)
for N in (3, 10):
    mieux = JT.shift(1).rolling(N).sum() > JR.shift(1).rolling(N).sum() * k
    bilan("la famille qui a le mieux marche sur %d j (l'autre a 0)" % N, pd.Series(np.where(mieux, JT, k * JR), idx))
    bilan("  l'inverse (celle qui a le moins bien marche)", pd.Series(np.where(mieux, k * JR, JT), idx))

print("\n5) Synthese par jour (petites regles seulement, hors bt_or)")
bilan("selection v11 : elan_m15 + cassure_m15", JT)
bilan("sans elan_m15", pj(T["cassure_m15"]).reindex(idx).fillna(0))
bilan("piste 1 : tendance en mode tendance + retour en mode retour", sum(pj(x).reindex(idx).fillna(0) for x in sel.values()))
bilan("piste 1, tendance seule en mode tendance", sum(pj(sel[n]).reindex(idx).fillna(0) for n in ("elan_m15", "cassure_m15")))
bilan("piste 4 : tendance filtree (fond 2 j + 20 h + pas au bout)", sum(pj(F[(n, "fond 2 j + 20 h + pas au bout")]).reindex(idx).fillna(0) for n in ("elan_m15", "cassure_m15")))
bilan("piste 4 : cassure_m15 filtree seule", pj(F[("cassure_m15", "fond 2 j + 20 h + pas au bout")]).reindex(idx).fillna(0))

print("\n2 bis) Suivre ce qui marche, mesure directe : gain du jour de la famille tendance selon son resultat des N jours d'avant")
for N in (1, 3, 5, 10):
    av = JT.shift(1).rolling(N).sum()
    for nom, per in (("reglage", JT.index < mil), ("verdict", JT.index >= mil)):
        a, b = JT[per & (av > 0)], JT[per & (av <= 0)]
        d = a.mean() - b.mean(); e = np.sqrt(a.var() / len(a) + b.var() / len(b))
        print("  N = %2d, %s : apres un gain %3d j %+6.2f $/j ; apres une perte ou rien %3d j %+6.2f $/j ; ecart %+5.2f (t %+.1f)" % (N, nom, len(a), a.mean(), len(b), b.mean(), d, d / e))
