# Carolin's Kasse - Konzept-Dokument

## Projektvision

Eine spielerische Selbstbedienungskasse für den Holz-Kaufladen, die Kindern (4-8 Jahre) Einkaufen, Rechnen und Verantwortung beibringt. Inspiriert von Supermarkt-Selbstbedienungskassen, aber im Tante-Emma-Spielmodus betrieben.

---

## Spielmodi

### 1. Freier Einkaufs-Modus
- Kunde scannt Kundenkarte → kauft beliebige Produkte → bezahlt
- Keine Vorgaben, freies Spiel

### 2. Rezept-Modus
- Rezept-Karte wird gescannt → Checkliste erscheint
- Kind sammelt & scannt die benötigten Zutaten
- **Falsches Produkt** → Fehlerton + Hinweis
- **Reihenfolge** → beliebig
- **Abschluss** → Pling + Haken + Belohnungs-Animation

### 3. Kassiererin-Modus
- Kind arbeitet als Kassierer/in im Tante-Emma-Stil
- Andere Kinder/Erwachsene sind "Kunden"
- Kassiererin sucht Waren raus, scannt, kassiert
- **Lohn:** Stundenlohn + Bonus pro erfolgreicher Transaktion
- **Anti-Hack:** Inaktivitätserkennung (kein Lohn ohne echte Nutzung)
- **Visualisierung:** Taler-Counter oben in der Ecke

### 4. Rechen-Spiel
- Geld verdienen durch Mathe-Aufgaben
- **Altersgruppe 4-8 Jahre:**
  - Einfach (Carolin, 4J): Punkte zählen, Zahl zuordnen (●●●● = 4)
  - Mittel: 2 + 2 = ? (mit visuellen Punkten)
  - Schwer (Annelie): 5 + 5, 2 × 3
- **Schwierigkeit = Belohnung:** Schwere Aufgaben geben mehr Taler
- **Personalisiert:** Eltern stellen Schwierigkeit pro Kind im Admin ein
- **Eingabe:** Nummernpad

---

## Rezepte (5 Stück, je 3-5 einfache Zutaten)

| Rezept | Zutaten |
|--------|---------|
| **Pfannkuchen** | Milch, Eier, Mehl, Zucker |
| **Nudeln mit Tomatensauce** | Nudeln, Tomaten, Käse |
| **Nudeln mit Käsesauce** | Nudeln, Käse, Milch, Butter |
| **Haferflocken mit Kirschen** | Haferflocken, Kirschen, Milch |
| **Kuchen** | Mehl, Eier, Zucker, Butter, Milch |

---

## Produkt-Katalog (Dummy-Daten)

### Grundnahrungsmittel (mit Barcode)
| Produkt | Preis | Kategorie |
|---------|-------|-----------|
| Milch | 1 T | Kühlregal |
| Eier (6er) | 2 T | Kühlregal |
| Butter | 1 T | Kühlregal |
| Käse | 2 T | Kühlregal |
| Mehl | 1 T | Backzutaten |
| Zucker | 1 T | Backzutaten |
| Haferflocken | 1 T | Frühstück |
| Nudeln | 1 T | Vorrat |
| Tomaten (Dose) | 1 T | Vorrat |
| Limonade | 2 T | Getränke |
| Saft | 2 T | Getränke |
| Wurst | 2 T | Kühlregal |
| Brot | 1 T | Backwaren |

### Obst (Touch-Auswahl, pro Stück)
| Produkt | Preis |
|---------|-------|
| Banane | 0.5 T |
| Apfel | 0.5 T |
| Orange | 0.5 T |
| Kirschen | 1 T |
| Trauben | 1 T |
| Birne | 0.5 T |

### Gemüse (Touch-Auswahl, pro Stück)
| Produkt | Preis |
|---------|-------|
| Tomate | 0.5 T |
| Gurke | 0.5 T |
| Karotte | 0.5 T |
| Paprika | 1 T |
| Salat | 1 T |
| Zwiebel | 0.5 T |

### Backwaren (Touch-Auswahl)
| Produkt | Preis |
|---------|-------|
| Brötchen | 0.5 T |
| Croissant | 1 T |
| Brezel | 0.5 T |

**Preislogik:** Günstig gehalten (0.5-2 Taler), damit 10 Taler Startguthaben für einen schönen Einkauf reichen.

---

## Benutzer-System

### Feste Benutzer
| Name | Farbe | Symbol |
|------|-------|--------|
| Carolin | Blau | TBD |
| Annelie | Rot | TBD |

### Gast-Karten
- Startguthaben: 10 Taler
- Name eingeben beim ersten Scan
- Zurücksetzbar durch Admin

### Login-Flow
1. Karte scannen
2. Pop-up: "Hallo [Name]!" + Avatar
3. Farbiger Rand um gesamten Screen
4. Name + Symbol oben in der Ecke

---

## Guthaben-System

| Aspekt | Wert |
|--------|------|
| Währung | Taler |
| Startguthaben | 10 Taler |
| Persistenz | Permanent gespeichert |
| Verdienen | Rechenspiele, Kassiererin-Arbeit |

### Geld reicht nicht?
→ Fehlermeldung, Transaktion abgebrochen

---

## Barcode-Management

### Barcode-Typen
| Typ | Format | Beispiel |
|-----|--------|----------|
| Produkte | EAN-13 | 4006381333931 |
| Kinder-Karten | Custom (8-stellig) | CARD0001 |
| Admin-Karte | Custom | ADMIN001 |
| Rezept-Karten | Custom | RECIPE01 |

### Data Pipeline
```
YAML (Source of Truth)
    │
    ├──► seed_database.py ──► SQLite (Runtime)
    │
    └──► generate_barcodes.py ──► PNG-Dateien (Druck)
```

### YAML-Format (Beispiel)
```yaml
# data/products.yaml
products:
  - barcode: "4006381333931"
    name: "Milch"
    price: 1.0
    category: "Kühlregal"
    emoji: "🥛"
    is_scannable: true

# data/users.yaml
users:
  - card_id: "CARD0001"
    name: "Carolin"
    balance: 10.0
    color: "#3B82F6"
    emoji: "👧"
    math_difficulty: 1
```

### Barcode-Workflows
1. **Eigene Barcodes generieren**: YAML → generate_barcodes.py → PNG drucken
2. **Existierende Barcodes nutzen**: Produkt scannen → im Admin zuordnen

---

## Admin-System

### Zugang
- **Admin-Karte scannen** → Aktiviert Admin-Modus
- Pi startet **WiFi-Hotspot** (wird zum Access Point)
- **FastAPI-Server** startet auf Port 8080
- pygame-UI zeigt: SSID, Passwort, IP-Adresse

### Verbindung (Eltern-Handy)
```
1. WLAN: "CarolinsKasse" (WPA2)
2. Browser: http://192.168.4.1:8080
3. Admin Web-UI öffnet sich
```

### Web-UI Bereiche
| Bereich | Funktionen |
|---------|------------|
| 📊 Dashboard | Übersicht, letzte Aktivität |
| 📦 Produkte | Anlegen, Bearbeiten, Bild-Upload, Barcode generieren |
| 👤 Benutzer | Verwalten, Guthaben, Mathe-Schwierigkeit |
| 💰 Guthaben | Aufladen (einzeln/Batch) |
| 🧾 Transaktionen | Verlauf, Statistiken, Stornieren |
| 🎮 Einstellungen | Lohn-Sätze, System-Config |

### Quick-Admin an der Kasse (ohne Web-UI)
Für häufige Aktionen direkt am Gerät:
- **Guthaben aufladen**: Admin-Karte → Kind-Karte → Betrag → Enter
- **Barcode zuordnen**: Admin-Karte → Scan-Modus → Produkt scannen → Name eingeben
- **Letzte Transaktion stornieren**: Admin-Karte → Storno-Option

### Sicherheit
- Admin-Barcode geheim halten (nicht ausdrucken/aufkleben)
- WiFi mit WPA2-Passwort geschützt
- Auto-Timeout: Hotspot schließt nach 10 Min Inaktivität
- Kein Internet-Zugang über Hotspot (isoliert)

---

## Benötigte Screens / Mockups

### Vorhanden (in /ui)
1. Einkaufsliste mit Detail-Ansicht (Mengen +/-)
2. Weitere Mockups (müssen noch gesichtet und benannt werden)

### Noch zu erstellen
- **Startbildschirm** - Vor Login, "Karte scannen"
- **Login-Bestätigung** - "Hallo Carolin!" Pop-up
- **Hauptmenü** - Modus-Auswahl (Einkauf/Rezept/Rechenspiel/Kassiererin)
- **Rezept-Checkliste** - Benötigte Zutaten zum Abhaken
- **Obst/Gemüse/Backwaren-Picker** - Kategorien + Mengen-Auswahl
- **Bezahl-Screen** - Guthaben, Summe, Bestätigung
- **Rechenspiel** - Aufgabe + visuelle Punkte + Nummernpad
- **Kassiererin-Dashboard** - Taler-Counter, Aktivitätsstatus
- **Erfolgs-Animation** - Rezept abgeschlossen / Kauf erfolgreich
- **Fehler-Screens** - "Falsches Produkt", "Guthaben reicht nicht"
- **Admin-Panel** - Produkte, Benutzer, Einstellungen

---

## Entwicklungs-Phasen

### Phase 1: Foundation
- pygame-Fenster (800x480)
- Scene Manager
- Input-Abstraktion (Barcode, Numpad, Touch)
- Basis-UI-Komponenten

### Phase 1.5: Data & Barcode Setup
- YAML-Struktur für Produkte/User definieren
- Barcode-Generator Tool (python-barcode)
- DB-Seed Skript (YAML → SQLite)
- Test-Barcodes generieren

### Phase 2: Core Shopping
- Produkt-Datenbank
- Barcode scannen → Warenkorb
- Touch-Auswahl für Obst/Gemüse
- Bezahlen mit Karten-Guthaben

### Phase 3: Benutzer-System
- Login per Karte
- Farbige Ränder pro User
- Gast-Karten mit Namenseingabe

### Phase 4: Game Modes
- Rezept-Modus mit Checkliste
- Rechenspiele mit Schwierigkeitsstufen
- Kassiererin-Modus mit Lohn-System

### Phase 5: Admin-System
- **Kasse-Admin**: Guthaben aufladen, Barcode zuordnen, Storno
- **WiFi-Hotspot**: Pi wird zum Access Point
- **FastAPI-Server**: Web-UI Backend
- **Admin Web-UI**: Produkte, User, Statistiken, Bild-Upload

### Phase 6: Polish
- Sound-Effekte
- Animationen
- Pi Zero Performance-Optimierung

---

## Offene Details (für später)

1. **Lohn:** Wie viel pro Stunde / pro Transaktion?
2. **Rechenspiel:** Wie viele Aufgaben pro Runde? Zeitlimit?
3. **Symbole/Avatare:** Welche für Carolin & Annelie?
4. **Sound-Design:** Welche Sounds? (Piep, Pling, Fehler, Erfolg-Fanfare?)

*Diese Details können während der Entwicklung iterativ festgelegt werden.*
