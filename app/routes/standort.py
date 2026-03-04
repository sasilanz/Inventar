from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models.standort import Zone, Raum, Gestell, Regalfach, Behaelter
from app.models.tracking import Bewegung

standort_bp = Blueprint('standort', __name__)


# ── Übersicht ──────────────────────────────────────────────────────────────
@standort_bp.route('/')
def index():
    return render_template('standort/index.html',
                            zonen=Zone.query.order_by(Zone.name).all(),
                            raeume=Raum.query.count(),
                            gestelle=Gestell.query.count(),
                            regalfaecher=Regalfach.query.count(),
                            behaelter=Behaelter.query.count())


# ── Zone ───────────────────────────────────────────────────────────────────
@standort_bp.route('/zonen')
def zone_liste():
    zonen = Zone.query.order_by(Zone.name).all()
    return render_template('standort/zone_liste.html', zonen=zonen)


@standort_bp.route('/zonen/neu', methods=['GET', 'POST'])
def zone_neu():
    if request.method == 'POST':
        zone = Zone(
            name=request.form['name'].strip(),
            beschreibung=request.form.get('beschreibung') or None
        )
        db.session.add(zone)
        db.session.commit()
        flash('Zone gespeichert.', 'success')
        return redirect(url_for('standort.zone_liste'))
    return render_template('standort/zone_formular.html', zone=None)


@standort_bp.route('/zonen/<int:id>/bearbeiten', methods=['GET', 'POST'])
def zone_bearbeiten(id):
    zone = Zone.query.get_or_404(id)
    if request.method == 'POST':
        zone.name = request.form['name'].strip()
        zone.beschreibung = request.form.get('beschreibung') or None
        db.session.commit()
        flash('Zone aktualisiert.', 'success')
        return redirect(url_for('standort.zone_liste'))
    return render_template('standort/zone_formular.html', zone=zone)


@standort_bp.route('/zonen/<int:id>/loeschen', methods=['POST'])
def zone_loeschen(id):
    zone = Zone.query.get_or_404(id)
    db.session.delete(zone)
    db.session.commit()
    flash(f'Zone „{zone.name}" gelöscht.', 'warning')
    return redirect(url_for('standort.zone_liste'))


# ── Raum ───────────────────────────────────────────────────────────────────
@standort_bp.route('/raeume')
def raum_liste():
    zonen = Zone.query.order_by(Zone.name).all()
    return render_template('standort/raum_liste.html', zonen=zonen)


@standort_bp.route('/raeume/neu', methods=['GET', 'POST'])
def raum_neu():
    zonen = Zone.query.order_by(Zone.name).all()
    if request.method == 'POST':
        raum = Raum(
            zone_id=request.form['zone_id'],
            name=request.form['name'].strip(),
            beschreibung=request.form.get('beschreibung') or None
        )
        db.session.add(raum)
        db.session.commit()
        flash('Raum gespeichert.', 'success')
        return redirect(url_for('standort.raum_liste'))
    return render_template('standort/raum_formular.html', raum=None, zonen=zonen)


@standort_bp.route('/raeume/<int:id>/bearbeiten', methods=['GET', 'POST'])
def raum_bearbeiten(id):
    raum = Raum.query.get_or_404(id)
    zonen = Zone.query.order_by(Zone.name).all()
    if request.method == 'POST':
        raum.zone_id = request.form['zone_id']
        raum.name = request.form['name'].strip()
        raum.beschreibung = request.form.get('beschreibung') or None
        db.session.commit()
        flash('Raum aktualisiert.', 'success')
        return redirect(url_for('standort.raum_liste'))
    return render_template('standort/raum_formular.html', raum=raum, zonen=zonen)


@standort_bp.route('/raeume/<int:id>/loeschen', methods=['POST'])
def raum_loeschen(id):
    raum = Raum.query.get_or_404(id)
    db.session.delete(raum)
    db.session.commit()
    flash(f'Raum „{raum.name}" gelöscht.', 'warning')
    return redirect(url_for('standort.raum_liste'))


# ── Gestell ────────────────────────────────────────────────────────────────
@standort_bp.route('/gestelle')
def gestell_liste():
    gestelle = Gestell.query.join(Raum).order_by(Raum.name, Gestell.name).all()
    zonen = Zone.query.order_by(Zone.name).all()
    raeume = Raum.query.join(Zone).order_by(Zone.name, Raum.name).all()
    return render_template('standort/gestell_liste.html', gestelle=gestelle, zonen=zonen, raeume=raeume)


@standort_bp.route('/gestelle/neu', methods=['GET', 'POST'])
def gestell_neu():
    raeume = Raum.query.join(Zone).order_by(Zone.name, Raum.name).all()
    prefill_raum_id = request.args.get('raum_id', type=int)
    if request.method == 'POST':
        gestell = Gestell(
            raum_id=request.form['raum_id'],
            typ=request.form.get('typ') or None,
            name=request.form['name'].strip(),
            beschreibung=request.form.get('beschreibung') or None
        )
        db.session.add(gestell)
        db.session.flush()
        db.session.add(Bewegung(gestell_id=gestell.id, von_beschreibung=None,
                                nach_beschreibung=gestell.standort_beschreibung()))
        db.session.commit()
        flash('Gestell gespeichert.', 'success')
        next_url = request.form.get('next')
        return redirect(next_url or url_for('standort.gestell_liste'))
    return render_template('standort/gestell_formular.html', gestell=None, raeume=raeume,
                           prefill_raum_id=prefill_raum_id,
                           next_url=request.args.get('next', ''))


@standort_bp.route('/gestelle/<int:id>/bearbeiten', methods=['GET', 'POST'])
def gestell_bearbeiten(id):
    gestell = Gestell.query.get_or_404(id)
    raeume = Raum.query.join(Zone).order_by(Zone.name, Raum.name).all()
    if request.method == 'POST':
        von = gestell.standort_beschreibung()
        gestell.raum_id = request.form['raum_id']
        gestell.typ = request.form.get('typ') or None
        gestell.name = request.form['name'].strip()
        gestell.beschreibung = request.form.get('beschreibung') or None
        db.session.flush()
        nach = gestell.standort_beschreibung()
        if von != nach:
            db.session.add(Bewegung(gestell_id=gestell.id, von_beschreibung=von, nach_beschreibung=nach))
        db.session.commit()
        flash('Gestell aktualisiert.', 'success')
        next_url = request.form.get('next')
        return redirect(next_url or url_for('standort.gestell_liste'))
    return render_template('standort/gestell_formular.html', gestell=gestell, raeume=raeume,
                           next_url=request.args.get('next', ''))


@standort_bp.route('/gestelle/<int:id>/loeschen', methods=['POST'])
def gestell_loeschen(id):
    gestell = Gestell.query.get_or_404(id)
    next_url = request.form.get('next') or url_for('standort.gestell_liste')
    if gestell.regalfaecher or gestell.behaelter or gestell.dinge:
        flash(f'Gestell „{gestell.name}" kann nicht gelöscht werden – enthält noch Einträge.', 'danger')
    else:
        name = gestell.name
        db.session.delete(gestell)
        db.session.commit()
        flash(f'Gestell „{name}" gelöscht.', 'warning')
    return redirect(next_url)


# ── Regalfach ──────────────────────────────────────────────────────────────
@standort_bp.route('/regalfaecher')
def regalfach_liste():
    regalfaecher = Regalfach.query.join(Gestell).order_by(
        Gestell.name, Regalfach.position_index).all()
    return render_template('standort/regalfach_liste.html', regalfaecher=regalfaecher)


@standort_bp.route('/regalfaecher/neu', methods=['GET', 'POST'])
def regalfach_neu():
    gestelle = Gestell.query.join(Raum).order_by(Raum.name, Gestell.name).all()
    prefill_gestell_id = request.args.get('gestell_id', type=int)
    if request.method == 'POST':
        fach = Regalfach(
            gestell_id=request.form['gestell_id'],
            bezeichnung=request.form['bezeichnung'].strip(),
            position_index=request.form.get('position_index') or 0
        )
        db.session.add(fach)
        db.session.commit()
        flash('Regalfach gespeichert.', 'success')
        next_url = request.form.get('next')
        return redirect(next_url or url_for('standort.regalfach_liste'))
    return render_template('standort/regalfach_formular.html', fach=None, gestelle=gestelle,
                           prefill_gestell_id=prefill_gestell_id,
                           next_url=request.args.get('next', ''))


@standort_bp.route('/regalfaecher/<int:id>/bearbeiten', methods=['GET', 'POST'])
def regalfach_bearbeiten(id):
    fach = Regalfach.query.get_or_404(id)
    gestelle = Gestell.query.join(Raum).order_by(Raum.name, Gestell.name).all()
    if request.method == 'POST':
        fach.gestell_id = request.form['gestell_id']
        fach.bezeichnung = request.form['bezeichnung'].strip()
        fach.position_index = request.form.get('position_index') or 0
        db.session.commit()
        flash('Regalfach aktualisiert.', 'success')
        next_url = request.form.get('next')
        return redirect(next_url or url_for('standort.regalfach_liste'))
    return render_template('standort/regalfach_formular.html', fach=fach, gestelle=gestelle,
                           next_url=request.args.get('next', ''))


@standort_bp.route('/regalfaecher/<int:id>/loeschen', methods=['POST'])
def regalfach_loeschen(id):
    fach = Regalfach.query.get_or_404(id)
    next_url = request.form.get('next') or url_for('standort.regalfach_liste')
    if fach.behaelter or fach.dinge:
        flash(f'Regalfach „{fach.bezeichnung}" kann nicht gelöscht werden – enthält noch Einträge.', 'danger')
    else:
        bezeichnung = fach.bezeichnung
        db.session.delete(fach)
        db.session.commit()
        flash(f'Regalfach „{bezeichnung}" gelöscht.', 'warning')
    return redirect(next_url)


# ── Behälter ───────────────────────────────────────────────────────────────
@standort_bp.route('/behaelter')
def behaelter_liste():
    behaelter = Behaelter.query.order_by(Behaelter.name).all()
    zonen = Zone.query.order_by(Zone.name).all()
    raeume = Raum.query.join(Zone).order_by(Zone.name, Raum.name).all()
    gestelle = Gestell.query.join(Raum).order_by(Raum.name, Gestell.name).all()
    return render_template('standort/behaelter_liste.html', behaelter=behaelter,
                           zonen=zonen, raeume=raeume, gestelle=gestelle)


@standort_bp.route('/behaelter/neu', methods=['GET', 'POST'])
def behaelter_neu():
    raeume = Raum.query.join(Zone).order_by(Zone.name, Raum.name).all()
    gestelle = Gestell.query.join(Raum).order_by(Raum.name, Gestell.name).all()
    regalfaecher = Regalfach.query.join(Gestell).order_by(Gestell.name, Regalfach.position_index).all()
    if request.method == 'POST':
        behaelter = Behaelter(
            typ=request.form.get('typ') or None,
            name=request.form['name'].strip(),
            beschreibung=request.form.get('beschreibung') or None,
            regalfach_id=request.form.get('regalfach_id') or None,
            gestell_id=request.form.get('gestell_id') or None,
            raum_id=request.form.get('raum_id') or None
        )
        db.session.add(behaelter)
        db.session.flush()
        nach = behaelter.standort_beschreibung()
        if nach != 'Kein Standort':
            db.session.add(Bewegung(behaelter_id=behaelter.id, von_beschreibung=None, nach_beschreibung=nach))
        db.session.commit()
        flash('Behälter gespeichert.', 'success')
        next_url = request.form.get('next')
        return redirect(next_url or url_for('standort.behaelter_liste'))
    prefill_gestell_id = request.args.get('gestell_id', type=int)
    prefill_regalfach_id = request.args.get('regalfach_id', type=int)
    return render_template('standort/behaelter_formular.html',
                            behaelter=None, raeume=raeume, gestelle=gestelle, regalfaecher=regalfaecher,
                            prefill_gestell_id=prefill_gestell_id,
                            prefill_regalfach_id=prefill_regalfach_id,
                            next_url=request.args.get('next', ''))


@standort_bp.route('/behaelter/<int:id>/bearbeiten', methods=['GET', 'POST'])
def behaelter_bearbeiten(id):
    behaelter = Behaelter.query.get_or_404(id)
    raeume = Raum.query.join(Zone).order_by(Zone.name, Raum.name).all()
    gestelle = Gestell.query.join(Raum).order_by(Raum.name, Gestell.name).all()
    regalfaecher = Regalfach.query.join(Gestell).order_by(Gestell.name, Regalfach.position_index).all()
    if request.method == 'POST':
        von = behaelter.standort_beschreibung()
        behaelter.typ = request.form.get('typ') or None
        behaelter.name = request.form['name'].strip()
        behaelter.beschreibung = request.form.get('beschreibung') or None
        behaelter.regalfach_id = request.form.get('regalfach_id') or None
        behaelter.gestell_id = request.form.get('gestell_id') or None
        behaelter.raum_id = request.form.get('raum_id') or None
        db.session.flush()
        nach = behaelter.standort_beschreibung()
        if von != nach:
            db.session.add(Bewegung(behaelter_id=behaelter.id, von_beschreibung=von, nach_beschreibung=nach))
        db.session.commit()
        flash('Behälter aktualisiert.', 'success')
        next_url = request.form.get('next')
        return redirect(next_url or url_for('standort.behaelter_liste'))
    return render_template('standort/behaelter_formular.html',
                            behaelter=behaelter, raeume=raeume, gestelle=gestelle, regalfaecher=regalfaecher,
                            next_url=request.args.get('next', ''))


@standort_bp.route('/behaelter/<int:id>/loeschen', methods=['POST'])
def behaelter_loeschen(id):
    behaelter = Behaelter.query.get_or_404(id)
    next_url = request.form.get('next') or url_for('standort.behaelter_liste')
    if behaelter.dinge:
        flash(f'Behälter „{behaelter.name}" kann nicht gelöscht werden – enthält noch Dinge.', 'danger')
    else:
        name = behaelter.name
        db.session.delete(behaelter)
        db.session.commit()
        flash(f'Behälter „{name}" gelöscht.', 'warning')
    return redirect(next_url)


# ── Detail-/Inhaltsseiten ──────────────────────────────────────────────────

@standort_bp.route('/behaelter/<int:id>')
def behaelter_detail(id):
    behaelter = Behaelter.query.get_or_404(id)
    return render_template('standort/behaelter_detail.html', behaelter=behaelter)


@standort_bp.route('/gestelle/<int:id>')
def gestell_detail(id):
    gestell = Gestell.query.get_or_404(id)
    return render_template('standort/gestell_detail.html', gestell=gestell)


@standort_bp.route('/regalfach/<int:id>')
def regalfach_detail(id):
    fach = Regalfach.query.get_or_404(id)
    return render_template('standort/regalfach_detail.html', fach=fach)


@standort_bp.route('/raum/<int:id>')
def raum_detail(id):
    raum = Raum.query.get_or_404(id)
    return render_template('standort/raum_detail.html', raum=raum)
