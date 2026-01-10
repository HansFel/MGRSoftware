import sqlite3

conn = sqlite3.connect('maschinengemeinschaft.db')
cursor = conn.cursor()

# Prüfe ob is_admin Spalte existiert
cursor.execute('PRAGMA table_info(benutzer)')
columns = [col[1] for col in cursor.fetchall()]
print(f"is_admin Spalte vorhanden: {'is_admin' in columns}")

# Zeige alle Benutzer
cursor.execute('SELECT id, name, vorname, username, is_admin FROM benutzer')
users = cursor.fetchall()

print(f"\nAnzahl Benutzer: {len(users)}\n")
print("Alle Benutzer:")
for u in users:
    admin_text = "👑 ADMIN" if u[4] else "Benutzer"
    username = u[3] or "(kein Username)"
    print(f"  ID {u[0]}: {u[1]} {u[2]}, Username: {username}, Rolle: {admin_text}")

# Zeige Admins
admins = [u for u in users if u[4]]
if admins:
    print(f"\n✅ Administratoren ({len(admins)}):")
    for a in admins:
        print(f"   Username: {a[3]}")
else:
    print("\n⚠️  Kein Administrator vorhanden!")
    print("   Erstellen Sie einen Admin über die Desktop-App (main.py)")

conn.close()
