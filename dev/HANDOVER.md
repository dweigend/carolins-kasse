# Session Handover

**Last Updated:** 2026-01-28

## Current State

✅ Phase 1 complete — Pygame + Scene Manager working
✅ Hardware bestellt — Lieferung erwartet

## Hardware (Bestellt ✅)

| Komponente | Modell | Preis |
|------------|--------|-------|
| Computer | **Raspberry Pi Zero 2 W** | 23€ |
| Display | **Elecrow 7" IPS 1024x600 Touch** | 47€ |
| Stromversorgung | **Anker 20K 87W (A1383)** | 40€ |
| HDMI-Kabel | CY Mini-HDMI Flachkabel 20cm | 9€ |

**Wichtig:** Display-Auflösung ist jetzt **1024x600** (statt 800x480)!

## What Was Done (This Session)

- Hardware recherchiert und bestellt
- Dokumentation aktualisiert:
  - `dev/ARCHITECTURE.md` — Hardware-Sektion, Admin-System, FastAPI
  - `dev/concept.md` — Barcode-Management, Admin-System
  - `dev/PLAN.md` — Phase 1.5 (Data Setup), Phase 5 (Admin) detailliert
  - `dev/setup-ideas.md` — Komplette Hardware-Specs, Verkabelung
  - `CLAUDE.md` — Display/Target aktualisiert

## Key Decisions

1. **Pi Zero 2 W** statt Zero W (5x schneller, gleicher Preis)
2. **1024x600 Display** statt 800x480 (höhere Auflösung, IPS)
3. **FastAPI + Jinja2 + HTMX** statt Flask für Admin-UI
4. **Anker Powerbank** mit Pass-Through (~20h Laufzeit)

## Next Steps

**Warte auf Hardware-Lieferung**, dann:

1. **Phase 1.5: Data & Barcode Setup**
   - `data/products.yaml` erstellen
   - `data/users.yaml` erstellen
   - `tools/seed_database.py` implementieren
   - `tools/generate_barcodes.py` implementieren

2. **Display-Auflösung anpassen**
   - `src/constants.py`: SCREEN_WIDTH=1024, SCREEN_HEIGHT=600

## Noch zu kaufen

- USB-C auf Micro-USB Adapter (~3€)
- USB-A auf Micro-USB Kabel (~5€)
- microSD-Karte 32GB (~8€)
- USB-Barcode-Scanner (~15-30€)
- USB-Nummernpad (~10€)

## Architecture Focus

Working on: **Data Layer** (YAML → SQLite Pipeline)

See `dev/ARCHITECTURE.md` for component diagram.

## Blockers

- ⏳ Hardware noch nicht da

## Notes

- Verkabelung dokumentiert in `dev/setup-ideas.md`
- Admin-System: WiFi-Hotspot + FastAPI Web-UI
- Stromverbrauch: ~700mA gesamt → ~20h Akkulaufzeit
