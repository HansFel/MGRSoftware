# -*- coding: utf-8 -*-
"""
Dokumentations-Route

Zeigt Dokumentation für verschiedene Benutzergruppen:
- Benutzer: Anleitungen und Schnellstart
- Administratoren: Admin-Dokumentation
- System: Technische Dokumentation (nur Haupt-Admins)
"""

import os
import markdown
from flask import Blueprint, render_template, abort, session, redirect, url_for, current_app
from utils.decorators import login_required, admin_required

dokumentation_bp = Blueprint('dokumentation', __name__, url_prefix='/dokumentation')


def get_docs_base():
    """Ermittelt den Basis-Pfad für Dokumentation"""
    # Versuche verschiedene Pfade
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs'),
        '/opt/maschinengemeinschaft/docs',
        os.path.join(os.getcwd(), 'docs'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return possible_paths[0]  # Fallback


# Basis-Pfad für Dokumentation
DOCS_BASE = get_docs_base()

# Dokumentations-Struktur mit Zugriffsebenen
# level: 0 = alle eingeloggten Benutzer, 1 = Admins, 2 = Haupt-Admins
DOCS_STRUCTURE = {
    'benutzer': {
        'title': 'Benutzer-Dokumentation',
        'icon': 'bi-person',
        'level': 0,
        'docs': [
            {'file': 'benutzer/SCHNELLSTART.md', 'title': 'Schnellstart-Anleitung', 'icon': 'bi-rocket'},
            {'file': 'benutzer/WEB_ANLEITUNG.md', 'title': 'Web-Anleitung', 'icon': 'bi-globe'},
            {'file': 'benutzer/ANLEITUNG_TRANSAKTIONSZUORDNUNG.md', 'title': 'Transaktionszuordnung', 'icon': 'bi-cash-stack'},
        ]
    },
    'admin': {
        'title': 'Administrator-Dokumentation',
        'icon': 'bi-shield-lock',
        'level': 1,
        'docs': [
            {'file': 'admin/ADMIN_ROLLEN.md', 'title': 'Admin-Rollen & Berechtigungen', 'icon': 'bi-people'},
            {'file': 'admin/UEBUNGSMODUS.md', 'title': 'Übungsmodus', 'icon': 'bi-mortarboard'},
            {'file': 'admin/UPDATE_RESERVIERUNGEN.md', 'title': 'Reservierungen Update', 'icon': 'bi-calendar-check'},
            {'file': 'admin/IMPLEMENTIERUNG_RESERVIERUNGEN.md', 'title': 'Reservierungen Implementierung', 'icon': 'bi-code-slash'},
        ]
    },
    'system': {
        'title': 'System-Dokumentation',
        'icon': 'bi-server',
        'level': 2,
        'docs': [
            {'file': 'server-installation.md', 'title': 'Server-Installation', 'icon': 'bi-hdd-network'},
            {'file': 'system/POSTGRESQL_INSTALLATION.md', 'title': 'PostgreSQL Installation', 'icon': 'bi-database'},
            {'file': 'LOKALE_TESTVERSION.md', 'title': 'Lokale Testversion', 'icon': 'bi-laptop'},
        ]
    },
    'entwicklung': {
        'title': 'Geplante Erweiterungen',
        'icon': 'bi-lightbulb',
        'level': 2,
        'docs': [
            {'file': 'geplante-erweiterungen/erweiterungen_rollenverteilung.md', 'title': 'Rollenverteilung', 'icon': 'bi-diagram-3'},
            {'file': 'geplante-erweiterungen/abänderungen.md', 'title': 'Geplante Änderungen', 'icon': 'bi-pencil-square'},
        ]
    }
}


def get_user_level():
    """Gibt die Berechtigungsstufe des aktuellen Benutzers zurück"""
    if not session.get('user_id'):
        return -1
    admin_level = session.get('admin_level', 0)
    is_admin = session.get('is_admin', False)

    if admin_level >= 2:
        return 2  # Haupt-Admin
    elif admin_level >= 1 or is_admin:
        return 1  # Admin
    return 0  # Normaler Benutzer


def render_markdown(filepath):
    """Liest und rendert eine Markdown-Datei"""
    full_path = os.path.join(DOCS_BASE, filepath)

    if not os.path.exists(full_path):
        return None

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Markdown zu HTML konvertieren
        md = markdown.Markdown(extensions=[
            'tables',
            'fenced_code',
            'codehilite',
            'toc',
            'nl2br'
        ])
        html = md.convert(content)
        return html
    except Exception as e:
        return f"<p class='text-danger'>Fehler beim Laden: {str(e)}</p>"


@dokumentation_bp.route('/')
@login_required
def index():
    """Dokumentations-Übersicht"""
    from flask import flash

    user_level = get_user_level()

    # Debug-Ausgabe
    flash(f'DEBUG: DOCS_BASE={DOCS_BASE}, user_level={user_level}, user_id={session.get("user_id")}', 'info')

    # Filtere Kategorien nach Benutzer-Level
    available_categories = {}
    for key, category in DOCS_STRUCTURE.items():
        if category['level'] <= user_level:
            # Filtere auch einzelne Docs
            available_docs = []
            for d in category['docs']:
                full_path = os.path.join(DOCS_BASE, d['file'])
                exists = os.path.exists(full_path)
                if exists:
                    available_docs.append(d)
            if available_docs:
                available_categories[key] = {
                    **category,
                    'docs': available_docs
                }

    flash(f'DEBUG: Kategorien gefunden: {list(available_categories.keys())}', 'info')

    return render_template('dokumentation_index.html',
                          categories=available_categories,
                          user_level=user_level)


@dokumentation_bp.route('/<category>/<path:doc_path>')
@login_required
def show_doc(category, doc_path):
    """Zeigt ein einzelnes Dokument"""
    user_level = get_user_level()

    # Prüfe ob Kategorie existiert und Zugriff erlaubt
    if category not in DOCS_STRUCTURE:
        abort(404)

    cat_info = DOCS_STRUCTURE[category]
    if cat_info['level'] > user_level:
        abort(403)

    # Finde das Dokument
    doc_file = f"{category}/{doc_path}" if category in ['benutzer', 'admin', 'system', 'geplante-erweiterungen'] else doc_path

    # Suche in der Struktur
    doc_info = None
    for doc in cat_info['docs']:
        if doc['file'] == doc_file or doc['file'].endswith(doc_path):
            doc_info = doc
            break

    if not doc_info:
        # Versuche direkten Pfad
        doc_file = doc_path
        for doc in cat_info['docs']:
            if doc_path in doc['file']:
                doc_info = doc
                doc_file = doc['file']
                break

    if not doc_info:
        abort(404)

    # Rendere Markdown
    html_content = render_markdown(doc_file)
    if html_content is None:
        abort(404)

    return render_template('dokumentation_show.html',
                          content=html_content,
                          doc=doc_info,
                          category=cat_info,
                          category_key=category,
                          user_level=user_level)
