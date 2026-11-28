"""Banc GC : grille / martingale CONTRE le prix sur l'or, a coefficient multiplicateur variable (PRIORITES 21/11, piste 2,
point 1). Compte DEMO, aucun ordre. Donnees : or XAUUSD du courtier, M5 xau_m5_2025a + xau_m5_90k (06/2025 -> 11/2026,
jeu principal fin), H1 xau_h1_50k depuis le 01/08/2022 (4 ans), M1 xau_m1_90k (3 mois, controle de l'ordre intrabougie
et rejeu du controle BlockFIFO sur sa periode reelle 29/09 -> 05/10/2026).
REGLE (commune a toutes les variantes) :
- Sens = cloture contre l'EMA (2 jours ; 12 h pour le controle BlockFIFO) : au-dessus -> panier ACHETEUR, en dessous ->
  panier VENDEUR (on achete les replis d'une hausse, comme BlockFIFO). Un panier au plus par cote.
- Entree a la cloture de la bougie : heures de bt_or (M5 banc_bt_regulier.H_M5 ; H1 banc_jumeau.H_H1) [« H »], ou ces
  heures + reprise dans les 30 min apres la cloture COMPLETE (hors stop) d'un panier du meme cote [« HR »]. Pas
  d'entree si spread > 0,50 $, ni pendant la pause apres un stop global.
- Ajouts CONTRE le prix : un palier tous les « pas » contre la DERNIERE entree ; lot du palier k = m_k x lot de base,
  m_k = coef^k (coef 1,0 / 1,2 / 1,3 / 1,5 / 2,0) ou « cloche » BlockFIFO (1 ; 1,4 ; 1,8 ; 2,2 ; 2,6 ; 3,0 au palier 5,
  puis x 0,98 par palier). Pas fixe en $ (F1.5, F3, F6) ou en fraction de l'ATR jour 20 j de la veille (A0.1, A0.2,
  A0.4), fige a l'ouverture. Paliers max 5 / 10 / 20 / « inf » (= 223 paliers et 100 $ entre 1re entree et dernier
  ajout pour un pas en $, 1,5 ATR pour un pas en ATR).
- Sortie : T1 / T3 = tout le panier quand le gain total atteint 1 (3) pas x lot de base ; B5 = T1 tant que < 5 paliers,
  puis point mort (gain 0) ; F = FIFO par blocs BlockFIFO : le plus petit bloc des positions les plus anciennes (20 au
  plus) dont le net atteint 0,8 pas x lot de base (bloc < 6 positions) ou 0,533 pas x lots du bloc (>= 6 ; = 2,4 $ et
  80 $/lot pour le pas de 1,5 $ et 0,02 lot) est ferme (le « suivi du gain » des gros paniers n'est PAS simule).
- SECURITE : stop global du panier a X % du solde au depart du panier (X = 5, 10, 20) ; taille : lot de base tel que ce
  stop tombe un pas apres le dernier palier possible (pire stop = X %) ; coupure si fonds propres < 50 % de la marge
  (levier 1:500 ; ajout saute si la marge libre manque) ; filtre de tendance : E = sens EMA seul, ED = E + pas de
  panier si |prix - EMA 2 j| > 1 ATR, EV = E + pas de panier si ATR 20 j > 1,2 x ATR 100 j, EDV = les deux ; pause
  apres un stop global 24 h ou 72 h (les deux cotes).
- Couts : spread reel de la bougie (achat a prix + sp, vente a prix, vente touchee quand haut + sp touche) ; portage
  6 %/an du notionnel (/252 par jour de bourse) sur les positions tenues a la derniere bougie du jour (~23 h serveur).
- Ordre intrabougie, par panier : ouverture (saut traite comme un trou : execution au prix d'ouverture), puis extreme
  defavorable (ajouts, stop), puis extreme favorable (sorties), puis cloture [« def », convention des consignes].
  AJOUT AVANT L'EXECUTION COMPLETE (apres un essai de vitesse sur 4 variantes) : pour une grille, « defavorable
  d'abord » fait recolter a chaque bougie l'aller-retour bas -> haut (ajout au bas puis sortie au haut), ce qui est
  OPTIMISTE pour le gain. Toutes les mesures sont donc faites aussi avec « favorable d'abord » [« fav »] ; le verdict
  est le PIRE des deux ; l'ordre « prudent » (total median M5 des variantes le plus bas) sert au tableau et au rejeu
  exact ; le M1 dit lequel est le plus proche de la realite.
- Unites : 0,01 lot = 1 once, 1 $ de mouvement = 1 $ par once. Mode % : lots fractionnaires, rendements en % du compte
  (invariant d'echelle). Mode compte cent : lots arrondis a 0,01 once (min 0,01 ; lot de base < 0,005 once = lot min
  impossible = ruine), compte en euros (1,16 $/EUR).
GRILLE FIXEE D'AVANCE (rien ajoute ensuite), base = A0.2|x1.3|N10|T1|S10|ED|P24|HR (EMA 2 j) :
 G1 pas {F1.5,F3,F6,A0.1,A0.2,A0.4} x coef {1,0 ; 1,2 ; 1,3 ; 1,5 ; 2,0 ; cloche}                         36
 G2 paliers {5, 20, inf} x coef {1,0 ; 1,5 ; cloche} x pas {F3, A0.2}                                     18
 G3 sortie {T3, F, B5} x coef {1,0 ; 1,5 ; cloche} x pas {F1.5, A0.2}                                     18
 G4 stop {5,10,20} x filtre {E, ED, EV, EDV} x pause {24,72} (sauf la base)                                23
 G5 entree « H » sans reprise x pas {F1.5, A0.2} x coef {1,0 ; 1,5 ; cloche}                                6
 G6 « BlockFIFO securise » F1.5|cloche|inf|F|ED|P24|HR, stop {5,10,20}                                      3
 G7 CONTROLE « BlockFIFO v25 » : F1.5|cloche|inf (223 paliers, 100 $)|F|EMA 12 h, filtre E seul, pas de pause, HR,
    lot fixe 0,02 lot (2 onces) par 100 000 $ (proportionnel), stop -12 % du solde. Exclu du choix walk-forward.    1
 N = 105 variantes (doublons retires).
MESURES (M5 17 mois ET H1 4 ans) : gain par mois median (% compose), % de mois > 0, pire baisse de la courbe
JOURNALIERE marquee au prix, paniers/mois ; SAUTS (stop global ou coupure de marge) : nombre, 1 tous les N mois, taille
mediane / pire (% du solde au depart du panier), mois de gain median effaces par saut. RUINE compte cent 100 EUR et
500 EUR (ruine = sous 20 % de la mise, ou solde trop petit pour poser le lot minimum au risque prevu, seuil = 0,01 once
/ lot de base median par $) : (a) rejeu historique H1 depuis chaque debut de mois, 12 et 24 mois, sur les rendements
journaliers de la variante (mode %) ; pour les variantes du tableau, aussi un rejeu EXACT arrondi au lot cent ;
(b) Monte-Carlo bootstrap stationnaire des JOURS H1 (blocs moyens 20 j, 5 000 tirages, graine 2111), 12 et 24 mois.
Aussi « finir sous la mise ».
RIGUEUR : walk-forward M5 6 mois -> 1 mois glissant, H1 12 -> 3 mois glissant ; choix au meilleur gain / pire baisse
(rendements journaliers additifs en %) parmi les variantes sans saut > 25 % sur l'apprentissage (controle exclu) ;
compare a ne rien faire et a bt_or (banc_freq.simule_v H7/N1/std = banc_bt_regulier.simule) mis a la meme pire baisse
que la variante choisie sur l'apprentissage. Reality check de White (BR.white, jours x 105 variantes, % journaliers,
contre zero) -> p corrige par jeu.
VERDICT FIXE D'AVANCE (pour chaque ordre, puis le pire des deux) : TIENT = walk-forward hors echantillon > 0 ET > bt_or au meme risque sur M5 ET H1, p corrige
< 0,10 sur les deux jeux, ET ruine 24 mois Monte-Carlo 500 EUR < 5 % pour la variante la plus choisie par le
walk-forward H1 ; PRESQUE = du bon cote hors echantillon sur les deux jeux mais p >= 0,10 ou ruine >= 5 % ; sinon NE
TIENT PAS.
Tableau : controle, variante la plus choisie WF M5 et WF H1, meilleure gain/pire baisse H1 et M5, meilleur % de mois
positifs H1, meilleur total M5, BlockFIFO securise S10, martingale x2 (A0.2|x2|N10), base -> controles M1/M5 et
ordres dessus (selection faite dans l'ordre prudent).
RESULTAT (execution du 21/11/2026, 70 s, 4 processus, rien de reduit) : verdict NE TIENT PAS (le pire des deux ordres).
  L'ORDRE INTRABOUGIE DECIDE DE TOUT : total median des 105 variantes sur M5 +34 % (def) contre -34 % (fav) ; H1 +364 %
  contre -96 %. Variantes > 0 : M5 87 (def) / 10 (fav), H1 76 (def) / 1 (fav). Le M1 et le REEL tranchent pour « fav »
  sur les pas fins : BlockFIFO v25 rejoue 29/09 -> 05/10/2026 en M1 fav = -7 169 $ avec LE stop du 02/10 18:53 achat
  -12 651 $ (64 positions ; reel 18:57, -12 500 $, 60 positions ; reel total -6 269 $) ; en M1 def ou M5 def, pas de
  stop et +2 563 / +1 228 $. Sur 3 mois M1 : BlockFIFO M1 def -19,6 %, M1 fav -56 %, M5 def +28,8 %, M5 fav -66,8 %.
  Pour les pas >= 0,2 ATR, M1 et M5 donnent a peu pres la meme chose quel que soit l'ordre ; en H1 l'ecart reste enorme.
  fav : WF M5 -11,7 % (bt_or meme risque +0,9 %), WF H1 -14,7 % (bt_or +3,4 %), p corrige M5 0,94, H1 1,00.
  def : WF M5 +12,2 %, H1 +143 %, p 0,000 / 0,000 mais ruine MC 24 m 500 EUR = 100 % (la plus choisie en H1,
  F1.5|xcl|Ninf|F|S5, demande 1 200 EUR pour poser le lot minimum) -> au mieux PRESQUE, et ce resultat vient du biais.
  % de mois positifs eleve meme quand la variante perd (fav H1 : A0.2|x2|N10 90 % de mois > 0, total -26 %).
  Sauts (fav, H1 4 ans) : de 1 tous les 10 mois (x2, sans lot min possible sous 1 276 EUR) a 1 tous les 0,3 mois ;
  chaque saut efface 6 a 22 mois de gain median quand celui-ci est > 0. Les martingales x1,5-x2 a 10-20 paliers ne sont
  pas posables sur 100-500 EUR au risque prevu (solde minimal 1 300 a 12 400 EUR ; x1,5 sans limite : 1,5 M EUR).
Ecrit donnees/grille_coef.csv. Usage : python3 banc_grille_coef.py"""
import os, time, warnings
from multiprocessing import Pool
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR
import banc_jumeau as BJ
import banc_freq as BF

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
EURUSD = 1.16
B_INIT = 10000.0
SWAP_J = 0.06 / 252


# ------------------------------------------------------------------ grille fixee
def V(pas="A0.2", coef=1.3, lev=10, sortie="T1", stop=10, filtre="ED", pause=24, ent="HR", ema="2j", lot0=None):
    return dict(pas=pas, coef=coef, lev=lev, sortie=sortie, stop=stop, filtre=filtre, pause=pause, ent=ent, ema=ema, lot0=lot0)


def nom(v):
    if v["lot0"]:
        return "CONTROLE BlockFIFO v25"
    c = "cl" if v["coef"] == "cl" else "%g" % v["coef"]
    return "%s|x%s|N%s|%s|S%d|%s|P%d|%s" % (v["pas"], c, v["lev"] or "inf", v["sortie"], v["stop"], v["filtre"], v["pause"], v["ent"])


COEFS = (1.0, 1.2, 1.3, 1.5, 2.0, "cl")
VAR = []
for p in ("F1.5", "F3", "F6", "A0.1", "A0.2", "A0.4"):
    for c in COEFS:
        VAR.append(V(pas=p, coef=c))
for lv in (5, 20, 0):
    for c in (1.0, 1.5, "cl"):
        for p in ("F3", "A0.2"):
            VAR.append(V(pas=p, coef=c, lev=lv))
for so in ("T3", "F", "B5"):
    for c in (1.0, 1.5, "cl"):
        for p in ("F1.5", "A0.2"):
            VAR.append(V(pas=p, coef=c, sortie=so))
for st in (5, 10, 20):
    for f in ("E", "ED", "EV", "EDV"):
        for pa in (24, 72):
            VAR.append(V(stop=st, filtre=f, pause=pa))
for p in ("F1.5", "A0.2"):
    for c in (1.0, 1.5, "cl"):
        VAR.append(V(pas=p, coef=c, ent="H"))
for st in (5, 10, 20):
    VAR.append(V(pas="F1.5", coef="cl", lev=0, sortie="F", stop=st))
VAR.append(V(pas="F1.5", coef="cl", lev=0, sortie="F", stop=12, filtre="E", pause=0, ent="HR", ema="12h", lot0=2.0 / 1e5))
_vu, _V = set(), []
for v in VAR:
    if nom(v) not in _vu:
        _vu.add(nom(v)); _V.append(v)
VAR = _V
NOMV = [nom(v) for v in VAR]
NV = len(VAR)
CTRL = NV - 1


def mults(coef, n=224):
    if coef == "cl":
        return [1 + 0.4 * k if k <= 5 else 3.0 * 0.98 ** (k - 5) for k in range(n)]
    return [coef ** k for k in range(n)]


# ------------------------------------------------------------------ donnees preparees
DATA, PREP = {}, {}


def prepare(jeu):
    if jeu in PREP:
        return PREP[jeu]
    d, barsec, heures = DATA[jeu]
    t = d.heure.values.astype(np.int64)
    c = d.cloture.values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": d.haut.values, "l": d.bas.values, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    a20 = tr.rolling(20).mean().shift(1).reindex(jour).values
    a100 = tr.rolling(100, min_periods=20).mean().shift(1).reindex(jour).values
    pb = 86400 // barsec
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    P = dict(t=t.tolist(), o=d.ouverture.values.tolist(), h=d.haut.values.tolist(), l=d.bas.values.tolist(), c=c.tolist(),
             sp=d.sp.values.tolist(), jour=jour.tolist(), fin=np.r_[jour[1:] != jour[:-1], True].tolist(),
             a20=np.nan_to_num(a20, nan=-1).tolist(), a100=np.nan_to_num(a100, nan=-1).tolist(),
             ent=[(a, b) in heures for a, b in zip(hh, mm)], barsec=barsec,
             ema={"2j": d.cloture.ewm(span=2 * pb, min_periods=2 * pb).mean().fillna(-1).values.tolist(),
                  "12h": d.cloture.ewm(span=pb // 2, min_periods=pb // 2).mean().fillna(-1).values.tolist()})
    PREP[jeu] = P
    return P


# ------------------------------------------------------------------ simulateur
def simule(jeu, v, cap=None, pas_lot=0.01, opt=False, i0=0, i1=None, te0=None, te1=None, log=False):
    """Une variante sur un jeu. cap=None : mode % (lots fractionnaires) ; sinon solde de depart en $ et lots arrondis
    a pas_lot onces. Entrees seulement entre te0 et te1 (heure serveur, s). Rend un dict."""
    D = prepare(jeu)
    T, O, H, L, C, SP, JO, FIN = D["t"], D["o"], D["h"], D["l"], D["c"], D["sp"], D["jour"], D["fin"]
    A20, A100, ENT, EMA = D["a20"], D["a100"], D["ent"], D["ema"][v["ema"]]
    E2 = D["ema"]["2j"]
    n = len(C) if i1 is None else i1
    rep_bars = 1800 // D["barsec"]
    M = mults(v["coef"])
    X = v["stop"] / 100.0
    fixe = v["pas"][0] == "F"
    kp = float(v["pas"][1:])
    so = v["sortie"]
    acct = B_INIT if cap is None else float(cap)
    acct0 = acct
    ouvert = {1: None, -1: None}
    der_ferm = {1: -10 ** 9, -1: -10 ** 9}
    pause_fin = -1
    PAN, JR, EQ, F_L0 = [], [], [], []
    npos = [0, 0]
    infaisable = False
    jlog = {}

    def ferme_bloc(p, k, x, sp_):
        nonlocal acct
        s = p["s"]; ofs = sp_ if s < 0 else 0.0
        r = 0.0
        for q in range(k):
            ri = s * (x + ofs - p["E"][q]) * p["L"][q]
            r += ri
            npos[0] += 1
            if ri > 0:
                npos[1] += 1
            if log:
                dj = jlog.setdefault(T[i] // 86400, [0, 0, 0.0]); dj[0] += 1; dj[1] += ri > 0; dj[2] += ri
        del p["L"][:k]; del p["E"][:k]
        p["SL"] = sum(p["L"]); p["SLE"] = sum(a * b for a, b in zip(p["L"], p["E"]))
        p["real"] += r; acct += r
        return r

    def fin_panier(p, typ):
        PAN.append((p["t0"], T[i], p["s"], p["nmax"], p["real"], p["real"] / p["B0"], typ, p["B0"]))

    def jambe(p, cur, b, sp_, saut):
        """Deplacement monotone cur -> b (prix bid). Rend None ou le type de fin ('S','M','T','F')."""
        nonlocal acct
        s = p["s"]; ofs = sp_ if s < 0 else 0.0
        if s * (b - cur) < 0:                                   # defavorable : ajouts et stop
            while True:
                SL, SLE = p["SL"], p["SLE"]
                pst = (SLE + s * (-p["K"] - p["real"])) / SL - ofs
                peut = p["n"] < p["nlev"]
                q = p["last"] - s * p["pas"]
                if peut and p["dmax"] and s * (p["first"] - q) > p["dmax"] + 1e-9:
                    peut = False
                if saut:
                    if s * (b - pst) <= 0:
                        ferme_bloc(p, len(p["L"]), b, sp_); return "S"
                    if peut and s * (b - q) <= 0:
                        ajoute(p, b, sp_)
                        if p["real"] + s * (p["SL"] * (b + ofs) - p["SLE"]) <= -p["K"]:
                            ferme_bloc(p, len(p["L"]), b, sp_); return "S"
                        if marge(p, b, sp_):
                            return "M"
                    return None
                if peut and s * (q - pst) >= 0 and s * (q - b) >= 0:
                    ajoute(p, q, sp_)
                    if marge(p, q, sp_):
                        return "M"
                    cur = q
                    continue
                if s * (pst - b) >= 0:
                    x = pst if s * (pst - cur) <= 0 else cur
                    ferme_bloc(p, len(p["L"]), x, sp_); return "S"
                return None
        else:                                                   # favorable : sorties
            while True:
                SL, SLE = p["SL"], p["SLE"]
                if so == "F":
                    best, kb = None, 0
                    cl = cle = 0.0
                    for k in range(min(20, len(p["L"]))):
                        cl += p["L"][k]; cle += p["L"][k] * p["E"][k]
                        thr = 0.8 * p["pas"] * p["L0"] if k + 1 < 6 else 0.5333 * p["pas"] * cl
                        pk = (cle + s * thr) / cl - ofs
                        if saut:
                            if s * (b - pk) >= 0:
                                best, kb = b, k + 1; break
                        elif best is None or s * (pk - best) < -1e-12:
                            best, kb = pk, k + 1
                    if best is None or s * (best - b) > 0:
                        return None
                    x = best if s * (best - cur) >= 0 else cur
                    ferme_bloc(p, kb, x, sp_)
                    if not p["L"]:
                        return "F"
                    cur = x
                    continue
                tgt = p["tgt"] if not (so == "B5" and p["n"] >= 5) else 0.0
                pt = (SLE + s * (tgt - p["real"])) / SL - ofs
                if s * (b - pt) >= 0:
                    x = b if saut else (pt if s * (pt - cur) >= 0 else cur)
                    ferme_bloc(p, len(p["L"]), x, sp_); return "T"
                return None

    def lot_niveau(p, k):
        x = M[k] * p["L0"]
        if cap is not None:
            x = max(pas_lot, round(x / pas_lot) * pas_lot)
        return x

    def ajoute(p, q, sp_):
        s = p["s"]
        lot = lot_niveau(p, p["n"])
        e = q + (sp_ if s > 0 else 0.0)
        eq = acct + s * (p["SL"] * (q + (sp_ if s < 0 else 0.0)) - p["SLE"])
        if eq < (p["SL"] + lot) * q / 500.0:                    # marge libre insuffisante : palier saute
            p["last"] = q; p["n"] += 1
            return
        p["L"].append(lot); p["E"].append(e); p["SL"] += lot; p["SLE"] += lot * e
        p["last"] = q; p["n"] += 1; p["nmax"] = max(p["nmax"], len(p["L"]))

    def marge(p, x, sp_):
        s = p["s"]
        eq = acct + s * (p["SL"] * (x + (sp_ if s < 0 else 0.0)) - p["SLE"])
        if eq < 0.5 * p["SL"] * x / 500.0:
            ferme_bloc(p, len(p["L"]), x, sp_)
            return True
        return False

    i = i0
    cprev = C[i0]
    for i in range(i0, n):
        sp_ = SP[i]
        for s in (1, -1):
            p = ouvert[s]
            if p is None:
                continue
            if (s > 0) != opt:
                pts = (O[i], L[i], H[i], C[i])
            else:
                pts = (O[i], H[i], L[i], C[i])
            cur = cprev
            res = None
            for kk, b in enumerate(pts):
                if b != cur:
                    res = jambe(p, cur, b, sp_, kk == 0)
                    if res:
                        break
                cur = b
            if res:
                fin_panier(p, res); ouvert[s] = None
                if res in ("S", "M"):
                    pause_fin = T[i] + v["pause"] * 3600
                else:
                    der_ferm[s] = i
        if FIN[i]:
            for s in (1, -1):
                p = ouvert[s]
                if p is not None:
                    cout = SWAP_J * p["SL"] * C[i]
                    p["real"] -= cout; acct -= cout
        # entree
        a = A20[i]; e = EMA[i]
        if a > 0 and e > 0 and T[i] >= pause_fin and sp_ <= 0.5 and (te0 is None or T[i] >= te0) and (te1 is None or T[i] < te1):
            s = 1 if C[i] > e else -1
            ok = ouvert[s] is None and (ENT[i] or (v["ent"] == "HR" and i - der_ferm[s] <= rep_bars))
            f = v["filtre"]
            if ok and "D" in f and abs(C[i] - E2[i]) > a:
                ok = False
            if ok and "V" in f and A100[i] > 0 and a > 1.2 * A100[i]:
                ok = False
            if ok:
                pas = kp if fixe else kp * a
                if v["lev"]:
                    nlev, dmax = v["lev"], 0.0
                else:
                    dmax = 100.0 if fixe else 1.5 * a
                    nlev = min(223, int(dmax / pas + 1e-9) + 1)
                if v["lot0"]:
                    L0 = v["lot0"] * acct
                else:
                    lu = sum(M[k] * ((nlev - k) * pas + sp_) for k in range(nlev))
                    L0 = X * acct / lu
                F_L0.append(L0 / acct)
                if cap is not None:
                    if L0 < 0.5 * pas_lot:
                        infaisable = True
                        break
                    L0 = max(pas_lot, round(L0 / pas_lot) * pas_lot)
                p = dict(s=s, L=[], E=[], SL=0.0, SLE=0.0, real=0.0, last=C[i] + s * pas, first=C[i], n=0, nlev=nlev,
                         dmax=dmax, pas=pas, L0=L0, K=X * acct, B0=acct, t0=T[i], nmax=0, tgt=(3 if so == "T3" else 1) * pas * L0)
                ajoute(p, C[i], sp_)
                if p["L"]:
                    ouvert[s] = p
        if FIN[i]:
            lat = 0.0
            for s in (1, -1):
                p = ouvert[s]
                if p is not None:
                    lat += s * (p["SL"] * (C[i] + (sp_ if s < 0 else 0.0)) - p["SLE"])
            JR.append(JO[i]); EQ.append(acct + lat)
        cprev = C[i]
    # fin de simulation : positions encore ouvertes marquees a la derniere cloture
    lat = 0.0
    for s in (1, -1):
        p = ouvert[s]
        if p is not None:
            lat += s * (p["SL"] * (C[i] + (SP[i] if s < 0 else 0.0)) - p["SLE"])
    return dict(jours=JR, eq=EQ, pan=PAN, npos=npos, inf=infaisable, f=F_L0, acct=acct, lat=lat, jlog=jlog,
                ouverts=sum(len(p["L"]) for p in ouvert.values() if p is not None))


def tache(arg):
    jeu, k = arg[0], arg[1]
    kw = arg[2] if len(arg) > 2 else {}
    r = simule(jeu, VAR[k], **kw)
    if not kw.get("log"):
        r.pop("jlog")
    return r


# ------------------------------------------------------------------ mesures
def serie(r):
    E = pd.Series(r["eq"], pd.to_datetime(np.array(r["jours"]) * 86400, unit="s"))
    E = E.clip(lower=1e-9 * B_INIT)
    x = (E / E.shift(1).fillna(B_INIT) - 1).clip(lower=-0.999)
    return x


def mesures(x, pan, nm):
    E = (1 + x).cumprod()
    mo = (1 + x).groupby(x.index.to_period("M")).prod() - 1
    dd = (E / np.maximum(E.cummax(), 1.0) - 1).min()
    P = pd.DataFrame(pan, columns=["t0", "t1", "s", "nmax", "res", "pct", "typ", "B0"])
    S = P[P.typ.isin(["S", "M"])]
    gm = mo.median() * 100
    taille = -S.pct * 100
    return dict(gain_mois_med=gm, pct_mois_pos=100 * (mo > 0).mean(), pire_mois=mo.min() * 100, total_pct=(E.iloc[-1] - 1) * 100,
                pire_baisse=dd * 100, paniers_mois=len(P) / nm, pos_max_med=P.nmax.median() if len(P) else 0,
                sauts=len(S), sauts_marge=int((S.typ == "M").sum()), un_saut_tous_mois=nm / len(S) if len(S) else np.inf,
                saut_med=taille.median() if len(S) else 0.0, saut_pire=taille.max() if len(S) else 0.0,
                mois_effaces=(taille.median() / gm) if len(S) and gm > 0 else np.inf, mois=nm)


def boot_idx(n, B, L, b, seed):
    g = np.random.default_rng(seed)
    out = np.empty((B, L), int)
    for k in range(B):
        neuf = g.random(L) < 1 / b; neuf[0] = True
        bl = np.cumsum(neuf) - 1; deb = np.flatnonzero(neuf)
        out[k] = (g.integers(n, size=len(deb))[bl] + np.arange(L) - deb[bl]) % n
    return out


def ruine(x, fmed, IDX):
    """x : rendements journaliers H1 (mode %). Rend rejeu mensuel et Monte-Carlo, 12/24 mois, 100/500 EUR."""
    out = {}
    bmin = 0.01 / fmed if fmed > 0 else np.inf
    mois = x.index.to_period("M"); MO = mois.unique()
    v = x.values
    for cap in (100, 500):
        thr = max(0.2, bmin / (cap * EURUSD))
        for h, L in ((12, 252), (24, 504)):
            ru, so = [], []
            for a in range(len(MO) - h + 1):
                w = v[(mois >= MO[a]) & (mois <= MO[a + h - 1])]
                E = np.cumprod(1 + w)
                ru.append(thr >= 1 or E.min() < thr); so.append(E[-1] < 1)
            out["rejeu_ruine_%d_%dm" % (cap, h)] = 100 * np.mean(ru)
            out["rejeu_sous_mise_%d_%dm" % (cap, h)] = 100 * np.mean(so)
            E = np.cumprod(1 + v[IDX[:, :L]], 1)
            out["mc_ruine_%d_%dm" % (cap, h)] = 100.0 if thr >= 1 else 100 * (E.min(1) < thr).mean()
            out["mc_sous_mise_%d_%dm" % (cap, h)] = 100 * (E[:, -1] < 1).mean()
    out["solde_min_eur"] = bmin / EURUSD
    return out


def rejeu_exact(arg):
    """Rejeu arrondi au lot cent (H1) depuis un debut de mois : ruine / sous la mise."""
    k, i0, i1, cap, opt = arg
    r = simule("or H1", VAR[k], cap=cap * EURUSD, pas_lot=0.01, i0=i0, i1=i1, opt=opt)
    if r["inf"]:
        return True, True
    E = np.array(r["eq"]) / (cap * EURUSD)
    return bool(len(E) and E.min() < 0.2), bool(len(E) == 0 or E[-1] < 1)


def bt_or_jour(jeu, d, m5, debut, idx):
    _, EQ = BF.simule_v(d, m5, "H7", 1, "std", debut)
    x = EQ.diff(); x.iloc[0] = EQ.iloc[0]
    return x.reindex(idx).fillna(0.0)


def creux_add(x):
    cs = np.cumsum(x); return (cs - np.maximum.accumulate(np.maximum(cs, 0))).min()


def walk_forward(X, PANS, bt, L_app, L_test):
    mois = X.index.to_period("M"); MO = mois.unique()
    oos, oosb, ch = [], [], []
    for i0 in range(L_app, len(MO), L_test):
        app = (mois >= MO[i0 - L_app]) & (mois <= MO[i0 - 1])
        te = (mois >= MO[i0]) & (mois <= MO[min(i0 + L_test, len(MO)) - 1])
        d0, d1 = X.index[app][0].timestamp(), X.index[app][-1].timestamp() + 86400
        best, kb = -np.inf, None
        for k in range(NV):
            if k == CTRL:
                continue
            P = PANS[k]
            if any(p[6] in "SM" and d0 <= p[1] < d1 and -p[5] > 0.25 for p in P):
                continue
            xa = X[k].values[app]; cr = creux_add(xa)
            rap = xa.sum() / -cr if cr < 0 else (np.inf if xa.sum() > 0 else 0.0)
            if rap > best:
                best, kb = rap, k
        if kb is None:
            oos.append(X[0][te] * 0); oosb.append(bt[te] * 0); ch.append("rien"); continue
        ca, cb = creux_add(X[kb].values[app]), creux_add(bt.values[app])
        fa = ca / cb if cb < 0 and ca < 0 else 0.0
        oos.append(X[kb][te]); oosb.append(bt[te] * fa); ch.append(NOMV[kb])
    o, ob = pd.concat(oos), pd.concat(oosb)
    return o, ob, pd.Series(ch).value_counts()


# ------------------------------------------------------------------ programme
def campagne(ordre, d5, dh):
    """Toutes les mesures pour un ordre intrabougie (def = defavorable d'abord ; fav = favorable d'abord)."""
    opt = ordre == "fav"
    with Pool(4) as pool:
        out = pool.map(tache, [(j, k, dict(opt=opt)) for j in ("or M5", "or H1") for k in range(NV)], chunksize=1)
    RES = {"or M5": out[:NV], "or H1": out[NV:]}
    LIG, XS, PANS = [], {}, {}
    for jeu, m5 in (("or M5", True), ("or H1", False)):
        R = RES[jeu]
        X = pd.DataFrame({k: serie(R[k]) for k in range(NV)}).fillna(0.0)
        X = X.iloc[25:] if m5 else X.iloc[22:]          # rechauffage ATR 20 j / EMA
        XS[jeu] = X; PANS[jeu] = [R[k]["pan"] for k in range(NV)]
        nm = len(X.index.to_period("M").unique())
        IDX = boot_idx(len(X), 5000, 504, 20, 2111)
        for k in range(NV):
            r = R[k]
            fmed = float(np.median(r["f"])) if r["f"] else 0.0
            lig = dict(ordre=ordre, jeu=jeu, variante=NOMV[k],
                       **{kk: VAR[k][kk] for kk in ("pas", "coef", "lev", "sortie", "stop", "filtre", "pause", "ent", "ema")},
                       **mesures(X[k], r["pan"], nm), positions=r["npos"][0],
                       pct_pos_gagnantes=100 * r["npos"][1] / max(1, r["npos"][0]), lot_base_oz_par_k=fmed * 1000)
            lig.update(ruine(X[k], fmed, IDX))
            LIG.append(lig)
    T = pd.DataFrame(LIG)
    SYN = {}
    for jeu, d, m5, debut, la, lt in (("or M5", d5, True, 600, 6, 1), ("or H1", dh, False, 60, 12, 3)):
        X = XS[jeu] * 100
        kb, pc = BR.white(X.values)
        bt = bt_or_jour(jeu, d, m5, debut, X.index)
        o, ob, fq = walk_forward(X, PANS[jeu], bt, la, lt)
        mo = o.groupby(o.index.to_period("M")).sum()
        SYN[jeu] = dict(p=pc, best=NOMV[kb], oos=o.sum(), bt=ob.sum(), cro=creux_add(o.values), crb=creux_add(ob.values), fq=fq,
                        mpos=100 * (mo > 0).mean(), nm=len(mo), ok=o.sum() > 0 and o.sum() > ob.sum(), dob=(o.index[0].date(), o.index[-1].date()))
        T.loc[T.jeu == jeu, "p_white_corrige"] = pc
        print("\n=== ordre %s, %s : %s -> %s, %d jours" % (ordre, jeu, X.index[0].date(), X.index[-1].date(), len(X)))
        print("Reality check de White (N = %d, contre zero) : meilleur %s, p corrige = %.3f" % (NV, NOMV[kb], pc))
        print("Walk-forward %d -> %d mois (%s -> %s, %d mois de test) : hors echantillon %+.1f %% (creux %+.1f %%, mois > 0 %.0f %%) ; "
              "bt_or meme risque %+.1f %% (creux %+.1f %%) ; ne rien faire 0" % (la, lt, *SYN[jeu]["dob"], len(mo), o.sum(), SYN[jeu]["cro"],
                                                                                SYN[jeu]["mpos"], ob.sum(), SYN[jeu]["crb"]))
        print("  choix : " + " ; ".join("%s %d" % (a, b) for a, b in fq.head(6).items()))
    kH = SYN["or H1"]["fq"].index[0]
    ru = T[(T.jeu == "or H1") & (T.variante == kH)].mc_ruine_500_24m.iloc[0] if kH in NOMV else 100.0
    deux = SYN["or M5"]["ok"] and SYN["or H1"]["ok"]
    v = "TIENT" if deux and SYN["or M5"]["p"] < 0.10 and SYN["or H1"]["p"] < 0.10 and ru < 5 else ("PRESQUE" if deux else "NE TIENT PAS")
    SYN["verdict"], SYN["ruine_kH"], SYN["kH"] = v, ru, kH
    W = pd.DataFrame([dict(ordre=ordre, jeu=j, variante="WF choisi", total_pct=SYN[j]["oos"], pire_baisse=SYN[j]["cro"], pct_mois_pos=SYN[j]["mpos"],
                           p_white_corrige=SYN[j]["p"], choix=" ; ".join("%s %d" % (a, b) for a, b in SYN[j]["fq"].items())) for j in ("or M5", "or H1")] +
                     [dict(ordre=ordre, jeu=j, variante="WF bt_or meme risque", total_pct=SYN[j]["bt"], pire_baisse=SYN[j]["crb"]) for j in ("or M5", "or H1")])
    return T, W, SYN


def affiche(T, sel, ordre):
    TH = T[(T.jeu == "or H1") & (T.ordre == ordre)].set_index("variante")
    T5 = T[(T.jeu == "or M5") & (T.ordre == ordre)].set_index("variante")
    print("\n=== Variantes du tableau, ordre %s (M5 17 mois / H1 4 ans) ; sauts = stop global ou marge ; ruine sur H1" % ordre)
    for z in sel:
        for jeu, Z in (("M5", T5), ("H1", TH)):
            r = Z.loc[z]
            print("%-32s %s gain/mois med %+6.2f %%  mois>0 %3.0f %%  pire baisse %6.1f %%  total %+9.4g %%  pan/mois %5.1f  sauts %3d "
                  "(1/%4.1f mois, med %4.1f %%, pire %5.1f %%, efface %4.1f mois)" % (
                      z, jeu, r.gain_mois_med, r.pct_mois_pos, r.pire_baisse, r.total_pct, r.paniers_mois, r.sauts, r.un_saut_tous_mois,
                      r.saut_med, r.saut_pire, r.mois_effaces))
        r = TH.loc[z]
        print("    ruine H1 rejeu 12/24 m : 100 EUR %.0f/%.0f %%, 500 EUR %.0f/%.0f %% ; MC 12/24 m : 100 EUR %.1f/%.1f %%, 500 EUR %.1f/%.1f %% ; "
              "sous la mise MC 24 m 500 EUR %.0f %% ; solde min pour le lot min %.0f EUR" % (
                  r.rejeu_ruine_100_12m, r.rejeu_ruine_100_24m, r.rejeu_ruine_500_12m, r.rejeu_ruine_500_24m, r.mc_ruine_100_12m,
                  r.mc_ruine_100_24m, r.mc_ruine_500_12m, r.mc_ruine_500_24m, r.mc_sous_mise_500_24m, r.solde_min_eur))


if __name__ == "__main__":
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d5 = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    dh = BR.charge("xau_h1_50k")
    dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    d1 = BR.charge("xau_m1_90k")
    DATA["or M5"] = (d5, 300, BR.H_M5); DATA["or H1"] = (dh, 3600, BJ.H_H1); DATA["or M1"] = (d1, 60, BR.H_M5)
    print("Grille fixee : N = %d variantes (controle = %s). 4 processus. Deux ordres intrabougie." % (NV, NOMV[CTRL]))
    TT, WW, SY = [], [], {}
    for ordre in ("def", "fav"):
        T, W, S = campagne(ordre, d5, dh)
        TT.append(T); WW.append(W); SY[ordre] = S
        print("Ordre %s : verdict %s (%.0f s)" % (ordre, S["verdict"], time.time() - T00))
    T = pd.concat(TT, ignore_index=True)
    # ordre prudent = celui dont le total median M5 des variantes est le plus bas
    med = {o: T[(T.ordre == o) & (T.jeu == "or M5")].total_pct.median() for o in SY}
    pru = min(med, key=med.get)
    print("\nTotal median M5 des %d variantes : def %+.1f %%, fav %+.1f %% -> ordre prudent = %s" % (NV, med["def"], med["fav"], pru))
    TP = T[T.ordre == pru]
    TH, T5 = TP[TP.jeu == "or H1"].set_index("variante"), TP[TP.jeu == "or M5"].set_index("variante")
    rap = lambda Z: Z.total_pct / -Z.pire_baisse.replace(0, np.nan)
    sel = [NOMV[CTRL]]
    for z in (SY[pru]["or M5"]["fq"].index[0], SY[pru]["or H1"]["fq"].index[0], rap(TH.drop(NOMV[CTRL])).idxmax(), rap(T5.drop(NOMV[CTRL])).idxmax(),
              TH.drop(NOMV[CTRL]).pct_mois_pos.idxmax(), T5.drop(NOMV[CTRL]).total_pct.idxmax(), "F1.5|xcl|Ninf|F|S10|ED|P24|HR",
              "A0.2|x2|N10|T1|S10|ED|P24|HR", "A0.2|x1.3|N10|T1|S10|ED|P24|HR"):
        if z in NOMV and z not in sel:
            sel.append(z)
    for o in ("def", "fav"):
        affiche(T, sel, o)
    # rejeu exact arrondi au lot cent (H1), variantes du tableau, ordre prudent
    dT = np.array(prepare("or H1")["t"])
    mo_h = pd.to_datetime(dT, unit="s").to_period("M"); MOH = mo_h.unique()
    taches = []
    for z in sel:
        k = NOMV.index(z)
        for h in (12, 24):
            for a in range(1, len(MOH) - h + 1):
                i0 = int(np.argmax(mo_h == MOH[a])); i1 = int(np.flatnonzero(mo_h <= MOH[a + h - 1])[-1]) + 1
                for cap in (100, 500):
                    taches.append((k, i0, i1, cap, h))
    with Pool(4) as pool:
        ex = pool.map(rejeu_exact, [(k, i0, i1, cap, pru == "fav") for k, i0, i1, cap, h in taches], chunksize=4)
    EX = pd.DataFrame([dict(variante=NOMV[t[0]], cap=t[3], h=t[4], ruine=e[0], sous=e[1]) for t, e in zip(taches, ex)])
    print("\nRejeu EXACT arrondi au lot cent (H1, ordre %s, depart a chaque debut de mois, ATR/EMA deja calcules) :" % pru)
    for z in sel:
        g = EX[EX.variante == z]
        print("  %-32s " % z + " ; ".join("%d EUR %d m ruine %.0f %% sous mise %.0f %%" % (c, h, 100 * g[(g.cap == c) & (g.h == h)].ruine.mean(),
                                                                                       100 * g[(g.cap == c) & (g.h == h)].sous.mean())
                                           for c in (100, 500) for h in (12, 24)))
        for c in (100, 500):
            for h in (12, 24):
                T.loc[(T.ordre == pru) & (T.jeu == "or H1") & (T.variante == z), "exact_ruine_%d_%dm" % (c, h)] = \
                    100 * EX[(EX.variante == z) & (EX.cap == c) & (EX.h == h)].ruine.mean()
    # controles : M1 contre M5, deux ordres (3 mois)
    t1m = prepare("or M1")["t"]
    ta, tb = t1m[0] + 25 * 86400, t1m[-1]
    print("\nControle de l'ordre intrabougie, entrees %s -> %s, solde 10 000 $ :" % (pd.to_datetime(ta, unit="s").date(), pd.to_datetime(tb, unit="s").date()))
    i5 = int(np.searchsorted(prepare("or M5")["t"], tb, "right"))
    combos = [("or M1", False), ("or M1", True), ("or M5", False), ("or M5", True)]
    with Pool(4) as pool:
        cm = pool.map(tache, [(j, NOMV.index(z), dict(te0=ta, te1=tb, opt=o_, i1=(i5 if j == "or M5" else None))) for z in sel for j, o_ in combos])
    f = lambda r: (r["acct"] + r["lat"] - B_INIT) / B_INIT * 100
    ns = lambda r: sum(p[6] in "SM" for p in r["pan"])
    for q, z in enumerate(sel):
        print("  %-32s " % z + " | ".join("%s %s %+7.1f %% (%d pan., %d sauts)" % (j[3:], "fav" if o_ else "def", f(r), len(r["pan"]), ns(r))
                                          for (j, o_), r in zip(combos, cm[4 * q: 4 * q + 4])))
    # controle BlockFIFO v25 contre le reel (29/09 -> 05/10/2026)
    t0r, t1r = pd.Timestamp("2026-09-29 18:40").timestamp(), pd.Timestamp("2026-10-05 08:31").timestamp()
    hreel = pd.read_csv(os.path.join(ICI, "mt5", "autres", "historique.csv.gz"))
    hreel = hreel[hreel.magique == 701100].copy()
    hreel["j"] = pd.to_datetime(hreel.fermeture_heure_serveur, unit="s").dt.date
    hreel["net"] = hreel.resultat + hreel.commission + hreel.swap
    reel = hreel.groupby("j").agg(n=("net", "size"), g=("net", lambda x: (x > 0).sum()), s=("net", "sum"))
    print("\nBlockFIFO v25 rejoue sur sa periode reelle (%s -> %s, solde 100 000 $, lot 0,02 cloche arrondi a 0,01 lot) ; reel : %d positions, "
          "%.1f %% gagnantes, %+.0f $" % (pd.to_datetime(t0r, unit="s"), pd.to_datetime(t1r, unit="s"), len(hreel), 100 * (hreel.net > 0).mean(), hreel.net.sum()))
    for j in ("or M1", "or M5"):
        for o_ in (False, True):
            Tt = prepare(j)["t"]; i1 = int(np.searchsorted(Tt, t1r, "right"))
            r = simule(j, VAR[CTRL], cap=1e5, pas_lot=1.0, te0=t0r, te1=t1r, i1=i1, log=True, opt=o_)
            P = pd.DataFrame(r["pan"], columns=["t0", "t1", "s", "nmax", "res", "pct", "typ", "B0"])
            print("  %s %s : %d positions fermees, %.1f %% gagnantes, %d paniers, resultat %+.0f $ (latent fin %+.0f $, %d pos. ouvertes) ; "
                  "achats %+.0f $, ventes %+.0f $ ; stops : %s" % (
                      j, "fav" if o_ else "def", r["npos"][0], 100 * r["npos"][1] / max(1, r["npos"][0]), len(P), r["acct"] + r["lat"] - 1e5, r["lat"],
                      r["ouverts"], P[P.s > 0].res.sum(), P[P.s < 0].res.sum(),
                      ", ".join("%s %s %+.0f $ (%d pos.)" % (pd.to_datetime(a, unit="s"), "achat" if s > 0 else "vente", g, nn)
                                for a, s, g, nn in P[P.typ.isin(["S", "M"])][["t1", "s", "res", "nmax"]].values) or "aucun"))
            for jj, (nn, gg, ss) in sorted(r["jlog"].items()):
                dd = pd.to_datetime(jj * 86400, unit="s").date()
                rr = reel.loc[dd] if dd in reel.index else None
                print("    %s simule %4d pos. %5.1f %% gagn. %+8.0f $ | reel %s" % (dd, nn, 100 * gg / nn, ss,
                      "%4d pos. %5.1f %% gagn. %+8.0f $" % (rr.n, 100 * rr.g / rr.n, rr.s) if rr is not None else "-"))
    # verdict : le pire des deux ordres
    rang = {"TIENT": 2, "PRESQUE": 1, "NE TIENT PAS": 0}
    v = min((SY[o]["verdict"] for o in SY), key=rang.get)
    for o in ("def", "fav"):
        S = SY[o]
        print("Ordre %s : %s. WF M5 %+.1f %% (bt_or meme risque %+.1f %%), WF H1 %+.1f %% (bt_or %+.1f %%), p corrige M5 %.3f H1 %.3f, N = %d, "
              "ruine MC 24 m 500 EUR de la plus choisie en H1 (%s) = %.1f %%" % (o, S["verdict"], S["or M5"]["oos"], S["or M5"]["bt"], S["or H1"]["oos"],
                                                                                S["or H1"]["bt"], S["or M5"]["p"], S["or H1"]["p"], NV, S["kH"], S["ruine_kH"]))
    print("=== Verdict (fixe d'avance, le pire des deux ordres) : %s" % v)
    pd.concat([T] + WW, ignore_index=True).round(4).to_csv(os.path.join(ICI, "donnees", "grille_coef.csv"), index=False)
    print("Ecrit donnees/grille_coef.csv (%d lignes). Duree totale %.0f s." % (len(T) + sum(len(w) for w in WW), time.time() - T00))
