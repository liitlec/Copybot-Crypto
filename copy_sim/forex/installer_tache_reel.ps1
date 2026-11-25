# Pont MT5 REEL (compte STARTRADER cent) : a lancer par Baptiste SUR SON PC, dans PowerShell, depuis ce dossier :
#   .\installer_tache_reel.ps1 -Terminal "C:\Program Files\STARTRADER MT5 cent\terminal64.exe"
# (le chemin du terminal64.exe du 2e MetaTrader 5, celui du compte cent ; voir copy_sim/labo/LANCER_REEL.md)
# Retirer :  Unregister-ScheduledTask -TaskName PontMT5Reel -Confirm:$false
#
# Ce script NE CREE PAS le fichier d'autorisation : sans AUTORISATION_REEL.json ecrit par Baptiste dans
# %USERPROFILE%\pont_mt5_reel, le pont reel tourne mais n'envoie AUCUN ordre.
# Le pont reel tourne depuis une copie figee a part (%USERPROFILE%\pont_mt5_reel) et un clone a part du depot
# (%USERPROFILE%\depot_reel) : il ne touche ni au pont demo (tache PontMT5), ni a son depot.
param([Parameter(Mandatory = $true)][string]$Terminal)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $Terminal)) { throw "terminal64.exe introuvable : $Terminal" }
$branche   = "claude/polymarket-weather-sigma-resolution-olv0bs"
$principal = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$depot     = Join-Path $env:USERPROFILE "depot_reel"
$dossier   = Join-Path $env:USERPROFILE "pont_mt5_reel"
if (-not (Test-Path (Join-Path $depot ".git"))) {
    $url = (& git -C $principal remote get-url origin).Trim()
    & git clone --branch $branche --single-branch $url $depot
    if ($LASTEXITCODE -ne 0) { throw "git clone a echoue" }
} else {
    & git -C $depot fetch origin $branche
    & git -C $depot checkout $branche
    & git -C $depot pull --ff-only origin $branche
}
New-Item -ItemType Directory -Force $dossier | Out-Null
Stop-ScheduledTask -TaskName "PontMT5Reel" -ErrorAction SilentlyContinue
foreach ($f in "pont_mt5.py", "pont_reel.py", "lanceur_robot.py", "acces_robot.py", "faux_mt5.py", "bac_a_sable.py",
             "tableau_bord.py", "tableau_bord.html", "tableau_bord.js") {
    Copy-Item (Join-Path $PSScriptRoot $f) $dossier -Force
}
$script  = Join-Path $dossier "pont_mt5.py"
$python  = (& python -c "import sys; print(sys.executable)").Trim()
$pythonw = Join-Path (Split-Path $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) { throw "pythonw.exe introuvable a cote de $python" }
$arguments = "`"$script`" --reel --terminal `"$Terminal`" --depot `"$depot`""
$action  = New-ScheduledTaskAction -Execute $pythonw -Argument $arguments -WorkingDirectory $dossier
$declen  = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$regles  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
           -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 1) `
           -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName "PontMT5Reel" -Action $action -Trigger $declen -Settings $regles -Force | Out-Null
Start-ScheduledTask -TaskName "PontMT5Reel"
Write-Host "Tache PontMT5Reel lancee depuis $dossier (clone du depot : $depot). Journal : $dossier\pont.log"
Write-Host "ARRET D'URGENCE : creer le fichier $dossier\STOP_PONT"
if (-not (Test-Path (Join-Path $dossier "AUTORISATION_REEL.json"))) {
    Write-Host "Pas encore d'AUTORISATION_REEL.json : le pont reel n'enverra AUCUN ordre (voir LANCER_REEL.md, etape 6)."
}
$raccourci = Join-Path ([Environment]::GetFolderPath("Desktop")) "Robot REEL en direct.url"
Set-Content -Path $raccourci -Value "[InternetShortcut]`r`nURL=http://127.0.0.1:8766/" -Encoding ASCII
Write-Host "Tableau de bord reel : http://127.0.0.1:8766/ (raccourci sur le bureau)"
