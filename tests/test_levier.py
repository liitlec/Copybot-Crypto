from funding import levier


class Resp:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def test_verdict_seuils():
    assert levier.verdict(0.12, 0.05)[1] == 2
    assert levier.verdict(0.06, 0.05)[1] == 1
    assert levier.verdict(0.02, 0.05)[1] == 0
    assert levier.verdict(-0.01, 0.05)[1] == -1


def test_taux_emprunt(monkeypatch):
    aave = {"data": {"markets": [
        {"name": "AaveV3Arbitrum", "reserves": [
            {"underlyingToken": {"symbol": "USDC"}, "borrowInfo": {"apy": {"value": "0.20"}}},   # USDC bridge
            {"underlyingToken": {"symbol": "USDC"}, "borrowInfo": {"apy": {"value": "0.041"}}},  # USDC natif
            {"underlyingToken": {"symbol": "WETH"}, "borrowInfo": {"apy": {"value": "0.02"}}}]},
        {"name": "AaveV3EthereumHorizon", "reserves": [
            {"underlyingToken": {"symbol": "USDC"}, "borrowInfo": {"apy": {"value": "0.11"}}}]}]}}
    okx = {"data": [{"basic": [{"ccy": "USDT", "rate": "0.0001"}, {"ccy": "BTC", "rate": "0.00001"}]}]}
    monkeypatch.setattr(levier.requests, "post", lambda *a, **k: Resp(aave))
    monkeypatch.setattr(levier.requests, "get", lambda *a, **k: Resp(okx))
    r = levier.borrow_rates()
    assert r == {"Aave Arbitrum USDC": 0.041, "OKX USDT": 0.0001 * 365}
