"""Vérification anti-secrets avant commit (idée ECC, réécrite ici, sans dépendance).
Usage : python3 copy_sim/labo/verif_secrets.py  -> lit `git diff --cached`, code 1 si un secret probable est ajouté."""
import re, subprocess, sys

MOTIFS = {
    "clé privée": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "jeton GitHub": r"\bgh[pousr]_[A-Za-z0-9]{30,}",
    "clé AWS": r"\bAKIA[0-9A-Z]{16}\b",
    "clé Anthropic/OpenAI": r"\bsk-(ant-)?[A-Za-z0-9_-]{20,}",
    "jeton Slack": r"\bxox[abpr]-[A-Za-z0-9-]{10,}",
    "mot de passe en clair": r"(?i)\b(password|passwd|mot_de_passe|api_key|apikey|secret|token)\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]",
    "identifiant MT5": r"(?i)\b(login|compte)\b\s*[:=]\s*['\"]?\d{6,}",
}

def main():
    diff = subprocess.run(["git", "diff", "--cached", "-U0"], capture_output=True, text=True).stdout
    fichier, trouves = "?", []
    for ligne in diff.splitlines():
        if ligne.startswith("+++ "):
            fichier = ligne[6:]
        elif ligne.startswith("+") and not ligne.startswith("+++"):
            for nom, m in MOTIFS.items():
                if re.search(m, ligne):
                    trouves.append(f"{fichier}: {nom}: {ligne[1:80]}")
    for t in trouves:
        print("SECRET PROBABLE ->", t)
    print("verif_secrets :", "ÉCHEC" if trouves else "OK")
    sys.exit(1 if trouves else 0)

if __name__ == "__main__":
    main()
