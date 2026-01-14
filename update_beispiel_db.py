import sqlite3
import os

db_path = 'distribution/beispiel_datenbanken/maschinengemeinschaft_uebung.db'

if not os.path.exists(db_path):
    print(f"Datei nicht gefunden: {db_path}")
    exit(1)

print(f"Aktualisiere {db_path}...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Prüfe ob admin_level schon existiert
cursor.execute("PRAGMA table_info(benutzer)")
columns = [col[1] for col in cursor.fetchall()]

if 'admin_level' in columns:
    print("✓ admin_level Spalte existiert bereits")
else:
    print("Füge admin_level Spalte hinzu...")
    cursor.execute("ALTER TABLE benutzer ADD COLUMN admin_level INTEGER DEFAULT 0")
    print("✓ admin_level Spalte hinzugefügt")

# Aktualisiere admin-user auf admin_level=2
cursor.execute("UPDATE benutzer SET admin_level=2 WHERE username='admin' AND is_admin=1")
affected = cursor.rowcount
print(f"✓ {affected} Admin-Benutzer aktualisiert")

conn.commit()
conn.close()

print("\n✓ Beispiel-Datenbank erfolgreich aktualisiert!")
