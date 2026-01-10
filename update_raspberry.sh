#!/bin/bash
# Update der Web-Anwendung auf Raspberry Pi

echo "🔄 UPDATE: Maschinengemeinschaft Web-App"
echo ""

cd ~/maschinengemeinschaft

echo "1️⃣ Container stoppen..."
docker compose down

echo ""
echo "2️⃣ Container NEU BAUEN (mit aktualisierten Python-Dateien)..."
docker compose build --no-cache

echo ""
echo "3️⃣ Container starten..."
docker compose up -d

echo ""
echo "⏳ Warte 5 Sekunden..."
sleep 5

echo ""
echo "4️⃣ Status prüfen..."
docker ps | grep maschinengemeinschaft

echo ""
echo "5️⃣ Letzte Log-Zeilen:"
docker logs --tail 10 maschinengemeinschaft

echo ""
echo "✅ UPDATE ABGESCHLOSSEN!"
echo ""
echo "Web-App verfügbar unter: http://192.168.178.36:5000"
