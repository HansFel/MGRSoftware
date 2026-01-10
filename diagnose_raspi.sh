#!/bin/bash
# Diagnose: Welche Dateien sind auf dem Raspberry Pi?

echo "🔍 DIAGNOSE - Web-App Status"
echo ""

cd ~/maschinengemeinschaft

echo "1️⃣ Prüfe ob neue Routen in web_app.py vorhanden sind:"
if grep -q "admin_benutzer_neu" web_app.py; then
    echo "   ✅ admin_benutzer_neu Route gefunden"
else
    echo "   ❌ admin_benutzer_neu Route FEHLT"
fi

if grep -q "admin_maschinen_neu" web_app.py; then
    echo "   ✅ admin_maschinen_neu Route gefunden"
else
    echo "   ❌ admin_maschinen_neu Route FEHLT"
fi

echo ""
echo "2️⃣ Prüfe Templates:"
if [ -f "templates/admin_benutzer_form.html" ]; then
    echo "   ✅ admin_benutzer_form.html vorhanden"
else
    echo "   ❌ admin_benutzer_form.html FEHLT"
fi

if [ -f "templates/admin_maschinen_form.html" ]; then
    echo "   ✅ admin_maschinen_form.html vorhanden"
else
    echo "   ❌ admin_maschinen_form.html FEHLT"
fi

echo ""
echo "3️⃣ Container Status:"
docker ps -a | grep maschinengemeinschaft

echo ""
echo "4️⃣ Container Logs (letzte 5 Zeilen):"
docker logs --tail 5 maschinengemeinschaft

echo ""
echo "📌 EMPFEHLUNG:"
echo "   Wenn Dateien fehlen, führen Sie aus:"
echo "   1. Container stoppen: docker compose down"
echo "   2. Container neu bauen: docker compose build --no-cache"
echo "   3. Container starten: docker compose up -d"
