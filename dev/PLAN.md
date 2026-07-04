# Development Plan

## North Star

Make Carolin's Kasse gift-ready for real play: reliable scanner/touch flows,
clear child-facing UI, parent-friendly admin, printable cards/labels, and safe
local data handling.

## Current Milestones

| Area | Status | Notes |
|---|---|---|
| Core kiosk | Done | Login, menu, shopping, picker, checkout, recipe, math |
| Economy | Done | Balances, sessions, earnings, transactions |
| UI shell | Done | Shared frame, footer, user colors, asset-based scene direction |
| Remote admin | Done | FastAPI pages, secured mutating POSTs, balances, barcode links, print PDFs |
| Pygame admin | Done | Admin card, QR/status, balance controls, account overview |
| Pi first-boot setup | Done | Automated Lite install path, systemd services, rollback-safe update hook, debug/update/backup observability |
| Regression tests | Active | 54-test unittest temp-DB and lifecycle suite for database, admin safety, atomic checkout, scene resets, recipe correctness, picker routing, math scanner filtering, Pi update rollback, debug status, and Pi update unit installation |
| Hardware validation | Open | Pi, SEENGREAT USB hub, scanner, touch, children |
| Data module split | Open | Tracked as issue #4 |

## Current Branch Coverage

The current `codex/pi-ops-safety` branch covers these open issues and should
close or update them after review/merge:

- #23 Add rollback safety to Pi update script.
- #24 Show install, update, and backup status on debug page.
- #28 Start the kiosk service without waiting for `network-online.target`.

## Active Priorities

1. **Number pad reliability**
   - Fix keypad digit handling when Pygame/SDL sends keypad keycodes with empty
     unicode text (#27).
   - Validate with the local raw keypad capture before and after the app fix.

2. **Pi performance**
   - Cache fonts and scaled assets for Pi Zero runtime (#22).
   - Remove NumPy paper texture generation from startup (#29).
   - Lazy-load admin and non-start scenes outside the cold path (#30).
   - Keep the deployed #28 systemd dependency fix validated on the Pi.
   - Keep changes measurable against the 1024x600 kiosk path.

3. **Hardware and child validation**
   - Keep the validated SEENGREAT topology: leave the Pi USB data port empty while the shield is in Pi mode, then attach touch, scanner, and number pad downstream of the shield.
   - Validate cashier, recipe, scanner, number pad, checkout, Admin card, math mode, update, and QR flows on real hardware.
   - Record child and hardware observations in issues #1, #2, #7, #8, and #9.

4. **Admin read-only history**
   - Add transaction history view.
   - Add earnings/session overview.
   - Keep exports/statistics simple until parents actually need them.

5. **Database boundary**
   - Split `src/utils/database.py` only in a dedicated pass.
   - Preserve behavior while separating schema/init, models, product/user/recipe queries, sessions, earnings, transactions, and admin balance changes.

6. **Regression coverage maintenance**
   - Keep the 54-test temp-DB and lifecycle unittest suite green.
   - Expand coverage when the next risky write, scene-state, or Pi operations path changes.
   - Use the local `carolins-kasse-debug` skill for repeatable SSH diagnostics,
     local checks, and safe Pi update/restart/backup actions.

7. **Later CRUD**
   - New products.
   - New users/cards.
   - Recipe creation/editing beyond active/name edits.
   - Image upload/copy workflow.

8. **Polish**
   - Sound effects.
   - Checkout/earning animations.
   - Error states on hardware.

## Current Decisions

- One local SQLite DB is used at runtime.
- Pi installs keep the runtime DB at `/var/lib/carolins-kasse/kasse.db`.
- SceneManager supports optional `on_enter()` and `reset_user_state()` scene
  lifecycle hooks. User changes and shell logout reset user-bound scene state;
  normal scene entry only runs the scene's own entry refresh.
- ScanScene can route into PickerScene for touch product selection while keeping
  scanner checkout and cart state intact.
- MathGameScene filters fast scanner-style digit bursts, including unterminated
  bursts, so scanner input does not leak into answer entry.
- `tools/pi_update.sh` records the previous commit before pulling and rolls
  back to it after post-pull failures before restarting the kiosk.
- SQLite connections enable foreign key checks and a busy timeout.
- Checkout commits use an atomic `BEGIN IMMEDIATE` transaction and return a
  `CheckoutResult` or `CheckoutError`.
- `tools/seed_database.py` contains the fixed Carolin/Annelie setup and is non-destructive by default.
- First-boot installation must not assume optional Linux groups exist, and it must install from the intended repo ref or carry required installer files from bootfs.
- Kiosk admin protection stays KISS via physical Admin card.
- Browser mutating POST routes require the locally generated setup PIN/admin
  session plus CSRF tokens.
- The PIN-protected debug page is the lightweight Pi operations dashboard for
  service state, install/update/backup state, backup timer, failed units, and
  short logs.
- The Pi stays on the home WiFi; no hotspot in v1.
- Hardware debugging uses SSH over WiFi so the Pi USB data bus can be isolated for OTG and hub tests.
- When the SEENGREAT shield is in Pi Zero hub mode, the Pi micro-USB data port must stay unused; downstream USB devices should connect through the shield.
- The shield topology is now validated on the Pi: QinHeng hub, QDTECH touch, M4 YX scanner, and SIGMACHIP number pad enumerate when all USB devices are connected through the shield.
- Raw Linux input validation confirms the SIGMACHIP number pad sends `KP1`,
  `KP2`, `KP3`, `NUMLOCK`, and `KPENTER`; the remaining issue is app-level
  keypad keycode handling (#27).
- Local repeatable Pi diagnostics live in the private Codex skill
  `/Users/davidweigend/.codex/skills/carolins-kasse-debug/`.
- Print output target is A4 PDF sheets plus existing SVG barcode files.
- Asset creation should reuse existing `assets/340er/`, `assets/680er/`, and `assets/ui/` before adding new files.

## Definition Of Done For The Current Phase

- Real scanner reads child cards, Admin card, product labels, and recipe cards.
- Touch targets are usable by children on the 1024x600 display.
- Parents can start remote admin from the kiosk and open it by QR code.
- Parents can adjust balances without editing the DB manually.
- Generated print PDFs are usable for cutting cards/labels.
- Open child-testing notes are captured in GitHub issues.
