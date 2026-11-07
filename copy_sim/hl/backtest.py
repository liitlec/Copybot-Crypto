"""Test sur l'historique : peut-on prédire, avec une probabilité, le sens de la prochaine bougie de 4 h des tokens les
plus échangés de Hyperliquid, assez bien pour gagner après frais ?

Règles du test (pour ne pas se mentir) :
- toutes les variables sont connues à la clôture de la bougie t ; on prédit le sens de la bougie t+1 ;
- apprentissage « walk-forward » : le modèle est réappris tous les 30 jours uniquement sur le passé, puis prédit les
  30 jours suivants qu'il n'a jamais vus ;
- les 90 derniers jours forment un « coffre » : ils ne servent à rien pendant la mise au point et sont lus une fois ;
- coûts par trade (aller-retour, sans levier) : 0,09 % de frais de preneur + 1,5 × l'écart achat-vente actuel du token ;
- un trade n'est pris que si la probabilité dépasse la précision nécessaire du token (frais / mouvement moyen appris
  sur le passé) plus une marge ;
- comparaisons : toujours acheteur, tendance 50 jours, retour à la moyenne sur 1 bougie, hasard.
Biais connu : les tokens sont les 30 plus échangés AUJOURD'HUI (biais du survivant, plutôt favorable au test).

Usage : python3 hl/backtest.py [--funding] [--holdout]   (sans --holdout : seulement la période de mise au point)"""
import json
import sys
import time
import urllib.request
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_hl"
BAR_H = 4
BARS_DAY = 24 // BAR_H
FEE_RT = 0.0009
REFIT_BARS = 30 * BARS_DAY
MIN_TRAIN_BARS = 180 * BARS_DAY
HOLDOUT_BARS = 90 * BARS_DAY
MARGIN = 0.01
MIN_TRAIN_ROWS_COIN = 60 * BARS_DAY


def load():
    uni = json.loads((DATA / "universe.json").read_text())["assets"]
    close, high, low, vol = {}, {}, {}, {}
    for a in uni:
        p = DATA / "candles_4h" / f"{a['coin']}.json"
        if not p.exists():
            continue
        c = json.loads(p.read_text())
        idx = pd.to_datetime([x["t"] for x in c], unit="ms", utc=True)
        close[a["coin"]] = pd.Series([float(x["c"]) for x in c], idx)
        high[a["coin"]] = pd.Series([float(x["h"]) for x in c], idx)
        low[a["coin"]] = pd.Series([float(x["l"]) for x in c], idx)
        vol[a["coin"]] = pd.Series([float(x["v"]) * float(x["c"]) for x in c], idx)
    f = lambda d: pd.DataFrame(d).sort_index()  # noqa: E731
    return f(close), f(high), f(low), f(vol)


def funding_frame(index):
    out = {}
    for p in (DATA / "funding").glob("*.json"):
        rows = json.loads(p.read_text())
        if not rows:
            continue
        s = pd.Series([float(r["fundingRate"]) for r in rows],
                      pd.to_datetime([r["time"] for r in rows], unit="ms", utc=True)).sort_index()
        s = s[~s.index.duplicated()]
        out[p.stem] = s.resample("4h").sum().reindex(index)  # financement payé sur la bougie
    return pd.DataFrame(out)


def spreads(coins):
    """Écart achat-vente actuel de chaque token (carnet Hyperliquid), gardé en cache dans data_hl/spreads.json."""
    cache = DATA / "spreads.json"
    out = json.loads(cache.read_text()) if cache.exists() else {}
    if all(c in out for c in coins):
        return out
    for coin in coins:
        try:
            req = urllib.request.Request("https://api.hyperliquid.xyz/info",
                                         data=json.dumps({"type": "l2Book", "coin": coin}).encode(),
                                         headers={"Content-Type": "application/json"})
            b = json.load(urllib.request.urlopen(req, timeout=20))
            bb, ba = float(b["levels"][0][0]["px"]), float(b["levels"][1][0]["px"])
            out[coin] = (ba - bb) / ((ba + bb) / 2)
        except Exception:
            out[coin] = 0.002  # prudent si le carnet n'a pas pu être lu
        time.sleep(1.0)
    cache.write_text(json.dumps(out, indent=1))
    return out


def features(close, high, low, vol, fund):
    r = close.pct_change()
    xs_mean = r.mean(axis=1)
    rows = []
    for coin in close.columns:
        c, rr = close[coin], r[coin]
        sd6 = rr.rolling(6).std()
        sd42 = rr.rolling(42).std()
        f = pd.DataFrame({
            "r0": rr / sd42, "r1": rr.shift(1) / sd42, "r2": rr.shift(2) / sd42,
            "r6": rr.rolling(6).sum() / (sd42 * np.sqrt(6)),
            "r18": rr.rolling(18).sum() / (sd42 * np.sqrt(18)),
            "r42": rr.rolling(42).sum() / (sd42 * np.sqrt(42)),
            "btc0": r["BTC"] / r["BTC"].rolling(42).std(),
            "btc6": r["BTC"].rolling(6).sum() / (r["BTC"].rolling(42).std() * np.sqrt(6)),
            "rel0": (rr - xs_mean) / sd42,
            "rel6": (rr - xs_mean).rolling(6).sum() / (sd42 * np.sqrt(6)),
            "volratio": np.log(sd6 / sd42),
            "vlm": np.log(vol[coin] / vol[coin].rolling(42).mean()),
            "range": (c - low[coin].rolling(42).min()) / (high[coin].rolling(42).max() - low[coin].rolling(42).min()),
            "trend300": np.log(c / c.rolling(300).mean()),
            "hour_s": np.sin(2 * np.pi * c.index.hour / 24), "hour_c": np.cos(2 * np.pi * c.index.hour / 24),
            "weekend": (c.index.dayofweek >= 5).astype(float),
        }, index=c.index)
        if coin in fund:
            fr = fund[coin]
            f["fund8h"] = fr.rolling(2).sum() * 1e4
            f["fund3d"] = fr.rolling(18).sum() * 1e4
        f["coin"] = coin
        f["absr"] = rr.abs()
        f["next"] = rr.shift(-1)  # rendement de la bougie suivante (cible)
        rows.append(f)
    df = pd.concat(rows).replace([np.inf, -np.inf], np.nan)
    return df


def run(df, cost, models, use_holdout):
    df = df.dropna(subset=["next", "r42", "btc6", "trend300"]).copy()
    feats = [c for c in df.columns if c not in ("coin", "absr", "next")]
    df[feats] = df[feats].fillna(0.0)
    times = np.sort(df.index.unique())
    end = len(times) if use_holdout else len(times) - HOLDOUT_BARS
    hold_start = times[len(times) - HOLDOUT_BARS]
    preds = {m: [] for m in models}
    t0 = MIN_TRAIN_BARS
    while t0 < end:
        tr_end, te_end = times[t0], times[min(t0 + REFIT_BARS, end) - 1]
        train = df[df.index < tr_end - pd.Timedelta(hours=BAR_H)]  # la cible de la dernière bougie n'est pas encore connue
        test = df[(df.index >= tr_end) & (df.index <= te_end)]
        if len(test):
            y = (train["next"] > 0).astype(int)
            m_abs = train.groupby("coin")["absr"].mean()
            n_coin = train.groupby("coin").size()
            for name, mk in models.items():
                mdl = mk().fit(train[feats].values, y.values)
                p = mdl.predict_proba(test[feats].values)[:, 1]
                out = test[["coin", "next"]].copy()
                out["p"] = p
                out["m_abs"] = out["coin"].map(m_abs)
                out["ok_hist"] = out["coin"].map(n_coin).fillna(0) >= MIN_TRAIN_ROWS_COIN
                preds[name].append(out)
        t0 += REFIT_BARS
    return {k: pd.concat(v) for k, v in preds.items()}, hold_start


def evaluate(pr, cost, label):
    pr = pr[pr["ok_hist"]].copy()
    pr["cost"] = pr["coin"].map(cost)
    pr["need"] = 0.5 + pr["cost"] / (2 * pr["m_abs"])
    up = (pr["next"] > 0).astype(int)
    hit_all = ((pr["p"] > 0.5).astype(int) == up).mean()
    base = up.mean()
    brier = ((pr["p"] - up) ** 2).mean()
    brier0 = ((base - up) ** 2).mean()
    side = np.where(pr["p"] > pr["need"] + MARGIN, 1, np.where(pr["p"] < 1 - pr["need"] - MARGIN, -1, 0))
    pr["side"] = side
    tr = pr[pr["side"] != 0]
    net = tr["side"] * tr["next"] - tr["cost"]
    hit_tr = (np.sign(tr["next"]) == tr["side"]).mean() if len(tr) else float("nan")
    # portefeuille : capital réparti à parts égales entre tous les tokens, un token sans trade rapporte 0
    port = (pr.assign(pnl=np.where(pr["side"] != 0, pr["side"] * pr["next"] - pr["cost"], 0.0))
            .groupby(level=0)["pnl"].mean())
    eq = (1 + port).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    days = (port.index.max() - port.index.min()).days or 1
    calib = pr.assign(b=pd.cut(pr["p"], [0, .45, .48, .5, .52, .55, 1])).groupby("b", observed=True).apply(
        lambda g: f"{len(g)} préd., annoncé {g['p'].mean():.1%}, réel {(g['next'] > 0).mean():.1%}")
    t = net.mean() / (net.std() / np.sqrt(len(net))) if len(net) > 1 else float("nan")
    lines = [f"### {label}",
             f"- période : {pr.index.min():%d/%m/%Y} → {pr.index.max():%d/%m/%Y} ({days} jours), {pr['coin'].nunique()} tokens, {len(pr)} bougies prédites",
             f"- sens bien prédit (toutes bougies, seuil 50 %) : {hit_all:.2%} (hausses réelles : {base:.1%}) ; score de Brier {brier:.5f} contre {brier0:.5f} sans modèle ({'mieux' if brier < brier0 else 'pas mieux'})",
             f"- trades pris (probabilité au-dessus de la précision nécessaire + {MARGIN:.0%}) : {len(tr)} ; justes {hit_tr:.2%}",
             f"- résultat net par trade : {net.mean():+.3%} (t = {t:+.2f}) ; total portefeuille {eq.iloc[-1] - 1:+.1%} sur {days} jours, pire baisse {dd:.1%}",
             "- calibration : " + " | ".join(f"{k} : {v}" for k, v in calib.items())]
    by_coin = tr.assign(net=net).groupby("coin")["net"].agg(["count", "mean"]).sort_values("mean")
    return "\n".join(lines), by_coin, port


def benchmarks(close, cost, start, end):
    r = close.pct_change()
    out = []
    sel = (r.index >= start) & (r.index <= end)
    nxt = r.shift(-1)
    # toujours acheteur (coût d'entrée négligé) ; tendance 50 jours (coût à chaque changement de sens) ; retour à la moyenne (coût à chaque bougie)
    trend_side = np.sign(close / close.rolling(300).mean() - 1)
    flips = (trend_side != trend_side.shift(1)).astype(float)
    cvec = pd.Series(cost)
    res = {
        "toujours acheteur": nxt[sel].mean(axis=1),
        "tendance 50 jours": (trend_side * nxt - flips.mul(cvec, axis=1))[sel].mean(axis=1),
        "retour à la moyenne (1 bougie)": (-np.sign(r) * nxt - cvec)[sel].mean(axis=1),
    }
    for k, port in res.items():
        port = port.dropna()
        eq = (1 + port).cumprod()
        out.append(f"- {k} : total {eq.iloc[-1] - 1:+.1%}, pire baisse {(eq / eq.cummax() - 1).min():.1%}")
    out.append("- hasard : en moyenne −(frais + écart) à chaque trade, soit environ −0,1 % à −0,15 % par trade")
    return "\n".join(out)


def main():
    use_holdout = "--holdout" in sys.argv
    close, high, low, vol = load()
    fund = funding_frame(close.index) if "--funding" in sys.argv else pd.DataFrame(index=close.index)
    print(f"{close.shape[1]} tokens, {len(close)} bougies, financement pour {fund.shape[1]} tokens", flush=True)
    sp = spreads(list(close.columns))
    cost = {k: FEE_RT + 1.5 * v for k, v in sp.items()}
    df = features(close, high, low, vol, fund)
    models = {
        "régression logistique": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.05, max_iter=500)),
        "arbres boostés": lambda: HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200,
                                                               min_samples_leaf=300, l2_regularization=1.0),
    }
    preds, hold_start = run(df, cost, models, use_holdout)
    md = [f"# Test de prédiction de direction, Hyperliquid 4 h — {time.strftime('%d/%m/%Y %H:%M')}", ""]
    for name, pr in preds.items():
        dev = pr[pr.index < hold_start]
        txt, by_coin, port = evaluate(dev, cost, f"{name} — période de mise au point")
        md += [txt, ""]
        if use_holdout:
            hold = pr[pr.index >= hold_start]
            txt2, by_coin2, _ = evaluate(hold, cost, f"{name} — COFFRE (90 derniers jours, lu une seule fois)")
            md += [txt2, ""]
        md += [f"Par token (mise au point, {name}) : " + ", ".join(f"{c} {int(n)} trades {m:+.2%}" for c, (n, m) in by_coin.iterrows()), ""]
    any_pr = next(iter(preds.values()))
    dev_end = any_pr[any_pr.index < hold_start].index.max()
    md += ["### Comparaisons sur la même période de mise au point", benchmarks(close, cost, any_pr.index.min(), dev_end), ""]
    rep = "\n".join(md)
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "hl_direction.md").write_text(rep, encoding="utf-8")
    print(rep)


if __name__ == "__main__":
    main()
