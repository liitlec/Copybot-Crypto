# Données gRPC Pump.fun du 16/10/2026 (session cloud)

Données publiques de la chaîne Solana, enregistrées par le hub Yellowstone gRPC (Chainstack) de la session cloud
(`copysim grpc-hub`, recorder `copysim/pumprec.py`) et par le collecteur `nuit/pump_enrich.py`. Contenu non modifié :
lignes extraites telles quelles, filtre sur le champ `bt` du 16/10 de 07:30 à 18:00 heure de Paris.

| Fichier | Lignes | Période réelle (`bt`, heure de Paris) | Taille non compressée |
|---|---|---|---|
| `pumpfun_1610.jsonl` (en 3 morceaux gzip) | 1 082 876 | 16/10 08:14:31 → 17:36:54 | 693 094 464 octets |
| `pump_enrich_1610.jsonl.gz` | 15 467 | 16/10 08:20:36 → 17:36:51 | 27 092 071 octets |

L'enregistrement a commencé à 08:14 (reprise dans le cloud après le plantage du PC) et s'est arrêté à 17:36 (arrêt des tests cloud).

Recomposer :

```bash
cat pumpfun_1610.jsonl.gz.part00 pumpfun_1610.jsonl.gz.part01 pumpfun_1610.jsonl.gz.part02 | gunzip > pumpfun_1610.jsonl
gunzip -k pump_enrich_1610.jsonl.gz
```

PowerShell (Windows) :

```powershell
cmd /c copy /b pumpfun_1610.jsonl.gz.part00+pumpfun_1610.jsonl.gz.part01+pumpfun_1610.jsonl.gz.part02 pumpfun_1610.jsonl.gz
python -c "import gzip,shutil;[shutil.copyfileobj(gzip.open(f+'.gz'),open(f,'wb')) for f in ('pumpfun_1610.jsonl','pump_enrich_1610.jsonl')]"
```

SHA-256 :

```
4a4453fbc2f638405c9a65327d88a8aad3db1330a05880eca2fa350f7362a724  pumpfun_1610.jsonl.gz.part00
4217061d510c137982847f4c7cc78c3d6e61cac5eda0df0953d41c2a2896d4de  pumpfun_1610.jsonl.gz.part01
e5fb3751cee0f6536612f15aa19728871101df930c7bf60dbf8d869a5e1c7a24  pumpfun_1610.jsonl.gz.part02
88b24fee69abaa54062f2faed70bc8becf634c21a3b927b06851b2f4f9ebe5e3  pump_enrich_1610.jsonl.gz
12d5a94b3be23a51c0b9652e0e3f16042972378e8569419addae19e3143b7cc7  pumpfun_1610.jsonl            (après recomposition)
7057bfbab3f9189009aaa272e06033aecb8e806aa9757936a47af1beed756982  pump_enrich_1610.jsonl        (après décompression)
```

Note : 7 lignes de `pumpfun_1610.jsonl` sur ~868 000 ventes/achats ont un état de courbe aberrant isolé (vente mal lue) ;
le code de rejeu de la branche `claude/polymarket-weather-sigma-resolution-olv0bs` les écarte (`drop_spikes()` dans
`copysim/scalpgrpc.py`). Aucune clé ni aucun token dans ces fichiers (vérifié).
