# Web-Anwendung für Maschinengemeinschaft

## 🌐 Zugriff von extern (Mobiltelefon, Tablet, PC)

Die Webanwendung ermöglicht allen Mitgliedern den Zugriff von überall aus, um Maschineneinsätze zu erfassen und ihre Nutzungsdaten einzusehen.

## Installation und Einrichtung

### 1. Flask installieren

```powershell
# Im Projektverzeichnis
pip install -r requirements.txt
```

### 2. Datenbank vorbereiten

Stellen Sie sicher, dass die Datenbank initialisiert ist:

```powershell
python database.py
```

### 3. Benutzer mit Login-Daten anlegen

Öffnen Sie die Desktop-Anwendung (`main.py`) und legen Sie Benutzer mit Benutzername und Passwort an:

1. Starten Sie `python main.py`
2. Menü: **Stammdaten → Benutzer verwalten**
3. Klicken Sie auf **Neuer Benutzer**
4. Füllen Sie aus:
   - **Name** (Pflicht)
   - **Vorname**
   - **Benutzername** (für Web-Login)
   - **Passwort** (für Web-Login)
5. Speichern

**Wichtig**: Nur Benutzer mit Benutzername und Passwort können sich in der Web-App anmelden!

### 4. Web-Server starten

```powershell
python web_app.py
```

Der Server läuft dann auf: `http://localhost:5000`

### 5. Von anderen Geräten zugreifen

#### Im lokalen Netzwerk

1. Ermitteln Sie die IP-Adresse Ihres Computers:
   ```powershell
   ipconfig
   ```
   Suchen Sie nach der IPv4-Adresse (z.B. `192.168.1.100`)

2. Von anderen Geräten im gleichen Netzwerk:
   - Öffnen Sie Browser auf Mobiltelefon/Tablet
   - Geben Sie ein: `http://192.168.1.100:5000`
   - Melden Sie sich mit Benutzername und Passwort an

#### Von außerhalb (Internet)

Für Zugriff von außerhalb benötigen Sie:
- Eine Portweiterleitung in Ihrem Router (Port 5000)
- Eine feste IP-Adresse oder DynDNS
- **Empfehlung**: Verwenden Sie HTTPS und stärkere Sicherheit für Produktivbetrieb

## Funktionen der Web-App

### 🔐 Login
- Sichere Anmeldung mit Benutzername und Passwort
- Session-basierte Authentifizierung

### 📊 Dashboard
- Übersicht über eigene Statistiken
  - Anzahl Einsätze
  - Gesamt-Betriebsstunden
  - Treibstoffverbrauch
  - Kosten
- Letzte 10 Einsätze
- Schnellzugriff auf Funktionen

### ➕ Neuer Einsatz
- Einfaches Formular zum Erfassen von Einsätzen
- Automatische Übernahme des aktuellen Stundenzählers
- Automatische Berechnung der Betriebsstunden
- Mobile-optimiert

### 📋 Meine Einsätze
- Vollständige Liste aller eigenen Einsätze
- Übersichtliche Tabelle mit Summen
- Filtermöglichkeiten

### 🔑 Passwort ändern
- Benutzer können ihr Passwort selbst ändern
- Sichere Passwort-Validierung

## Produktivbetrieb

Für den Produktivbetrieb empfehlen wir:

### 1. WSGI-Server verwenden (z.B. Gunicorn)

```powershell
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

### 2. Hinter einem Reverse Proxy (z.B. Nginx)

Nginx-Konfiguration:
```nginx
server {
    listen 80;
    server_name ihre-domain.de;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. HTTPS aktivieren

Verwenden Sie Let's Encrypt für kostenlose SSL-Zertifikate:
```bash
certbot --nginx -d ihre-domain.de
```

### 4. Sicherheitseinstellungen

- Ändern Sie `app.secret_key` in `web_app.py` zu einem starken, zufälligen Schlüssel
- Deaktivieren Sie Debug-Modus (`debug=False`)
- Verwenden Sie starke Passwörter (mindestens 8 Zeichen)
- Regelmäßige Backups der Datenbank

## Mobile-Optimierung

Die Web-App ist bereits für Mobilgeräte optimiert:
- ✅ Responsive Design (Bootstrap 5)
- ✅ Touch-freundliche Buttons
- ✅ Übersichtliche Navigation
- ✅ Optimierte Formulare für Touchscreen

## Browser-Kompatibilität

Getestet mit:
- Chrome/Edge (empfohlen)
- Firefox
- Safari (iOS)
- Chrome Mobile (Android)

## Troubleshooting

### Problem: "Connection refused"
**Lösung**: Prüfen Sie, ob der Server läuft und die Firewall Port 5000 freigibt.

```powershell
# Windows Firewall-Regel hinzufügen
New-NetFirewallRule -DisplayName "Flask Web App" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

### Problem: "Ungültiger Benutzername oder Passwort"
**Lösung**: Stellen Sie sicher, dass der Benutzer in der Desktop-App mit Benutzername und Passwort angelegt wurde.

### Problem: Zugriff von anderem Gerät funktioniert nicht
**Lösung**: 
1. Prüfen Sie die IP-Adresse
2. Stellen Sie sicher, dass beide Geräte im gleichen Netzwerk sind
3. Deaktivieren Sie ggf. die Firewall testweise

## Datenschutz & Sicherheit

- ⚠️ Passwörter werden mit SHA-256 gehasht (für Produktiv: bcrypt verwenden)
- ⚠️ Für Internet-Zugriff: HTTPS ist Pflicht!
- ⚠️ Regelmäßige Backups der Datenbank durchführen
- ✅ Session-basierte Authentifizierung
- ✅ Geschützte Routen (nur für angemeldete Benutzer)

## Tipps für Benutzer

1. **Lesezeichen setzen**: Speichern Sie die Web-Adresse als Lesezeichen auf dem Handy
2. **Home-Screen**: Fügen Sie die Web-App zum Home-Screen hinzu (funktioniert wie eine App)
3. **Offline**: Die App benötigt Internet/Netzwerk-Verbindung
4. **Datum**: Wird automatisch auf heute gesetzt
5. **Stundenzähler**: Wird automatisch von der Maschine übernommen

## Support

Bei Problemen wenden Sie sich an den Administrator Ihrer Gemeinschaft.

---

**Version**: 1.0  
**Erstellt**: Januar 2026
