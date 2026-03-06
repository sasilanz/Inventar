from flask import Blueprint, render_template, redirect, url_for, flash, request, session
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
        ls = _standort_fuer_session(ding)
        session['last_standort'] = ls
        flash('Ding gespeichert.', 'success')
        if request.form.get('add_another'):
            params = {k: v for k, v in ls.items()}
            next_url = request.form.get('next')
            if next_url:
                params['next'] = next_url
            return redirect(url_for('ding.neu', **params))
        next_url = request.form.get('next')
        return redirect(next_url or url_for('ding.detail', id=ding.id))
    # URL-Params überschreiben Session-Prefill (z.B. aus Baumansicht)
    url_prefill = {k: request.args.get(k) for k in
                   ('behaelter_id', 'regalfach_id', 'gestell_id', 'raum_id')
                   if request.args.get(k)}
    prefill = url_prefill if url_prefill else session.get('last_standort', {})
    return render_template('ding/formular.html', ding=None, prefill=prefill,
                           next_url=request.args.get('next', ''), **_formular_daten())


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


def _standort_fuer_session(ding):
    """Ermittelt Zone/Raum/Standort-IDs für Session-Prefill beim nächsten Ding."""
    ls = {}
    if ding.behaelter_id:
        b = ding.behaelter
        eff_raum = b.raum or (b.gestell.raum if b.gestell else (b.regalfach.gestell.raum if b.regalfach else None))
        if eff_raum:
            ls['zone_id'] = str(eff_raum.zone_id)
            ls['raum_id'] = str(eff_raum.id)
        ls['behaelter_id'] = str(ding.behaelter_id)
    elif ding.gestell_id:
        ls['zone_id'] = str(ding.gestell.raum.zone_id)
        ls['raum_id'] = str(ding.gestell.raum_id)
        ls['gestell_id'] = str(ding.gestell_id)
    elif ding.regalfach_id:
        ls['zone_id'] = str(ding.regalfach.gestell.raum.zone_id)
        ls['raum_id'] = str(ding.regalfach.gestell.raum_id)
        ls['regalfach_id'] = str(ding.regalfach_id)
    elif ding.raum_id:
        ls['zone_id'] = str(ding.raum.zone_id)
        ls['raum_id'] = str(ding.raum_id)
    return ls


def _formular_daten():
    return dict(
        kategorien=Kategorie.query.order_by(Kategorie.name).all(),
        alle_tags=Tag.query.order_by(Tag.name).all(),
        zonen=Zone.query.order_by(Zone.name).all(),
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
    # Standort: genau eines setzen, Priorität: Behälter > Regalfach > Gestell > Raum
    behaelter_id = form.get('behaelter_id') or None
    regalfach_id = form.get('regalfach_id') or None
    gestell_id   = form.get('gestell_id') or None
    raum_id      = form.get('raum_id') or None
    if behaelter_id:
        ding.behaelter_id, ding.regalfach_id, ding.gestell_id, ding.raum_id = behaelter_id, None, None, None
    elif regalfach_id:
        ding.behaelter_id, ding.regalfach_id, ding.gestell_id, ding.raum_id = None, regalfach_id, None, None
    elif gestell_id:
        ding.behaelter_id, ding.regalfach_id, ding.gestell_id, ding.raum_id = None, None, gestell_id, None
    else:
        ding.behaelter_id, ding.regalfach_id, ding.gestell_id, ding.raum_id = None, None, None, raum_id
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
