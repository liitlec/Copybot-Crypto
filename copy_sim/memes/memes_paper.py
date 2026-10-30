"""Test PAPIER de la stratégie memecoins du post « Hedge Fund Terminal » (@savipww, 13/10/2026), au plus près de ses
règles, sur Solana. Aucune clé, aucun wallet, aucun ordre : lecture seule de GeckoTerminal (gratuit) et de FRED.

Règles (figées dans memes/regle_memes.json au premier lancement) :
- toutes les 5 min, univers = nouveaux pools + pools tendance GeckoTerminal ;
- filtre : âge 15 min à 72 h, liquidité > 12 000 $, volume 24 h > 40 000 $, capitalisation 60 000 $ à 8 M$ ;
- classement : les détenteurs montent plus vite que le prix sur la dernière heure (écart en tête) ; croissance des
  détenteurs = (portefeuilles acheteurs − vendeurs distincts sur 1 h) / nombre de détenteurs, car le nombre de
  détenteurs de GeckoTerminal n'est rafraîchi que toutes les 1 à 19 h ; écarté si le prix monte plus vite que les
  détenteurs, ou si les ventes dépassent les achats sur 30 min ET sur 1 h ;
- cadran « meme » (calculé une fois par jour) = part de feux verts parmi : liquidité nette de la Fed en hausse sur
  4 semaines, VIX < 22, BTC > moyenne 200 jours, SOL > moyenne 50 jours ; sous 0,5 : aucune entrée ce jour-là ;
- taille = 6 % de la caisse × cadran, plafonnée à 2 % de la liquidité du pool ; frais 0,45 % par côté (min 0,95 $)
  + impact sur le prix calculé sur la liquidité du pool, à l'achat et à la vente ;
- sortie : volume des 6 dernières heures < 20 % de la normale (volume 24 h / 4), vérifié toutes les 5 min ; pool
  disparu ou liquidité < 1 000 $ = vidé, compté à la valeur de revente réelle (souvent proche de −100 %) ;
- trois caisses séparées : « classement » (règles du post, cadran compris), « sans_cadran » (mêmes choix tous les jours,
  pour juger le cadran) et « temoin » (à chaque entrée de « sans_cadran », un token tiré au hasard parmi ceux qui
  passent le filtre, même taille, même sortie). Si le classement ne bat pas le témoin, il ne sert à rien.
Différences assumées avec le post : pas d'IA « juge » (le premier du classement est pris), pas de Kelly (pas
d'avantage connu à mettre dedans), Solana seulement.

Usage : python3 memes_paper.py [--dir DOSSIER] [--once] [--bank 10000]"""
import argparse
import json
import random
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

GT = "https://api.geckoterminal.com/api/v2/networks/solana"
UA = {"Accept": "application/json", "User-Agent": "memes-paper/1.0 (read-only research)"}
RULE = {
    "nom": "memecoins façon @savipww, papier",
    "age_min_s": 15 * 60, "age_max_s": 72 * 3600, "liq_min": 12_000, "vol24_min": 40_000,
    "mcap_min": 60_000, "mcap_max": 8_000_000,
    "ticket_part": 0.06, "plafond_liquidite": 0.02, "frais": 0.0045, "frais_min": 0.95,
    "sortie_ratio_volume": 0.20, "vide_liquidite": 1_000, "max_positions": 10, "cycle_s": 300,
    "cadran_min": 0.50, "holders_cache_s": 3600,
    "verdict": "après au moins 100 trades fermés : gagnant seulement si la moyenne dépasse 2 fois sa marge d'erreur, "
               "reste positive sans les 3 meilleurs trades ET bat le témoin tiré au hasard ; le cadran n'est utile que si « classement » bat « sans_cadran »",
}
_last_call = [0.0]


def get(url, tries=4):
    for k in range(tries):
        wait = 2.2 - (time.time() - _last_call[0])  # ≤ ~27 appels/min, sous la limite gratuite
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception as exc:
            if k == tries - 1:
                raise
            time.sleep(10 * (k + 1))
            last = exc  # noqa: F841
    return None


def text(url, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl/8.5.0"}),
                                        timeout=90) as r:
                return r.read().decode()
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(15)


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ cadran du jour
def fred(series):
    rows = [ln.split(",") for ln in text(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}").splitlines()[1:]]
    return [(d, float(v)) for d, v in rows if v not in ("", ".")]


def hl_closes(coin, days):
    now = int(time.time() * 1000)
    body = json.dumps({"type": "candleSnapshot", "req": {"coin": coin, "interval": "1d",
                                                           "startTime": now - (days + 5) * 86_400_000, "endTime": now}})
    req = urllib.request.Request("https://api.hyperliquid.xyz/info", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return [float(c["c"]) for c in json.load(r)]


def dial():
    greens, info = {}, {}
    try:
        walcl, tga, rrp = dict(fred("WALCL")), dict(fred("WTREGEN")), dict(fred("RRPONTSYD"))
        dates = sorted(d for d in walcl if d in tga)

        def net(d):  # WALCL et WTREGEN en millions, RRPONTSYD en milliards
            r = max((x for x in rrp if x <= d), default=None)
            return walcl[d] / 1000 - tga[d] / 1000 - (rrp[r] if r else 0)
        chg = net(dates[-1]) - net(dates[-5])
        greens["liquidite"], info["net_liq_4s_mds"] = chg > 0, round(chg, 1)
    except Exception as exc:
        greens["liquidite"], info["liquidite_erreur"] = False, str(exc)[:80]  # donnée manquante = rouge
    try:
        vix = fred("VIXCLS")[-1]
        greens["vix"], info["vix"] = vix[1] < 22, vix
    except Exception as exc:
        greens["vix"], info["vix_erreur"] = False, str(exc)[:80]
    for coin, n in (("BTC", 200), ("SOL", 50)):
        try:
            c = hl_closes(coin, n)
            ma = sum(c[-n:]) / n
            greens[coin.lower()], info[f"{coin.lower()}_vs_ma{n}"] = c[-1] > ma, round(c[-1] / ma - 1, 4)
        except Exception as exc:
            greens[coin.lower()], info[f"{coin.lower()}_erreur"] = False, str(exc)[:80]
    value = sum(greens.values()) / 4
    return {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "cadran": value, "verts": greens, "donnees": info}


# ------------------------------------------------------------------ marché
def pools_universe():
    out = {}
    for path, pages in (("new_pools", 5), ("trending_pools", 3)):
        for page in range(1, pages + 1):
            try:
                d = get(f"{GT}/{path}?page={page}")
            except Exception:
                continue
            for p in d.get("data", []):
                a = p["attributes"]
                token = p["relationships"]["base_token"]["data"]["id"].split("_", 1)[1]
                prev = out.get(token)
                if prev is None or (fnum(a["reserve_in_usd"]) or 0) > (fnum(prev["reserve_in_usd"]) or 0):
                    out[token] = dict(a, pool=a["address"], token=token)
    return list(out.values())


def passes(a, now):
    try:
        age = now - datetime.fromisoformat(a["pool_created_at"].replace("Z", "+00:00")).timestamp()
    except Exception:
        return False
    liq, vol = fnum(a["reserve_in_usd"]) or 0, fnum(a["volume_usd"]["h24"]) or 0
    mcap = fnum(a.get("market_cap_usd")) or fnum(a.get("fdv_usd")) or 0
    return (RULE["age_min_s"] <= age <= RULE["age_max_s"] and liq > RULE["liq_min"] and vol > RULE["vol24_min"]
            and RULE["mcap_min"] <= mcap <= RULE["mcap_max"])


def holders(token, cache, now):
    c = cache.get(token)
    if c and now - c["t"] < RULE["holders_cache_s"]:
        return c["n"]
    try:
        n = get(f"{GT}/tokens/{token}/info")["data"]["attributes"]["holders"]["count"]
    except Exception:
        n = None
    cache[token] = {"t": now, "n": n}
    return n


def pools_now(addresses):
    res = {}
    for i in range(0, len(addresses), 30):
        try:
            d = get(f"{GT}/pools/multi/{','.join(addresses[i:i + 30])}")
        except Exception:
            continue
        for p in d.get("data", []):
            res[p["attributes"]["address"]] = p["attributes"]
    return res


# ------------------------------------------------------------------ comptabilité
def cost(dollars):
    return max(RULE["frais"] * dollars, RULE["frais_min"])


def impact(dollars, liq):
    """Pool à produit constant, côté SOL ≈ moitié de la liquidité : glissement ≈ montant / (liquidité / 2)."""
    return min(dollars / max(liq / 2, 1.0), 0.95)


def open_pos(book, a, dollars, now, why):
    liq, px = fnum(a["reserve_in_usd"]), fnum(a["base_token_price_usd"])
    fill = px * (1 + impact(dollars, liq))
    fee = cost(dollars)
    qty = (dollars - fee) / fill
    book["cash"] -= dollars
    book["open"][a["token"]] = {"pool": a["pool"], "name": a.get("name"), "t": now, "dollars": dollars, "qty": qty,
                                "px_in": px, "fill_in": fill, "liq_in": liq, "why": why}


def close_pos(book, token, a, now, reason, log):
    p = book["open"].pop(token)
    liq = fnum(a.get("reserve_in_usd")) if a else 0.0
    px = fnum(a.get("base_token_price_usd")) if a else 0.0
    gross = p["qty"] * (px or 0) * (1 - impact(p["qty"] * (px or 0), liq or 0))
    proceeds = max(gross - cost(gross) if gross > 0 else 0.0, 0.0)
    book["cash"] += proceeds
    rec = {"book": book["name"], "token": token, "pool": p["pool"], "name": p["name"], "t_in": p["t"], "t_out": now,
           "minutes": round((now - p["t"]) / 60), "dollars": p["dollars"], "proceeds": round(proceeds, 4),
           "ret": round(proceeds / p["dollars"] - 1, 5), "reason": reason, "why": p["why"]}
    book["closed"].append(rec)
    log(rec)


def equity(book, live):
    val = book["cash"]
    for token, p in book["open"].items():
        a = live.get(p["pool"])
        if a:
            val += p["qty"] * (fnum(a["base_token_price_usd"]) or 0)
    return val


# ------------------------------------------------------------------ boucle
def cycle(state, out_dir, now):
    log_path = out_dir / "trades.jsonl"

    def log(rec):
        with log_path.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    d = state.get("dial", {})
    failed = any(k.endswith("_erreur") for k in d.get("donnees", {}))
    if d.get("date") != today or (failed and now - d.get("t", 0) > 1800):  # nouvel essai toutes les 30 min si erreur
        state["dial"] = dict(dial(), t=now)
        log({"event": "cadran", **state["dial"]})
    dial_v = state["dial"]["cadran"]
    # 1. sorties
    held = {p["pool"] for b in state["books"].values() for p in b["open"].values()}
    live = pools_now(sorted(held))
    for b in state["books"].values():
        for token, p in list(b["open"].items()):
            a = live.get(p["pool"])
            if a is None or (fnum(a["reserve_in_usd"]) or 0) < RULE["vide_liquidite"]:
                close_pos(b, token, a, now, "pool vidé ou disparu", log)
                continue
            v24, v6 = fnum(a["volume_usd"]["h24"]) or 0, fnum(a["volume_usd"]["h6"]) or 0
            if v24 > 0 and v6 / (v24 / 4) < RULE["sortie_ratio_volume"]:
                close_pos(b, token, a, now, f"volume 6 h à {v6 / (v24 / 4):.0%} de la normale", log)
    # 2. candidats
    uni = [a for a in pools_universe() if passes(a, now)]
    # Classement. Le nombre de détenteurs de GeckoTerminal n'est rafraîchi que toutes les 1 à 19 h : on mesure donc la
    # croissance des détenteurs sur la dernière heure par les portefeuilles distincts acheteurs moins vendeurs (donnée en
    # continu), rapportés au nombre de détenteurs, et on la compare à la variation de prix sur la même heure.
    ranked = []
    for a in uni:
        tx = a["transactions"]
        if tx["m30"]["sells"] > tx["m30"]["buys"] and tx["h1"]["sells"] > tx["h1"]["buys"]:
            continue
        n = holders(a["token"], state.setdefault("hcache", {}), now)
        pg = (fnum(a["price_change_percentage"].get("h1")) or 0.0) / 100
        if not n:
            continue
        hg = (tx["h1"].get("buyers", 0) - tx["h1"].get("sellers", 0)) / n
        if hg > pg:
            ranked.append((hg - pg, a, round(hg, 4), round(pg, 4)))
    ranked.sort(key=lambda x: -x[0])
    state.pop("snaps", None)
    # 3. entrées (une par cycle et par caisse). « classement » suit le cadran comme dans le post ; « sans_cadran » prend
    #    les mêmes choix tous les jours ; « temoin » tire au hasard dans le filtre à chaque entrée de « sans_cadran ».
    def enter(book, a, dial_mult, why):
        dollars = min(RULE["ticket_part"] * book["cash_ref"] * dial_mult, RULE["plafond_liquidite"] * fnum(a["reserve_in_usd"]),
                      book["cash"])
        if dollars < RULE["frais_min"] / 0.02 or len(book["open"]) >= RULE["max_positions"]:  # frais > 2 % : pas de trade
            return None
        open_pos(book, a, dollars, now, why)
        log({"event": "achat", "book": book["name"], "token": a["token"], "name": a.get("name"), "dollars": round(dollars, 2)})
        return dollars

    books = state["books"]
    if ranked:
        for name, mult in (("classement", dial_v if dial_v >= RULE["cadran_min"] else 0), ("sans_cadran", 1.0)):
            if mult <= 0:
                continue
            bk = books[name]
            pick = next((r for r in ranked if r[1]["token"] not in bk["open"]), None)
            if pick and enter(bk, pick[1], mult, {"score": round(pick[0], 4), "detenteurs": pick[2], "prix": pick[3]}) \
                    and name == "sans_cadran":
                pool = [x for x in uni if x["token"] not in books["temoin"]["open"]]
                if pool:
                    enter(books["temoin"], random.choice(pool), 1.0, {"hasard": True})
    # caisse de référence pour la taille : valeur du compte au début de chaque jour (pas de réinvestissement intra-jour)
    for b in state["books"].values():
        if b.get("ref_day") != state["dial"]["date"]:
            b["cash_ref"], b["ref_day"] = equity(b, live), state["dial"]["date"]
    state["last_cycle"] = now
    state["last_universe"] = len(uni)
    state["last_ranked"] = len(ranked)
    write_status(state, out_dir, live)


def stats(rs):
    if not rs:
        return "0 trade"
    xs = [r["ret"] for r in rs]
    n, m = len(xs), sum(xs) / len(xs)
    sd = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5 if n > 1 else 0
    srt = sorted(xs, reverse=True)
    no3 = sum(srt[3:]) / len(srt[3:]) if len(srt) > 3 else float("nan")
    return (f"{n} trades, moyenne {m:+.1%} ± {sd / n ** 0.5 if n > 1 else 0:.1%}, gagnants {sum(x > 0 for x in xs) / n:.0%}, "
            f"sans les 3 meilleurs {no3:+.1%}, vidés {sum(r['reason'].startswith('pool vidé') for r in rs)}")


def write_status(state, out_dir, live):
    lines = [f"# Memecoins papier (façon @savipww) — {datetime.now(timezone.utc):%d/%m %H:%M} UTC", "",
             f"Cadran du jour : {state['dial']['cadran']:.2f} {state['dial']['verts']}",
             f"Dernier cycle : {state['last_universe']} tokens passent le filtre, {state['last_ranked']} classés", ""]
    for b in state["books"].values():
        lines += [f"## {b['name']}", f"- caisse {b['cash']:.2f} $, valeur {equity(b, live):.2f} $ (départ {b['start']:.0f} $), "
                  f"{len(b['open'])} positions ouvertes", f"- {stats(b['closed'])}", ""]
    lines.append("Verdict prévu : " + RULE["verdict"])
    (out_dir / "status.md").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(Path(__file__).resolve().parent / "data"))
    ap.add_argument("--bank", type=float, default=10000.0)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    out_dir = Path(args.dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rule_p = out_dir / "regle_memes.json"
    if not rule_p.exists():
        rule_p.write_text(json.dumps(dict(RULE, debut=datetime.now(timezone.utc).isoformat()), ensure_ascii=False, indent=1))
    st_p = out_dir / "state.json"
    if st_p.exists():
        state = json.loads(st_p.read_text())
    else:
        state = {"books": {k: {"name": k, "cash": args.bank, "start": args.bank, "cash_ref": args.bank, "open": {},
                               "closed": []} for k in ("classement", "sans_cadran", "temoin")}}
    while True:
        t0 = time.time()
        try:
            cycle(state, out_dir, t0)
        except Exception as exc:
            with (out_dir / "erreurs.log").open("a") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat()} {exc!r}\n")
        if args.once:
            break
        time.sleep(max(30, RULE["cycle_s"] - (time.time() - t0)))


if __name__ == "__main__":
    main()
