@echo off
REM Paper trading live avec les reglages Raven (sans commission, frais Jito/priority). Lecture seule.
cd /d "%~dp0"
set CS_DATA_DIR=data_raven
set CS_BOT_FEE_PCT=0
set CS_TX_FEE_SOL=0.0027
set CS_ROTATE_AFTER_LOSSES=0
:loop
echo [%date% %time%] demarrage du test Raven...
uv run python -m copysim live --leaders leaders_live.txt --report live_raven
echo [%date% %time%] arret inattendu, redemarrage dans 15 s
timeout /t 15 >nul
goto loop
