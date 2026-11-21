"""Banc IA juge (17/11, PRIORITES 12 h 15, point 4) : un modèle de langage, à qui l'on montre seulement ce qui était
connu à l'instant t (bougies anonymes, sans date ni prix réels), dit-il juste « calme / tendance / aller-retour » pour
les 4 heures SUIVANTES de l'or ? Ce script PRÉPARE le banc à l'aveugle et NOTE les réponses ; il ne lance aucun modèle.

Moments : 180 tirés au hasard (graine fixe) dans les bougies du courtier (or M15/M5, Nasdaq et S&P M5), 60 à 9 h,
60 à 12 h et 60 à 15 h 30 heure de Paris, jours ouvrés, jamais deux moments le même jour. Horloge du serveur =
New York + 7 h ; la conversion vers Paris passe par les fuseaux (America/New_York -> Europe/Paris), ce qui gère les
semaines où les changements d'heure d'été ne tombent pas le même jour des deux côtés de l'Atlantique.

Vérité (définition des types de journée du labo, banc Y `banc_aller_retour.py`, ramenée à une fenêtre de 4 h) :
fenêtre = les bougies de l'or qui commencent à t ou après et avant t + 4 h ; amplitude = plus haut - plus bas ;
efficacité = |clôture - ouverture| / amplitude ; médiane de référence = médiane des amplitudes de la même fenêtre
(même horaire de Paris) sur les 60 jours ouvrés PRÉCÉDENTS.
  - calme        : amplitude <= médiane de référence ;
  - tendance     : amplitude > médiane et efficacité >= 0,35 ;
  - aller-retour : amplitude > médiane et efficacité < 0,35.

Texte montré au juge, par moment : identifiant opaque (m001..m180, mélangés), « matin Europe / midi Europe /
ouverture États-Unis », 32 dernières H1 et 32 dernières M15 de l'actif A (or), 16 dernières H1 des actifs B (Nasdaq)
et C (S&P) ; seules les bougies FERMÉES à t ; chaque actif ramené à 100 à l'ouverture de sa première bougie montrée
puis multiplié par un facteur aléatoire propre au moment (0,5 à 2) ; amplitude médiane d'une fenêtre de 4 h sur les
60 jours précédents (même échelle que l'actif A). Contrôles anti-fuite : aucune bougie montrée ne finit après t, la
médiane n'utilise que des jours antérieurs, aucun texte ne contient date, année, mois, jour ou nom de marché.

Usage :
  python3 banc_ia_juge.py prepare <dossier>   -> paquet_1.txt .. paquet_6.txt (pour les juges) + cle.json (À PART)
  python3 banc_ia_juge.py score <dossier>     -> lit reponses_<juge>.txt (lignes « m0xx;classe;confiance »)"""
import os, sys, re, json, glob, math
from collections import Counter
import numpy as np, pandas as pd
import banc_or as B

GRAINE = 20261117
CLASSES = ("calme", "tendance", "aller-retour")
CRENEAUX = {"9h": (9, 0, "matin Europe"), "12h": (12, 0, "midi Europe"), "15h30": (15, 30, "ouverture États-Unis")}
N_PAR_CRENEAU, N_PAQUETS = 60, 6
FENETRE = pd.Timedelta(hours=4)
SEUIL_EFF = 0.35
MAX_OCTETS = 60_000


# ---------- heures ----------
def serveur_vers_paris(idx):
    ny = (pd.DatetimeIndex(idx) - pd.Timedelta(hours=7)).tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
    return ny.tz_convert("Europe/Paris")


def paris_vers_serveur(ts_paris):
    """ts_paris : Timestamp avec fuseau Europe/Paris -> horloge naïve du serveur."""
    return ts_paris.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)


def h1(d):
    """Bougies H1 (début d'heure du serveur) à partir de M5/M15 ; 'fin' = début + 1 h."""
    g = d.resample("1h", label="left", closed="left").agg(
        {"ouverture": "first", "haut": "max", "bas": "min", "cloture": "last"}).dropna()
    g["fin"] = g.index + pd.Timedelta(hours=1)
    return g


# ---------- préparation ----------
def fenetres(m15, jours, hh, mm):
    """Pour chaque jour ouvré (date de Paris) : t serveur, o, c, amplitude de la fenêtre [t, t+4h)."""
    rows = []
    idx = m15.index
    for j in jours:
        tp = pd.Timestamp(j.year, j.month, j.day, hh, mm, tz="Europe/Paris")
        t = paris_vers_serveur(tp)
        a, b = idx.searchsorted(t), idx.searchsorted(t + FENETRE)
        x = m15.iloc[a:b]
        if len(x) < 14 or x.index[0] != t:
            continue
        amp = x.haut.max() - x.bas.min()
        rows.append((j, t, x.ouverture.iloc[0], x.cloture.iloc[-1], amp))
    F = pd.DataFrame(rows, columns=["jour", "t", "o", "c", "amp"]).set_index("jour")
    F["eff"] = (F.c - F.o).abs() / F.amp
    F["med"] = F.amp.rolling(60).median().shift(1)        # 60 jours PRÉCÉDENTS seulement
    F["classe"] = np.where(F.amp <= F.med, "calme", np.where(F.eff >= SEUIL_EFF, "tendance", "aller-retour"))
    return F


def bloc(df, base, f, titre, pas):
    """Lignes « h l c » : l'ouverture d'une bougie = clôture de la précédente (à 0,01-0,02 près, vérifié sur l'or) ;
    l'ouverture de la 1re bougie est dans le titre, celle qui suit une coupure dans la ligne de coupure."""
    e = lambda x: "%.2f" % (100 * f * x / base)
    lignes, prec = ["%s (h l c, la plus ancienne d'abord ; ouverture de la 1re : %s) :" % (titre, e(df.ouverture.iloc[0]))], None
    for ts, r in df.iterrows():
        if prec is not None and ts - prec > pas:
            lignes.append("-- coupure du marché, réouverture à %s --" % e(r.ouverture))
        prec = ts
        lignes.append(" ".join(e(x) for x in (r.haut, r.bas, r.cloture)))
    return lignes


def prepare(dossier):
    rng = np.random.default_rng(GRAINE)
    m15, _ = B.charge("xau_m15_50k")
    m5, _ = B.charge("xau_m5_90k")
    nas, _ = B.charge("nas_m5_90k")
    sp, _ = B.charge("sp_m5_90k")
    a_h1, nas_h1, sp_h1 = h1(m15), h1(nas), h1(sp)

    # période commune des 15 mois (M5 de l'or et des deux indices), + 1 jour de recul pour les 16 H1 des indices
    debut = max(m5.index[0], nas.index[0], sp.index[0]) + pd.Timedelta(days=2)
    fin = min(m5.index[-1], nas.index[-1], sp.index[-1], m15.index[-1]) - pd.Timedelta(hours=6)
    p = serveur_vers_paris(m15.index)
    jours = sorted({x.date() for x in p.dropna() if x.weekday() < 5})
    jours = [pd.Timestamp(j) for j in jours]

    cand = {}
    for cr, (hh, mm, _) in CRENEAUX.items():
        F = fenetres(m15, jours, hh, mm).dropna()
        F = F[(F.t >= debut) & (F.t + FENETRE <= fin)]
        cand[cr] = F
    # tirage : 180 jours distincts, 60 par créneau
    pris, choisis = set(), []
    for cr in rng.permutation(list(CRENEAUX)):
        F = cand[cr]
        libres = [j for j in F.index if j not in pris]
        sel = rng.choice(len(libres), N_PAR_CRENEAU, replace=False)
        for k in sel:
            j = libres[k]
            pris.add(j)
            choisis.append((cr, j, F.loc[j]))
    assert len(pris) == len(choisis) == 3 * N_PAR_CRENEAU

    ordre = rng.permutation(len(choisis))
    cle, textes = {}, {}
    controle_m5 = 0
    for num, k in enumerate(ordre, 1):
        cr, j, r = choisis[k]
        ident = "m%03d" % num
        t = r.t
        f = float(np.exp(rng.uniform(np.log(0.5), np.log(2.0))))
        A1 = a_h1[a_h1.fin <= t].iloc[-32:]
        A15 = m15[m15.index + pd.Timedelta(minutes=15) <= t].iloc[-32:]
        Bh = nas_h1[nas_h1.fin <= t].iloc[-16:]
        Ch = sp_h1[sp_h1.fin <= t].iloc[-16:]
        # anti-fuite : aucune bougie montrée ne finit après t ; fenêtre de vérité entièrement après t
        assert A1.fin.max() <= t and (A15.index + pd.Timedelta(minutes=15)).max() <= t
        assert Bh.fin.max() <= t and Ch.fin.max() <= t
        assert len(A1) == 32 and len(A15) == 32 and len(Bh) == 16 and len(Ch) == 16
        # recul raisonnable (pas de trou de données énorme)
        assert t - A1.index[0] < pd.Timedelta(days=5) and t - Bh.index[0] < pd.Timedelta(days=5)
        # contrôle croisé de la vérité sur M5
        x5 = m5[(m5.index >= t) & (m5.index < t + FENETRE)]
        if len(x5) and abs((x5.haut.max() - x5.bas.min()) - r.amp) < 1e-6 and abs(x5.ouverture.iloc[0] - r.o) < 1e-6:
            controle_m5 += 1
        baseA = A1.ouverture.iloc[0]
        lig = ["### %s" % ident,
               "moment : %s" % CRENEAUX[cr][2],
               "amplitude médiane d'une fenêtre de 4 h à cet horaire (60 jours précédents), échelle de l'actif A : %.2f"
               % (100 * f * r.med / baseA),
               ]
        lig += bloc(A1, baseA, f, "actif A, 32 dernières bougies H1", pd.Timedelta(hours=1))
        lig += bloc(A15, baseA, f, "actif A, 32 dernières bougies M15", pd.Timedelta(minutes=15))
        lig.append("actif B, clôtures des 16 dernières H1 : " + " ".join(
            "%.2f" % (100 * f * x / Bh.ouverture.iloc[0]) for x in Bh.cloture))
        lig.append("actif C, clôtures des 16 dernières H1 : " + " ".join(
            "%.2f" % (100 * f * x / Ch.ouverture.iloc[0]) for x in Ch.cloture))
        textes[ident] = "\n".join(lig)
        cle[ident] = {"classe": r.classe, "heure": cr, "date": str(j.date()), "t_serveur": str(t),
                      "amp": round(float(r.amp), 3), "med": round(float(r.med), 3), "eff": round(float(r.eff), 3),
                      "facteur": round(f, 4)}

    consigne = (
        "CONSIGNE. Chaque bloc ci-dessous montre un instant t (bougies déjà fermées seulement, prix déguisés : "
        "chaque actif est ramené à 100 puis multiplié par un facteur inconnu). Actif A = celui à juger ; B et C = "
        "deux autres marchés au même instant. Prédis le type des 4 HEURES SUIVANTES de l'actif A :\n"
        "- calme : amplitude des 4 h (plus haut - plus bas) <= l'amplitude médiane indiquée ;\n"
        "- tendance : amplitude > médiane ET |clôture - ouverture des 4 h| >= 0,35 x amplitude ;\n"
        "- aller-retour : amplitude > médiane ET |clôture - ouverture des 4 h| < 0,35 x amplitude.\n"
        "Bougies de A : une ligne « h l c » (haut, bas, clôture) ; l'ouverture de chaque bougie est la clôture de la "
        "précédente, sauf la 1re (donnée dans le titre) et après « -- coupure du marché, réouverture à x -- » "
        "(marché fermé entre deux bougies). B et C : clôtures horaires seulement.\n"
        "RÉPONSE : une ligne par moment, exactement « identifiant;classe;confiance » (ex. m007;calme;55), classe parmi "
        "calme, tendance, aller-retour, confiance entière de 0 à 100. Rien d'autre : pas de titre, pas d'explication.\n")
    # anti-fuite textuelle
    interdit = re.compile(r"(19|20)\d\d|janv|févr|mars|avril|mai\b|juin|juil|août|sept|octo|nove|déce|lundi|mardi|"
                          r"mercredi|jeudi|vendredi|samedi|dimanche|\bor\b|gold|xau|nas|s&p|sp500|nasdaq|dow|usd|\$",
                          re.I)
    for ident, s in textes.items():
        corps = "\n".join(l for l in s.split("\n") if not re.fullmatch(r"[\d. ]+", l))
        m = interdit.search(corps)
        assert not m, (ident, m.group(0))
    os.makedirs(dossier, exist_ok=True)
    ids = list(textes)
    rng.shuffle(ids)
    tailles = []
    for p in range(N_PAQUETS):
        part = ids[p * 30:(p + 1) * 30]
        s = consigne + "\n" + "\n\n".join(textes[i] for i in part) + "\n"
        chemin = os.path.join(dossier, "paquet_%d.txt" % (p + 1))
        with open(chemin, "w", encoding="utf-8") as fh:
            fh.write(s)
        tailles.append(len(s.encode("utf-8")))
    with open(os.path.join(dossier, "cle.json"), "w", encoding="utf-8") as fh:
        json.dump(cle, fh, ensure_ascii=False, indent=1, sort_keys=True)

    rep = Counter(v["classe"] for v in cle.values())
    print("%d moments (%s), %d jours distincts ; vérité recalculée à l'identique sur M5 : %d / %d" % (
        len(cle), ", ".join("%s %d" % (c, sum(v["heure"] == c for v in cle.values())) for c in CRENEAUX),
        len({v["date"] for v in cle.values()}), controle_m5, len(cle)))
    print("répartition : " + ", ".join("%s %d (%.0f %%)" % (c, rep[c], 100 * rep[c] / len(cle)) for c in CLASSES))
    for cr in CRENEAUX:
        rc = Counter(v["classe"] for v in cle.values() if v["heure"] == cr)
        print("  %-6s " % cr + ", ".join("%s %d" % (c, rc[c]) for c in CLASSES))
    print("période : %s -> %s" % (min(v["date"] for v in cle.values()), max(v["date"] for v in cle.values())))
    print("paquets (octets) : %s ; max %d (limite %d)" % (tailles, max(tailles), MAX_OCTETS))
    assert max(tailles) < MAX_OCTETS, "paquet trop gros"
    print("contrôles anti-fuite : bougies <= t, fenêtre >= t, médiane sur jours antérieurs, texte sans date ni nom : OK")
    print("cle.json ne doit JAMAIS être montré aux juges.")


# ---------- notation ----------
def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    e = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - e, c + e


def binom_sup(k, n, p):
    """P(X >= k), X ~ Binomiale(n, p)."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def lit(chemin, ids):
    rep, mauvaises = {}, 0
    for l in open(chemin, encoding="utf-8"):
        l = l.strip()
        if not l:
            continue
        m = re.fullmatch(r"(m\d{3})\s*;\s*([a-zé-]+)\s*;\s*(\d{1,3})", l, re.I)
        if not m or m.group(1) not in ids or m.group(2).lower() not in CLASSES or int(m.group(3)) > 100:
            mauvaises += 1
            continue
        rep[m.group(1)] = (m.group(2).lower(), int(m.group(3)))
    return rep, mauvaises


def rapport(nom, rep, cle, rng):
    ids = sorted(rep)
    n = len(ids)
    print("\n== %s : %d réponses sur %d moments ==" % (nom, n, len(cle)))
    if not n:
        return
    vrai = [cle[i]["classe"] for i in ids]
    pred = [rep[i][0] for i in ids]
    k = sum(a == b for a, b in zip(vrai, pred))
    lo, hi = wilson(k, n)
    freq = Counter(vrai)
    maj_c, maj_n = freq.most_common(1)[0]
    p_maj = maj_n / n
    p_hasard = sum((v / n) ** 2 for v in freq.values())
    print("bonnes réponses : %d / %d = %.1f %%  (IC 95 %% : %.1f - %.1f %%)" % (k, n, 100 * k / n, 100 * lo, 100 * hi))
    print("toujours « %s » (classe la plus fréquente) : %.1f %% ; hasard selon les fréquences : %.1f %%" % (
        maj_c, 100 * p_maj, 100 * p_hasard))
    print("p binomial (>= %d bonnes) contre la classe la plus fréquente : %.4f ; contre le hasard : %.4f" % (
        k, binom_sup(k, n, p_maj), binom_sup(k, n, p_hasard)))
    v = np.array(vrai)
    pr = np.array(pred)
    perm = np.array([(rng.permutation(v) == pr).sum() for _ in range(10000)])
    print("p permutation (mêmes prédictions, vérités mélangées, 10 000 tirages) : %.4f" % ((perm >= k).mean()))
    print("matrice de confusion (lignes = vrai, colonnes = prédit) :")
    print("  %-13s" % "" + "".join("%14s" % c for c in CLASSES))
    for a in CLASSES:
        print("  %-13s" % a + "".join("%14d" % sum((x == a) and (y == b) for x, y in zip(vrai, pred)) for b in CLASSES))
    print("par heure :")
    for cr in CRENEAUX:
        s = [i for i in ids if cle[i]["heure"] == cr]
        if s:
            kk = sum(rep[i][0] == cle[i]["classe"] for i in s)
            fr = Counter(cle[i]["classe"] for i in s).most_common(1)[0][1]
            print("  %-6s %2d / %2d = %5.1f %%  (classe la plus fréquente à cette heure : %.1f %%)" % (
                cr, kk, len(s), 100 * kk / len(s), 100 * fr / len(s)))
    hautes = [i for i in ids if rep[i][1] >= 70]
    basses = [i for i in ids if rep[i][1] < 70]
    for lab, s in (("confiance >= 70", hautes), ("confiance <  70", basses)):
        if s:
            kk = sum(rep[i][0] == cle[i]["classe"] for i in s)
            print("calibration %s : %d / %d = %.1f %% (confiance moyenne %.0f)" % (
                lab, kk, len(s), 100 * kk / len(s), np.mean([rep[i][1] for i in s])))


def score(dossier):
    cle = json.load(open(os.path.join(dossier, "cle.json"), encoding="utf-8"))
    rng = np.random.default_rng(GRAINE)
    modele = os.path.join(dossier, "..", "modele_scores.txt")
    if os.path.exists(modele):
        print("rappel modèle simple (point 1) : " + open(modele, encoding="utf-8").readline().strip())
    juges = {}
    for chemin in sorted(glob.glob(os.path.join(dossier, "reponses_*.txt"))):
        nom = os.path.basename(chemin)[len("reponses_"):-4]
        rep, mauv = lit(chemin, set(cle))
        print("juge %s : %d lignes valides, %d lignes mal formées ignorées" % (nom, len(rep), mauv))
        juges[nom] = rep
    if not juges:
        print("aucun fichier reponses_*.txt dans", dossier)
        return
    for nom, rep in juges.items():
        rapport("juge " + nom, rep, cle, rng)
    if len(juges) >= 2:
        vote = {}
        for i in cle:
            vs = [r[i] for r in juges.values() if i in r]
            if not vs:
                continue
            tot = Counter()
            for c, conf in vs:
                tot[c] += 1000 + conf          # majorité, puis somme des confiances pour départager
            c = tot.most_common(1)[0][0]
            vote[i] = (c, int(np.mean([conf for cc, conf in vs if cc == c])))
        rapport("vote majoritaire (%d juges)" % len(juges), vote, cle, rng)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("prepare", "score"):
        sys.exit(__doc__)
    (prepare if sys.argv[1] == "prepare" else score)(sys.argv[2])
