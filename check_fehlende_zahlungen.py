import sqlite3

conn = sqlite3.connect('maschinengemeinschaft.db')
c = conn.cursor()

# Alle Transaktionen
c.execute('SELECT COUNT(*) FROM bank_transaktionen')
total = c.fetchone()[0]
print(f'Total bank_transaktionen: {total}')

# Mit benutzer_id
c.execute('SELECT COUNT(*) FROM bank_transaktionen WHERE benutzer_id IS NOT NULL')
mit_user = c.fetchone()[0]
print(f'Mit benutzer_id: {mit_user}')

# Bereits importierte Buchungen
c.execute('SELECT COUNT(*) FROM buchungen WHERE typ = "einzahlung"')
einzahlungen = c.fetchone()[0]
print(f'Einzahlungs-Buchungen: {einzahlungen}')

# Noch zu importierende
c.execute('''
    SELECT bt.id, bt.buchungsdatum, bt.verwendungszweck, bt.betrag, bt.benutzer_id, b.name
    FROM bank_transaktionen bt
    JOIN benutzer b ON bt.benutzer_id = b.id
    WHERE bt.benutzer_id IS NOT NULL 
    AND NOT EXISTS (
        SELECT 1 FROM buchungen bu 
        WHERE bu.referenz_typ = 'bank_transaktion' 
        AND bu.referenz_id = bt.id
    )
    ORDER BY bt.buchungsdatum
''')

print(f'\nNoch zu importierende Transaktionen:')
fehlende = c.fetchall()
if fehlende:
    for row in fehlende:
        print(f'  ID {row[0]}: {row[1]} - {row[5]} - {row[3]:.2f}€')
        print(f'     Zweck: {row[2][:80]}')
else:
    print('  Keine fehlenden Transaktionen!')

conn.close()
