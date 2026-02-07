# -*- coding: utf-8 -*-
"""
Admin - Gemeinschaften-Verwaltung
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import MaschinenDBContext
from utils.decorators import admin_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

admin_gemeinschaften_bp = Blueprint('admin_gemeinschaften', __name__, url_prefix='/admin')


@admin_gemeinschaften_bp.route('/gemeinschaften')
@admin_required
def admin_gemeinschaften():
    """Gemeinschaften verwalten"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        cursor = db.cursor
        sql = convert_sql("SELECT * FROM gemeinschaften_uebersicht ORDER BY name")
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        gemeinschaften = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return render_template('admin_gemeinschaften.html', gemeinschaften=gemeinschaften)


@admin_gemeinschaften_bp.route('/gemeinschaften/neu', methods=['GET', 'POST'])
@admin_required
def admin_gemeinschaften_neu():
    """Neue Gemeinschaft"""
    db_path = get_current_db_path()
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash('Name ist erforderlich!', 'danger')
            return redirect(url_for('admin_gemeinschaften.admin_gemeinschaften_neu'))

        with MaschinenDBContext(db_path) as db:
            cursor = db.cursor
            sql = convert_sql("""
                INSERT INTO gemeinschaften (name, beschreibung, aktiv)
                VALUES (?, ?, ?)
            """)
            cursor.execute(sql, (
                name,
                request.form.get('beschreibung'),
                bool(request.form.get('aktiv'))
            ))
            db.connection.commit()
        flash('Gemeinschaft erfolgreich angelegt!', 'success')
        return redirect(url_for('admin_gemeinschaften.admin_gemeinschaften'))
    return render_template('admin_gemeinschaften_form.html', gemeinschaft=None)


@admin_gemeinschaften_bp.route('/gemeinschaften/<int:gemeinschaft_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_gemeinschaften_edit(gemeinschaft_id):
    """Gemeinschaft bearbeiten"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        cursor = db.cursor

        if request.method == 'POST':
            name = request.form.get('name')
            if not name:
                flash('Name ist erforderlich!', 'danger')
                return redirect(url_for('admin_gemeinschaften.admin_gemeinschaften_edit', gemeinschaft_id=gemeinschaft_id))

            sql = convert_sql("""
                UPDATE gemeinschaften
                SET name = ?,
                    beschreibung = ?,
                    adresse = ?,
                    telefon = ?,
                    email = ?,
                    aktiv = ?,
                    bank_name = ?,
                    bank_iban = ?,
                    bank_bic = ?,
                    bank_kontoinhaber = ?
                WHERE id = ?
            """)
            cursor.execute(sql, (
                name,
                request.form.get('beschreibung'),
                request.form.get('adresse'),
                request.form.get('telefon'),
                request.form.get('email'),
                bool(request.form.get('aktiv')),
                request.form.get('bank_name'),
                request.form.get('bank_iban'),
                request.form.get('bank_bic'),
                request.form.get('bank_kontoinhaber'),
                gemeinschaft_id
            ))
            db.connection.commit()
            flash('Gemeinschaft erfolgreich aktualisiert!', 'success')
            return redirect(url_for('admin_gemeinschaften.admin_gemeinschaften'))

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))

    return render_template('admin_gemeinschaften_form.html', gemeinschaft=gemeinschaft)


@admin_gemeinschaften_bp.route('/gemeinschaften/<int:gemeinschaft_id>/mitglieder', methods=['GET', 'POST'])
@admin_required
def admin_gemeinschaften_mitglieder(gemeinschaft_id):
    """Betriebe einer Gemeinschaft verwalten"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'hinzufuegen':
                betrieb_ids = request.form.getlist('betriebe')
                if not betrieb_ids:
                    flash('Bitte mindestens einen Betrieb auswählen!', 'error')
                else:
                    for betrieb_id in betrieb_ids:
                        sql = convert_sql("""
                            INSERT INTO betriebe_gemeinschaften (betrieb_id, gemeinschaft_id)
                            VALUES (?, ?)
                            ON CONFLICT DO NOTHING
                        """)
                        cursor.execute(sql, (int(betrieb_id), gemeinschaft_id))
                    db.connection.commit()
                    flash(f'{len(betrieb_ids)} Betrieb(e) hinzugefügt!', 'success')

            elif action == 'entfernen':
                entfernen_ids = request.form.getlist('entfernen')
                if not entfernen_ids:
                    flash('Bitte mindestens einen Betrieb auswählen!', 'error')
                else:
                    for betrieb_id in entfernen_ids:
                        sql = convert_sql("""
                            DELETE FROM betriebe_gemeinschaften
                            WHERE betrieb_id = ? AND gemeinschaft_id = ?
                        """)
                        cursor.execute(sql, (int(betrieb_id), gemeinschaft_id))
                    db.connection.commit()
                    flash(f'{len(entfernen_ids)} Betrieb(e) entfernt!', 'success')

            return redirect(url_for('admin_gemeinschaften.admin_gemeinschaften_mitglieder',
                                   gemeinschaft_id=gemeinschaft_id))

        # Zugewiesene Betriebe laden (mit benutzer_betriebe für Benutzeranzahl)
        sql = convert_sql("""
            SELECT b.*, bg.beigetreten_am,
                   (SELECT COUNT(*) FROM benutzer_betriebe WHERE betrieb_id = b.id) as anzahl_benutzer
            FROM betriebe b
            JOIN betriebe_gemeinschaften bg ON b.id = bg.betrieb_id
            WHERE bg.gemeinschaft_id = ?
            ORDER BY b.name
        """)
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        aktuelle_betriebe = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Verfügbare Betriebe (noch nicht zugewiesen, mit benutzer_betriebe für Benutzeranzahl)
        sql = convert_sql("""
            SELECT b.*,
                   (SELECT COUNT(*) FROM benutzer_betriebe WHERE betrieb_id = b.id) as anzahl_benutzer
            FROM betriebe b
            WHERE b.aktiv = true
            AND b.id NOT IN (
                SELECT betrieb_id FROM betriebe_gemeinschaften
                WHERE gemeinschaft_id = ?
            )
            ORDER BY b.name
        """)
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        verfuegbare_betriebe = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('admin_gemeinschaften_mitglieder.html',
                         gemeinschaft=gemeinschaft,
                         aktuelle_betriebe=aktuelle_betriebe,
                         verfuegbare_betriebe=verfuegbare_betriebe)


@admin_gemeinschaften_bp.route('/gemeinschaften/<int:gemeinschaft_id>/abrechnung')
@admin_required
def admin_gemeinschaften_abrechnung(gemeinschaft_id):
    """Abrechnungsübersicht einer Gemeinschaft"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))

        # Einsätze nach Betrieb (über benutzer_betriebe)
        sql = convert_sql("""
            SELECT
                bt.id,
                bt.name,
                COUNT(e.id) as anzahl_einsaetze,
                SUM(e.endstand - e.anfangstand) as betriebsstunden,
                SUM(
                    CASE
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as maschinenkosten,
                SUM(COALESCE(e.treibstoffkosten, 0)) as treibstoffkosten
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            JOIN benutzer_betriebe bb ON e.benutzer_id = bb.benutzer_id
            JOIN betriebe bt ON bb.betrieb_id = bt.id
            JOIN betriebe_gemeinschaften bg ON bt.id = bg.betrieb_id AND bg.gemeinschaft_id = ?
            WHERE m.gemeinschaft_id = ?
            GROUP BY bt.id, bt.name
            ORDER BY maschinenkosten DESC
        """)
        cursor.execute(sql, (gemeinschaft_id, gemeinschaft_id))
        columns = [desc[0] for desc in cursor.description]
        betriebe_abrechnung = [dict(zip(columns, row)) for row in cursor.fetchall()]

        for b in betriebe_abrechnung:
            b['gesamtkosten'] = (b['maschinenkosten'] or 0)

        # Gesamtsummen berechnen
        gesamtsummen = {
            'anzahl_einsaetze': sum(b.get('anzahl_einsaetze', 0) or 0 for b in betriebe_abrechnung),
            'betriebsstunden': sum(b.get('betriebsstunden', 0) or 0 for b in betriebe_abrechnung),
            'maschinenkosten': sum(b.get('maschinenkosten', 0) or 0 for b in betriebe_abrechnung),
            'treibstoffkosten': sum(b.get('treibstoffkosten', 0) or 0 for b in betriebe_abrechnung),
            'gesamtkosten': sum(b.get('gesamtkosten', 0) or 0 for b in betriebe_abrechnung)
        }

        # Admins der Gemeinschaft laden
        sql = convert_sql("""
            SELECT b.id, b.name, b.vorname, b.email
            FROM benutzer b
            JOIN gemeinschafts_admin ga ON b.id = ga.benutzer_id
            WHERE ga.gemeinschaft_id = ?
        """)
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        admins = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('admin_gemeinschaften_abrechnung.html',
                         gemeinschaft=gemeinschaft,
                         betriebe_abrechnung=betriebe_abrechnung,
                         gesamtsummen=gesamtsummen,
                         admins=admins)


@admin_gemeinschaften_bp.route('/gemeinschaften/<int:gemeinschaft_id>/abrechnung/csv')
@admin_required
def admin_gemeinschaften_abrechnung_csv(gemeinschaft_id):
    """CSV Export der Gemeinschafts-Abrechnung"""
    import csv
    from io import StringIO
    from datetime import datetime
    from flask import make_response

    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.cursor

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))

        sql = convert_sql("""
            SELECT
                b.id, b.name, b.vorname,
                COUNT(e.id) as anzahl_einsaetze,
                SUM(e.endstand - e.anfangstand) as betriebsstunden,
                SUM(
                    CASE
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as maschinenkosten
            FROM benutzer b
            JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
            LEFT JOIN maschineneinsaetze e ON b.id = e.benutzer_id
            LEFT JOIN maschinen m ON e.maschine_id = m.id AND m.gemeinschaft_id = ?
            WHERE mg.gemeinschaft_id = ?
            GROUP BY b.id, b.name, b.vorname
            ORDER BY b.name, b.vorname
        """)
        cursor.execute(sql, (gemeinschaft_id, gemeinschaft_id))

        rows = cursor.fetchall()

    output = StringIO()
    writer = csv.writer(output, delimiter=';')

    writer.writerow([f'Abrechnung: {gemeinschaft["name"]}'])
    writer.writerow([f'Erstellt am: {datetime.now().strftime("%d.%m.%Y %H:%M")}'])
    writer.writerow([])
    writer.writerow(['Name', 'Vorname', 'Anzahl Einsätze', 'Betriebsstunden', 'Maschinenkosten (EUR)'])

    gesamt_einsaetze = 0
    gesamt_stunden = 0
    gesamt_maschinenkosten = 0

    for row in rows:
        maschinenkosten = row[5] or 0
        writer.writerow([
            row[1], row[2], row[3] or 0,
            f"{row[4] or 0:.1f}", f"{maschinenkosten:.2f}"
        ])
        gesamt_einsaetze += row[3] or 0
        gesamt_stunden += row[4] or 0
        gesamt_maschinenkosten += maschinenkosten

    writer.writerow([])
    writer.writerow(['GESAMT', '', gesamt_einsaetze, f"{gesamt_stunden:.1f}", f"{gesamt_maschinenkosten:.2f}"])

    output.seek(0)
    response = make_response(output.getvalue().encode('utf-8-sig'))
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=Abrechnung_{gemeinschaft["name"]}_{datetime.now().strftime("%Y%m%d")}.csv'
    return response


@admin_gemeinschaften_bp.route('/gemeinschaften/<int:gemeinschaft_id>/maschinenuebersicht/pdf')
@admin_required
def admin_gemeinschaften_maschinenuebersicht_pdf(gemeinschaft_id):
    """PDF-Übersicht aller Maschinen einer Gemeinschaft"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from io import BytesIO
    import os
    from datetime import datetime

    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))

        sql = convert_sql("""
            SELECT m.*,
                (SELECT SUM(e.endstand - e.anfangstand) FROM maschineneinsaetze e WHERE e.maschine_id = m.id) as betriebsstunden,
                (SELECT SUM(CASE WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                                 ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0) END) FROM maschineneinsaetze e WHERE e.maschine_id = m.id) as einnahmen,
                (SELECT SUM(auf.wartungskosten + auf.reparaturkosten + auf.versicherung + auf.steuern + auf.sonstige_kosten) FROM maschinen_aufwendungen auf WHERE auf.maschine_id = m.id) as aufwendungen
            FROM maschinen m
            WHERE m.gemeinschaft_id = ?
            ORDER BY m.bezeichnung
        """)
        cursor.execute(sql, (gemeinschaft_id,))
        maschinen = cursor.fetchall()
        maschinen_columns = [desc[0] for desc in cursor.description]

    font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'fonts', 'DejaVuSans.ttf')
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        default_font = 'DejaVuSans'
    else:
        default_font = 'Helvetica'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = default_font

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=20, fontName=default_font)
    elements.append(Paragraph(f"Maschinenübersicht: {gemeinschaft['name']}", title_style))
    elements.append(Paragraph(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    table_data = [[
        'Bezeichnung', 'Hersteller', 'Modell', 'Baujahr', 'Betriebsstunden',
        'Einnahmen', 'Aufwendungen', 'Abschreibung (Jahr)', 'Deckungsbeitrag'
    ]]
    for row in maschinen:
        maschine = dict(zip(maschinen_columns, row))
        einnahmen = maschine.get('einnahmen') or 0
        aufwendungen = maschine.get('aufwendungen') or 0
        anschaffungspreis = maschine.get('anschaffungspreis') or 0
        abschreibungsdauer = maschine.get('abschreibungsdauer_jahre') or 10
        try:
            abschreibung_jahr = float(anschaffungspreis) / float(abschreibungsdauer) if abschreibungsdauer else 0
        except Exception:
            abschreibung_jahr = 0
        deckungsbeitrag = einnahmen - aufwendungen - abschreibung_jahr
        table_data.append([
            maschine.get('bezeichnung', '-'),
            maschine.get('hersteller', '-'),
            maschine.get('modell', '-'),
            maschine.get('baujahr', '-'),
            f"{maschine.get('betriebsstunden') or 0:.1f}",
            f"{einnahmen:.2f} €",
            f"{aufwendungen:.2f} €",
            f"{abschreibung_jahr:.2f} €",
            f"{deckungsbeitrag:.2f} €"
        ])

    table = Table(table_data, colWidths=[3.2*cm, 2.2*cm, 2.2*cm, 1.5*cm, 2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), default_font),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue(), 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': f'inline; filename="Maschinenuebersicht_{gemeinschaft["name"]}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    }
