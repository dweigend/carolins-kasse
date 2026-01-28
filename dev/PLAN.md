# Development Plan

## Phase Overview

| # | Phase | Status | Goal |
|---|-------|--------|------|
| 1 | Foundation | 🔲 | App runs, handles input, basic UI |
| 1.5 | Data Setup | 🔲 | YAML structure, barcode tools, DB seed |
| 2 | Core Shopping | 🔲 | Scan → Cart → Checkout flow |
| 3 | User System | 🔲 | Login, balance, persistence |
| 4 | Game Modes | 🔲 | Recipe mode, math games |
| 5 | Admin System | 🔲 | WiFi-Hotspot, Web-UI, Quick-Admin |
| 6 | Polish | 🔲 | Sounds, animations, edge cases |

---

## Phase 1: Foundation

**Goal:** App runs, handles all input types, shows basic UI

- [ ] Pygame window (800x480)
- [ ] Scene manager
- [ ] Input abstraction (barcode, numpad, touch)
- [ ] Basic UI components
- [ ] Asset loading

**Exit:** App starts, scenes switch, all inputs work

---

## Phase 1.5: Data & Barcode Setup

**Goal:** Data infrastructure for products and users

- [ ] YAML-Struktur definieren (`data/products.yaml`, `data/users.yaml`)
- [ ] Barcode-Generator Tool (`tools/generate_barcodes.py`)
  - python-barcode Library
  - EAN-13 für Produkte
  - Custom-Format für Karten
- [ ] DB-Seed Skript (`tools/seed_database.py`)
  - YAML → SQLite Import
  - Idempotent (kann mehrfach ausgeführt werden)
- [ ] Test-Daten erstellen
  - 10-15 Produkte
  - 2-3 User (Carolin, Annelie, Gast)
  - 1 Admin-Karte

**Exit:** `uv run python tools/seed_database.py` erstellt funktionierende DB

---

## Phase 2: Core Shopping

**Goal:** Complete shopping flow

- [ ] Product database (SQLite)
- [ ] Barcode scanning
- [ ] Cart management
- [ ] Product picker (Touch für Obst/Gemüse)
- [ ] Checkout screen

**Exit:** Can scan products, manage cart, complete purchase

---

## Phase 3: User System

**Goal:** Multiple users with balances

- [ ] User database
- [ ] Card login
- [ ] Balance tracking
- [ ] User indicator (farbiger Rand)
- [ ] Guest cards

**Exit:** Users log in, purchases deduct balance, data persists

---

## Phase 4: Game Modes

**Goal:** Educational features

- [ ] Recipe mode (Checkliste, Fehler bei falschem Produkt)
- [ ] Math games (3 Schwierigkeitsstufen)
- [ ] Cashier mode (Lohn-System)
- [ ] Mode selection menu

**Exit:** Can complete recipe, play math game, earn money as cashier

---

## Phase 5: Admin System

**Goal:** Full admin capabilities for parents

### 5.1 Quick-Admin an der Kasse
- [ ] Admin-Karte Erkennung
- [ ] Guthaben aufladen (Kind-Karte → Betrag → Enter)
- [ ] Barcode zuordnen (Scan → Name eingeben)
- [ ] Letzte Transaktion stornieren

### 5.2 WiFi-Hotspot
- [ ] hostapd Setup (Pi als Access Point)
- [ ] dnsmasq für DHCP
- [ ] Auto-Start bei Admin-Karte
- [ ] Auto-Timeout (10 Min Inaktivität)
- [ ] UI zeigt SSID + Passwort + IP

### 5.3 FastAPI Admin-Server
- [ ] FastAPI + Jinja2 + HTMX Setup
- [ ] Produkt-Verwaltung (CRUD)
- [ ] Bild-Upload für Produkte
- [ ] User-Verwaltung
- [ ] Guthaben aufladen (einzeln/Batch)
- [ ] Barcode generieren + Download
- [ ] Transaktions-Verlauf
- [ ] Statistiken/Dashboard

**Exit:** Parents can manage everything via phone browser

---

## Phase 6: Polish

**Goal:** Production-ready

- [ ] Sound effects (Scan, Error, Success)
- [ ] Animations (Checkout, Recipe complete)
- [ ] Error handling (alle Edge Cases)
- [ ] Pi Zero performance optimization

**Exit:** No crashes, kids use independently

---

## Open Design Questions

Needs prototyping with kids:

1. **Product Picker:** Touch vs. Numpad?
2. **Quantity Input:** +/- vs. direct number?
3. **Navigation:** `[*]` key vs. touch for "back"?

---

## Dependencies

```
Phase 1 ──► Phase 1.5 ──► Phase 2 ──► Phase 3 ──► Phase 4
                                          │
                                          ▼
                                      Phase 5 ──► Phase 6
```

Phase 5 (Admin) kann parallel zu Phase 4 (Game Modes) entwickelt werden.
