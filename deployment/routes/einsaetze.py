# -*- coding: utf-8 -*-
"""
Einsätze - Erfassen, Anzeigen, Stornieren
"""

import csv
from io import StringIO, BytesIO
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from database import MaschinenDBContext
from utils.decorators import login_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

einsaetze_bp = Blueprint('einsaetze', __name__)


@einsaetze_bp.route('/neuer-einsatz', methods=['GET', 'POST'])
@login_required
def neuer_einsatz():
    """Neuen Einsatz erfassen"""
    db_path = get_current_db_path()

    if request.method == 'POST':
        try:
            datum = request.form.get('datum')
            maschine_id = int(request.form.get('maschine_id'))
            einsatzzweck_id = int(request.form.get('einsatzzweck_id'))
            anmerkungen = request.form.get('anmerkungen')
            treibstoff = request.form.get('treibstoffverbrauch')
            kosten = request.form.get('treibstoffkosten')
            flaeche_menge = request.form.get('flaeche_menge')

            with MaschinenDBContext(db_path) as db:
                maschine = db.get_maschine_by_id(maschine_id)
                erfassungsmodus = maschine.get('erfassungsmodus', 'fortlaufend')

                if erfassungsmodus == 'direkt':
                    direkt_wert = float(request.form.get('direkt_wert', 0))
                    if direkt_wert <= 0:
                        flash('Bitte geben Sie einen Wert ein!', 'danger')
                        return redirect(url_for('einsaetze.neuer_einsatz'))

                    aktueller_stand = maschine.get('stundenzaehler_aktuell', 0) or 0
                    anfangstand = aktueller_stand

                    if maschine.get('abrechnungsart') == 'stunden':
                        endstand = anfangstand + direkt_wert
                    else:
                        endstand = anfangstand + direkt_wert
                        if not flaeche_menge:
                            flaeche_menge = str(direkt_wert)
                else:
                    anfangstand = float(request.form.get('anfangstand'))
                    endstand = float(request.form.get('endstand'))

                    if endstand < anfangstand:
                        flash('Endstand muss größer oder gleich Anfangstand sein!', 'danger')
                        return redirect(url_for('einsaetze.neuer_einsatz'))

                db.add_einsatz(
                    datum=datum,
                    benutzer_id=session['benutzer_id'],
                    maschine_id=maschine_id,
                    einsatzzweck_id=einsatzzweck_id,
                    anfangstand=anfangstand,
                    endstand=endstand,
                    treibstoffverbrauch=float(treibstoff) if treibstoff else None,
                    treibstoffkosten=float(kosten) if kosten else None,
                    anmerkungen=anmerkungen if anmerkungen else None,
                    flaeche_menge=float(flaeche_menge) if flaeche_menge else None
                )

                if kosten:
                    cursor = db.connection.cursor()
                    sql = convert_sql("""
                        UPDATE benutzer
                        SET letzter_treibstoffpreis = ?
                        WHERE id = ?
                    """)
                    cursor.execute(sql, (float(kosten), session['benutzer_id']))
                    db.connection.commit()

            flash('Einsatz wurde erfolgreich gespeichert!', 'success')
            return redirect(url_for('dashboard.dashboard'))

        except Exception as e:
            flash(f'Fehler beim Speichern: {str(e)}', 'danger')
            return redirect(url_for('einsaetze.neuer_einsatz'))

    # GET - Formular anzeigen
    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT DISTINCT m.*
            FROM maschinen m
            JOIN gemeinschaften g ON m.gemeinschaft_id = g.id
            JOIN mitglied_gemeinschaft mg ON g.id = mg.gemeinschaft_id
            WHERE mg.mitglied_id = ?
              AND m.aktiv = true
              AND g.aktiv = true
            ORDER BY m.bezeichnung
        """)
        cursor.execute(sql, (session['benutzer_id'],))

        columns = [desc[0] for desc in cursor.description]
        maschinen = [dict(zip(columns, row)) for row in cursor.fetchall()]

        einsatzzwecke = db.get_all_einsatzzwecke()

        benutzer = db.get_benutzer(session['benutzer_id'])
        treibstoffkosten_preis = benutzer.get('treibstoffkosten_preis', 1.50) if benutzer else 1.50

        sql = convert_sql("""
            SELECT letzter_treibstoffpreis FROM benutzer WHERE id = ?
        """)
        cursor.execute(sql, (session['benutzer_id'],))
        result = cursor.fetchone()
        letzter_treibstoffpreis = result[0] if result and result[0] else None

    return render_template('neuer_einsatz.html',
                         maschinen=maschinen,
                         einsatzzwecke=einsatzzwecke,
                         heute=datetime.now().strftime('%Y-%m-%d'),
                         treibstoffkosten_preis=treibstoffkosten_preis,
                         letzter_treibstoffpreis=letzter_treibstoffpreis)


@einsaetze_bp.route('/meine-einsaetze')
@login_required
def meine_einsaetze():
    """Liste aller eigenen Einsätze"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        einsaetze = db.get_einsaetze_by_benutzer(session['benutzer_id'])

        for e in einsaetze:
            for key in ['anfangstand', 'endstand', 'flaeche_menge', 'betriebsstunden',
                       'treibstoffverbrauch', 'treibstoffkosten', 'kosten_berechnet']:
                if e.get(key) is None:
                    e[key] = 0

            abrechnungsart = e.get('abrechnungsart', 'stunden')
            preis = e.get('preis_pro_einheit', 0)

            if abrechnungsart == 'hektar':
                einheit = 'ha'
            elif abrechnungsart == 'kilometer':
                einheit = 'km'
            elif abrechnungsart == 'stueck':
                einheit = 'St'
            else:
                einheit = 'h'

            if e.get('erfassungsmodus', 'fortlaufend') == 'fortlaufend':
                menge = e['endstand'] - e['anfangstand']
            else:
                menge = e.get('flaeche_menge', 0)

            maschinenkosten = menge * preis

            if einheit == 'ha':
                menge_str = f"{menge:.2f} ha"
            elif einheit == 'km':
                menge_str = f"{menge:.1f} km"
            elif einheit == 'St':
                menge_str = f"{menge:.0f} St"
            else:
                menge_str = f"{menge:.1f} h"

            e['menge_berechnet'] = menge_str
            e['einheit'] = einheit
            e['maschinenkosten_berechnet'] = maschinenkosten

        summe_treibstoff = sum(e.get('treibstoffkosten', 0) for e in einsaetze)
        summe_maschine = sum(e.get('maschinenkosten_berechnet', 0) for e in einsaetze)
        summe_gesamt = summe_maschine

    return render_template('meine_einsaetze.html',
                         einsaetze=einsaetze,
                         summe_treibstoff=summe_treibstoff,
                         summe_maschine=summe_maschine,
                         summe_gesamt=summe_gesamt)


@einsaetze_bp.route('/einsatz/<int:einsatz_id>/stornieren', methods=['GET', 'POST'])
@login_required
def einsatz_stornieren(einsatz_id):
    """Einsatz stornieren"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT e.*, m.bezeichnung as maschine_name,
                   b.name as benutzer_name, b.vorname as benutzer_vorname
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            JOIN benutzer b ON e.benutzer_id = b.id
            WHERE e.id = ?
        """)
        cursor.execute(sql, (einsatz_id,))

        row = cursor.fetchone()
        if not row:
            flash('Einsatz nicht gefunden.', 'danger')
            return redirect(url_for('einsaetze.meine_einsaetze'))

        columns = [desc[0] for desc in cursor.description]
        einsatz = dict(zip(columns, row))

        if einsatz['benutzer_id'] != session['benutzer_id'] and not session.get('is_admin'):
            flash('Keine Berechtigung zum Stornieren dieses Einsatzes.', 'danger')
            return redirect(url_for('einsaetze.meine_einsaetze'))

        if request.method == 'POST':
            stornierungsgrund = request.form.get('stornierungsgrund', '')

            sql = convert_sql("""
                INSERT INTO maschineneinsaetze_storniert
                (original_einsatz_id, datum, benutzer_id, maschine_id, einsatzzweck_id,
                 stundenzaehler_anfang, stundenzaehler_ende, betriebsstunden,
                 hektar, kilometer, stueck, treibstoffverbrauch, treibstoffkosten,
                 maschinenkosten, gesamtkosten, bemerkung, storniert_am, storniert_von, stornierungsgrund)
                SELECT id, datum, benutzer_id, maschine_id, einsatzzweck_id,
                       anfangstand, endstand, betriebsstunden,
                       flaeche_menge, flaeche_menge, flaeche_menge, treibstoffverbrauch, treibstoffkosten,
                       kosten_berechnet, (COALESCE(treibstoffkosten, 0) + COALESCE(kosten_berechnet, 0)), anmerkungen, ?, ?, ?
                FROM maschineneinsaetze
                WHERE id = ?
            """)
            cursor.execute(sql, (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                session['benutzer_id'],
                stornierungsgrund,
                einsatz_id
            ))

            sql = convert_sql("DELETE FROM maschineneinsaetze WHERE id = ?")
            cursor.execute(sql, (einsatz_id,))
            db.connection.commit()

            flash('Einsatz wurde erfolgreich storniert.', 'success')

            if session.get('is_admin'):
                return redirect(url_for('admin_system.admin_alle_einsaetze'))
            else:
                return redirect(url_for('einsaetze.meine_einsaetze'))

        return render_template('einsatz_stornieren.html', einsatz=einsatz)


@einsaetze_bp.route('/meine-stornierten-einsaetze')
@login_required
def meine_stornierten_einsaetze():
    """Liste aller eigenen stornierten Einsätze"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT s.*, m.bezeichnung as maschine_name,
                   b.name as benutzer_name, b.vorname as benutzer_vorname,
                   sv.name as storniert_von_name, sv.vorname as storniert_von_vorname,
                   ez.bezeichnung as einsatzzweck_name
            FROM maschineneinsaetze_storniert s
            JOIN maschinen m ON s.maschine_id = m.id
            JOIN benutzer b ON s.benutzer_id = b.id
            JOIN benutzer sv ON s.storniert_von = sv.id
            LEFT JOIN einsatzzwecke ez ON s.einsatzzweck_id = ez.id
            WHERE s.benutzer_id = ?
            ORDER BY s.storniert_am DESC
        """)
        cursor.execute(sql, (session['benutzer_id'],))

        columns = [desc[0] for desc in cursor.description]
        stornierte_einsaetze = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('meine_stornierten_einsaetze.html',
                         stornierte_einsaetze=stornierte_einsaetze)


@einsaetze_bp.route('/meine-einsaetze/csv')
@login_required
def meine_einsaetze_csv():
    """Exportiere eigene Einsätze als CSV"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        einsaetze = db.get_einsaetze_by_benutzer(session['benutzer_id'])

    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer, delimiter=';')

    writer.writerow([
        'Datum', 'Benutzer', 'Maschine', 'Einsatzzweck',
        'Abrechnungsart', 'Preis pro Einheit',
        'Anfangstand', 'Endstand', 'Betriebsstunden',
        'Treibstoffverbrauch (l)', 'Treibstoffkosten (€)',
        'Fläche/Menge', 'Maschinenkosten (€)', 'Anmerkungen'
    ])

    def de_format(val, decimals=2):
        if val is None or val == '':
            return ''
        try:
            return f"{float(val):.{decimals}f}".replace('.', ',')
        except Exception:
            return str(val)

    def de_date(val):
        import datetime as dt
        if not val:
            return ''
        if isinstance(val, dt.date):
            return val.strftime('%d.%m.%Y')
        try:
            return dt.datetime.strptime(str(val), '%Y-%m-%d').strftime('%d.%m.%Y')
        except Exception:
            return str(val)

    for e in einsaetze:
        writer.writerow([
            de_date(e.get('datum', '')),
            e.get('benutzer', ''),
            e.get('maschine', ''),
            e.get('einsatzzweck', ''),
            e.get('abrechnungsart', 'stunden'),
            de_format(e.get('preis_pro_einheit'), 2),
            de_format(e.get('anfangstand'), 1),
            de_format(e.get('endstand'), 1),
            de_format(e.get('betriebsstunden'), 1),
            de_format(e.get('treibstoffverbrauch'), 1),
            de_format(e.get('treibstoffkosten'), 2),
            de_format(e.get('flaeche_menge'), 1),
            de_format(e.get('kosten_berechnet'), 2),
            e.get('anmerkungen', '')
        ])

    csv_bytes = BytesIO(csv_buffer.getvalue().encode('utf-8-sig'))
    csv_bytes.seek(0)

    filename = f'meine_einsaetze_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return send_file(
        csv_bytes,
        mimetype='text/csv; charset=utf-8',
        as_attachment=True,
        download_name=filename
    )
