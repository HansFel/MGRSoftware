import sqlite3
import sys

# Prüfe eine mit der EXE erstellte Datenbank
db_file = input("Pfad zur Datenbank-Datei (die Sie gerade mit der EXE erstellt haben): ").strip('"')

try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Prüfe Schema der benutzer-Tabelle
    cursor.execute("PRAGMA table_info(benutzer)")
    columns = cursor.fetchall()
    
    print("\n=== SPALTEN DER BENUTZER-TABELLE ===")
    has_admin_level = False
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
        if col[1] == 'admin_level':
            has_admin_level = True
    
    if not has_admin_level:
        print("\n❌ FEHLER: Spalte 'admin_level' fehlt!")
        print("   Diese Datenbank wurde mit einer alten Version erstellt.")
        print("   Bitte löschen Sie die Datei und erstellen Sie eine neue Datenbank.")
    else:
        print("\n✓ Spalte 'admin_level' vorhanden")
    
    # Prüfe Admin-User
    print("\n=== ADMIN-USER IN DATENBANK ===")
    cursor.execute("SELECT id, username, password_hash, is_admin, admin_level, aktiv FROM benutzer WHERE username='admin'")
    row = cursor.fetchone()
    
    if row:
        print(f"  ID: {row[0]}")
        print(f"  Username: {row[1]}")
        print(f"  Password-Hash: {row[2]}")
        print(f"  Is_Admin: {row[3]}")
        print(f"  Admin_Level: {row[4]}")
        print(f"  Aktiv: {row[5]}")
        
        # Teste mit erwartetem Hash
        import hashlib
        expected_hash = hashlib.sha256("admin123".encode('utf-8')).hexdigest()
        print(f"\n=== HASH-VERGLEICH ===")
        print(f"  In DB: {row[2]}")
        print(f"  Erwartet: {expected_hash}")
        
        if row[2] == expected_hash:
            print("  ✓ Hashes stimmen überein!")
        else:
            print("  ❌ Hashes unterschiedlich!")
            
        if row[5] != 1:
            print("\n  ❌ FEHLER: Benutzer ist nicht aktiv!")
    else:
        print("  ❌ KEIN Admin-User gefunden!")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ FEHLER: {e}")
    
print("\n" + "="*50)
input("Drücken Sie Enter zum Beenden...")
