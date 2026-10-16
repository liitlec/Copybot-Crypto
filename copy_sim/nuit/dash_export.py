"""Exporte tous les trades papier du test scalp gRPC (règles A à F et leurs comparaisons) en un seul fichier JSON
de lignes, lu par la page de suivi : data_grpc/dash_trades.json. Lecture seule."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from copysim.scalpgrpc import run_once  # noqa: E402

# nom de la série dans le rapport -> identifiant court
SERIES = [
    ("B confirmé", "B"), ("A brut", "A"), ("C :", "C"), ("B sur les mêmes lancements que C", "B_C"),
    ("E :", "E"), ("B sur les mêmes lancements que E", "B_E"), ("D :", "D"), ("F :", "F"),
    ("D sur les mêmes lancements que F", "D_F"), ("même sélection, revente à 60 s", "D_60"),
    ("tous les lancements, sortie C", "TOUS_C"),
]


def main():
    data = ROOT / "data_grpc"
    out = run_once(data / "pumpfun.jsonl", float((data / "START").read_text()))
    rows = []
    for name, trades in out.items():
        sid = next((s for prefix, s in SERIES if name.startswith(prefix)), None)
        if sid is None:
            continue
        for bt, mint, ret in trades:
            if ret is None:
                continue
            rows.append({"serie": sid, "heure": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(bt)),
                         "token": mint[:8], "rendement": round(ret, 5)})
    rows.sort(key=lambda r: (r["heure"], r["serie"]))
    p = data / "dash_trades.json"
    p.write_text(json.dumps(rows, separators=(",", ":")), encoding="utf-8")
    print(p, len(rows), "lignes", p.stat().st_size // 1024, "Ko")


if __name__ == "__main__":
    main()
