#!/bin/bash
# Deploy auf alle Server
# mgs2 und mgs1 nur nach Bestätigung

set -e

echo "=== Deployment ==="

echo ""
echo ">>> MGV1 (Entwicklung)"
ssh mgserver@mgv1 "cd /opt/mgr && git pull origin main && cd deployment && docker compose restart web"

echo ""
echo "============================================"
echo "  Entwicklungs-Server aktualisiert!"
echo "  Bitte testen: http://mgv1:5000"
echo "============================================"
echo ""

read -p "MGS2 (REPLIKATION) aktualisieren? (j/n): " confirm2

if [[ "$confirm2" == "j" || "$confirm2" == "J" ]]; then
    echo ""
    echo ">>> MGS2 (Replikation)"
    ssh mgserver@mgs2 "cd /home/mgserver/mgserver && git pull origin main && cd deployment && docker-compose restart web"
    echo ""
    echo "  MGS2 aktualisiert! Testen: http://mgs2:5000"
    echo ""
fi

read -p "MGS1 (PRODUKTION) aktualisieren? (j/n): " confirm1

if [[ "$confirm1" == "j" || "$confirm1" == "J" ]]; then
    echo ""
    echo ">>> MGS1 (PRODUKTION)"
    ssh mgserver@mgs1 "cd /home/mgserver/mgserver && git pull origin main && cd deployment && docker-compose restart web"
    echo ""
    echo "=== Produktion aktualisiert! ==="
else
    echo ""
    echo "MGS1 wurde NICHT aktualisiert."
fi
