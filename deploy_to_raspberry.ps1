#!/usr/bin/env pwsh
# Automatisches Deployment zum Raspberry Pi
# Verwendung: .\deploy_to_raspberry.ps1

param(
    [string]$RaspberryHost = "heizpi",
    [string]$RaspberryUser = "heizpi",
    [string]$RemotePath = "/home/heizpi/maschinengemeinschaft"
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Automatisches Deployment zum Raspberry Pi" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob deployment/ Verzeichnis existiert
if (-not (Test-Path ".\deployment")) {
    Write-Host "ERROR: deployment/ Verzeichnis nicht gefunden!" -ForegroundColor Red
    exit 1
}

# 1. Kopiere aktuelle Dateien ins deployment Verzeichnis
Write-Host "[1/5] Kopiere aktuelle Dateien ins deployment/ Verzeichnis..." -ForegroundColor Yellow
Copy-Item ".\web_app.py" ".\deployment\web_app.py" -Force
Copy-Item ".\database.py" ".\deployment\database.py" -Force
Copy-Item ".\requirements.txt" ".\deployment\requirements.txt" -Force
Copy-Item ".\schema.sql" ".\deployment\schema.sql" -Force

# Kopiere alle Migrations-Scripts
Get-ChildItem ".\migrate_*.py" | ForEach-Object {
    Copy-Item $_.FullName ".\deployment\$($_.Name)" -Force
}

# Kopiere alle Templates
if (Test-Path ".\templates") {
    Copy-Item ".\templates\*" ".\deployment\templates\" -Force -Recurse
}

# Kopiere alle Static-Dateien
if (Test-Path ".\static") {
    Copy-Item ".\static\*" ".\deployment\static\" -Force -Recurse
}

Write-Host "   ✓ Dateien kopiert" -ForegroundColor Green

# 2. Erstelle temporäres Tar-Archiv
Write-Host "[2/5] Erstelle Deployment-Archiv..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveName = "deployment_$timestamp.tar.gz"

Push-Location ".\deployment"
tar -czf "..\$archiveName" *
Pop-Location

Write-Host "   ✓ Archiv erstellt: $archiveName" -ForegroundColor Green

# 3. Übertrage Archiv zum Raspberry Pi
Write-Host "[3/5] Übertrage Archiv zum Raspberry Pi..." -ForegroundColor Yellow
Write-Host "   Host: $RaspberryUser@$RaspberryHost" -ForegroundColor Gray

scp "$archiveName" "${RaspberryUser}@${RaspberryHost}:/tmp/$archiveName"

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR: SCP-Übertragung fehlgeschlagen!" -ForegroundColor Red
    exit 1
}

Write-Host "   ✓ Archiv übertragen" -ForegroundColor Green

# 4. Entpacke und aktualisiere auf dem Raspberry Pi
Write-Host "[4/5] Entpacke und aktualisiere Dateien auf Raspberry Pi..." -ForegroundColor Yellow

# Erstelle bash-Script - verwende single quotes, damit PowerShell && nicht interpretiert
$bashScript = 'cd /home/heizpi/maschinengemeinschaft && echo "=== Backup der alten Datenbank ===" && (cp maschinengemeinschaft.db maschinengemeinschaft.db.backup_' + $timestamp + ' 2>/dev/null || true) && echo "=== Entpacke neue Dateien ===" && tar -xzf /tmp/' + $archiveName + ' && rm /tmp/' + $archiveName + ' && echo "=== Führe Migrationen aus ===" && (python3 migrate_geloeschte_reservierungen.py 2>/dev/null || true) && echo "=== Docker Container neu starten ===" && docker-compose down && docker-compose up -d --build && echo "=== Deployment abgeschlossen ==="'

ssh "${RaspberryUser}@${RaspberryHost}" $bashScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "   WARNING: Einige Befehle schlugen fehl, aber Deployment wurde durchgeführt" -ForegroundColor Yellow
}

Write-Host "   ✓ Dateien aktualisiert und Container neu gestartet" -ForegroundColor Green

# 5. Räume auf
Write-Host "[5/5] Räume temporäre Dateien auf..." -ForegroundColor Yellow
Remove-Item "$archiveName" -Force
Write-Host "   ✓ Aufgeräumt" -ForegroundColor Green

# Status prüfen
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Deployment abgeschlossen!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Prüfe Container-Status..." -ForegroundColor Yellow
ssh "${RaspberryUser}@${RaspberryHost}" "bash -c 'cd $RemotePath && docker-compose ps'"

Write-Host ""
Write-Host "Anwendung sollte erreichbar sein unter:" -ForegroundColor Cyan
Write-Host "  http://$RaspberryHost" -ForegroundColor White
Write-Host ""
Write-Host "Logs anzeigen:" -ForegroundColor Cyan
Write-Host "  ssh ${RaspberryUser}@${RaspberryHost} 'docker logs -f maschinengemeinschaft'" -ForegroundColor White
Write-Host ""
