# -*- coding: utf-8 -*-
"""
Admin - Maschinenverwaltung und Rentabilität
"""

from datetime import datetime
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import MaschinenDBContext
from utils.decorators import admin_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql, db_execute

admin_maschinen_bp = Blueprint('admin_maschinen', __name__, url_prefix='/admin')


@admin_maschinen_bp.route('/maschinen')
@admin_required
def admin_maschinen():
    """Maschinenverwaltung"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        maschinen = db.get_all_maschinen(nur_aktive=False)
    return render_template('admin_maschinen.html', maschinen=maschinen)


@admin_maschinen_bp.route('/maschinen/neu', methods=['GET', 'POST'])
@admin_required
def admin_maschinen_neu():
    """Neue Maschine anlegen"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        if request.method == 'POST':
            maschine_id = db.add_maschine(
                bezeichnung=request.form['bezeichnung'],
                hersteller=request.form.get('hersteller'),
                modell=request.form.get('modell'),
                baujahr=int(request.form['baujahr']) if request.form.get('baujahr') else None,
                kennzeichen=request.form.get('kennzeichen'),
                stundenzaehler_aktuell=float(request.form.get('stundenzaehler_aktuell', 0)),
                wartungsintervall=int(request.form.get('wartungsintervall', 50)),
                naechste_wartung=float(request.form.get('naechste_wartung')) if request.form.get('naechste_wartung') else None,
                anmerkungen=request.form.get('anmerkungen'),
                abrechnungsart=request.form.get('abrechnungsart', 'stunden'),
                preis_pro_einheit=float(request.form.get('preis_pro_einheit', 0)),
                erfassungsmodus=request.form.get('erfassungsmodus', 'fortlaufend'),
                gemeinschaft_id=int(request.form['gemeinschaft_id']),
                anschaffungspreis=float(request.form.get('anschaffungspreis', 0)),
                abschreibungsdauer_jahre=int(request.form.get('abschreibungsdauer_jahre', 10)),
                anschaffungsdatum=request.form.get('anschaffungsdatum') if request.form.get('anschaffungsdatum') else None
            )

            cursor = db.connection.cursor()
            treibstoff_berechnen = True if request.form.get('treibstoff_berechnen') else False
            sql = convert_sql("UPDATE maschinen SET treibstoff_berechnen = ? WHERE id = ?")
            cursor.execute(sql, (treibstoff_berechnen, maschine_id))

            flash('Maschine erfolgreich angelegt!', 'success')
            return redirect(url_for('admin_maschinen.admin_maschinen'))

        cursor = db.cursor
        sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true ORDER BY name")
        cursor.execute(sql)
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    return render_template('admin_maschinen_form.html', maschine=None, gemeinschaften=gemeinschaften)


@admin_maschinen_bp.route('/maschinen/<int:maschine_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_maschinen_edit(maschine_id):
    """Maschine bearbeiten"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        if request.method == 'POST':
            update_data = {
                'bezeichnung': request.form['bezeichnung'],
                'hersteller': request.form.get('hersteller'),
                'modell': request.form.get('modell'),
                'baujahr': int(request.form['baujahr']) if request.form.get('baujahr') else None,
                'kennzeichen': request.form.get('kennzeichen'),
                'stundenzaehler_aktuell': float(request.form.get('stundenzaehler_aktuell', 0)),
                'wartungsintervall': int(request.form.get('wartungsintervall', 50)),
                'naechste_wartung': float(request.form.get('naechste_wartung')) if request.form.get('naechste_wartung') else None,
                'anmerkungen': request.form.get('anmerkungen'),
                'abrechnungsart': request.form.get('abrechnungsart', 'stunden'),
                'preis_pro_einheit': float(request.form.get('preis_pro_einheit', 0)),
                'erfassungsmodus': request.form.get('erfassungsmodus', 'fortlaufend'),
                'gemeinschaft_id': int(request.form['gemeinschaft_id']),
                'anschaffungspreis': float(request.form.get('anschaffungspreis', 0)),
                'abschreibungsdauer_jahre': int(request.form.get('abschreibungsdauer_jahre', 10)),
                'anschaffungsdatum': request.form.get('anschaffungsdatum') if request.form.get('anschaffungsdatum') else None
            }
            db.update_maschine(maschine_id, **update_data)

            cursor = db.connection.cursor()
            treibstoff_berechnen = True if request.form.get('treibstoff_berechnen') else False
            sql = convert_sql("UPDATE maschinen SET treibstoff_berechnen = ? WHERE id = ?")
            cursor.execute(sql, (treibstoff_berechnen, maschine_id))

            flash('Maschine erfolgreich aktualisiert!', 'success')
            return redirect(url_for('admin_maschinen.admin_maschinen'))

        maschine = db.get_maschine_by_id(maschine_id)

        cursor = db.connection.cursor()
        sql = convert_sql("SELECT treibstoff_berechnen FROM maschinen WHERE id = ?")
        cursor.execute(sql, (maschine_id,))
        result = cursor.fetchone()
        maschine['treibstoff_berechnen'] = result[0] if result else 0

        sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true ORDER BY name")
        cursor.execute(sql)
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    return render_template('admin_maschinen_form.html', maschine=maschine, gemeinschaften=gemeinschaften)


@admin_maschinen_bp.route('/maschinen/<int:maschine_id>/delete', methods=['POST'])
@admin_required
def admin_maschinen_delete(maschine_id):
    """Maschine löschen"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        maschine = db.get_maschine_by_id(maschine_id)
        db.delete_maschine(maschine_id)
    flash(f'Maschine {maschine["bezeichnung"]} wurde gelöscht.', 'success')
    return redirect(url_for('admin_maschinen.admin_maschinen'))


@admin_maschinen_bp.route('/maschinen/<int:maschine_id>/rentabilitaet')
@admin_required
def admin_maschinen_rentabilitaet(maschine_id):
    """Rentabilitätsbericht für eine Maschine"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.cursor
        maschine = db.get_maschine_by_id(maschine_id)

        sql = convert_sql("""
            SELECT
                COUNT(e.id) as anzahl_einsaetze,
                SUM(e.endstand - e.anfangstand) as betriebsstunden_gesamt,
                SUM(
                    CASE
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as einnahmen_gesamt
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            WHERE m.id = ?
        """)
        cursor.execute(sql, (maschine_id,))
        row = cursor.fetchone()
        anzahl_einsaetze = row[0] or 0
        betriebsstunden = row[1] or 0
        einnahmen = row[2] or 0

        anschaffungspreis = maschine.get('anschaffungspreis', 0) or 0
        abschreibungsdauer = maschine.get('abschreibungsdauer_jahre', 10) or 10
        anschaffungsdatum = maschine.get('anschaffungsdatum')
        abschreibung_pro_jahr = anschaffungspreis / abschreibungsdauer if abschreibungsdauer > 0 else 0

        alter_jahre_float = 0
        alter_jahre = 0
        alter_error = None
        if anschaffungsdatum:
            try:
                datum = datetime.strptime(str(anschaffungsdatum)[:10], '%Y-%m-%d')
                tage = (datetime.now() - datum).days
                alter_jahre_float = tage / 365.25
                alter_jahre = max(0, int(tage // 365))
            except Exception as e:
                alter_error = f"Ungültiges Anschaffungsdatum: {anschaffungsdatum}"
        else:
            alter_error = "Kein Anschaffungsdatum hinterlegt"

        abschreibung_bisher = min(abschreibung_pro_jahr * alter_jahre_float, anschaffungspreis)
        restwert = max(anschaffungspreis - abschreibung_bisher, 0)

        sql = convert_sql("""
            SELECT jahr, wartungskosten, reparaturkosten, versicherung, steuern, sonstige_kosten
            FROM maschinen_aufwendungen
            WHERE maschine_id = ?
            ORDER BY jahr
        """)
        cursor.execute(sql, (maschine_id,))
        columns = [desc[0] for desc in cursor.description]
        alle_aufwendungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
        aufwendungen_gesamt = sum(
            (a.get('wartungskosten') or 0) + (a.get('reparaturkosten') or 0) +
            (a.get('versicherung') or 0) + (a.get('steuern') or 0) + (a.get('sonstige_kosten') or 0)
            for a in alle_aufwendungen
        )

        sql = convert_sql("""
            SELECT datum, betrag, beschreibung, typ FROM buchungen
            WHERE referenz_typ = 'maschine' AND referenz_id = ?
            ORDER BY datum
        """)
        cursor.execute(sql, (maschine_id,))
        bankbuchungen = [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
        bankkosten_gesamt = sum(b['betrag'] for b in bankbuchungen)

        db_execute(cursor, """
            SELECT
                strftime('%Y', e.datum) as jahr,
                COUNT(e.id) as anzahl,
                SUM(e.endstand - e.anfangstand) as stunden,
                SUM(
                    CASE
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as einnahmen
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            WHERE m.id = ?
            GROUP BY jahr
            ORDER BY jahr DESC
        """, (maschine_id,))
        columns = [desc[0] for desc in cursor.description]
        einsaetze_pro_jahr = [dict(zip(columns, row)) for row in cursor.fetchall()]

        aufwendungen_dict = {str(a['jahr']): a for a in alle_aufwendungen}
        for einsatz in einsaetze_pro_jahr:
            jahr = einsatz['jahr']
            if jahr in aufwendungen_dict:
                a = aufwendungen_dict[jahr]
                einsatz['aufwendungen'] = (
                    (a.get('wartungskosten') or 0) + (a.get('reparaturkosten') or 0) +
                    (a.get('versicherung') or 0) + (a.get('steuern') or 0) + (a.get('sonstige_kosten') or 0)
                )
            else:
                einsatz['aufwendungen'] = 0
            einsatz['gewinn'] = (einsatz['einnahmen'] or 0) - einsatz['aufwendungen']

        gesamtkosten = aufwendungen_gesamt + bankkosten_gesamt
        deckungsbeitrag = einnahmen - abschreibung_pro_jahr - gesamtkosten
        rentabilitaet_prozent = (deckungsbeitrag / anschaffungspreis * 100) if anschaffungspreis > 0 else 0

        rentabilitaet = {
            'anzahl_einsaetze': anzahl_einsaetze,
            'betriebsstunden': betriebsstunden,
            'einnahmen_gesamt': einnahmen,
            'aufwendungen_gesamt': aufwendungen_gesamt,
            'bankkosten_gesamt': bankkosten_gesamt,
            'gesamtkosten': gesamtkosten,
            'anschaffungspreis': anschaffungspreis,
            'abschreibungsdauer': abschreibungsdauer,
            'abschreibung_pro_jahr': abschreibung_pro_jahr,
            'alter_jahre': alter_jahre,
            'alter_jahre_float': alter_jahre_float,
            'alter_error': alter_error,
            'abschreibung_bisher': abschreibung_bisher,
            'restwert': restwert,
            'deckungsbeitrag': deckungsbeitrag,
            'rentabilitaet_prozent': rentabilitaet_prozent
        }

    return render_template('admin_maschinen_rentabilitaet.html',
                         maschine=maschine,
                         rentabilitaet=rentabilitaet,
                         einsaetze_pro_jahr=einsaetze_pro_jahr,
                         bankbuchungen=bankbuchungen)


@admin_maschinen_bp.route('/maschinen/<int:maschine_id>/aufwendungen', methods=['GET', 'POST'])
@admin_required
def admin_maschinen_aufwendungen(maschine_id):
    """Jährliche Aufwendungen für eine Maschine verwalten"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()
        maschine = db.get_maschine_by_id(maschine_id)
        aktuelles_jahr = datetime.now().year

        if request.method == 'POST':
            jahr = int(request.form.get('jahr', aktuelles_jahr))
            wartungskosten = float(request.form.get('wartungskosten', 0))
            reparaturkosten = float(request.form.get('reparaturkosten', 0))
            versicherung = float(request.form.get('versicherung', 0))
            steuern = float(request.form.get('steuern', 0))
            sonstige_kosten = float(request.form.get('sonstige_kosten', 0))
            bemerkung = request.form.get('bemerkung', '')

            sql = convert_sql("""
                INSERT INTO maschinen_aufwendungen
                (maschine_id, jahr, wartungskosten, reparaturkosten, versicherung, steuern, sonstige_kosten, bemerkung)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(maschine_id, jahr) DO UPDATE SET
                    wartungskosten = excluded.wartungskosten,
                    reparaturkosten = excluded.reparaturkosten,
                    versicherung = excluded.versicherung,
                    steuern = excluded.steuern,
                    sonstige_kosten = excluded.sonstige_kosten,
                    bemerkung = excluded.bemerkung,
                    geaendert_am = CURRENT_TIMESTAMP
            """)
            cursor.execute(sql, (maschine_id, jahr, wartungskosten, reparaturkosten,
                                versicherung, steuern, sonstige_kosten, bemerkung))

            db.connection.commit()
            flash(f'Aufwendungen für {jahr} gespeichert.', 'success')
            return redirect(url_for('admin_maschinen.admin_maschinen_aufwendungen', maschine_id=maschine_id))

        sql = convert_sql("""
            SELECT * FROM maschinen_aufwendungen
            WHERE maschine_id = ? AND jahr = ?
        """)
        cursor.execute(sql, (maschine_id, aktuelles_jahr))

        row = cursor.fetchone()
        aktuelle_aufwendung = {}
        if row:
            columns = [desc[0] for desc in cursor.description]
            aktuelle_aufwendung = dict(zip(columns, row))

        sql = convert_sql("""
            SELECT * FROM maschinen_aufwendungen
            WHERE maschine_id = ? AND jahr != ?
            ORDER BY jahr DESC
        """)
        cursor.execute(sql, (maschine_id, aktuelles_jahr))

        columns = [desc[0] for desc in cursor.description]
        aufwendungen_historie = [dict(zip(columns, row)) for row in cursor.fetchall()]

        summe = {
            'wartungskosten': sum(a.get('wartungskosten', 0) or 0 for a in aufwendungen_historie),
            'reparaturkosten': sum(a.get('reparaturkosten', 0) or 0 for a in aufwendungen_historie),
            'versicherung': sum(a.get('versicherung', 0) or 0 for a in aufwendungen_historie),
            'steuern': sum(a.get('steuern', 0) or 0 for a in aufwendungen_historie),
            'sonstige_kosten': sum(a.get('sonstige_kosten', 0) or 0 for a in aufwendungen_historie)
        }
        summe['gesamt'] = sum(summe.values())

    return render_template('admin_maschinen_aufwendungen.html',
                         maschine=maschine,
                         aktuelles_jahr=aktuelles_jahr,
                         aktuelle_aufwendung=aktuelle_aufwendung,
                         aufwendungen_historie=aufwendungen_historie,
                         summe=summe)
