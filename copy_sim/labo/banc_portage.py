"""Banc I : portage sur Hyperliquid. Le financement horaire des contrats perpetuels est verse par les acheteurs aux
vendeurs quand il est positif. Montage neutre : acheter l'actif au comptant et vendre le perpetuel pour la meme
valeur ; on encaisse le financement sans risque de prix (reste : risque de plateforme, frais, marge).
Mesure : financement moyen annualise sur ~1 an et par trimestre. Usage : python3 banc_portage.py"""
import json, time, urllib.request
import numpy as np

URL = "https://api.hyperliquid.xyz/info"


def historique(coin, debut_ms):
    out, t = [], debut_ms
    for _ in range(40):
        req = urllib.request.Request(URL, data=json.dumps({"type": "fundingHistory", "coin": coin, "startTime": t}).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        d = json.load(urllib.request.urlopen(req, timeout=30))
        if not d:
            break
        out += d
        t = d[-1]["time"] + 1
        if len(d) < 500:
            break
        time.sleep(0.25)
    return out


if __name__ == "__main__":
    debut = int((time.time() - 365 * 86400) * 1000)
    print("Financement Hyperliquid, 12 derniers mois (taux horaire -> % par an, sans levier)")
    print("%-6s %6s %9s | par trimestre (%% par an)            | part des heures > 0 | pire mois" % ("actif", "heures", "% par an"))
    for coin in ("BTC", "ETH", "SOL", "PAXG"):
        try:
            h = historique(coin, debut)
        except Exception as e:
            print(coin, "echec :", type(e).__name__); continue
        if len(h) < 100:
            print(coin, "pas assez de donnees"); continue
        f = np.array([float(x["fundingRate"]) for x in h])
        an = f.mean() * 24 * 365 * 100
        q = [f[i * len(f) // 4:(i + 1) * len(f) // 4].mean() * 24 * 365 * 100 for i in range(4)]
        mois = [f[i:i + 720].sum() * 100 for i in range(0, len(f) - 719, 720)]
        print("%-6s %6d %+8.1f%% | %s | %17.0f %% | %+.2f %% sur le mois" % (
            coin, len(f), an, "  ".join("%+6.1f" % x for x in q), 100 * (f > 0).mean(), min(mois)))
    print("Frais a compter : ~0,045 % par ordre sur le perpetuel et ~0,07 % au comptant, a l'entree et a la sortie\n"
          "(≈ 0,25 % l'aller-retour complet), et de la marge immobilisee cote perpetuel (rendement / ~1,2 a 1,5).")
