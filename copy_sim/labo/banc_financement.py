"""Banc FI : arbitrage des taux de financement crypto (« cash and carry », point 4b de PRIORITES 21/11, piste 2).
Compte DEMO, aucun ordre, aucune cle : donnees PUBLIQUES de data.binance.vision (archives mensuelles, sans cle).
Montage : acheter le comptant (BTCUSDT / ETHUSDT spot) et vendre le perpetuel USDT-M pour la meme quantite ; le prix
s'annule (reste l'ecart de base perpetuel - comptant), on encaisse le financement verse toutes les 8 h par les
acheteurs aux vendeurs quand il est positif (on le PAIE quand il est negatif).
NB : le compte demo MT5 (CFD BTCUSD/ETHUSD du courtier) NE PERMET PAS ce montage : pas de vrai comptant, pas de
perpetuel, et le CFD fait payer un portage dans les deux sens au lieu de verser le financement. Il faudrait un compte
sur une plateforme crypto (comptant + perpetuels), hors du perimetre du labo.

Donnees (telechargees une fois, gardees en donnees/financement_<actif>.csv.gz, 01/2022 -> 10/2026) : taux de
financement Binance (fundingRate), bougies 8 h du perpetuel (ouverture/haut/bas/cloture) et cloture 8 h du comptant.
La bougie qui FERME a l'heure du financement (0, 8, 16 h UTC) donne les prix de cet instant.

Regle (a chaque financement t, toutes les 8 h) :
  signal = taux annualise = moyenne des k derniers taux connus (dont celui de t) x 3 x 365.
  A plat et signal > ENTREE : achat comptant a la cloture comptant de t, vente du perpetuel a la cloture perp de t.
  En position et signal < SORTIE : on defait les deux jambes aux clotures de t.
  Le financement de t est encaisse si la position etait ouverte AVANT t (pas de fuite : on decide avec le taux de t
  pour le financement suivant).
Capital : K = 100 par actif = jambe comptant N + marge du perpetuel N / L (levier L = 3) -> N = 75 % du capital ;
  tout est exprime en % de ce capital total (les deux jambes immobilisees). Capital a plat : rapporte 0 ici ; la
  comparaison se fait contre les bons du Tresor 3 mois (donnees/cal_dtb3.csv) sur la part de temps en position
  (« exces » = rendement - Tresor x fraction du jour en position).
Couts : 0,1 % par jambe au comptant, 0,05 % par jambe sur le perpetuel, a l'entree et a la sortie (deux allers-retours :
  0,30 % du notionnel par cycle) ; ecart de base suppose (glissement entre les deux jambes) 0,05 % du notionnel a
  l'entree et a la sortie ; l'ecart de base REEL (perp - comptant) est marque a chaque cloture 8 h.
Jambe courte (levier 3) : reequilibrage quand le perp s'ecarte de 15 % du prix de reference : les deux jambes sont
  ramenees a la quantite N / prix (la marge redevient N / L ; cout 0,1 % + 0,05 % de la quantite deplacee, ref = prix) ; liquidation si le HAUT 8 h du
  perp depasse ref x (1 + 1/L - 0,5 %) : perte du perp au prix de liquidation + 0,5 % de penalite, jambe comptant
  vendue a la cloture de la bougie (non couverte entre les deux), position close. Liquidation = « saut ».
  Saut aussi : une periode de 8 h qui perd plus de 1 % du capital.
Risque d'echange : non simulable sur l'historique Binance (pas de defaut) ; scenario chiffre a part : faillite type FTX
  (11/2022) = perte de la marge du perpetuel (25 % du capital) + gain latent non rendu.

GRILLE FIXEE D'AVANCE (ecrite avant l'execution, rien d'ajoute ensuite), par actif (BTC, ETH) :
  ENTREE (% par an) {5, 10, 20, 30} x SORTIE {0, ENTREE/2} x lissage k {1 (dernier taux), 21 (7 jours)} = 16
  + « toujours dedans » (entre au debut, reste, re-entre apres une liquidation) = 17 variantes par actif, N = 34.
Mesures par variante (2022-01 -> 2026-10, courbe JOURNALIERE marquee aux clotures, base perp-comptant comprise) :
  rendement par an et median par mois en % du capital total, % de mois positifs, pire baisse, temps en position,
  cycles, liquidations, sauts (nombre, 1 tous les N mois, pire), exces par an sur le Tresor.
Walk-forward : apprentissage 12 mois / test 3 mois glissant (tests 01/2023 -> 10/2026), par actif ; choix = meilleur
  exces / pire baisse (courbe de l'exces) sur l'apprentissage ; si aucun exces > 0 a l'apprentissage, on reste a plat.
Essais multiples : reality check de White (banc_bt_regulier.white, bootstrap stationnaire de jours, blocs 5 j,
  2000 tirages, graine 17) sur la matrice jours x 34 variantes de l'EXCES journalier sur le Tresor -> p corrige.
Verdict fixe d'avance : TIENT = exces walk-forward hors echantillon > 0 sur BTC ET ETH, p corrige < 0,10, et pire
  baisse walk-forward > -10 % du capital ; PRESQUE = exces > 0 sur les deux mais p >= 0,10 (ou pire baisse <= -10 %) ;
  sinon NE TIENT PAS. Rappel du but (10-20 % par mois) : ce montage n'y pretend pas, on mesure s'il bat le Tresor.
RESULTAT (execution du 21/11/2026, telechargement ~2 min puis 1 s de calcul, rien de reduit) : verdict PRESQUE
  par la regle ecrite (exces hors echantillon > 0 sur les deux, mais p corrige = 0,459), en pratique un placement.
  Donnees : 5 294 financements par actif, tous a 8 h ; taux moyen BTC +6,6 %/an (2022 4,2 ; 2023 7,9 ; 2024 11,9 ;
  2025 5,1 ; 2026 3,1), ETH +5,9 %/an (0,8 ; 8,3 ; 13,0 ; 4,9 ; 2,1) ; > 0 82-85 % du temps ; base perp - comptant
  mediane -0,04 % (1-99 % : -0,08 / +0,09 %).
  Toujours dedans : BTC +4,75 %/an du capital total (93 % de mois > 0, pire baisse -0,36 %), ETH +4,20 %/an (90 %,
  -1,39 %) ; exces sur le Tresor +0,77 et +0,22 %/an. Seuil sur le dernier taux (k = 1) a 5-10 % : -3 a -24 %/an
  (allers-retours : 135 a 474 cycles, les frais mangent tout). Meilleures sur tout l'echantillon : E5/S0/k21
  (BTC +3,8 %/an), E20/S0/k1 (ETH exces +1,2 %/an). Aucune liquidation avec reequilibrage a 15 % ; sans
  reequilibrage (controle hors grille) 3 liquidations BTC, 1 ETH, pire 8 h -3,75 %. Aucun saut > 1 % en 8 h.
  Walk-forward (46 mois de test 01/2023-10/2026) : BTC +2,97 %/an (exces +1,34 %), ETH +2,82 %/an (exces +1,27 %),
  pire baisse -0,29 / -0,38 %, mois > 0 : 35 / 33 % (les autres a plat a 0), a plat depuis 01/2026 (taux faibles).
  Faillite de plateforme (marge perdue = 25 % du capital) : efface 5 a 6 ans de gain. Loin des 10-20 % par mois.
Ecrit donnees/financement_btc.csv.gz, donnees/financement_eth.csv.gz (brut) et donnees/financement_res.csv.
Usage : python3 banc_financement.py"""
import io, os, time, zipfile, urllib.request, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
DON = os.path.join(ICI, "donnees")
BASE = "https://data.binance.vision/data/"
MOIS = pd.period_range("2022-01", "2026-10", freq="M")
L, MM, PEN = 3.0, 0.005, 0.005
F_SPOT, F_PERP, EB = 0.001, 0.0005, 0.0005
REEQ = 0.15
H8 = 8 * 3600 * 1000


def _zip_csv(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for essai in range(3):
        try:
            z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()))
            return pd.read_csv(z.open(z.namelist()[0]), header=None)
        except Exception:
            time.sleep(2)
    raise RuntimeError("echec " + url)


def _ms(x):
    x = pd.to_numeric(x, errors="coerce")
    return np.where(x > 1e14, x // 1000, x).astype("int64")     # le comptant passe en microsecondes en 2025


def telecharge(actif):
    f = os.path.join(DON, "financement_%s.csv.gz" % actif)
    if os.path.exists(f):
        return pd.read_csv(f)
    sym = actif.upper() + "USDT"
    fu, pk, sk = [], [], []
    for m in MOIS:
        s = "%s-%s" % (sym, m)
        a = _zip_csv(BASE + "futures/um/monthly/fundingRate/%s/%s-fundingRate-%s.zip" % (sym, sym, m))
        a = a[pd.to_numeric(a[0], errors="coerce").notna()]
        fu.append(pd.DataFrame({"t": _ms(a[0]), "taux": a[2].astype(float), "intervalle_h": a[1].astype(int)}))
        b = _zip_csv(BASE + "futures/um/monthly/klines/%s/8h/%s-8h-%s.zip" % (sym, sym, m))
        b = b[pd.to_numeric(b[0], errors="coerce").notna()]
        pk.append(pd.DataFrame({"t": _ms(b[0]) + H8, "p_ouv": b[1].astype(float), "p_haut": b[2].astype(float),
                                "p_bas": b[3].astype(float), "p_clo": b[4].astype(float)}))
        c = _zip_csv(BASE + "spot/monthly/klines/%s/8h/%s-8h-%s.zip" % (sym, sym, m))
        sk.append(pd.DataFrame({"t": _ms(c[0]) + H8, "s_clo": c[4].astype(float)}))
    fu = pd.concat(fu)
    fu["t"] = -(-(fu.t - 60000) // H8) * H8          # financement rattache a la borne 8 h (0/8/16 UTC) qui suit
    fu = fu.groupby("t").agg(taux=("taux", "sum"), intervalle_h=("intervalle_h", "min")).reset_index()
    d = fu.merge(pd.concat(pk), on="t").merge(pd.concat(sk), on="t").sort_values("t").reset_index(drop=True)
    d.to_csv(f, index=False, compression="gzip")
    return d


def simule(d, entree, sortie, k, toujours=False, reeq=REEQ):
    """Rend (gain par periode 8 h en % du capital, en position (0/1) par periode, cycles, liquidations)."""
    tx = d.taux.values; pc = d.p_clo.values; ph = d.p_haut.values; sc = d.s_clo.values
    sig = pd.Series(tx).rolling(k, min_periods=1).mean().values * 3 * 365 * 100
    n = len(d); g = np.zeros(n); pos = np.zeros(n); N = 100.0 / (1 + 1 / L)
    dedans = False; q = ref = 0.0; cycles = liq = 0
    for i in range(n):
        if dedans:
            pos[i] = 1
            pliq = ref * (1 + 1 / L - MM)
            if ph[i] >= pliq:          # jambe courte liquidee dans la bougie
                g[i] += q * (sc[i] - sc[i - 1]) - q * (pliq - pc[i - 1]) - PEN * q * pliq - F_SPOT * q * sc[i]
                dedans = False; liq += 1
                continue
            g[i] += q * (sc[i] - sc[i - 1]) - q * (pc[i] - pc[i - 1]) + q * pc[i] * tx[i]
            if abs(pc[i] / ref - 1) >= reeq:
                q2 = N / pc[i]                     # retour a N : la marge reprend N / L, l'equite reste ~ 100
                g[i] -= abs(q - q2) * (sc[i] * F_SPOT + pc[i] * F_PERP)
                q = q2; ref = pc[i]
            if not toujours and sig[i] < sortie:
                g[i] -= q * sc[i] * F_SPOT + q * pc[i] * (F_PERP + EB)
                dedans = False
                continue
        if not dedans and (toujours or sig[i] > entree) and i < n - 1:
            q = N / sc[i]; ref = pc[i]; dedans = True; cycles += 1
            g[i] -= q * sc[i] * F_SPOT + q * pc[i] * (F_PERP + EB)
    return g, pos, cycles, liq


def jour(d, x, agg="sum"):
    j = pd.to_datetime(d.t - 1, unit="ms").dt.floor("D")
    return pd.Series(x).groupby(j.values).agg(agg)


def mesure(r, ex, sauts8):
    """r, ex : series journalieres (% du capital)."""
    m = r.groupby(r.index.to_period("M")).sum()
    c = r.cumsum(); dd = (c - np.maximum(c.cummax(), 0)).min()
    ans = len(r) / 365.25
    return dict(an=r.sum() / ans, med_mois=m.median(), mois_pos=100 * (m > 0).mean(), pire_mois=m.min(), pire_baisse=dd,
                exces_an=ex.sum() / ans, sauts=int(sauts8), saut_n_mois=(len(m) / sauts8 if sauts8 else np.nan))


if __name__ == "__main__":
    tb = pd.read_csv(os.path.join(DON, "cal_dtb3.csv"), parse_dates=["date"]).set_index("date").dtb3
    GRILLE = [(e, s, k, False) for e in (5, 10, 20, 30) for s in (0, None) for k in (1, 21)] + [(None, None, 1, True)]
    nomv = lambda v: "toujours" if v[3] else "E%d/S%s/k%d" % (v[0], "0" if v[1] == 0 else "E/2", v[2])
    RJ, EXJ, LIG, SIM = {}, {}, [], {}
    for actif in ("btc", "eth"):
        d = telecharge(actif)
        print("%s : %d financements, %s -> %s, intervalles %s h, taux moyen %+.2f %% par an, > 0 : %.0f %% du temps"
              % (actif.upper(), len(d), pd.to_datetime(d.t.iloc[0], unit="ms"), pd.to_datetime(d.t.iloc[-1], unit="ms"),
                 sorted(d.intervalle_h.unique()), d.taux.mean() * 3 * 365 * 100, 100 * (d.taux > 0).mean()))
        base = 100 * (d.p_clo / d.s_clo - 1)
        print("   ecart perp - comptant a la cloture : median %+.3f %%, 1 %% / 99 %% : %+.3f / %+.3f %%"
              % (base.median(), base.quantile(0.01), base.quantile(0.99)))
        for v in GRILLE:
            e, s, k, tj = v
            g, pos, cyc, liq = simule(d, e if e is not None else 0, (e / 2 if s is None else s) if e else 0, k, tj)
            r = jour(d, g); p = jour(d, pos, "mean")
            tbj = tb.reindex(r.index, method="ffill").fillna(tb.iloc[0]).values / 100 / 365 * 100
            ex = r - p * tbj
            nm = actif + " " + nomv(v)
            RJ[nm], EXJ[nm] = r, ex
            SIM[nm] = (g, d)
            s8 = liq + int((g < -1).sum())
            LIG.append(dict(variante=nm, cycles=cyc, liquidations=liq, en_position=100 * pos.mean(),
                            pire_8h=g.min(), **mesure(r, ex, s8)))
    R = pd.DataFrame(LIG)
    R.to_csv(os.path.join(DON, "financement_res.csv"), index=False, float_format="%.4f")
    pd.set_option("display.width", 220)
    print("\nToutes les variantes, 01/2022 -> 10/2026 (% du capital total = comptant + marge) :")
    print(R.round(2).to_string(index=False))
    # ---------------------------------------------------------------- walk-forward 12 / 3 mois
    print("\nWalk-forward 12 mois / 3 mois (choix au meilleur exces / pire baisse de l'exces a l'apprentissage) :")
    WF = {}
    for actif in ("btc", "eth"):
        noms = [n for n in RJ if n.startswith(actif)]
        E = pd.DataFrame({n: EXJ[n] for n in noms}); Rr = pd.DataFrame({n: RJ[n] for n in noms})
        Mo = E.index.to_period("M")
        oos_r, oos_e, choix = [], [], []
        for t0 in pd.period_range("2023-01", "2026-10", freq="M")[::3]:
            app = (Mo >= t0 - 12) & (Mo < t0); tst = (Mo >= t0) & (Mo < t0 + 3)
            c = E[app].cumsum(); dd = (c - np.maximum(c.cummax(), 0)).min().abs().clip(lower=0.05)
            sc_ = E[app].sum() / dd
            if E[app].sum().max() <= 0:
                choix.append("(a plat)"); oos_r.append(Rr[tst].iloc[:, 0] * 0); oos_e.append(E[tst].iloc[:, 0] * 0)
                continue
            b = sc_.idxmax(); choix.append(b.split(" ")[1])
            oos_r.append(Rr[tst][b]); oos_e.append(E[tst][b])
        ro, eo = pd.concat(oos_r), pd.concat(oos_e)
        WF[actif] = (ro, eo)
        mo = ro.groupby(ro.index.to_period("M")).sum()
        c = ro.cumsum()
        print("  %s : %d mois de test ; rendement %+.2f %% (%+.2f %% par an), exces sur Tresor %+.2f %% par an ; "
              "mois > 0 : %.0f %% ; median/mois %+.3f %% ; pire baisse %.2f %%" % (
                  actif.upper(), len(mo), ro.sum(), ro.sum() / (len(ro) / 365.25), eo.sum() / (len(eo) / 365.25),
                  100 * (mo > 0).mean(), mo.median(), (c - np.maximum(c.cummax(), 0)).min()))
        print("     choix successifs :", ", ".join(choix))
    # ---------------------------------------------------------------- reality check de White
    Dm = pd.DataFrame(EXJ).fillna(0).values
    best, p = BR.white(Dm)
    print("\nReality check de White sur l'exces journalier (N = %d) : meilleure %s, p corrige = %.3f"
          % (Dm.shape[1], list(EXJ)[best], p))
    # ---------------------------------------------------------------- controle hors grille : sans reequilibrage
    for actif in ("btc", "eth"):
        d = telecharge(actif)
        g, pos, cyc, liq = simule(d, 0, 0, 1, True, reeq=9e9)
        r = jour(d, g)
        print("Controle hors grille %s toujours dedans SANS reequilibrage : %d liquidations, %+.2f %% par an, pire baisse %.2f %%, pire 8 h %.2f %%"
              % (actif.upper(), liq, r.sum() / (len(r) / 365.25), (r.cumsum() - np.maximum(r.cumsum().cummax(), 0)).min(), g.min()))
    # ---------------------------------------------------------------- risque d'echange
    for nm in ("btc toujours", "eth toujours"):
        an = R.set_index("variante").loc[nm, "an"]
        print("Scenario faillite de la plateforme (perte de la marge = %.0f %% du capital) pour %s : efface %.1f ans de gain"
              % (100 / (1 + L), nm, (100 / (1 + L)) / an if an > 0 else np.inf))
    eb = all(WF[a][1].sum() > 0 for a in WF)
    dd = min(((WF[a][0].cumsum() - np.maximum(WF[a][0].cumsum().cummax(), 0)).min()) for a in WF)
    v = "TIENT" if eb and p < 0.10 and dd > -10 else ("PRESQUE" if eb else "NE TIENT PAS")
    print("\nVERDICT : %s  (exces hors echantillon > 0 sur les deux : %s ; p = %.3f ; pire baisse WF %.2f %%)  [%.0f s]"
          % (v, eb, p, dd, time.time() - T00))
