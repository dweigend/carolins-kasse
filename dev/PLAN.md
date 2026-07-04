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
| Pi first-boot setup | Implemented | Automated Lite install path, systemd services, rollback-safe update hook, debug/update/backup observability; still needs one clean first-boot validation |
| Regression tests | Active | 86-test pipeline suite for database, admin safety, atomic checkout, scene resets, recipe correctness, picker routing, math scanner filtering, Pi update rollback, debug status, Pi update unit installation, cashier feedback components, operation scripts, bootfs prep, Pi debug CLI output, database import compatibility, and product/recipe/user public API compatibility |
| Hardware validation | Open | Pi, SEENGREAT USB hub, scanner, touch, children |
| Data module split | Active | #4 first slices moved database models/types plus product, recipe, and basic user CRUD query helpers; other SQL/query families remain |
| Quality gate | Active | `uv run poe check` runs Ruff, `ty`, Vulture, Deptry, jscpd, Radon, and pytest-cov |
| Test coverage | Covered for current refactor safety | Issue #25 is closed; add focused tests with the next risky change |
| UI handler complexity | Done for current Radon baseline | Focused #26 pass removed current C/D findings |

## Open Issue Snapshot

`gh issue list --limit 30` on 2026-07-04 shows these issues as open:

- #31 Pi unreachable over SSH for deployment validation: blocks safe Pi update
  and #27/#29/#30 hardware acceptance until power/WiFi/address is confirmed.
- #27 Accept keypad digit keycodes when unicode text is empty: deployed, but
  still needs physical app-path validation with the SIGMACHIP keypad.
- #29 Remove NumPy paper texture generation from kiosk cold start: deployed,
  but still needs clean power-cycle first-screen timing and admin smoke.
- #30 Lazy-load admin and non-start scenes outside the kiosk cold path:
  deployed, but still needs clean power-cycle first-screen timing and admin
  smoke.
- #22 Cache fonts and scaled assets for Pi Zero runtime: partially covered;
  keep the remaining work as a profiling backlog.
- #1, #2, #7, #8, and #9 remain hardware, child, and first-boot validation
  issues.
- #4 database module split has started: `database_models.py` owns row models,
  checkout result/error types, and column-list constants; `database_products.py`
  owns product query helpers; `database_recipes.py` owns recipe query helpers;
  `database_users.py` owns basic user CRUD query helpers; other query-family
  splits remain.

## Active Priorities

1. **Number pad reliability**
   - Validate the deployed keypad digit fix with the physical app path (#27).
   - Reuse the local raw keypad capture when app behavior and Linux events
     disagree.

2. **Pi performance**
   - Clean power-cycle the Pi and measure the deployed #29/#30 cold-start
     changes on the first visible 1024x600 screen.
   - Smoke the admin flow after lazy loading, especially Admin card, server QR,
     and remote admin launch.
   - Continue #22 only where profiling still shows repeated font, scale, or
     render cost.

3. **Hardware and child validation**
   - Resolve #31 before attempting Pi update or acceptance: confirm power,
     WiFi, DHCP address, and SSH reachability.
   - Use `kasse-debug.sh acceptance` as the short read-only hardware sign-off
     path for #27/#29/#30: number pad app test, clean power-cycle first-screen
     timing, and admin smoke.
   - Keep detail diagnosis in the focused helper commands: `status`, `usb`,
     `boot`, `logs`, and `keypad`.
   - Keep the validated SEENGREAT topology: leave the Pi USB data port empty while the shield is in Pi mode, then attach touch, scanner, and number pad downstream of the shield.
   - Validate cashier, recipe, scanner, number pad, checkout, Admin card, math mode, update, and QR flows on real hardware.
   - Run one clean first-boot validation; the implementation is in place, but
     the prior fresh install still needed manual service-start recovery.
   - Record child and hardware observations in issues #1, #2, #7, #8, and #9.

4. **Admin read-only history**
   - Add transaction history view.
   - Add earnings/session overview.
   - Keep exports/statistics simple until parents actually need them.

5. **Database boundary**
   - Continue #4 in small behavior-preserving slices.
   - `src/utils/database_models.py` now owns row dataclasses, checkout
     result/error types, and column-list constants.
   - `src/utils/database_products.py` owns product SQL helpers that receive an
     existing connection and do not commit.
   - `src/utils/database_recipes.py` owns recipe SQL helpers that receive an
     existing connection and do not commit.
   - `src/utils/database_users.py` owns basic user CRUD SQL helpers that receive
     an existing connection and do not commit.
   - Keep `src/utils/database.py` import-compatible while separating
     schema/init, product/user/recipe queries, sessions, earnings,
     transactions, and admin balance changes.
   - Do not move `process_checkout`, `update_user_balance`, or transaction
     writes without focused safety tests and a narrow review.

6. **Regression coverage maintenance**
   - Keep the 86-test pipeline suite green.
   - Add focused tests with the next risky scene, database, admin, or
     Pi-operations change instead of keeping a broad standing coverage issue.
   - Expand coverage when the next risky write, scene-state, or Pi operations path changes.
   - Use the local `carolins-kasse-debug` skill for repeatable SSH diagnostics,
     local checks, and safe Pi update/restart/backup actions.
   - Run `uv run poe check` as the single local quality command before review.

7. **UI handler complexity**
   - `Numpad.handle_event` has been reduced from Radon D to A with direct
     component tests.
   - `ScrollableCart.handle_event` has been reduced out of the Radon C list
     with direct component tests.
   - `RecipeScene._handle_barcode` has been split into branch-specific scan
     helpers; the current Radon pipeline reports no C/D findings.
   - Keep refactors behavior-preserving and covered by targeted smoke tests.

8. **Later CRUD**
   - New products.
   - New users/cards.
   - Recipe creation/editing beyond active/name edits.
   - Image upload/copy workflow.

9. **Polish**
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
- First-boot installation must not assume optional Linux groups exist, and it must install from the intended repo ref or carry required installer files from bootfs. The implementation is in place, but #7/#9 stay open until one clean first boot completes without manual service-start recovery.
- Kiosk admin protection stays KISS via physical Admin card.
- Browser mutating POST routes require the locally generated setup PIN/admin
  session plus CSRF tokens.
- The PIN-protected debug page is the lightweight Pi operations dashboard for
  service state, install/update/backup state, backup timer, failed units, and
  short logs.
- `uv run poe check` is the code-quality pipeline. Ruff format/lint, `ty`,
  Vulture, Deptry, jscpd, and pytest-cov are strict gates; Radon reports
  future complexity findings.
- The Pi stays on the home WiFi; no hotspot in v1.
- Hardware debugging uses SSH over WiFi so the Pi USB data bus can be isolated for OTG and hub tests.
- When the SEENGREAT shield is in Pi Zero hub mode, the Pi micro-USB data port must stay unused; downstream USB devices should connect through the shield.
- The shield topology is now validated on the Pi: QinHeng hub, QDTECH touch, M4 YX scanner, and SIGMACHIP number pad enumerate when all USB devices are connected through the shield.
- Raw Linux input validation confirms the SIGMACHIP number pad sends `KP1`,
  `KP2`, `KP3`, `NUMLOCK`, and `KPENTER`; the app-level keypad fix is deployed
  and still needs physical app validation (#27).
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
