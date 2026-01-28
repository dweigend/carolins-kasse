# Kinder-Kasse: Technische Dokumentation

## Projektziel

Interaktives Kassenspiel für Kinder auf Raspberry Pi Zero mit minimalem Ressourcenverbrauch. Die Kasse unterstützt vier Spielmodi: Freier Einkauf, Rezept-Modus, Kassiererin-Modus und Rechenspiele. Kinder scannen Produkte mit Barcode-Scanner, sehen visuelles Feedback und bezahlen mit ihrer persönlichen Guthaben-Karte.

---

## Hardware-Setup

### Bestellte Komponenten ✅

| Komponente | Modell | Preis | Status |
|------------|--------|-------|--------|
| **Computer** | Raspberry Pi Zero 2 W | 23€ | ✅ Bestellt |
| **Display** | Elecrow 7" IPS 1024x600 Touchscreen | 47€ | ✅ Bestellt |
| **Stromversorgung** | Anker Powerbank 20.000mAh 87W (A1383) | 40€ | ✅ Bestellt |
| **HDMI-Kabel** | CY Mini-HDMI auf HDMI Flachkabel 20cm | 9€ | ✅ Bestellt |
| **Barcode-Scanner** | USB (emuliert Tastatur) | TBD | 🔲 |
| **Nummernpad** | USB (numerische Eingabe) | TBD | 🔲 |
| **microSD-Karte** | 32GB Class 10 | ~8€ | 🔲 |

**Gesamt: ~135€** (ohne Scanner/Numpad)

### Hardware-Spezifikationen

#### Raspberry Pi Zero 2 W
- **CPU**: Quad-Core ARM Cortex-A53 @ 1GHz (5x schneller als Zero W!)
- **RAM**: 512 MB LPDDR2
- **WiFi**: 2.4 GHz 802.11 b/g/n
- **Bluetooth**: 4.2 / BLE
- **Video**: Mini-HDMI
- **Stromverbrauch**: ~120mA idle, ~600mA peak

#### Elecrow 7" Display
- **Auflösung**: 1024x600 (höher als geplante 800x480!)
- **Panel**: IPS (gute Blickwinkel)
- **Touchscreen**: Kapazitiv (5-Punkt)
- **Anschluss**: HDMI (Video) + Micro-USB (Touch + Strom)
- **Stromverbrauch**: ~400mA @ 5V

#### Anker Powerbank A1383
- **Kapazität**: 20.000 mAh
- **Ausgang**: 87W total (65W max pro Port)
- **Ports**: 1x USB-C (Ein/Aus), 1x USB-A, 1x integriertes USB-C Kabel
- **Pass-Through**: ✅ Ja (laden während Betrieb)
- **Display**: Digitale Prozent-Anzeige

### Stromverbrauch & Laufzeit

| Komponente | Verbrauch |
|------------|-----------|
| Pi Zero 2 W (Last) | ~300 mA |
| Elecrow Display | ~400 mA |
| **Gesamt** | **~700 mA (~3.5W)** |

| Powerbank-Kapazität | Nutzbar (5V) | Laufzeit |
|---------------------|--------------|----------|
| 20.000 mAh | ~14.800 mAh | **~20 Stunden** |

### Verkabelung

```
┌─────────────────────────────────────────┐
│         Anker Powerbank A1383           │
│                                         │
│  [Integriertes USB-C Kabel]             │
│         │                               │
│         └──► Pi Zero 2 W                │
│              (via USB-C auf Micro-USB)  │
│                                         │
│  [USB-A Port]                           │
│         │                               │
│         └──► Elecrow Display            │
│              (Micro-USB für Strom+Touch)│
│                                         │
│  [USB-C Port] ◄── Ladekabel             │
│                   (zum Aufladen)        │
└─────────────────────────────────────────┘

Plus: Mini-HDMI (Pi) ──► HDMI (Display)
      via CY Flachkabel 20cm
```

### Noch benötigt

| Teil | Zweck | Geschätzt |
|------|-------|-----------|
| USB-C auf Micro-USB Adapter | Pi Zero hat Micro-USB | ~3€ |
| USB-A auf Micro-USB Kabel | Display-Stromversorgung | ~5€ |
| microSD-Karte 32GB | OS + Daten | ~8€ |
| USB-Barcode-Scanner | Produkte/Karten scannen | ~15-30€ |
| USB-Nummernpad | Eingabe für Rechenspiele | ~10€ |

### OS-Setup
```bash
# Raspberry Pi OS Lite (KEIN Desktop!)
# Spart ~300MB RAM und Boot-Zeit

# Wichtig in /boot/config.txt:
dtoverlay=vc4-kms-v3d  # Hardware-beschleunigung

# Für 1024x600 Display:
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 3 0 0 0
```

---

## Tech Stack

### Gewählt: Pygame mit SDL2-KMSDRM

**Warum Pygame?**
- Python = schnelle Entwicklung
- Läuft OHNE X11/Desktop (direkt auf Framebuffer)
- Hardware-beschleunigtes Rendering via GPU
- ~150MB RAM statt 400MB+ mit Desktop
- Einfaches Event-Handling für Scanner/Keypad

**Alternativen verworfen:**
- Kivy: Zu heavy für Pi Zero, OpenGL ES overhead
- GUI-Frameworks (Tkinter, Qt): Brauchen X11
- C/C++: Zu aufwendig, keine schnelle Iteration

---

## Architektur-Übersicht

### Projektstruktur
```
carolins_kasse/
├── pyproject.toml              # uv project config
├── src/
│   ├── main.py                 # Game loop & entry point
│   ├── config.py               # Settings & constants
│   ├── database.py             # SQLite database layer
│   ├── input_manager.py        # Scanner/Keypad/Touch handling
│   ├── scenes/                 # Screen-basierte Architektur
│   │   ├── base_scene.py       # Abstract base class
│   │   ├── login_scene.py      # Karte scannen, Begrüßung
│   │   ├── menu_scene.py       # Modus-Auswahl
│   │   ├── scan_scene.py       # Hauptbildschirm (Scannen)
│   │   ├── recipe_scene.py     # Rezept-Modus mit Checkliste
│   │   ├── picker_scene.py     # Obst/Gemüse/Backwaren Auswahl
│   │   ├── payment_scene.py    # Bezahl-Bildschirm
│   │   ├── math_scene.py       # Rechenspiele
│   │   ├── cashier_scene.py    # Kassiererin-Modus
│   │   └── admin_scene.py      # Admin-Panel
│   ├── components/             # Wiederverwendbare UI
│   │   ├── product_card.py
│   │   ├── cart_display.py
│   │   ├── user_badge.py       # Name + Farbe oben rechts
│   │   ├── taler_counter.py    # Guthaben-Anzeige
│   │   └── popup.py            # "Hallo Carolin!" etc.
│   └── utils/
│       ├── sounds.py           # Sound-Effekte
│       ├── animations.py       # Einfache Animationen
│       └── colors.py           # Farbschema
├── assets/
│   ├── products/               # Produkt-Bilder
│   ├── sounds/                 # Beep, Erfolg, Fehler
│   ├── fonts/                  # Große, kindgerechte Fonts
│   └── avatars/                # Benutzer-Symbole
├── data/
│   └── kasse.db                # SQLite Datenbank
└── dev/
    ├── project-goal.md         # Projektziel (lesbar)
    ├── concept.md              # Vollständiges Konzept
    └── setup-ideas.md          # Diese Datei
```

### Scene-System Pattern

```python
# scenes/base_scene.py
class BaseScene(ABC):
    def __init__(self, game):
        self.game = game
        self.current_user = game.current_user
    
    def handle_input(self, input_event): pass
    def update(self, dt): pass
    def draw(self, surface): pass
    def switch_to(self, scene_name, **kwargs): pass
```

### Scenes im Detail

| Scene | Beschreibung | Eingabe |
|-------|--------------|---------|
| **LoginScene** | "Bitte Karte scannen" | Barcode |
| **MenuScene** | Modus-Auswahl (4 große Buttons) | Touch |
| **ScanScene** | Produkte scannen, Warenkorb | Barcode, Touch |
| **RecipeScene** | Rezept-Checkliste abhaken | Barcode, Touch |
| **PickerScene** | Obst/Gemüse/Backwaren wählen | Touch |
| **PaymentScene** | Bezahlen, Guthaben prüfen | Barcode (Karte) |
| **MathScene** | Rechenaufgaben | Nummernpad |
| **CashierScene** | Kassiererin-Dashboard | Barcode, Touch |
| **AdminScene** | Einstellungen, Guthaben | Touch |

---

## Datenbank-Design (SQLite)

### Schema

```sql
-- Benutzer (Kinder + Gäste)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    barcode TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    color TEXT NOT NULL,           -- Hex-Farbe für Rand
    avatar TEXT,                   -- Pfad zu Avatar-Bild
    balance INTEGER DEFAULT 1000,  -- In Cent (1000 = 10 Taler)
    math_level INTEGER DEFAULT 1,  -- Schwierigkeitsstufe
    is_guest INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Produkte
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    barcode TEXT UNIQUE,           -- NULL für Touch-Produkte
    name TEXT NOT NULL,
    price INTEGER NOT NULL,        -- In Cent
    category TEXT NOT NULL,        -- 'barcode', 'obst', 'gemuese', 'backwaren'
    image TEXT NOT NULL
);

-- Rezepte
CREATE TABLE recipes (
    id INTEGER PRIMARY KEY,
    barcode TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    image TEXT
);

-- Rezept-Zutaten (n:m)
CREATE TABLE recipe_ingredients (
    recipe_id INTEGER,
    product_id INTEGER,
    quantity INTEGER DEFAULT 1,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Transaktions-Log (optional, für Statistiken)
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    total INTEGER,
    mode TEXT,                     -- 'free', 'recipe', 'cashier'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Initiale Daten

```python
# Feste Benutzer
USERS = [
    {"barcode": "USER_CAROLIN", "name": "Carolin", "color": "#3B82F6", "math_level": 1},
    {"barcode": "USER_ANNELIE", "name": "Annelie", "color": "#EF4444", "math_level": 2},
    {"barcode": "USER_ADMIN", "name": "Admin", "color": "#9333EA", "is_admin": True},
]

# Gast-Karten (zurücksetzbar)
GUEST_CARDS = [
    {"barcode": "GUEST_001", "name": "Gast 1", "color": "#10B981", "is_guest": True},
    {"barcode": "GUEST_002", "name": "Gast 2", "color": "#F59E0B", "is_guest": True},
]
```

---

## Input-System Design

### Input Manager

```python
class InputManager:
    """
    Zentralisiertes Input-Handling:
    - Barcode: pygame.KEYDOWN events (Scanner emuliert Tastatur)
    - Nummernpad: pygame.KEYDOWN events (K_KP0 - K_KP9)
    - Touch: pygame.MOUSEBUTTONDOWN
    """
    
    def __init__(self):
        self.barcode_buffer = ""
        self.numpad_buffer = ""
    
    def process_event(self, event) -> InputEvent | None:
        if event.type == pygame.KEYDOWN:
            # Barcode-Scanner (endet mit ENTER)
            if event.key == pygame.K_RETURN and self.barcode_buffer:
                barcode = self.barcode_buffer
                self.barcode_buffer = ""
                return BarcodeEvent(barcode)
            elif event.unicode.isprintable():
                self.barcode_buffer += event.unicode
            
            # Nummernpad
            if event.key in NUMPAD_KEYS:
                return NumpadEvent(NUMPAD_KEYS[event.key])
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return TouchEvent(event.pos)
        
        return None
```

### Barcode-Typen erkennen

```python
def identify_barcode(barcode: str) -> BarcodeType:
    """Erkennt den Typ eines gescannten Barcodes."""
    if barcode.startswith("USER_") or barcode.startswith("GUEST_"):
        return BarcodeType.USER
    elif barcode.startswith("ADMIN"):
        return BarcodeType.ADMIN
    elif barcode.startswith("RECIPE_"):
        return BarcodeType.RECIPE
    else:
        return BarcodeType.PRODUCT
```

---

## UI/UX Prinzipien für Kinder

### Design-Regeln

1. **Große Touch-Targets:** Mindestens 80x80px (Kinderfinger!)
2. **Hoher Kontrast:** Helle Farben, gut lesbar
3. **Große Schrift:** Min. 32px für Text, 60px+ für Zahlen
4. **Sofortiges Feedback:** Scan → Sound + Animation (<100ms)
5. **Kein Scrolling:** Alles sichtbar auf 800x480px
6. **Farbiger Rand:** Zeigt an, wer eingeloggt ist

### Farbschema (aus Mockups)

```python
# Warme, kindgerechte Farben
BG_CREAM = (253, 246, 236)        # Hintergrund
ORANGE_PRIMARY = (245, 158, 66)   # Buttons, Akzente
GREEN_SUCCESS = (74, 222, 128)    # Mengen, Erfolg
RED_ERROR = (248, 113, 113)       # Fehler, Kosten
BLUE_CAROLIN = (59, 130, 246)     # Carolins Farbe
RED_ANNELIE = (239, 68, 68)       # Annelies Farbe
```

### Benutzer-Feedback-System

```python
# Visuelle Zustände
class UserBadge:
    """Zeigt eingeloggten Benutzer oben rechts."""
    def __init__(self, user):
        self.name = user.name
        self.color = user.color
        self.avatar = user.avatar

class ScreenBorder:
    """Farbiger Rand um den gesamten Bildschirm."""
    def __init__(self, color, width=8):
        self.color = color
        self.width = width
```

---

## Performance-Optimierung Pi Zero

### Resource Budget

```
Ziel: <100MB RAM, 30 FPS konstant

RAM-Verteilung:
- Pygame/SDL: ~40MB
- Python Runtime: ~30MB
- Assets (Images/Sounds): ~20MB
- SQLite: ~5MB
- Headroom: ~5MB
```

### Optimization Strategies

1. **Asset-Loading:** Einmal beim Start laden, dann cachen
2. **Dirty Rectangle Drawing:** Nur geänderte Bereiche neu zeichnen
3. **Sound Pre-Loading:** Alle Sounds beim Start laden
4. **Font-Rendering Cache:** Text nicht jeden Frame neu rendern
5. **SQLite WAL-Modus:** Bessere Performance bei Schreibzugriffen

---

## Development Workflow

### Mac Development
```bash
# Setup
cd carolins_kasse
uv sync

# Run (Window-Modus für Debug)
uv run python src/main.py

# Datenbank initialisieren
uv run python -m src.database init
```

### Deploy to Pi
```bash
# Via rsync
rsync -avz --exclude='.venv' --exclude='*.pyc' ./ pi@raspberrypi.local:~/kasse/

# Auf Pi
ssh pi@raspberrypi.local
cd kasse
uv sync
export SDL_VIDEODRIVER=kmsdrm
uv run python src/main.py
```

### Autostart Setup
```bash
# /etc/systemd/system/kasse.service
[Unit]
Description=Carolins Kasse
After=multi-user.target

[Service]
User=pi
Environment="SDL_VIDEODRIVER=kmsdrm"
WorkingDirectory=/home/pi/kasse
ExecStart=/home/pi/.local/bin/uv run python src/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Barcode-Generator Tool

Für die Spielwaren müssen Barcodes generiert und gedruckt werden.

```python
# tools/barcode_generator.py
import barcode
from barcode.writer import ImageWriter

def generate_product_barcode(product_id: str, name: str):
    """Generiert einen Barcode für ein Produkt."""
    code = barcode.get('code128', product_id, writer=ImageWriter())
    filename = code.save(f'barcodes/{name}')
    return filename

def generate_user_card(user_id: str, name: str):
    """Generiert eine Benutzerkarte."""
    code = barcode.get('code128', f'USER_{user_id}', writer=ImageWriter())
    filename = code.save(f'cards/{name}')
    return filename
```

---

## Entwicklungs-Phasen

### Phase 1: MVP
- [x] Projekt-Setup mit uv
- [ ] SQLite Datenbank-Schema
- [ ] Input-Manager (Barcode + Touch)
- [ ] LoginScene + ScanScene
- [ ] Produkte scannen → Warenkorb
- [ ] PaymentScene mit Guthaben-Abzug
- [ ] Sound-Feedback

### Phase 2: Benutzer-System
- [ ] Farbige Ränder pro Benutzer
- [ ] UserBadge Component
- [ ] Gast-Karten
- [ ] Guthaben persistent speichern

### Phase 3: Rezept-Modus
- [ ] RecipeScene mit Checkliste
- [ ] Fehler bei falschem Produkt
- [ ] Erfolgs-Animation

### Phase 4: Geld verdienen
- [ ] MathScene mit Nummernpad-Eingabe
- [ ] Schwierigkeitsstufen (pro Benutzer)
- [ ] CashierScene mit Lohn-System
- [ ] Inaktivitäts-Erkennung

### Phase 5: Admin & Polish
- [ ] AdminScene
- [ ] Barcode-Generator Tool
- [ ] Remote-Zugang dokumentieren
- [ ] Kinder-Testing

---

## Testing Strategy

1. **Mac:** UI/UX mit Keyboard-Simulation (Barcodes als Text-Input)
2. **Pi:** Echte Hardware mit Scanner/Keypad
3. **Kinder-Test:** Beobachten, nicht erklären!
   - Finden sie Buttons ohne Hilfe?
   - Verstehen sie das Feedback?
   - Macht es Spaß?

---

**Entwickelt mit:** `uv` + `pygame` + `sqlite3`
