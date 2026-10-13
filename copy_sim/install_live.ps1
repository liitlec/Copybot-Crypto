# Installe et lance les 3 paper tests live (lecture seule, aucun ordre reel, aucune cle privee).
# Usage (PowerShell) :
#   irm https://raw.githubusercontent.com/liitlec/Copybot-Crypto/claude/polymarket-weather-sigma-resolution-olv0bs/copy_sim/install_live.ps1 | iex
$ErrorActionPreference = "Stop"
$branch = "claude/polymarket-weather-sigma-resolution-olv0bs"
$dest = Join-Path $env:USERPROFILE "copysim"

Write-Host "1/6 Telechargement du simulateur..."
$zip = Join-Path $env:TEMP "copysim.zip"
$tmp = Join-Path $env:TEMP "copysim_extract"
Invoke-WebRequest "https://github.com/liitlec/Copybot-Crypto/archive/refs/heads/$branch.zip" -OutFile $zip -UseBasicParsing
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
Expand-Archive $zip $tmp -Force
$src = Get-ChildItem $tmp -Directory | Select-Object -First 1
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item (Join-Path $src.FullName "copy_sim\*") $dest -Recurse -Force
Set-Location $dest

Write-Host "2/6 Configuration (.env reste sur ce PC, jamais envoye sur GitHub)..."
if (-not (Test-Path ".env")) {
  $rpc = Read-Host "URL RPC Helius (https://mainnet.helius-rpc.com/?api-key=...)"
  $st = Read-Host "Cle API Solana Tracker"
  @("SOLANA_RPC_URL=$rpc", "SOLANATRACKER_API_KEY=$st", "CS_POLL_S=1", "CS_BANKROLL_SOL=6.2", "CS_SIZE=0.1") |
    Set-Content ".env" -Encoding ascii
}
"515vh1DrPuwMATt9Zoq9kP4sJL9fyojA1dHJu4DQpNRp  # 515vh1" | Set-Content "leaders_live.txt" -Encoding ascii

Write-Host "3/6 Installation de uv / Python si besoin..."
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  powershell -ExecutionPolicy ByPass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
  $env:Path = (Join-Path $env:USERPROFILE ".local\bin") + ";" + $env:Path
}
uv venv --python 3.12
uv pip install -r requirements.txt

Write-Host "4/6 Lancement automatique a chaque ouverture de session..."
$startup = [Environment]::GetFolderPath("Startup")
$shell = New-Object -ComObject WScript.Shell
foreach ($bat in @("start_live.bat", "start_live_filtre.bat", "start_live_raven.bat", "start_sniper.bat")) {
  $lnk = $shell.CreateShortcut((Join-Path $startup ("copysim_" + $bat + ".lnk")))
  $lnk.TargetPath = Join-Path $dest $bat
  $lnk.WorkingDirectory = $dest
  $lnk.WindowStyle = 7  # fenetre reduite
  $lnk.Save()
}

Write-Host "5/6 Desactivation de la mise en veille sur secteur..."
try { powercfg /change standby-timeout-ac 0 } catch { Write-Host "  (a faire a la main : Parametres > Alimentation > Veille : Jamais)" }

Write-Host "6/6 Demarrage des 3 tests (temoin, base + anti-rug, Raven + anti-rug) et de l'enregistreur sniper..."
foreach ($bat in @("start_live.bat", "start_live_filtre.bat", "start_live_raven.bat", "start_sniper.bat")) {
  Start-Process -FilePath (Join-Path $dest $bat) -WorkingDirectory $dest -WindowStyle Minimized
}
Write-Host ""
Write-Host "OK. Suivi (mis a jour chaque minute) : $dest\reports\live_temoin.md, live_filtre.md, live_raven.md ; sniper : uv run python -m copysim snipe-report"
