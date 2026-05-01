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
| Remote admin | Done | FastAPI pages, edits, balances, history, barcode links, print PDFs |
| Pygame admin | Done | Admin card, QR/status, balance controls, account overview |
| Pi first-boot setup | Done | Automated Lite install path, systemd services, debug/update hooks |
| Hardware validation | Open | Pi, SEENGREAT USB hub, scanner, touch, children |
| Data module split | Open | Tracked as issue #4 |

## Active Priorities

1. **Hardware and kid testing**
   - Fix the Pi first-boot installer regression tracked in issue #9 before the next clean automated install attempt.
   - Push or merge the installer branch before using `--repo-ref` on a fresh Pi, because the Pi clones from GitHub during first boot.
   - Validate automated first-boot setup on a freshly flashed Pi.
   - Validate the corrected SEENGREAT topology: leave the Pi USB data port empty while the shield is in Pi mode, then attach touch, scanner, and number pad downstream of the shield.
   - Validate the SEENGREAT hub as a normal USB hub on the Mac.
   - Validate the SEENGREAT hub on the Pi with `SW1 = 0` and `SW2 = 1`.
   - Validate cashier UI on Pi touch display with scanner.
   - Validate recipe UI with children.
   - Record observations in issues #1, #2, #7, and #8.

2. **Admin read-only history**
   - Add transaction history view.
   - Add earnings/session overview.
   - Keep exports/statistics simple until parents actually need them.

3. **Database boundary**
   - Split `src/utils/database.py` only in a dedicated pass.
   - Preserve behavior while separating schema/init, models, product/user/recipe queries, sessions, earnings, transactions, and admin balance changes.

4. **Later CRUD**
   - New products.
   - New users/cards.
   - Recipe creation/editing beyond active/name edits.
   - Image upload/copy workflow.

5. **Polish**
   - Sound effects.
   - Checkout/earning animations.
   - Error states on hardware.
   - Pi Zero performance pass.

## Current Decisions

- One local SQLite DB is used at runtime.
- Pi installs keep the runtime DB at `/var/lib/carolins-kasse/kasse.db`.
- `tools/seed_database.py` contains the fixed Carolin/Annelie setup and is non-destructive by default.
- First-boot installation must not assume optional Linux groups exist, and it must install from the intended repo ref or carry required installer files from bootfs.
- Kiosk admin protection stays KISS via physical Admin card.
- Browser debug/update actions require the locally generated setup PIN.
- The Pi stays on the home WiFi; no hotspot in v1.
- Hardware debugging uses SSH over WiFi so the Pi USB data bus can be isolated for OTG and hub tests.
- When the SEENGREAT shield is in Pi Zero hub mode, the Pi micro-USB data port must stay unused; downstream USB devices should connect through the shield.
- Print output target is A4 PDF sheets plus existing SVG barcode files.
- Asset creation should reuse existing `assets/340er/`, `assets/680er/`, and `assets/ui/` before adding new files.

## Definition Of Done For The Current Phase

- Real scanner reads child cards, Admin card, product labels, and recipe cards.
- Touch targets are usable by children on the 1024x600 display.
- Parents can start remote admin from the kiosk and open it by QR code.
- Parents can adjust balances without editing the DB manually.
- Generated print PDFs are usable for cutting cards/labels.
- Open child-testing notes are captured in GitHub issues.
