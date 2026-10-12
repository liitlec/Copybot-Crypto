"""Commande backtest complète avec RPC Solana et GeckoTerminal simulés (aucun réseau)."""
import json
import time

from test_copysim import MINT, W, tx

from copysim import __main__ as cli
from copysim import net
from copysim.config import LAMPORTS, WSOL


def test_backtest_cli(tmp_path, monkeypatch, capsys):
    now = int(time.time())
    t_buy, t_sell = now - 3600, now - 1800
    buy = tx(10.0, 9.0 - 5000 / LAMPORTS, None, 1_000_000_000)
    buy["blockTime"] = t_buy
    sell = tx(9.0, 10.5 - 5000 / LAMPORTS, 1_000_000_000, 0)
    sell["blockTime"] = t_sell
    txs = {"sigB": buy, "sigS": sell}

    def fake_post(self, payload):
        if isinstance(payload, list):
            return [{"id": p["id"], "result": txs[p["params"][0]]} for p in payload]
        if payload["method"] == "getSignaturesForAddress":
            return {"result": [{"signature": "sigS", "blockTime": t_sell, "err": None},
                               {"signature": "sigB", "blockTime": t_buy, "err": None}]}
        raise AssertionError(payload)

    def fake_get(url, params=None, **kw):
        if url.endswith(f"/tokens/{MINT}/pools"):
            return {"data": [{"attributes": {"address": "POOL", "reserve_in_usd": "50000"},
                              "relationships": {"base_token": {"data": {"id": f"solana_{MINT}"}},
                                                "quote_token": {"data": {"id": f"solana_{WSOL}"}}}}]}
        if "/pools/POOL/ohlcv/minute" in url:
            if params["before_timestamp"] < t_buy - 600:
                return {"data": {"attributes": {"ohlcv_list": []}}}
            rows = [[t, 0.001, 0.0011, 0.0009, 0.001, 1] for t in range(t_buy - 300 - t_buy % 60, t_sell - 120, 60)]
            rows += [[t, 0.0015, 0.0016, 0.0014, 0.0015, 1] for t in range(t_sell - 120 - t_sell % 60, now + 60, 60)]
            return {"data": {"attributes": {"ohlcv_list": sorted(rows, reverse=True)}}}
        raise AssertionError(url)

    monkeypatch.setattr(net.SolanaRPC, "_post", fake_post)
    monkeypatch.setattr(net, "get_json", fake_get)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CS_DATA_DIR", str(tmp_path / "data"))
    (tmp_path / "leaders.txt").write_text(f"# top 1\n{W}\n")
    cli.main(["backtest", "--leaders", "leaders.txt", "--days", "1", "--gecko-sleep", "0"])
    data = json.loads((tmp_path / "reports" / "backtest.json").read_text())
    neutral = data["results"]["neutral"]
    assert neutral["n_closed"] == 1 and neutral["win_rate"] == 1.0
    assert neutral["return"] > 0
    assert data["results"]["pessimistic"]["final_equity"] <= neutral["final_equity"]
    assert "Résultat propre des leaders" in capsys.readouterr().out
