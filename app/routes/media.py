import os
from flask import Blueprint, redirect, url_for, flash, request, send_from_directory, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models.media import Medium
from app.models.inventar import Ding

media_bp = Blueprint('media', __name__)

ERLAUBTE_ENDUNGEN = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}


def erlaubte_datei(dateiname):
    return '.' in dateiname and dateiname.rsplit('.', 1)[1].lower() in ERLAUBTE_ENDUNGEN


@media_bp.route('/upload/<int:ding_id>', methods=['POST'])
def upload(ding_id):
    ding = Ding.query.get_or_404(ding_id)
    typ = request.form.get('typ', 'foto')
    beschreibung = request.form.get('beschreibung') or None

    # Datei-Upload
    datei = request.files.get('datei')
    if datei and datei.filename and erlaubte_datei(datei.filename):
        dateiname = secure_filename(datei.filename)
        ordner = os.path.join(current_app.config['UPLOAD_FOLDER'], str(ding_id))
        os.makedirs(ordner, exist_ok=True)
        # Bei gleichem Dateinamen: Nummer anhängen
        basis, endung = os.path.splitext(dateiname)
        zähler = 1
        while os.path.exists(os.path.join(ordner, dateiname)):
            dateiname = f'{basis}_{zähler}{endung}'
            zähler += 1
        datei.save(os.path.join(ordner, dateiname))
        medium = Medium(
            ding_id=ding_id,
            typ=typ,
            dateiname=dateiname,
            pfad=os.path.join(str(ding_id), dateiname),
            beschreibung=beschreibung
        )
        db.session.add(medium)
        db.session.commit()
        flash('Datei hochgeladen.', 'success')

    # Externer Link
    elif request.form.get('url'):
        medium = Medium(
            ding_id=ding_id,
            typ=typ,
            url=request.form['url'],
            beschreibung=beschreibung
        )
        db.session.add(medium)
        db.session.commit()
        flash('Link gespeichert.', 'success')

    else:
        flash('Keine Datei oder URL angegeben.', 'warning')

    return redirect(url_for('ding.detail', id=ding_id))


@media_bp.route('/datei/<int:medium_id>')
def datei(medium_id):
    medium = Medium.query.get_or_404(medium_id)
    if not medium.pfad:
        flash('Keine lokale Datei vorhanden.', 'warning')
        return redirect(url_for('ding.detail', id=medium.ding_id))
    ordner = os.path.abspath(os.path.join(current_app.config['UPLOAD_FOLDER'], str(medium.ding_id)))
    return send_from_directory(ordner, medium.dateiname)


@media_bp.route('/loeschen/<int:medium_id>', methods=['POST'])
def loeschen(medium_id):
    medium = Medium.query.get_or_404(medium_id)
    ding_id = medium.ding_id
    # Datei vom Dateisystem löschen
    if medium.pfad:
        pfad = os.path.join(current_app.config['UPLOAD_FOLDER'], medium.pfad)
        if os.path.exists(pfad):
            os.remove(pfad)
    db.session.delete(medium)
    db.session.commit()
    flash('Medium gelöscht.', 'warning')
    return redirect(url_for('ding.detail', id=ding_id))
