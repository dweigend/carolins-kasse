# Session Handover

**Last Updated:** 2026-04-26 10:57 CEST

## Current State

✅ Phase 1-6.4 inhaltlich weitgehend vorhanden
✅ UI-Migration auf Shell-basierte Scenes ist im Projektstand verankert
✅ Produkt- und Rezept-Assets wurden bereits auf das neue Schema umgestellt
🟡 Codex-Portierung der Projektdoku ist jetzt angelegt
🟡 Phase 7 Admin-Bereich hat erste Schreibflows für Eltern
🟡 Barcode-Erzeugung ist jetzt als eigene Backend-Verantwortung vorbereitet
✅ DB-Initialsetup ist entschieden: eine lokale DB, festes Carolin/Annelie-Setup, normales Setup nicht-destruktiv
✅ Remote-Admin hat Guthaben, minimale Edits, Barcode-Downloads und Druck-PDFs
✅ Pygame-Adminmodus ist über die bestehende Admin-Karte erreichbar
🔲 Phase 8 Polish und Hardware-Validierung offen

| Area | Status | Notes |
|------|--------|-------|
| Gameplay core | ✅ | Login, Menu, Scan, Recipe, Math, Picker vorhanden |
| Session economy | ✅ | Balance, Earnings, Transactions, Session tracking vorhanden |
| UI overhaul | 🟡 | Neue Shell sowie asset-basierte Kassen- und Rezept-UI; Hardware-Test offen |
| Admin area | 🟡 | Remote-Admin plus Pygame-Quick-Admin vorhanden; Hardware-Test offen |
| Codex workflow | ✅ | `AGENTS.md` ist jetzt die führende Assistenz-Doku |

## What Was Done In This Session

### Initial Database Setup Discipline

- Die DB-Entscheidung wurde KISS festgelegt: Es gibt eine lokale `data/kasse.db` und ein initiales Setup-Skript, keine separate Demo-DB als Architekturkonzept.
- `tools/seed_database.py` ist jetzt standardmäßig nicht-destruktiv:
  - fehlende/leere DB wird initialisiert und mit Startdaten befüllt
  - vorhandene DB mit Produkten, Benutzern, Rezepten oder Runtime-Daten wird nicht überschrieben
  - vollständiger Neuaufbau geht nur bewusst über `uv run python tools/seed_database.py --reset`
- Die feste Carolin/Annelie-Konfiguration bleibt im Setup-Code und ist mit einem kurzen Kommentar als aktuelle Installation markiert.
- Doku aktualisiert:
  - `README.md`
  - `dev/PLAN.md`
  - `dev/ARCHITECTURE.md`
  - `dev/STATUS_REPORT.md`
- Admin-Schutz-Entscheidung dokumentiert: KISS-Version nutzt die Admin-Karte bzw. den passenden Barcode; kein Basic Auth, kein Web-Login, keine PIN.
- Verifikation:
  - `uv run ruff format src/ tools/`
  - `uv run ruff check src/ tools/`
  - `uv run python -m compileall src tools`
  - `uv run python tools/seed_database.py` verweigert erwartungsgemäß das Überschreiben der vorhandenen DB
  - `uv run python tools/seed_database.py --help`

### Remote Admin Implementation Pass

- FastAPI bleibt der Remote-Admin für Eltern im Heimnetz.
- Umgesetzt in diesem Pass:
  - Guthaben setzen und per `+1`, `+5`, `+10` aufladen
  - einfache `balance_adjustments`-Historie
  - minimale Edits für User, Produkte und Rezepte
  - `active`-Flags für User, Produkte und Rezepte
  - Admin-CSS aus dem Template in `src/admin/static/admin.css`
  - A4-PDF-Druckbögen für Karten, Rezepte, Produktlabels und alles zusammen
- Follow-up-Issues:
  - #5 printable barcode workflow wurde geschlossen
  - #6 Pygame-Adminmodus wurde umgesetzt und geschlossen

### On-Device Pygame Admin Pass

- Bestehender Admin-Barcode bleibt unverändert: `2000000000046`.
- `LoginScene` startet für Admin-User eine Session und wechselt direkt in `AdminScene`; Kinder-Logins gehen weiter ins Menü.
- `AdminScene` hat drei Touch-Tabs:
  - Status/QR: lokale IP, Serverstatus, Admin-URL und QR-Code
  - User & Konten: Saldo, Guthaben `-1`, `+1`, `+5`, `+10`, aktiv/inaktiv, Schwierigkeit und letzte Änderung
  - Hinweise: kurze Eltern-Hinweise zum Heim-WLAN und Remote-Admin
- Der Admin-User kann im Pygame-Admin nicht deaktiviert werden.
- `src/utils/admin_runtime.py` startet/stoppt den FastAPI-Server als verwalteten Hintergrundprozess.
- `src/utils/network.py` ermittelt die Heimnetz-IP und baut die URL `http://<ip>:8080`.
- Neue Dependency: `qrcode` für die QR-Surface im Pygame-Screen.
- Verifikation:
  - `uv run ruff format src/ tools/`
  - `uv run ruff check src/ tools/`
  - `uv run python -m compileall src tools`
  - Login-Smoke gegen temporäre DB: Admin-Barcode → `admin`, Kinderkarte → `menu`
  - AdminScene-Smoke gegen temporäre DB: Render nicht leer, Guthabenänderung schreibt `balance_adjustments`
  - Remote-Smoke: Server startet, `/users` antwortet mit 200, Stop beendet den verwalteten Prozess

### AdminScene Refactor Pass

- `src/scenes/admin.py` wurde ohne UI-Verhaltensänderung auf kleinere Rendering-Helfer geschnitten.
- Status-Tab trennt jetzt Panel-Layout, Statuszeilen, Server-Controls und QR-Rendering.
- User-&-Konten-Tab trennt User-Zeile, Zusammenfassung, Guthabenbuttons und Admin-/Schwierigkeitsbuttons.
- Das Klick-Register nutzt jetzt eine kleine `AdminButton`-Dataclass statt eines unbenannten Tuples.
- Verifikation:
  - `uv run ruff format src/ tools/`
  - `uv run ruff check src/ tools/`
  - `uv run python -m compileall src tools`
  - AdminScene-Smoke gegen temporäre DB: Tabs rendern, Button-Registration vorhanden, `+1`-Klick ändert Guthaben korrekt

### Project State + Backend Foundation

- Aktueller Stand geprüft: `master` enthält die Remote-Admin-Grundlage; `data/kasse.db` kann lokale Runtime-Änderungen enthalten und sollte nicht automatisch mitcommitted werden.
- GitHub-Issues geprüft:
  - #1 Validate cashier UI with kids on touch display
  - #2 Validate recipe UI with kids on touch display
  - #3 Define demo database workflow
  - #4 Split database module for admin backend
  - #5 Add printable barcode workflow
- Backend-/Admin-Schnitt vorbereitet:
  - Barcode-Präfixe, EAN-13-Check-Digit, Dateipfade und SVG-Erzeugung liegen jetzt zentral in `src/utils/barcodes.py`.
  - `src/admin/server.py` nutzt die zentrale Barcode-URL-Erzeugung statt eigener Dateinamenlogik.
  - `tools/seed_database.py` und `tools/generate_barcodes.py` sind aus der Ignorierliste herausgenommen und sollen versioniert werden.
  - `dev/ARCHITECTURE.md` ist jetzt ebenfalls zur Versionierung vorgesehen, weil es im Session-Start gelesen werden muss.
- Refactor-Fund für später: `src/utils/database.py` ist noch das größte Modul und sollte in einer separaten Runde in Schema, Queries und Transaktionslogik aufgeteilt werden.
- `python-barcode`-Doku geprüft: `Barcode.save(...)` hängt die Dateiendung selbst an; die neue Utility schreibt deshalb über den Pfad ohne Suffix.

### Verification In This Session

- Erfolgreich ausgeführt:
  - `uv run ruff format src/ tools/`
  - `uv run ruff check src/ tools/`
  - `uv run python -m compileall src tools`
  - `uv run python tools/generate_barcodes.py`
  - Admin-/Barcode-Import-Smoke-Test

## Previous Session Notes

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

### Cashier UI Analysis, Mockups, and First Assets

- Kassen-relevante Dateien geprüft:
  - `src/scenes/scan.py`
  - `src/scenes/picker.py`
  - `src/components/product_display.py`
  - `src/components/scrollable_cart.py`
  - `src/components/cart_item_row.py`
  - `src/scenes/checkout_mixin.py`
  - `src/ui/shell.py`
  - `src/utils/assets.py`
  - `src/utils/fonts.py`
- Bestehende Asset-Familien in `assets/340er/`, `assets/40er/`, `assets/50er/`, `assets/680er/` und `assets/ui/` geprüft.
- Lokale Ist-Screenshots der Kassen-UI erstellt:
  - `/tmp/carolins_kasse_cashier_verification/scan_empty_cart.png`
  - `/tmp/carolins_kasse_cashier_verification/scan_one_product.png`
  - `/tmp/carolins_kasse_cashier_verification/scan_many_products.png`
  - `/tmp/carolins_kasse_cashier_verification/scan_checkout_badge.png`
  - `/tmp/carolins_kasse_cashier_verification/picker_first_category.png`
- Analyse-Ergebnis: aktuelle Kassen-UI funktioniert, ist aber für nicht-lesende Kinder noch zu text- und tabellenlastig. Besonders `WARENKORB`, Hint-Texte, `GESAMT`, Checkout-Hinweistext und kleine +/- Buttons sollten durch stärkere Bildführung ersetzt oder deutlich reduziert werden.
- Zwei Mockup-Runden erstellt; die zweite Runde nutzt die 680er-Referenzbilder stärker als Stilanker:
  - `/tmp/carolins_kasse_cashier_mockups/mockup_refstyle_01_idle.png`
  - `/tmp/carolins_kasse_cashier_mockups/mockup_refstyle_01_idle_1024x600.png`
  - `/tmp/carolins_kasse_cashier_mockups/mockup_refstyle_02_active.png`
  - `/tmp/carolins_kasse_cashier_mockups/mockup_refstyle_02_active_1024x600.png`
- Erste transparente Kassen-UI-Assets mit `bg-remover`-Pipeline erstellt und in `assets/ui/cashier/` abgelegt:
  - `scan_hint.png`
  - `quantity_plus_button.png`
  - `quantity_minus_button.png`
  - `remove_from_cart_icon.png`
- Asset-Verifikation:
  - RGBA geprüft
  - transparente Ecken geprüft
  - Kontaktansicht: `/tmp/carolins_kasse_cashier_assets_contact.png`
  - Pygame-Asset-Loader mit `ui/cashier/...` erfolgreich getestet
- Hinweis: `bg-remover` hat bei den Plus/Minus-Quellen zuerst nur die weißen Symbole behalten. Die finalen Plus/Minus-Dateien wurden deshalb aus den geprüften Quellen per verbundenem Weiß-Hintergrund-Freisteller repariert; `rembg` wurde nicht verwendet.
- Follow-up-Issue für Hardware-/Kinder-Test erstellt: https://github.com/dweigend/carolins-kasse/issues/1

### Cashier UI Implementation Pass

- Kassen-UI asset-basiert umgesetzt, ohne Cart-/Checkout-Logik umzubauen und ohne zweite Shell einzuführen.
- Aktualisierte Dateien:
  - `src/scenes/scan.py`
  - `src/scenes/picker.py`
  - `src/scenes/checkout_mixin.py`
  - `src/components/product_display.py`
  - `src/components/scrollable_cart.py`
  - `src/components/cart_item_row.py`
  - `src/components/product_tile.py`
  - `src/components/checkout_receipt.py`
  - `src/components/insufficient_funds_popup.py`
  - `src/utils/assets.py`
- Neue Kassen-Assets in `assets/ui/cashier/`:
  - `badge_scan_hint.png`
  - `checkout_success.png`
  - `insufficient_funds.png`
  - `quantity_minus_button.png`
  - `quantity_plus_button.png`
  - `remove_from_cart_icon.png`
  - `scan_hint.png`
- Finaler Screenshot-Satz:
  - `/tmp/carolins_kasse_cashier_implementation/scan_empty_cart.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_one_product.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_many_products.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_checkout_badge.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_checkout_success.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_insufficient_funds.png`
  - `/tmp/carolins_kasse_cashier_implementation/picker_first_category.png`
- Visuelle Richtung:
  - Scan-Bereich ist jetzt eine große Bildbühne mit Scan-Hinweis oder großem Produktbild.
  - Warenkorb nutzt Basket-Icon, Produktbilder, Mengen-Badges und große Plus/Minus-Buttons.
  - Checkout nutzt Badge-Scan-Illustration, Coin+Zahl statt erklärendem Text und Icon-Bezahlbutton.
  - Receipt und Insufficient-Funds-Popup sind stärker bildgeführt.
- Verifikation:
  - `uv run ruff format src/`
  - `uv run ruff check src/`
  - `uv run python -m compileall src`
  - synthetischer Kassen-Interaktions-Smoke-Test mit Plus/Minus, Pay-Button und Picker-Auswahl
  - PNG-Alpha-/transparente-Ecken-Prüfung für `assets/ui/cashier/*.png`
  - Screenshot-Dimensions-/Nonblank-Prüfung für alle finalen Kassen-Screenshots
  - `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/homebrew/bin/timeout 3 uv run python main.py` initialisiert den Entry Point; Exit `124` ist erwarteter Timeout nach 3 Sekunden.

### Cashier UI Visual Feedback Pass

- Visuelles Feedback aus drei Screenshots systematisch umgesetzt:
  - leerer Scan-Zustand wirkt jetzt bildgeführt und ohne zweite leere Zielfläche
  - rechter Cart-Footer, Gesamtsumme und Bezahlbutton liegen höher und konkurrieren nicht mehr mit dem Shell-Footer
  - Cart-Zeilen und Produktkarte fitten oder kürzen lange Produktnamen zuverlässig innerhalb ihrer Fläche
  - Checkout-Badge-Overlay ist kompakter und weniger leer
  - Picker-Tabs rendern Icon und Text als gemeinsame Gruppe, damit `Backwaren` nicht überlappt
  - Erfolgsbeleg hält die Countdown-Zahl innerhalb der Dialogkarte
- Aktualisierte Screenshot-Prüfung:
  - `/tmp/carolins_kasse_cashier_implementation/scan_empty_cart.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_one_product.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_many_products.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_long_name_stress.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_checkout_badge.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_checkout_success.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_insufficient_funds.png`
  - `/tmp/carolins_kasse_cashier_implementation/picker_first_category.png`
- Verifikation erneut grün:
  - `uv run ruff format src/`
  - `uv run ruff check src/`
  - `uv run python -m compileall src`
  - synthetischer Kassen-Smoke-Test für Plus/Minus, Pay-Button und Picker-Auswahl
  - PNG-RGBA-/transparente-Ecken-Prüfung für `assets/ui/cashier/*.png`
  - Screenshot-Dimensions-/Nonblank-Prüfung für alle finalen Kassen-Screenshots
  - `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/homebrew/bin/timeout 3 uv run python main.py` initialisiert den Entry Point; Exit `124` ist erwarteter Timeout nach 3 Sekunden.

### Cashier UI Calm Background Pass

- Zweites visuelles Feedback umgesetzt: die Kassen-UI ist jetzt ruhiger, weil zentrale Flächen nicht mehr einzeln gezeichnet werden, sondern aus konsistenten PNG-Hintergründen kommen.
- Neue Mockup-Referenzen:
  - `/tmp/carolins_kasse_cashier_polish_mockups/mockup_calm_idle.png`
  - `/tmp/carolins_kasse_cashier_polish_mockups/mockup_checkout_table.png`
- Neue Kassen-Hintergrundassets in `assets/ui/cashier/`:
  - `panel_scan_bg.png`
  - `panel_cart_bg.png`
  - `cart_row_bg.png`
  - `cart_row_alt_bg.png`
  - `pay_button_enabled_bg.png`
  - `pay_button_disabled_bg.png`
  - `checkout_wait_card_bg.png`
  - `checkout_card_bg.png`
  - `checkout_payment_row_bg.png`
  - `checkout_earning_row_bg.png`
- Code-Anschluss:
  - `src/utils/assets.py` hat jetzt `get_raw(...)` für nicht quadratisch skalierte UI-Hintergründe.
  - `ProductDisplay`, `ScrollableCart`, `CartItemRow`, Checkout-Warteoverlay und Checkout-Beleg nutzen diese Raw-Assets.
  - Der leere Warenkorb zeigt keinen grauen Pay-Button mehr; Bezahlen erscheint erst, wenn etwas im Warenkorb liegt.
  - Der Checkout-Erfolgsbeleg zeigt jetzt zwei klare Buchungszeilen: zahlendes Kind rot mit Minus, kassierendes Kind grün mit Plus.
- Aktualisierte Screenshot-Prüfung:
  - `/tmp/carolins_kasse_cashier_implementation/scan_empty_cart.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_many_products.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_checkout_badge.png`
  - `/tmp/carolins_kasse_cashier_implementation/scan_checkout_success.png`
- Verifikation erneut grün:
  - `uv run ruff format src/`
  - `uv run ruff check src/`
  - `uv run python -m compileall src`
  - synthetischer Kassen-Smoke-Test für Plus/Minus, leeren Pay-Button, aktiven Pay-Button und Picker-Auswahl
  - Raw-Asset-Größenprüfung für alle neuen Hintergrund-PNGs
  - PNG-RGBA-/transparente-Ecken-Prüfung für `assets/ui/cashier/*.png`
  - Screenshot-Dimensions-/Nonblank-Prüfung
  - `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/homebrew/bin/timeout 3 uv run python main.py` initialisiert den Entry Point; Exit `124` ist erwarteter Timeout nach 3 Sekunden.

### Cashier Self-Checkout Salary Fix

- Economy-Exploit geschlossen: Wenn die eingeloggte Kassiererin mit ihrer eigenen Karte bezahlt, bekommt sie keinen Kassierlohn.
- `award_cashier_salary(...)` prüft jetzt primär die `customer_card_id` gegen die eingeloggte `cashier.card_id`; Namensvergleich bleibt nur als Fallback für alte Aufrufe.
- `CheckoutMixin` übergibt beim Bezahlen jetzt `customer.card_id`.
- Render-Probe für Selbstkauf ohne grüne `+5`-Zeile:
  - `/tmp/carolins_kasse_cashier_implementation/scan_checkout_self_purchase.png`
- Verifikation:
  - gezielter Python-Smoke-Test für Fremdkauf `+5`, Selbstkauf `0`, Fallback per Name `0`
  - `uv run ruff format src/`
  - `uv run ruff check src/`
  - `uv run python -m compileall src`

### Recipe UI Analysis, Mockups, Assets, and Implementation

- Aktueller Kassenstand vor der Rezeptarbeit als eigener Commit gesichert:
  - `a5e4b63 feat: redesign cashier UI`
  - `data/kasse.db` blieb ungestaged.
- Rezept-Ist-Screenshots erstellt:
  - `/tmp/carolins_kasse_recipe_verification/recipe_waiting.png`
  - `/tmp/carolins_kasse_recipe_verification/recipe_loaded_none.png`
  - `/tmp/carolins_kasse_recipe_verification/recipe_partial.png`
  - `/tmp/carolins_kasse_recipe_verification/recipe_complete.png`
  - `/tmp/carolins_kasse_recipe_verification/recipe_checkout_badge.png`
  - `/tmp/carolins_kasse_recipe_verification/recipe_checkout_success.png`
- Analyse-Ergebnis: Rezeptbereich war noch text-/checkboxlastig, Rezeptbild zu klein, Fortschritt und Kosten zu abstrakt, und der alte Bezahlbutton saß optisch zu nah am Shell-Footer.
- Neue Mockup-Referenzen:
  - `/tmp/carolins_kasse_recipe_mockups/mockup_recipe_idle.png`
  - `/tmp/carolins_kasse_recipe_mockups/mockup_recipe_active.png`
- Neue Rezept-Assets in `assets/ui/recipe/`:
  - `recipe_panel_bg.png`
  - `ingredient_list_bg.png`
  - `ingredient_row_pending_bg.png`
  - `ingredient_row_done_bg.png`
  - `recipe_scan_hint.png`
  - `recipe_complete_badge.png`
  - `recipe_pay_button_bg.png`
- Umsetzung:
  - `RecipeScene` bleibt im bestehenden Flow: Rezeptkarte scannen → Zutaten scannen → bezahlen.
  - Keine neue Rezeptlogik, keine neue Belohnungslogik, keine zweite Shell.
  - Linkes Panel zeigt großes Rezeptbild, Rezeptname, Fortschritt und Coin+Kosten.
  - Rechtes Panel zeigt Zutaten als bildgeführte Zeilen mit Produktbild, sekundärem Namen und großem Status-Kreis/Check-Badge.
  - Pay-Button erscheint erst, wenn alle Zutaten gesammelt sind.
  - `ChecklistItem` wurde zur visuellen Zutatenzeile erweitert.
- Finaler Screenshot-Satz:
  - `/tmp/carolins_kasse_recipe_implementation/recipe_waiting.png`
  - `/tmp/carolins_kasse_recipe_implementation/recipe_loaded_none.png`
  - `/tmp/carolins_kasse_recipe_implementation/recipe_partial.png`
  - `/tmp/carolins_kasse_recipe_implementation/recipe_complete.png`
  - `/tmp/carolins_kasse_recipe_implementation/recipe_checkout_badge.png`
  - `/tmp/carolins_kasse_recipe_implementation/recipe_checkout_success.png`
  - `/tmp/carolins_kasse_recipe_implementation/scan_regression_one_product.png`
- Verifikation:
  - `uv run ruff format src/`
  - `uv run ruff check src/`
  - `uv run python -m compileall src`
  - Rezept-Smoke-Test für Rezept-Scan, falsche Zutat, richtige Zutat, doppelte Zutat, vollständiges Rezept, Pay-Button und Checkout-Mode
  - Kassen-Regressionstest für Cart-Plus-Button
  - PNG-RGBA-/transparente-Ecken-/Größenprüfung für `assets/ui/recipe/*.png`
  - Screenshot-Dimensions-/Nonblank-Prüfung
  - `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/homebrew/bin/timeout 3 uv run python main.py` initialisiert den Entry Point; Exit `124` ist erwarteter Timeout nach 3 Sekunden.

### Recipe UI Visual Feedback Polish

- Visuelles Feedback aus den 18:00-Screenshots umgesetzt:
  - Startzustand nutzt jetzt eine größere eigene Rezeptkarten-Scan-Grafik auf Basis der bestehenden `kochbuch_gelb`-, Barcode- und Scanner-Assets.
  - Rezept- und Zutatencontainer wurden symmetrischer im Shell-Innenraum ausgerichtet; Außenabstände sind nun ruhiger und näher an der Kassen-UI.
  - Die Kostenanzeige im linken Rezeptpanel ist jetzt ein eigener Coin-Badge statt losem Coin+Zahl-Block.
  - `recipe_complete_badge.png` wurde ohne gelbe Artefakte neu erstellt.
  - Doppelte Pay-Button-Renderlogik aus `ScanScene` und `RecipeScene` wurde in `src/components/icon_pay_button.py` zusammengeführt.
- Aktualisierte Screenshot-Prüfung:
  - `/tmp/carolins_kasse_recipe_feedback/recipe_waiting.png`
  - `/tmp/carolins_kasse_recipe_feedback/recipe_loaded_none.png`
  - `/tmp/carolins_kasse_recipe_feedback/recipe_partial.png`
  - `/tmp/carolins_kasse_recipe_feedback/recipe_complete.png`
  - `/tmp/carolins_kasse_recipe_feedback/recipe_checkout_badge.png`
  - `/tmp/carolins_kasse_recipe_feedback/scan_regression_one_product.png`
- Verifikation:
  - `uv run ruff format src/`
  - `uv run ruff check src/`
  - `uv run python -m compileall src`
  - Rezept-Smoke-Test für falsche Zutat, richtige Zutat, doppelte Zutat, vollständiges Rezept und Pay-Button-Platzierung
  - Kassen-Regressionstest für den extrahierten gemeinsamen Pay-Button
  - PNG-RGBA-/transparente-Ecken-/sichtbares-Motiv-Prüfung für die erneuerten Rezept-Assets
- Follow-up-Issue für Hardware-/Kinder-Test erstellt: https://github.com/dweigend/carolins-kasse/issues/2

### Context Verified

- Bestehende App-Struktur, Plan-Dokumente und Admin-Backend geprüft
- GitHub-Issue-Kontext versucht zu laden; aktuell kam keine Issue-Liste zurück
- Git-Tree aufgeräumt: offene Code-, Asset-, Doku- und lokale DB-Testdaten geprüft und für getrennte Commits vorbereitet
- Checks liefen sauber: `uv run ruff check src/`, `uv run ruff format src/`, `uv run python -m compileall src`

## Current Risks / Open Questions

1. Die neue Kassen- und Rezept-UI wurde lokal per Screenshots und synthetischem Smoke-Test geprüft; ein echter Durchklick-Test auf App/Hardware bleibt offen.
2. Der Admin-Bereich hat Remote- und Kassen-Quick-Flows; nächste sinnvolle Phase sind Hardware-Test, Transaktionsansicht und spätere CRUD-Erweiterungen.
3. Hardware-Tests auf dem Raspberry Pi fehlen weiterhin für Touch, Scanner und Performance.
4. Das neue Rechenspiel inklusive Coin-Assets ist im Code verdrahtet, aber noch nicht auf dem Raspberry-Pi-Display mit echter USB-Numpad-Eingabe getestet.
5. Kassen- und Rezept-UI sind implementiert und visuell nachpoliert, aber noch nicht mit echter Scanner-/Touch-Hardware und Kindern validiert. Wichtig: `FrameShell` bleibt weiterhin die einzige Shell-/Footer-Wahrheit.

## Recommended Next Session

1. `uv run python main.py` am echten Display starten und Scan, Picker, Rezeptkarte, Zutaten-Scan, Plus/Minus, Checkout-Badge, Erfolg und zu-wenig-Geld durchklicken.
2. Issues #1 und #2 mit Kinder-/Touch-Testdaten füllen: was verstehen die Kinder ohne Text, wo tippen sie falsch, welche Buttons sind noch zu klein?
3. `data/kasse.db` weiterhin bewusst behandeln und nicht versehentlich mit UI-Änderungen committen.
4. Rechenspiel mit richtiger Eingabe, erster falscher Eingabe, zweiter falscher Eingabe und Session-Ende am Gerät durchtesten.
5. `uv run uvicorn src.admin.server:app --reload --port 8080` prüfen und entscheiden, ob Phase 7 bei FastAPI bleibt.

## Quick Start

```bash
uv run python main.py
uv run uvicorn src.admin.server:app --reload --port 8080
uv run uvicorn src.admin.server:app --host 0.0.0.0 --port 8080
uv run python tools/seed_database.py
uv run python tools/generate_printables.py
uv run ruff check src/
uv run ruff format src/
```
