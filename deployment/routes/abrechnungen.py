# -*- coding: utf-8 -*-
"""
Abrechnungen - Meine Abrechnungen, Konto-Übersicht
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response
from database import MaschinenDBContext
from utils.decorators import login_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

abrechnungen_bp = Blueprint('abrechnungen', __name__)


@abrechnungen_bp.route('/meine-abrechnungen')
@login_required
def meine_abrechnungen():
    """Zeigt alle Abrechnungen des angemeldeten Mitglieds"""
    benutzer_id = session.get('benutzer_id')
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT
                ma.id,
                ma.zeitraum_von,
                ma.zeitraum_bis,
                ma.betrag_maschinen,
                ma.betrag_treibstoff,
                ma.status,
                ma.erstellt_am,
                ma.bezahlt_am,
                g.name as gemeinschaft_name,
                g.id as gemeinschaft_id
            FROM mitglieder_abrechnungen ma
            JOIN gemeinschaften g ON ma.gemeinschaft_id = g.id
            WHERE ma.benutzer_id = ?
            ORDER BY ma.erstellt_am DESC
        """)
        cursor.execute(sql, (benutzer_id,))

        abrechnungen = []
        for row in cursor.fetchall():
            abrechnungen.append({
                'id': row[0],
                'zeitraum_von': row[1],
                'zeitraum_bis': row[2],
                'betrag_maschinen': row[3] or 0,
                'betrag_treibstoff': row[4] or 0,
                'betrag_gesamt': (row[3] or 0) + (row[4] or 0),
                'status': row[5],
                'erstellt_am': row[6],
                'bezahlt_am': row[7],
                'gemeinschaft_name': row[8],
                'gemeinschaft_id': row[9]
            })

        summe_offen = sum(a['betrag_gesamt'] for a in abrechnungen if a['status'] == 'offen')
        summe_bezahlt = sum(a['betrag_gesamt'] for a in abrechnungen if a['status'] == 'bezahlt')
        anzahl_offen = sum(1 for a in abrechnungen if a['status'] == 'offen')

        return render_template('meine_abrechnungen.html',
                             abrechnungen=abrechnungen,
                             summe_offen=summe_offen,
                             summe_bezahlt=summe_bezahlt,
                             anzahl_offen=anzahl_offen)


@abrechnungen_bp.route('/abrechnung/<int:abrechnung_id>/pdf')
@login_required
def abrechnung_pdf(abrechnung_id):
    """Generiert PDF für eine Abrechnung"""
    benutzer_id = session.get('benutzer_id')
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT
                ma.id,
                ma.zeitraum_von,
                ma.zeitraum_bis,
                ma.betrag_maschinen,
                ma.betrag_treibstoff,
                ma.status,
                ma.erstellt_am,
                g.name as gemeinschaft_name,
                g.bank_name,
                g.bank_iban,
                g.bank_bic,
                g.bank_kontoinhaber,
                b.name,
                b.vorname,
                b.email,
                g.adresse,
                g.telefon,
                g.email as gemeinschaft_email
            FROM mitglieder_abrechnungen ma
            JOIN gemeinschaften g ON ma.gemeinschaft_id = g.id
            JOIN benutzer b ON ma.benutzer_id = b.id
            WHERE ma.id = ? AND ma.benutzer_id = ?
        """)
        cursor.execute(sql, (abrechnung_id, benutzer_id))

        row = cursor.fetchone()
        if not row:
            flash('Abrechnung nicht gefunden!', 'danger')
            return redirect(url_for('abrechnungen.meine_abrechnungen'))

        abrechnung = {
            'id': row[0],
            'zeitraum_von': row[1],
            'zeitraum_bis': row[2],
            'betrag_maschinen': row[3] or 0,
            'betrag_treibstoff': row[4] or 0,
            'betrag_gesamt': (row[3] or 0) + (row[4] or 0),
            'status': row[5],
            'erstellt_am': row[6],
            'gemeinschaft_name': row[7],
            'bank_name': row[8],
            'bank_iban': row[9],
            'bank_bic': row[10],
            'bank_kontoinhaber': row[11],
            'mitglied_name': f"{row[13]} {row[12]}",
            'mitglied_email': row[14],
            'gemeinschaft_adresse': row[15],
            'gemeinschaft_telefon': row[16],
            'gemeinschaft_email': row[17]
        }

        sql = convert_sql("SELECT gemeinschaft_id FROM mitglieder_abrechnungen WHERE id = ?")
        cursor.execute(sql, (abrechnung_id,))
        abrechnung_gemeinschaft_id = cursor.fetchone()[0]

        sql = convert_sql("""
            SELECT
                m.bezeichnung,
                me.datum,
                me.endstand - me.anfangstand as betriebsstunden,
                m.preis_pro_einheit,
                me.kosten_berechnet,
                me.treibstoffverbrauch,
                me.treibstoffkosten,
                m.treibstoff_berechnen
            FROM maschineneinsaetze me
            JOIN maschinen m ON me.maschine_id = m.id
            WHERE me.benutzer_id = ?
            AND me.datum >= ?
            AND me.datum <= ?
            AND m.gemeinschaft_id = ?
            ORDER BY me.datum
        """)
        cursor.execute(sql, (benutzer_id, abrechnung['zeitraum_von'],
                            abrechnung['zeitraum_bis'], abrechnung_gemeinschaft_id))

        einsaetze = []
        for row in cursor.fetchall():
            treibstoff_berechnen = row[7]
            einsaetze.append({
                'maschine': row[0],
                'datum': row[1],
                'betriebsstunden': row[2] if row[2] else 0,
                'preis_pro_stunde': row[3] if row[3] else 0,
                'betrag_maschine': row[4] if row[4] else 0,
                'treibstoff_liter': row[5] if treibstoff_berechnen and row[5] else 0,
                'treibstoffkosten': row[6] if treibstoff_berechnen and row[6] else 0,
                'treibstoff_berechnen': treibstoff_berechnen
            })

        html = render_template('abrechnung_pdf.html',
                             abrechnung=abrechnung,
                             einsaetze=einsaetze)

        response = make_response(html)
        response.headers['Content-Type'] = 'text/html'
        response.headers['Content-Disposition'] = f'inline; filename=Abrechnung_{abrechnung_id}.html'

        return response


@abrechnungen_bp.route('/mein-konto/<int:gemeinschaft_id>')
@login_required
def mein_konto(gemeinschaft_id):
    """Kontoübersicht für ein Mitglied in einer Gemeinschaft"""
    benutzer_id = session.get('benutzer_id')
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Gemeinschaft laden
        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        if not row:
            flash('Gemeinschaft nicht gefunden!', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        gemeinschaft = dict(zip(columns, row))

        # Prüfe Mitgliedschaft
        sql = convert_sql("""
            SELECT COUNT(*) FROM mitglied_gemeinschaft
            WHERE mitglied_id = ? AND gemeinschaft_id = ?
        """)
        cursor.execute(sql, (benutzer_id, gemeinschaft_id))
        if cursor.fetchone()[0] == 0:
            flash('Sie sind nicht Mitglied dieser Gemeinschaft!', 'danger')
            return redirect(url_for('dashboard.dashboard'))

        # Konto laden oder erstellen
        sql = convert_sql("""
            SELECT * FROM mitglieder_konten
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
        """)
        cursor.execute(sql, (benutzer_id, gemeinschaft_id))
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

        if row:
            konto = dict(zip(columns, row))
            saldo = konto.get('kontostand', 0) or 0
        else:
            konto = {'kontostand': 0}
            saldo = 0

        # Buchungen laden (über benutzer_id und gemeinschaft_id)
        sql = convert_sql("""
            SELECT b.*,
                   b.referenz_typ,
                   b.referenz_id
            FROM buchungen b
            WHERE b.benutzer_id = ? AND b.gemeinschaft_id = ?
            ORDER BY b.datum DESC, b.id DESC
            LIMIT 100
        """)
        cursor.execute(sql, (benutzer_id, gemeinschaft_id))
        columns = [desc[0] for desc in cursor.description]
        buchungen = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Offene Abrechnungen laden
        sql = convert_sql("""
            SELECT ma.id, ma.zeitraum_von, ma.zeitraum_bis,
                   ma.betrag_maschinen, ma.betrag_treibstoff,
                   COALESCE(ma.betrag_maschinen, 0) + COALESCE(ma.betrag_treibstoff, 0) as betrag_gesamt,
                   ma.status, ma.erstellt_am
            FROM mitglieder_abrechnungen ma
            WHERE ma.benutzer_id = ? AND ma.gemeinschaft_id = ? AND ma.status = 'offen'
            ORDER BY ma.erstellt_am DESC
        """)
        cursor.execute(sql, (benutzer_id, gemeinschaft_id))
        columns = [desc[0] for desc in cursor.description]
        offene_abrechnungen = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Saldo Vorjahr (vereinfacht: 0)
        saldo_vorjahr = 0

    return render_template('mein_konto.html',
                         gemeinschaft=gemeinschaft,
                         saldo=saldo,
                         saldo_vorjahr=saldo_vorjahr,
                         offene_abrechnungen=offene_abrechnungen,
                         buchungen=buchungen)
