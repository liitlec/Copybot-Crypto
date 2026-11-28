"""Diversité du tournoi (06/11) : les places achètent-elles vraiment des tokens différents ?

Lit state.json : pour la championne (caisse ia) et chaque place defi_N, les tokens achetés depuis le début de la
règle en place. Affiche les paires de places qui partagent plus de --seuil (50 %) de leurs achats : deux places qui
achètent les mêmes tokens ne testent qu'une seule idée, et leurs résultats ne se confirment pas l'un l'autre.

Usage : python3 diversite.py /tmp/d [--seuil 0.5]"""
import argparse
import json
from pathlib import Path


def achats(state):
    """{place: (nom, set de tokens)} pour ia et les places du tournoi, depuis le début de leur règle actuelle."""
    books = state.get("books") or {}
    out = {}
    places = [("ia", "championne", 0)] + [(k, v.get("nom", ""), v.get("debut", 0))
                                          for k, v in sorted((state.get("defis") or {}).items(),
                                                             key=lambda kv: int(kv[0].split("_")[1]))]
    for slot, nom, debut in places:
        b = books.get(slot) or {}
        toks = {r["token"] for r in b.get("closed", []) if r.get("t_in", 0) >= debut}
        toks |= {t for t, p in (b.get("open") or {}).items() if p.get("t", 0) >= debut}
        out[slot] = (nom, toks)
    return out


def paires(acs, seuil=0.5):
    """[(place a, place b, part commune, n communs)] au-dessus du seuil (part = communs / plus petite des deux)."""
    res, cles = [], list(acs)
    for i, a in enumerate(cles):
        for b in cles[i + 1:]:
            ta, tb = acs[a][1], acs[b][1]
            if len(ta) >= 3 and len(tb) >= 3:
                com = len(ta & tb)
                part = com / min(len(ta), len(tb))
                if part >= seuil:
                    res.append((a, b, part, com))
    return sorted(res, key=lambda x: -x[2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--seuil", type=float, default=0.5)
    a = ap.parse_args()
    state = json.loads((Path(a.data) / "state.json").read_text())
    acs = achats(state)
    tous = [t for _, ts in acs.values() for t in ts]
    print(f"{len(acs)} places, {len(tous)} achats, {len(set(tous))} tokens distincts "
          f"({len(set(tous)) / len(tous):.0%} de diversité)" if tous else "aucun achat")
    for slot, (nom, ts) in acs.items():
        print(f"  {slot:8} {len(ts):3d} tokens  {nom[:50]}")
    ps = paires(acs, a.seuil)
    if ps:
        print(f"\npaires trop proches (≥ {a.seuil:.0%} d'achats communs) : remplace l'une des deux par une autre famille d'idées")
        for x, y, part, com in ps:
            print(f"  {x} et {y} : {part:.0%} ({com} tokens communs)")
    else:
        print(f"\naucune paire au-dessus de {a.seuil:.0%} : les places testent des idées différentes")


if __name__ == "__main__":
    main()
