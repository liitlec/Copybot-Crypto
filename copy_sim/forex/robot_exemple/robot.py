"""Robot d'essai minimal (exemple pour le labo) : ouvre 0,01 lot XAUUSD avec un stop, ferme après une minute,
puis attend sans rien faire. Il montre l'interface : `lancer(pont)` ne revient jamais tant que STOP_PONT est absent."""
import time

SYMBOLE, LOTS, ECART_STOP, DUREE = "XAUUSD", 0.01, 5.0, 60


def un_cycle(pont, duree=DUREE):
    p = pont.prix(SYMBOLE)
    r = pont.ouvrir(SYMBOLE, "achat", LOTS, stop=round(p["bid"] - ECART_STOP, 2), id="essai_robot")
    pont.noter(decision="ouverture d'essai", prix=p, resultat=r)
    if not r.get("ok"):
        return r, None
    fin = time.time() + duree
    while time.time() < fin and not pont.arret_demande():
        time.sleep(1)
    f = pont.fermer(r["ticket"])
    pont.noter(decision="fermeture d'essai", resultat=f)
    return r, f


def lancer(pont):
    un_cycle(pont)
    while not pont.arret_demande():
        time.sleep(5)
