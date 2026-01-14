import sqlite3

# Öffne die test_maschinengemeinschaft.db
conn = sqlite3.connect('test_maschinengemeinschaft.db')
cursor = conn.cursor()

# Prüfe ob Admin existiert
cursor.execute("SELECT id, name, username, password_hash, is_admin, admin_level, aktiv FROM benutzer WHERE username='admin'")
admin = cursor.fetchone()

if admin:
    print("✓ Admin-Benutzer gefunden:")
    print(f"  ID: {admin[0]}")
    print(f"  Name: {admin[1]}")
    print(f"  Username: {admin[2]}")
    print(f"  Password Hash: {admin[3]}")
    print(f"  Is Admin: {admin[4]}")
    print(f"  Admin Level: {admin[5]}")
    print(f"  Aktiv: {admin[6]}")
    print()
    
    # Test Password
    import hashlib
    test_password = "admin123"
    test_hash = hashlib.sha256(test_password.encode('utf-8')).hexdigest()
    print(f"Erwarteter Hash: {test_hash}")
    print(f"Hash stimmt überein: {test_hash == admin[3]}")
else:
    print("✗ Kein Admin-Benutzer gefunden!")

# Prüfe ob Tabelle gemeinschafts_admin existiert
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gemeinschafts_admin'")
if cursor.fetchone():
    print("\n✓ Tabelle 'gemeinschafts_admin' existiert")
else:
    print("\n✗ Tabelle 'gemeinschafts_admin' fehlt!")

conn.close()