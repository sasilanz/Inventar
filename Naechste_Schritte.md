# InventarDB – Nächste Schritte

## Phase 9 – LAN-Betrieb auf dem Dev-Desktop

**Ziel:** App ist im lokalen Netzwerk erreichbar (nicht nur auf localhost).

### 9.1 docker-compose.yml anpassen
`docker-compose.yml` → Port auf `0.0.0.0` binden (statt nur localhost):
```yaml
ports:
  - "0.0.0.0:5000:5000"
```
→ App ist dann unter `http://<desktop-ip>:5000` im LAN erreichbar.

### 9.2 Flask im Production-Modus starten (optional aber empfohlen)
In `docker-compose.yml` den CMD auf gunicorn umstellen:
```yaml
command: gunicorn -w 2 -b 0.0.0.0:5000 "app:create_app()"
```
`requirements.txt` → `gunicorn` hinzufügen.

### 9.3 Testen
- Desktop-IP herausfinden: `ip addr show` oder `hostname -I`
- Vom Handy/anderen Gerät im WLAN `http://<ip>:5000` aufrufen


---

## Phase 10 – Automatisches DB-Backup

**Ziel:** Täglicher pg_dump ins Verzeichnis `~/dev/Inventar/backups/`.

### 10.1 Backup-Script erstellen
Datei: `~/dev/Inventar/backup.sh`
```bash
#!/bin/bash
BACKUP_DIR="$(dirname "$0")/backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose -f "$(dirname "$0")/docker-compose.yml" exec -T db \
  pg_dump -U inventar inventar > "$BACKUP_DIR/inventar_$TIMESTAMP.sql"
# Nur die letzten 14 Backups behalten
ls -t "$BACKUP_DIR"/*.sql | tail -n +15 | xargs -r rm
```

### 10.2 Cron-Job einrichten
```bash
crontab -e
# Täglich um 02:00 Uhr:
0 2 * * * /home/asiarch/dev/Inventar/backup.sh >> /home/asiarch/dev/Inventar/backups/backup.log 2>&1
```

### 10.3 Manueller Test
```bash
bash ~/dev/Inventar/backup.sh
ls ~/dev/Inventar/backups/
```


---

## Phase 11 – GUI: Separate Suchen-Maske

**Ziel:** Eigene Seite `/suchen` mit kombinierten Filterkriterien.

### Suchkriterien
- Freitext (Name, Beschreibung, Hersteller, Modell, Seriennummer)
- Kategorie (Dropdown)
- Tag (Mehrfachauswahl)
- Standort: Zone / Raum / Gestell / Regalfach / Behälter (jeweils Dropdown, kaskadierend oder unabhängig)
- Ausgeliehen: ja / nein / egal
- Kaufdatum von/bis
- Garantie läuft ab (Checkbox: nur Dinge mit ablaufender Garantie)

### Umsetzung
- Neue Route `GET /suchen` in `routes/main.py`
- Template `templates/suchen.html` mit Formular + Ergebnistabelle
- Navbar-Link "Suchen" ersetzt das bestehende Inline-Suchfeld in `base.html`


---

## Phase 12 – GUI: Separate Erfassen-Maske

**Ziel:** Eine zentrale Seite `/erfassen` als Einstiegspunkt für alle Neuerfassungen.

### Inhalt der Maske
Kacheln / Buttons für:

| Bereich | Route |
|---|---|
| Neues Ding | `/ding/neu` |
| Neuer Behälter | `/standort/behaelter/neu` |
| Neues Regal (Gestell) | `/standort/gestell/neu` |
| Neues Regalfach | `/standort/regalfach/neu` |
| Neuer Raum | `/standort/raum/neu` |
| Neue Kategorie | `/stammdaten/kategorien/neu` |
| Neuer Tag | `/stammdaten/tags/neu` |
| Neue Person* | (siehe unten) |

*Personen sind bisher nur im Verleih-Formular als Freitext. Optional: eigene Personen-Verwaltung (`/stammdaten/personen`).

### Umsetzung
- Neue Route `GET /erfassen` in `routes/main.py`
- Template `templates/erfassen.html`
- Navbar-Link "Erfassen"


---

## Phase 13 – Stammdaten: Personen-Verwaltung (optional)

**Ziel:** Personen, denen man Dinge ausleiht, vorerfassen statt Freitext.

### Modell
```python
class Person(db.Model):
    id, name, email, telefon, notiz
```

### Umsetzung
- Migration
- CRUD in `routes/stammdaten.py`
- Templates `stammdaten/personen_liste.html`, `personen_formular.html`
- Verleih-Formular: Dropdown statt Freitext für `person`


---

## Phase 14 – Git & GitHub

**Ziel:** Code versioniert und gesichert auf GitHub.

### 14.1 .gitignore erstellen
```
.env
*.pyc
__pycache__/
app/media/
backups/
keller.db
migrations/__pycache__/
*.egg-info/
```

### 14.2 Repo initialisieren & pushen
```bash
cd ~/dev/Inventar
git init
git add .
git commit -m "Initial commit – InventarDB v1"
# GitHub: neues Repo erstellen (privat empfohlen!)
git remote add origin git@github.com:<user>/inventardb.git
git push -u origin main
```


---

## Phase 15 – Deployment auf DietPi

**Ziel:** App läuft dauerhaft auf dem DietPi-Server.

### Voraussetzungen klären
- [ ] DietPi-IP im LAN notieren
- [ ] SSH-Zugang testen: `ssh <user>@<dietpi-ip>`
- [ ] Docker auf DietPi verfügbar? (`docker --version`)
- [ ] Port 5000 frei? Konflikt mit bestehender dieti-it-App? → ggf. Port 5001 verwenden oder nginx Reverse Proxy einrichten

### 15.1 Auf DietPi deployen
```bash
ssh <user>@<dietpi-ip>
git clone git@github.com:<user>/inventardb.git ~/inventar
cd ~/inventar
cp .env.example .env   # .env manuell befüllen (Passwörter!)
docker compose up -d
docker compose exec app flask db upgrade
```

### 15.2 Autostart sicherstellen
Docker Compose startet Container bei Reboot automatisch, wenn `restart: unless-stopped` in `docker-compose.yml` gesetzt ist.

### 15.3 Backup-Cron auch auf DietPi einrichten
Gleich wie Phase 10, aber auf dem Server – ggf. Backup auf NAS/externe Disk rsyncen.

### 15.4 Optional: nginx Reverse Proxy
Falls App auf Port 80 laufen soll (ohne `:5000` in der URL):
```nginx
server {
    listen 80;
    server_name inventar.local;
    location / {
        proxy_pass http://localhost:5000;
    }
}
```


---

## Reihenfolge (Empfehlung)

```
Phase 9  → LAN (schnell, sofort nutzbar)
Phase 10 → Backup (wichtig vor Deployment)
Phase 14 → Git (vor Phase 15 zwingend)
Phase 11 → Suchen-Maske
Phase 12 → Erfassen-Maske
Phase 13 → Personen (optional, nach Bedarf)
Phase 15 → DietPi-Deployment
```
