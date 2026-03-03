from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models.standort import Raum, Gestell, Regalfach, Behaelter, Zone
from app.models.inventar import Kategorie, Tag, Ding
from app.models.tracking import Bewegung

ding_bp = Blueprint('ding', __name__)


@ding_bp.route('/')
def liste():
    q = request.args.get('q', '').strip()
    kategorie_id = request.args.get('kategorie_id', type=int)
    tag_id = request.args.get('tag_id', type=int)

    query = Ding.query
    if q:
        query = query.filter(Ding.name.ilike(f'%{q}%'))
    if kategorie_id:
        query = query.filter_by(kategorie_id=kategorie_id)
    if tag_id:
        query = query.filter(Ding.tags.any(id=tag_id))

    dinge = query.order_by(Ding.name).all()
    kategorien = Kategorie.query.order_by(Kategorie.name).all()
    tags = Tag.query.order_by(Tag.name).all()
    return render_template('ding/liste.html', dinge=dinge,
                           kategorien=kategorien, tags=tags,
                           q=q, kategorie_id=kategorie_id, tag_id=tag_id)


@ding_bp.route('/<int:id>')
def detail(id):
    ding = Ding.query.get_or_404(id)
    return render_template('ding/detail.html', ding=ding)


@ding_bp.route('/neu', methods=['GET', 'POST'])
def neu():
    if request.method == 'POST':
        ding = Ding(name=request.form['name'].strip())
        _ding_aus_formular(ding, request.form)
        db.session.add(ding)
        db.session.flush()
        nach = ding.standort_beschreibung()
        if nach != 'Kein Standort':
            db.session.add(Bewegung(ding_id=ding.id, von_beschreibung=None, nach_beschreibung=nach))
        db.session.commit()
        flash('Ding gespeichert.', 'success')
        return redirect(url_for('ding.detail', id=ding.id))
    return render_template('ding/formular.html', ding=None, **_formular_daten())


@ding_bp.route('/<int:id>/bearbeiten', methods=['GET', 'POST'])
def bearbeiten(id):
    ding = Ding.query.get_or_404(id)
    if request.method == 'POST':
        von = ding.standort_beschreibung()
        ding.name = request.form['name'].strip()
        _ding_aus_formular(ding, request.form)
        db.session.flush()
        nach = ding.standort_beschreibung()
        if von != nach:
            db.session.add(Bewegung(ding_id=ding.id, von_beschreibung=von, nach_beschreibung=nach))
        db.session.commit()
        flash('Ding aktualisiert.', 'success')
        return redirect(url_for('ding.detail', id=ding.id))
    return render_template('ding/formular.html', ding=ding, **_formular_daten())


@ding_bp.route('/<int:id>/loeschen', methods=['POST'])
def loeschen(id):
    ding = Ding.query.get_or_404(id)
    name = ding.name
    db.session.delete(ding)
    db.session.commit()
    flash(f'„{name}" gelöscht.', 'warning')
    return redirect(url_for('ding.liste'))


def _formular_daten():
    return dict(
        kategorien=Kategorie.query.order_by(Kategorie.name).all(),
        alle_tags=Tag.query.order_by(Tag.name).all(),
        raeume=Raum.query.join(Zone).order_by(Zone.name, Raum.name).all(),
        gestelle=Gestell.query.order_by(Gestell.name).all(),
        regalfaecher=Regalfach.query.all(),
        behaelter=Behaelter.query.order_by(Behaelter.name).all(),
    )


def _ding_aus_formular(ding, form):
    ding.beschreibung = form.get('beschreibung') or None
    ding.anzahl = int(form.get('anzahl') or 1)
    ding.hersteller = form.get('hersteller') or None
    ding.modell = form.get('modell') or None
    ding.seriennummer = form.get('seriennummer') or None
    ding.kategorie_id = form.get('kategorie_id') or None
    # Standort: genau eines setzen, Rest auf None
    ding.raum_id = form.get('raum_id') or None
    ding.gestell_id = form.get('gestell_id') or None
    ding.regalfach_id = form.get('regalfach_id') or None
    ding.behaelter_id = form.get('behaelter_id') or None
    # Versicherung
    ding.kaufdatum = form.get('kaufdatum') or None
    ding.kaufpreis = form.get('kaufpreis') or None
    ding.waehrung = form.get('waehrung') or 'CHF'
    ding.garantie_bis = form.get('garantie_bis') or None
    ding.versichert_bei = form.get('versichert_bei') or None
    ding.versicherungsnummer = form.get('versicherungsnummer') or None
    # Tags
    tag_ids = form.getlist('tag_ids')
    ding.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all() if tag_ids else []
