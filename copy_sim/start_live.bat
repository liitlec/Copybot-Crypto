@echo off
REM Paper trading live (lecture seule, aucun ordre reel). Double-cliquer pour lancer.
cd /d "%~dp0"
if not exist .env (
  copy .env.example .env >nul
  echo Renseigne SOLANA_RPC_URL et SOLANATRACKER_API_KEY dans .env puis relance.
  notepad .env
  exit /b
)
if not exist leaders_live.txt (
  echo 515vh1DrPuwMATt9Zoq9kP4sJL9fyojA1dHJu4DQpNRp  # 515vh1> leaders_live.txt
)
if not exist .venv (
  uv venv
  uv pip install -r requirements.txt
)
:loop
echo [%date% %time%] demarrage du paper trading live...
uv run python -m copysim live --leaders leaders_live.txt
echo [%date% %time%] arret inattendu, redemarrage dans 15 s (Ctrl+C pour quitter)
timeout /t 15 >nul
goto loop
