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
