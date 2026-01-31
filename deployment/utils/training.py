# -*- coding: utf-8 -*-
"""
Training-Datenbank Funktionen
"""

import os
from flask import session

# Datenbank-Pfade
# Basis-Pfad ermitteln (relativ zum deployment-Verzeichnis oder Hauptverzeichnis)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH_PRODUCTION = os.environ.get('DB_PATH', os.path.join(_BASE_DIR, 'data', 'maschinengemeinschaft.db'))
TRAINING_DB_DIR = os.path.join(_BASE_DIR, 'data', 'training')

# Trainings-Datenbanken Konfiguration
TRAINING_DATABASES = {
    'uebung_leer': {
        'name': 'Leere Übungsdatenbank',
        'description': 'Zum freien Üben - nur Admin-Benutzer vorhanden',
        'file': 'uebung_leer.db',
        'level': 'anfaenger'
    },
    'uebung_anfaenger': {
        'name': 'Anfänger-Training',
        'description': 'Einfache Daten: 5 Benutzer, 3 Maschinen, ca. 25 Einsätze',
        'file': 'uebung_anfaenger.db',
        'level': 'anfaenger'
    },
    'uebung_fortgeschritten': {
        'name': 'Fortgeschrittenen-Training',
        'description': 'Mehr Daten: 15 Benutzer, 8 Maschinen, 2 Gemeinschaften, 250+ Einsätze',
        'file': 'uebung_fortgeschritten.db',
        'level': 'fortgeschritten'
    },
    'uebung_admin': {
        'name': 'Admin-Training',
        'description': 'Komplexe Daten: 25 Benutzer, 15 Maschinen, 3 Gemeinschaften, 700+ Einsätze',
        'file': 'uebung_admin.db',
        'level': 'admin'
    }
}


def get_current_db_path():
    """Gibt den aktuellen Datenbankpfad basierend auf Session zurück"""
    if 'current_database' in session and session['current_database'] != 'produktion':
        db_key = session['current_database']
        if db_key in TRAINING_DATABASES:
            training_path = os.path.join(TRAINING_DB_DIR, TRAINING_DATABASES[db_key]['file'])
            if os.path.exists(training_path):
                return training_path
    return DB_PATH_PRODUCTION


def get_available_training_dbs():
    """Gibt Liste der verfügbaren Trainingsdatenbanken zurück"""
    available = []
    for key, config in TRAINING_DATABASES.items():
        path = os.path.join(TRAINING_DB_DIR, config['file'])
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            available.append({
                'key': key,
                'name': config['name'],
                'description': config['description'],
                'level': config['level'],
                'size_kb': round(size_kb, 1)
            })
    return available


def is_training_mode():
    """Prüft ob aktuell im Trainingsmodus"""
    return session.get('current_database', 'produktion') != 'produktion'


def can_access_production():
    """Prüft ob Benutzer Zugriff auf Produktionsdatenbank hat"""
    # Admins haben immer Zugriff
    if session.get('is_admin'):
        return True
    # Prüfe ob nur Trainingsmodus erlaubt
    return not session.get('nur_training', False)
