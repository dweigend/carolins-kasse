# Session Handover

**Last Updated:** 2026-01-29

## Current State

✅ Phase 1 complete — Pygame + Scene Manager working
✅ Phase 1.5 in progress — Assets organisiert
⏳ Hardware bestellt — Lieferung erwartet

## What Was Done (This Session)

### Asset-Organisation ✅
- **155 Master-Dateien** in neue Struktur sortiert:
  ```
  assets/master/
  ├── products/   # 87 Lebensmittel, Spielzeug
  ├── icons/      # 25 UI-Icons
  ├── buttons/    # 6 Button-Grafiken
  ├── avatars/    # 6 User-Avatare
  ├── emojis/     # 6 Smileys
  ├── digits/     # 18 Zahlen, Euro-Münzen
  ├── frames/     # 4 Rahmen
  └── recipes/    # 3 Rezeptbilder
  ```
- Alle Dateien **DE → EN** umbenannt
- Tippfehler korrigiert (crosiont → croissant, etc.)
- Alte Test-Exports gelöscht

### Dokumentation ✅
- `dev/ASSETS.md` — Aktualisiert mit Status-Markierungen
- `dev/ASSET_CATALOG.md` — NEU: LLM-lesbarer Katalog (155 Assets)
- `dev/UI_SCREENS.md` — NEU: Screen-Dokumentation mit Layouts

### UI-Mockups ✅
- 9 Dateien in `ui/` einheitlich umbenannt
- Alle Screens dokumentiert

## Fehlende Assets

### 🔴 Hohe Priorität
| Asset | Beschreibung |
|-------|--------------|
| `tile_shopping.png` | Menu-Tile blau (180×180) |
| `tile_recipe.png` | Menu-Tile rot (180×180) |
| `tile_math_game.png` | Menu-Tile grün (180×180) |
| `tile_cashier.png` | Menu-Tile gelb (180×180) |

### 🟡 Mittlere Priorität
| Asset | Text |
|-------|------|
| `btn_pay.png` | "BEZAHLEN" |
| `btn_add_to_cart.png` | "IN DEN KORB" |
| `btn_back_to_store.png` | "ZURÜCK ZUM LADEN" |
| `btn_finish_recipe.png` | "REZEPT FERTIGSTELLEN" |
| `btn_calculate.png` | "BERECHNEN" |

## Next Session: UI bauen

### Ziel
Pygame-UI basierend auf Mockups implementieren.

### Reihenfolge
1. **Asset-Pipeline** — via `/img` Skill (Dreischritt)

   ```
   assets/master/     →  assets/nobg/      →  assets/S/, M/, L/
   (Original)            (ohne Hintergrund)   (skaliert)
   ```

   **Schritt 1:** Hintergrund entfernen → `assets/nobg/`
   **Schritt 2:** Skalieren → `assets/S/` (30px), `assets/M/` (60px), `assets/L/` (120px)

   **Wichtig:**
   - `assets/master/` bleibt IMMER unverändert (Source of Truth)
   - Ermöglicht Neubearbeitung bei Bedarf

   **Ausnahmen (bereits ohne Hintergrund):**
   - `buttons/` — direkt skalieren
   - `frames/` — NICHT skalieren (UI-Rahmen, volle Größe)

2. **Asset Loader** — `src/utils/assets.py`
   - Lädt vorskalierte Bilder (kein Runtime-Scaling)
   - Simples Caching (dict)
   - `assets.get("products/milk", "M")` → `assets/M/products/milk.png`
   - `assets.get("frames/red")` → `assets/nobg/frames/red.png` (keine Größe)

3. **Hauptmenü** — `src/scenes/menu.py`
   - 4 Tiles (Einkauf, Rezept, Rechenspiel, Kassiererin)
   - Touch-Navigation
   - Siehe `ui/05_main_menu.png`

4. **Scan-Screen** — `src/scenes/scan.py`
   - Produktliste mit Zähler
   - User-Badge (Rahmenfarbe)
   - +/- Buttons
   - Siehe `ui/07_scan_screen_annelie.png`

### Wichtige Dateien
- `dev/UI_SCREENS.md` — Layout-Dokumentation
- `dev/ASSETS.md` — Asset-Übersicht
- `dev/ASSET_CATALOG.md` — Alle Pfade

## Hardware (Bestellt ✅)

| Komponente | Modell |
|------------|--------|
| Computer | Raspberry Pi Zero 2 W |
| Display | Elecrow 7" IPS 1024x600 Touch |
| Stromversorgung | Anker 20K 87W |

**Display:** 1024×600 px

## Noch zu kaufen

- USB-C auf Micro-USB Adapter (~3€)
- USB-A auf Micro-USB Kabel (~5€)
- microSD-Karte 32GB (~8€)
- USB-Barcode-Scanner (~15-30€)
- USB-Nummernpad (~10€)

## Blockers

- ⏳ Hardware noch nicht da
- ⏳ 4 Menu-Tiles fehlen noch (werden nachgeliefert)
