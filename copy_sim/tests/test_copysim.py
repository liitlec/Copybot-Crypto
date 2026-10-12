import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from copysim.config import LAMPORTS, USDC, WSOL, Settings  # noqa: E402
from copysim.engine import CopyEngine  # noqa: E402
from copysim.prices import BacktestPrices, GeckoCandles  # noqa: E402
from copysim.report import leader_baseline, render, stats  # noqa: E402
from copysim.swaps import SwapEvent, convert_usd, fill_pre_balances, parse_enhanced, parse_swap  # noqa: E402

W = "LeaderWallet111111111111111111111111111111111"
MINT = "MemeMint11111111111111111111111111111111111"


def tb(idx, mint, owner, amount_raw, dec=6):
    return {"accountIndex": idx, "mint": mint, "owner": owner,
            "uiTokenAmount": {"amount": str(amount_raw), "decimals": dec}}


def tx(sol_pre, sol_post, pre_tok, post_tok, fee=5000, wsol=None, err=None, usdc=None, signer=True):
    pre_tb = [tb(1, MINT, W, pre_tok)] if pre_tok is not None else []
    post_tb = [tb(1, MINT, W, post_tok)] if post_tok is not None else []
    if wsol:
        pre_tb.append(tb(2, WSOL, W, wsol[0], 9))
        post_tb.append(tb(2, WSOL, W, wsol[1], 9))
    if usdc:
        pre_tb.append(tb(2, USDC, W, usdc[0], 6))
        post_tb.append(tb(2, USDC, W, usdc[1], 6))
    return {"slot": 1, "blockTime": 1_700_000_000,
            "transaction": {"signatures": ["sig1"], "message": {"accountKeys": [
                {"pubkey": W, "signer": signer}, {"pubkey": "ata"}, {"pubkey": "wsolata"}]}},
            "meta": {"err": err, "fee": fee, "preBalances": [int(sol_pre * LAMPORTS), 0, 0],
                     "postBalances": [int(sol_post * LAMPORTS), 0, 0],
                     "preTokenBalances": pre_tb, "postTokenBalances": post_tb}}


def test_parse_buy_excludes_network_fee():
    ev = parse_swap(tx(10.0, 8.0 - 5000 / LAMPORTS, None, 1_000_000_000), W)
    assert ev.side == "BUY" and ev.mint == MINT
    assert ev.sol_amount == pytest.approx(2.0) and ev.token_amount == pytest.approx(1000)
    assert ev.price_sol == pytest.approx(0.002) and ev.leader_pre_tokens == 0


def test_parse_sell_partial_and_wsol():
    # Vend la moitié ; produit reçu en WSOL (non déballé)
    ev = parse_swap(tx(5.0, 5.0 - 5000 / LAMPORTS, 1_000_000_000, 500_000_000, wsol=(0, 3 * LAMPORTS)), W)
    assert ev.side == "SELL" and ev.sol_amount == pytest.approx(3.0)
    assert ev.token_amount == pytest.approx(500) and ev.leader_pre_tokens == pytest.approx(1000)


def test_parse_ignores_failed_and_transfers():
    assert parse_swap(tx(10, 8, None, 1000, err={"x": 1}), W) is None
    assert parse_swap(tx(10, 10 - 5000 / LAMPORTS, None, 1000), W) is None  # airdrop reçu
    assert parse_swap(tx(10, 8, None, 1000), "SomeoneElse") is None


def ev(side, t, sol, tok, pre=0.0, wallet=W, mint=MINT, sig=None):
    return SwapEvent(sig or f"{wallet}{side}{t}", t, t, wallet, side, mint, sol, tok, 6, pre)


@pytest.fixture
def s():
    return replace(Settings(), bankroll_sol=1.0, size_mode="fraction", size=0.5, max_open=5,
                   latency_s=2, slippage_bps=0, bot_fee_pct=0, tx_fee_sol=0, rotate_after_losses=2,
                   max_leader_buy_sol=0)


def candles_flat(mint, prices: dict[int, float]):
    c = GeckoCandles()
    c.set_candles(mint, {t: [p, p * 1.1, p * 0.9, p] for t, p in prices.items()})
    return c


def test_engine_round_trip_neutral(s):
    c = candles_flat(MINT, {0: 0.001, 60: 0.002})
    eng = CopyEngine(s, BacktestPrices(c, "neutral", 0), [W])
    eng.on_event(ev("BUY", 10, 1.0, 1000))           # copie à t=12 au prix 0.001
    eng.on_event(ev("SELL", 70, 2.0, 1000, pre=1000))  # sortie à t=72 au prix 0.002
    eng.finalize(200)
    r = stats(eng.st, 1.0)
    assert r["n_closed"] == 1 and r["win_rate"] == 1.0
    assert r["final_equity"] == pytest.approx(1.5)  # 0.5 SOL doublés
    assert r["median_entry_slippage"] == pytest.approx(0.0)


def test_pessimistic_never_beats_leader(s):
    c = candles_flat(MINT, {0: 0.001})
    eng = CopyEngine(s, BacktestPrices(c, "pessimistic", 0), [W])
    eng.on_event(ev("BUY", 10, 1.0, 500))  # leader paie 0.002 > bougie : on paie au moins ça
    pos = next(iter(eng.st.positions.values()))
    assert pos["entry_price"] == pytest.approx(0.002)


def test_partial_sell_mirrors_fraction(s):
    c = candles_flat(MINT, {0: 0.001})
    eng = CopyEngine(s, BacktestPrices(c, "neutral", 0), [W])
    eng.on_event(ev("BUY", 10, 1.0, 1000))
    eng.on_event(ev("SELL", 20, 0.5, 500, pre=1000))
    pos = next(iter(eng.st.positions.values()))
    assert pos["tokens"] == pytest.approx(250)  # 500 tokens copiés, moitié vendue


def test_rotation_after_two_losses(s):
    L2 = "Leader2" + "1" * 37
    c = GeckoCandles()
    for m in ("A", "B", "C"):
        c.set_candles(m, {0: [1.0] * 4, 60: [0.5] * 4})
    eng = CopyEngine(s, BacktestPrices(c, "neutral", 0), [W, L2])
    for m, t in (("A", 0), ("B", 5)):
        eng.on_event(ev("BUY", t, 1, 1, mint=m))
    for m, t in (("A", 70), ("B", 75)):
        eng.on_event(ev("SELL", t, 0.5, 1, pre=1, mint=m))
    assert eng.active_leader == L2 and len(eng.st.rotations) == 1
    eng.on_event(ev("BUY", 80, 1, 1, mint="C"))  # ancien leader : ignoré
    assert eng.st.skips.get("leader non actif (rotation)") == 1


def test_fees_and_insufficient_capital(s):
    s2 = replace(s, size_mode="fixed", size=0.6, bot_fee_pct=1.0, tx_fee_sol=0.001)
    c = candles_flat(MINT, {0: 0.001})
    eng = CopyEngine(s2, BacktestPrices(c, "neutral", 0), [W])
    eng.on_event(ev("BUY", 10, 1, 1000))
    assert eng.st.cash == pytest.approx(1 - 0.6 - 0.001)
    pos = next(iter(eng.st.positions.values()))
    assert pos["tokens"] == pytest.approx(0.6 * 0.99 / 0.001)
    eng.on_event(ev("BUY", 11, 1, 1000, mint="X"))  # plus que 0.399 SOL -> taille plafonnée au cash
    assert len(eng.st.positions) in (1, 2)


def test_open_position_without_price_counts_zero(s):
    c = candles_flat(MINT, {0: 0.001})
    eng = CopyEngine(s, BacktestPrices(c, "neutral", 0), [W])
    eng.on_event(ev("BUY", 10, 1, 1000))
    eng.p.c._sol_unit[MINT] = ([], [])  # rug : plus aucune donnée
    eng.finalize(10_000)
    r = stats(eng.st, 1.0)
    assert r["open_no_price"] == 1 and r["final_equity"] == pytest.approx(0.5)


def test_baseline_and_render(s):
    evs = [ev("BUY", 1, 1.0, 100), ev("SELL", 2, 1.5, 100, pre=100)]
    b = leader_baseline(evs)
    assert b[W]["pnl"] == pytest.approx(0.5) and b[W]["wins"] == 1
    c = candles_flat(MINT, {0: 0.01})
    eng = CopyEngine(s, BacktestPrices(c, "neutral", 0), [W])
    for e in evs:
        eng.on_event(e)
    md = render({"neutral": stats(eng.st, 1.0)}, b, {"title": "t", "assumptions": {"x": 1}})
    assert "Résultat propre des leaders" in md and "| neutral |" in md


def test_duplicate_events_ignored(s):
    c = candles_flat(MINT, {0: 0.001})
    eng = CopyEngine(s, BacktestPrices(c, "neutral", 0), [W])
    e = ev("BUY", 10, 1, 1000)
    eng.on_event(e)
    assert eng.on_event(e) is None and len(eng.st.positions) == 1


def test_parse_usdc_swap_and_conversion():
    # Achat de 1000 tokens pour 300 USDC, le SOL ne bouge que des frais
    e = parse_swap(tx(1.0, 1.0 - 5000 / LAMPORTS, None, 1_000_000_000, usdc=(500_000_000, 200_000_000)), W)
    assert e.side == "BUY" and e.quote == "USD" and e.quote_amount == pytest.approx(300)
    [e] = convert_usd([e], lambda ts: 150.0)
    assert e.sol_amount == pytest.approx(2.0) and e.price_sol == pytest.approx(0.002)
    assert convert_usd([parse_swap(tx(1.0, 1.0, None, 10**9, usdc=(10**8, 0)), W)], lambda ts: None) == []


def test_unsigned_tx_ignored():
    # Distribution reçue d'un autre wallet : le leader n'a pas signé
    assert parse_swap(tx(10.0, 8.0, None, 1_000_000_000, signer=False), W) is None


def test_usd_candles_converted_to_sol():
    c = GeckoCandles()
    c._usd[WSOL] = ([0], [[150.0] * 4])
    c._usd[MINT] = ([0], [[0.3, 0.45, 0.15, 0.3]])
    (o, h, l, cl), exact = c.at(MINT, 30)
    assert exact and cl == pytest.approx(0.002) and h == pytest.approx(0.003)


def enh(native, tok, fee=5000, payer=W, usdc=None, err=None):
    changes = [{"userAccount": W, "mint": MINT, "rawTokenAmount": {"tokenAmount": str(tok), "decimals": 6}}]
    if usdc:
        changes.append({"userAccount": W, "mint": USDC, "rawTokenAmount": {"tokenAmount": str(usdc), "decimals": 6}})
    return {"signature": "s", "slot": 1, "timestamp": 100, "fee": fee, "feePayer": payer, "transactionError": err,
            "accountData": [{"account": W, "nativeBalanceChange": native, "tokenBalanceChanges": []},
                            {"account": "ata", "nativeBalanceChange": 0, "tokenBalanceChanges": changes}]}


def test_parse_enhanced_buy_sell_usd():
    b = parse_enhanced(enh(-2 * LAMPORTS - 5000, 1_000_000_000), W)
    assert b.side == "BUY" and b.sol_amount == pytest.approx(2.0) and b.token_amount == pytest.approx(1000)
    s_ = parse_enhanced(enh(3 * LAMPORTS - 5000, -400_000_000), W)
    assert s_.side == "SELL" and s_.sol_amount == pytest.approx(3.0)
    u = parse_enhanced(enh(-5000, 1_000_000, usdc=-50_000_000), W)
    assert u.quote == "USD" and u.quote_amount == pytest.approx(50)
    assert parse_enhanced(enh(0, 5_000_000, payer="other"), W) is None  # airdrop reçu
    assert parse_enhanced(enh(-LAMPORTS, 10**6, err={"x": 1}), W) is None


def test_fill_pre_balances():
    evs = [ev("BUY", 1, 1, 1000), ev("SELL", 2, 1, 400, pre=-1.0), ev("SELL", 3, 1, 600, pre=-1.0),
           ev("SELL", 4, 1, 50, pre=-1.0, mint="OTHER")]
    fill_pre_balances(evs)
    assert [e.leader_pre_tokens for e in evs[1:]] == [1000, 600, 50]
