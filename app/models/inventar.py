from app import db
from datetime import datetime

ding_tag = db.Table('ding_tag',
    db.Column('ding_id', db.Integer, db.ForeignKey('ding.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


class Kategorie(db.Model):
    __tablename__ = 'kategorie'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    beschreibung = db.Column(db.Text)

    dinge = db.relationship('Ding', backref='kategorie', lazy=True)

    def __repr__(self):
        return f'<Kategorie {self.name}>'


class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Tag {self.name}>'


class Ding(db.Model):
    __tablename__ = 'ding'
    id = db.Column(db.Integer, primary_key=True)

    # Basis
    name = db.Column(db.String(200), nullable=False)
    beschreibung = db.Column(db.Text)

    # Standort (genau eines davon gesetzt)
    raum_id = db.Column(db.Integer, db.ForeignKey('raum.id'), nullable=True)
    gestell_id = db.Column(db.Integer, db.ForeignKey('gestell.id'), nullable=True)
    regalfach_id = db.Column(db.Integer, db.ForeignKey('regalfach.id'), nullable=True)
    behaelter_id = db.Column(db.Integer, db.ForeignKey('behaelter.id'), nullable=True)

    # Klassifikation
    kategorie_id = db.Column(db.Integer, db.ForeignKey('kategorie.id'), nullable=True)
    tags = db.relationship('Tag', secondary=ding_tag, lazy='subquery',
                            backref=db.backref('dinge', lazy=True))

    # Gerätedaten
    hersteller = db.Column(db.String(200))
    modell = db.Column(db.String(200))
    seriennummer = db.Column(db.String(200))

    # Versicherung
    kaufdatum = db.Column(db.Date)
    kaufpreis = db.Column(db.Numeric(10, 2))
    waehrung = db.Column(db.String(10), default='CHF')
    garantie_bis = db.Column(db.Date)
    versichert_bei = db.Column(db.String(200))
    versicherungsnummer = db.Column(db.String(200))

    # Sonstiges
    qr_code = db.Column(db.String(100), unique=True)
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)
    aktualisiert_am = db.Column(db.DateTime, default=datetime.utcnow,
                                 onupdate=datetime.utcnow)

    # Beziehungen
    medien = db.relationship('Medium', backref='ding', lazy=True,
                              cascade='all, delete-orphan')
    verleih_eintraege = db.relationship('Verleih', backref='ding', lazy=True,
                                         cascade='all, delete-orphan')
    bewegungen = db.relationship('Bewegung', backref='ding', lazy=True,
                                  cascade='all, delete-orphan')

    @property
    def ist_ausgeliehen(self):
        return any(v.zurueck_am is None for v in self.verleih_eintraege)

    def standort_beschreibung(self):
        """Lesbare Standortangabe für Bewegungshistorie."""
        if self.behaelter_id and self.behaelter:
            return f'{self.behaelter.name} (Behälter)'
        if self.regalfach_id and self.regalfach:
            return f'{self.regalfach.bezeichnung} / {self.regalfach.gestell.name}'
        if self.gestell_id and self.gestell:
            return f'{self.gestell.name} (direkt im Gestell)'
        if self.raum_id and self.raum:
            return f'{self.raum.name} (frei im Raum)'
        return 'Kein Standort'

    def __repr__(self):
        return f'<Ding {self.name}>'
