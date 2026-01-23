# Hochverfügbarkeit der Maschinengemeinschaft-Anwendung

## Was ist Hochverfügbarkeit?

Hochverfügbarkeit (High Availability, HA) bedeutet, dass eine Anwendung auch bei Ausfällen von Hardware oder Software weiterhin erreichbar bleibt. Das Ziel ist eine **Verfügbarkeit von 99,9% oder höher**.

| Verfügbarkeit | Ausfallzeit pro Jahr |
|---------------|----------------------|
| 99%           | 3,65 Tage            |
| 99,9%         | 8,76 Stunden         |
| 99,99%        | 52,6 Minuten         |

---

## Warum ist das wichtig?

- Mitglieder können jederzeit Maschineneinsätze erfassen
- Reservierungen sind rund um die Uhr möglich
- Keine Datenverluste bei Serverausfall
- Professioneller Eindruck der Gemeinschaft

---

## Herausforderung: SQLite-Datenbank

Unsere Anwendung verwendet **SQLite** als Datenbank. SQLite ist:

**Vorteile:**
- Einfach (eine Datei)
- Keine separate Installation
- Schnell für kleine bis mittlere Datenmengen

**Nachteile für Hochverfügbarkeit:**
- Datei-basiert (nicht für Netzwerk-Zugriff gedacht)
- Keine eingebaute Replikation
- Locking-Probleme bei gleichzeitigem Schreibzugriff von mehreren Servern

---

## Optionen für Hochverfügbarkeit

### Option 1: Active-Passive (Failover)

```
┌─────────────────┐         ┌─────────────────┐
│   Server 1      │         │   Server 2      │
│   (AKTIV)       │         │   (STANDBY)     │
│                 │         │                 │
│  ┌───────────┐  │  Kopie  │  ┌───────────┐  │
│  │  SQLite   │──┼────────►│  │  SQLite   │  │
│  │    DB     │  │         │  │  (Backup) │  │
│  └───────────┘  │         │  └───────────┘  │
└─────────────────┘         └─────────────────┘
        │                           │
        ▼                           │
   Benutzer                    Bei Ausfall
   greifen zu                  umschalten
```

**Funktionsweise:**
1. Server 1 ist aktiv und bedient alle Anfragen
2. Datenbank wird regelmäßig auf Server 2 kopiert
3. Bei Ausfall von Server 1 wird auf Server 2 umgeschaltet

**Vorteile:**
- Einfach einzurichten
- Keine Code-Änderungen nötig
- Günstig (nur 2 Server)

**Nachteile:**
- Manuelles oder automatisches Umschalten nötig
- Kurze Ausfallzeit beim Umschalten
- Möglicher Datenverlust seit letztem Backup

**Kosten:** ca. 10-20 EUR/Monat für zweiten Server

---

### Option 2: Litestream (Echtzeit-Replikation)

```
┌─────────────────┐                    ┌─────────────────┐
│   Server 1      │                    │   Server 2      │
│   (AKTIV)       │                    │   (STANDBY)     │
│                 │                    │                 │
│  ┌───────────┐  │                    │  ┌───────────┐  │
│  │  SQLite   │  │                    │  │  SQLite   │  │
│  └─────┬─────┘  │                    │  └─────▲─────┘  │
│        │        │                    │        │        │
│  ┌─────▼─────┐  │    Echtzeit-       │  ┌─────┴─────┐  │
│  │Litestream │──┼───Replikation─────►│  │Litestream │  │
│  └───────────┘  │    (Sekunden)      │  └───────────┘  │
└─────────────────┘                    └─────────────────┘
```

**Was ist Litestream?**
- Open-Source Tool für SQLite-Replikation
- Streamt Änderungen in Echtzeit
- Kann auf S3, SFTP oder anderen Server replizieren

**Funktionsweise:**
1. Litestream überwacht die SQLite-Datenbank
2. Jede Änderung wird sofort repliziert
3. Server 2 kann innerhalb von Sekunden übernehmen

**Vorteile:**
- Nahezu Echtzeit-Backup (Sekunden)
- Minimaler Datenverlust
- SQLite bleibt erhalten
- Einfache Installation

**Nachteile:**
- Zusätzliche Software nötig
- Umschalten noch manuell oder per Script

**Kosten:** Kostenlos (Open Source) + zweiter Server

**Installation:**
```bash
# Auf Server 1 (Quelle)
apt install litestream
litestream replicate /pfad/zur/db.sqlite s3://bucket/db

# Auf Server 2 (Ziel)
litestream restore -o /pfad/zur/db.sqlite s3://bucket/db
```

---

### Option 3: Datenbank-Wechsel zu PostgreSQL/MySQL

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Server 1   │     │  Server 2   │     │  Datenbank  │
│  (Flask)    │────►│  (Flask)    │────►│  Cluster    │
└─────────────┘     └─────────────┘     │             │
                                        │ PostgreSQL  │
        ▲               ▲               │  Primary    │
        │               │               │      │      │
        └───────┬───────┘               │      ▼      │
                │                       │  Replica    │
         Load Balancer                  └─────────────┘
```

**Funktionsweise:**
1. SQLite wird durch PostgreSQL oder MySQL ersetzt
2. Datenbank läuft auf eigenem Server mit Replikation
3. Mehrere App-Server können gleichzeitig zugreifen

**Vorteile:**
- Professionelle Lösung
- Native Replikation
- Mehrere App-Server möglich
- Bessere Performance bei vielen Benutzern

**Nachteile:**
- Code-Änderungen nötig (SQLite → PostgreSQL)
- Komplexere Infrastruktur
- Höhere Kosten
- Mehr Wartungsaufwand

**Kosten:** ca. 30-50 EUR/Monat (managed Database)

**Code-Änderungen:**
```python
# Vorher (SQLite)
DATABASE = 'data/maschinengemeinschaft.db'

# Nachher (PostgreSQL)
DATABASE_URL = 'postgresql://user:pass@dbserver:5432/maschinengemeinschaft'
```

---

### Option 4: Load Balancer + Shared Storage

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │  (HAProxy/Nginx)│
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌──────────┐   ┌──────────┐   ┌──────────┐
       │ Server 1 │   │ Server 2 │   │ Server 3 │
       │ (Flask)  │   │ (Flask)  │   │ (Flask)  │
       └────┬─────┘   └────┬─────┘   └────┬─────┘
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                    ┌─────────────┐
                    │    NAS      │
                    │  (Shared    │
                    │  Storage)   │
                    │             │
                    │  SQLite DB  │
                    └─────────────┘
```

**Funktionsweise:**
1. Mehrere Server teilen sich eine Datenbank auf NAS
2. Load Balancer verteilt Anfragen
3. Fällt ein Server aus, übernehmen die anderen

**Vorteile:**
- Lastverteilung
- Kein Umschalten nötig
- Skalierbar

**Nachteile:**
- SQLite nicht für gleichzeitigen Schreibzugriff geeignet!
- NAS wird zum Single Point of Failure
- Locking-Probleme möglich

**Empfehlung:** Nur mit Datenbank-Wechsel zu PostgreSQL sinnvoll!

---

### Option 5: Cloud-Hosting

```
┌──────────────────────────────────────────────┐
│                   Cloud                       │
│  (Azure / AWS / Google Cloud)                │
│                                              │
│   ┌────────────┐      ┌────────────┐         │
│   │  Region 1  │      │  Region 2  │         │
│   │  Server    │◄────►│  Server    │         │
│   │  + DB      │      │  (Standby) │         │
│   └────────────┘      └────────────┘         │
│                                              │
│   Automatisches Failover durch Cloud-Anbieter│
└──────────────────────────────────────────────┘
```

**Anbieter:**
- **Microsoft Azure:** App Service + Azure SQL
- **Amazon AWS:** Elastic Beanstalk + RDS
- **Google Cloud:** App Engine + Cloud SQL

**Vorteile:**
- Vollständig verwaltet
- Automatisches Failover
- Globale Verfügbarkeit
- Automatische Backups

**Nachteile:**
- Höhere Kosten
- Abhängigkeit vom Anbieter
- Datenbank-Wechsel nötig (kein SQLite)
- Datenschutz (DSGVO) beachten!

**Kosten:** ca. 50-100 EUR/Monat

---

## Vergleich der Optionen

| Kriterium | Active-Passive | Litestream | PostgreSQL | Cloud |
|-----------|----------------|------------|------------|-------|
| **Komplexität** | Niedrig | Niedrig | Mittel | Niedrig |
| **Kosten/Monat** | 10-20 EUR | 10-20 EUR | 30-50 EUR | 50-100 EUR |
| **Code-Änderungen** | Keine | Keine | Ja | Ja |
| **Datenverlust-Risiko** | Minuten | Sekunden | Minimal | Minimal |
| **Umschaltzeit** | Minuten | Minuten | Sekunden | Automatisch |
| **Wartungsaufwand** | Niedrig | Niedrig | Mittel | Minimal |

---

## Empfehlung für die Maschinengemeinschaft

### Kurzfristig: Litestream (Option 2)

**Warum?**
- Kein Code-Umbau nötig
- SQLite bleibt erhalten
- Schnell einzurichten
- Geringe Kosten
- Nahezu Echtzeit-Backup

**Umsetzung:**
1. Zweiten Server mieten (z.B. Hetzner VPS für 5 EUR/Monat)
2. Litestream auf beiden Servern installieren
3. Replikation einrichten
4. Monitoring einrichten (z.B. UptimeRobot)
5. Umschalt-Script erstellen

### Langfristig: PostgreSQL (Option 3)

**Warum?**
- Professionelle Lösung
- Bessere Skalierbarkeit
- Native Replikation
- Mehrere Server gleichzeitig möglich

---

## PostgreSQL-Migration im Detail

### Ist der Umbau möglich?

**Ja, mit mittlerem Aufwand.** Die Analyse unseres Codes zeigt folgende Situation:

#### Aktuelle Architektur

```
web_app.py (Flask)
    │
    ▼
database.py (MaschinenDBContext)
    │
    ▼
maschinengemeinschaft.db (SQLite)
    ├── 25 Tabellen
    ├── 2 Views
    ├── Triggers (Auto-Datum)
    └── Generierte Spalten
```

#### SQLite-spezifische Features im Code

| Feature | SQLite | PostgreSQL | Anpassung |
|---------|--------|------------|-----------|
| `INSERT OR IGNORE` | ✓ | `ON CONFLICT DO NOTHING` | Suchen/Ersetzen |
| `datetime('+24 hours')` | ✓ | `+ INTERVAL '24 hours'` | Suchen/Ersetzen |
| `GENERATED ALWAYS AS` | ✓ | ✓ (gleiche Syntax) | Keine |
| Parameterisierung `?` | ✓ | `%s` | Suchen/Ersetzen |
| `sqlite3.Row` | ✓ | `psycopg2.DictCursor` | Kleine Anpassung |
| Trigger-Syntax | `BEGIN...END` | PL/pgSQL Funktion | Umschreiben |

#### Beispiel: SQL-Änderungen

```sql
-- VORHER (SQLite)
INSERT OR IGNORE INTO gemeinschafts_admin
(benutzer_id, gemeinschaft_id) VALUES (?, ?)

-- NACHHER (PostgreSQL)
INSERT INTO gemeinschafts_admin
(benutzer_id, gemeinschaft_id) VALUES (%s, %s)
ON CONFLICT DO NOTHING
```

```sql
-- VORHER (SQLite)
WHERE datetime(zeitpunkt, '+24 hours') > datetime('now')

-- NACHHER (PostgreSQL)
WHERE zeitpunkt + INTERVAL '24 hours' > NOW()
```

#### Beispiel: Python-Änderungen

```python
# VORHER (SQLite)
import sqlite3
self.connection = sqlite3.connect(self.db_path)
self.connection.row_factory = sqlite3.Row

# NACHHER (PostgreSQL)
import psycopg2
from psycopg2.extras import DictCursor
self.connection = psycopg2.connect(
    host="localhost",
    database="maschinengemeinschaft",
    user="mgr_user",
    password="geheim"
)
self.cursor = self.connection.cursor(cursor_factory=DictCursor)
```

---

### Auswirkung auf das Backup-System

#### Aktuelles Backup-System (SQLite)

```
┌────────────────────────────────────────────────────────────┐
│                   AKTUELLES BACKUP-SYSTEM                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  1. SCHWELLWERT-PRÜFUNG                                    │
│     └── Zählt Einsätze seit letztem Backup                 │
│     └── Warnt bei Schwellwert (Standard: 50)               │
│                                                            │
│  2. ZWEI-ADMIN-BESTÄTIGUNG                                 │
│     └── Admin 1 initiiert Backup-Bestätigung               │
│     └── 24 Stunden Zeitfenster                             │
│     └── Admin 2 muss bestätigen                            │
│                                                            │
│  3. DATEI-BASIERTES BACKUP                                 │
│     └── shutil.copy2(db.sqlite, backup.sqlite)             │
│     └── Download als .db Datei                             │
│                                                            │
│  4. WIEDERHERSTELLUNG                                      │
│     └── Upload der .db Datei                               │
│     └── Validierung (SQLite-Format prüfen)                 │
│     └── Datei ersetzen                                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### Neues Backup-System (PostgreSQL)

```
┌────────────────────────────────────────────────────────────┐
│                    NEUES BACKUP-SYSTEM                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  1. SCHWELLWERT-PRÜFUNG (bleibt gleich)                    │
│     └── Zählt Einsätze seit letztem Backup                 │
│     └── Warnt bei Schwellwert                              │
│                                                            │
│  2. ZWEI-ADMIN-BESTÄTIGUNG (bleibt gleich)                 │
│     └── Admin 1 initiiert                                  │
│     └── Admin 2 bestätigt                                  │
│                                                            │
│  3. DATENBANK-DUMP                                         │
│     └── pg_dump -Fc database > backup.dump                 │
│     └── Download als .dump oder .sql Datei                 │
│                                                            │
│  4. WIEDERHERSTELLUNG                                      │
│     └── Upload der .dump Datei                             │
│     └── pg_restore -d database backup.dump                 │
│                                                            │
│  NEU: AUTOMATISCHE FEATURES                                │
│     └── Point-in-Time Recovery (PITR)                      │
│     └── Continuous Archiving (WAL)                         │
│     └── Streaming Replication                              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### Vergleich der Backup-Methoden

| Aspekt | SQLite (aktuell) | PostgreSQL (neu) |
|--------|------------------|------------------|
| **Backup erstellen** | `shutil.copy2()` | `pg_dump -Fc` |
| **Backup-Größe** | 1:1 Kopie | Komprimiert (~30% kleiner) |
| **Während Backup** | Kurze Sperre möglich | Keine Unterbrechung |
| **Wiederherstellung** | Datei ersetzen | `pg_restore` |
| **Zeitpunkt wählbar** | Nein (nur Snapshots) | Ja (PITR auf Sekunde genau) |
| **Automatisch** | Cron-Job nötig | WAL-Archivierung eingebaut |
| **Replikation** | Extern (Litestream) | Eingebaut (Streaming) |

#### Neue Backup-Befehle

```bash
# Vollständiges Backup erstellen
pg_dump -Fc -h localhost -U mgr_user maschinengemeinschaft > backup.dump

# Backup wiederherstellen
pg_restore -h localhost -U mgr_user -d maschinengemeinschaft backup.dump

# Nur Daten exportieren (ohne Schema)
pg_dump -a -h localhost -U mgr_user maschinengemeinschaft > data_only.sql

# Automatisches tägliches Backup (Cron)
0 2 * * * pg_dump -Fc maschinengemeinschaft > /backup/mgr_$(date +\%Y\%m\%d).dump
```

#### Code-Änderungen im Backup-System

```python
# VORHER (SQLite) - web_app.py
def backup_download():
    temp_backup_path = os.path.join(tempfile.gettempdir(), 'backup.db')
    shutil.copy2(DB_PATH, temp_backup_path)
    return send_file(temp_backup_path, as_attachment=True)

# NACHHER (PostgreSQL)
import subprocess

def backup_download():
    temp_backup_path = os.path.join(tempfile.gettempdir(), 'backup.dump')
    subprocess.run([
        'pg_dump', '-Fc',
        '-h', DB_HOST,
        '-U', DB_USER,
        '-d', DB_NAME,
        '-f', temp_backup_path
    ], env={'PGPASSWORD': DB_PASSWORD})
    return send_file(temp_backup_path, as_attachment=True)
```

---

### Vorteile von PostgreSQL für Datensicherung

#### 1. Point-in-Time Recovery (PITR)

```
Timeline:  ──────────────────────────────────────────►
                │           │           │
             Backup      Fehler    Wiederherstellung
             10:00       14:30      auf 14:29:59
                │           │           │
                └───────────┴───────────┘
                    WAL-Archiv ermöglicht
                    Wiederherstellung auf
                    jeden beliebigen Zeitpunkt
```

**Vorteil:** Bei versehentlichem Löschen kann auf den Zeitpunkt VOR dem Löschen zurückgesetzt werden.

#### 2. Streaming Replication

```
┌─────────────┐         ┌─────────────┐
│  Primary    │ ──WAL──►│  Standby    │
│  Server     │  Stream │  Server     │
│             │         │             │
│  Schreiben  │         │  Nur Lesen  │
│  + Lesen    │         │  (Hot       │
│             │         │   Standby)  │
└─────────────┘         └─────────────┘
       │                       │
       │    Bei Ausfall:       │
       └───────────────────────┘
           Automatisches Failover
```

**Vorteil:** Echtzeit-Kopie ohne externe Tools wie Litestream.

#### 3. Logische Replikation

```
┌─────────────┐         ┌─────────────┐
│  Server A   │         │  Server B   │
│             │         │             │
│  Tabelle X  │────────►│  Tabelle X  │
│  Tabelle Y  │    ✗    │             │
│  Tabelle Z  │────────►│  Tabelle Z  │
└─────────────┘         └─────────────┘
```

**Vorteil:** Nur bestimmte Tabellen replizieren (z.B. ohne sensible Daten).

---

### Geschätzter Migrationsaufwand

| Aufgabe | Geschätzter Aufwand |
|---------|---------------------|
| `database.py` anpassen (Verbindung) | 2-4 Stunden |
| SQL-Syntax ändern (~20 Stellen) | 4-6 Stunden |
| Triggers in PL/pgSQL umschreiben | 2 Stunden |
| Backup-System umbauen | 4-6 Stunden |
| Daten von SQLite → PostgreSQL migrieren | 1-2 Stunden |
| Testen aller Funktionen | 4-8 Stunden |
| **Gesamt** | **~20-30 Stunden** |

### Migrations-Script (Daten übertragen)

```bash
# 1. SQLite zu SQL exportieren
sqlite3 maschinengemeinschaft.db .dump > sqlite_dump.sql

# 2. SQL-Syntax anpassen (automatisch)
sed -i 's/INTEGER PRIMARY KEY AUTOINCREMENT/SERIAL PRIMARY KEY/g' sqlite_dump.sql
sed -i 's/DATETIME/TIMESTAMP/g' sqlite_dump.sql

# 3. In PostgreSQL importieren
psql -h localhost -U mgr_user -d maschinengemeinschaft < sqlite_dump.sql
```

Oder mit Python-Tool **pgloader**:

```bash
pgloader sqlite:///maschinengemeinschaft.db \
         postgresql://user:pass@localhost/maschinengemeinschaft
```

---

## Zusätzliche Maßnahmen

### 1. Regelmäßige Backups

```bash
# Tägliches Backup per Cron
0 2 * * * cp /pfad/db.sqlite /backup/db_$(date +\%Y\%m\%d).sqlite
```

### 2. Monitoring

- **UptimeRobot** (kostenlos): Prüft ob Server erreichbar
- **Healthcheck-Endpoint:** `/health` Route in der App

```python
@app.route('/health')
def health_check():
    return {'status': 'ok', 'database': 'connected'}
```

### 3. Automatische Benachrichtigung

- E-Mail bei Serverausfall
- SMS für kritische Ausfälle

---

## Zusammenfassung

1. **Hochverfügbarkeit** schützt vor Ausfällen
2. **SQLite** hat Einschränkungen, aber Lösungen existieren
3. **Litestream** ist die beste kurzfristige Lösung
4. **PostgreSQL** für langfristige Skalierbarkeit
5. **Monitoring** ist genauso wichtig wie Redundanz

---

## Fragen?

**Kontakt:** [Administrator der Gemeinschaft]

---

*Dokument erstellt: Januar 2026*
*Version: 1.0*
