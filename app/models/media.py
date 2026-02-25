from app import db
from datetime import datetime


class Medium(db.Model):
    __tablename__ = 'medium'
    id = db.Column(db.Integer, primary_key=True)
    ding_id = db.Column(db.Integer, db.ForeignKey('ding.id'), nullable=False)
    typ = db.Column(db.String(20), nullable=False)
    # Werte: 'foto', 'beleg', 'anleitung', 'link', 'sonstiges'
    dateiname = db.Column(db.String(255))
    pfad = db.Column(db.String(500))        # lokale Datei im Media-Volume
    url = db.Column(db.String(1000))        # externer Link
    beschreibung = db.Column(db.Text)
    hochgeladen_am = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Medium {self.typ} für Ding {self.ding_id}>'
