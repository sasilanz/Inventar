import io
import qrcode
from flask import Blueprint, send_file, render_template, request
from app.models.inventar import Ding
from app.models.standort import Behaelter, Regalfach, Raum

qr_bp = Blueprint('qr', __name__)


def _make_qr(url):
    img = qrcode.QRCode(box_size=6, border=2)
    img.add_data(url)
    img.make(fit=True)
    bild = img.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    bild.save(buf, format='PNG')
    buf.seek(0)
    return buf


def _base(req):
    return req.host_url.rstrip('/')


# ── QR-Code-Bilder ─────────────────────────────────────────────────────────

@qr_bp.route('/ding/<int:id>.png')
def ding_qr(id):
    Ding.query.get_or_404(id)
    return send_file(_make_qr(f'{_base(request)}/ding/{id}'), mimetype='image/png')


@qr_bp.route('/behaelter/<int:id>.png')
def behaelter_qr(id):
    Behaelter.query.get_or_404(id)
    return send_file(_make_qr(f'{_base(request)}/standort/behaelter/{id}'), mimetype='image/png')


@qr_bp.route('/regalfach/<int:id>.png')
def regalfach_qr(id):
    Regalfach.query.get_or_404(id)
    return send_file(_make_qr(f'{_base(request)}/standort/regalfach/{id}'), mimetype='image/png')


@qr_bp.route('/raum/<int:id>.png')
def raum_qr(id):
    Raum.query.get_or_404(id)
    return send_file(_make_qr(f'{_base(request)}/standort/raum/{id}'), mimetype='image/png')


# ── Label-Einzelansicht ────────────────────────────────────────────────────

@qr_bp.route('/ding/<int:id>/label')
def ding_label(id):
    ding = Ding.query.get_or_404(id)
    qr_url = f'{_base(request)}/qr/ding/{id}.png'
    return render_template('qr/label.html', ding=ding, qr_url=qr_url)


# ── Druckansicht mehrere Labels ────────────────────────────────────────────

@qr_bp.route('/druck')
def druck():
    ids = request.args.getlist('id', type=int)
    dinge = Ding.query.filter(Ding.id.in_(ids)).order_by(Ding.name).all() if ids \
            else Ding.query.order_by(Ding.name).all()
    base = _base(request)
    labels = [{'ding': d, 'qr_url': f'{base}/qr/ding/{d.id}.png'} for d in dinge]
    return render_template('qr/druck.html', labels=labels)
