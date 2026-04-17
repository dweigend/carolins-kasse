# Session Handover

**Last Updated:** 2026-04-17

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

### Context Verified

- Bestehende App-Struktur, Plan-Dokumente und Admin-Backend geprüft
- GitHub-Issue-Kontext versucht zu laden; aktuell kam keine Issue-Liste zurück

## Current Risks / Open Questions

1. Die neue UI wurde in dieser Session nicht visuell durchgeklickt; das bleibt der wichtigste nächste Verifikationsschritt.
2. Der Admin-Bereich ist weiterhin nur lesend; Phase 7 braucht noch eine klare Entscheidung zum Scope.
3. Hardware-Tests auf dem Raspberry Pi fehlen weiterhin für Touch, Scanner und Performance.

## Recommended Next Session

1. `uv run python main.py` starten und alle Scenes einmal visuell testen.
2. `uv run uvicorn src.admin.server:app --reload --port 8080` prüfen und entscheiden, ob Phase 7 bei FastAPI bleibt.
3. `dev/ARCHITECTURE.md` und Asset-Docs auf den neuen Shell-/Asset-Stand nachziehen.
4. Danach entweder Phase 7 sauber schneiden oder erst einen UI-Polish-/Bugfix-Pass machen.

## Quick Start

```bash
uv run python main.py
uv run uvicorn src.admin.server:app --reload --port 8080
uv run ruff check src/
uv run ruff format src/
```
