# -*- coding: utf-8 -*-
"""
Skript zum Aktualisieren der url_for-Aufrufe in Templates
für die neue Blueprint-Struktur
"""

import os
import re
import glob

# Mapping von alten zu neuen Route-Namen
ROUTE_MAPPING = {
    # Auth
    'login': 'auth.login',
    'logout': 'auth.logout',
    'datenbank_auswahl': 'auth.datenbank_auswahl',
    'datenbank_wechseln': 'auth.datenbank_wechseln',
    'passwort_aendern': 'auth.passwort_aendern',

    # Dashboard
    'dashboard': 'dashboard.dashboard',
    'index': 'dashboard.index',

    # Einsätze
    'neuer_einsatz': 'einsaetze.neuer_einsatz',
    'meine_einsaetze': 'einsaetze.meine_einsaetze',
    'einsatz_stornieren': 'einsaetze.einsatz_stornieren',
    'meine_stornierten_einsaetze': 'einsaetze.meine_stornierten_einsaetze',
    'meine_einsaetze_csv': 'einsaetze.meine_einsaetze_csv',

    # Reservierungen
    'maschine_reservieren': 'reservierungen.maschine_reservieren',
    'reservierungen_kalender': 'reservierungen.reservierungen_kalender',
    'reservierungen_balken': 'reservierungen.reservierungen_balken',
    'meine_reservierungen': 'reservierungen.meine_reservierungen',
    'reservierung_stornieren': 'reservierungen.reservierung_stornieren',
    'geloeschte_reservierungen': 'reservierungen.geloeschte_reservierungen',
    'abgelaufene_reservierungen': 'reservierungen.abgelaufene_reservierungen',

    # Nachrichten
    'nachrichten': 'nachrichten.nachrichten',
    'nachricht_lesen': 'nachrichten.nachricht_lesen',
    'nachricht_neu': 'nachrichten.nachricht_neu',

    # Abrechnungen
    'meine_abrechnungen': 'abrechnungen.meine_abrechnungen',
    'abrechnung_pdf': 'abrechnungen.abrechnung_pdf',
    'mein_konto': 'abrechnungen.mein_konto',

    # API
    'get_stundenzaehler': 'api.get_stundenzaehler',
    'api_maschine_details': 'api.api_maschine_details',

    # Admin Benutzer
    'admin_benutzer': 'admin_benutzer.admin_benutzer',
    'admin_benutzer_neu': 'admin_benutzer.admin_benutzer_neu',
    'admin_benutzer_edit': 'admin_benutzer.admin_benutzer_edit',
    'admin_benutzer_delete': 'admin_benutzer.admin_benutzer_delete',
    'admin_benutzer_activate': 'admin_benutzer.admin_benutzer_activate',

    # Admin Maschinen
    'admin_maschinen': 'admin_maschinen.admin_maschinen',
    'admin_maschinen_neu': 'admin_maschinen.admin_maschinen_neu',
    'admin_maschinen_edit': 'admin_maschinen.admin_maschinen_edit',
    'admin_maschinen_delete': 'admin_maschinen.admin_maschinen_delete',
    'admin_maschinen_rentabilitaet': 'admin_maschinen.admin_maschinen_rentabilitaet',
    'admin_maschinen_rentabilitaet_pdf': 'admin_maschinen.admin_maschinen_rentabilitaet_pdf',
    'admin_maschinen_aufwendungen': 'admin_maschinen.admin_maschinen_aufwendungen',
    'admin_maschinen_aufwendungen_bearbeiten': 'admin_maschinen.admin_maschinen_aufwendungen_bearbeiten',

    # Admin Einsatzzwecke
    'admin_einsatzzwecke': 'admin_einsatzzwecke.admin_einsatzzwecke',
    'admin_einsatzzwecke_neu': 'admin_einsatzzwecke.admin_einsatzzwecke_neu',
    'admin_einsatzzwecke_edit': 'admin_einsatzzwecke.admin_einsatzzwecke_edit',
    'admin_einsatzzwecke_delete': 'admin_einsatzzwecke.admin_einsatzzwecke_delete',
    'admin_einsatzzwecke_activate': 'admin_einsatzzwecke.admin_einsatzzwecke_activate',

    # Admin Gemeinschaften
    'admin_gemeinschaften': 'admin_gemeinschaften.admin_gemeinschaften',
    'admin_gemeinschaften_neu': 'admin_gemeinschaften.admin_gemeinschaften_neu',
    'admin_gemeinschaften_edit': 'admin_gemeinschaften.admin_gemeinschaften_edit',
    'admin_gemeinschaften_mitglieder': 'admin_gemeinschaften.admin_gemeinschaften_mitglieder',
    'admin_gemeinschaften_abrechnung': 'admin_gemeinschaften.admin_gemeinschaften_abrechnung',
    'admin_gemeinschaften_abrechnung_csv': 'admin_gemeinschaften.admin_gemeinschaften_abrechnung_csv',
    'admin_gemeinschaften_maschinenuebersicht_pdf': 'admin_gemeinschaften.admin_gemeinschaften_maschinenuebersicht_pdf',

    # Admin Finanzen
    'admin_konten': 'admin_finanzen.admin_konten',
    'admin_konten_buchung_neu': 'admin_finanzen.admin_konten_buchung_neu',
    'admin_konten_detail': 'admin_finanzen.admin_konten_detail',
    'admin_konten_zahlung': 'admin_finanzen.admin_konten_zahlung',
    'admin_abrechnungen': 'admin_finanzen.admin_abrechnungen',
    'abrechnungen_erstellen': 'admin_finanzen.abrechnungen_erstellen',
    'abrechnungen_liste': 'admin_finanzen.abrechnungen_liste',
    'admin_csv_import': 'admin_finanzen.admin_csv_import',
    'admin_csv_konfiguration': 'admin_finanzen.admin_csv_konfiguration',
    'admin_transaktionen': 'admin_finanzen.admin_transaktionen',
    'transaktion_zuordnen': 'admin_finanzen.transaktion_zuordnen',
    'transaktion_zuordnung_aufheben': 'admin_finanzen.transaktion_zuordnung_aufheben',
    'transaktion_loeschen': 'admin_finanzen.transaktion_loeschen',
    'import_loeschen': 'admin_finanzen.import_loeschen',
    'anfangssaldo_bearbeiten': 'admin_finanzen.anfangssaldo_bearbeiten',

    # Admin System
    'admin_dashboard': 'admin_system.admin_dashboard',
    'admin_alle_einsaetze': 'admin_system.admin_alle_einsaetze',
    'admin_stornierte_einsaetze': 'admin_system.admin_stornierte_einsaetze',
    'admin_backup_bestaetigen': 'admin_system.admin_backup_bestaetigen',
    'admin_rollen': 'admin_system.admin_rollen',
    'admin_rollen_set_level': 'admin_system.admin_rollen_set_level',
    'admin_rollen_add_gemeinschaft': 'admin_system.admin_rollen_add_gemeinschaft',
    'admin_rollen_remove_gemeinschaft': 'admin_system.admin_rollen_remove_gemeinschaft',
    'admin_export_json': 'admin_system.admin_export_json',
    'admin_export_csv': 'admin_system.admin_export_csv',
    'admin_export_alle_einsaetze_csv': 'admin_system.admin_export_alle_einsaetze_csv',
    'admin_backup_database': 'admin_system.admin_backup_database',
    'admin_database_backup': 'admin_system.admin_database_backup',
    'admin_database_restore': 'admin_system.admin_database_restore',
    'admin_einsaetze_loeschen': 'admin_system.admin_einsaetze_loeschen',
    'admin_training_rechte': 'admin_system.admin_training_rechte',
    'admin_training_rechte_update': 'admin_system.admin_training_rechte_update',
    'admin_training_datenbanken': 'admin_system.admin_training_datenbanken',
    'admin_training_db_erstellen': 'admin_system.admin_training_db_erstellen',
}

def update_file(filepath):
    """Aktualisiert url_for-Aufrufe in einer Datei"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes = 0

    # Ersetze url_for('route_name' durch url_for('blueprint.route_name'
    for old_name, new_name in ROUTE_MAPPING.items():
        # Pattern für url_for('name') und url_for("name")
        patterns = [
            (rf"url_for\('{old_name}'", f"url_for('{new_name}'"),
            (rf'url_for\("{old_name}"', f'url_for("{new_name}"'),
            (rf"url_for\('{old_name}',", f"url_for('{new_name}',"),
            (rf'url_for\("{old_name}",', f'url_for("{new_name}",'),
        ]

        for pattern, replacement in patterns:
            new_content, n = re.subn(pattern, replacement, content)
            if n > 0:
                content = new_content
                changes += n

    if changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  {filepath}: {changes} Änderungen")
        return changes
    return 0

def main():
    """Hauptfunktion"""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')

    print("Aktualisiere Templates...")
    print(f"Templates-Verzeichnis: {templates_dir}")
    print()

    total_changes = 0
    files_changed = 0

    for filepath in glob.glob(os.path.join(templates_dir, '**/*.html'), recursive=True):
        changes = update_file(filepath)
        if changes > 0:
            total_changes += changes
            files_changed += 1

    print()
    print(f"Fertig! {total_changes} Änderungen in {files_changed} Dateien.")

if __name__ == '__main__':
    main()
