# -*- coding: utf-8 -*-
"""
Routes-Module für Maschinengemeinschaft Web-App
Enthält alle Flask Blueprints
"""

from .auth import auth_bp
from .dashboard import dashboard_bp
from .einsaetze import einsaetze_bp
from .reservierungen import reservierungen_bp
from .nachrichten import nachrichten_bp
from .abrechnungen import abrechnungen_bp
from .admin_benutzer import admin_benutzer_bp
from .admin_maschinen import admin_maschinen_bp
from .admin_einsatzzwecke import admin_einsatzzwecke_bp
from .admin_gemeinschaften import admin_gemeinschaften_bp
from .admin_finanzen import admin_finanzen_bp
from .admin_system import admin_system_bp
from .api import api_bp

# Alle Blueprints für einfachen Import
all_blueprints = [
    auth_bp,
    dashboard_bp,
    einsaetze_bp,
    reservierungen_bp,
    nachrichten_bp,
    abrechnungen_bp,
    admin_benutzer_bp,
    admin_maschinen_bp,
    admin_einsatzzwecke_bp,
    admin_gemeinschaften_bp,
    admin_finanzen_bp,
    admin_system_bp,
    api_bp,
]
