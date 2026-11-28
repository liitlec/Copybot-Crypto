"""Telecharge et met en cache les prix (Yahoo Finance). Usage : python3 donnees.py
Ecrit data/jour.csv.gz (clotures journalieres) et data/h1.csv.gz (clotures 1 h, ~2 ans)."""
import json, time, urllib.request, os
import pandas as pd

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
ICI = os.path.dirname(os.path.abspath(__file__))
# nom court -> (ticker Yahoo, classe)
UNIVERS = {
    "EURUSD": ("EURUSD=X", "fx"), "GBPUSD": ("GBPUSD=X", "fx"), "USDJPY": ("JPY=X", "fx"),
    "AUDUSD": ("AUDUSD=X", "fx"), "USDCAD": ("CAD=X", "fx"), "USDCHF": ("CHF=X", "fx"),
    "NZDUSD": ("NZDUSD=X", "fx"),
    "OR": ("GC=F", "metal"), "ARGENT": ("SI=F", "metal"),
    "SP500": ("^GSPC", "indice"), "NASDAQ": ("^NDX", "indice"), "DAX": ("^GDAXI", "indice"),
    "NIKKEI": ("^N225", "indice"), "FTSE": ("^FTSE", "indice"),
    "BTC": ("BTC-USD", "crypto"), "ETH": ("ETH-USD", "crypto"),
    "TAUX_US_3M": ("^IRX", "taux"),
}
H1 = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "OR", "SP500", "NASDAQ", "BTC", "ETH"]


def yahoo(ticker, interval, rng):
    if rng == "max":  # "range=max" rend du mensuel : on demande les dates explicitement
        q = "period1=0&period2=%d" % int(time.time())
    else:
        q = "range=" + rng
    url = ("https://query2.finance.yahoo.com/v8/finance/chart/%s?interval=%s&%s"
           % (urllib.request.quote(ticker), interval, q))
    for essai in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            d = json.load(urllib.request.urlopen(req, timeout=30))
            r = d["chart"]["result"][0]
            s = pd.Series(r["indicators"]["quote"][0]["close"],
                          index=pd.to_datetime(r["timestamp"], unit="s", utc=True))
            return s.dropna()
        except Exception as e:  # reseau capricieux : on reessaie
            err = e
            time.sleep(2 * (essai + 1))
    raise RuntimeError("echec %s : %s" % (ticker, err))


def main():
    jour, h1 = {}, {}
    for nom, (tk, _) in UNIVERS.items():
        s = yahoo(tk, "1d", "max")
        s.index = s.index.tz_convert(None).normalize()
        jour[nom] = s[~s.index.duplicated(keep="last")]
        print(nom, "jour", len(s), s.index[0].date(), s.index[-1].date())
        time.sleep(0.5)
    pd.DataFrame(jour).sort_index().to_csv(os.path.join(ICI, "data", "jour.csv.gz"), float_format="%.6g")
    for nom in H1:
        s = yahoo(UNIVERS[nom][0], "1h", "730d")
        s.index = s.index.tz_convert(None).floor("h")
        h1[nom] = s[~s.index.duplicated(keep="last")]
        print(nom, "1h", len(s), s.index[0], s.index[-1])
        time.sleep(0.5)
    pd.DataFrame(h1).sort_index().to_csv(os.path.join(ICI, "data", "h1.csv.gz"), float_format="%.6g")


if __name__ == "__main__":
    main()
