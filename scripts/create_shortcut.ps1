# LehrerAgent – Desktop-Verknüpfung erstellen
# Wird von install.bat aufgerufen. Nicht direkt ausführen.

param(
    [string]$InstallDir
)

$shell     = New-Object -ComObject WScript.Shell
$desktop   = [System.Environment]::GetFolderPath('Desktop')
$target    = Join-Path $InstallDir "start.bat"
$shortcut  = $shell.CreateShortcut((Join-Path $desktop "LehrerAgent starten.lnk"))

$shortcut.TargetPath       = $target
$shortcut.WorkingDirectory = $InstallDir
$shortcut.Description      = "LehrerAgent starten"
$shortcut.IconLocation     = "$env:SystemRoot\System32\imageres.dll,109"
$shortcut.Save()

Write-Host "        OK: Verknüpfung auf Desktop erstellt."
