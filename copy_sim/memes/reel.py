"""Test en RÉEL avec de petites sommes (demandé par l'utilisateur le 05/11) : copie les achats et les ventes de la
caisse papier « ia » (IA chercheuse) sur un portefeuille Solana dédié, via Jupiter. Rien d'autre.

Sécurités écrites dans le code (en plus du réglage reel.json, qui ne peut que les resserrer) :
- le portefeuille ne doit contenir que le budget du test : c'est la vraie limite de perte ;
- mise fixe par achat (2 $ par défaut, entre MISE_MIN_USD et MISE_MAX_USD), MAX_POSITIONS positions au plus, MAX_ACHATS achats au total ;
- plus aucun achat si la valeur du portefeuille passe sous PLANCHER de sa valeur de départ (les ventes continuent) ;
- glissement limité (GLISSEMENT_BPS à l'achat ; à la vente, essais à 3 %, 6 % puis 15 % pour toujours sortir) ;
- un achat papier vieux de plus de RETARD_MAX_S secondes n'est pas copié (le prix a déjà bougé) ;
- pas d'achat si le prix du devis Jupiter dépasse le prix papier de plus de ECART_ACHAT_MAX (07/11 : GLITCHPEPE acheté
  32 % plus cher que le papier, en pleine flambée, puis vidé à −95 %) ;
- arrêt d'urgence : fichier STOP_REEL à côté de reel.py ou dans data/ (plus aucun achat), ou "actif": false dans reel.json.

Depuis le 06/11 (mises à jour automatiques du papier) : ce script tourne sous son propre utilisateur, dans son propre
dossier (--sortie : reel.jsonl, reel_etat.json), et ne fait que LIRE les fichiers du papier (--dir : trades.jsonl,
state.json). Le code du papier, qui peut changer sans validation, ne peut donc ni lire la clé ni modifier cet état.

La clé privée reste dans wallet.json (format solana-keygen, lisible seulement par l'utilisateur memes) et n'est
jamais affichée ni envoyée : seule la transaction signée part vers le réseau. Chaque ordre est noté dans
data/reel.jsonl avec le prix obtenu et le prix du jumeau papier.

Usage : python3 reel.py --dir /opt/memes_paper/data            (boucle)
        python3 reel.py --creer-portefeuille                   (crée wallet.json, affiche l'adresse à alimenter)
        python3 reel.py --dir /opt/memes_paper/data --etat     (solde, positions, bilan)"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
SOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
JUP = "https://lite-api.jup.ag/swap/v1"
RPC_DEFAUT = "https://api.mainnet-beta.solana.com"
# plafonds durs : reel.json peut les baisser, jamais les dépasser
MISE_MAX_USD, MAX_POSITIONS, MAX_ACHATS, PLANCHER = 25.0, 3, 20, 0.5
GLISSEMENT_BPS, VENTE_BPS, RETARD_MAX_S = 300, (300, 600, 1500), 120
ECART_ACHAT_MAX = 0.10  # devis au plus 10 % au-dessus du prix papier (07/11) ; reel.json peut seulement le baisser
FRAIS_PRIO_MAX = 100_000  # lamports (0,0001 SOL, ~0,01 $) par transaction au plus
MISE_MIN_USD, MISE_DEFAUT_USD = 1.0, 2.0  # premier test (05/11) : de toutes petites mises
PROGRAMMES_JETON = ("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
UA = {"User-Agent": "memes-reel/1.0", "Content-Type": "application/json"}


def http(url, data=None, timeout=30):
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=UA, method="POST" if body else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


class Rpc:
    def __init__(self, url):
        self.url = url

    def __call__(self, method, params):
        r = http(self.url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        if "error" in r:
            raise RuntimeError(f"RPC {method} : {r['error']}")
        return r["result"]

    def solde_sol(self, pub):
        return self("getBalance", [pub, {"commitment": "confirmed"}])["value"] / 1e9

    def comptes_jeton(self, pub, mint):
        """[(adresse du compte, programme du jeton, montant brut)] des comptes de ce jeton."""
        r = self("getTokenAccountsByOwner", [pub, {"mint": mint}, {"encoding": "jsonParsed", "commitment": "confirmed"}])
        return [(acc["pubkey"], acc["account"]["owner"], int(acc["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"]))
                for acc in r["value"]]

    def decimales(self, mint):
        return int(self("getTokenSupply", [mint])["value"]["decimals"])

    def solde_jeton(self, pub, mint):
        """(montant brut, décimales) du jeton détenu, tous comptes confondus."""
        r = self("getTokenAccountsByOwner", [pub, {"mint": mint}, {"encoding": "jsonParsed", "commitment": "confirmed"}])
        brut, dec = 0, 0
        for acc in r["value"]:
            ta = acc["account"]["data"]["parsed"]["info"]["tokenAmount"]
            brut += int(ta["amount"])
            dec = int(ta["decimals"])
        return brut, dec


def lire_cle(path):
    from solders.keypair import Keypair
    return Keypair.from_bytes(bytes(json.loads(Path(path).read_text())))


def creer_portefeuille(path):
    from solders.keypair import Keypair
    path = Path(path)
    if path.exists():
        print(f"{path} existe déjà : rien n'est créé (adresse : {lire_cle(path).pubkey()})")
        return
    kp = Keypair()
    old = os.umask(0o077)
    try:
        path.write_text(json.dumps(list(bytes(kp))))
    finally:
        os.umask(old)
    os.chmod(path, 0o600)
    print(f"Portefeuille créé : {path} (clé privée dans ce fichier, à ne jamais partager)")
    print(f"Adresse à alimenter avec le budget du test (en SOL) : {kp.pubkey()}")


def fermer_comptes_vides(rpc, kp, mint):
    """Ferme les comptes de jeton vides après une vente : chaque compte bloque ~0,002 SOL (~0,19 $), soit 10 % d'une
    mise de 2 $ ; la fermeture les rend au portefeuille. Renvoie le nombre de comptes fermés."""
    from solders.hash import Hash
    from solders.instruction import AccountMeta, Instruction
    from solders.message import Message
    from solders.pubkey import Pubkey
    from solders.transaction import Transaction
    vides = [(a, prog) for a, prog, brut in rpc.comptes_jeton(str(kp.pubkey()), mint) if brut == 0 and prog in PROGRAMMES_JETON]
    if not vides:
        return 0
    moi = kp.pubkey()
    ixs = [Instruction(Pubkey.from_string(prog), bytes([9]),  # 9 = CloseAccount (programme SPL Token et Token-2022)
                       [AccountMeta(Pubkey.from_string(a), False, True), AccountMeta(moi, False, True),
                        AccountMeta(moi, True, False)]) for a, prog in vides]
    bh = Hash.from_string(rpc("getLatestBlockhash", [{"commitment": "confirmed"}])["value"]["blockhash"])
    tx = Transaction([kp], Message.new_with_blockhash(ixs, moi, bh), bh)
    rpc("sendTransaction", [base64.b64encode(bytes(tx)).decode(), {"encoding": "base64", "maxRetries": 3}])
    return len(vides)


def prix_sol():
    q = http(f"{JUP}/quote?inputMint={SOL}&outputMint={USDC}&amount=100000000&slippageBps=50")
    return int(q["outAmount"]) / 1e6 / 0.1


class Refus(Exception):
    """Devis refusé avant tout envoi (rien n'a été signé)."""


def echanger(rpc, kp, entree, sortie, montant_brut, bps, garde=None):
    """Échange montant_brut (unités de base) du jeton `entree` contre `sortie`. Renvoie (signature, devis).
    `garde(devis)` peut lever Refus pour annuler avant la signature."""
    from solders.transaction import VersionedTransaction
    q = http(f"{JUP}/quote?inputMint={entree}&outputMint={sortie}&amount={int(montant_brut)}&slippageBps={bps}")
    if garde:
        garde(q)
    sw = http(f"{JUP}/swap", {"quoteResponse": q, "userPublicKey": str(kp.pubkey()), "wrapAndUnwrapSol": True,
                              "dynamicComputeUnitLimit": True,
                              "prioritizationFeeLamports": {"priorityLevelWithMaxLamports": {
                                  "maxLamports": FRAIS_PRIO_MAX, "priorityLevel": "high"}}})
    tx = VersionedTransaction.from_bytes(base64.b64decode(sw["swapTransaction"]))
    signee = VersionedTransaction(tx.message, [kp])
    sig = rpc("sendTransaction", [base64.b64encode(bytes(signee)).decode(),
                                  {"encoding": "base64", "skipPreflight": False, "maxRetries": 3}])
    for _ in range(40):  # confirmation : 60 s au plus
        time.sleep(1.5)
        st = rpc("getSignatureStatuses", [[sig]])["value"][0]
        if st and st.get("err"):
            raise RuntimeError(f"transaction refusée : {st['err']}")
        if st and st.get("confirmationStatus") in ("confirmed", "finalized"):
            return sig, q
    raise RuntimeError(f"transaction non confirmée en 60 s : {sig}")


class Reel:
    def __init__(self, d, cfg, sortie=None):
        self.d, self.cfg = Path(d), cfg  # d : fichiers du papier (lecture seule)
        self.out = Path(sortie) if sortie else self.d  # nos propres fichiers
        self.etat_p = self.out / "reel_etat.json"
        self.etat = json.loads(self.etat_p.read_text()) if self.etat_p.exists() else {}
        self.rpc = Rpc(cfg.get("rpc") or RPC_DEFAUT)
        self.kp = lire_cle(ICI / "wallet.json")
        self.pub = str(self.kp.pubkey())

    def noter(self, rec):
        rec = dict(rec, t=round(time.time(), 1))
        with (self.out / "reel.jsonl").open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(json.dumps(rec, ensure_ascii=False), flush=True)

    def sauver(self):
        tmp = self.etat_p.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.etat, indent=1))
        tmp.replace(self.etat_p)

    def valeur(self, psol):
        """Valeur du portefeuille en dollars : SOL + positions au prix d'achat (estimation prudente)."""
        return self.rpc.solde_sol(self.pub) * psol + sum(p["usd"] for p in self.etat["positions"].values())

    def demarrer(self):
        f = self.d / "trades.jsonl"
        if "offset" not in self.etat:  # premier lancement : on ne rejoue pas l'historique
            while self.rpc.solde_sol(self.pub) < 0.05:  # le plancher se calcule sur le portefeuille alimenté
                print(f"en attente d'au moins 0,05 SOL sur {self.pub}", flush=True)
                time.sleep(60)
            psol = prix_sol()
            self.etat.update(offset=f.stat().st_size if f.exists() else 0, positions={}, achats=0,
                             depart_usd=round(self.rpc.solde_sol(self.pub) * psol, 2), adresse=self.pub)
            self.sauver()
            self.noter({"event": "depart", "adresse": self.pub, "valeur_usd": self.etat["depart_usd"]})

    def acheter(self, ev):
        mint, cfg = ev["token"], self.cfg
        mise = min(max(float(cfg.get("mise_usd", MISE_DEFAUT_USD)), MISE_MIN_USD), MISE_MAX_USD)
        raison = None
        if not cfg.get("actif", True) or any((x / "STOP_REEL").exists() for x in (ICI, self.out, self.d)):
            raison = "arrêt demandé"
        elif mint in self.etat["positions"]:
            raison = "déjà détenu"
        elif len(self.etat["positions"]) >= min(int(cfg.get("max_positions", MAX_POSITIONS)), MAX_POSITIONS):
            raison = "positions au maximum"
        elif self.etat["achats"] >= min(int(cfg.get("max_achats", MAX_ACHATS)), MAX_ACHATS):
            raison = f"{MAX_ACHATS} achats atteints : fin du test, faire le bilan"
        elif time.time() - ev.get("t_reel", ev.get("t", time.time())) > RETARD_MAX_S:  # 06/11 : heure réelle
            raison = "achat papier trop ancien"
        if raison:
            return self.noter({"event": "achat_ignore", "token": mint, "nom": ev.get("name"), "raison": raison})
        psol = prix_sol()
        if self.valeur(psol) < max(float(cfg.get("plancher", PLANCHER)), PLANCHER) * self.etat["depart_usd"]:
            return self.noter({"event": "achat_ignore", "token": mint, "nom": ev.get("name"),
                               "raison": "portefeuille sous le plancher : plus d'achat"})
        lamports = int(mise / psol * 1e9)
        if self.rpc.solde_sol(self.pub) * 1e9 < lamports + 10_000_000:  # garder 0,01 SOL pour les frais
            return self.noter({"event": "achat_ignore", "token": mint, "nom": ev.get("name"), "raison": "solde SOL insuffisant"})
        ecart_max = min(float(cfg.get("ecart_achat_max", ECART_ACHAT_MAX)), ECART_ACHAT_MAX)

        def garde(q):  # 07/11 : prix du devis comparé au prix papier, avant toute signature
            if not ev.get("px_in"):
                return
            try:
                dec = self.rpc.decimales(mint)
                px = mise / (int(q["outAmount"]) / 10 ** dec)
            except Exception as exc:
                raise Refus(f"prix du devis illisible ({str(exc)[:80]})")
            if px / ev["px_in"] - 1 > ecart_max:
                raise Refus(f"devis {px / ev['px_in'] - 1:+.0%} au-dessus du prix papier (au plus {ecart_max:+.0%})")
        t0 = time.time()
        try:
            sig, q = echanger(self.rpc, self.kp, SOL, mint, lamports, GLISSEMENT_BPS, garde)
        except Refus as exc:
            return self.noter({"event": "achat_ignore", "token": mint, "nom": ev.get("name"), "raison": str(exc)})
        except Exception as exc:
            # 06/11 : une transaction confirmée en retard arrive quand même ; sans cette vérification, les jetons
            # resteraient dans le portefeuille sans jamais être revendus
            time.sleep(20)
            brut, _ = self.rpc.solde_jeton(self.pub, mint)
            if not brut:
                return self.noter({"event": "achat_echec", "token": mint, "nom": ev.get("name"), "erreur": str(exc)[:300]})
            sig, q = "confirmée en retard", {}
            self.noter({"event": "achat_tardif", "token": mint, "nom": ev.get("name"), "erreur": str(exc)[:200]})
        brut, dec = 0, 0
        for _ in range(6):  # le solde peut mettre quelques secondes à apparaître
            brut, dec = self.rpc.solde_jeton(self.pub, mint)
            if brut:
                break
            time.sleep(3)
        qte = brut / 10 ** dec if brut else None
        px_reel = mise / qte if qte else None
        self.etat["achats"] += 1
        self.etat["positions"][mint] = {"nom": ev.get("name"), "usd": mise, "qte": qte, "px_reel": px_reel,
                                        "px_papier": ev.get("px_in"), "t": time.time(), "sig": sig}
        self.sauver()
        self.noter({"event": "achat", "token": mint, "nom": ev.get("name"), "usd": mise, "sig": sig,
                    "px_reel": px_reel, "px_papier": ev.get("px_in"), "secondes": round(time.time() - t0, 1),
                    "ecart_achat": round(px_reel / ev["px_in"] - 1, 4) if px_reel and ev.get("px_in") else None})

    def vendre(self, rec, tries=VENTE_BPS):
        mint = rec["token"]
        pos = self.etat["positions"].get(mint)
        if not pos or time.time() < pos.get("reessai", 0):
            return
        brut, dec = self.rpc.solde_jeton(self.pub, mint)
        if not brut:
            self.etat["positions"].pop(mint)
            self.sauver()
            return self.noter({"event": "vente_impossible", "token": mint, "nom": pos["nom"], "raison": "solde nul"})
        psol, err = prix_sol(), None
        sol_avant = self.rpc.solde_sol(self.pub)
        for bps in tries:
            try:
                sig, q = echanger(self.rpc, self.kp, mint, SOL, brut, bps)
                recu = (self.rpc.solde_sol(self.pub) - sol_avant) * psol
                self.etat["positions"].pop(mint)
                self.sauver()
                try:
                    time.sleep(2)
                    fermes = fermer_comptes_vides(self.rpc, self.kp, mint)
                except Exception:
                    fermes = 0
                return self.noter({"event": "vente", "token": mint, "nom": pos["nom"], "sig": sig, "comptes_fermes": fermes,
                                   "usd_mise": pos["usd"], "usd_recu": round(recu, 2),
                                   "ret_reel": round(recu / pos["usd"] - 1, 4), "ret_papier": rec.get("ret"),
                                   "raison_papier": rec.get("reason"), "glissement_bps": bps})
            except Exception as exc:
                err = str(exc)[:300]
        pos["reessai"] = time.time() + 120  # nouvel essai dans 2 min (rattrapage), pas toutes les 5 s
        self.sauver()
        self.noter({"event": "vente_echec", "token": mint, "nom": pos["nom"], "erreur": err})

    def tourner(self):
        self.demarrer()
        while True:
            self.une_passe()
            time.sleep(5)

    def une_passe(self):
        f = self.d / "trades.jsonl"
        if True:
            try:
                if f.exists() and f.stat().st_size < self.etat["offset"]:  # fichier remplacé (remise à zéro)
                    self.etat["offset"] = 0
                if f.exists() and f.stat().st_size > self.etat["offset"]:
                    with f.open() as fh:
                        fh.seek(self.etat["offset"])
                        lignes = fh.readlines()
                        self.etat["offset"] = fh.tell()
                    self.sauver()
                    for ln in lignes:
                        try:
                            ev = json.loads(ln)
                        except ValueError:
                            continue
                        if ev.get("book") != self.cfg.get("caisse", "ia"):
                            continue
                        if ev.get("event") == "achat":
                            self.acheter(ev)
                        elif "ret" in ev:
                            self.vendre(ev)
                # une vente ratée est retentée tant que la position papier est fermée
                # 06/11 : state.json n'est réécrit qu'en fin de cycle, plusieurs minutes après l'achat ; une position
                # n'est jugée fermée en papier que si l'état a été réécrit après notre achat et ne la contient plus
                ouvertes, maj = self.ouvertes_papier()
                for mint in list(self.etat["positions"]):
                    if ouvertes is not None and mint not in ouvertes and maj > self.etat["positions"][mint]["t"] + 30:
                        self.vendre({"token": mint, "reason": "rattrapage : position papier fermée"})
            except Exception as exc:
                self.noter({"event": "erreur", "erreur": repr(exc)[:300]})
                time.sleep(30)

    def ouvertes_papier(self):
        """(positions ouvertes de la caisse papier, heure de dernière écriture de state.json)."""
        f = self.d / "state.json"
        try:
            maj = f.stat().st_mtime
            s = json.loads(f.read_text())
            return set(s["books"][self.cfg.get("caisse", "ia")]["open"]), maj
        except Exception:
            return None, 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ICI / "data"), help="fichiers du papier (lecture)")
    ap.add_argument("--sortie", default=None, help="dossier de reel.jsonl et reel_etat.json (par défaut --dir)")
    ap.add_argument("--creer-portefeuille", action="store_true")
    ap.add_argument("--etat", action="store_true")
    a = ap.parse_args()
    if a.creer_portefeuille:
        return creer_portefeuille(ICI / "wallet.json")
    if not (ICI / "wallet.json").exists():
        print("pas de portefeuille (wallet.json) : test réel inactif. Créer avec --creer-portefeuille.", flush=True)
        while True:  # le service attend qu'un portefeuille soit créé et alimenté
            time.sleep(60)
            if (ICI / "wallet.json").exists():
                break
    cfg_p = ICI / "reel.json"
    cfg = json.loads(cfg_p.read_text()) if cfg_p.exists() else {}
    r = Reel(a.dir, cfg, a.sortie)
    if a.etat:
        psol = prix_sol()
        print(f"adresse {r.pub} ; SOL {r.rpc.solde_sol(r.pub):.4f} ({r.rpc.solde_sol(r.pub) * psol:.2f} $) ; "
              f"positions {list((r.etat.get('positions') or {}).keys())} ; achats {r.etat.get('achats', 0)}")
        return
    r.tourner()


if __name__ == "__main__":
    sys.exit(main())
