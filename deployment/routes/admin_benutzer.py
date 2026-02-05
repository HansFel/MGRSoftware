# -*- coding: utf-8 -*-
"""
Admin - Benutzerverwaltung
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import MaschinenDBContext
from utils.decorators import admin_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

admin_benutzer_bp = Blueprint('admin_benutzer', __name__, url_prefix='/admin')


@admin_benutzer_bp.route('/benutzer')
@admin_required
def admin_benutzer():
    """Benutzerverwaltung"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        benutzer = db.get_all_benutzer(nur_aktive=False)
    return render_template('admin_benutzer.html', benutzer=benutzer)


@admin_benutzer_bp.route('/benutzer/neu', methods=['GET', 'POST'])
@admin_required
def admin_benutzer_neu():
    """Neuen Benutzer anlegen"""
    db_path = get_current_db_path()
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash('Name ist erforderlich!', 'danger')
            return redirect(url_for('admin_benutzer.admin_benutzer_neu'))

        with MaschinenDBContext(db_path) as db:
            db.add_benutzer(
                name=name,
                vorname=request.form.get('vorname'),
                username=request.form.get('username'),
                password=request.form.get('password'),
                is_admin=bool(request.form.get('is_admin')),
                telefon=request.form.get('telefon'),
                email=request.form.get('email')
            )
        flash('Benutzer erfolgreich angelegt!', 'success')
        return redirect(url_for('admin_benutzer.admin_benutzer'))

    # Gemeinschaften laden für Formular
    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()
        sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true ORDER BY name")
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        gemeinschaften = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('admin_benutzer_form.html', benutzer=None, gemeinschaften=gemeinschaften)


@admin_benutzer_bp.route('/benutzer/<int:benutzer_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_benutzer_edit(benutzer_id):
    """Benutzer bearbeiten"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        if request.method == 'POST':
            name = request.form.get('name')
            if not name:
                flash('Name ist erforderlich!', 'danger')
                return redirect(url_for('admin_benutzer.admin_benutzer_edit', benutzer_id=benutzer_id))

            update_data = {
                'name': name,
                'vorname': request.form.get('vorname'),
                'username': request.form.get('username'),
                'is_admin': bool(request.form.get('is_admin')),
                'telefon': request.form.get('telefon'),
                'email': request.form.get('email')
            }
            password = request.form.get('password')
            if password:
                db.update_password(benutzer_id, password)
            db.update_benutzer(benutzer_id, **update_data)
            flash('Benutzer erfolgreich aktualisiert!', 'success')
            return redirect(url_for('admin_benutzer.admin_benutzer'))

        benutzer = db.get_benutzer_by_id(benutzer_id)

        # Gemeinschaften laden
        cursor = db.connection.cursor()
        sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true ORDER BY name")
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        gemeinschaften = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('admin_benutzer_form.html', benutzer=benutzer, gemeinschaften=gemeinschaften)


@admin_benutzer_bp.route('/benutzer/<int:benutzer_id>/delete', methods=['POST'])
@admin_required
def admin_benutzer_delete(benutzer_id):
    """Benutzer löschen"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        benutzer = db.get_benutzer_by_id(benutzer_id)
        db.delete_benutzer(benutzer_id, soft_delete=False)
    flash(f'Benutzer {benutzer["name"]} wurde gelöscht.', 'success')
    return redirect(url_for('admin_benutzer.admin_benutzer'))


@admin_benutzer_bp.route('/benutzer/<int:benutzer_id>/activate', methods=['POST'])
@admin_required
def admin_benutzer_activate(benutzer_id):
    """Benutzer reaktivieren"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        benutzer = db.get_benutzer_by_id(benutzer_id)
        db.activate_benutzer(benutzer_id)
    flash(f'Benutzer {benutzer["name"]} wurde reaktiviert.', 'success')
    return redirect(url_for('admin_benutzer.admin_benutzer'))
