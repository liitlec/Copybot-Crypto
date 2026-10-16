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


def test_ws_url():
    from copysim.stream import ws_url
    assert ws_url("https://mainnet.helius-rpc.com/?api-key=k") == "wss://mainnet.helius-rpc.com/?api-key=k"
    assert ws_url("http://localhost:8899") == "ws://localhost:8899"


def test_path_recorder_writes_rows(tmp_path, monkeypatch):
    import time as _t
    from copysim.engine import EngineState
    from copysim.paths import PathRecorder
    st = EngineState(cash=1.0, positions={"L:M": {"mint": "M", "leader": "L", "decimals": 6, "tokens": 1000.0,
                                                  "cost_sol": 0.2, "opened_ts": _t.time() - 5}})
    rec = PathRecorder(st, "http://q", tmp_path / "p.jsonl", interval_s=0.01)
    monkeypatch.setattr(rec, "_quote_sell", lambda mint, raw: {"outAmount": str(int(0.22 * LAMPORTS)), "priceImpactPct": "0.01"})
    rec.start()
    _t.sleep(0.1)
    import json as _j
    rows = [_j.loads(l) for l in (tmp_path / "p.jsonl").read_text().splitlines()]
    assert rows and rows[0]["ret_vs_cost"] == pytest.approx(0.1) and rows[0]["age_s"] >= 5


def test_token_info_summary():
    from copysim.tokeninfo import summarize
    d = {"token": {"creation": {"creator": "C", "created_time": 900}},
         "pools": [{"market": "pumpfun", "liquidity": {"usd": 5000}, "lpBurn": 100, "createdAt": 950_000,
                    "security": {"mintAuthority": None, "freezeAuthority": None}, "deployer": "D",
                    "txns": {"buys": 10, "sells": 4}},
                   {"market": "x", "liquidity": {"usd": 100}}],
         "risk": {"score": 3, "rugged": False, "top10": 30.5, "dev": {"percentage": 2.0},
                  "bundlers": {"totalPercentage": 5.0}, "snipers": {"totalPercentage": 1.0},
                  "risks": [{"name": "No social media"}]}}
    s = summarize(d, now=1000)
    assert s["token_age_s"] == 100 and s["pool_age_s"] == 50 and s["liquidity_usd"] == 5000
    assert s["liquidity_usd_all_pools"] == 5100 and s["bundlers_pct"] == 5.0 and s["insiders_pct"] is None
    assert s["risks"] == ["No social media"] and s["lp_burn_pct"] == 100


def test_rug_filter_reasons_and_engine_hook(s):
    from copysim.prices import Fill
    from copysim.rugfilter import RugFilter
    rf = RugFilter(None)
    good = {"mint_authority": None, "freeze_authority": None, "rugged_flag": False, "liquidity_usd": 20000,
            "pool_age_s": 600, "top10_pct": 30, "dev_pct": 2, "bundlers_pct": 5, "insiders_pct": 0}
    assert rf.reasons(good) == []
    bad = dict(good, freeze_authority="X", liquidity_usd=1000, pool_age_s=30, top10_pct=80)
    assert len(rf.reasons(bad)) == 4
    assert rf.check(ev("BUY", 1, 1, 1000)) == "anti-rug : fiche token indisponible"  # pas de clé -> refus

    class P:
        def buy(self, e, sol, ts): return Fill(sol / 0.001, 0.001, "impact=0.08")
    eng = CopyEngine(s, P(), [W], pre_buy_check=lambda e: None, max_impact=0.03)
    eng.on_event(ev("BUY", 10, 1, 1000))
    assert not eng.st.positions and eng.st.skips == {"impact de notre achat > 3%": 1}
    eng2 = CopyEngine(s, P(), [W], pre_buy_check=lambda e: "anti-rug : test")
    eng2.on_event(ev("BUY", 10, 1, 1000, sig="x2"))
    assert eng2.st.skips == {"anti-rug : test": 1}


def test_scout_round_trips_and_profile():
    from copysim.scout import leader_profile, round_trips, verdict
    evs = [ev("BUY", 0, 1.0, 100, mint="A"), ev("SELL", 300, 1.5, 100, pre=100, mint="A"),
           ev("BUY", 10, 1.0, 100, mint="B"), ev("SELL", 20, 0.5, 100, pre=100, mint="B"),
           ev("BUY", 30, 1.0, 100, mint="C")]  # C jamais revendu
    rts = round_trips(evs)
    assert sorted(r["mint"] for r in rts) == ["A", "B"]
    p = leader_profile(evs)
    assert p["n_round_trips"] == 2 and p["median_hold_s"] == 155 and p["share_under_30s"] == 0.5
    assert p["leader_pnl"] == pytest.approx(0.0) and p["n_tokens"] == 3
    ok = {"copier_h1": {"neutral": {"return": 0.1}}, "copier_h2": {"neutral": {"return": 0.05},
          "pessimistic": {"return": 0.0}}, "crash_rate": 0.05}
    assert verdict(ok).startswith("✅")
    assert verdict(dict(ok, copier_h2={"neutral": {"return": -0.1}, "pessimistic": {"return": -0.2}})).startswith("❌ ne tient")


def test_pump_curve_and_snipe_simulation():
    from copysim.sniper import Rule, buy_tokens, sell_sol, simulate, snipe_report
    v_sol, v_tok = 30.0, 1_073_000_000.0
    t = buy_tokens(1.0, v_sol, v_tok, 0.0)
    assert sell_sol(t, v_sol + 1.0, v_tok - t, 0.0) == pytest.approx(1.0)  # aller-retour sans frais = neutre
    # Le prix double (réserves SOL ×√2 environ) après notre entrée
    rec = {"states": [[0.0, 30.0, 1.073e9, "c", 0, 1], [0.3, 31.0, 1.073e9 * 30 / 31, "b", 1, 0],
                      [5.0, 45.0, 1.073e9 * 30 / 45, "b", 14, 0], [20.0, 25.0, 1.073e9 * 30 / 25, "s", 20, 1]]}
    up = simulate(rec, Rule(0.5, 0.5, None, 60), 0.5, 0.0125, 0.002)
    assert up > 0.5  # TP touché à t=5 s
    hold = simulate(rec, Rule(0.5, None, None, 60), 0.5, 0.0125, 0.002)
    assert hold < 0  # sans TP, on sort au dernier état (le dev a vendu)
    recs = [dict(rec, t0=i, dev_buy_sol=0) for i in range(60)]
    md = snipe_report(recs, 0.5, 0.0125, 0.002)
    assert "Meilleure règle" in md and "| entrée 0.5s" in md


def test_sniper_drops_bad_curves():
    from copysim.sniper import valid_curve
    assert valid_curve({"states": [[0.0, 30, 1.073e9, "c", 0, 0], [1.0, 80, 4e8, "b", 50, 0]]})
    assert not valid_curve({"states": [[0.0, 30, 1.073e9, "c", 0, 0], [2.4, 295047.06, 1.0e9, "b", 295017, 0]]})


def test_stream_single_connection_routing():
    from copysim.stream import SignatureStream
    st = SignatureStream.__new__(SignatureStream)
    import queue
    st.q, st.log = queue.Queue(), lambda *_: None
    subs, pending = {}, {1: "WA", 2: "WB"}
    st.handle('{"jsonrpc":"2.0","result":777,"id":2}', subs, pending)
    st.handle('{"jsonrpc":"2.0","result":555,"id":1}', subs, pending)
    assert subs == {777: "WB", 555: "WA"} and not pending
    st.handle('{"method":"logsNotification","params":{"subscription":777,"result":{"value":{"signature":"S1","err":null}}}}', subs, pending)
    st.handle('{"method":"logsNotification","params":{"subscription":555,"result":{"value":{"signature":"S2","err":{"x":1}}}}}', subs, pending)
    w, sig, _ = st.q.get_nowait()
    assert (w, sig) == ("WB", "S1") and st.q.empty()


def test_copy_rules_deltas():
    from copysim.rules import evaluate
    pre = {"regles": {"R1_prix_entree_max": {"seuil_entry_slippage": 0.2},
                      "R2_moitie_a_plus_50": {"seuil_ret_vs_cost": 0.5, "fraction_vendue": 0.5},
                      "R3_confluence": {"fenetre_s": 600, "multiplicateur": 2.0}}}
    t1 = {"leader": "A", "mint": "M1", "opened_ts": 100.0, "pnl_sol": -0.5, "proceeds_sol": 0.5, "entry_slippage": 0.5}
    t2 = {"leader": "B", "mint": "M2", "opened_ts": 200.0, "pnl_sol": -1.0, "proceeds_sol": 0.0, "entry_slippage": 0.0}
    t3 = {"leader": "C", "mint": "M2", "opened_ts": 300.0, "pnl_sol": 0.2, "proceeds_sol": 1.2, "entry_slippage": 0.1}
    paths = {("B", "M2", 200): [(5.0, 0.1, 1.1), (9.0, 0.6, 1.6), (20.0, -1.0, 0.0)]}
    r = evaluate([t1, t2, t3], paths, pre, bot_fee_pct=0.0, tx_fee=0.0)
    assert r["base"] == -1.3
    assert r["R1"]["delta"] == 0.5 and r["R1"]["touches"] == 1          # t1 évité
    assert abs(r["R2"]["delta"] - 0.8) < 1e-9                            # moitié vendue à 1,6 au lieu de 0
    assert abs(r["R3"]["delta"] - (-1.0 + 0.2)) < 1e-9                   # t2 et t3 doublés


def test_rugfilter_unknown_curve_liquidity_not_refused():
    from copysim.rugfilter import RugFilter
    f = RugFilter(None)
    base = {"mint_authority": None, "freeze_authority": None, "pool_age_s": 300}
    assert f.reasons({**base, "liquidity_usd": None, "liquidity_unknown": True}) == []
    assert f.reasons({**base, "liquidity_usd": None}) == ["liquidité < 2000 $"]
    assert f.reasons({**base, "liquidity_usd": 500.0}) == ["liquidité < 2000 $"]


def test_scalp_b_entry_condition():
    from copysim.sniper import scalp_entry_ok
    c = [0.0, 30, 1.073e9, "c", 0.5, 0]
    assert scalp_entry_ok({"states": [c]}, 5, False)
    assert not scalp_entry_ok({"states": [c]}, 5, True)                                   # personne n'a acheté
    assert scalp_entry_ok({"states": [c, [2.0, 31, 1.04e9, "b", 1, 0]]}, 5, True)         # un acheteur à 2 s
    assert not scalp_entry_ok({"states": [c, [0.2, 31, 1.04e9, "b", 1, 0], [2.0, 32, 1.0e9, "b", 1, 0]]}, 5, True)
    assert not scalp_entry_ok({"states": [c, [6.0, 31, 1.04e9, "b", 1, 0]]}, 5, True)     # acheteur après l'entrée


def test_scalp_sol_in_curve_cap():
    from copysim.sniper import sol_in_curve_at
    rec = {"states": [[0.0, 30.4, 1.06e9, "c", 0.4, 0], [3.0, 33.0, 0.97e9, "b", 2.6, 0]]}
    assert abs(sol_in_curve_at(rec, 1.0) - 0.4) < 1e-9     # A : 0,4 SOL < 0,5 -> achète
    assert abs(sol_in_curve_at(rec, 5.0) - 3.0) < 1e-9     # B : 3 SOL >= 2,5 -> n'achète pas


def test_scalp_rule_c_exit():
    from copysim.scalpgrpc import V_TOK0, evaluate, evaluate_c
    c = {"bt": 0.0, "slot": 1, "signer": "DEV", "signer_sol": -0.03}
    row = lambda t, v, s: {"bt": t, "slot": s, "kind": "buy", "v_tok": v, "curve_tok": 0.0, "signer": "X"}  # noqa: E731
    flat = [row(3.0, V_TOK0 * 0.999, 2), row(30.0, V_TOK0 * 0.998, 3)]
    args = (5.0, 2.5, 60.0, 0.20, 0.30, 540.0)
    assert abs(evaluate_c(c, flat, *args) - evaluate(c, flat, 5.0, 60.0, 2.5)) < 1e-12   # < +20 % à 60 s : comme B
    run = [row(3.0, V_TOK0 * 0.999, 2), row(50.0, V_TOK0 * 0.8, 3), row(120.0, V_TOK0 * 0.6, 4),
           row(200.0, V_TOK0 * 0.75, 5), row(300.0, V_TOK0 * 0.5, 6)]
    x = evaluate_c(c, run, *args)
    assert x > evaluate(c, run, 5.0, 60.0, 2.5)          # gardé au-delà de 60 s : capte la montée
    assert x < 1.5                                          # revendu au stop suiveur (t=200), pas au plus haut


def test_scalp_rule_e_exit():
    from copysim.scalpgrpc import K, V_SOL0, V_TOK0, evaluate_scale, tokens_for

    def vtok_at(sol):  # v_tok quand la courbe contient `sol` SOL réels
        return K / (V_SOL0 + sol)

    c = {"bt": 1000.0, "slot": 1, "signer_sol": 0.0}
    tr = lambda t, sol: {"bt": 1000.0 + t, "slot": 2, "kind": "buy", "v_tok": vtok_at(sol), "curve_tok": 0.0}  # noqa: E731
    flat = [tr(4, 0.5), tr(30, 0.5), tr(70, 0.5)]
    x = evaluate_scale(c, flat, 5.0, 2.5)
    assert x == pytest.approx(evaluate_scale(c, flat[:2], 5.0, 2.5))  # < +20 % à 60 s : vendu à 60 s
    pump = [tr(4, 0.5), tr(30, 6.0), tr(40, 20.0), tr(50, 1.0), tr(60, 0.5)]
    y = evaluate_scale(c, pump, 5.0, 2.5)
    assert y > 0.4  # moitié vendue au ×2 (et plus), reste coupé par le stop −40 %
    assert V_TOK0 > tokens_for(V_TOK0, 0.1) > 0


def test_scalp_wave_filter():
    from copysim.scalpgrpc import wave_ok
    b = [(1000.0 + i, "m", 0.05) for i in range(20)]
    bt = [t for t, _, _ in b]
    assert wave_ok(b, bt, 1100.0)  # 20 trades B positifs terminés
    assert not wave_ok(b, bt, 1070.0)  # trop peu de trades B déjà revendus à t
    neg = [(t, m, -0.02) for t, m, _ in b]
    assert not wave_ok(neg, bt, 1100.0)
    assert not wave_ok(b, bt, 1000.0 + 1800 + 65 + 30)  # hors de la fenêtre de 30 min


def test_scalp_drop_spikes():
    from copysim.scalpgrpc import drop_spikes
    rs = [{"v_tok": v} for v in (1.0e9, 0.99e9, 0.0733e9, 0.985e9, 0.98e9)]
    assert [r["v_tok"] for r in drop_spikes(rs)] == [1.0e9, 0.99e9, 0.985e9, 0.98e9]
    steady = [{"v_tok": v} for v in (1.0e9, 0.5e9, 0.3e9)]  # vrai pump : pas de retour au niveau d'avant
    assert len(drop_spikes(steady)) == 3
