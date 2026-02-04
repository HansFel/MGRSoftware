# -*- coding: utf-8 -*-
"""
Flask-Webanwendung für Maschinengemeinschaft
Modulare Version - Hauptdatei

Struktur:
- routes/         - Alle Flask Blueprints (Routen)
- utils/          - Hilfsfunktionen (Decorators, SQL-Helpers, Training)
- database.py     - Datenbank-Modul
- templates/      - HTML-Templates
- static/         - CSS, JS, Fonts

Erstellt: Januar 2026
"""

import os
from flask import Flask, session

# Schema-Migration beim Start ausführen
from utils.schema_migration import run_migrations
run_migrations()

# App initialisieren
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Datenbank-Pfad (wird von utils.training verwendet)
DB_PATH_PRODUCTION = os.environ.get('DB_PATH', './data/maschinengemeinschaft.db')
DB_PATH = DB_PATH_PRODUCTION

# Utils importieren
from utils.training import (
    TRAINING_DATABASES,
    get_current_db_path,
    is_training_mode
)

# Blueprints importieren
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.einsaetze import einsaetze_bp
from routes.reservierungen import reservierungen_bp
from routes.nachrichten import nachrichten_bp
from routes.abrechnungen import abrechnungen_bp
from routes.api import api_bp
from routes.admin_benutzer import admin_benutzer_bp
from routes.admin_maschinen import admin_maschinen_bp
from routes.admin_einsatzzwecke import admin_einsatzzwecke_bp
from routes.admin_gemeinschaften import admin_gemeinschaften_bp
from routes.admin_finanzen import admin_finanzen_bp
from routes.admin_system import admin_system_bp
from routes.admin_schriftfuehrer import admin_schriftfuehrer_bp

# Blueprints registrieren
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(einsaetze_bp)
app.register_blueprint(reservierungen_bp)
app.register_blueprint(nachrichten_bp)
app.register_blueprint(abrechnungen_bp)
app.register_blueprint(api_bp)
app.register_blueprint(admin_benutzer_bp)
app.register_blueprint(admin_maschinen_bp)
app.register_blueprint(admin_einsatzzwecke_bp)
app.register_blueprint(admin_gemeinschaften_bp)
app.register_blueprint(admin_finanzen_bp)
app.register_blueprint(admin_system_bp)
app.register_blueprint(admin_schriftfuehrer_bp)


@app.context_processor
def inject_database_info():
    """Fügt Datenbank-Info zu allen Templates hinzu"""
    current_db = session.get('current_database', 'produktion')
    is_training = current_db != 'produktion'

    db_info = {
        'current_database': current_db,
        'is_training_mode': is_training,
        'database_name': 'Produktion'
    }

    if is_training and current_db in TRAINING_DATABASES:
        db_info['database_name'] = TRAINING_DATABASES[current_db]['name']

    return {'db_info': db_info}


@app.before_request
def set_database_path():
    """Setzt DB_PATH basierend auf Session vor jedem Request"""
    global DB_PATH
    DB_PATH = get_current_db_path()


# Für Gunicorn/WSGI
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
