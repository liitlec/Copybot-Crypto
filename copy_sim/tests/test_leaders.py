import time

from test_copysim import W

from copysim import leaders as L
from copysim import net

REAL = "So11111111111111111111111111111111111111112"  # adresse valide (mint WSOL)


def test_address_validation():
    assert L.is_solana_address(REAL)
    assert L.is_solana_address("11111111111111111111111111111111")  # system program
    assert not L.is_solana_address(REAL[:-1] + "0")   # caractère hors base58
    assert not L.is_solana_address(REAL[:-3])           # tronquée
    assert not L.is_solana_address(W)                   # adresse factice des tests


def test_solanatracker_parsing(monkeypatch):
    monkeypatch.setattr(net, "get_json", lambda *a, **k: {"traders": [
        {"wallet": REAL, "identity": {"name": "Alice"}, "period": {"realized": 1234.5}},
        {"wallet": "pasbon", "identity": {"name": "Bob"}, "period": {"realized": 99}},
    ]})
    c = L.from_solanatracker("k")
    assert [(x.wallet, x.label, x.pnl) for x in c] == [(REAL, "Alice", 1234.5)]


def test_gecko_ranking(monkeypatch):
    A, B = REAL, "11111111111111111111111111111111"

    def fake(url, params=None, **k):
        if url.endswith("trending_pools"):
            return {"data": [{"attributes": {"address": "P1"}}, {"attributes": {"address": "P2"}}]}
        trades = [(A, "buy", 100), (A, "sell", 300), (B, "buy", 100), (B, "sell", 50)]
        return {"data": [{"attributes": {"tx_from_address": w, "kind": k_, "volume_in_usd": v}}
                         for w, k_, v in trades]}
    monkeypatch.setattr(net, "get_json", fake)
    c = L.from_gecko(sleep_s=0)
    assert c[0].wallet == A and c[0].pnl == 400 and c[1].pnl == -100


def test_filter_active():
    now = time.time()

    class R:
        def signatures(self, w, limit=1000):
            return {"act": [{"blockTime": now - 60}] * 10, "dead": [{"blockTime": now - 10 * 86400}],
                    "bot": [{"blockTime": now - 1}] * 1000}[w]
    cands = [L.Candidate(w, w, 0) for w in ("act", "dead", "bot")]
    kept = L.filter_active(R(), cands, log=lambda *a: None)
    assert [c.wallet for c in kept] == ["act"] and kept[0].trades == 10
