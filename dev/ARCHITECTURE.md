# Architecture

## Hardware (Bestellt ✅)

| Komponente | Modell | Specs |
|------------|--------|-------|
| **Computer** | Raspberry Pi Zero 2 W | Quad-Core A53, 512MB RAM, WiFi |
| **Display** | Elecrow 7" IPS Touch | 1024x600, kapazitiv, HDMI+USB |
| **Stromversorgung** | Anker 20K 87W (A1383) | Pass-Through, ~20h Laufzeit |
| **Video-Kabel** | CY Mini-HDMI Flachkabel | 20cm, Pi → Display |

**Auflösung**: 1024x600 (statt ursprünglich geplanter 800x480)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                               │
│                      (Entry Point)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     Game Loop                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │  Input   │→ │  Update  │→ │  Render  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Input Manager │ │ Scene Manager │ │   Database    │
│               │ │               │ │               │
│ • Barcode     │ │ • Login       │ │ • Products    │
│ • Numpad      │ │ • Menu        │ │ • Users       │
│ • Touch       │ │ • Scan        │ │ • Transactions│
│               │ │ • Cart        │ │               │
└───────────────┘ │ • Checkout    │ └───────────────┘
                  │ • Recipe      │
                  │ • MathGame    │
                  │ • Admin       │
                  └───────────────┘
```

## Key Abstractions

### 1. Scene Manager
State machine for screens. One active scene at a time.

```python
# Conceptual
scenes = {
    "login": LoginScene,
    "menu": MenuScene,
    "scan": ScanScene,
    ...
}
current_scene.handle_input(event)
current_scene.update()
current_scene.render(screen)
```

### 2. Input Manager
Unified input from three sources → normalized events.

```python
# Raw inputs
USB Barcode Scanner → keyboard events (string + Enter)
USB Numpad → keyboard events (0-9, *, #, Enter)
Touchscreen → mouse events

# Normalized to
InputEvent(type="barcode", value="4006381...")
InputEvent(type="numpad", value="5")
InputEvent(type="touch", position=(400, 240))
```

### 3. Database (SQLite)

```
products
├── barcode (PK)        # EAN-13 oder custom
├── name                # "Milch"
├── price               # Preis in Talern
├── category            # Kühlregal, Obst, Backwaren...
├── emoji               # 🥛 für schnelle visuelle ID
├── image_path          # Pfad zum Produktbild
├── is_scannable        # True = Barcode, False = Touch-Picker
└── active              # Produkt verfügbar?

users
├── card_id (PK)        # Barcode der Kinderkarte
├── name                # "Carolin"
├── balance             # Aktuelles Guthaben in Talern
├── color               # UI-Farbe (#3B82F6)
├── emoji               # Avatar-Emoji
├── is_admin            # Admin-Rechte?
├── math_difficulty     # 1-3 für Rechenspiele
└── created_at          # Registriert am

transactions
├── id (PK)
├── user_id (FK)
├── timestamp
├── total
└── items               # JSON: [{barcode, qty, price}]
```

## Data Flow

```
[Scan Barcode] → Input Manager → Scene receives event
                                        │
                    ┌───────────────────┘
                    ▼
            Scene looks up product in DB
                    │
                    ▼
            Scene updates cart state
                    │
                    ▼
            Scene re-renders UI
```

## Current Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Entry Point | ✅ Stub | `main.py` |
| Scene Manager | 🔲 | `src/scenes/` |
| Input Manager | 🔲 | `src/utils/input.py` |
| Database | 🔲 | `src/utils/database.py` |
| UI Components | 🔲 | `src/components/` |
| Scenes | 🔲 | `src/scenes/*.py` |
| **Data & Tools** | | |
| YAML Definitions | 🔲 | `data/*.yaml` |
| Barcode Generator | 🔲 | `tools/generate_barcodes.py` |
| DB Seed Script | 🔲 | `tools/seed_database.py` |
| **Admin System** | | |
| Admin Scene | 🔲 | `src/scenes/admin.py` |
| WiFi Hotspot | 🔲 | `src/utils/wifi.py` |
| FastAPI Server | 🔲 | `src/admin/server.py` |
| Admin Web-UI | 🔲 | `src/admin/templates/` |

## Design Decisions

### Why pygame?
- Runs on Pi Zero (no browser overhead)
- Full control over rendering
- Simple input handling
- Kids don't need web features

### Why SQLite?
- Zero setup
- File-based (easy backup)
- Sufficient for single-user app
- Python built-in support

### Why Scene-based?
- Clear separation of screens
- Each scene owns its state
- Easy to add new modes
- Simple mental model

## Conventions

- **Scenes** handle their own input, update, render
- **Components** are reusable UI pieces (buttons, lists)
- **Utils** are stateless helpers
- **Assets** loaded once at startup, cached globally

---

## Admin-Modus Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Admin-Karte wird gescannt                        │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Admin Scene aktiviert                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  • WiFi-Hotspot starten (wpa_supplicant → hostapd)           │   │
│  │  • FastAPI-Server starten (Port 8080)                           │   │
│  │  • UI zeigt: SSID, Passwort, IP (192.168.4.1)                │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  WiFi Modul   │         │ FastAPI Server  │         │  pygame UI    │
│               │         │               │         │               │
│ • hostapd     │         │ • /products   │         │ • SSID anzeigen│
│ • dnsmasq     │         │ • /users      │         │ • IP anzeigen │
│ • IP: .4.1    │         │ • /barcodes   │         │ • Status      │
└───────────────┘         │ • /scan       │         └───────────────┘
                          └───────────────┘
```

### Data Pipeline: YAML → SQLite

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   products.yaml     │     │  seed_database.py   │     │     kasse.db        │
│   users.yaml        │────▶│  (Import-Tool)      │────▶│   (SQLite)          │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
         │
         │                  ┌─────────────────────┐     ┌─────────────────────┐
         └─────────────────▶│ generate_barcodes.py│────▶│   data/barcodes/    │
                            │  (Barcode-Generator)│     │   (PNG-Dateien)     │
                            └─────────────────────┘     └─────────────────────┘

Single Source of Truth: YAML-Dateien
→ DB wird bei Bedarf neu generiert
→ Barcodes werden für den Druck generiert
```

### Admin Web-UI Flow

```
[Eltern-Handy] ──WiFi──▶ [Pi Hotspot] ──HTTP──▶ [FastAPI @ :8080]
                                                       │
                         ┌─────────────────────────────┘
                         ▼
           ┌──────────────────────────┐
           │    Admin Web-UI          │
           ├──────────────────────────┤
           │ • Produkte verwalten     │
           │ • User verwalten         │
           │ • Barcodes scannen       │
           │ • Barcodes generieren    │
           │ • Guthaben aufladen      │
           └──────────────────────────┘
```

### Admin-Bereiche (Web-UI)

| Bereich | Funktionen |
|---------|------------|
| 📦 **Produkte** | Liste, Anlegen, Bearbeiten, Bild-Upload, Barcode generieren/drucken |
| 👤 **Benutzer** | Liste, Guthaben einsehen, Mathe-Schwierigkeit einstellen |
| 💰 **Guthaben** | Aufladen (einzeln oder Batch für alle) |
| 🧾 **Transaktionen** | Verlauf einsehen, Statistiken, Stornieren |
| 🎮 **Einstellungen** | Lohn-Sätze, Kassiererin-Modus-Config |
| 📊 **Dashboard** | Übersicht: Wer hat wie viel, letzte Aktivität |

### Funktionsaufteilung: Kasse vs. Web-UI

| Funktion | Kasse (pygame) | Web-UI | Anmerkung |
|----------|:--------------:|:------:|-----------|
| Guthaben aufladen | ✅ | ✅ | Kasse: schnell für Alltag |
| Guthaben einsehen | ✅ | ✅ | Nach Login sichtbar |
| Neuen User anlegen | ❌ | ✅ | Nur Admin |
| Produkt anlegen | ❌ | ✅ | Mit Bild-Upload |
| Barcode zuordnen | ✅ | ✅ | Kasse: Scan-Modus |
| Barcode generieren | ❌ | ✅ | Mit Druck-Option |
| Transaktion stornieren | ✅ | ✅ | Kasse: nur letzte |
| Statistiken | ❌ | ✅ | Charts, Export |
| Mathe-Schwierigkeit | ❌ | ✅ | Pro Kind einstellbar |

**Guthaben aufladen an der Kasse (Quick-Flow):**
```
[Admin-Karte scannen] → Admin-Modus aktiv
[Kind-Karte scannen] → "Carolin: 5 Taler"
[Numpad: 10] → "Aufladen: +10 Taler?"
[Enter] → "Carolin: 15 Taler ✓"
```

---

## Erweiterte Projektstruktur

```
tools/
├── generate_barcodes.py   # YAML → Barcode-PNGs (python-barcode)
├── seed_database.py       # YAML → SQLite
└── start_admin.sh         # WiFi-Hotspot + FastAPI starten

data/
├── products.yaml          # Produkt-Definitionen (Source of Truth)
├── users.yaml             # User-Definitionen (Source of Truth)
├── barcodes/              # Generierte Barcode-Bilder (EAN-13 PNGs)
└── kasse.db               # SQLite (generiert aus YAML)

assets/
└── products/              # Produkt-Bilder (Upload via Web-UI)

src/
├── admin/                 # Admin-Server
│   ├── server.py          # FastAPI App + Jinja2
│   ├── routes.py          # API Endpoints
│   ├── templates/         # Jinja2 Templates + HTMX
│   └── static/            # CSS, JS (minimal)
├── scenes/
│   └── admin.py           # Admin-Scene (zeigt SSID/IP)
└── utils/
    └── wifi.py            # WiFi-Hotspot Toggle (hostapd/dnsmasq)
```

## Design Decisions (Admin-System)

### Why FastAPI + Jinja2 + HTMX?
- **FastAPI**: Modern, async, auto-generierte API-Docs, Pydantic-Validation
- **Jinja2**: Server-side Templates, kein Build-Step nötig
- **HTMX**: Interaktivität ohne JavaScript-Framework, partial page updates
- **Kein separates Frontend**: Alles in einem Python-Prozess, einfaches Deployment

### Why python-barcode?
- Einfache API: `barcode.get('ean13', '123...').save('file')`
- Generiert PNG/SVG
- Keine externen Dependencies
