import numpy as np
import pandas as pd

from tendance.algo import exposure


def test_exposition_tendance_et_volatilite():
    idx = pd.date_range("2024-01-01", periods=120, freq="D")
    calme = pd.Series(np.linspace(100, 160, 120), index=idx)            # hausse reguliere, faible volatilite
    assert exposure(calme, 50, 0.4).iloc[-1] == 1.0
    baisse = pd.Series(np.linspace(160, 100, 120), index=idx)
    assert exposure(baisse, 50, 0.4).iloc[-1] == 0.0
    rng = np.random.default_rng(0)
    agite = pd.Series(100 * np.exp(np.cumsum(0.01 + rng.normal(0, 0.06, 120))), index=idx)  # ~115 %/an de volatilite
    ex = exposure(agite, 50, 0.4).iloc[-1]
    assert 0 <= ex < 0.6                                                 # taille reduite quand ca s'agite


def test_ensemble_proportion_de_signaux():
    idx = pd.date_range("2024-01-01", periods=260, freq="D")
    hausse = pd.Series(np.linspace(100, 200, 260), index=idx)
    assert exposure(hausse, 50, 10.0, ensemble=True).iloc[-1] == 1.0       # tous les signaux haussiers
    # longue hausse puis petite baisse recente : les signaux courts basculent, pas les longs
    p = pd.Series(np.r_[np.linspace(100, 200, 230), np.linspace(200, 185, 30)], index=idx)
    e = exposure(p, 50, 10.0, ensemble=True).iloc[-1]
    assert 0 < e < 1
