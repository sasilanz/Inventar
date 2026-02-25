from app import db

class Zone(db.Model):
    __tablename__ = 'zone'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    beschreibung = db.Column(db.Text)
    qr_code = db.Column(db.String(100), unique=True)

    raeume = db.relationship('Raum', backref='zone', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Zone {self.name}>'


class Raum(db.Model):
    __tablename__ = 'raum'
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    beschreibung = db.Column(db.Text)
    qr_code = db.Column(db.String(100), unique=True)

    gestelle = db.relationship('Gestell', backref='raum', lazy=True, cascade='all, delete-orphan')
    behaelter = db.relationship('Behaelter', backref='raum', lazy=True,
                                 foreign_keys='Behaelter.raum_id')
    dinge = db.relationship('Ding', backref='raum', lazy=True,
                             foreign_keys='Ding.raum_id')

    def __repr__(self):
        return f'<Raum {self.name}>'


class Gestell(db.Model):
    __tablename__ = 'gestell'
    id = db.Column(db.Integer, primary_key=True)
    raum_id = db.Column(db.Integer, db.ForeignKey('raum.id'), nullable=False)
    typ = db.Column(db.String(100))
    name = db.Column(db.String(100), nullable=False)
    beschreibung = db.Column(db.Text)
    qr_code = db.Column(db.String(100), unique=True)

    regalfaecher = db.relationship('Regalfach', backref='gestell', lazy=True,
                                    cascade='all, delete-orphan',
                                    order_by='Regalfach.position_index')
    behaelter = db.relationship('Behaelter', backref='gestell', lazy=True,
                                 foreign_keys='Behaelter.gestell_id')
    dinge = db.relationship('Ding', backref='gestell', lazy=True,
                             foreign_keys='Ding.gestell_id')

    def __repr__(self):
        return f'<Gestell {self.name}>'


class Regalfach(db.Model):
    __tablename__ = 'regalfach'
    id = db.Column(db.Integer, primary_key=True)
    gestell_id = db.Column(db.Integer, db.ForeignKey('gestell.id'), nullable=False)
    bezeichnung = db.Column(db.String(100), nullable=False)
    position_index = db.Column(db.Integer, default=0)

    behaelter = db.relationship('Behaelter', backref='regalfach', lazy=True,
                                 foreign_keys='Behaelter.regalfach_id')
    dinge = db.relationship('Ding', backref='regalfach', lazy=True,
                             foreign_keys='Ding.regalfach_id')

    def __repr__(self):
        return f'<Regalfach {self.bezeichnung}>'


class Behaelter(db.Model):
    __tablename__ = 'behaelter'
    id = db.Column(db.Integer, primary_key=True)
    typ = db.Column(db.String(50))
    name = db.Column(db.String(100), nullable=False)
    regalfach_id = db.Column(db.Integer, db.ForeignKey('regalfach.id'), nullable=True)
    gestell_id = db.Column(db.Integer, db.ForeignKey('gestell.id'), nullable=True)
    raum_id = db.Column(db.Integer, db.ForeignKey('raum.id'), nullable=True)
    beschreibung = db.Column(db.Text)
    qr_code = db.Column(db.String(100), unique=True)

    dinge = db.relationship('Ding', backref='behaelter', lazy=True,
                             foreign_keys='Ding.behaelter_id')

    def __repr__(self):
        return f'<Behaelter {self.name}>'
