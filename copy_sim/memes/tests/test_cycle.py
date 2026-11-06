"""Test hors ligne du cycle de memes_paper (06/11), sans réseau : 14 cycles simulés de 5 min avec de faux pools.
Vérifie les achats et ventes, les noms interdits, les relevés de transactions, les évolutions sur 30 min, le tournoi
(12 places, élimination, place morte, champs composés) et la page. Affiche « TEST OK » si tout passe.
Lancé par maj_auto.py avant toute mise à jour automatique ; à lancer aussi avant chaque commit :
    python3 tests/test_cycle.py /tmp/essai_memes"""
import json, os, random, sys, time, shutil, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SRC = Path(os.environ.get("MEMES_SRC") or Path(__file__).resolve().parents[1])
sys.path.insert(0, str(SRC))
import memes_paper as M
import apprend as A

OUT = Path(sys.argv[1])
shutil.rmtree(OUT, ignore_errors=True)
OUT.mkdir(parents=True)
random.seed(1)
T0 = time.time()
NOMS = ["XTEN", "PREDICT", "XTEN", "Alpha", "Bravo", "Charlie", "Delta", "Echo", "Fox"]
TOK = {f"T{i}{'x' * 38}": n for i, n in enumerate(NOMS)}
POOL = {t: f"P{t[1:]}" for t in TOK}
PX = {t: 0.001 for t in TOK}
APPELS = {"trades": 0, "info": 0, "multi": 0}
NOW = [T0]


def attrs(t):
    n = TOK[t]
    age = 6 * 3600
    tx = lambda b, s: {"buys": b, "sells": s, "buyers": b // 2, "sellers": s // 2}
    k = 1 + (NOW[0] - T0) / 3600  # acheteurs h1 qui montent au fil du temps
    return {"address": POOL[t], "name": f"{n} / SOL", "base_token_price_usd": str(PX[t]),
            "pool_created_at": datetime.fromtimestamp(NOW[0] - age, timezone.utc).isoformat().replace("+00:00", "Z"),
            "fdv_usd": "500000", "market_cap_usd": None, "reserve_in_usd": str(60000 * (1 + 0.1 * (NOW[0] - T0) / 1800)),
            "price_change_percentage": {"m5": "1", "m15": "1", "m30": "2", "h1": "-5", "h6": "10", "h24": "20"},
            "transactions": {"m5": tx(20, 5), "m15": tx(50, 10), "m30": tx(90, 20), "h1": tx(int(200 * k), 40),
                             "h6": tx(1000, 300), "h24": tx(4000, 1500)},
            "volume_usd": {"m5": "2000", "m15": "5000", "m30": "9000", "h1": "20000", "h6": "100000", "h24": "300000"}}


def fake_get(url, tries=4):
    if "/trades" in url:
        APPELS["trades"] += 1
        pool = url.split("/pools/")[1].split("/")[0]
        t = next(k for k, v in POOL.items() if v == pool)
        robot = TOK[t] in ("XTEN", "PREDICT")
        out = []
        for i in range(300):
            w = f"W{random.randint(0, 60 if robot else 250)}"
            out.append({"attributes": {"tx_from_address": w, "kind": random.choice(["buy", "sell"]),
                                       "volume_in_usd": str(700 if robot else random.lognormvariate(3, 1.5)),
                                       "block_timestamp": datetime.fromtimestamp(NOW[0] - i * 10, timezone.utc).isoformat()}})
        return {"data": out}
    if "/tokens/" in url and url.endswith("/info"):
        APPELS["info"] += 1
        return {"data": {"attributes": {"holders": {"count": 800, "distribution_percentage": {"top_10": "30"}},
                                        "mint_authority": "no", "freeze_authority": "no"}}}
    if "/pools/multi/" in url:
        APPELS["multi"] += 1
        ads = url.split("/pools/multi/")[1].split(",")
        return {"data": [{"attributes": attrs(t), "relationships": {"base_token": {"data": {"id": "solana_" + t}}}}
                         for t in TOK if POOL[t] in ads]}
    for path, pages, post in M.SOURCES:
        if path.split("?")[0] in url:
            if "page=1" not in url:
                return {"data": []}
            return {"data": [{"attributes": attrs(t), "relationships": {"base_token": {"data": {"id": "solana_" + t}}}}
                             for t in TOK]}
    raise RuntimeError("non simulé " + url)


def no_net(*a, **k):
    raise OSError("pas de réseau dans le test")


M.get = fake_get
urllib.request.urlopen = no_net
M.dial = lambda: {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "cadran": 0.75, "verts": 3, "donnees": {}}

# règle ia et 6 challengeuses
base = {"version": 7, "entree": {"conditions": [{"champ": "liquidite", "op": ">", "val": 1000}]},
        "classement": {"champ": "score", "ordre": "desc"}, "max_positions": 3,
        "sortie": {"stop": -0.25, "objectif": 0.5, "duree_max_h": 4}}
(OUT / "ia_regle.json").write_text(json.dumps(base))
def ch(i, extra_cond=None):
    r = json.loads(json.dumps(base))
    r["entree"]["conditions"].append({"champ": "liquidite", "op": ">", "val": 1000 + i})
    if extra_cond:
        r["entree"]["conditions"].append(extra_cond)
    return {"nom": f"idee{i}", "regle": r}
chal = [ch(1), ch(2), ch(3), ch(4, {"champ": "tx_part_aller_retour", "op": "<", "val": 0.6}),
        ch(5, {"champ": "evol_acheteurs_h1_30m", "op": ">", "val": 0.0}), ch(6)] + [ch(i) for i in range(7, 12)]
comp = ch(12, {"champ": "c_flux", "op": ">=", "val": 0.05})  # champ composé (06/11)
comp["regle"]["entree"]["composes"] = [{"nom": "c_flux", "a": "transactions.m5.buyers", "op": "/", "b": "transactions.h1.buyers"}]
comp["regle"]["classement"] = {"champ": "c_flux"}
chal.append(comp)
assert len(chal) == 12 and A.regle_ia(comp["regle"]) is not None
(OUT / "ia_challengeuses.json").write_text(json.dumps({"challengeuses": chal}))

state = {"books": {k: {"name": k, "cash": 10000.0, "start": 10000.0, "cash_ref": 10000.0, "open": {}, "closed": []}
                   for k in M.BOOKS}, "remise": M.REMISE, "correction": M.CORRECTION, "correction_2": M.CORRECTION_2}
M.NOMS_VIDES[0] = state.setdefault("noms_vides", {})
state["dial"] = dict(M.dial(), t=T0)
# places existantes : defi_1 perd (8 trades à −20 %, 1 h), defi_2 morte (25 h sans achat), defi_3 jeune et gagnante
old = lambda i: {"nom": f"vieille{i}", "cle": "ancienne", "regle": A.regle_ia(base), "debut": round(T0 - 3600)}
def bk(name, rets, t_in):
    return {"name": name, "cash": 10000.0, "start": 10000.0, "cash_ref": 10000.0, "open": {},
            "closed": [{"token": "z", "ret": r, "t_in": t_in, "t_out": t_in + 60, "dollars": 100, "proceeds": 100 * (1 + r),
                        "reason": "test", "pool": "z", "minutes": 1, "name": "z", "book": name} for r in rets]}
state["defis"] = {"defi_1": old(1), "defi_2": dict(old(2), debut=round(T0 - 25 * 3600)), "defi_3": old(3)}
state["books"]["defi_1"] = bk("defi_1", [-0.2] * 8, T0 - 3000)
state["books"]["defi_2"] = bk("defi_2", [], T0)
state["books"]["defi_3"] = bk("defi_3", [0.1, 0.2], T0 - 3000)

for c in range(14):  # 70 min de cycles de 5 min
    NOW[0] = T0 + c * 300
    for t in PX:
        PX[t] *= 1.01
    if c == 8:  # Bravo chute de 40 % : les caisses qui le détiennent doivent sortir sur leur stop
        PX[next(t for t, n in TOK.items() if n == "Bravo")] *= 0.6
    M.cycle(state, OUT, NOW[0], avec_apprentissage=False)
    json.dumps(state)  # l'état reste sérialisable
(OUT / "state.json").write_text(json.dumps(state))
print("appels", APPELS)

L = [json.loads(l) for l in (OUT / "trades.jsonl").read_text().splitlines()]
achats = [r for r in L if r.get("event") == "achat"]
ventes = [r for r in L if "ret" in r]
caisses = {r["book"] for r in achats}
U = [json.loads(l) for l in (OUT / "univers.jsonl").read_text().splitlines()]
verifs = {
    "aucune erreur": not (OUT / "erreurs.log").exists(),
    "achats ia": "ia" in caisses,
    "12 places remplies": all(f"defi_{i}" in state["defis"] for i in range(1, 13)),
    "achats dans 12 places": all(f"defi_{i}" in caisses for i in range(1, 13)),
    "XTEN/PREDICT jamais achetés": not any(A.nom_interdit(r.get("name")) for r in achats),
    "place perdante et place morte remplacées, place jeune gardée":
        state["defis"]["defi_1"]["nom"] == "idee1" and state["defis"]["defi_2"]["nom"] == "idee2"
        and state["defis"]["defi_3"]["nom"] == "vieille3",
    "ventes sur stop": any("stop" in r.get("reason", "") for r in ventes),
    "relevés de transactions": any(u.get("tx_portefeuilles") for u in U),
    "évolutions 30 min": any(u.get("evol_prix_30m") is not None for u in U),
    "page de suivi": (OUT / "suivi.html").exists() and (OUT / "suivi.html").stat().st_size > 5000,
    "champ composé utilisé": "defi_12" in caisses,
}
for k, v in verifs.items():
    print(("ok   " if v else "ÉCHEC"), k)
if all(verifs.values()):
    print("TEST OK")
else:
    sys.exit(1)
