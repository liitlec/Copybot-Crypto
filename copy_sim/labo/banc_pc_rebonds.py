"""Banc AR : pari court (PRIORITES 17/11 20 h 10), piste « bt_or et rebonds d'indices a tres forte mise sur horizon
court ». Seules des regles a AVANTAGE PROUVE au labo sont misees :
  rebond_nas : contre-pied d'une grande journee du Nasdaq 100, une journee (Yahoo ^NDX 2001-2026, ouvertures reelles) ;
  rebond_nas_sp : le meme sur Nasdaq et S&P (S&P depuis 2008, regle figee du Nasdaq, banc_grande_journee.py) ;
  repli_us : repli des 4 indices US (RSI 2 j < 10 au-dessus de la moyenne 200 j, 1 a 10 jours ; Yahoo 1990-2026) ;
  bt_or : paniers de la mecanique BlockTrend sur l'or (H1 courtier 08/2022-11/2026 ; « presque » : gagne surtout en 2024-26).
Couts : 1,5 bp aller-retour (indices) + nuit pour le repli ; or : spread reel du banc. Tailles du courtier aux prix
d'aujourd'hui (lot minimum : NAS100+ 0,1 x ~28 000 $, SP500+ 0,1 x ~7 600 $, DJ30+ 0,1 x ~51 000 $, US2000+ 0,1 x ~2 800 $,
or 0,01 lot = 1 once ~3 880 $). Mise : levier L = 10 / 25 / 50 / 100 fois le compte (N = 4 montages x 4 leviers x 2
modes « compose » / « fixe » = 32 essais), comparee par pari_court_commun.comparer (fenetres historiques reelles,
version mesuree, avantage / 2, reference sans avantage). Choix fixe d'avance : parmi les essais dont la version
« avantage / 2 » bat nettement la reference (bat_ref) a 1 semaine ou 1 mois, celui qui maximise la chance de x3 en
1 mois a 100 $ ; si aucun ne bat la reference, rien n'est mis sur la demo.
Usage : python3 banc_pc_rebonds.py"""
import os, sys, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import pari_court_commun as C
import banc_portefeuille as BP
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR

UNITE = {"NAS": 0.1 * 28355, "SP": 0.1 * 7600, "DJ": 0.1 * 52300, "RUT": 0.1 * 2790}
COUT = 1.5e-4


def rebond(D, n, depuis):
    o = D[n]; c = o["close"]
    amp = (o["high"] - o["low"]) / c.shift(1)
    med = amp.shift(1).rolling(20).median()
    s = -np.sign(c - c.shift(1)).where(amp > 1.5 * med, 0).shift(1)
    ok = (s != 0) & o["open"].notna() & o["high"].notna() & (o.index >= depuis)
    x = o[ok]; s = s[ok]
    r = s * (x["close"] - x["open"]) / x["open"] - COUT
    mae = np.where(s > 0, (x["open"] - x["low"]) / x["open"], (x["high"] - x["open"]) / x["open"])
    return pd.DataFrame({"t0": x.index + pd.Timedelta(hours=1), "t1": x.index + pd.Timedelta(hours=23), "r": r.values,
                         "cout": COUT, "mae": np.clip(mae, 0, None), "unite": UNITE[n], "marche": n})


def repli(D, n):
    o = D[n]; c = o["close"]; idx = c.index
    rs, ma200, ma5 = BP.rsi2(c), c.rolling(200).mean(), c.rolling(5).mean()
    fin = BP.nuit(D, idx)
    T, i, N = [], 200, len(idx)
    while i < N - 1:
        if rs.iloc[i] < 10 and c.iloc[i] > ma200.iloc[i]:
            j = i + 1
            while j < N - 1 and not (c.iloc[j] > ma5.iloc[j] or j - i >= 10):
                j += 1
            e = c.iloc[i]
            lo = o["low"].iloc[i + 1:j + 1].min()
            lo = c.iloc[i + 1:j + 1].min() if lo != lo else lo
            r = c.iloc[j] / e - 1 - COUT - fin.iloc[i + 1:j + 1].sum()
            T.append((idx[i] + pd.Timedelta(hours=23), idx[j] + pd.Timedelta(hours=22), r, COUT + fin.iloc[i + 1:j + 1].sum(),
                      max(0.0, (e - lo) / e), UNITE[n], n))
            i = j + 1
        else:
            i += 1
    return pd.DataFrame(T, columns=["t0", "t1", "r", "cout", "mae", "unite", "marche"])


def bt_or():
    d = BR.charge("xau_h1_50k")
    d = d[d.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    P = BR.simule(d, span=48, heures={(2, 0), (7, 0), (11, 0), (14, 0), (15, 0)}, debut=60)
    sp = float(np.median(d.sp)) / float(np.median(d.cloture))
    return pd.DataFrame({"t0": pd.to_datetime(P.t0, unit="s"), "t1": pd.to_datetime(P.t1, unit="s"),
                         "r": (P.g * P.stop / P.px).values, "cout": sp, "mae": (P.stop / P.px).values,
                         "unite": 3880.0, "marche": "XAU"})


if __name__ == "__main__":
    D = BP.donnees()
    M = {"rebond_nas": rebond(D, "NAS", "2001-01-01"),
         "rebond_nas_sp": pd.concat([rebond(D, "NAS", "2008-01-01"), rebond(D, "SP", "2008-01-01")], ignore_index=True),
         "repli_us": pd.concat([repli(D, n) for n in ("SP", "NAS", "DJ", "RUT")], ignore_index=True),
         "bt_or": bt_or()}
    for k, T in M.items():
        print("%-14s %5d trades %s -> %s : %+.1f bp par trade (t %.1f), cout %.1f bp" % (
            k, len(T), T.t0.min().date(), T.t0.max().date(), 1e4 * T.r.mean(), T.r.mean() / T.r.std() * np.sqrt(len(T)), 1e4 * T.cout.mean()))
    lignes = []
    for k, T in M.items():
        for mode in ("compose", "fixe"):
            for L in (10, 25, 50, 100):
                for dep in (100.0, 500.0):
                    R = C.comparer(T, L, dep, mode)
                    R.insert(0, "depart", int(dep)); R.insert(0, "levier", L); R.insert(0, "mode", mode); R.insert(0, "montage", k)
                    lignes.append(R)
    R = pd.concat(lignes, ignore_index=True)
    R.to_csv(os.path.join(ICI, "donnees", "pc_rebonds_resultats.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 1000)
    v = R[(R.version != "mesure") & (R.depart == 100) & (R["mode"] == "compose")].copy()
    for c in ("ruine", "x2", "x3", "x5", "x10", "esperance"):
        v[c] = (100 * v[c]).round(1)
    print(v[["montage", "levier", "version", "horizon", "fenetres", "independantes", "ruine", "esperance", "x2", "x3", "x5", "x10", "bat_ref"]].to_string(index=False))
    a = R[(R.version == "avantage / 2") & (R.bat_ref == True) & R.horizon.isin(["1 semaine", "1 mois"])]
    cand = set(zip(a.montage, a["mode"], a.levier))
    print("\nEssais qui battent nettement la reference (avantage / 2, 1 semaine ou 1 mois) :", sorted(cand))
    m = R[(R.version == "avantage / 2") & (R.horizon == "1 mois") & (R.depart == 100)]
    m = m[[(x, y, z) in cand for x, y, z in zip(m.montage, m["mode"], m.levier)]]
    if len(m):
        b = m.sort_values("x3", ascending=False).iloc[0]
        print("Choix fixe d'avance :", dict(b[["montage", "mode", "levier", "x2", "x3", "x5", "x10", "ruine", "esperance"]]))
    else:
        print("Choix fixe d'avance : aucun essai ne bat la reference -> rien sur la demo pour cette piste.")
