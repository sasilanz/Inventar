from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models.inventar import Kategorie, Tag

stammdaten_bp = Blueprint('stammdaten', __name__)


# ── Kategorien ─────────────────────────────────────────────────────────────

@stammdaten_bp.route('/kategorien')
def kategorie_liste():
    kategorien = Kategorie.query.order_by(Kategorie.name).all()
    return render_template('stammdaten/kategorie_liste.html', kategorien=kategorien)


@stammdaten_bp.route('/kategorien/neu', methods=['GET', 'POST'])
def kategorie_neu():
    if request.method == 'POST':
        kat = Kategorie(
            name=request.form['name'].strip(),
            beschreibung=request.form.get('beschreibung') or None
        )
        db.session.add(kat)
        db.session.commit()
        flash('Kategorie gespeichert.', 'success')
        return redirect(url_for('stammdaten.kategorie_liste'))
    return render_template('stammdaten/kategorie_formular.html', kategorie=None)


@stammdaten_bp.route('/kategorien/<int:id>/bearbeiten', methods=['GET', 'POST'])
def kategorie_bearbeiten(id):
    kat = Kategorie.query.get_or_404(id)
    if request.method == 'POST':
        kat.name = request.form['name'].strip()
        kat.beschreibung = request.form.get('beschreibung') or None
        db.session.commit()
        flash('Kategorie aktualisiert.', 'success')
        return redirect(url_for('stammdaten.kategorie_liste'))
    return render_template('stammdaten/kategorie_formular.html', kategorie=kat)


@stammdaten_bp.route('/kategorien/<int:id>/loeschen', methods=['POST'])
def kategorie_loeschen(id):
    kat = Kategorie.query.get_or_404(id)
    db.session.delete(kat)
    db.session.commit()
    flash(f'Kategorie „{kat.name}" gelöscht.', 'warning')
    return redirect(url_for('stammdaten.kategorie_liste'))


# ── Tags ───────────────────────────────────────────────────────────────────

@stammdaten_bp.route('/tags')
def tag_liste():
    tags = Tag.query.order_by(Tag.name).all()
    return render_template('stammdaten/tag_liste.html', tags=tags)


@stammdaten_bp.route('/tags/neu', methods=['GET', 'POST'])
def tag_neu():
    if request.method == 'POST':
        tag = Tag(name=request.form['name'].strip())
        db.session.add(tag)
        db.session.commit()
        flash('Tag gespeichert.', 'success')
        return redirect(url_for('stammdaten.tag_liste'))
    return render_template('stammdaten/tag_formular.html', tag=None)


@stammdaten_bp.route('/tags/<int:id>/bearbeiten', methods=['GET', 'POST'])
def tag_bearbeiten(id):
    tag = Tag.query.get_or_404(id)
    if request.method == 'POST':
        tag.name = request.form['name'].strip()
        db.session.commit()
        flash('Tag aktualisiert.', 'success')
        return redirect(url_for('stammdaten.tag_liste'))
    return render_template('stammdaten/tag_formular.html', tag=tag)


@stammdaten_bp.route('/tags/<int:id>/loeschen', methods=['POST'])
def tag_loeschen(id):
    tag = Tag.query.get_or_404(id)
    db.session.delete(tag)
    db.session.commit()
    flash(f'Tag „{tag.name}" gelöscht.', 'warning')
    return redirect(url_for('stammdaten.tag_liste'))
