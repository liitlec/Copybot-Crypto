@echo off
REM Paper trading live sur les meilleurs wallets valides (top.txt, mis a jour depuis GitHub a chaque demarrage). Lecture seule.
cd /d "%~dp0"
set CS_DATA_DIR=data_top
set CS_SIZE=0.1
set CS_ROTATE_AFTER_LOSSES=0
:loop
curl -fsSL -o top.new https://raw.githubusercontent.com/liitlec/Copybot-Crypto/claude/polymarket-weather-sigma-resolution-olv0bs/copy_sim/top.txt && move /y top.new top.txt >nul
echo [%date% %time%] demarrage du test top wallets...
uv run python -m copysim live --leaders top.txt --record-paths --report live_top
echo [%date% %time%] arret inattendu, redemarrage dans 15 s
timeout /t 15 >nul
goto loop
