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
| Pi first-boot setup | Done | Automated Lite install path, systemd services, debug/update hooks |
| Regression tests | Active | 21-test unittest temp-DB and lifecycle suite for database, admin safety, atomic checkout, and scene resets |
| Hardware validation | Open | Pi, SEENGREAT USB hub, scanner, touch, children |
| Data module split | Open | Tracked as issue #4 |

## Active Priorities

1. **Scene-state and kiosk correctness bugs**
   - Treat reset scene state between kiosk users (#12) as implemented on
     `codex/kiosk-correctness` in commit `ef654b8`; close after review/merge.
   - Track recipe ingredient quantities correctly (#13).
   - Prevent inactive recipe ingredients from blocking completion (#17).
   - Make PickerScene reachable from the kiosk flow (#18).
   - Ignore barcode scanner input in math mode (#19).
   - Award recipe bonus only after successful recipe checkout (#20).
   - Add focused regression coverage around each risky scene or checkout path.

2. **Regression coverage maintenance**
   - Keep the 21-test temp-DB and lifecycle unittest suite green.
   - Expand coverage when the next risky write or scene-state path changes.
   - Treat scene reset between kiosk users (#12), atomic checkout/balance
     updates (#11), self-checkout balance refresh (#14), and SQLite foreign key
     enforcement (#16) as implemented on the current branch and ready to close
     after review/merge.

3. **Pi operations and hardware validation**
   - Add rollback safety to the update script (#23).
   - Show install, update, and backup status on the debug page (#24).
   - Cache fonts and scaled assets for Pi Zero runtime (#22).
   - Keep the validated SEENGREAT topology: leave the Pi USB data port empty while the shield is in Pi mode, then attach touch, scanner, and number pad downstream of the shield.
   - Validate cashier, recipe, scanner, number pad, checkout, Admin card, math mode, update, and QR flows on real hardware.
   - Record child and hardware observations in issues #1, #2, #7, and #8.

4. **Admin read-only history**
   - Add transaction history view.
   - Add earnings/session overview.
   - Keep exports/statistics simple until parents actually need them.

5. **Database boundary**
   - Split `src/utils/database.py` only in a dedicated pass.
   - Preserve behavior while separating schema/init, models, product/user/recipe queries, sessions, earnings, transactions, and admin balance changes.

6. **Later CRUD**
   - New products.
   - New users/cards.
   - Recipe creation/editing beyond active/name edits.
   - Image upload/copy workflow.

7. **Polish**
   - Sound effects.
   - Checkout/earning animations.
   - Error states on hardware.

## Current Decisions

- One local SQLite DB is used at runtime.
- Pi installs keep the runtime DB at `/var/lib/carolins-kasse/kasse.db`.
- SceneManager supports optional `on_enter()` and `reset_user_state()` scene
  lifecycle hooks. User changes and shell logout reset user-bound scene state;
  normal scene entry only runs the scene's own entry refresh.
- SQLite connections enable foreign key checks and a busy timeout.
- Checkout commits use an atomic `BEGIN IMMEDIATE` transaction and return a
  `CheckoutResult` or `CheckoutError`.
- `tools/seed_database.py` contains the fixed Carolin/Annelie setup and is non-destructive by default.
- First-boot installation must not assume optional Linux groups exist, and it must install from the intended repo ref or carry required installer files from bootfs.
- Kiosk admin protection stays KISS via physical Admin card.
- Browser mutating POST routes require the locally generated setup PIN/admin
  session plus CSRF tokens.
- The Pi stays on the home WiFi; no hotspot in v1.
- Hardware debugging uses SSH over WiFi so the Pi USB data bus can be isolated for OTG and hub tests.
- When the SEENGREAT shield is in Pi Zero hub mode, the Pi micro-USB data port must stay unused; downstream USB devices should connect through the shield.
- The shield topology is now validated on the Pi: QinHeng hub, QDTECH touch, M4 YX scanner, and SIGMACHIP number pad enumerate when all USB devices are connected through the shield.
- Print output target is A4 PDF sheets plus existing SVG barcode files.
- Asset creation should reuse existing `assets/340er/`, `assets/680er/`, and `assets/ui/` before adding new files.

## Definition Of Done For The Current Phase

- Real scanner reads child cards, Admin card, product labels, and recipe cards.
- Touch targets are usable by children on the 1024x600 display.
- Parents can start remote admin from the kiosk and open it by QR code.
- Parents can adjust balances without editing the DB manually.
- Generated print PDFs are usable for cutting cards/labels.
- Open child-testing notes are captured in GitHub issues.
