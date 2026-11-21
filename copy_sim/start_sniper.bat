@echo off
REM Enregistrement des nouveaux tokens Pump.fun pour le paper test sniper. Lecture seule.
cd /d "%~dp0"
:loop
echo [%date% %time%] demarrage de l'enregistreur sniper...
uv run python -m copysim snipe-record --dir data_sniper --horizon 120
echo [%date% %time%] arret inattendu, redemarrage dans 15 s
timeout /t 15 >nul
goto loop
