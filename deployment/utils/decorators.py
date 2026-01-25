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
