#!/bin/bash
# Vollständiges Update auf Raspberry Pi
# Aufruf: ./update_raspberry_vollstaendig.sh

echo "🔄 VOLLSTÄNDIGES UPDATE: Maschinengemeinschaft"
echo "================================================"
echo ""

cd ~/maschinengemeinschaft

echo "1️⃣ Container stoppen..."
docker compose down

echo ""
echo "2️⃣ Migrationen ausführen..."
python migrate_aufwendungen.py
python migrate_reservierungen.py

echo ""
echo "3️⃣ Container NEU BAUEN (mit ReportLab für PDF-Export)..."
docker compose build --no-cache

echo ""
echo "4️⃣ Container starten..."
docker compose up -d

echo ""
echo "⏳ Warte 5 Sekunden..."
sleep 5

echo ""
echo "5️⃣ Status prüfen..."
docker ps | grep maschinengemeinschaft

echo ""
echo "6️⃣ Letzte Log-Zeilen:"
docker logs --tail 20 maschinengemeinschaft

echo ""
echo "✅ UPDATE ABGESCHLOSSEN!"
echo ""
echo "Neue Features:"
echo "  ✓ Treibstoffpreis-Eingabe in Einstellungen"
echo "  ✓ Maschinenreservierungen (Datum, Uhrzeit)"
echo "  ✓ Reservierungsanzeige im Dashboard"
echo "  ✓ Stornierungsfunktion"
echo "  ✓ Jährliche Aufwendungen für Maschinen"
echo "  ✓ Erweiterte Rentabilitätsrechnung"
echo "  ✓ PDF-Export für Rentabilitätsbericht"
echo ""
