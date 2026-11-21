"""Registre papier en direct (ajout seulement, jamais de reecriture).
A chaque passage : python3 donnees.py && python3 registre.py
Ajoute a registre.csv une ligne par montage et par jour de bourse TERMINE apres le dernier jour deja inscrit.
Le gain du jour J utilise les poids decides a la cloture J-2 (executes a J-1) : rien ne depend du futur.
Depart : 10 000 (papier) le 11/11/2026 ; premier jour compte : 12/11/2026."""
import os, datetime
import numpy as np, pandas as pd
import banc_tendance as T, banc_prime as P
from donnees import UNIVERS

ICI = os.path.dirname(os.path.abspath(__file__))
REG = os.path.join(ICI, "registre.csv")
POS = os.path.join(ICI, "registre_positions.csv")
DEPART, CAPITAL = pd.Timestamp("2026-11-11"), 10000.0


def montages():
    r, taux = T.charge()
    r = r["2015":]
    taux = taux.reindex(r.index).ffill()
    cols = [a for a in r if UNIVERS[a][1] != "fx"]
    rp = r[cols]
    px = (1 + rp.fillna(0)).cumprod().where(rp.notna())
    ma = px.rolling(200).mean()
    out = {}
    w = P.poids(rp, rp * 0 + 1, 3.0, 3.0)
    out["P1_panier_CFD_x3"] = (P.net(rp, w, taux, "CFD"), w)
    w = P.poids(rp, (px > ma).astype(float).where(ma.notna()), 3.0, 3.0)
    out["P2_panier_CFD_x3_filtre200"] = (P.net(rp, w, taux, "CFD"), w)
    w = P.poids(rp, rp * 0 + 1, 1.0, 1.0)
    out["P3_panier_comptant"] = (P.net(rp, w, taux, "comptant"), w)
    w = T.poids(r, T.signal(r))
    b, c, f = T.resultat(r, w, taux)
    out["T0_tendance_temoin"] = (b - c - f, w)
    return out


if __name__ == "__main__":
    auj = pd.Timestamp(datetime.datetime.now(datetime.timezone.utc).date())
    m = montages()
    if os.path.exists(REG):
        reg = pd.read_csv(REG, parse_dates=["jour"])
    else:
        reg = pd.DataFrame([dict(jour=DEPART, montage=k, gain_pct=0.0, capital=CAPITAL) for k in m])
        reg.to_csv(REG, index=False)
    ajout, pos = [], []
    for k, (x, w) in m.items():
        der = reg[reg.montage == k].iloc[-1]
        cap = der.capital
        for j, g in x[(x.index > der.jour) & (x.index < auj)].items():   # jours termines seulement
            cap *= 1 + g
            ajout.append(dict(jour=j.date(), montage=k, gain_pct=round(100 * g, 4), capital=round(cap, 2)))
        wj = w[w.index < auj].iloc[-1]
        pos.append(dict(decide_le=wj.name.date(), ecrit_le=auj.date(), montage=k,
                        **{a: round(v, 3) for a, v in wj.dropna().items()}))
    if ajout:
        pd.DataFrame(ajout).to_csv(REG, mode="a", header=False, index=False)
    deja = set(pd.read_csv(POS)["decide_le"].astype(str)) if os.path.exists(POS) else set()
    neuf = [p for p in pos if str(p["decide_le"]) not in deja]      # une seule fois par jour de decision
    if neuf:
        pd.DataFrame(neuf).to_csv(POS, mode="a", header=not os.path.exists(POS), index=False)
    reg = pd.read_csv(REG)
    print("Lignes ajoutees :", len(ajout))
    print(reg.groupby("montage").agg(dernier_jour=("jour", "last"), jours=("jour", "count"), capital=("capital", "last")))
    print(pd.DataFrame(pos).set_index("montage").T.to_string())
