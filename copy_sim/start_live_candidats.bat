@echo off
REM Paper trading live sur les leaders "calmes" (non scalpeurs) trouves par le scout. Lecture seule.
REM La liste candidats.txt est remise a jour depuis GitHub a chaque demarrage.
cd /d "%~dp0"
set CS_DATA_DIR=data_cands
set CS_SIZE=0.05
set CS_MAX_OPEN=15
set CS_ROTATE_AFTER_LOSSES=0
:loop
curl -fsSL -o candidats.new https://raw.githubusercontent.com/liitlec/Copybot-Crypto/claude/polymarket-weather-sigma-resolution-olv0bs/copy_sim/candidats.txt && move /y candidats.new candidats.txt >nul
echo [%date% %time%] demarrage du test candidats...
uv run python -m copysim live --leaders candidats.txt --record-paths --report live_candidats
echo [%date% %time%] arret inattendu, redemarrage dans 15 s
timeout /t 15 >nul
goto loop
