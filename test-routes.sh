#!/bin/bash
# Test alle Routen auf einem Server
# Verwendung: ./test-routes.sh [server]
# Beispiel: ./test-routes.sh mgv1

SERVER=${1:-mgv1}
BASE_URL="http://${SERVER}:5000"
SETUP_TOKEN="mgr-setup-2026"

echo "=== Route-Test für $SERVER ==="
echo ""

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

test_route() {
    local path=$1
    local expected=${2:-200,302}
    local code=$(curl -s -o /dev/null -w '%{http_code}' "${BASE_URL}${path}")

    if [[ "$expected" == *"$code"* ]]; then
        echo -e "${GREEN}OK${NC}  [$code] $path"
        return 0
    else
        echo -e "${RED}FAIL${NC} [$code] $path (erwartet: $expected)"
        return 1
    fi
}

ERRORS=0

echo "--- Öffentliche Routen ---"
test_route "/" || ((ERRORS++))
test_route "/login" || ((ERRORS++))
test_route "/setup/?token=${SETUP_TOKEN}" "200" || ((ERRORS++))
test_route "/setup/status?token=${SETUP_TOKEN}" "200" || ((ERRORS++))

echo ""
echo "--- Geschützte Routen (erwarte 302 Redirect) ---"
test_route "/dashboard" "302" || ((ERRORS++))
test_route "/meine-einsaetze" "302" || ((ERRORS++))
test_route "/meine-reservierungen" "302" || ((ERRORS++))
test_route "/reservierungen-kalender" "302" || ((ERRORS++))
test_route "/abstimmungen" "302" || ((ERRORS++))
test_route "/meine-antraege" "302" || ((ERRORS++))
test_route "/nachrichten" "302" || ((ERRORS++))

echo ""
echo "--- Admin-Routen (erwarte 302 Redirect) ---"
test_route "/admin" "302" || ((ERRORS++))
test_route "/admin/benutzer" "302" || ((ERRORS++))
test_route "/admin/maschinen" "302" || ((ERRORS++))
test_route "/admin/gemeinschaften" "302" || ((ERRORS++))
test_route "/admin/abstimmungen" "302" || ((ERRORS++))
test_route "/admin/antraege" "302" || ((ERRORS++))

echo ""
echo "============================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}Alle Tests bestanden!${NC}"
else
    echo -e "${RED}$ERRORS Fehler gefunden!${NC}"
fi
echo "============================================"

exit $ERRORS
