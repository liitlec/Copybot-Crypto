"""Essais hors ligne du robot d'exemple, sur le faux terminal. Doit finir par « ESSAIS OK »."""
import faux_mt5
import acces_robot
import robot

pont = acces_robot.AccesRobot.pour_essais(faux_mt5)
r, f = robot.un_cycle(pont, duree=0)
assert r["ok"] and r["ticket"], r
assert f and f["ok"], f
assert not pont.positions()
ordre = faux_mt5.ordres_recus[0]
assert ordre["volume"] == 0.01 and ordre["sl"] > 0
sans_stop = pont.ouvrir("XAUUSD", "achat", 0.01, stop=0)
assert not sans_stop["ok"] and "stop" in sans_stop["refus"], sans_stop
print("ESSAIS OK")
