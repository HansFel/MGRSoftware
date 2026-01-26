# -*- coding: utf-8 -*-
"""
Admin - Finanzen, Konten, Buchungen, CSV-Import
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import MaschinenDBContext
from utils.decorators import admin_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

admin_finanzen_bp = Blueprint('admin_finanzen', __name__, url_prefix='/admin')


@admin_finanzen_bp.route('/gemeinschaften/<int:gemeinschaft_id>/konten')
@admin_required
def admin_konten(gemeinschaft_id):
    """Mitgliederkonten-Übersicht"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))

        sql = convert_sql("""
            SELECT
                mk.benutzer_id,
                b.vorname || ' ' || b.name as mitglied_name,
                b.email,
                mk.saldo
            FROM mitglieder_konten mk
            JOIN benutzer b ON mk.benutzer_id = b.id
            WHERE mk.gemeinschaft_id = ?
            ORDER BY mk.saldo ASC
        """)
        cursor.execute(sql, (gemeinschaft_id,))

        columns = [desc[0] for desc in cursor.description]
        konten = [dict(zip(columns, row)) for row in cursor.fetchall()]

        sql = convert_sql("""
            SELECT
                SUM(CASE WHEN saldo > 0 THEN saldo ELSE 0 END) as guthaben,
                SUM(CASE WHEN saldo < 0 THEN saldo ELSE 0 END) as schulden,
                SUM(saldo) as saldo_gesamt
            FROM mitglieder_konten
            WHERE gemeinschaft_id = ?
        """)
        cursor.execute(sql, (gemeinschaft_id,))

        stat_row = cursor.fetchone()
        statistik = {
            'guthaben': stat_row[0] or 0,
            'schulden': stat_row[1] or 0,
            'saldo_gesamt': stat_row[2] or 0
        }

        sql = convert_sql("""
            SELECT
                bu.datum,
                b.vorname || ' ' || b.name as mitglied_name,
                bu.typ,
                bu.beschreibung,
                bu.betrag
            FROM buchungen bu
            JOIN benutzer b ON bu.benutzer_id = b.id
            WHERE bu.gemeinschaft_id = ?
            ORDER BY bu.erstellt_am DESC
            LIMIT 20
        """)
        cursor.execute(sql, (gemeinschaft_id,))

        columns = [desc[0] for desc in cursor.description]
        letzte_buchungen = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('admin_konten.html',
                         gemeinschaft=gemeinschaft,
                         konten=konten,
                         statistik=statistik,
                         letzte_buchungen=letzte_buchungen)


@admin_finanzen_bp.route('/gemeinschaften/<int:gemeinschaft_id>/konten/buchung-neu', methods=['GET', 'POST'])
@admin_required
def admin_konten_buchung_neu(gemeinschaft_id):
    """Neue manuelle Buchung erstellen"""
    benutzer_id = session.get('benutzer_id')
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))

        if request.method == 'POST':
            mitglied_id = request.form['benutzer_id']
            typ = request.form['typ']
            betrag_input = float(request.form['betrag'])
            datum = request.form['datum']
            beschreibung = request.form['beschreibung']

            if typ == 'einzahlung':
                betrag = betrag_input
            elif typ == 'auszahlung':
                betrag = -betrag_input
            elif typ == 'korrektur':
                betrag = betrag_input
            else:
                flash('Ungültiger Buchungstyp!', 'danger')
                return redirect(url_for('admin_finanzen.admin_konten_buchung_neu',
                                       gemeinschaft_id=gemeinschaft_id))

            sql = convert_sql("""
                INSERT INTO buchungen (
                    benutzer_id, gemeinschaft_id, datum, betrag,
                    typ, beschreibung, referenz_typ, erstellt_von
                ) VALUES (?, ?, ?, ?, ?, ?, 'manually', ?)
            """)
            cursor.execute(sql, (mitglied_id, gemeinschaft_id, datum, betrag,
                                typ, beschreibung, benutzer_id))

            sql = convert_sql("""
                INSERT INTO mitglieder_konten (benutzer_id, gemeinschaft_id, saldo)
                VALUES (?, ?, ?)
                ON CONFLICT(benutzer_id, gemeinschaft_id)
                DO UPDATE SET
                    saldo = saldo + ?,
                    letzte_aktualisierung = CURRENT_TIMESTAMP
            """)
            cursor.execute(sql, (mitglied_id, gemeinschaft_id, betrag, betrag))

            db.connection.commit()

            flash(f'Buchung erfolgreich erstellt: {betrag:,.2f} €', 'success')
            return redirect(url_for('admin_finanzen.admin_konten', gemeinschaft_id=gemeinschaft_id))

        sql = convert_sql("""
            SELECT
                b.id,
                b.vorname || ' ' || b.name as name,
                COALESCE(mk.saldo, 0) as saldo
            FROM benutzer b
            JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
            LEFT JOIN mitglieder_konten mk ON b.id = mk.benutzer_id
                AND mk.gemeinschaft_id = mg.gemeinschaft_id
            WHERE mg.gemeinschaft_id = ?
            ORDER BY b.name
        """)
        cursor.execute(sql, (gemeinschaft_id,))

        columns = [desc[0] for desc in cursor.description]
        mitglieder = [dict(zip(columns, row)) for row in cursor.fetchall()]

        heute = datetime.now().strftime('%Y-%m-%d')

    return render_template('admin_konten_buchung_neu.html',
                         gemeinschaft=gemeinschaft,
                         mitglieder=mitglieder,
                         heute=heute)


@admin_finanzen_bp.route('/gemeinschaften/<int:gemeinschaft_id>/konten/detail/<int:benutzer_id>')
@admin_required
def admin_konten_detail(gemeinschaft_id, benutzer_id):
    """Kontodetail für ein Mitglied"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))

        sql = convert_sql("SELECT * FROM benutzer WHERE id = ?")
        cursor.execute(sql, (benutzer_id,))
        columns = [desc[0] for desc in cursor.description]
        mitglied = dict(zip(columns, cursor.fetchone()))

        sql = convert_sql("""
            SELECT * FROM mitglieder_konten
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
        """)
        cursor.execute(sql, (benutzer_id, gemeinschaft_id))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            konto = dict(zip(columns, row))
        else:
            konto = {'saldo': 0}

        sql = convert_sql("""
            SELECT * FROM buchungen
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
            ORDER BY datum DESC, id DESC
        """)
        cursor.execute(sql, (benutzer_id, gemeinschaft_id))
        columns = [desc[0] for desc in cursor.description]
        buchungen = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('admin_konten_detail.html',
                         gemeinschaft=gemeinschaft,
                         mitglied=mitglied,
                         konto=konto,
                         buchungen=buchungen)


@admin_finanzen_bp.route('/abrechnungen')
@admin_required
def admin_abrechnungen():
    """Abrechnungen-Übersicht"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Gemeinschaften des Admins laden
        if session.get('admin_level', 0) >= 2:
            # Hauptadmin sieht alle Gemeinschaften
            sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true")
            cursor.execute(sql)
        else:
            # Gemeinschafts-Admin sieht nur seine Gemeinschaften
            sql = convert_sql("""
                SELECT g.id, g.name
                FROM gemeinschaften g
                JOIN gemeinschafts_admin ga ON g.id = ga.gemeinschaft_id
                WHERE ga.benutzer_id = ? AND g.aktiv = true
            """)
            cursor.execute(sql, (session['benutzer_id'],))

        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

        # Statistiken
        statistiken = {}
        for gem in gemeinschaften:
            sql = convert_sql("""
                SELECT
                    COUNT(*) as anzahl_offen,
                    COALESCE(SUM(betrag_gesamt), 0) as summe_offen
                FROM mitglieder_abrechnungen
                WHERE gemeinschaft_id = ? AND status = 'offen'
            """)
            cursor.execute(sql, (gem['id'],))

            row = cursor.fetchone()
            statistiken[gem['id']] = {
                'anzahl_offen': row[0],
                'summe_offen': row[1]
            }

    return render_template('admin_abrechnungen.html',
                         gemeinschaften=gemeinschaften,
                         statistiken=statistiken)


@admin_finanzen_bp.route('/gemeinschaften/<int:gemeinschaft_id>/konten/zahlung/<int:benutzer_id>', methods=['GET', 'POST'])
@admin_required
def admin_konten_zahlung(gemeinschaft_id, benutzer_id):
    """Zahlung für offene Abrechnungen verbuchen"""
    admin_id = session.get('benutzer_id')
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))

        sql = convert_sql("SELECT * FROM benutzer WHERE id = ?")
        cursor.execute(sql, (benutzer_id,))
        columns = [desc[0] for desc in cursor.description]
        mitglied = dict(zip(columns, cursor.fetchone()))

        if request.method == 'POST':
            betrag = float(request.form['betrag'])
            datum = request.form['datum']
            beschreibung = request.form.get('beschreibung', f'Zahlung von {mitglied["vorname"]} {mitglied["name"]}')

            sql = convert_sql("""
                INSERT INTO buchungen (
                    benutzer_id, gemeinschaft_id, datum, betrag,
                    typ, beschreibung, referenz_typ, erstellt_von
                ) VALUES (?, ?, ?, ?, 'einzahlung', ?, 'zahlung', ?)
            """)
            cursor.execute(sql, (benutzer_id, gemeinschaft_id, datum, betrag, beschreibung, admin_id))

            sql = convert_sql("""
                INSERT INTO mitglieder_konten (benutzer_id, gemeinschaft_id, saldo)
                VALUES (?, ?, ?)
                ON CONFLICT(benutzer_id, gemeinschaft_id)
                DO UPDATE SET
                    saldo = saldo + ?,
                    letzte_aktualisierung = CURRENT_TIMESTAMP
            """)
            cursor.execute(sql, (benutzer_id, gemeinschaft_id, betrag, betrag))

            sql = convert_sql("""
                SELECT id, betrag_gesamt
                FROM mitglieder_abrechnungen
                WHERE benutzer_id = ?
                AND gemeinschaft_id = ?
                AND status = 'offen'
                ORDER BY zeitraum_bis
            """)
            cursor.execute(sql, (benutzer_id, gemeinschaft_id))

            offene_abrechnungen = cursor.fetchall()
            verbleibend = betrag

            for abr_id, abr_betrag in offene_abrechnungen:
                if verbleibend >= abr_betrag:
                    sql = convert_sql("""
                        UPDATE mitglieder_abrechnungen
                        SET status = 'bezahlt'
                        WHERE id = ?
                    """)
                    cursor.execute(sql, (abr_id,))
                    verbleibend -= abr_betrag
                else:
                    break

            db.connection.commit()

            flash(f'Zahlung von {betrag:,.2f} € erfolgreich verbucht!', 'success')
            return redirect(url_for('admin_finanzen.admin_konten', gemeinschaft_id=gemeinschaft_id))

        sql = convert_sql("""
            SELECT id, zeitraum_von, zeitraum_bis, betrag_gesamt, erstellt_am
            FROM mitglieder_abrechnungen
            WHERE benutzer_id = ? AND gemeinschaft_id = ? AND status = 'offen'
            ORDER BY zeitraum_bis DESC
        """)
        cursor.execute(sql, (benutzer_id, gemeinschaft_id))

        columns = [desc[0] for desc in cursor.description]
        offene_abrechnungen = [dict(zip(columns, row)) for row in cursor.fetchall()]

        sql = convert_sql("""
            SELECT COALESCE(saldo, 0)
            FROM mitglieder_konten
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
        """)
        cursor.execute(sql, (benutzer_id, gemeinschaft_id))
        saldo_row = cursor.fetchone()
        saldo = saldo_row[0] if saldo_row else 0

        heute = datetime.now().strftime('%Y-%m-%d')

    return render_template('admin_konten_zahlung.html',
                         gemeinschaft=gemeinschaft,
                         mitglied=mitglied,
                         offene_abrechnungen=offene_abrechnungen,
                         saldo=saldo,
                         heute=heute)


@admin_finanzen_bp.route('/abrechnungen/<int:gemeinschaft_id>/erstellen', methods=['GET', 'POST'])
@admin_required
def abrechnungen_erstellen(gemeinschaft_id):
    """Erstellt Abrechnungen für alle Mitglieder einer Gemeinschaft"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        if session.get('admin_level', 0) < 2:
            sql = convert_sql("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """)
            cursor.execute(sql, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung!', 'danger')
                return redirect(url_for('admin_finanzen.admin_abrechnungen'))

        if request.method == 'POST':
            zeitraum_von = request.form.get('zeitraum_von')
            zeitraum_bis = request.form.get('zeitraum_bis')

            if not zeitraum_von or not zeitraum_bis:
                flash('Bitte beide Datumsfelder ausfüllen!', 'warning')
                return redirect(request.url)

            von_obj = datetime.strptime(zeitraum_von, '%Y-%m-%d')
            bis_obj = datetime.strptime(zeitraum_bis, '%Y-%m-%d')
            abrechnungszeitraum = f"{von_obj.strftime('%m/%Y')} - {bis_obj.strftime('%m/%Y')}"

            sql = convert_sql("""
                SELECT DISTINCT b.id, b.name, b.vorname
                FROM benutzer b
                JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
                WHERE mg.gemeinschaft_id = ?
                ORDER BY b.name
            """)
            cursor.execute(sql, (gemeinschaft_id,))
            mitglieder = cursor.fetchall()

            erstellt = 0
            uebersprungen = 0

            for mitglied in mitglieder:
                mitglied_benutzer_id = mitglied[0]

                sql = convert_sql("""
                    SELECT COUNT(*) FROM mitglieder_abrechnungen
                    WHERE gemeinschaft_id = ? AND benutzer_id = ?
                    AND zeitraum_von = ? AND zeitraum_bis = ?
                """)
                cursor.execute(sql, (gemeinschaft_id, mitglied_benutzer_id, zeitraum_von, zeitraum_bis))

                if cursor.fetchone()[0] > 0:
                    uebersprungen += 1
                    continue

                sql = convert_sql("""
                    SELECT COALESCE(SUM(me.kosten_berechnet), 0)
                    FROM maschineneinsaetze me
                    JOIN maschinen m ON me.maschine_id = m.id
                    WHERE me.benutzer_id = ?
                    AND me.datum BETWEEN ? AND ?
                    AND m.gemeinschaft_id = ?
                """)
                cursor.execute(sql, (mitglied_benutzer_id, zeitraum_von, zeitraum_bis, gemeinschaft_id))
                betrag_maschinen = cursor.fetchone()[0]

                sql = convert_sql("""
                    SELECT COALESCE(SUM(me.treibstoffkosten), 0)
                    FROM maschineneinsaetze me
                    JOIN maschinen m ON me.maschine_id = m.id
                    WHERE me.benutzer_id = ?
                    AND me.datum BETWEEN ? AND ?
                    AND m.treibstoff_berechnen = 1
                    AND m.gemeinschaft_id = ?
                """)
                cursor.execute(sql, (mitglied_benutzer_id, zeitraum_von, zeitraum_bis, gemeinschaft_id))
                betrag_treibstoff = cursor.fetchone()[0]

                betrag_gesamt = betrag_maschinen + betrag_treibstoff

                if betrag_gesamt > 0:
                    sql = convert_sql("""
                        INSERT INTO mitglieder_abrechnungen
                        (gemeinschaft_id, benutzer_id, abrechnungszeitraum,
                         zeitraum_von, zeitraum_bis, betrag_gesamt,
                         betrag_treibstoff, betrag_maschinen, betrag_sonstiges,
                         status, erstellt_von)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'offen', ?)
                    """)
                    cursor.execute(sql, (gemeinschaft_id, mitglied_benutzer_id, abrechnungszeitraum,
                                        zeitraum_von, zeitraum_bis, betrag_gesamt,
                                        betrag_treibstoff, betrag_maschinen, session['benutzer_id']))

                    abrechnung_id = cursor.lastrowid

                    sql = convert_sql("""
                        INSERT INTO buchungen (
                            benutzer_id, gemeinschaft_id, datum, betrag,
                            typ, beschreibung, referenz_typ, referenz_id, erstellt_von
                        ) VALUES (?, ?, ?, ?, 'abrechnung', ?, 'abrechnung', ?, ?)
                    """)
                    cursor.execute(sql, (
                        mitglied_benutzer_id, gemeinschaft_id, zeitraum_bis,
                        -betrag_gesamt,
                        f'Abrechnung #{abrechnung_id} für {abrechnungszeitraum}',
                        abrechnung_id, session['benutzer_id']
                    ))

                    sql = convert_sql("""
                        INSERT INTO mitglieder_konten (benutzer_id, gemeinschaft_id, saldo, saldo_vorjahr)
                        VALUES (?, ?, ?, 0)
                        ON CONFLICT(benutzer_id, gemeinschaft_id)
                        DO UPDATE SET
                            saldo = saldo + ?,
                            letzte_aktualisierung = CURRENT_TIMESTAMP
                    """)
                    cursor.execute(sql, (mitglied_benutzer_id, gemeinschaft_id, -betrag_gesamt, -betrag_gesamt))

                    erstellt += 1

            db.connection.commit()

            if erstellt > 0:
                flash(f'{erstellt} Abrechnung(en) erfolgreich erstellt', 'success')
            if uebersprungen > 0:
                flash(f'{uebersprungen} Abrechnung(en) bereits vorhanden (übersprungen)', 'info')
            if erstellt == 0 and uebersprungen == 0:
                flash(f'Keine Maschineneinsätze im Zeitraum {zeitraum_von} bis {zeitraum_bis} gefunden.', 'warning')

            return redirect(url_for('admin_finanzen.abrechnungen_liste', gemeinschaft_id=gemeinschaft_id))

        sql = convert_sql("SELECT name FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        gemeinschaft_name = cursor.fetchone()[0]

        heute = datetime.now()
        jahr = heute.year
        aktueller_monat = heute.month

        vorschlag_von = f"{jahr}-{aktueller_monat:02d}-01"

        if aktueller_monat in [1, 3, 5, 7, 8, 10, 12]:
            letzter_tag = 31
        elif aktueller_monat in [4, 6, 9, 11]:
            letzter_tag = 30
        else:
            if jahr % 4 == 0 and (jahr % 100 != 0 or jahr % 400 == 0):
                letzter_tag = 29
            else:
                letzter_tag = 28

        vorschlag_bis = f"{jahr}-{aktueller_monat:02d}-{letzter_tag}"

        sql = convert_sql("""
            SELECT MIN(datum) as erster_einsatz, MAX(datum) as letzter_einsatz, COUNT(*) as anzahl_einsaetze
            FROM maschineneinsaetze me
            JOIN mitglied_gemeinschaft mg ON me.benutzer_id = mg.mitglied_id
            WHERE mg.gemeinschaft_id = ?
        """)
        cursor.execute(sql, (gemeinschaft_id,))
        stats = cursor.fetchone()
        einsatz_info = {
            'erster': stats[0],
            'letzter': stats[1],
            'anzahl': stats[2]
        }

    return render_template('abrechnungen_erstellen.html',
                         gemeinschaft_id=gemeinschaft_id,
                         gemeinschaft_name=gemeinschaft_name,
                         vorschlag_von=vorschlag_von,
                         vorschlag_bis=vorschlag_bis,
                         einsatz_info=einsatz_info)


@admin_finanzen_bp.route('/abrechnungen/<int:gemeinschaft_id>/liste')
@admin_required
def abrechnungen_liste(gemeinschaft_id):
    """Liste aller Abrechnungen einer Gemeinschaft"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        if session.get('admin_level', 0) < 2:
            sql = convert_sql("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """)
            cursor.execute(sql, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung!', 'danger')
                return redirect(url_for('admin_finanzen.admin_abrechnungen'))

        sql = convert_sql("""
            SELECT
                ma.id, ma.zeitraum_von, ma.zeitraum_bis,
                ma.betrag_maschinen, ma.betrag_treibstoff, ma.betrag_gesamt,
                ma.status, ma.erstellt_am, ma.bezahlt_am, ma.benutzer_id,
                b.name, b.vorname, b.email
            FROM mitglieder_abrechnungen ma
            JOIN benutzer b ON ma.benutzer_id = b.id
            WHERE ma.gemeinschaft_id = ?
            ORDER BY ma.erstellt_am DESC
        """)
        cursor.execute(sql, (gemeinschaft_id,))

        abrechnungen = []
        summe_maschinen = 0
        summe_treibstoff = 0

        for row in cursor.fetchall():
            betrag_maschinen = row[3] or 0
            betrag_treibstoff = row[4] or 0
            abr_benutzer_id = row[9]

            sql = convert_sql("""
                SELECT datum, betrag, beschreibung, typ
                FROM buchungen
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
                AND typ = 'einzahlung' AND datum >= ?
                ORDER BY datum DESC
                LIMIT 5
            """)
            cursor.execute(sql, (abr_benutzer_id, gemeinschaft_id, row[1]))

            zahlungen = []
            for z in cursor.fetchall():
                zahlungen.append({
                    'datum': z[0],
                    'betrag': z[1],
                    'beschreibung': z[2],
                    'typ': z[3]
                })

            abrechnungen.append({
                'id': row[0],
                'zeitraum_von': row[1],
                'zeitraum_bis': row[2],
                'betrag_maschinen': betrag_maschinen,
                'betrag_treibstoff': betrag_treibstoff,
                'betrag_gesamt': row[5],
                'status': row[6],
                'erstellt_am': row[7],
                'bezahlt_am': row[8],
                'mitglied_name': f"{row[11] or ''} {row[10]}".strip(),
                'mitglied_email': row[12],
                'zahlungen': zahlungen
            })

            summe_maschinen += betrag_maschinen
            summe_treibstoff += betrag_treibstoff

        sql = convert_sql("SELECT name FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        gemeinschaft_name = cursor.fetchone()[0]

    return render_template('abrechnungen_liste.html',
                         gemeinschaft_id=gemeinschaft_id,
                         gemeinschaft_name=gemeinschaft_name,
                         abrechnungen=abrechnungen,
                         summe_maschinen=summe_maschinen,
                         summe_treibstoff=summe_treibstoff)


@admin_finanzen_bp.route('/abrechnungen/<int:gemeinschaft_id>/csv-import', methods=['GET', 'POST'])
@admin_required
def admin_csv_import(gemeinschaft_id):
    """CSV-Import für Banktransaktionen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        if session.get('admin_level', 0) < 2:
            sql = convert_sql("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """)
            cursor.execute(sql, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung für diese Gemeinschaft!', 'danger')
                return redirect(url_for('admin_finanzen.admin_abrechnungen'))

        sql = convert_sql("SELECT * FROM csv_import_konfiguration WHERE gemeinschaft_id = ?")
        cursor.execute(sql, (gemeinschaft_id,))

        result = cursor.fetchone()
        if result:
            columns = [desc[0] for desc in cursor.description]
            config = dict(zip(columns, result))
        else:
            sql = convert_sql("INSERT INTO csv_import_konfiguration (gemeinschaft_id) VALUES (?)")
            cursor.execute(sql, (gemeinschaft_id,))
            db.connection.commit()
            return redirect(request.url)

        sql = convert_sql("SELECT name FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        gemeinschaft_name = cursor.fetchone()[0]

    return render_template('admin_csv_import.html',
                         gemeinschaft_id=gemeinschaft_id,
                         gemeinschaft_name=gemeinschaft_name,
                         config=config)


@admin_finanzen_bp.route('/abrechnungen/<int:gemeinschaft_id>/csv-konfiguration', methods=['GET', 'POST'])
@admin_required
def admin_csv_konfiguration(gemeinschaft_id):
    """CSV-Import-Format konfigurieren"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        if session.get('admin_level', 0) < 2:
            sql = convert_sql("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """)
            cursor.execute(sql, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung für diese Gemeinschaft!', 'danger')
                return redirect(url_for('admin_finanzen.admin_abrechnungen'))

        if request.method == 'POST':
            sql = convert_sql("""
                UPDATE csv_import_konfiguration
                SET trennzeichen = ?, kodierung = ?,
                    spalte_buchungsdatum = ?, spalte_valutadatum = ?,
                    spalte_betrag = ?, spalte_verwendungszweck = ?,
                    spalte_empfaenger = ?, spalte_kontonummer = ?,
                    spalte_bic = ?, dezimaltrennzeichen = ?,
                    tausendertrennzeichen = ?, datumsformat = ?,
                    hat_kopfzeile = ?, zeilen_ueberspringen = ?
                WHERE gemeinschaft_id = ?
            """)
            cursor.execute(sql, (
                request.form.get('trennzeichen'),
                request.form.get('kodierung'),
                request.form.get('spalte_buchungsdatum'),
                request.form.get('spalte_valutadatum'),
                request.form.get('spalte_betrag'),
                request.form.get('spalte_verwendungszweck'),
                request.form.get('spalte_empfaenger'),
                request.form.get('spalte_kontonummer'),
                request.form.get('spalte_bic'),
                request.form.get('dezimaltrennzeichen'),
                request.form.get('tausendertrennzeichen'),
                request.form.get('datumsformat'),
                1 if request.form.get('hat_kopfzeile') else 0,
                int(request.form.get('zeilen_ueberspringen', 0)),
                gemeinschaft_id
            ))

            db.connection.commit()
            flash('CSV-Konfiguration gespeichert!', 'success')
            return redirect(url_for('admin_finanzen.admin_csv_import', gemeinschaft_id=gemeinschaft_id))

        sql = convert_sql("SELECT * FROM csv_import_konfiguration WHERE gemeinschaft_id = ?")
        cursor.execute(sql, (gemeinschaft_id,))

        result = cursor.fetchone()
        if result:
            columns = [desc[0] for desc in cursor.description]
            config = dict(zip(columns, result))
        else:
            sql = convert_sql("INSERT INTO csv_import_konfiguration (gemeinschaft_id) VALUES (?)")
            cursor.execute(sql, (gemeinschaft_id,))
            db.connection.commit()
            return redirect(request.url)

        sql = convert_sql("SELECT name FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        gemeinschaft_name = cursor.fetchone()[0]

    return render_template('admin_csv_konfiguration.html',
                         gemeinschaft_id=gemeinschaft_id,
                         gemeinschaft_name=gemeinschaft_name,
                         config=config)


@admin_finanzen_bp.route('/abrechnungen/<int:gemeinschaft_id>/transaktionen')
@admin_required
def admin_transaktionen(gemeinschaft_id):
    """Übersicht aller Transaktionen einer Gemeinschaft"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        if session.get('admin_level', 0) < 2:
            sql = convert_sql("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """)
            cursor.execute(sql, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung für diese Gemeinschaft!', 'danger')
                return redirect(url_for('admin_finanzen.admin_abrechnungen'))

        filter_typ = request.args.get('typ', 'alle')

        query = convert_sql("""
            SELECT t.*, b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name,
                   m.bezeichnung as maschine_name, g.name as gemeinschaft_name
            FROM bank_transaktionen t
            LEFT JOIN benutzer b ON t.benutzer_id = b.id
            LEFT JOIN maschinen m ON t.zuordnung_typ = 'maschine' AND t.zuordnung_id = m.id
            JOIN gemeinschaften g ON t.gemeinschaft_id = g.id
            WHERE t.gemeinschaft_id = ?
        """)

        params = [gemeinschaft_id]

        if filter_typ == 'eingaenge':
            query = query.rstrip() + " AND t.betrag > 0"
        elif filter_typ == 'ausgaenge':
            query = query.rstrip() + " AND t.betrag < 0"
        elif filter_typ == 'unzugeordnet':
            query = query.rstrip() + " AND (t.zugeordnet = 0 OR t.zugeordnet IS NULL)"

        query = query + " ORDER BY t.buchungsdatum DESC, t.id DESC LIMIT 500"

        cursor.execute(query, params)

        columns = [desc[0] for desc in cursor.description]
        transaktionen = [dict(zip(columns, row)) for row in cursor.fetchall()]

        sql = convert_sql("""
            SELECT
                COUNT(*) as anzahl_gesamt,
                COUNT(CASE WHEN zugeordnet = 1 THEN 1 END) as anzahl_zugeordnet,
                COALESCE(SUM(betrag), 0) as summe_gesamt,
                COALESCE(SUM(CASE WHEN zugeordnet = 1 THEN betrag ELSE 0 END), 0) as summe_zugeordnet,
                COALESCE(SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END), 0) as summe_eingaenge,
                COALESCE(SUM(CASE WHEN betrag < 0 THEN betrag ELSE 0 END), 0) as summe_ausgaenge,
                COUNT(CASE WHEN betrag > 0 AND zugeordnet = 0 THEN 1 END) as unzugeordnete_eingaenge,
                COUNT(CASE WHEN betrag < 0 AND zugeordnet = 0 THEN 1 END) as unzugeordnete_ausgaenge
            FROM bank_transaktionen
            WHERE gemeinschaft_id = ?
        """)
        cursor.execute(sql, (gemeinschaft_id,))

        row = cursor.fetchone()

        sql = convert_sql("SELECT anfangssaldo_bank, anfangssaldo_datum FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        saldo_row = cursor.fetchone()
        anfangssaldo = saldo_row[0] if saldo_row else 0.0
        anfangssaldo_datum = saldo_row[1] if saldo_row else None

        statistik = {
            'anzahl_gesamt': row[0],
            'anzahl_zugeordnet': row[1],
            'summe_gesamt': row[2],
            'summe_zugeordnet': row[3],
            'summe_eingaenge': row[4],
            'summe_ausgaenge': row[5],
            'unzugeordnete_eingaenge': row[6],
            'unzugeordnete_ausgaenge': row[7],
            'anfangssaldo': anfangssaldo,
            'anfangssaldo_datum': anfangssaldo_datum,
            'aktueller_saldo': anfangssaldo + row[2]
        }

        sql = convert_sql("SELECT name FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        gemeinschaft_name = cursor.fetchone()[0]

        sql = convert_sql("""
            SELECT DISTINCT b.id, b.name, b.vorname
            FROM benutzer b
            JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
            WHERE mg.gemeinschaft_id = ?
            ORDER BY b.name, b.vorname
        """)
        cursor.execute(sql, (gemeinschaft_id,))
        benutzer = [{'id': row[0], 'name': f"{row[1]} {row[2] or ''}"} for row in cursor.fetchall()]

        sql = convert_sql("SELECT id, bezeichnung FROM maschinen WHERE gemeinschaft_id = ? ORDER BY bezeichnung")
        cursor.execute(sql, (gemeinschaft_id,))
        maschinen = [{'id': row[0], 'bezeichnung': row[1]} for row in cursor.fetchall()]

        sql = convert_sql("""
            SELECT date(importiert_am) as import_datum, importiert_von, COUNT(*) as anzahl,
                   b.name || ' ' || COALESCE(b.vorname, '') as importiert_von_name
            FROM bank_transaktionen t
            LEFT JOIN benutzer b ON t.importiert_von = b.id
            WHERE t.gemeinschaft_id = ?
            GROUP BY date(importiert_am), importiert_von
            ORDER BY importiert_am DESC
        """)
        cursor.execute(sql, (gemeinschaft_id,))

        imports = []
        for row in cursor.fetchall():
            imports.append({
                'datum': row[0],
                'importiert_von_id': row[1],
                'anzahl': row[2],
                'importiert_von_name': row[3] or 'Unbekannt'
            })

    return render_template('admin_transaktionen.html',
                         gemeinschaft_id=gemeinschaft_id,
                         transaktionen=transaktionen,
                         statistik=statistik,
                         filter_typ=filter_typ,
                         benutzer=benutzer,
                         maschinen=maschinen,
                         imports=imports)


@admin_finanzen_bp.route('/transaktion/<int:transaktion_id>/zuordnen', methods=['POST'])
@admin_required
def transaktion_zuordnen(transaktion_id):
    """Ordnet eine Transaktion einem Benutzer, einer Maschine oder Gemeinschaftskosten zu"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT gemeinschaft_id, betrag FROM bank_transaktionen WHERE id = ?")
        cursor.execute(sql, (transaktion_id,))
        result = cursor.fetchone()
        if not result:
            flash('Transaktion nicht gefunden!', 'danger')
            return redirect(url_for('admin_finanzen.admin_abrechnungen'))

        gemeinschaft_id, betrag = result

        if session.get('admin_level', 0) < 2:
            sql = convert_sql("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """)
            cursor.execute(sql, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung!', 'danger')
                return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))

        zuordnung_typ = request.form.get('zuordnung_typ')

        if betrag > 0:
            zuordnen_benutzer_id = request.form.get('benutzer_id')
            if not zuordnen_benutzer_id:
                flash('Bitte Benutzer auswählen!', 'warning')
                return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))

            sql = convert_sql("""
                UPDATE bank_transaktionen
                SET benutzer_id = ?, zugeordnet = 1,
                    zuordnung_typ = 'benutzer', zuordnung_id = ?
                WHERE id = ?
            """)
            cursor.execute(sql, (zuordnen_benutzer_id, zuordnen_benutzer_id, transaktion_id))

            db.connection.commit()
            flash('Eingang dem Benutzer zugeordnet', 'success')

        else:
            if zuordnung_typ == 'maschine':
                maschine_id = request.form.get('maschine_id')
                if not maschine_id:
                    flash('Bitte Maschine auswählen!', 'warning')
                    return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))

                beschreibung = request.form.get('beschreibung', '')

                sql = convert_sql("""
                    INSERT INTO gemeinschafts_kosten
                    (gemeinschaft_id, transaktion_id, maschine_id, kategorie, betrag, datum, beschreibung, erstellt_von)
                    VALUES (?, ?, ?, 'maschine', ?, date('now'), ?, ?)
                """)
                cursor.execute(sql, (gemeinschaft_id, transaktion_id, maschine_id, abs(betrag), beschreibung, session['benutzer_id']))

                sql = convert_sql("""
                    UPDATE bank_transaktionen
                    SET zugeordnet = 1, zuordnung_typ = 'maschine', zuordnung_id = ?
                    WHERE id = ?
                """)
                cursor.execute(sql, (maschine_id, transaktion_id))

                db.connection.commit()
                flash('Ausgang der Maschine zugeordnet', 'success')

            elif zuordnung_typ == 'gemeinschaft':
                kategorie = request.form.get('kategorie', 'sonstiges')
                beschreibung = request.form.get('beschreibung', '')

                sql = convert_sql("""
                    INSERT INTO gemeinschafts_kosten
                    (gemeinschaft_id, transaktion_id, kategorie, betrag, datum, beschreibung, erstellt_von)
                    VALUES (?, ?, ?, ?, date('now'), ?, ?)
                """)
                cursor.execute(sql, (gemeinschaft_id, transaktion_id, kategorie, abs(betrag), beschreibung, session['benutzer_id']))

                sql = convert_sql("""
                    UPDATE bank_transaktionen
                    SET zugeordnet = 1, zuordnung_typ = 'gemeinschaft', zuordnung_id = NULL
                    WHERE id = ?
                """)
                cursor.execute(sql, (transaktion_id,))

                db.connection.commit()
                flash('Ausgang als Gemeinschaftskosten verbucht', 'success')

    return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))


@admin_finanzen_bp.route('/transaktion/<int:transaktion_id>/zuordnung-aufheben', methods=['POST'])
@admin_required
def transaktion_zuordnung_aufheben(transaktion_id):
    """Hebt die Zuordnung einer Transaktion auf"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT gemeinschaft_id, zuordnung_typ, zuordnung_id FROM bank_transaktionen WHERE id = ?")
        cursor.execute(sql, (transaktion_id,))
        result = cursor.fetchone()
        if not result:
            flash('Transaktion nicht gefunden!', 'danger')
            return redirect(url_for('admin_finanzen.admin_abrechnungen'))

        gemeinschaft_id, zuordnung_typ, zuordnung_id = result

        if session.get('admin_level', 0) < 2:
            sql = convert_sql("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """)
            cursor.execute(sql, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung!', 'danger')
                return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))

        sql = convert_sql("""
            UPDATE bank_transaktionen
            SET zugeordnet = 0, zuordnung_typ = NULL, zuordnung_id = NULL, benutzer_id = NULL
            WHERE id = ?
        """)
        cursor.execute(sql, (transaktion_id,))

        if zuordnung_typ in ['maschine', 'gemeinschaft']:
            sql = convert_sql("DELETE FROM gemeinschafts_kosten WHERE transaktion_id = ?")
            cursor.execute(sql, (transaktion_id,))

        db.connection.commit()
        flash('Zuordnung aufgehoben', 'info')

    return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))


@admin_finanzen_bp.route('/transaktion/<int:transaktion_id>/loeschen', methods=['POST'])
@admin_required
def transaktion_loeschen(transaktion_id):
    """Löscht eine einzelne Transaktion"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT gemeinschaft_id, zuordnung_typ FROM bank_transaktionen WHERE id = ?")
        cursor.execute(sql, (transaktion_id,))
        result = cursor.fetchone()
        if not result:
            flash('Transaktion nicht gefunden!', 'danger')
            return redirect(url_for('admin_finanzen.admin_abrechnungen'))

        gemeinschaft_id, zuordnung_typ = result

        if session.get('admin_level', 0) < 2:
            sql = convert_sql("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """)
            cursor.execute(sql, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung!', 'danger')
                return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))

        if zuordnung_typ in ['maschine', 'gemeinschaft']:
            sql = convert_sql("DELETE FROM gemeinschafts_kosten WHERE transaktion_id = ?")
            cursor.execute(sql, (transaktion_id,))

        sql = convert_sql("DELETE FROM bank_transaktionen WHERE id = ?")
        cursor.execute(sql, (transaktion_id,))

        db.connection.commit()
        flash('Transaktion gelöscht', 'success')

    return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))


@admin_finanzen_bp.route('/abrechnungen/<int:gemeinschaft_id>/import-loeschen', methods=['POST'])
@admin_required
def import_loeschen(gemeinschaft_id):
    """Löscht alle Transaktionen eines bestimmten Imports"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        if session.get('admin_level', 0) < 2:
            sql = convert_sql("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """)
            cursor.execute(sql, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung für diese Gemeinschaft!', 'danger')
                return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))

        import_datum = request.form.get('import_datum')
        importiert_von = request.form.get('importiert_von')

        if not import_datum or not importiert_von:
            flash('Fehlende Parameter!', 'danger')
            return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))

        sql = convert_sql("""
            SELECT COUNT(*) FROM bank_transaktionen
            WHERE gemeinschaft_id = ? AND date(importiert_am) = ? AND importiert_von = ?
        """)
        cursor.execute(sql, (gemeinschaft_id, import_datum, importiert_von))
        anzahl = cursor.fetchone()[0]

        if anzahl == 0:
            flash('Keine Transaktionen zum Löschen gefunden!', 'warning')
            return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))

        sql = convert_sql("""
            SELECT id FROM bank_transaktionen
            WHERE gemeinschaft_id = ? AND date(importiert_am) = ? AND importiert_von = ?
        """)
        cursor.execute(sql, (gemeinschaft_id, import_datum, importiert_von))
        trans_ids = [row[0] for row in cursor.fetchall()]

        if trans_ids:
            placeholders = ','.join(['?' for _ in trans_ids])
            sql = f"DELETE FROM gemeinschafts_kosten WHERE transaktion_id IN ({placeholders})"
            cursor.execute(sql, trans_ids)

        sql = convert_sql("""
            DELETE FROM bank_transaktionen
            WHERE gemeinschaft_id = ? AND date(importiert_am) = ? AND importiert_von = ?
        """)
        cursor.execute(sql, (gemeinschaft_id, import_datum, importiert_von))

        db.connection.commit()
        flash(f'{anzahl} Transaktionen des Imports vom {import_datum} gelöscht', 'success')

    return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))


@admin_finanzen_bp.route('/abrechnungen/<int:gemeinschaft_id>/anfangssaldo', methods=['GET', 'POST'])
@admin_required
def anfangssaldo_bearbeiten(gemeinschaft_id):
    """Anfangssaldo für Gemeinschaft eingeben/bearbeiten"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        if session.get('admin_level', 0) < 2:
            sql = convert_sql("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """)
            cursor.execute(sql, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung!', 'danger')
                return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))

        if request.method == 'POST':
            anfangssaldo = request.form.get('anfangssaldo', '0')
            anfangssaldo_datum = request.form.get('anfangssaldo_datum', None)

            try:
                anfangssaldo = float(anfangssaldo.replace(',', '.'))
            except ValueError:
                flash('Ungültiger Betrag!', 'danger')
                return redirect(request.url)

            sql = convert_sql("""
                UPDATE gemeinschaften
                SET anfangssaldo_bank = ?, anfangssaldo_datum = ?
                WHERE id = ?
            """)
            cursor.execute(sql, (anfangssaldo, anfangssaldo_datum, gemeinschaft_id))

            db.connection.commit()
            flash(f'Anfangssaldo auf {anfangssaldo:.2f} € gesetzt', 'success')
            return redirect(url_for('admin_finanzen.admin_transaktionen', gemeinschaft_id=gemeinschaft_id))

        sql = convert_sql("SELECT name, anfangssaldo_bank, anfangssaldo_datum FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        row = cursor.fetchone()

        gemeinschaft = {
            'id': gemeinschaft_id,
            'name': row[0],
            'anfangssaldo': row[1] or 0.0,
            'anfangssaldo_datum': row[2]
        }

    return render_template('anfangssaldo_bearbeiten.html', gemeinschaft=gemeinschaft)
