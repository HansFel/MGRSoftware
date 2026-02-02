# -*- coding: utf-8 -*-
"""
Admin - Einsatzzwecke-Verwaltung
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import MaschinenDBContext
from utils.decorators import admin_required
from utils.training import get_current_db_path

admin_einsatzzwecke_bp = Blueprint('admin_einsatzzwecke', __name__, url_prefix='/admin')


@admin_einsatzzwecke_bp.route('/einsatzzwecke')
@admin_required
def admin_einsatzzwecke():
    """Einsatzzwecke verwalten"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        einsatzzwecke = db.get_all_einsatzzwecke(nur_aktive=False)
    return render_template('admin_einsatzzwecke.html', einsatzzwecke=einsatzzwecke)


@admin_einsatzzwecke_bp.route('/einsatzzwecke/neu', methods=['GET', 'POST'])
@admin_required
def admin_einsatzzwecke_neu():
    """Neuer Einsatzzweck"""
    db_path = get_current_db_path()
    if request.method == 'POST':
        bezeichnung = request.form.get('bezeichnung')
        if not bezeichnung:
            flash('Bezeichnung ist erforderlich!', 'danger')
            return redirect(url_for('admin_einsatzzwecke.admin_einsatzzwecke_neu'))

        with MaschinenDBContext(db_path) as db:
            db.add_einsatzzweck(
                bezeichnung=bezeichnung,
                beschreibung=request.form.get('beschreibung')
            )
        flash('Einsatzzweck erfolgreich angelegt!', 'success')
        return redirect(url_for('admin_einsatzzwecke.admin_einsatzzwecke'))
    return render_template('admin_einsatzzwecke_form.html', einsatzzweck=None)


@admin_einsatzzwecke_bp.route('/einsatzzwecke/<int:einsatzzweck_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_einsatzzwecke_edit(einsatzzweck_id):
    """Einsatzzweck bearbeiten"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        if request.method == 'POST':
            bezeichnung = request.form.get('bezeichnung')
            if not bezeichnung:
                flash('Bezeichnung ist erforderlich!', 'danger')
                return redirect(url_for('admin_einsatzzwecke.admin_einsatzzwecke_edit', einsatzzweck_id=einsatzzweck_id))

            update_data = {
                'bezeichnung': bezeichnung,
                'beschreibung': request.form.get('beschreibung'),
                'aktiv': 1 if request.form.get('aktiv') else 0
            }
            db.update_einsatzzweck(einsatzzweck_id, **update_data)
            flash('Einsatzzweck erfolgreich aktualisiert!', 'success')
            return redirect(url_for('admin_einsatzzwecke.admin_einsatzzwecke'))

        einsatzzweck = db.get_einsatzzweck_by_id(einsatzzweck_id)
    return render_template('admin_einsatzzwecke_form.html', einsatzzweck=einsatzzweck)


@admin_einsatzzwecke_bp.route('/einsatzzwecke/<int:einsatzzweck_id>/delete', methods=['POST'])
@admin_required
def admin_einsatzzwecke_delete(einsatzzweck_id):
    """Einsatzzweck löschen"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        einsatzzweck = db.get_einsatzzweck_by_id(einsatzzweck_id)
        db.delete_einsatzzweck(einsatzzweck_id, soft_delete=False)
    flash(f'Einsatzzweck {einsatzzweck["bezeichnung"]} wurde gelöscht.', 'success')
    return redirect(url_for('admin_einsatzzwecke.admin_einsatzzwecke'))


@admin_einsatzzwecke_bp.route('/einsatzzwecke/<int:einsatzzweck_id>/activate', methods=['POST'])
@admin_required
def admin_einsatzzwecke_activate(einsatzzweck_id):
    """Einsatzzweck reaktivieren"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        db.activate_einsatzzweck(einsatzzweck_id)
    flash('Einsatzzweck wurde reaktiviert.', 'success')
    return redirect(url_for('admin_einsatzzwecke.admin_einsatzzwecke'))
