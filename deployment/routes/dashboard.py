# -*- coding: utf-8 -*-
"""
Dashboard und Index-Routen
"""

from flask import Blueprint, render_template, redirect, url_for, session
from database import MaschinenDBContext
from utils.decorators import login_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

dashboard_bp = Blueprint('dashboard', __name__)


def archiviere_abgelaufene_reservierungen():
    """Verschiebt abgelaufene Reservierungen in die Archiv-Tabelle"""
    try:
        db_path = get_current_db_path()
        with MaschinenDBContext(db_path) as db:
            cursor = db.connection.cursor()

            # Finde alle abgelaufenen Reservierungen
            sql = convert_sql("""
                SELECT r.*, m.bezeichnung as maschine_bezeichnung,
                       b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name
                FROM maschinen_reservierungen r
                JOIN maschinen m ON r.maschine_id = m.id
                JOIN benutzer b ON r.benutzer_id = b.id
                WHERE r.status = 'aktiv'
                AND datetime(r.datum || ' ' || r.uhrzeit_bis) < datetime('now', 'localtime')
            """)
            cursor.execute(sql)

            abgelaufene = cursor.fetchall()

            if abgelaufene:
                columns = [desc[0] for desc in cursor.description]

                for row in abgelaufene:
                    reservierung = dict(zip(columns, row))

                    # In Archiv-Tabelle kopieren
                    sql = convert_sql("""
                        INSERT INTO reservierungen_abgelaufen
                        (reservierung_id, maschine_id, maschine_bezeichnung, benutzer_id,
                         benutzer_name, datum, uhrzeit_von, uhrzeit_bis, nutzungsdauer_stunden,
                         zweck, bemerkung, erstellt_am)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """)
                    cursor.execute(sql, (
                        reservierung['id'], reservierung['maschine_id'],
                        reservierung['maschine_bezeichnung'], reservierung['benutzer_id'],
                        reservierung['benutzer_name'], reservierung['datum'],
                        reservierung['uhrzeit_von'], reservierung['uhrzeit_bis'],
                        reservierung.get('nutzungsdauer_stunden'), reservierung.get('zweck'),
                        reservierung.get('bemerkung'), reservierung['erstellt_am']
                    ))

                    # Status auf 'abgelaufen' setzen
                    sql = convert_sql("""
                        UPDATE maschinen_reservierungen
                        SET status = 'abgelaufen', geaendert_am = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """)
                    cursor.execute(sql, (reservierung['id'],))

                db.connection.commit()
                return len(abgelaufene)

            return 0

    except Exception as e:
        print(f"Fehler beim Archivieren abgelaufener Reservierungen: {e}")
        return 0


@dashboard_bp.route('/')
def index():
    """Startseite - Weiterleitung"""
    archiviere_abgelaufene_reservierungen()

    if 'benutzer_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - Übersicht für den Benutzer"""
    archiviere_abgelaufene_reservierungen()

    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        benutzer_id = session['benutzer_id']

        # Statistiken laden
        statistik = db.get_statistik_benutzer(benutzer_id)

        # Gesamtkosten berechnen
        treibstoffkosten = statistik.get('gesamt_kosten', 0) or 0
        maschinenkosten = statistik.get('gesamt_maschinenkosten', 0) or 0
        statistik['gesamtkosten'] = treibstoffkosten + maschinenkosten

        # Letzte Einsätze
        einsaetze = db.get_einsaetze_by_benutzer(benutzer_id)
        letzte_einsaetze = einsaetze[:10] if einsaetze else []

        # Schulden nach Gemeinschaft
        cursor = db.connection.cursor()
        sql = convert_sql("""
            SELECT
                g.id,
                g.name,
                COUNT(e.id) as anzahl_einsaetze,
                SUM(
                    CASE
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as maschinenkosten
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            JOIN gemeinschaften g ON m.gemeinschaft_id = g.id
            WHERE e.benutzer_id = ?
            GROUP BY g.id, g.name
            ORDER BY g.name
        """)
        cursor.execute(sql, (benutzer_id,))

        columns = [desc[0] for desc in cursor.description]
        schulden_nach_gemeinschaft = []
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            d['bezeichnung'] = d['name']
            d['gesamtkosten'] = d['maschinenkosten'] or 0
            schulden_nach_gemeinschaft.append(d)

        # Meine aktiven Reservierungen laden
        sql = convert_sql("""
            SELECT r.*, m.bezeichnung as maschine_bezeichnung
            FROM maschinen_reservierungen r
            JOIN maschinen m ON r.maschine_id = m.id
            WHERE r.benutzer_id = ?
              AND r.datum >= date('now')
              AND r.status = 'aktiv'
            ORDER BY r.datum, r.uhrzeit_von
        """)
        cursor.execute(sql, (benutzer_id,))

        columns = [desc[0] for desc in cursor.description]
        reservierungen = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Ungelesene Nachrichten zählen (über Betrieb des Benutzers)
        sql = convert_sql("""
            SELECT COUNT(DISTINCT n.id) FROM gemeinschafts_nachrichten n
            JOIN betriebe_gemeinschaften bg ON n.gemeinschaft_id = bg.gemeinschaft_id
            JOIN benutzer u ON u.betrieb_id = bg.betrieb_id
            LEFT JOIN nachricht_gelesen ng ON n.id = ng.nachricht_id AND ng.benutzer_id = ?
            WHERE u.id = ? AND ng.nachricht_id IS NULL
        """)
        cursor.execute(sql, (benutzer_id, benutzer_id))

        ungelesene_nachrichten = cursor.fetchone()[0]

        # Zahlungsreferenzen des Benutzers laden
        sql = convert_sql("""
            SELECT z.*, g.name as gemeinschaft_name
            FROM zahlungsreferenzen z
            JOIN gemeinschaften g ON z.gemeinschaft_id = g.id
            WHERE z.benutzer_id = ? AND z.aktiv = true
            ORDER BY g.name
        """)
        cursor.execute(sql, (benutzer_id,))

        columns = [desc[0] for desc in cursor.description]
        zahlungsreferenzen = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('dashboard.html',
                         statistik=statistik,
                         einsaetze=letzte_einsaetze,
                         schulden_nach_gemeinschaft=schulden_nach_gemeinschaft,
                         reservierungen=reservierungen,
                         ungelesene_nachrichten=ungelesene_nachrichten,
                         zahlungsreferenzen=zahlungsreferenzen)
