@echo off
REM Bilan des tests : rapports a jour + evaluation des regles pre-enregistrees. Lecture seule.
cd /d "%~dp0"
echo Mise a jour des rapports...
uv run python -m copysim report --report live_temoin
set CS_DATA_DIR=data_filtre& uv run python -m copysim report --report live_filtre
set CS_DATA_DIR=data_raven& set CS_BOT_FEE_PCT=0& set CS_TX_FEE_SOL=0.0027& uv run python -m copysim report --report live_raven
set CS_BOT_FEE_PCT=& set CS_TX_FEE_SOL=
set CS_DATA_DIR=data_cands& set CS_SIZE=0.05& uv run python -m copysim report --report live_candidats
set CS_DATA_DIR=& set CS_SIZE=
uv run python -m copysim copy-check --dirs data data_filtre data_raven data_cands
echo.
echo Rapports dans %~dp0reports : live_*.md et copy_rules.md
start "" "%~dp0reports"
pause
