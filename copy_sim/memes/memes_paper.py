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
- pas d'achat d'un token qui remplit déjà la condition de sortie, ni d'un token revendu dans les 24 h par la même caisse ;
- sortie : volume des 6 dernières heures < 20 % de la normale (volume 24 h / 4), vérifié toutes les 5 min ; pool
  disparu ou liquidité < 1 000 $ = vidé, compté à la valeur de revente réelle (souvent proche de −100 %) ;
- trois caisses séparées : « classement » (règles du post, cadran compris), « sans_cadran » (mêmes choix tous les jours,
  pour juger le cadran) et « temoin » (à chaque entrée de « sans_cadran », un token tiré au hasard parmi ceux qui
  passent le filtre, même taille, même sortie). Si le classement ne bat pas le témoin, il ne sert à rien.
- deux caisses au rythme du post (une décision par jour à 06:00 New York, cadran compris) : « juge » = une IA (Claude,
  tâche planifiée) lit les 10 premiers candidats du jour (candidats_jour.json) et en choisit un ou aucun selon
  memes/juge/CONSIGNE.md, son choix est publié dans memes/juge/AAAA-MM-JJ.json sur la branche du dépôt et acheté au
  cycle suivant (accepté jusqu'à 10:00 New York, uniquement parmi les candidats du jour) ; « un_par_jour » = le
  premier du classement à 06:00, sans IA, pour juger ce que l'IA apporte. Même taille, même sortie.
Différences assumées avec le post : pas de Kelly (pas d'avantage connu à mettre dedans), Solana seulement ; les
trois premières caisses achètent à chaque cycle (jusqu'à 10 positions) pour accumuler des trades plus vite.

Usage : python3 memes_paper.py [--dir DOSSIER] [--once] [--bank 10000]"""
import argparse
import json
import random
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

GT = "https://api.geckoterminal.com/api/v2/networks/solana"
NY = ZoneInfo("America/New_York")
JUGE_URL = ("https://raw.githubusercontent.com/liitlec/Copybot-Crypto/claude/polymarket-weather-sigma-resolution-olv0bs/"
            "copy_sim/memes/juge/{date}.json")
BOOKS = ("classement", "sans_cadran", "temoin", "juge", "un_par_jour", "auto", "ia", "ia_filtre")
UA = {"Accept": "application/json", "User-Agent": "memes-paper/1.0 (read-only research)"}
RULE = {
    "nom": "memecoins façon @savipww, papier",
    "age_min_s": 15 * 60, "age_max_s": 72 * 3600, "liq_min": 12_000, "vol24_min": 40_000,
    "mcap_min": 60_000, "mcap_max": 8_000_000,
    "ticket_part": 0.06, "plafond_liquidite": 0.02, "frais": 0.0045, "frais_min": 0.95,
    "sortie_ratio_volume": 0.20, "vide_liquidite": 1_000, "max_positions": 10, "cycle_s": 300, "suivi_s": 15,
    "cadran_min": 0.50, "holders_cache_s": 3600, "filtre_detenteurs_min": 300, "filtre_top10_max": 50, "decisions_ny": ["02:00", "06:00", "10:00", "14:00", "18:00", "22:00"], "juge_delai_h": 3, "candidats_max": 10,
    "verdict": "après au moins 100 trades fermés : gagnant seulement si la moyenne dépasse 2 fois sa marge d'erreur, "
               "reste positive sans les 3 meilleurs trades ET bat le témoin tiré au hasard ; le cadran n'est utile que si « classement » bat « sans_cadran » ; l'IA n'est utile que si « juge » bat « un_par_jour »",
}
_last_call = [0.0]
LOCK = threading.Lock()   # le cycle, le suivi GeckoTerminal et le gardien gRPC ne touchent pas les caisses en même temps
LAST_GT = {}              # pool -> derniers attributs GeckoTerminal (prix de la cotation en dollars, liquidité…)
FLUX = [None]             # suivi des prix en direct par gRPC (flux.py), s'il est configuré


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
# Sources de l'univers. Les trois caisses du post gardent celui du post (nouveaux pools + tendance, « _post ») ; les
# autres caisses et la collecte voient en plus les pools les plus actifs sur 24 h (volume, transactions, PumpSwap,
# Raydium), ajoutés le 01/11 parce que l'univers du post ne laissait passer qu'une dizaine de tokens.
SOURCES = (("new_pools", 5, True), ("trending_pools", 3, True),
           ("pools?sort=h24_volume_usd_desc", 8, False), ("pools?sort=h24_tx_count_desc", 4, False),
           ("dexes/pumpswap/pools?sort=h24_volume_usd_desc", 2, False),
           ("dexes/raydium/pools?sort=h24_volume_usd_desc", 2, False))


def pools_universe():
    out = {}
    for path, pages, post in SOURCES:
        for page in range(1, pages + 1):
            try:
                d = get(f"{GT}/{path}{'&' if '?' in path else '?'}page={page}")
            except Exception:
                continue
            for p in d.get("data", []):
                a = p["attributes"]
                token = p["relationships"]["base_token"]["data"]["id"].split("_", 1)[1]
                prev = out.get(token)
                if prev is None or (fnum(a["reserve_in_usd"]) or 0) > (fnum(prev["reserve_in_usd"]) or 0):
                    out[token] = dict(a, pool=a["address"], token=token, _post=post or bool(prev and prev["_post"]))
                elif post:
                    prev["_post"] = True
                LAST_GT[a["address"]] = a
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


def holders(token, cache, now, full=False):
    """Nombre de détenteurs (GeckoTerminal, mis en cache 1 h) ; full=True renvoie aussi la sécurité du token : part des
    10 plus gros détenteurs (en %) et autorisations de création / gel encore actives."""
    c = cache.get(token)
    if not (c and now - c["t"] < RULE["holders_cache_s"] and (not full or "top10" in c)):
        try:
            a = get(f"{GT}/tokens/{token}/info")["data"]["attributes"]
            h = a.get("holders") or {}
            c = {"t": now, "n": h.get("count"), "top10": fnum((h.get("distribution_percentage") or {}).get("top_10")),
                 "mint": a.get("mint_authority"), "freeze": a.get("freeze_authority")}
        except Exception:
            c = {"t": now, "n": None, "top10": None, "mint": None, "freeze": None}
        cache[token] = c
    return c if full else c["n"]


def securite(token, cache, now):
    """Filtre anti-pièges de la caisse « ia_filtre » (ajouté le 01/11 après trois effondrements : USDF −100 %, Kim −95 %,
    SA −77 %). Renvoie None si le token passe, sinon la raison du refus."""
    c = holders(token, cache, now, full=True)
    if c["mint"] == "yes" or c["freeze"] == "yes":
        return "autorisation de création ou de gel encore active"
    if not c["n"] or c["n"] < RULE["filtre_detenteurs_min"]:
        return f"trop peu de détenteurs ({c['n']})"
    if c["top10"] is None or c["top10"] > RULE["filtre_top10_max"]:
        return f"10 plus gros détenteurs à {c['top10']} %"
    return None


def pools_now(addresses):
    res = {}
    for i in range(0, len(addresses), 30):
        try:
            d = get(f"{GT}/pools/multi/{','.join(addresses[i:i + 30])}")
        except Exception:
            continue
        for p in d.get("data", []):
            res[p["attributes"]["address"]] = p["attributes"]
    LAST_GT.update(res)
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
        # position achetée pendant ce cycle (pas encore de cotation relevée) : comptée à son prix d'achat
        val += p["qty"] * (fnum(a["base_token_price_usd"]) or 0) if a else p["dollars"]
    return val


def suivie(p):
    """Position à sortie par règle (stop, objectif, durée) : son prix est suivi toutes les SUIVI_S secondes."""
    return bool(p.get("sortie_ia") or p.get("sortie"))


def sortie_regle(b, token, p, a, now, log):
    """Sortie des positions à règle (caisses « ia », « juge » avec sa sortie, « auto ») ; False si la position suit
    la sortie du post (volume essoufflé), traitée par le cycle de 5 min."""
    if p.get("sortie_ia"):  # sortie de la version de règle sous laquelle la position a été achetée
        import apprend
        x = (fnum(a["base_token_price_usd"]) or 0) / p["px_in"] - 1
        p["pic"] = max(p.get("pic", 0.0), x)
        v24, v6 = fnum(a["volume_usd"]["h24"]) or 0, fnum(a["volume_usd"]["h6"]) or 0
        why = apprend.sortir_ia(p["sortie_ia"], x, p["pic"], (now - p["t"]) / 3600,
                                v24 > 0 and v6 / (v24 / 4) < RULE["sortie_ratio_volume"])
        if why:
            close_pos(b, token, a, now, f"{p['sortie_ia'].get('nom') or 'IA v%d' % p['sortie_ia']['version']} : {why}", log)
        return True
    rule = p.get("sortie")
    if rule:  # caisse « auto »
        x = (fnum(a["base_token_price_usd"]) or 0) / p["px_in"] - 1
        if x <= rule["stop"] or x >= rule["objectif"] or now - p["t"] >= rule["duree_max_h"] * 3600:
            close_pos(b, token, a, now, f"règle auto : {x:+.0%} après {(now - p['t']) / 60:.0f} min", log)
        return True
    return False


def surveiller(state, out_dir, now):
    """Entre deux cycles : relève le prix des positions à règle (un seul appel GeckoTerminal pour toutes) et applique
    leurs stops, objectifs et durées au plus tard SUIVI_S secondes après le franchissement (au lieu de 5 min)."""
    pos = [(b, t, p) for b in state["books"].values() for t, p in b["open"].items() if suivie(p)]
    if not pos:
        return
    live = pools_now(sorted({p["pool"] for _, _, p in pos}))

    def log(rec):
        with (out_dir / "trades.jsonl").open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    n = sum(len(b["closed"]) for b in state["books"].values())
    for b, token, p in pos:
        a = live.get(p["pool"])
        if a is not None and token in b["open"]:  # pool absent de la réponse : le cycle de 5 min tranchera
            sortie_regle(b, token, p, a, now, log)
    if sum(len(b["closed"]) for b in state["books"].values()) != n:
        (out_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")


def pools_suivis(state):
    return {p["pool"]: token for b in state["books"].values() for token, p in b["open"].items() if suivie(p)}


def gardien(state, out_dir):
    """Fil de fond : chaque seconde, applique les stops, objectifs et stops suiveurs des positions à règle au prix
    gRPC le plus récent (moins de 20 s), converti en dollars avec le prix de la cotation relevé par GeckoTerminal."""
    def log(rec):
        with (out_dir / "trades.jsonl").open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    while True:
        time.sleep(1)
        fx = FLUX[0]
        if fx is None or not fx.prix:
            continue
        try:
            with LOCK:
                now = time.time()
                n = sum(len(b["closed"]) for b in state["books"].values())
                for b in state["books"].values():
                    for token, p in list(b["open"].items()):
                        pr, g = fx.prix.get(p["pool"]), LAST_GT.get(p["pool"])
                        if not suivie(p) or not pr or now - pr[0] > 20 or not g:
                            continue
                        q, ref = fnum(g.get("quote_token_price_usd")), fnum(g.get("base_token_price_usd"))
                        usd = pr[1] * (q or 0)
                        if not usd or (ref and not 0.2 * ref <= usd <= 5 * ref):  # cotation mal appariée : ignoré
                            continue
                        sortie_regle(b, token, p, dict(g, base_token_price_usd=str(usd)), now, log)
                if sum(len(b["closed"]) for b in state["books"].values()) != n:
                    (out_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
                    fx.suivre(pools_suivis(state))
        except Exception as exc:
            with (out_dir / "erreurs.log").open("a") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat()} gardien {exc!r}\n")


# ------------------------------------------------------------------ boucle
def apprentissage(state, out_dir, now):
    """Caisse « auto » : règle réapprise toutes les heures (apprend.py), sur le passé seulement. Appelé hors du verrou
    par la boucle principale (peut durer quelques minutes) ; ne touche à aucune caisse."""
    hour = datetime.now(timezone.utc).strftime("%Y-%m-%d %H")
    if state.get("auto_heure") != hour:
        state["auto_heure"] = hour
        try:
            import apprend
            state["auto"] = apprend.apprendre(out_dir, get, now)
        except Exception as exc:
            state["auto"] = {"t": now, "regle": None, "raison": f"erreur : {exc!r}"[:200]}
        try:
            apprend.resultats_candidats(out_dir, get, now)
        except Exception as exc:
            with (out_dir / "erreurs.log").open("a") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat()} resultats_candidats {exc!r}\n")
        with (out_dir / "apprentissage.jsonl").open("a") as f:
            f.write(json.dumps(state["auto"], ensure_ascii=False) + "\n")


def cycle(state, out_dir, now, avec_apprentissage=True):
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
    if avec_apprentissage:
        apprentissage(state, out_dir, now)
    # 1. sorties
    held ={p["pool"] for b in state["books"].values() for p in b["open"].values()}
    live = pools_now(sorted(held))
    for b in state["books"].values():
        for token, p in list(b["open"].items()):
            a = live.get(p["pool"])
            if a is None or (fnum(a["reserve_in_usd"]) or 0) < RULE["vide_liquidite"]:
                close_pos(b, token, a, now, "pool vidé ou disparu", log)
                continue
            if sortie_regle(b, token, p, a, now, log):
                continue
            v24, v6 = fnum(a["volume_usd"]["h24"]) or 0, fnum(a["volume_usd"]["h6"]) or 0
            if v24 > 0 and v6 / (v24 / 4) < RULE["sortie_ratio_volume"]:
                close_pos(b, token, a, now, f"volume 6 h à {v6 / (v24 / 4):.0%} de la normale", log)
    # 2. candidats
    uni = [a for a in pools_universe() if passes(a, now)]
    # Classement. Le nombre de détenteurs de GeckoTerminal n'est rafraîchi que toutes les 1 à 19 h : on mesure donc la
    # croissance des détenteurs sur la dernière heure par les portefeuilles distincts acheteurs moins vendeurs (donnée en
    # continu), rapportés au nombre de détenteurs, et on la compare à la variation de prix sur la même heure.
    # Un token qui remplit déjà la condition de sortie (volume 6 h < 20 % de la normale) n'est jamais acheté : la règle
    # RISK le revendrait au cycle suivant. Un token revendu ne peut pas être racheté par la même caisse pendant 24 h.
    def fading(a):
        v24, v6 = fnum(a["volume_usd"]["h24"]) or 0, fnum(a["volume_usd"]["h6"]) or 0
        return v24 <= 0 or v6 / (v24 / 4) < RULE["sortie_ratio_volume"]
    uni_all = uni
    uni = [a for a in uni if not fading(a)]
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
    ranked_post = [r for r in ranked if r[1].get("_post")]   # univers du post, pour ses trois caisses
    uni_post = [a for a in uni if a.get("_post")]
    # 2 bis. collecte : chaque token qui passe le filtre, à chaque cycle, pour chercher plus tard une meilleure règle
    #        d'entrée et de sortie sur des données qu'aucune règle n'a encore vues (jamais utilisé pour trader ici).
    scores = {a["token"]: (r, hg, pg) for r, a, hg, pg in ranked}
    recs = []
    with (out_dir / "univers.jsonl").open("a") as f:
        for a in uni_all:
            r, hg, pg = scores.get(a["token"], (None, None, None))
            rec = dict(dossier(r or 0.0, a, hg, pg, None, state.get("hcache", {}).get(a["token"], {}).get("n")),
                       t=round(now), classe=r is not None, essouffle=fading(a), univers_post=bool(a.get("_post")))
            recs.append((rec, a))
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
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
    if ranked_post:
        for name, mult in (("classement", dial_v if dial_v >= RULE["cadran_min"] else 0), ("sans_cadran", 1.0)):
            if mult <= 0:
                continue
            bk = books[name]
            recent = {r["token"] for r in bk["closed"] if now - r["t_out"] < 24 * 3600}
            pick = next((r for r in ranked_post if r[1]["token"] not in bk["open"] and r[1]["token"] not in recent), None)
            if pick and enter(bk, pick[1], mult, {"score": round(pick[0], 4), "detenteurs": pick[2], "prix": pick[3]}) \
                    and name == "sans_cadran":
                recent_t = {r["token"] for r in books["temoin"]["closed"] if now - r["t_out"] < 24 * 3600}
                pool = [x for x in uni_post if x["token"] not in books["temoin"]["open"] and x["token"] not in recent_t]
                if pool:
                    enter(books["temoin"], random.choice(pool), 1.0, {"hasard": True})
    # 3 bis. caisse « auto » : un achat par cycle parmi les candidats qui passent la règle du jour
    rule = (state.get("auto") or {}).get("regle")
    if rule:
        import apprend
        bk = books["auto"]
        recent = {r["token"] for r in bk["closed"] if now - r["t_out"] < 24 * 3600}
        ok = sorted((x for x in recs if apprend.entre(rule, x[0]) and x[1]["token"] not in bk["open"]
                     and x[1]["token"] not in recent), key=lambda x: -(x[0]["score"] or 0))
        if ok and enter(bk, ok[0][1], 1.0, {"regle": rule}):
            bk["open"][ok[0][1]["token"]]["sortie"] = rule
    # 3 ter. caisse « ia » : règle de l'IA chercheuse, relue à chaque cycle (la dernière règle valide reste en vigueur)
    try:
        import apprend
        new = apprend.lire_regle_ia(local=out_dir / "ia_regle.json")
    except Exception:
        new = None
    if new and new["version"] != (state.get("ia") or {}).get("version"):
        state["ia"] = new
        with (out_dir / "ia_regles.jsonl").open("a") as f:
            f.write(json.dumps(dict(new, t=now), ensure_ascii=False) + "\n")
    ia = state.get("ia")
    if ia and not ia["pause"]:
        bk = books["ia"]
        recent = {r["token"] for r in bk["closed"] if now - r["t_out"] < 24 * 3600}
        ok = [x for x in recs if apprend.entre_ia(ia, x[0]) and x[1]["token"] not in bk["open"]
              and x[1]["token"] not in recent]
        ok.sort(key=lambda x: (apprend.champ(x[0], ia["tri"]) or 0) * (-1 if ia["tri_desc"] else 1))
        if ok and len(bk["open"]) < ia["max_positions"] and enter(bk, ok[0][1], 1.0, {"ia_version": ia["version"]}):
            bk["open"][ok[0][1]["token"]]["sortie_ia"] = ia
        # caisse « ia_filtre » : la même règle, mais seulement des tokens qui passent le filtre anti-pièges
        bf = books["ia_filtre"]
        recent_f = {r["token"] for r in bf["closed"] if now - r["t_out"] < 24 * 3600}
        refus = state.setdefault("filtre_refus", [])
        ok_f = [x for x in recs if apprend.entre_ia(ia, x[0]) and x[1]["token"] not in bf["open"]
                and x[1]["token"] not in recent_f]
        ok_f.sort(key=lambda x: (apprend.champ(x[0], ia["tri"]) or 0) * (-1 if ia["tri_desc"] else 1))
        for rec, a in ok_f:
            if len(bf["open"]) >= ia["max_positions"]:
                break
            why = securite(a["token"], state.setdefault("hcache", {}), now)
            if why:
                refus.append({"t": round(now), "token": a["token"], "nom": a.get("name"), "raison": why})
                del refus[:-50]
                continue
            if enter(bf, a, 1.0, {"ia_version": ia["version"], "filtre": "ok"}):
                bf["open"][a["token"]]["sortie_ia"] = ia
            break
    # 4. caisses « juge » (IA) et « un_par_jour » (sans IA) : une décision par créneau de 4 h (heure de New York) ;
    #    le post n'en prenait qu'une par jour à 06:00, l'utilisateur a voulu une IA qui ajuste plus souvent
    ny = datetime.fromtimestamp(now, NY)
    day, hm = ny.strftime("%Y-%m-%d"), ny.strftime("%H:%M")
    daily_mult = dial_v if dial_v >= RULE["cadran_min"] else 0
    slot = max((h for h in RULE["decisions_ny"] if h <= hm), default=None)
    key = f"{day}_{slot[:2]}" if slot else None
    if key and state.get("creneau") != key:
        state["creneau"] = key
        snap = [dossier(r, a, hg, pg, i + 1, state.setdefault("hcache", {}).get(a["token"], {}).get("n"))
                for i, (r, a, hg, pg) in enumerate(ranked[:RULE["candidats_max"]])]
        doc = json.dumps({"date": day, "creneau": key, "t": now, "cadran": dial_v,
                          "cadran_verts": state["dial"]["verts"], "candidats": snap}, ensure_ascii=False, indent=1)
        (out_dir / "candidats_jour.json").write_text(doc, encoding="utf-8")
        (out_dir / "candidats").mkdir(exist_ok=True)
        (out_dir / "candidats" / f"{key}.json").write_text(doc, encoding="utf-8")  # archive : l'IA apprend de ses choix
        state["candidats_jour"] = {c["token"]: c["pool"] for c in snap}
        bk = books["un_par_jour"]
        recent = {r["token"] for r in bk["closed"] if now - r["t_out"] < 24 * 3600}
        pick = next((r for r in ranked if r[1]["token"] not in bk["open"] and r[1]["token"] not in recent), None)
        if not daily_mult:
            log({"event": "jour", "book": "un_par_jour", "creneau": key, "rien": "cadran sous 0,5"})
        elif not pick:
            log({"event": "jour", "book": "un_par_jour", "creneau": key, "rien": "aucun candidat classé"})
        else:
            enter(bk, pick[1], daily_mult, {"score": round(pick[0], 4), "detenteurs": pick[2], "prix": pick[3]})
    if key and state.get("creneau") == key and state.get("juge_fait") != key:
        t_slot = datetime.strptime(f"{day} {slot}", "%Y-%m-%d %H:%M").replace(tzinfo=NY).timestamp()
        if now - t_slot > RULE["juge_delai_h"] * 3600:
            state["juge_fait"] = key
            log({"event": "jour", "book": "juge", "creneau": key, "rien": "pas de réponse de l'IA à temps"})
        else:
            try:  # déposé sur le VPS par l'IA (serveur.py), sinon publié sur la branche GitHub
                local = out_dir / f"juge_{key}.json"
                if local.exists():
                    verdict = json.loads(local.read_text())
                else:
                    with urllib.request.urlopen(urllib.request.Request(JUGE_URL.format(date=key), headers=UA),
                                                timeout=20) as r:
                        verdict = json.load(r)
            except Exception:
                verdict = None  # pas encore publié
            if verdict is not None and verdict.get("creneau") == key:
                state["juge_fait"] = key
                tok = verdict.get("choix")
                bk = books["juge"]
                pool = state.get("candidats_jour", {}).get(tok)
                if not tok or not daily_mult or pool is None or tok in bk["open"]:
                    why = ("aucun" if not tok else "cadran sous 0,5" if not daily_mult else
                           "hors des candidats du créneau" if pool is None else "déjà détenu")
                    log({"event": "jour", "book": "juge", "creneau": key, "rien": why, "ia": verdict})
                else:
                    a = pools_now([pool]).get(pool)
                    if a is None or (fnum(a.get("reserve_in_usd")) or 0) < RULE["vide_liquidite"]:
                        log({"event": "jour", "book": "juge", "creneau": key, "rien": "pool introuvable à l'achat",
                             "ia": verdict})
                    elif enter(bk, dict(a, pool=pool, token=tok), daily_mult,
                               {"ia_proba": verdict.get("proba"), "ia_raison": str(verdict.get("raison", ""))[:300]}):
                        # sortie choisie par l'IA (bornée comme celle de l'IA chercheuse), sinon celle du post
                        try:
                            import apprend
                            sx = apprend.regle_ia({"version": 0, "entree": {"conditions": []},
                                                   "sortie": verdict.get("sortie")}) if verdict.get("sortie") else None
                        except Exception:
                            sx = None
                        if sx:
                            bk["open"][tok]["sortie_ia"] = dict(sx, nom="juge")
    # caisse de référence pour la taille : valeur du compte au début de chaque jour (pas de réinvestissement intra-jour)
    for b in state["books"].values():
        if b.get("ref_day") != state["dial"]["date"]:
            b["cash_ref"], b["ref_day"] = equity(b, live), state["dial"]["date"]
    state["last_cycle"] = now
    state["last_universe"] = len(uni)
    state["last_universe_post"] = len(uni_post)
    state["last_ranked"] = len(ranked)
    write_status(state, out_dir, live)


def dossier(score, a, hg, pg, rank, n_holders):
    """Ce que l'IA juge reçoit pour un candidat : chiffres seulement (le nom est une donnée, jamais une consigne)."""
    age_h = None
    try:
        age_h = round((time.time() - datetime.fromisoformat(a["pool_created_at"].replace("Z", "+00:00")).timestamp()) / 3600, 1)
    except Exception:
        pass
    keep = ("m5", "m15", "m30", "h1", "h6", "h24")
    return {"rang": rank, "token": a["token"], "pool": a["pool"], "nom": a.get("name"), "age_h": age_h,
            "liquidite": fnum(a.get("reserve_in_usd")), "mcap": fnum(a.get("market_cap_usd")) or fnum(a.get("fdv_usd")),
            "prix": fnum(a.get("base_token_price_usd")), "detenteurs": n_holders,
            "volume": {k: fnum(v) for k, v in a.get("volume_usd", {}).items() if k in keep},
            "variation_prix_pct": {k: fnum(v) for k, v in a.get("price_change_percentage", {}).items() if k in keep},
            "transactions": {k: v for k, v in a.get("transactions", {}).items() if k in keep},
            "croissance_detenteurs_1h": hg, "variation_prix_1h": pg, "score": round(score, 4)}


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
             f"Dernier cycle : {state['last_universe']} tokens passent le filtre (dont {state.get('last_universe_post', '?')} "
             f"dans l'univers du post), {state['last_ranked']} classés", ""]
    fx = FLUX[0]
    lines += ["Prix en direct (gRPC) : " + ("non configuré, suivi par GeckoTerminal toutes les 15 s" if fx is None else
              f"{'connecté' if fx.actif else 'déconnecté'}, {len(fx.pools)} pools suivis, "
              f"{sum(1 for t, *_ in fx.prix.values() if time.time() - t < 60)} prix reçus dans la dernière minute"), ""]
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
    juge_p = out_dir / "regle_juge.json"  # caisses ajoutées le 30/10 : leurs règles sont figées à leur premier lancement
    if not juge_p.exists():
        juge_p.write_text(json.dumps({k: RULE[k] for k in ("decisions_ny", "juge_delai_h", "candidats_max", "verdict")} |
                                     {"juge_url": JUGE_URL, "debut": datetime.now(timezone.utc).isoformat()},
                                     ensure_ascii=False, indent=1))
    st_p = out_dir / "state.json"
    if st_p.exists():
        state = json.loads(st_p.read_text())
    else:
        state = {"books": {}}
    for k in BOOKS:  # les caisses ajoutées après le premier lancement démarrent avec la même mise
        state["books"].setdefault(k, {"name": k, "cash": args.bank, "start": args.bank, "cash_ref": args.bank,
                                      "open": {}, "closed": []})
    if not args.once:  # prix en direct par gRPC si grpc.env (GRPC_ENDPOINT, GRPC_TOKEN) est à côté du script
        try:
            import flux

            def flog(m):
                with (out_dir / "flux.log").open("a") as f:
                    f.write(f"{datetime.now(timezone.utc).isoformat()} {m}\n")
            FLUX[0] = flux.Flux.depuis_fichier(Path(__file__).resolve().parent / "grpc.env", log=flog)
        except Exception as exc:
            with (out_dir / "erreurs.log").open("a") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat()} flux {exc!r}\n")
        threading.Thread(target=gardien, args=(state, out_dir), daemon=True).start()
    while True:
        t0 = time.time()
        try:
            apprentissage(state, out_dir, t0)
            with LOCK:
                cycle(state, out_dir, t0, avec_apprentissage=False)
                if FLUX[0]:
                    FLUX[0].suivre(pools_suivis(state))
        except Exception as exc:
            with (out_dir / "erreurs.log").open("a") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat()} {exc!r}\n")
        if args.once:
            break
        while time.time() - t0 < RULE["cycle_s"] - RULE["suivi_s"]:  # suivi des positions à règle entre deux cycles
            time.sleep(RULE["suivi_s"])
            try:
                with LOCK:
                    surveiller(state, out_dir, time.time())
                    if FLUX[0]:
                        FLUX[0].suivre(pools_suivis(state))
            except Exception as exc:
                with (out_dir / "erreurs.log").open("a") as f:
                    f.write(f"{datetime.now(timezone.utc).isoformat()} suivi {exc!r}\n")
        time.sleep(max(1.0, RULE["cycle_s"] - (time.time() - t0)))


if __name__ == "__main__":
    main()
