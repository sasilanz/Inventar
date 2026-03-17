# Playwright-Testbefund – Fixes

## Status-Legende
- [ ] offen
- [x] erledigt

---

## Bugs (Code)

- [x] **#1 – Verleih-Formular: `ausgeliehen_am` ohne Placeholder**
  `app/templates/ding/detail.html:157`
  Fix: `placeholder="Ausgeliehen am"` hinzugefügt.

- [x] **#2 – favicon.ico → 404**
  `app/templates/base.html`
  Fix: Favicon als SVG-Data-URI im `<head>` eingefügt (📦-Emoji).

- [x] **#3 – Singular/Plural: "1 Dinge" statt "1 Ding"**
  Fix: Jinja-Filter `dinge` in `app/__init__.py` registriert.
  Angewendet in: `kategorie_liste.html`, `tag_liste.html`, `behaelter_liste.html`,
  `gestell_detail.html`, `raum_detail.html`, `regalfach_detail.html`,
  `standort/index.html`, `gestell_liste.html`.

- [x] **#4 – Tooltip auf disabled Button nicht sichtbar**
  `app/templates/stammdaten/kategorie_liste.html`
  Fix: Button in `<span title="...">` gewrapped, Tooltip zeigt Anzahl zugeordneter Dinge.

## UX (Code)

- [x] **#5 – Suche: Raum-Dropdown ohne Zone-Kontext**
  `app/templates/suchen.html`
  Fix: Optionstext als `Zone / Raum` angezeigt, JS-Kaskade filtert weiterhin per `data-zone`.

- [x] **#6 – Suchergebnis: unvollständiger Standort-Pfad**
  `app/models/inventar.py` (`standort_beschreibung()`)
  Fix: Gibt jetzt vollständigen Pfad zurück, z.B. "UG → Werkstatt → Werkbank".

## Datenfehler

- [x] **#7 – Trailing Space: "Karton-Stoffkiste " (Behälter ID 36, Feld `typ`)**
  Fix: `UPDATE behaelter SET typ = trim(typ)` – direkt in DB korrigiert.

- [ ] **#8 – Werkstattwagen-Schubladen mit Zahlen-Präfix**
  Behälter heissen "1 Schraubenzieher", "2 Zangen Hammer" etc.
  Zahlen sind Schubladennummern, sehen aber wie Anzahl aus.
  → Offen: manuell umbenennen oder so belassen?
