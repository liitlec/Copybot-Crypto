"""Collecteur pour l'analyse structurée du scalp pump.fun (lecture seule).

Pour chaque NOUVELLE création enregistrée par le hub (data_grpc/pumpfun.jsonl), au moment du lancement :
- nom, symbole, lien des métadonnées (décodés de l'instruction de création pump.fun) ;
- contenu des métadonnées : présence d'un compte X, d'un Telegram, d'un site, longueur de la description ;
- état du wallet du créateur : nombre de transactions (plafonné à 1000), âge du wallet, solde SOL.
Ces infos n'existent qu'au moment du lancement (le wallet du créateur change ensuite) : à collecter en direct.
Sortie : data_grpc/pump_enrich.jsonl (une ligne par création)."""
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
from copysim.grpchub import B58  # noqa: E402
from copysim.net import SolanaRPC  # noqa: E402

PUMP = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
SRC, OUT = ROOT / "data_grpc" / "pumpfun.jsonl", ROOT / "data_grpc" / "pump_enrich.jsonl"
rpc = SolanaRPC(f"https://solana-mainnet.core.chainstack.com/{os.getenv('GRPC_TOKEN')}")
http = requests.Session()
lock = threading.Lock()
stats = {"ok": 0, "err": 0}


def b58decode(s: str) -> bytes:
    n = 0
    for ch in s:
        n = n * 58 + B58.index(ch)
    b = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return b"\0" * (len(s) - len(s.lstrip("1"))) + b


def decode_create(data: bytes):
    p, out = 8, []
    for _ in range(3):
        n = int.from_bytes(data[p:p + 4], "little")
        if n > 400:
            return None
        out.append(data[p + 4:p + 4 + n].decode("utf-8", "replace"))
        p += 4 + n
    return out


# la passerelle de pump.fun sert ses fichiers tout de suite ; les publiques échouent la plupart du temps (testé)
GATEWAYS = ["https://pump.mypinata.cloud/ipfs/", "https://ipfs.io/ipfs/"]


def _get_json(uri: str):
    urls = [uri]
    if "/ipfs/" in uri:
        cid = uri.split("/ipfs/", 1)[1]
        urls = [g + cid for g in GATEWAYS]
    for u in urls:
        try:
            r = http.get(u, timeout=6, stream=True)
            if r.status_code == 200:
                return json.loads(r.raw.read(200_000, decode_content=True))
        except Exception:  # noqa: BLE001
            continue
    return None


def metadata(uri: str) -> dict:
    j = _get_json(uri)
    if j is None:  # pas encore publié sur IPFS : un second essai plus tard (les métadonnées ne changent pas)
        time.sleep(20)
        j = _get_json(uri)
    if not isinstance(j, dict):
        return {"ok": False}
    txt = lambda k: (j.get(k) or "") if isinstance(j.get(k), str) else ""
    ext = j.get("extensions") if isinstance(j.get("extensions"), dict) else {}
    tw = txt("twitter") or ext.get("twitter") or ""
    tg = txt("telegram") or ext.get("telegram") or ""
    web = txt("website") or ext.get("website") or ""
    return {"ok": True, "twitter": bool(tw), "twitter_url": tw[:120], "telegram": bool(tg), "website": bool(web),
            "website_url": web[:120], "desc_len": len(txt("description")), "image": bool(txt("image")),
            "created_on": txt("createdOn")[:60]}


def creator_state(w: str) -> dict:
    out = {}
    try:
        sigs = rpc.signatures(w, limit=1000)
        out["n_tx"] = len(sigs)
        times = [s["blockTime"] for s in sigs if s.get("blockTime")]
        out["age_h"] = round((time.time() - min(times)) / 3600, 2) if times and len(sigs) < 1000 else None
    except Exception:  # noqa: BLE001
        pass
    try:
        out["sol"] = rpc.call("getBalance", [w])["value"] / 1e9
    except Exception:  # noqa: BLE001
        pass
    return out


def enrich(c: dict) -> None:
    row = {"sig": c["sig"], "mint": c["mint"], "accs": c.get("accs"), "creator": c["signer"], "bt": c["bt"],
           "fetched": round(time.time(), 2)}
    row["creator_state"] = creator_state(c["signer"])  # d'abord : c'est l'état AU MOMENT du lancement qui compte
    try:
        tx = None
        for attempt in range(6):  # la transaction n'est lisible qu'une fois confirmée (~1 s)
            tx = rpc.call("getTransaction", [c["sig"], {"encoding": "json", "maxSupportedTransactionVersion": 1,
                                                        "commitment": "confirmed"}])
            if tx:
                break
            time.sleep(1.5)
        msg = tx["transaction"]["message"]
        keys = msg["accountKeys"] + tx["meta"]["loadedAddresses"]["writable"] + tx["meta"]["loadedAddresses"]["readonly"]
        for ix in msg["instructions"] + [i for g in tx["meta"]["innerInstructions"] for i in g["instructions"]]:
            if keys[ix["programIdIndex"]] == PUMP:
                d = decode_create(b58decode(ix["data"]))
                if d and d[2].startswith("http"):
                    row["name"], row["symbol"], row["uri"] = d
                    break
    except Exception as exc:  # noqa: BLE001
        row["tx_err"] = str(exc)[:80]
    if row.get("uri"):
        row["meta"] = metadata(row["uri"])
    with lock:
        with OUT.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        stats["ok" if "tx_err" not in row else "err"] += 1


def main() -> None:
    start = time.time()
    pool = ThreadPoolExecutor(max_workers=24)  # attentes réseau (confirmation, IPFS) : beaucoup de fils légers
    last = time.time()
    with SRC.open("r", encoding="utf-8") as fh:
        fh.seek(0, 2)  # seulement les nouvelles créations (état du créateur au moment du lancement)
        buf = ""
        while True:
            line = fh.readline()
            if not line:
                time.sleep(0.2)
                if SRC.stat().st_size < fh.tell():
                    fh.seek(0)
            else:
                buf += line
                if buf.endswith("\n"):
                    try:
                        r = json.loads(buf)
                    except ValueError:
                        r = None
                    buf = ""
                    if r and r.get("kind") == "create" and r["bt"] >= start - 30:
                        pool.submit(enrich, r)
            if time.time() - last > 60:
                last = time.time()
                print(time.strftime("%H:%M"), stats, "en attente", pool._work_queue.qsize(), flush=True)


if __name__ == "__main__":
    main()
