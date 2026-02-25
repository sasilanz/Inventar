# InventarDB – Fachliches Konzept & ER-Beschreibung

Stand: 2026-02-23
Ziel: Selbstgehostete Inventarverwaltung (Haus/Wohnung) mit Standort-Hierarchie, Versicherungsdaten, Medien (Fotos/Belege), Verleih-Tracking und QR-Codes. Deployment als Web-App im LAN, vollständig in Docker (Raspberry Pi).

---

## 1. Fachliche Ziele

- Inventar von Gegenständen in Haus/Wohnung verwalten.
- Standortmodell mit Hierarchie:
  - **Zone** → Raum → Gestell → Regalfach → Behälter → Ding.
  - Ein Ding kann **optional** auch direkt im Raum stehen (z.B. Laufband, Velo).
- Pro Ding:
  - Grunddaten (Name, Beschreibung, Hersteller, Modell, Seriennummer).
  - Versicherungsrelevante Daten (Kaufdatum, Kaufpreis, Garantie, Versicherer, Vertrag etc.).
  - Medien: Fotos des Gegenstands, Kaufbelege, Bedienungsanleitungen (als Datei oder Link).
- Klassifikation:
  - Kategorien (1 Kategorie je Ding).
  - Tags (beliebig viele Tags je Ding).
- Verleih:
  - Verleih an Personen, mit Datum, Fälligkeit und Rückgabe.
- Bewegungen:
  - Historie von Ortswechseln (Umzüge innerhalb des Hauses).
- QR-Codes:
  - QR-Feld für Zone, Raum, Gestell, Behälter und Ding.
  - Scan soll direkt die Detailseite öffnen (oder eine passende Übersicht).
- Technik:
  - **Alles läuft in Docker – kein lokales Python-Venv nötig.**
  - Zwei separate Container: `app` (Flask/Python) und `db` (PostgreSQL).
  - Medien als Dateien in einem Docker-Volume (kein Cloud-Speicher).
  - Uploads per Handy-Foto über Browser-Formulare.
  - Deployment auf vorhandenem Raspberry Pi mit bestehender Webapp (dieti-it), via docker compose.
- **Beispiel-Zonen**: Keller, EG, Garten, OG, DG.
- **Beispiel-Räume**:
  - Keller: Werkstatt, Keller, Garage, Vorratsraum, Heizraum, Kreml, ...
  - EG: Wohnzimmer, Küche, Arbeitszimmer, ...
  - Garten: Terrasse, Gartenhaus, grosse Aussenkiste, ...
  - OG: Wohnzimmer, Küche, Bad, Asi-Zimmer, grosse Terrasse, Eingangsterrasse, ...
  - DG: Bad, Schlafzimmer, Sandra-Zimmer, Terrasse, ...

---

## 2. Entitäten und Attribute (ER-Beschreibung)

### 2.1 Standort-Hierarchie

#### 2.1.1 `zone`

Repräsentiert eine Zone/Bereich im Haus (EG, OG, Keller, Garten etc.).

- `id` (PK)
- `name`
  Beispiel: „Keller", „EG", „Garten", „OG", „DG"
- `beschreibung` (optional)
- `qr_code` (optional, Text; eindeutiger Code für QR-Label)

**Beziehung:**

- 1 `zone` hat 0..N `raum`.

---

#### 2.1.2 `raum`

Repräsentiert einen Raum innerhalb einer Zone.

- `id` (PK)
- `zone_id` (FK → `zone.id`)
- `name`
  Beispiel: „Werkstatt", „Wohnzimmer", „Gartenhaus", „Terrasse"
- `beschreibung` (optional)
- `qr_code` (optional; QR-Label an der Tür oder im Raum)

**Beziehungen:**

- N `raum` gehören zu genau 1 `zone`.
- 1 `raum` hat 0..N `gestell`.
- 1 `raum` kann 0..N `behaelter` direkt enthalten.
- 1 `raum` kann 0..N `ding` direkt enthalten (z.B. Laufband ohne Behälter/Regal).

---

#### 2.1.3 `gestell`

Repräsentiert ein Regal, Schrank etc. in einem Raum.

- `id` (PK)
- `raum_id` (FK → `raum.id`)
- `typ` (Text; z.B. „Metallregal", „Schrank")
- `name` (frei vergebbar, z.B. „Werkstatt-Regal links")
- `beschreibung` (optional)
- `qr_code` (optional; QR-Label am Gestell)

**Beziehungen:**

- N `gestell` gehören zu genau 1 `raum`.
- 1 `gestell` hat 0..N `regalfach`.

---

#### 2.1.4 `regalfach`

Repräsentiert ein Fach/Boden in einem Gestell.

- `id` (PK)
- `gestell_id` (FK → `gestell.id`)
- `bezeichnung`
  Beispiel: „Fach A", „Boden 3", „Schublade oben"
- `position_index` (Integer; für sortierte Anzeige der Fächer)

**Beziehungen:**

- N `regalfach` gehören zu genau 1 `gestell`.
- 1 `regalfach` hat 0..N `behaelter`.
- 1 `regalfach` kann 0..N `ding` direkt enthalten (Dinge ohne Behälter).

---

#### 2.1.5 `behaelter`

Repräsentiert einen Behälter (Box, Kiste, Schublade etc.).

- `id` (PK)
- `typ`
  Beispiel: „Box", „Kiste", „Schublade"
- `name`
  Beispiel: „Elektro-Kleinteile", „Weihnachtskiste"
- `regalfach_id` (FK → `regalfach.id`, optional)
- `raum_id` (FK → `raum.id`, optional)
- `beschreibung` (optional)
- `qr_code` (optional; QR-Label auf dem Behälter)

**Beziehungen / Regeln:**

- Ein Behälter steht entweder in einem `regalfach` **oder** direkt in einem `raum`.
- 1 `behaelter` hat 0..N `ding`.

Die App-Logik stellt sicher, dass ein Behälter nicht gleichzeitig im Fach und im Raum gesetzt ist.

---

### 2.2 Inventar-Daten

#### 2.2.1 `kategorie`

Grobkategorie für Dinge.

- `id` (PK)
- `name`
  Beispiel: „Elektronik", „Werkzeug", „Möbel", „Haushalt"
- `beschreibung` (optional)

**Beziehung:**

- 1 `kategorie` kann 0..N `ding` enthalten.
- 1 `ding` hat maximal 1 `kategorie` (FK in `ding`).

---

#### 2.2.2 `tag`

Freie Tags zur flexiblen Kennzeichnung.

- `id` (PK)
- `name`
  Beispiel: „versichert", „Garantie läuft bald ab", „Gaming", „im Einsatz", „Archiv"

---

#### 2.2.3 `ding_tag` (N:M-Verknüpfung)

Verknüpft `ding` und `tag`.

- `ding_id` (FK → `ding.id`)
- `tag_id` (FK → `tag.id`)
- PK aus (`ding_id`, `tag_id`)

**Beziehungen:**

- Ein `ding` kann 0..N `tag` bekommen.
- Ein `tag` kann 0..N `ding` markieren.

---

#### 2.2.4 `ding`

Zentrales Objekt: ein physischer Gegenstand.

- `id` (PK)
- Basis:
  - `name`
  - `beschreibung` (optional)
- Standort (alle optional; App sorgt dafür, dass **genau eine** logische Ortsangabe verwendet wird):
  - `raum_id` (FK → `raum.id`, optional; Ding steht frei im Raum)
  - `regalfach_id` (FK → `regalfach.id`, optional; Ding liegt auf einem Fach)
  - `behaelter_id` (FK → `behaelter.id`, optional; Ding ist in einem Behälter)
- Klassifikation:
  - `kategorie_id` (FK → `kategorie.id`, optional)
- Hersteller / Gerätedaten:
  - `hersteller` (optional)
  - `modell` (optional)
  - `seriennummer` (optional)
- Versicherungsrelevante Daten:
  - `kaufdatum` (optional, Datum)
  - `kaufpreis` (optional, numeric)
  - `waehrung` (optional, z.B. „CHF", „EUR"; Standard: „CHF")
  - `garantie_bis` (optional, Datum)
  - `versichert_bei` (optional, Text; Name des Versicherers)
  - `versicherungsnummer` (optional, Text)
- Weitere:
  - `qr_code` (optional, Text; eindeutiger Code für QR-Label)
  - `erstellt_am` (Timestamp, automatisch)
  - `aktualisiert_am` (Timestamp, automatisch)

**Beziehungen:**

- 1 `ding` hat 0..N `medium`.
- 1 `ding` hat 0..N `verleih`.
- 1 `ding` hat 0..N `bewegung`.
- 1 `ding` hat 0..N `tag` (via `ding_tag`).

---

#### 2.2.5 `medium`

Datei oder Link, der einem Ding zugeordnet ist (Foto, Beleg, Anleitung etc.).

- `id` (PK)
- `ding_id` (FK → `ding.id`)
- `typ`
  Werte: `foto`, `beleg`, `anleitung`, `link`, `sonstiges`
- `dateiname` (optional; Originalname der hochgeladenen Datei)
- `pfad` (optional; relativer Pfad im Media-Volume, bei Datei-Upload)
- `url` (optional; externer Link, z.B. Hersteller-PDF)
- `beschreibung` (optional)
- `hochgeladen_am` (Timestamp, automatisch)

**Regeln:**

- Entweder `pfad` (lokale Datei) **oder** `url` (externer Link) ist gesetzt – nicht beides.

---

#### 2.2.6 `verleih`

Protokolliert, wann ein Ding an jemanden ausgeliehen wurde.

- `id` (PK)
- `ding_id` (FK → `ding.id`)
- `person` (Text; Name der Person, an die verliehen wird)
- `ausgeliehen_am` (Datum)
- `faellig_am` (optional, Datum; geplantes Rückgabedatum)
- `zurueck_am` (optional, Datum; tatsächliches Rückgabedatum; `NULL` = noch ausgeliehen)
- `notiz` (optional)

**Beziehung:**

- N `verleih`-Einträge gehören zu 1 `ding`.
- Ein `ding` gilt als „ausgeliehen", wenn ein `verleih`-Eintrag mit `zurueck_am IS NULL` existiert.

---

#### 2.2.7 `bewegung`

Protokolliert Ortswechsel eines Dings (Umzug innerhalb des Hauses).

- `id` (PK)
- `ding_id` (FK → `ding.id`)
- `von_beschreibung` (Text; lesbare Beschreibung des alten Standorts, z.B. „Keller / Werkstatt / Regal links / Fach B")
- `nach_beschreibung` (Text; lesbare Beschreibung des neuen Standorts)
- `zeitpunkt` (Timestamp)
- `notiz` (optional)

**Hinweis:** Die Standortbeschreibungen werden beim Speichern als Text denormalisiert – so bleibt die Historie auch dann lesbar, wenn Räume/Gestelle später umbenannt werden.

---

## 3. Technik & Deployment

### 3.1 Architektur

Zwei Docker-Container, verwaltet via `docker-compose.yml`:

| Service | Image            | Aufgabe                          |
|---------|------------------|----------------------------------|
| `db`    | postgres:16-alpine | PostgreSQL-Datenbank           |
| `app`   | eigener Build    | Flask-Web-App (Python 3.12)      |

Die Container laufen im selben Docker-Netzwerk. Die App spricht die DB über den internen Hostnamen `db:5432` an. Von aussen ist nur Port 5000 (App) erreichbar.

---

### 3.2 Volumes

| Volume              | Inhalt                                              |
|---------------------|-----------------------------------------------------|
| `inventardb-pgdata` | PostgreSQL-Datenbankdateien (persistent)            |
| `inventardb-media`  | Hochgeladene Medien (Fotos, Belege, Anleitungen)    |

---

### 3.3 Umgebungsvariablen

Konfiguration via `.env`-Datei (wird von docker-compose.yml eingelesen):

| Variable       | Wert (Beispiel)                                      | Hinweis                          |
|----------------|------------------------------------------------------|----------------------------------|
| `DATABASE_URL` | `postgresql://inventardb:<pw>@db:5432/inventardb`    | Hostname = Service-Name `db`     |
| `SECRET_KEY`   | langer zufälliger String                             | Für Flask-Sessions               |
| `FLASK_ENV`    | `development` oder `production`                      |                                  |
| `POSTGRES_PASSWORD` | gleiches Passwort wie in DATABASE_URL           | Nur für den `db`-Container       |

**Wichtig:** In Docker ist der DB-Hostname immer `db` (Service-Name aus docker-compose.yml), niemals `localhost`.

---

### 3.4 Entwicklungs-Workflow

Kein lokales venv, kein lokales Python erforderlich. Alles läuft über Docker:

```bash
# Erster Start oder nach Änderungen am Dockerfile/requirements.txt:
docker compose up --build

# Normaler Start:
docker compose up

# Im Hintergrund starten:
docker compose up -d

# Logs der App anschauen:
docker compose logs -f app

# Stoppen (Daten bleiben erhalten):
docker compose down

# Stoppen + alle Daten löschen (Achtung!):
docker compose down -v
```

Im Entwicklungsmodus wird der Quellcode als Volume in den Container gemountet → Dateiänderungen sind sofort ohne Rebuild sichtbar (Flask-Debug-Modus mit Auto-Reload).

---

### 3.5 Datenbankmigrationen

Migrationen laufen im App-Container via Flask-Migrate (Alembic):

```bash
# Einmalig: Migrations-Ordner initialisieren
docker compose exec app flask db init

# Nach einer Modelländerung: Migration generieren
docker compose exec app flask db migrate -m "Kurzbeschreibung"

# Migration auf die DB anwenden
docker compose exec app flask db upgrade
```

---

### 3.6 Tech-Stack

| Komponente        | Technologie                          |
|-------------------|--------------------------------------|
| Backend           | Python 3.12 / Flask                  |
| Datenbank         | PostgreSQL 16 (Alpine)               |
| ORM               | Flask-SQLAlchemy                     |
| Migrationen       | Flask-Migrate (Alembic)              |
| QR-Codes          | qrcode (Python-Library)              |
| Frontend          | Jinja2-Templates, Bootstrap 5        |
| Containerisierung | Docker / Docker Compose              |
| Zielplattform     | Raspberry Pi (ARM64 / linux/arm64)   |
