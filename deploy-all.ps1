# MGR Software - Deployment Script
# Aktualisiert alle Server und synchronisiert Datenbanken

param(
    [switch]$SyncDB,        # Datenbank von mgs2 auf andere Server kopieren
    [switch]$SkipBuild,     # Container nicht neu bauen
    [string]$Only           # Nur bestimmten Server: mgs1, mgs2, mgv1
)

$servers = @{
    "mgs1" = @{
        host = "mgserver@mgs1"
        path = "/opt/mgr"
        compose = "docker-compose"
        sudo = $false
    }
    "mgs2" = @{
        host = "mgserver@mgs2"
        path = "/opt/mgr"
        compose = "docker-compose"
        sudo = $false
    }
    "mgv1" = @{
        host = "mgserver@mgv1"
        path = "/opt/mgr"
        compose = "sudo docker compose"
        sudo = $true
    }
}

function Write-Status($message, $color = "Cyan") {
    Write-Host "`n=== $message ===" -ForegroundColor $color
}

function Invoke-ServerCommand($server, $command) {
    $info = $servers[$server]
    Write-Host "[$server] $command" -ForegroundColor Gray
    ssh $info.host $command
    return $LASTEXITCODE -eq 0
}

# Git Push zuerst
Write-Status "Git Push" "Yellow"
git add -A
git commit -m "Auto-deploy $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>$null
git push

# Server filtern
$targetServers = if ($Only) { @($Only) } else { $servers.Keys }

# Datenbank-Sync (mgs2 als Master)
if ($SyncDB) {
    Write-Status "Datenbank-Backup von mgs2" "Magenta"

    # Backup auf mgs2 erstellen
    Invoke-ServerCommand "mgs2" "docker exec maschinengemeinschaft-db pg_dump -U mgr_user -d maschinengemeinschaft > /tmp/db_backup.sql"

    # Backup herunterladen
    Write-Host "Backup herunterladen..." -ForegroundColor Gray
    scp mgserver@mgs2:/tmp/db_backup.sql "$env:TEMP\mgr_db_backup.sql"

    foreach ($server in $targetServers) {
        if ($server -eq "mgs2") { continue }

        Write-Status "Datenbank auf $server wiederherstellen" "Magenta"

        # Backup hochladen
        $info = $servers[$server]
        scp "$env:TEMP\mgr_db_backup.sql" "$($info.host):/tmp/db_backup.sql"

        # Restore
        $prefix = if ($info.sudo) { "sudo " } else { "" }
        Invoke-ServerCommand $server "${prefix}docker exec -i maschinengemeinschaft-db psql -U mgr_user -d maschinengemeinschaft < /tmp/db_backup.sql"
    }
}

# Server aktualisieren
foreach ($server in $targetServers) {
    $info = $servers[$server]
    $prefix = if ($info.sudo) { "sudo " } else { "" }

    Write-Status "Aktualisiere $server" "Green"

    # Git Pull
    Invoke-ServerCommand $server "cd $($info.path) && git pull"

    # Container stoppen und entfernen
    Write-Status "Container neu starten auf $server" "Yellow"
    Invoke-ServerCommand $server "cd $($info.path)/deployment && ${prefix}docker rm -f maschinengemeinschaft-app maschinengemeinschaft-caddy 2>/dev/null; ${prefix}$($info.compose) up -d --build web caddy"

    # Status prüfen
    Invoke-ServerCommand $server "${prefix}docker ps --format 'table {{.Names}}\t{{.Status}}' | grep maschinengemeinschaft"
}

Write-Status "Deployment abgeschlossen!" "Green"
Write-Host "`nServer-Status:" -ForegroundColor White
foreach ($server in $targetServers) {
    $info = $servers[$server]
    Write-Host "  $server : " -NoNewline
    $prefix = if ($info.sudo) { "sudo " } else { "" }
    ssh $info.host "${prefix}docker ps --format '{{.Names}}: {{.Status}}' | grep maschinengemeinschaft-app"
}
