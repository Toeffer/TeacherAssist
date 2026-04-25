# LehrerAgent – Konfiguration einrichten
# Wird von install.bat aufgerufen. Nicht direkt ausführen.

param(
    [string]$InstallDir,
    [string]$ConfigFile
)

# Pfade in der Config-Vorlage ersetzen
$template = Get-Content (Join-Path $InstallDir "openclaw_config_template.yaml") -Raw -Encoding UTF8
$toolsPath   = (Join-Path $InstallDir "tools").Replace("\", "/")
$pythonPath  = (Join-Path $InstallDir "tools\.venv\Scripts\python.exe").Replace("\", "/")

$template = $template -replace [regex]::Escape("/absoluter/pfad/zu/lehreragent/tools/.venv/bin/python"), $pythonPath
$template = $template -replace [regex]::Escape("/absoluter/pfad/zu/lehreragent/tools"), $toolsPath

$template | Set-Content $ConfigFile -Encoding UTF8
Write-Host "        OK: Konfigurationsdatei erstellt."
