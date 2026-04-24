# LehrerAgent – API-Schlüssel einrichten
# Wird von install.bat aufgerufen. Nicht direkt ausführen.

param(
    [string]$ConfigFile
)

$config = Get-Content $ConfigFile -Raw -Encoding UTF8

# Nur abfragen wenn noch kein echter Key eingetragen ist
if ($config -notmatch '\$\{ANTHROPIC_API_KEY\}') {
    Write-Host "        OK: API-Schlüssel bereits konfiguriert."
    exit 0
}

Add-Type -AssemblyName Microsoft.VisualBasic

$message = @"
Bitte gib deinen API-Schlüssel ein.

Den Schlüssel bekommst du unter:
https://console.anthropic.com/

(Anmeldung erforderlich, der Schlüssel beginnt mit: sk-ant-...)
"@

$key = [Microsoft.VisualBasic.Interaction]::InputBox(
    $message,
    "LehrerAgent – Einrichtung",
    ""
)

if ($key -and $key.Length -gt 20) {
    $config = $config -replace '\$\{ANTHROPIC_API_KEY\}', $key
    $config | Set-Content $ConfigFile -Encoding UTF8
    Write-Host "        OK: API-Schlüssel gespeichert."
} elseif ($key) {
    Write-Host "        HINWEIS: Der eingegebene Schlüssel scheint ungültig (zu kurz)."
    Write-Host "                 Bitte später manuell in die Konfigurationsdatei eintragen."
} else {
    Write-Host "        HINWEIS: Kein Schlüssel eingegeben."
    Write-Host "                 Bitte später manuell eintragen (siehe SETUP.md)."
}
