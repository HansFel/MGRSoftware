# -*- coding: utf-8 -*-
"""
Decorators für Zugriffsrechte
"""

from functools import wraps
from flask import session, flash, redirect, url_for


def login_required(f):
    """Decorator für geschützte Routen"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'benutzer_id' not in session:
            flash('Bitte melden Sie sich an.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator für Admin-Routen - Level 1 oder höher"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'benutzer_id' not in session:
            flash('Bitte melden Sie sich an.', 'warning')
            return redirect(url_for('auth.login'))
        if not session.get('is_admin'):
            flash('Zugriff verweigert. Administrator-Rechte erforderlich.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def hauptadmin_required(f):
    """Decorator für Haupt-Administrator-Routen - Level 2"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'benutzer_id' not in session:
            flash('Bitte melden Sie sich an.', 'warning')
            return redirect(url_for('auth.login'))
        if not session.get('is_admin'):
            flash('Zugriff verweigert. Administrator-Rechte erforderlich.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        if session.get('admin_level', 0) < 2:
            flash('Zugriff verweigert. Haupt-Administrator-Rechte erforderlich.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def rolle_required(*required_roles):
    """Decorator für rollenbasierte Zugriffskontrolle (Vorstandsmitglieder)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'benutzer_id' not in session:
                flash('Bitte melden Sie sich an.', 'warning')
                return redirect(url_for('auth.login'))

            user_rolle = session.get('rolle')
            admin_level = session.get('admin_level', 0)

            # Haupt-Admin (Level 2) hat immer Zugriff
            if admin_level >= 2:
                return f(*args, **kwargs)

            # Obmann hat alle Rechte
            if user_rolle == 'obmann':
                return f(*args, **kwargs)

            # Prüfe ob Benutzer eine der erforderlichen Rollen hat
            if user_rolle not in required_roles:
                flash('Keine Berechtigung für diese Funktion.', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def kassier_required(f):
    """Decorator für Kassier-Funktionen"""
    return rolle_required('kassier', 'obmann')(f)


def schriftfuehrer_required(f):
    """Decorator für Schriftführer-Funktionen"""
    return rolle_required('schriftfuehrer', 'obmann')(f)


def kassaprufer_required(f):
    """Decorator für Kassaprüfer-Funktionen"""
    return rolle_required('kassaprufer1', 'kassaprufer2', 'obmann')(f)
