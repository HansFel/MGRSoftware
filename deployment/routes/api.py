# -*- coding: utf-8 -*-
"""
API-Endpunkte für AJAX-Anfragen
"""

from flask import Blueprint, jsonify
from database import MaschinenDBContext
from utils.decorators import login_required
from utils.training import get_current_db_path

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/maschine/<int:maschine_id>/stundenzaehler')
@login_required
def get_stundenzaehler(maschine_id):
    """API: Aktuellen Stundenzählerstand abrufen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        maschine = db.get_maschine_by_id(maschine_id)
        if maschine:
            return jsonify({
                'success': True,
                'stundenzaehler': maschine.get('stundenzaehler_aktuell', 0)
            })
        return jsonify({'success': False}), 404


@api_bp.route('/maschine/<int:maschine_id>')
@login_required
def api_maschine_details(maschine_id):
    """API-Endpunkt für Maschinen-Details (für AJAX)"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        maschine = db.get_maschine(maschine_id)

    if maschine:
        return jsonify({
            'success': True,
            'stundenzaehler': maschine['stundenzaehler_aktuell'],
            'bezeichnung': maschine['bezeichnung'],
            'erfassungsmodus': maschine.get('erfassungsmodus', 'fortlaufend'),
            'abrechnungsart': maschine.get('abrechnungsart', 'stunden'),
            'preis_pro_einheit': maschine.get('preis_pro_einheit', 0)
        })
    return jsonify({'success': False}), 404
