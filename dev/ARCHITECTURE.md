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
├── name                # Stable English asset key, e.g. "milk"
├── name_de             # German UI name, e.g. "Milch"
├── price               # Preis in Talern
├── category            # kuehlregal, obst, backwaren...
├── image_path          # Asset key
└── has_barcode         # True = scanner, False = touch picker

users
├── card_id (PK)        # Barcode der Kinderkarte
├── name                # "Carolin"
├── balance             # Aktuelles Guthaben in Talern
├── color               # UI-Farbe (#3B82F6)
├── difficulty          # 1-3 für Rechenspiele
└── is_admin            # Admin-Rechte?

sessions                # Phase 4.5: Arbeits-Sessions (Login → Logout)
├── id (PK)
├── user_card_id (FK)
├── started_at          # Session-Start
└── ended_at            # Session-Ende (NULL wenn aktiv)

earnings                # Phase 4.5: Verdienst-Einträge (pro Aktivität)
├── id (PK)
├── session_id (FK)
├── user_card_id (FK)
├── source              # 'math', 'cashier', 'time'
├── amount              # Taler verdient
├── description         # z.B. "3 Aufgaben gelöst"
└── earned_at           # Zeitstempel

transactions            # Einkäufe
├── id (PK)
├── user_card_id (FK)
├── total               # Gesamtbetrag in Talern
├── items_json          # JSON: [{barcode, name, qty, price}]
└── timestamp           # Zeitstempel
```

### 4. Admin Backend

FastAPI provides the parent-facing admin surface. It should stay separate from
pygame scene state:

```text
src/admin/server.py
  ↓
src/utils/database.py      # persistence boundary
src/utils/barcodes.py      # EAN-13 conventions, SVG paths, barcode files
```

Current remote admin scope:

- product list with barcode SVG links
- user list with card barcode SVG links
- recipe list with ingredients and recipe barcode SVG links
- balance changes with a small manual adjustment history
- minimal product, user, and recipe edits
- A4 PDF print sheets for cards, recipes, and product labels

The pygame app has a separate on-device admin mode for quick parent work at the
register. Scanning the existing Admin card opens `AdminScene`; that scene can
start or stop the FastAPI server process, show the current home-network URL as a
QR code, and adjust existing user balances without leaving the kiosk.

Further CRUD should be added in small slices. View/form orchestration belongs in
`src/admin/`, persistence belongs in `src/utils/database.py` or future smaller
database modules, and barcode file naming/generation belongs in
`src/utils/barcodes.py`.

### 5. Barcode Rules

Internal EAN-13 prefixes:

| Prefix | Meaning |
|--------|---------|
| `100` | Products |
| `200` | User cards |
| `300` | Recipe cards |

Generated SVGs live under `data/barcodes/{products,users,recipes}/`.

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

## Login System
Login (Badge-Scan)
    ↓
  state.start_session()  ← Timer startet hier
    ↓
  Menu (Auswahl)
    ↓
  ├── Scan (Einkauf) ← hier wird gescannt
  ├── Recipe         ← hier wird gescannt
  ├── MathGame       ← Verdienst durch Aufgaben
    ↓
  Logout
    ↓
  state.logout()  ← Timer endet hier

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

### Why Asset-First + Grid-Layout (Phase 6)?

**Problem:** Die App sieht aus wie "Developer-UI", nicht wie die handgezeichneten Mockups.

**Warum NICHT pygame-gui?**
- Pygame-GUI erwartet programmatische Widgets
- Handgezeichnete Assets (btn_green.png, icon_cart.png) passen nicht
- Overhead für Features die nicht gebraucht werden
- Lernkurve ohne Benefit

**Lösung: Eigenes Grid + Asset-Components**
- Assets sind schon im richtigen Stil vorhanden
- Volle Kontrolle über Asset-Rendering
- Einfaches System für ~10 UI-Komponenten
- Keine neue Dependency

---

## Asset-First Design Pattern

### Philosophie

```
Mockup (ui/*.png) → Identifiziere Assets → Baue Component → Positioniere im Grid
```

**Nicht:** "Wie baue ich einen Button mit pygame?"
**Sondern:** "Welches Asset nutze ich für diesen Button?"

### Asset-Kategorien

| Kategorie | Pfad | Verwendung |
|-----------|------|------------|
| **Buttons** | `assets/nobg/buttons/` | Interaktive Elemente |
| **Icons** | `assets/nobg/icons/` | Menu-Tiles, Indikatoren |
| **Frames** | `assets/nobg/frames/` | User-Rahmen (Farb-Coding) |
| **Products** | `assets/M/products/` | Warenkorb, Picker |
| **Tiles** | `assets/nobg/menue/` | Hauptmenü-Kacheln |

### Component-Asset-Mapping

| Component | Asset(s) | Beschreibung |
|-----------|----------|--------------|
| `ImageButton` | btn_green/red/brown.png | Button mit Text-Overlay |
| `IconTile` | menue/*.png | Menu-Kachel wie Mockup |
| `CartTable` | (neu zu erstellen) | Warenkorb-Tabelle |
| `PriceDisplay` | (neu: orange Banner) | Summen-Anzeige |
| `NumpadKey` | (neu: digit buttons) | Calculator-Style |

### Grid-Layout System

```python
# Konzept (noch zu implementieren)
grid = GridLayout(cols=4, rows=3, padding=20)
grid.place(button, col=0, row=0)        # Einzelne Zelle
grid.place(cart, col=1, row=0, colspan=2)  # Mehrere Spalten
```

**Debug-Modus:** Grid-Linien sichtbar machen für Entwicklung.

## Conventions

- **Scenes** handle their own input, update, render
- **Components** are reusable UI pieces (buttons, lists)
- **Utils** are stateless helpers
- **Assets** vorskaliert in S/M/L, geladen beim Startup, gecached in dict

---

## Code Patterns

### ClickableMixin (Components)

Standardisiertes Click-Handling für UI-Komponenten:

```python
from src.components.mixins import ClickableMixin

class MyButton(ClickableMixin):
    def __init__(self):
        self._pressed = False  # Required!
        self.rect = pygame.Rect(...)

    def handle_event(self, event):
        return self._handle_click(event, self.rect, self.on_click)
        # Oder mit Args: self._handle_click(event, self.rect, self.on_click, item_id)
```

### MessageMixin (Scenes)

Temporäre Feedback-Messages mit optionaler Farbe:

```python
from src.scenes.mixins import MessageMixin

class MyScene(MessageMixin, Scene):
    def update(self):
        self._update_message_timer()

    def render(self, screen):
        self._render_message(screen, font, x, y, center_x=True)

    def some_action(self):
        self._show_message("Erfolg!", 90, color=SUCCESS)  # Grün, 3 Sekunden
```

### FontRegistry

Zentrale, gecachte Font-Verwaltung:

```python
from src.utils.fonts import Fonts

font = Fonts.title()      # 42pt - Headers
font = Fonts.body()       # 36pt - Regular text
font = Fonts.small()      # 28pt - Hints
font = Fonts.get(None, 72)  # Custom size
```

### Scene Navigation

Base Class bietet Navigation-Helpers:

```python
class MyScene(Scene):
    def some_action(self):
        self._go_to("menu")  # Request scene change

    def handle_event(self, event):
        # ... handle events ...
        return self._consume_next_scene()  # Get and clear pending transition
```

### Database Context Manager

Garantiert Connection-Cleanup:

```python
from src.utils.database import get_db

def my_query():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM products")
        return cursor.fetchall()
    # Connection wird automatisch geschlossen
```

### Session & Earnings (Phase 4.5)

Zentrales State-Management für Sessions und Verdienste:

```python
from src.utils import state
from src.constants import EARNING_MATH

# Login startet Session automatisch
state.start_session(user)  # Erstellt DB-Session, setzt current_user

# Verdienst tracken (schreibt in DB + aktualisiert Balance)
state.add_earning("math", EARNING_MATH[difficulty], "Aufgabe gelöst")
state.add_earning("cashier", 1, f"Kunde bedient ({items} Artikel)")
state.add_earning("time", 1, "10 Min Anwesenheit")

# Balance nach Transaktion aktualisieren
state.refresh_current_user()  # Holt User mit neuer Balance aus DB
```

**Wirtschaftssystem-Konstanten:**
```python
BALANCE_BAR_MAX = 50           # Voller Balken = 50 Taler
EARNING_MATH = {1: 1, 2: 2, 3: 3}  # Leicht/Mittel/Schwer
EARNING_CASHIER = 5            # 5 Taler pro Kassieren
EARNING_RECIPE = 8             # 8 Taler pro Rezept
EARNING_TIME_SECONDS = 600     # 10 Min = 1 Taler
```

### CheckoutMixin (Scenes)

Wiederverwendbarer Checkout-Flow für Shopping-Scenes:

```python
from src.scenes.checkout_mixin import CheckoutMixin

class MyShoppingScene(CheckoutMixin, MessageMixin, Scene):
    def _init_ui(self):
        self._init_checkout_ui()  # Mixin-Init

    # Pflicht-Implementierungen:
    def _get_checkout_total(self) -> int:
        return self._cart.total

    def _get_checkout_items(self) -> list[dict]:
        return [{"barcode": ..., "name": ..., "qty": ..., "price": ...}]

    def _on_checkout_complete(self) -> None:
        self._cart.clear()

    # Nutzung in handle_event:
    def handle_event(self, event):
        if self._handle_checkout_event(event):
            return self._consume_next_scene()
        if self._checkout_mode:
            self._handle_checkout_barcode(barcode)

    # Nutzung in update/render:
    def update(self):
        self._update_checkout_ui()

    def render(self, screen):
        self._render_checkout_overlays(screen)
```

### InactivityMonitor (Auto-Shutdown)

Überwacht User-Aktivität und fährt System nach Timeout herunter:

```python
from src.components.inactivity_monitor import InactivityMonitor

# In main.py
monitor = InactivityMonitor()

# Game Loop:
for event in pygame.event.get():
    if event.type in (KEYDOWN, MOUSEBUTTONDOWN, FINGERDOWN):
        monitor.register_activity()

monitor.update()  # Prüft Timeout
monitor.render(screen)  # Countdown-Overlay
```

### Global Time Bonus

Zeit-basierter Verdienst über alle Scenes hinweg:

```python
from src.utils import state

# In jeder Scene.update():
def update(self):
    bonus = state.check_time_bonus()
    if bonus:
        self._show_message("+1 Taler! (10 Min Anwesenheit)")
```

### Asset Pipeline (Dreischritt)

```
assets/master/        →  assets/nobg/         →  assets/S/, M/, L/
(Original, NIEMALS      (Hintergrund           (skaliert: 30/60/120px)
 verändern!)             entfernt)
```

**Schritt 1:** Hintergrund entfernen
**Schritt 2:** Skalieren in drei Größen

**Ausnahmen:**
- `buttons/` — bereits transparent, direkt skalieren
- `frames/` — bereits transparent, NICHT skalieren (UI-Rahmen, volle Größe)

**Loader-Aufrufe:**
```python
assets.get("products/milk", "M")  →  assets/M/products/milk.png
assets.get("frames/red")          →  assets/nobg/frames/red.png  # keine Größe
```

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
│  │  • Heim-WLAN bleibt aktiv                                    │   │
│  │  • FastAPI-Server starten/stoppen (Port 8080)                │   │
│  │  • UI zeigt IP, Admin-URL, QR-Code und Kontoübersicht        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  Netzwerk     │         │ FastAPI Server  │         │  pygame UI    │
│               │         │               │         │               │
│ • Heim-WLAN   │         │ • /products   │         │ • IP anzeigen │
│ • lokale IP   │         │ • /users      │         │ • QR-Code     │
│ • kein Hotspot│         │ • /printables │         │ • Guthaben    │
└───────────────┘         │ • /scan       │         └───────────────┘
                          └───────────────┘
```

### Data Pipeline: Initial Setup → SQLite

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  seed_database.py   │────▶│      kasse.db       │────▶│  pygame + admin    │
│  (initial setup)    │     │      (SQLite)       │     │  runtime usage     │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
          │
          │                 ┌─────────────────────┐     ┌─────────────────────┐
          └────────────────▶│ generate_barcodes.py│────▶│   data/barcodes/    │
                            │ (SVG generation)    │     │   (SVG files)       │
                            └─────────────────────┘     └─────────────────────┘

There is one local SQLite database. `tools/seed_database.py` contains the
current Carolin/Annelie family setup and initializes a missing or empty DB. The
default setup path is non-destructive and must not overwrite runtime balances,
sessions, earnings, or transactions. A full rebuild is only allowed through an
explicit reset command.
```

### Admin Web-UI Flow

```
[Eltern-Handy] ──Heim-WLAN──▶ [Pi] ──HTTP──▶ [FastAPI @ :8080]
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
| Transaktion stornieren | ❌ | ✅ | Noch nicht umgesetzt |
| Statistiken | ❌ | ✅ | Charts, Export |
| Mathe-Schwierigkeit | ✅ | ✅ | Pro Kind einstellbar |

Admin access is intentionally kept simple for now: the kiosk flow is gated by
the Admin card barcode. No separate web login, Basic Auth, or PIN is planned in
the KISS version.

**Guthaben aufladen an der Kasse (Quick-Flow):**
```
[Admin-Karte scannen] → Admin-Modus aktiv
[User & Konten öffnen] → Carolin/Annelie/Gast sehen
[+1/+5/+10 tippen] → Guthaben wird gespeichert
[Kopfzeile prüfen] → letzte manuelle Änderung sehen
```

---

## Erweiterte Projektstruktur

```
tools/
├── generate_barcodes.py   # DB → Barcode SVGs (python-barcode)
├── seed_database.py       # Initial setup → SQLite
└── generate_printables.py # DB → A4 PDF sheets

data/
├── barcodes/              # Generierte Barcode-Bilder (EAN-13 SVGs)
└── kasse.db               # Lokale SQLite-Datenbank

assets/
├── master/                # Original-Assets (NIEMALS verändern!)
├── nobg/                  # Hintergrund entfernt (via /img)
├── S/                     # Skaliert 30×30 (via /img)
├── M/                     # Skaliert 60×60 (via /img)
└── L/                     # Skaliert 120×120 (via /img)

src/
├── admin/                 # Admin-Server
│   ├── server.py          # FastAPI App + Jinja2
│   ├── templates/         # Jinja2 Templates
│   └── static/            # CSS
├── scenes/
│   └── admin.py           # On-device Admin scene
└── utils/
    ├── admin_runtime.py   # FastAPI process start/stop
    └── network.py         # Local IP and admin URL helpers
```

## Design Decisions (Admin-System)

### Why FastAPI + Jinja2?
- **FastAPI**: Modern, async, auto-generierte API-Docs, Pydantic-Validation
- **Jinja2**: Server-side Templates, kein Build-Step nötig
- **Kein separates Frontend**: Alles in einem Python-Prozess, einfaches Deployment
- **Pygame-Admin separat**: Direkte Kassenarbeit bleibt im Kiosk und startet den Remote-Admin nur bei Bedarf

### Why python-barcode?
- Einfache API: `barcode.get('ean13', '123...').save('file')`
- Generiert SVGs für den aktuellen Barcode-Workflow
- Keine externen Dependencies
