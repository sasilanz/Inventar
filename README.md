# InventarDB

Selbstgehostete Inventarverwaltung für Haus und Wohnung.
Stack: Python / Flask · PostgreSQL · Docker Compose

---

## Voraussetzungen

- [Docker](https://docs.docker.com/get-docker/) inkl. Docker Compose Plugin
- Git

```bash
# Versionen prüfen
docker --version
docker compose version
```

---

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/<dein-user>/inventardb.git
cd inventardb
```

### 2. Umgebungsvariablen einrichten

Die App benötigt eine `.env`-Datei im Projektverzeichnis.
**Diese Datei ist nicht im Repository** (steht in `.gitignore`) – du musst sie manuell anlegen.

```bash
cp .env.example .env
```

> Falls keine `.env.example` vorhanden ist, einfach eine neue Datei anlegen:

```bash
touch .env
```

Dann die Datei mit einem Editor öffnen und folgende Zeilen eintragen:

```dotenv
# Datenbankpasswort (frei wählbar, wird beim ersten Start automatisch gesetzt)
POSTGRES_PASSWORD=sicherespasswort

# Geheimer Schlüssel für Flask-Sessions (frei wählbar, lang und zufällig)
SECRET_KEY=einlangesgeheimeszeichenfolge

# Basis-URL für QR-Codes (IP oder Domain, unter der die App erreichbar ist)
# Wichtig: ohne abschliessenden Schrägstrich
QR_BASE_URL=http://192.168.1.100:5000
```

> **Wichtig:** `POSTGRES_PASSWORD` und `SECRET_KEY` können beliebige Werte sein,
> müssen aber gesetzt werden – sonst startet die App nicht korrekt.

### 3. Container starten

```bash
docker compose up -d
```

Beim ersten Start werden automatisch:
- der PostgreSQL-Container gestartet und die Datenbank `inventardb` erstellt
- der App-Container gebaut (dauert beim ersten Mal 1–2 Minuten)

Status prüfen:

```bash
docker compose ps
```

Beide Container (`inventardb-db` und `inventardb-app`) sollten `running` anzeigen.

### 4. Datenbank-Schema einrichten

Beim **allerersten Start** muss das Schema in die leere Datenbank eingespielt werden:

```bash
docker compose exec app flask db upgrade
```

Dieser Befehl führt alle Migrationen aus und erstellt die nötigen Tabellen.
Bei späteren Updates (nach `git pull`) denselben Befehl erneut ausführen.

### 5. App aufrufen

```
http://<ip-adresse>:5000
```

---

## QR-Codes richtig einrichten

QR-Codes enthalten eine fixe URL. Damit sie auch vom Handy scanbar sind,
muss `QR_BASE_URL` in der `.env` auf die **Netzwerk-IP** des Servers zeigen –
**nicht** auf `localhost`.

```dotenv
# Richtig (IP im lokalen Netzwerk):
QR_BASE_URL=http://192.168.1.100:5000

# Falsch (funktioniert nur auf dem Server selbst):
QR_BASE_URL=http://localhost:5000
```

Nach einer Änderung an `.env` Container neu starten:

```bash
docker compose up -d
```

---

## Häufige Probleme

### „Connection refused" / App startet nicht

```bash
# Logs anzeigen
docker compose logs app
docker compose logs db
```

### Datenbank leer nach Neustart

Das Schema wurde noch nicht eingespielt. Lösung:

```bash
docker compose exec app flask db upgrade
```

### Port 5000 bereits belegt

In `docker-compose.yml` den Port ändern, z.B. auf 5001:

```yaml
ports:
  - "0.0.0.0:5001:5000"
```

Dann auch `QR_BASE_URL` in `.env` anpassen:

```dotenv
QR_BASE_URL=http://192.168.1.100:5001
```

---

## Updates einspielen

```bash
git pull
docker compose up -d --build
docker compose exec app flask db upgrade
```

---

## Daten sichern

### Datenbank-Backup erstellen

```bash
docker compose exec db pg_dump -U inventardb inventardb > backup_$(date +%Y%m%d).sql
```

### Backup wiederherstellen

```bash
cat backup_20260101.sql | docker compose exec -T db psql -U inventardb inventardb
```

---

## Verzeichnisstruktur

```
inventardb/
├── app/
│   ├── models/          # Datenmodelle (Standort, Inventar, Medien, Verleih)
│   ├── routes/          # Flask Blueprints
│   └── templates/       # Jinja2-Templates
├── migrations/          # Alembic-Migrationen (Datenbankschema)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env                 # ← selbst anlegen, nicht im Repo!
```

---

## Technische Details

| Komponente | Details |
|---|---|
| App | Python 3.12, Flask 3.0 |
| Datenbank | PostgreSQL 16 |
| ORM | SQLAlchemy + Flask-Migrate (Alembic) |
| Frontend | Bootstrap 5.3, Jinja2 |
| Deployment | Docker Compose, 2 Container |
| Daten-Volumes | `inventardb-pgdata` (DB), `inventardb-media` (Uploads) |
