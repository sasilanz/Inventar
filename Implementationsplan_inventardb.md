# InventarDB – Implementationsplan

Stand: 2026-02-23
Ziel: Schritt-für-Schritt-Anleitung zum Selbermachen. Bei Fragen einfach Claude fragen.

---

## Übersicht

| Phase | Inhalt                              | Ziel                                      |
|-------|-------------------------------------|-------------------------------------------|
| 1     | Docker-Fundament                    | `docker compose up --build` läuft         |
| 2     | Datenmodell & Migrationen           | DB-Schema steht                           |
| 3     | Grundgerüst UI                      | Navigation, Base-Template                 |
| 4     | CRUD Standort-Hierarchie            | Zonen, Räume, Gestelle etc. verwaltbar    |
| 5     | CRUD Dinge                          | Dinge erfassen, suchen, filtern           |
| 6     | Medien & Uploads                    | Fotos und Belege hochladen                |
| 7     | Verleih & Bewegungshistorie         | Ausleihen tracken, Umzüge protokollieren  |
| 8     | QR-Codes                            | QR generieren, Scan öffnet Detailseite    |

---

## Phase 1 – Docker-Fundament

### Ziel
`docker compose up --build` startet beide Container (app + db). Die App ist unter `http://localhost:5000` erreichbar. Kein lokales Python/venv nötig.

---

### 1.1 `requirements.txt` vervollständigen

```
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.7
Flask-WTF==1.2.1
WTForms==3.1.2
psycopg2-binary==2.9.9
python-dotenv==1.0.1
Werkzeug==3.0.3
Pillow==10.4.0
qrcode==7.4.2
```

---

### 1.2 `Dockerfile` schreiben

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Abhängigkeiten zuerst installieren (besseres Layer-Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode kopieren
COPY . .

EXPOSE 5000

# Flask-Dev-Server mit Auto-Reload
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
```

---

### 1.3 `.dockerignore` schreiben

```
__pycache__/
*.pyc
*.pyo
.env
.git/
*.md
app/media/
migrations/
```

---

### 1.4 `docker-compose.yml` – App-Service ergänzen

```yaml
services:

  db:
    image: postgres:16-alpine
    container_name: inventardb-db
    environment:
      POSTGRES_DB: inventardb
      POSTGRES_USER: inventardb
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - inventardb-pgdata:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U inventardb -d inventardb"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    container_name: inventardb-app
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgresql://inventardb:${POSTGRES_PASSWORD}@db:5432/inventardb
      SECRET_KEY: ${SECRET_KEY}
      FLASK_APP: run.py
      FLASK_ENV: development
      FLASK_DEBUG: "1"
    volumes:
      - .:/app                              # Hot-Reload: Codeänderungen sofort sichtbar
      - inventardb-media:/app/app/media     # Medien-Volume
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

volumes:
  inventardb-pgdata:
  inventardb-media:
```

---

### 1.5 `.env` anpassen

```
POSTGRES_PASSWORD=sicher-aendern-2026
SECRET_KEY=langen-zufaelligen-string-hier-eintragen
FLASK_ENV=development
```

Hinweis: `DATABASE_URL` nicht mehr in `.env` – docker-compose.yml baut sie selbst zusammen.

---

### 1.6 `app/__init__.py` bereinigen

Die Datei heisst aktuell `app/init.py` (ohne Unterstriche). Sie muss `app/__init__.py` heissen damit Flask das Package erkennt. Inhalt:

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import DevelopmentConfig, ProductionConfig
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    db.init_app(app)
    migrate.init_app(app, db)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Blueprints – werden in Phase 3 eingebaut
    # from app.routes import main_bp
    # app.register_blueprint(main_bp)

    @app.route('/')
    def index():
        return 'InventarDB läuft!'

    return app
```

---

### 1.7 Starten und testen

```bash
docker compose up --build
```

Erwartetes Ergebnis:
- `inventardb-db` startet, wird healthy
- `inventardb-app` startet danach
- `http://localhost:5000` zeigt: `InventarDB läuft!`

Logs anschauen falls etwas nicht stimmt:
```bash
docker compose logs -f app
docker compose logs -f db
```

---

## Phase 2 – Datenmodell & Migrationen

### Ziel
Alle Tabellen aus dem Konzept als SQLAlchemy-Models. Migration anwenden → DB-Schema steht.

---

### 2.1 Dateistruktur für Models

Alle Models in einzelne Dateien aufteilen, dann in `app/models/__init__.py` zusammenführen:

```
app/
  models/
    __init__.py       ← importiert alle Models
    standort.py       ← Zone, Raum, Gestell, Regalfach, Behaelter
    inventar.py       ← Kategorie, Tag, DingTag, Ding
    media.py          ← Medium
    tracking.py       ← Verleih, Bewegung
```

---

### 2.2 `app/models/standort.py`

```python
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
    raum_id = db.Column(db.Integer, db.ForeignKey('raum.id'), nullable=True)
    beschreibung = db.Column(db.Text)
    qr_code = db.Column(db.String(100), unique=True)

    dinge = db.relationship('Ding', backref='behaelter', lazy=True,
                             foreign_keys='Ding.behaelter_id')

    def __repr__(self):
        return f'<Behaelter {self.name}>'
```

---

### 2.3 `app/models/inventar.py`

```python
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
        if self.raum_id and self.raum:
            return f'{self.raum.name} (frei im Raum)'
        return 'Kein Standort'

    def __repr__(self):
        return f'<Ding {self.name}>'
```

---

### 2.4 `app/models/media.py`

```python
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
```

---

### 2.5 `app/models/tracking.py`

```python
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
    ding_id = db.Column(db.Integer, db.ForeignKey('ding.id'), nullable=False)
    von_beschreibung = db.Column(db.String(500))   # denormalisiert als Text
    nach_beschreibung = db.Column(db.String(500))
    zeitpunkt = db.Column(db.DateTime, default=datetime.utcnow)
    notiz = db.Column(db.Text)

    def __repr__(self):
        return f'<Bewegung Ding {self.ding_id} um {self.zeitpunkt}>'
```

---

### 2.6 `app/models/__init__.py`

```python
from app.models.standort import Zone, Raum, Gestell, Regalfach, Behaelter
from app.models.inventar import Kategorie, Tag, Ding, ding_tag
from app.models.media import Medium
from app.models.tracking import Verleih, Bewegung
```

---

### 2.7 Migration erstellen und anwenden

```bash
# Migrations-Ordner initialisieren (einmalig)
docker compose exec app flask db init

# Erste Migration generieren
docker compose exec app flask db migrate -m "initiales Schema"

# Migration anwenden
docker compose exec app flask db upgrade
```

Prüfen ob Tabellen da sind:
```bash
docker compose exec db psql -U inventardb -d inventardb -c '\dt'
```

---

## Phase 3 – Grundgerüst UI

### Ziel
Saubere Blueprint-Struktur, Base-Template mit Bootstrap 5, Navigation (Desktop + Handy).

---

### 3.1 Dateistruktur

```
app/
  routes/
    __init__.py       ← registriert alle Blueprints
    main.py           ← Startseite, Suche
    standort.py       ← Zonen, Räume, Gestelle etc.
    ding.py           ← Ding CRUD
    media.py          ← Upload, Download
    verleih.py        ← Verleih
    qr.py             ← QR-Code generieren
  templates/
    base.html         ← Layout mit Navigation
    index.html        ← Startseite
    standort/
      zone_liste.html
      ...
    ding/
      liste.html
      detail.html
      formular.html
  static/
    css/
      custom.css
```

---

### 3.2 `app/templates/base.html`

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}InventarDB{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
        rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"
        rel="stylesheet">
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container-fluid">
    <a class="navbar-brand" href="/">
      <i class="bi bi-house-door"></i> InventarDB
    </a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
            data-bs-target="#nav">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="nav">
      <ul class="navbar-nav me-auto">
        <li class="nav-item">
          <a class="nav-link" href="/ding">Dinge</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/standort">Standorte</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/verleih">Verleih</a>
        </li>
      </ul>
      <form class="d-flex" action="/suche" method="get">
        <input class="form-control me-2" type="search" name="q" placeholder="Suchen...">
        <button class="btn btn-outline-light" type="submit">
          <i class="bi bi-search"></i>
        </button>
      </form>
    </div>
  </div>
</nav>

<main class="container-fluid py-3">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for category, message in messages %}
      <div class="alert alert-{{ category }} alert-dismissible fade show">
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    {% endfor %}
  {% endwith %}

  {% block content %}{% endblock %}
</main>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js">
</script>
</body>
</html>
```

---

### 3.3 Blueprints registrieren

`app/routes/__init__.py`:
```python
from app.routes.main import main_bp
from app.routes.standort import standort_bp
from app.routes.ding import ding_bp
from app.routes.verleih import verleih_bp
from app.routes.qr import qr_bp
```

`app/__init__.py` – Blueprints einhängen:
```python
from app.routes import main_bp, standort_bp, ding_bp, verleih_bp, qr_bp
app.register_blueprint(main_bp)
app.register_blueprint(standort_bp, url_prefix='/standort')
app.register_blueprint(ding_bp, url_prefix='/ding')
app.register_blueprint(verleih_bp, url_prefix='/verleih')
app.register_blueprint(qr_bp, url_prefix='/qr')
```

---

## Phase 4 – CRUD Standort-Hierarchie

### Ziel
Zonen, Räume, Gestelle, Regalfächer und Behälter können angelegt, bearbeitet und gelöscht werden.

---

### 4.1 Reihenfolge

Von oben nach unten:
1. Zone (keine Abhängigkeit)
2. Raum (braucht Zone)
3. Gestell (braucht Raum)
4. Regalfach (braucht Gestell)
5. Behälter (braucht Regalfach oder Raum)

---

### 4.2 Muster für eine Route (Beispiel: Zone)

`app/routes/standort.py`:
```python
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Zone

standort_bp = Blueprint('standort', __name__)


@standort_bp.route('/zonen')
def zone_liste():
    zonen = Zone.query.order_by(Zone.name).all()
    return render_template('standort/zone_liste.html', zonen=zonen)


@standort_bp.route('/zonen/neu', methods=['GET', 'POST'])
def zone_neu():
    if request.method == 'POST':
        zone = Zone(
            name=request.form['name'],
            beschreibung=request.form.get('beschreibung')
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
        zone.name = request.form['name']
        zone.beschreibung = request.form.get('beschreibung')
        db.session.commit()
        flash('Zone aktualisiert.', 'success')
        return redirect(url_for('standort.zone_liste'))
    return render_template('standort/zone_formular.html', zone=zone)


@standort_bp.route('/zonen/<int:id>/loeschen', methods=['POST'])
def zone_loeschen(id):
    zone = Zone.query.get_or_404(id)
    db.session.delete(zone)
    db.session.commit()
    flash('Zone gelöscht.', 'warning')
    return redirect(url_for('standort.zone_liste'))
```

Dieses Muster (liste / neu / bearbeiten / loeschen) für alle anderen Standort-Entitäten wiederholen.

---

### 4.3 Muster-Template (Beispiel: Zone-Liste)

`app/templates/standort/zone_liste.html`:
```html
{% extends 'base.html' %}
{% block title %}Zonen{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h1>Zonen</h1>
  <a href="{{ url_for('standort.zone_neu') }}" class="btn btn-primary">
    <i class="bi bi-plus-circle"></i> Neue Zone
  </a>
</div>

<div class="list-group">
  {% for zone in zonen %}
  <div class="list-group-item d-flex justify-content-between align-items-center">
    <div>
      <strong>{{ zone.name }}</strong>
      {% if zone.beschreibung %}
        <small class="text-muted ms-2">{{ zone.beschreibung }}</small>
      {% endif %}
      <span class="badge bg-secondary ms-2">{{ zone.raeume|length }} Räume</span>
    </div>
    <div>
      <a href="{{ url_for('standort.zone_bearbeiten', id=zone.id) }}"
         class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-pencil"></i>
      </a>
      <form method="post"
            action="{{ url_for('standort.zone_loeschen', id=zone.id) }}"
            style="display:inline"
            onsubmit="return confirm('Zone wirklich löschen?')">
        <button class="btn btn-sm btn-outline-danger">
          <i class="bi bi-trash"></i>
        </button>
      </form>
    </div>
  </div>
  {% else %}
  <div class="list-group-item text-muted">Noch keine Zonen erfasst.</div>
  {% endfor %}
</div>
{% endblock %}
```

---

## Phase 5 – CRUD Dinge

### Ziel
Dinge erfassen, bearbeiten, löschen. Liste mit Suche und Filter. Detailseite.

---

### 5.1 Ding-Liste mit Suche/Filter

`app/routes/ding.py`:
```python
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Ding, Kategorie, Tag, Raum, Regalfach, Behaelter

ding_bp = Blueprint('ding', __name__)


@ding_bp.route('/')
def liste():
    q = request.args.get('q', '')
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
        ding = Ding(name=request.form['name'])
        _ding_aus_formular(ding, request.form)
        db.session.add(ding)
        db.session.commit()
        flash('Ding gespeichert.', 'success')
        return redirect(url_for('ding.detail', id=ding.id))
    return render_template('ding/formular.html', ding=None,
                            **_formular_daten())


@ding_bp.route('/<int:id>/bearbeiten', methods=['GET', 'POST'])
def bearbeiten(id):
    ding = Ding.query.get_or_404(id)
    if request.method == 'POST':
        ding.name = request.form['name']
        _ding_aus_formular(ding, request.form)
        db.session.commit()
        flash('Ding aktualisiert.', 'success')
        return redirect(url_for('ding.detail', id=ding.id))
    return render_template('ding/formular.html', ding=ding,
                            **_formular_daten())


@ding_bp.route('/<int:id>/loeschen', methods=['POST'])
def loeschen(id):
    ding = Ding.query.get_or_404(id)
    db.session.delete(ding)
    db.session.commit()
    flash('Ding gelöscht.', 'warning')
    return redirect(url_for('ding.liste'))


def _formular_daten():
    return dict(
        kategorien=Kategorie.query.order_by(Kategorie.name).all(),
        alle_tags=Tag.query.order_by(Tag.name).all(),
        raeume=Raum.query.order_by(Raum.name).all(),
        regalfaecher=Regalfach.query.all(),
        behaelter=Behaelter.query.order_by(Behaelter.name).all(),
    )


def _ding_aus_formular(ding, form):
    ding.beschreibung = form.get('beschreibung')
    ding.hersteller = form.get('hersteller')
    ding.modell = form.get('modell')
    ding.seriennummer = form.get('seriennummer')
    ding.kategorie_id = form.get('kategorie_id') or None
    ding.raum_id = form.get('raum_id') or None
    ding.regalfach_id = form.get('regalfach_id') or None
    ding.behaelter_id = form.get('behaelter_id') or None
    # Tags
    tag_ids = form.getlist('tag_ids')
    ding.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all() if tag_ids else []
```

---

## Phase 6 – Medien & Uploads

### Ziel
Fotos und Dokumente hochladen, anzeigen, löschen.

---

### 6.1 Upload-Route

```python
import os
from werkzeug.utils import secure_filename
from flask import current_app
from app.models import Medium

ERLAUBTE_ENDUNGEN = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webp'}

def erlaubte_datei(dateiname):
    return '.' in dateiname and \
           dateiname.rsplit('.', 1)[1].lower() in ERLAUBTE_ENDUNGEN


@media_bp.route('/ding/<int:ding_id>/upload', methods=['POST'])
def upload(ding_id):
    ding = Ding.query.get_or_404(ding_id)
    datei = request.files.get('datei')

    if datei and erlaubte_datei(datei.filename):
        dateiname = secure_filename(datei.filename)
        # Eindeutiger Unterordner pro Ding
        ordner = os.path.join(current_app.config['UPLOAD_FOLDER'], str(ding_id))
        os.makedirs(ordner, exist_ok=True)
        pfad = os.path.join(ordner, dateiname)
        datei.save(pfad)

        medium = Medium(
            ding_id=ding_id,
            typ=request.form.get('typ', 'foto'),
            dateiname=dateiname,
            pfad=os.path.join(str(ding_id), dateiname),
            beschreibung=request.form.get('beschreibung')
        )
        db.session.add(medium)
        db.session.commit()
        flash('Datei hochgeladen.', 'success')

    return redirect(url_for('ding.detail', id=ding_id))
```

---

## Phase 7 – Verleih & Bewegungshistorie

### Ziel
Dinge ausleihen und zurückgeben. Bei Standortwechsel automatisch Bewegung protokollieren.

---

### 7.1 Verleih-Routen

```python
@verleih_bp.route('/neu/<int:ding_id>', methods=['POST'])
def neu(ding_id):
    verleih = Verleih(
        ding_id=ding_id,
        person=request.form['person'],
        ausgeliehen_am=datetime.strptime(request.form['ausgeliehen_am'], '%Y-%m-%d'),
        faellig_am=datetime.strptime(request.form['faellig_am'], '%Y-%m-%d')
                   if request.form.get('faellig_am') else None,
        notiz=request.form.get('notiz')
    )
    db.session.add(verleih)
    db.session.commit()
    flash(f'Ding an {verleih.person} ausgeliehen.', 'success')
    return redirect(url_for('ding.detail', id=ding_id))


@verleih_bp.route('/<int:id>/zurueck', methods=['POST'])
def zurueck(id):
    verleih = Verleih.query.get_or_404(id)
    verleih.zurueck_am = datetime.utcnow().date()
    db.session.commit()
    flash('Rückgabe vermerkt.', 'success')
    return redirect(url_for('ding.detail', id=verleih.ding_id))
```

---

### 7.2 Bewegung automatisch beim Speichern

In der `bearbeiten`-Route von `ding.py` – vor dem Commit prüfen ob Standort sich geändert hat:

```python
# Alten Standort merken
alter_standort = ding.standort_beschreibung()

_ding_aus_formular(ding, request.form)

# Neuen Standort vergleichen
neuer_standort = ding.standort_beschreibung()
if alter_standort != neuer_standort:
    bewegung = Bewegung(
        ding_id=ding.id,
        von_beschreibung=alter_standort,
        nach_beschreibung=neuer_standort
    )
    db.session.add(bewegung)

db.session.commit()
```

---

## Phase 8 – QR-Codes

### Ziel
QR-Code für jedes Ding (und Behälter, Raum etc.) generieren. Scan öffnet direkt die Detailseite.

---

### 8.1 QR-Code generieren

```python
import qrcode
import io
from flask import send_file

@qr_bp.route('/ding/<int:id>')
def ding_qr(id):
    ding = Ding.query.get_or_404(id)
    url = f'http://<raspberry-pi-ip>:5000/ding/{id}'  # IP anpassen

    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')
```

### 8.2 QR-Label drucken

QR-Code-Bild in Template einbetten:
```html
<img src="{{ url_for('qr.ding_qr', id=ding.id) }}"
     width="150" height="150"
     alt="QR-Code {{ ding.name }}">
```

Für den Druck: separates Print-Template mit mehreren QR-Codes auf einer Seite (Avery-Label-Format o.ä.).

---

## Hilfreiche Befehle (Spickzettel)

```bash
# Container starten
docker compose up --build

# Stoppen
docker compose down

# App-Logs
docker compose logs -f app

# Flask-Befehl ausführen
docker compose exec app flask <befehl>

# Migration neu erstellen
docker compose exec app flask db migrate -m "beschreibung"

# Migration anwenden
docker compose exec app flask db upgrade

# PostgreSQL-Shell
docker compose exec db psql -U inventardb -d inventardb

# Tabellen anzeigen
docker compose exec db psql -U inventardb -d inventardb -c '\dt'

# App-Shell (für schnelle DB-Tests)
docker compose exec app flask shell
```

---

## Mögliche Erweiterungen (später)

- **Mehrbenutzerbetrieb** mit Login (Flask-Login)
- **Barcode-Scan** über Handy-Kamera (HTML5 + JavaScript)
- **Export** als CSV oder PDF
- **Erinnerungen** bei ablaufender Garantie
- **Backup-Script** für DB und Medien-Volume
- **Reverse Proxy** (nginx) damit die App unter Port 80 läuft (mit bestehender dieti-it-App koexistieren)
