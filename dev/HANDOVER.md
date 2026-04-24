# Session Handover

**Last Updated:** 2026-04-24 21:59 CEST

## Current State

✅ Phase 1-6.4 inhaltlich weitgehend vorhanden
✅ UI-Migration auf Shell-basierte Scenes ist im Projektstand verankert
✅ Produkt- und Rezept-Assets wurden bereits auf das neue Schema umgestellt
🟡 Codex-Portierung der Projektdoku ist jetzt angelegt
🟡 Git-Historie wurde lokal in sinnvolle Blöcke überführt und sollte als Nächstes gepusht werden
🟡 Phase 7 Admin-Bereich ist nur als read-only FastAPI-Ansicht vorhanden
🔲 Phase 8 Polish und Hardware-Validierung offen

| Area | Status | Notes |
|------|--------|-------|
| Gameplay core | ✅ | Login, Menu, Scan, Recipe, Math, Picker vorhanden |
| Session economy | ✅ | Balance, Earnings, Transactions, Session tracking vorhanden |
| UI overhaul | 🟡 | Neue Shell und Assets im Worktree, visueller Gesamttest noch offen |
| Admin area | 🟡 | Listenansichten für Products, Users, Recipes vorhanden, noch keine CRUD-Flows |
| Codex workflow | ✅ | `AGENTS.md` ist jetzt die führende Assistenz-Doku |

## What Was Done In This Session

### Codex Port

- `AGENTS.md` auf eine Codex-zentrierte Repo-Anleitung umgestellt
- Claude/Cloud-Code-spezifische Dateien entfernt
- `dev/WORKFLOW.md` auf den Codex-Start- und Abschlussablauf aktualisiert
- `dev/STATUS_REPORT.md` als kompakte Projektübersicht ergänzt

### UI + Repo Cleanup

- Shell-basierte Scene-Migration mit `src/ui/shell.py`, `StartScene` und aktualisierten Szenen zusammengeführt
- Produkt- und Rezept-Assets auf die neuen `340er`- und `680er`-Pfade ausgerichtet
- Lokale Commits und offene Änderungen zu wenigen, nachvollziehbaren Git-Einheiten gebündelt
- Shell-Titel im oberen Notch von fixer X-Position auf echte horizontale Zentrierung umgestellt, damit auch kurze Namen wie `Gast` mittig sitzen

### Login Screen Simplification

- `LoginScene` zeigt jetzt direkt `assets/680er/karte_scannen.png` fullscreen
- Avatar-/Text-Layout auf dem Login-Screen entfernt
- Der App-Start nutzt wieder eine vorgeschaltete `StartScene`, die `startbildschirm.png` für 5 Sekunden zeigt und danach automatisch in den Login-Flow wechselt

### Math Game Design Handover

- `dev/assets/MATH_GAME_LAYOUT_SPEC.md` als konkrete Illustrator-Spec für das neue Rechenspiel-Layout angelegt
- Fokus auf ein einziges Haupt-Asset `math_game_layout.png` plus dynamische Zahlen-/Punkt-Overlays im Code
- Nächster Schritt: finale Exportpfade eintragen, sobald die neuen Mockup-/Asset-Dateien vorliegen

### Math Game Rule + UI Pass

- `MathGameScene` auf das neue kinderfreundliche Aufgabenlayout umgestellt: große farbige Aufgabe im bestehenden Shell-Rahmen, keine sichtbare On-Screen-Tastatur
- Eingabe läuft weiter über Tastatur/USB-Numpad; Antwortfelder zeigen per ein oder zwei Unterstrichen die erwartete Stellenzahl
- Ohne Fehler gibt es keine Hilfepunkte und eine `+2`-Belohnung
- Nach dem ersten Fehler erscheinen Punkt-Hilfen unter den Operanden und die Belohnung sinkt auf `+1`
- Nach dem zweiten Fehler wird ohne Belohnung direkt die nächste Aufgabe geladen
- Lokale Render-Verifikation erstellt:
  - `/tmp/carolins_kasse_math_verification/math_without_help.png`
  - `/tmp/carolins_kasse_math_verification/math_with_help.png`

### Math Game Reward Coin Asset Pass

- Neue transparente Reward-Coin-Assets über den `asset-pipeline`-Skill erstellt und in `assets/ui/rewards/` abgelegt:
  - `coin_1_a.png`, `coin_1_b.png`, `coin_1_c.png`
  - `coin_2_a.png`, `coin_2_b.png`, `coin_2_c.png`
- Die finalen Assets basieren auf der neuen Bildgenerierung:
  - `/Users/davidweigend/.codex/generated_images/019dbef6-8135-7632-a8e1-ce58106bca3a/ig_047ce466690c57430169eb42aa485081918aa42030e72f66ca.png`
- `MathGameScene` lädt pro Aufgabe stabil eine `+1`- oder `+2`-Coin-Variante; bei fehlenden Assets bleibt ein programmatischer Badge-Fallback aktiv.
- `src/utils/assets.py` unterstützt jetzt die allgemeine Kategorie `ui/` und eine 96px-Größe `XL`.
- Transparenz und Render-Screenshots wurden lokal geprüft:
  - `/tmp/carolins_kasse_reward_coins_contact_v2.png`
  - `/tmp/carolins_kasse_math_verification/math_without_help.png`
  - `/tmp/carolins_kasse_math_verification/math_with_help.png`

### Math Game Feedback Polish

- Reward-Coin näher an die Aufgabe verschoben, damit die Belohnung visuell zur Antwort gehört.
- Korrekte Eingaben starten jetzt eine kurze visuelle Erfolgsphase:
  - zuerst bleibt die gelöste Antwort mit Sternen und Konfetti kurz sichtbar
  - danach fliegt eine kleine Coin-Kopie Richtung Konto-/Footerbereich
  - erst nach der Ankunft wird die Belohnung gutgeschrieben
- Die Gutschrift wird am Ende der Transfer-Animation angewendet; danach lädt automatisch die nächste Aufgabe.
- Während dieser kurzen Erfolgsphase wird Eingabe ignoriert.
- Zusätzliche Render-Probe erstellt:
  - `/tmp/carolins_kasse_math_verification/math_success_animation.png`
  - `/tmp/carolins_kasse_math_verification/math_success_stars.png`
  - `/tmp/carolins_kasse_math_verification/math_reward_transfer_mid.png`
  - `/tmp/carolins_kasse_math_verification/math_reward_transfer_arrive.png`
  - `/tmp/carolins_kasse_math_verification/math_success_confetti_phase.png`
  - `/tmp/carolins_kasse_math_verification/math_reward_transfer_phase.png`
  - `/tmp/carolins_kasse_math_verification/math_reward_before_balance_update.png`

### Context Verified

- Bestehende App-Struktur, Plan-Dokumente und Admin-Backend geprüft
- GitHub-Issue-Kontext versucht zu laden; aktuell kam keine Issue-Liste zurück
- Git-Tree aufgeräumt: offene Code-, Asset-, Doku- und lokale DB-Testdaten geprüft und für getrennte Commits vorbereitet
- Checks liefen sauber: `uv run ruff check src/`, `uv run ruff format src/`, `uv run python -m compileall src`

## Current Risks / Open Questions

1. Die neue UI wurde in dieser Session nur per lokaler Render-Screenshots geprüft; ein echter Durchklick-Test auf App/Hardware bleibt offen.
2. Der Admin-Bereich ist weiterhin nur lesend; Phase 7 braucht noch eine klare Entscheidung zum Scope.
3. Hardware-Tests auf dem Raspberry Pi fehlen weiterhin für Touch, Scanner und Performance.
4. Das neue Rechenspiel inklusive Coin-Assets ist im Code verdrahtet, aber noch nicht auf dem Raspberry-Pi-Display mit echter USB-Numpad-Eingabe getestet.

## Recommended Next Session

1. `uv run python main.py` starten und das Rechenspiel mit richtiger Eingabe, erster falscher Eingabe, zweiter falscher Eingabe und Session-Ende durchtesten.
2. `uv run uvicorn src.admin.server:app --reload --port 8080` prüfen und entscheiden, ob Phase 7 bei FastAPI bleibt.
3. Mockup-/Illustrator-Dateien für weitere Rechenspiel-Polish-Assets bei Bedarf auf Basis von `dev/assets/MATH_GAME_LAYOUT_SPEC.md` erstellen.
4. Danach mit der Kassen-UI-Welle aus `KASSEN_UI.md` fortfahren, sobald die Mockups abgestimmt sind.

## Quick Start

```bash
uv run python main.py
uv run uvicorn src.admin.server:app --reload --port 8080
uv run ruff check src/
uv run ruff format src/
```
