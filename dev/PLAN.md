# Development Plan

## Phase Overview

| # | Phase | Status | Goal |
|---|-------|--------|------|
| 1 | Foundation | ✅ | App runs, UI Grundgerüst, Navigation |
| 1.5 | Data Setup | ✅ | Assets verarbeitet (nobg, S, M, L) |
| 2 | Core Shopping | ✅ | Scan → Cart → Checkout flow |
| 3 | Game Modes | ✅ | Recipe, Math, Cashier modes |
| 3.5 | Refactoring | ✅ | Mixins, Fonts, Scene Base, Code Cleanup |
| 4 | User System | ✅ | Login, Frame-Overlay, Checkout mit Balance |
| 4.5 | Session Tracking | ✅ | Verdienst-System, Balance-Visualisierung |
| 5 | System Integration | ✅ | Inactivity, Time-Bonus, UX-Verbesserungen |
| 5.5 | UI-Refactoring | ✅ | Kindgerechte Fortschrittsanzeige |
| **6** | **UI-Overhaul** | 🔨 | **Asset-First Design, Mockup-Style** |
| 7 | Admin-Bereich | 🔨 | Vollständige Web-UI für Eltern |
| 8 | Polish | 🔲 | Sounds, Animationen, Edge Cases |

---

## Phase 1: Foundation ✅

**Goal:** App runs, handles all input types, shows basic UI

- [x] Pygame window (1024x600)
- [x] Scene manager
- [x] Basic UI components (Button)
- [x] Asset loading (`src/utils/assets.py`)
- [x] 6 navigierbare Scenes (Menu, Scan, Recipe, MathGame, Cashier, Picker)
- [x] Input abstraction (barcode, numpad, touch)

---

## Phase 1.5: Data & Asset Setup ✅

**Goal:** Data infrastructure and assets prepared

- [x] 155 Master-Assets organisiert
- [x] DB-Seed Skript (`tools/seed_database.py`)
- [x] Test-Daten erstellt (26 Produkte, 4 User, 5 Rezepte)
- [x] Asset-Pipeline via `/img` Skill
- [x] Menu-Tiles erstellt
- [x] Barcode-Generator Tool

---

## Phase 2: Core Shopping ✅

**Goal:** Complete shopping flow

- [x] ScanScene ausgebaut (Produktliste, +/- Buttons, Warenkorb)
- [x] Product database integration
- [x] Barcode scanning → Produkt-Lookup
- [x] Cart management (State, Summe)
- [x] Product picker (Touch für Obst/Gemüse)
- [x] Checkout (Bezahlen-Button)

---

## Phase 3: Game Modes ✅

**Goal:** Educational features

- [x] Recipe mode (Checkliste, Zutaten scannen)
- [x] Math games (3 Schwierigkeitsstufen)
- [x] Cashier mode (Timer-basierter Lohn)
- [x] Komponenten: ChecklistItem, Numpad, ProductDisplay

---

## Phase 3.5: Refactoring ✅

**Goal:** Code Cleanup & Architektur-Patterns

- [x] ClickableMixin für Components
- [x] FontRegistry für zentrale Font-Verwaltung
- [x] Scene Base Class erweitert
- [x] MessageMixin mit Color-Support
- [x] ~150 Zeilen duplizierter Code eliminiert

---

## Phase 4: User System ✅

**Goal:** Multiple users with balances

- [x] LoginScene (User-Karte scannen)
- [x] User-State in App speichern
- [x] Frame-Overlay pro User (Farb-Rahmen)
- [x] Balance tracking in DB
- [x] Checkout prüft Balance
- [x] Balance-Update nach Kauf

---

## Phase 4.5: Session Tracking ✅

**Goal:** Verdienst-System & Balance-Visualisierung

- [x] DB-Tabellen: sessions, earnings, transactions
- [x] `BalanceBar` Komponente (max_value, milestone)
- [x] `CheckoutReceipt` mit Kunden-Balance
- [x] Session-Start bei Login
- [x] Earnings bei Mathe/Kassiererin
- [x] Time-Bonus (10 Min = 1 Taler)

---

## Phase 5: System Integration ✅

**Goal:** Production-ready UX

- [x] InactivityMonitor (Auto-Shutdown nach Timeout)
- [x] Global Time-Bonus über alle Scenes
- [x] ScrollableCart für viele Produkte
- [x] InsufficientFundsPopup bei zu wenig Guthaben
- [x] CheckoutMixin für wiederverwendbaren Flow

---

## Phase 5.5: UI-Refactoring ✅

**Goal:** Kindgerechte Visualisierung

- [x] Mathe-Spiel: Session-basierter Fortschrittsbalken (0→15)
- [x] Milestone-Stern bei 10 Talern + Bonus
- [x] "Super gemacht" Overlay bei Session-Ende
- [x] Kassiererin: Vereinfachtes Layout (nur Guthaben-Karte)

---

## Phase 6: UI-Overhaul 🔨

**Goal:** Visueller Stil wie Mockups (handgezeichnet, kindgerecht)

### 6.1 Codebase Cleanup ✅
- [x] Duplicate colors/constants konsolidiert → `constants.py`
- [x] Unused components gelöscht (theme.py, grid.py, stats_card.py, inactivity_monitor.py)
- [x] Font-System refactored → simple functions (heading, body, caption, bold, custom)
- [x] Fredoka font family installiert (Regular + Bold)

### 6.2 UI Reference Implementation ✅
- [x] `ui_test.py` als Referenz-Scene gebaut
- [x] Paper texture background + orange Frame mit Notches
- [x] Titel "CAROLIN" (bold, DANGER-Farbe, obere Aussparung)
- [x] Close-Button "X" (bold, DANGER, oben rechts)
- [x] Progress Bar (abgerundet, ORANGE bg, DANGER fg) → `src/ui/progress_bar.py`
- [x] Geld-Icon links der Progress Bar
- [x] Zählerstand (caption font) rechts der Progress Bar
- [x] Alle Variablen zentral am Skript-Anfang deklariert

### 6.3 Screen-by-Screen Migration 🔨

**Architektur:** Zentrale `FrameShell` (`src/ui/shell.py`) rendert Paper-BG + Frame-Overlay + Shell-UI (Titel, Footer, Close-Button). Scenes rendern nur noch Content.

**Rendering-Reihenfolge (main.py):**
1. Paper Texture (fullscreen) — `shell.render_background()`
2. Scene Content — `scene.render()` (OHNE screen.fill!)
3. Frame Overlay (user-farbig) — `shell.render_overlay()`
4. Shell-UI: Titel + Footer + Close/Back-Button

#### Step 0: Infrastruktur ✅
- [x] `src/ui/shell.py` (NEU) — FrameShell Klasse
- [x] `src/constants.py` — COLOR_TO_FRAME, FRAME_TITLE_COLOR, SHELL_* Mappings
- [x] `main.py` — Shell integrieren, Rendering-Loop umbauen

#### Step 1: StartScene ✅
- [x] `src/scenes/start.py` (NEU) — `startbildschirm.png` fullscreen
- [x] Beliebige Taste / Touch → LoginScene
- [x] `main.py` initial scene: `"start"`

#### Step 2: LoginScene ✅
- [x] `screen.fill()` entfernen — Paper-BG von Shell
- [x] Kein Rahmen (kein User eingeloggt)
- [x] Zwei Avatare (Carolin + Annelie) nebeneinander
- [x] Fredoka fonts, bestehende Input-Logik beibehalten

#### Step 3: MenuScene ✅
- [x] `screen.fill()` + system fonts entfernen
- [x] 3 Kacheln horizontal: Rezept (kochbuch), Einkaufen (einkaufskorb), Rechnen (taschenrechner)
- [x] Labels in caption font
- [x] Logout über Shell Close-Button (X)
- [x] CashierScene aus Menu entfernt

#### Step 4: ScanScene ✅
- [x] Header-Component entfernen → Shell-Titel
- [x] Content innerhalb Content-Rect
- [x] ProductDisplay + ScrollableCart repositioniert

#### Step 5: RecipeScene ✅
- [x] Header entfernen → Shell-Titel
- [x] Content-Rect Layout
- [x] ChecklistItems repositioniert

#### Step 6: MathGameScene ✅
- [x] Header + TwoPanel entfernen
- [x] Numpad + Aufgabe im Content-Rect
- [x] Score als Badge, BalanceBar repositioniert

#### Step 7: CashierScene — ENTFÄLLT
- [x] ~~Header + Card entfernen~~ → Scene gelöscht (nicht mehr im Menu, Dead Code)

#### Step 8: PickerScene ✅
- [x] Header entfernen
- [x] Category-Tabs + Product-Grid im Content-Rect

#### Step 9: Aufräumen 🔨
- [x] `src/scenes/ui_test.py` gelöscht
- [x] `src/scenes/cashier.py` gelöscht
- [x] `src/scenes/__init__.py` aktualisiert (StartScene rein, UITest/Cashier raus)
- [x] `src/components/header.py` löschen (kein Import mehr)
- [x] `src/components/two_panel.py` löschen (kein Import mehr)
- [ ] Alte Konstanten in `layout.py` aufräumen
- [x] Docs finalisieren

### 6.4 Asset-Erstellung 🔜
- [x] 28+ Produkt-Assets im neuen `340er`-Schema vorhanden
- [x] Rezept-Assets im neuen `680er`-Schema vorhanden
- [ ] Visueller Gesamttest aller Scenes

---

## Phase 7: Admin-Bereich 🔨

**Goal:** Vollständige Admin-Web-UI für Eltern

**Status 2026-04-26:** FastAPI ist als read-only Viewer vorhanden. Die nächste Phase sollte keine zweite Backend-Struktur aufbauen, sondern die bestehenden DB-Funktionen vorsichtig erweitern und klare Modulgrenzen setzen.

### 7.0 Backend Foundation
- [x] Read-only Admin-Seiten für Produkte, Benutzer und Rezepte
- [x] Zentrale Barcode-Konventionen in `src/utils/barcodes.py`
- [x] Versionierbare Seed- und Barcode-Tools vorbereiten
- [x] DB-Initialsetup festlegen: eine lokale DB, festes Carolin/Annelie-Setup im Code, normales Setup nicht-destruktiv
- [ ] `src/utils/database.py` in kleinere Verantwortlichkeiten schneiden
- [ ] Admin-Form-Validierung und Fehlerdarstellung festlegen
- [ ] Barcode-Printformat festlegen: SVG-Einzeldruck, PDF-Bögen oder beides

### 7.1 User-Verwaltung
- [ ] User-Liste anzeigen
- [ ] Neuen User anlegen
- [ ] User bearbeiten (Name, Farbe, Schwierigkeit)
- [ ] User-Karte (Barcode) zuweisen

### 7.2 Produkt-Verwaltung
- [ ] Produkt-Liste mit Bildern
- [ ] Neues Produkt anlegen
- [ ] Bild-Upload für Produkte
- [ ] Barcode zuweisen/generieren
- [ ] Barcode drucken

### 7.3 Guthaben-System
- [ ] Guthaben einsehen (alle User)
- [ ] Einzeln aufladen
- [ ] Batch-Aufladung

### 7.4 Transaktionen & Statistiken
- [ ] Transaktions-Verlauf
- [ ] Earnings-Übersicht
- [ ] Statistiken (Charts)
- [ ] Export-Funktion

### 7.5 Quick-Admin an der Kasse
- [ ] Admin-Karte Erkennung
- [ ] Schnelles Guthaben-Aufladen
- [ ] Letzte Transaktion stornieren

### Recommended Implementation Order

1. Database boundary: split schema, models, and query functions enough that admin CRUD does not keep growing `database.py`.
2. Product CRUD: add/create/edit product fields and regenerate a barcode SVG when barcode-bearing products change.
3. User CRUD: add/edit users, difficulty, color, balance, and card barcode generation.
4. Printable barcodes: start with product/user/recipe SVG download links, then add PDF sheets.
5. Transactions/earnings: read-only history first, then controlled balance top-ups.
6. Admin-card flow on the pygame side only after the web admin is stable.

---

## Phase 8: Polish 🔲

**Goal:** Production-ready

- [ ] Sound-Effekte (Scan, Erfolg, Fehler)
- [ ] Animationen bei Checkout/Bonus
- [ ] Error handling (alle Edge Cases)
- [ ] Pi Zero Performance-Test
- [ ] Offline-Modus testen

---

## Dependencies

```
Phase 1 → 1.5 → 2 → 3 → 3.5 → 4 → 4.5 → 5 → 5.5 → 6 → 7 → 8
                                                        ↑
                                                   (aktuell: 6.4)
```

---

## Konstanten (Wirtschaft)

```python
# Balance-Visualisierung
BALANCE_BAR_MAX = 50  # Voller Balken = 50 Taler

# Verdienst-Raten
EARNING_MATH = {1: 1, 2: 2, 3: 3}  # Leicht=1, Mittel=2, Schwer=3
EARNING_CASHIER = 5    # 5 Taler pro Kassieren
EARNING_RECIPE = 8     # 8 Taler pro Rezept
EARNING_TIME_SECONDS = 600  # 10 Min = 1 Taler

# Farbschwellen für Balance-Balken
BALANCE_THRESHOLD_LOW = 10   # < 10 = rot
BALANCE_THRESHOLD_MED = 25   # 10-25 = gelb, > 25 = grün
```
