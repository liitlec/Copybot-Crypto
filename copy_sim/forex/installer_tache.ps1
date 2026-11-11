# Lance le pont MT5 a chaque ouverture de session Windows (MT5 a besoin de la session ouverte).
# A lancer une fois, dans PowerShell, depuis ce dossier :  .\installer_tache.ps1
# Retirer :  Unregister-ScheduledTask -TaskName PontMT5 -Confirm:$false
$script  = Join-Path $PSScriptRoot "pont_mt5.py"
$pythonw = (Get-Command pythonw.exe -ErrorAction Stop).Source
$action  = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$script`"" -WorkingDirectory $PSScriptRoot
$declen  = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$regles  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
           -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName "PontMT5" -Action $action -Trigger $declen -Settings $regles -Force | Out-Null
Start-ScheduledTask -TaskName "PontMT5"
Write-Host "Tache PontMT5 installee et lancee. Journal : $PSScriptRoot\pont.log"
