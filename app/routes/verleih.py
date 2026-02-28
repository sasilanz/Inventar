from flask import Blueprint, redirect, url_for, flash, request, render_template
from app import db
from app.models.tracking import Verleih
from datetime import datetime, date

verleih_bp = Blueprint('verleih', __name__)


@verleih_bp.route('/')
def index():
    offen = (Verleih.query
             .filter_by(zurueck_am=None)
             .order_by(Verleih.ausgeliehen_am)
             .all())
    zurueck = (Verleih.query
               .filter(Verleih.zurueck_am != None)
               .order_by(Verleih.zurueck_am.desc())
               .limit(30)
               .all())
    return render_template('verleih/liste.html', offen=offen, zurueck=zurueck, today=date.today())


@verleih_bp.route('/neu/<int:ding_id>', methods=['POST'])
def neu(ding_id):
    ausgeliehen_am = request.form.get('ausgeliehen_am')
    faellig_am = request.form.get('faellig_am')
    verleih = Verleih(
        ding_id=ding_id,
        person=request.form['person'],
        ausgeliehen_am=datetime.strptime(ausgeliehen_am, '%Y-%m-%d').date() if ausgeliehen_am else datetime.utcnow().date(),
        faellig_am=datetime.strptime(faellig_am, '%Y-%m-%d').date() if faellig_am else None,
        notiz=request.form.get('notiz') or None
    )
    db.session.add(verleih)
    db.session.commit()
    flash(f'Ausgeliehen an {verleih.person}.', 'success')
    return redirect(url_for('ding.detail', id=ding_id))


@verleih_bp.route('/<int:id>/zurueck', methods=['POST'])
def zurueck(id):
    verleih = Verleih.query.get_or_404(id)
    verleih.zurueck_am = datetime.utcnow().date()
    db.session.commit()
    flash('Rückgabe vermerkt.', 'success')
    return redirect(url_for('ding.detail', id=verleih.ding_id))
