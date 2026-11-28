"""Moteur de copy trading simulé (identique en backtest et en live).

Règles reproduisant le post :
  * on copie les ACHATS du leader actif (taille = fraction du capital courant -> composition)
  * on copie ses VENTES au prorata (s'il vend 50 % de sa ligne, on vend 50 % de la nôtre)
  * rotation : après N pertes d'affilée, on passe au leader suivant du classement
  * option : ignorer les achats du leader au-dessus d'une taille (« sized in too big -> skipped »)
"""
from __future__ import annotations

import time
from collections import Counter
from dataclasses import asdict, dataclass, field

from .config import Settings
from .swaps import SwapEvent


@dataclass
class Position:
    leader: str
    mint: str
    decimals: int
    tokens: float
    cost_sol: float          # SOL engagés (frais inclus)
    proceeds_sol: float      # SOL récupérés par les ventes partielles (frais déduits)
    opened_ts: float
    entry_price: float
    leader_entry_price: float
    leader_buy_sig: str


@dataclass
class EngineState:
    cash: float
    active_idx: int = 0
    positions: dict[str, dict] = field(default_factory=dict)   # "leader:mint" -> Position
    closed: list[dict] = field(default_factory=list)
    skips: dict[str, int] = field(default_factory=dict)
    streak: dict[str, int] = field(default_factory=dict)
    rotations: list[dict] = field(default_factory=list)
    equity_curve: list[tuple[float, float]] = field(default_factory=list)
    seen: list[str] = field(default_factory=list)


class CopyEngine:
    def __init__(self, s: Settings, prices, leaders: list[str], state: EngineState | None = None,
                 live: bool = False, pre_buy_check=None, max_impact: float | None = None):
        self.s, self.p, self.leaders, self.live = s, prices, leaders, live
        self.pre_buy_check = pre_buy_check  # ev -> motif de refus ou None (filtre anti-rug)
        self.max_impact = max_impact        # refuse l'achat si notre impact de prix dépasse ce seuil
        self.st = state or EngineState(cash=s.bankroll_sol)
        self._seen = set(self.st.seen)

    # ------------------------------------------------------------ helpers
    @property
    def active_leader(self) -> str | None:
        if self.s.rotate_after_losses <= 0 or not self.leaders:
            return None
        return self.leaders[self.st.active_idx % len(self.leaders)]

    def _skip(self, reason: str) -> None:
        self.st.skips[reason] = self.st.skips.get(reason, 0) + 1

    def _positions(self) -> dict[str, Position]:
        return {k: Position(**v) for k, v in self.st.positions.items()}

    def _save_pos(self, key: str, pos: Position | None) -> None:
        if pos is None:
            self.st.positions.pop(key, None)
        else:
            self.st.positions[key] = asdict(pos)

    def equity_at_cost(self) -> float:
        return self.st.cash + sum(p["cost_sol"] - p["proceeds_sol"] for p in self.st.positions.values())

    # ------------------------------------------------------------ events
    def on_event(self, ev: SwapEvent, now_ts: float | None = None) -> dict | None:
        if ev.signature in self._seen:
            return None
        self._seen.add(ev.signature)
        self.st.seen.append(ev.signature)
        ts = now_ts if (self.live and now_ts) else ev.block_time + self.s.latency_s
        return self._on_buy(ev, ts) if ev.side == "BUY" else self._on_sell(ev, ts)

    def _on_buy(self, ev: SwapEvent, ts: float) -> dict | None:
        s = self.s
        active = self.active_leader
        if active is not None and ev.wallet != active:
            return self._skip("leader non actif (rotation)")
        key = f"{ev.wallet}:{ev.mint}"
        if key in self.st.positions:
            return self._skip("renforcement ignoré (position déjà ouverte)")
        if len(self.st.positions) >= s.max_open:
            return self._skip("trop de positions ouvertes")
        if s.max_leader_buy_sol > 0 and ev.sol_amount > s.max_leader_buy_sol:
            return self._skip("achat du leader trop gros")
        size = s.size * self.equity_at_cost() if s.size_mode == "fraction" else s.size
        size = min(size, self.st.cash - s.tx_fee_sol)
        if size < s.min_trade_sol:
            return self._skip("capital insuffisant")
        if self.pre_buy_check:
            reason = self.pre_buy_check(ev)
            if reason:
                return self._skip(reason)
            if self.live:
                ts = time.time()  # la vérification a pris du temps : on cote maintenant
        bot_fee = size * s.bot_fee_pct / 100
        fill = self.p.buy(ev, size - bot_fee, ts)
        if not fill or fill.amount_out <= 0:
            return self._skip("pas de prix / pas de route à l'achat")
        if self.max_impact is not None and fill.note.startswith("impact="):
            try:
                if float(fill.note.split("=", 1)[1] or 0) > self.max_impact:
                    return self._skip(f"impact de notre achat > {self.max_impact:.0%}")
            except ValueError:
                pass
        self.st.cash -= size + s.tx_fee_sol
        pos = Position(ev.wallet, ev.mint, ev.decimals, fill.amount_out, size + s.tx_fee_sol, 0.0, ts,
                       fill.price_sol, ev.price_sol, ev.signature)
        self._save_pos(key, pos)
        return {"type": "BUY", "leader": ev.wallet, "mint": ev.mint, "sol": round(size, 6),
                "price": fill.price_sol, "leader_price": ev.price_sol,
                "delay_s": round(ts - ev.block_time, 2), "note": fill.note}

    def _on_sell(self, ev: SwapEvent, ts: float) -> dict | None:
        s = self.s
        key = f"{ev.wallet}:{ev.mint}"
        if key not in self.st.positions:
            return None  # on ne détenait pas ce token via ce leader
        pos = Position(**self.st.positions[key])
        frac = ev.token_amount / ev.leader_pre_tokens if ev.leader_pre_tokens > 0 else 1.0
        frac = 1.0 if frac > 0.98 else max(frac, 0.0)
        qty = pos.tokens * frac
        fill = self.p.sell(pos.mint, pos.decimals, qty, ts, ev.price_sol)
        sol = fill.amount_out if fill else 0.0
        net = sol * (1 - s.bot_fee_pct / 100) - s.tx_fee_sol
        self.st.cash += net
        pos.tokens -= qty
        pos.proceeds_sol += net
        evt = {"type": "SELL", "leader": ev.wallet, "mint": ev.mint, "fraction": round(frac, 3),
               "sol": round(net, 6), "price": fill.price_sol if fill else 0.0, "leader_price": ev.price_sol,
               "delay_s": round(ts - ev.block_time, 2)}
        if pos.tokens <= 1e-12 or frac >= 1.0:
            self._close(key, pos, ts, "sortie du leader")
        else:
            self._save_pos(key, pos)
        return evt

    def _close(self, key: str, pos: Position, ts: float, reason: str, open_mark: bool = False) -> dict:
        pnl = pos.proceeds_sol - pos.cost_sol
        rec = {"leader": pos.leader, "mint": pos.mint, "opened_ts": pos.opened_ts, "closed_ts": ts,
               "cost_sol": round(pos.cost_sol, 6), "proceeds_sol": round(pos.proceeds_sol, 6),
               "pnl_sol": round(pnl, 6), "ret": pnl / pos.cost_sol if pos.cost_sol else 0.0,
               "entry_price": pos.entry_price, "leader_entry_price": pos.leader_entry_price,
               "entry_slippage": (pos.entry_price / pos.leader_entry_price - 1) if pos.leader_entry_price else None,
               "reason": reason, "still_open": open_mark}
        self.st.closed.append(rec)
        self._save_pos(key, None)
        self.st.equity_curve.append((ts, self.equity_at_cost()))
        if not open_mark:
            self._update_rotation(pos.leader, pnl, ts)
        return rec

    def _update_rotation(self, leader: str, pnl: float, ts: float) -> None:
        self.st.streak[leader] = self.st.streak.get(leader, 0) + 1 if pnl < 0 else 0
        n = self.s.rotate_after_losses
        if n > 0 and leader == self.active_leader and self.st.streak[leader] >= n:
            self.st.active_idx += 1
            self.st.streak[leader] = 0
            self.st.rotations.append({"ts": ts, "dropped": leader, "next": self.active_leader})

    def finalize(self, end_ts: float) -> None:
        """Valorise les positions encore ouvertes (prix de sortie estimé, frais du bot déduits)."""
        for key, pos in list(self._positions().items()):
            val = self.p.mark(pos.mint, pos.decimals, pos.tokens, end_ts)
            reason = "ouverte, valorisée" if val is not None else "ouverte, sans prix (compté 0)"
            pos.proceeds_sol += (val or 0.0) * (1 - self.s.bot_fee_pct / 100)
            self._close(key, pos, end_ts, reason, open_mark=True)

    def skip_counts(self) -> Counter:
        return Counter(self.st.skips)
