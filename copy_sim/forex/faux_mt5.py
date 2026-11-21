"""Faux module MetaTrader5, en mémoire, pour essayer le pont sans terminal (`essais_pont.py --faux`).

Il imite seulement ce que le pont utilise. Les identifiants factices servent à vérifier que le pont n'en écrit aucun.
"""
from collections import namedtuple

ACCOUNT_TRADE_MODE_DEMO, ACCOUNT_TRADE_MODE_CONTEST, ACCOUNT_TRADE_MODE_REAL = 0, 1, 2
TRADE_ACTION_DEAL, TRADE_ACTION_SLTP = 1, 6
ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1
POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1
ORDER_FILLING_FOK, ORDER_FILLING_IOC, ORDER_FILLING_RETURN = 0, 1, 2
ORDER_TIME_GTC = 0
TIMEFRAME_M1, TIMEFRAME_M5, TIMEFRAME_M15, TIMEFRAME_M30 = 1, 5, 15, 30
TIMEFRAME_H1, TIMEFRAME_H4, TIMEFRAME_D1 = 16385, 16388, 16408

FAUX_LOGIN, FAUX_SERVEUR, FAUX_NOM = 987654321, "FAUX-SERVEUR-XYZ", "Jean Factice"

Compte = namedtuple("Compte", "login server name trade_mode balance equity margin_free currency leverage")
Terminal = namedtuple("Terminal", "trade_allowed connected")
Symbole = namedtuple("Symbole", "name visible point digits volume_min volume_step filling_mode trade_contract_size")
Tick = namedtuple("Tick", "bid ask time")
Position = namedtuple("Position", "ticket time type magic volume price_open sl tp price_current swap profit symbol comment")
Resultat = namedtuple("Resultat", "retcode price order comment")
Deal = namedtuple("Deal", "position profit swap commission fee")

mode_compte = ACCOUNT_TRADE_MODE_DEMO
positions: list = []
ordres_recus: list = []          # toutes les demandes passées à order_send
transactions: list = []          # Deal(...) : historique des positions fermées (garde-fou)
_ticket = [5000]
_prix = {"EURUSD": (1.10000, 1.10012), "XAUUSD": (2650.10, 2650.35)}


def initialize(*a, **k):
    return True


def last_error():
    return (1, "ok")


def terminal_info():
    return Terminal(True, True)


def account_info():
    return Compte(FAUX_LOGIN, FAUX_SERVEUR, FAUX_NOM, mode_compte, 10000.0, 10000.0, 9900.0, "USD", 500)


def symbol_info(sym):
    if sym not in _prix:
        return None
    or_ = sym == "XAUUSD"
    return Symbole(sym, True, 0.01 if or_ else 0.00001, 2 if or_ else 5, 0.01, 0.01, 2, 100.0 if or_ else 100000.0)


def symbol_select(sym, actif=True):
    return sym in _prix


def symbol_info_tick(sym):
    return Tick(*_prix[sym], 1794000000) if sym in _prix else None


def positions_get(ticket=None, **k):
    return tuple(p for p in positions if ticket is None or p.ticket == ticket)


def order_send(d):
    ordres_recus.append(dict(d))
    if d["action"] == TRADE_ACTION_SLTP:
        for i, p in enumerate(positions):
            if p.ticket == d["position"]:
                positions[i] = p._replace(sl=d["sl"], tp=d["tp"])
                return Resultat(10009, 0.0, 0, "Request executed")
        return Resultat(10013, 0.0, 0, "Invalid request")
    if d.get("type_filling") != ORDER_FILLING_IOC:
        return Resultat(10030, 0.0, 0, "Unsupported filling mode")
    if "position" in d:
        for p in list(positions):
            if p.ticket == d["position"]:
                positions.remove(p)
                return Resultat(10009, d["price"], 0, "Request executed")
        return Resultat(10013, 0.0, 0, "Invalid request")
    _ticket[0] += 1
    positions.append(Position(_ticket[0], 1794000000, d["type"], d["magic"], d["volume"], d["price"], d["sl"],
                              d["tp"], d["price"], 0.0, 0.0, d["symbol"], d["comment"]))
    return Resultat(10009, d["price"], _ticket[0], "Request executed")


def _barres(n):
    return [{"time": 1794000000 + 60 * i, "open": 1.1, "high": 1.1002, "low": 1.0998, "close": 1.1001,
             "tick_volume": 42, "spread": 12} for i in range(n)]


def copy_rates_from_pos(sym, tf, depart, n):
    return _barres(n) if sym in _prix else None


def copy_rates_range(sym, tf, debut, fin):
    return _barres(500) if sym in _prix else None


def history_deals_get(position=None, **k):
    return tuple(d for d in transactions if position is None or d.position == position)
