# Lance le pont MT5 a chaque ouverture de session Windows (MT5 a besoin de la session ouverte).
# A lancer une fois, dans PowerShell, depuis ce dossier :  .\installer_tache.ps1
# Retirer :  Unregister-ScheduledTask -TaskName PontMT5 -Confirm:$false
#
# Le pont tourne depuis une COPIE FIGEE hors du depot (%USERPROFILE%\pont_mt5) : le git pull qu'il fait chaque minute
# ne peut donc pas changer son code. Nouvelle version relue = relancer ce script.
$depot   = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$dossier = Join-Path $env:USERPROFILE "pont_mt5"
New-Item -ItemType Directory -Force $dossier | Out-Null
Stop-ScheduledTask -TaskName "PontMT5" -ErrorAction SilentlyContinue   # l'ancienne version s'arrete d'abord
foreach ($f in "pont_mt5.py", "lanceur_robot.py", "acces_robot.py", "faux_mt5.py", "bac_a_sable.py",
             "tableau_bord.py", "tableau_bord.html", "tableau_bord.js") {
    Copy-Item (Join-Path $PSScriptRoot $f) $dossier -Force
}
$script  = Join-Path $dossier "pont_mt5.py"
# vrai chemin de pythonw (l'alias WindowsApps ne marche pas toujours dans le Planificateur)
$python  = (& python -c "import sys; print(sys.executable)").Trim()
$pythonw = Join-Path (Split-Path $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) { throw "pythonw.exe introuvable a cote de $python" }
$action  = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$script`" --depot `"$depot`"" -WorkingDirectory $dossier
$declen  = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$regles  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
           -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 1) `
           -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName "PontMT5" -Action $action -Trigger $declen -Settings $regles -Force | Out-Null
Start-ScheduledTask -TaskName "PontMT5"
Write-Host "Tache PontMT5 lancee depuis $dossier. Journal : $dossier\pont.log ; arret d'urgence : $dossier\STOP_PONT"
# raccourci du tableau de bord sur le bureau (lecture seule, 127.0.0.1)
$raccourci = Join-Path ([Environment]::GetFolderPath("Desktop")) "Robot du labo en direct.url"
Set-Content -Path $raccourci -Value "[InternetShortcut]`r`nURL=http://127.0.0.1:8765/" -Encoding ASCII
Write-Host "Tableau de bord : http://127.0.0.1:8765/ (raccourci sur le bureau)"
