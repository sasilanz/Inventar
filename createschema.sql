-- ========================================
-- InventarDB Schema (KORRIGIERT)
-- ========================================

-- Zone (Stockwerk/Bereich)
CREATE TABLE zone (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  beschreibung TEXT,
  qr_code VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raum
CREATE TABLE raum (
  id SERIAL PRIMARY KEY,
  zone_id INT NOT NULL REFERENCES zone(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  beschreibung TEXT,
  qr_code VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(zone_id, name)
);

-- Gestell
CREATE TABLE gestell (
  id SERIAL PRIMARY KEY,
  raum_id INT NOT NULL REFERENCES raum(id) ON DELETE CASCADE,
  typ VARCHAR(100),
  name VARCHAR(100) NOT NULL,
  beschreibung TEXT,
  qr_code VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Regalfach
CREATE TABLE regalfach (
  id SERIAL PRIMARY KEY,
  gestell_id INT NOT NULL REFERENCES gestell(id) ON DELETE CASCADE,
  bezeichnung VARCHAR(100) NOT NULL,
  position_index INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Behälter
CREATE TABLE behaelter (
  id SERIAL PRIMARY KEY,
  typ VARCHAR(100),
  name VARCHAR(255) NOT NULL,
  raum_id INT REFERENCES raum(id) ON DELETE SET NULL,
  regalfach_id INT REFERENCES regalfach(id) ON DELETE SET NULL,
  beschreibung TEXT,
  qr_code VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK ((raum_id IS NOT NULL AND regalfach_id IS NULL) OR
         (raum_id IS NULL AND regalfach_id IS NOT NULL) OR
         (raum_id IS NULL AND regalfach_id IS NULL))
);

-- Kategorie
CREATE TABLE kategorie (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  beschreibung TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tag
CREATE TABLE tag (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ding (Haupttabelle)
CREATE TABLE ding (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  beschreibung TEXT,
  raum_id INT REFERENCES raum(id) ON DELETE SET NULL,
  gestell_id INT REFERENCES gestell(id) ON DELETE SET NULL,
  regalfach_id INT REFERENCES regalfach(id) ON DELETE SET NULL,
  behaelter_id INT REFERENCES behaelter(id) ON DELETE SET NULL,
  kategorie_id INT REFERENCES kategorie(id) ON DELETE SET NULL,
  hersteller VARCHAR(255),
  modell VARCHAR(255),
  seriennummer VARCHAR(255),
  kaufdatum DATE,
  kaufpreis NUMERIC(10, 2),
  waehrung VARCHAR(3) DEFAULT 'CHF',
  garantie_bis DATE,
  versichert_bei VARCHAR(255),
  versicherungsnummer VARCHAR(255),
  ersatzwert_geschaetzt NUMERIC(10, 2),
  zustand VARCHAR(100),
  qr_code VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ding-Tag Verknüpfung
CREATE TABLE ding_tag (
  ding_id INT NOT NULL REFERENCES ding(id) ON DELETE CASCADE,
  tag_id INT NOT NULL REFERENCES tag(id) ON DELETE CASCADE,
  PRIMARY KEY (ding_id, tag_id)
);

-- Medium (Foto, Beleg, Anleitung)
CREATE TABLE medium (
  id SERIAL PRIMARY KEY,
  ding_id INT NOT NULL REFERENCES ding(id) ON DELETE CASCADE,
  typ VARCHAR(50) CHECK (typ IN ('foto', 'beleg', 'anleitung', 'sonstiges')),
  pfad VARCHAR(512) NOT NULL,
  mime_type VARCHAR(100),
  extern_url TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Person (für Verleih)
CREATE TABLE person (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  kontakt TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Verleih
CREATE TABLE verleih (
  id SERIAL PRIMARY KEY,
  ding_id INT NOT NULL REFERENCES ding(id) ON DELETE CASCADE,
  person_id INT NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  ausgeliehen_am DATE NOT NULL DEFAULT CURRENT_DATE,
  faellig_am DATE,
  zurueckgegeben_am DATE,
  notiz TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bewegung (Umzugs-Historie)
CREATE TABLE bewegung (
  id SERIAL PRIMARY KEY,
  ding_id INT NOT NULL REFERENCES ding(id) ON DELETE CASCADE,
  von_raum_id INT REFERENCES raum(id) ON DELETE SET NULL,
  von_behaelter_id INT REFERENCES behaelter(id) ON DELETE SET NULL,
  von_regalfach_id INT REFERENCES regalfach(id) ON DELETE SET NULL,
  zu_raum_id INT REFERENCES raum(id) ON DELETE SET NULL,
  zu_behaelter_id INT REFERENCES behaelter(id) ON DELETE SET NULL,
  zu_regalfach_id INT REFERENCES regalfach(id) ON DELETE SET NULL,
  grund VARCHAR(255),
  zeitpunkt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  benutzer VARCHAR(100)
);

-- Trigger für updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ding_updated_at
    BEFORE UPDATE ON ding
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indizes für Performance
CREATE INDEX idx_raum_zone ON raum(zone_id);
CREATE INDEX idx_gestell_raum ON gestell(raum_id);
CREATE INDEX idx_regalfach_gestell ON regalfach(gestell_id);
CREATE INDEX idx_behaelter_raum ON behaelter(raum_id);
CREATE INDEX idx_behaelter_regalfach ON behaelter(regalfach_id);
CREATE INDEX idx_ding_raum ON ding(raum_id);
CREATE INDEX idx_ding_behaelter ON ding(behaelter_id);
CREATE INDEX idx_ding_kategorie ON ding(kategorie_id);
CREATE INDEX idx_medium_ding ON medium(ding_id);
CREATE INDEX idx_verleih_ding ON verleih(ding_id);
CREATE INDEX idx_verleih_person ON verleih(person_id);
CREATE INDEX idx_bewegung_ding ON bewegung(ding_id);

-- ========================================
-- INITIALE MASTERDATEN
-- ========================================

-- Zonen einfügen
INSERT INTO zone (name, beschreibung) VALUES
('UG', 'Untergeschoss'),
('EG', 'Erdgeschoss'),
('Garten', 'Aussenbereich'),
('OG', 'Obergeschoss'),
('DG', 'Dachgeschoss');

-- Räume UG
INSERT INTO raum (zone_id, name) VALUES
((SELECT id FROM zone WHERE name='UG'), 'Werkstatt'),
((SELECT id FROM zone WHERE name='UG'), 'Lager'),
((SELECT id FROM zone WHERE name='UG'), 'Garage'),
((SELECT id FROM zone WHERE name='UG'), 'Vorratsraum'),
((SELECT id FROM zone WHERE name='UG'), 'Heizraum'),
((SELECT id FROM zone WHERE name='UG'), 'Kreml');

-- Räume EG
INSERT INTO raum (zone_id, name) VALUES
((SELECT id FROM zone WHERE name='EG'), 'Wohnzimmer'),
((SELECT id FROM zone WHERE name='EG'), 'Schlafzimmer'),
((SELECT id FROM zone WHERE name='EG'), 'Küche'),
((SELECT id FROM zone WHERE name='EG'), 'Bad'),
((SELECT id FROM zone WHERE name='EG'), 'Arbeitszimmer');

-- Räume Garten
INSERT INTO raum (zone_id, name) VALUES
((SELECT id FROM zone WHERE name='Garten'), 'Terrasse'),
((SELECT id FROM zone WHERE name='Garten'), 'Gartenhaus'),
((SELECT id FROM zone WHERE name='Garten'), 'Aussenkiste');

-- Räume OG
INSERT INTO raum (zone_id, name) VALUES
((SELECT id FROM zone WHERE name='OG'), 'Wohnzimmer'),
((SELECT id FROM zone WHERE name='OG'), 'Küche'),
((SELECT id FROM zone WHERE name='OG'), 'Bad'),
((SELECT id FROM zone WHERE name='OG'), 'Asi-Zimmer'),
((SELECT id FROM zone WHERE name='OG'), 'grosse Terrasse'),
((SELECT id FROM zone WHERE name='OG'), 'Eingangsterrasse');

-- Räume DG
INSERT INTO raum (zone_id, name) VALUES
((SELECT id FROM zone WHERE name='DG'), 'Bad'),
((SELECT id FROM zone WHERE name='DG'), 'Schlafzimmer'),
((SELECT id FROM zone WHERE name='DG'), 'Sandra-Zimmer'),
((SELECT id FROM zone WHERE name='DG'), 'Terrasse');

-- Standard-Kategorien
INSERT INTO kategorie (name) VALUES
('Maschinen und Elektrowerkzeug'),
('Werkzeug'),
('Montagematerial'),
('Elektro und Lampen'),
('Möbel'),
('Musik'),
('Velo und Zubehör'),
('Reinigung und Pflege'),
('Kinder'),
('Bastel und Geschenkmaterial'),
('Kunst und Malen'),
('IT'),
('Foto und Zubehör'),
('Textilien'),
('Reisegepäck'),
('Haushalt'),
('Dokumente'),
('Sport'),
('Camping'),
('Sonstiges');

-- Standard-Tags
INSERT INTO tag (name) VALUES
('versichert'),
('Garantie läuft ab'),
('im Einsatz'),
('Archiv'),
('verliehen'),
('defekt');
