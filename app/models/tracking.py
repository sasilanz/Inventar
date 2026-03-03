from app import db
from datetime import datetime


class Verleih(db.Model):
    __tablename__ = 'verleih'
    id = db.Column(db.Integer, primary_key=True)
    ding_id = db.Column(db.Integer, db.ForeignKey('ding.id'), nullable=False)
    person = db.Column(db.String(200), nullable=False)
    ausgeliehen_am = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    faellig_am = db.Column(db.Date)
    zurueck_am = db.Column(db.Date)     # NULL = noch ausgeliehen
    notiz = db.Column(db.Text)

    @property
    def ist_offen(self):
        return self.zurueck_am is None

    def __repr__(self):
        return f'<Verleih {self.ding_id} an {self.person}>'


class Bewegung(db.Model):
    __tablename__ = 'bewegung'
    id = db.Column(db.Integer, primary_key=True)
    ding_id = db.Column(db.Integer, db.ForeignKey('ding.id'), nullable=True)
    behaelter_id = db.Column(db.Integer, db.ForeignKey('behaelter.id'), nullable=True)
    gestell_id = db.Column(db.Integer, db.ForeignKey('gestell.id'), nullable=True)
    von_beschreibung = db.Column(db.String(500))
    nach_beschreibung = db.Column(db.String(500))
    zeitpunkt = db.Column(db.DateTime, default=datetime.utcnow)
    notiz = db.Column(db.Text)

    def __repr__(self):
        return f'<Bewegung um {self.zeitpunkt}>'
