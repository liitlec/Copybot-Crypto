@echo off
REM Paper trading live, strategie de base + filtre anti-rug. Lecture seule.
cd /d "%~dp0"
set CS_DATA_DIR=data_filtre
:loop
echo [%date% %time%] demarrage du test base + filtre anti-rug...
uv run python -m copysim live --leaders leaders_live.txt --rug-filter --report live_filtre
echo [%date% %time%] arret inattendu, redemarrage dans 15 s
timeout /t 15 >nul
goto loop
