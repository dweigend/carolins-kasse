# Kassen-UI Asset Plan

## Goal

This document tracks all visual assets that still need to be created for the next checkout UI overhaul.

Current implementation focus:
- Scan area
- Cart area
- Checkout flow
- Payment overlays
- Shell interaction targets

Not in the first implementation wave:
- Recipe UI refactor
- Math game UI refactor

## Workflow

1. Create the missing Illustrator assets listed below.
2. Generate 3-4 mockup reference images for the new checkout flow.
3. Pause implementation work.
4. Return with the exact local file paths to the generated mockups.
5. Start implementation and refactor based on the approved assets and mockups.

## Pause Gate

Implementation must not start before these inputs are available:

| Item | Status | Notes |
|---|---|---|
| Illustrator export plan reviewed | Open | This file is the source of truth |
| Mockup 01 path | Waiting | Empty cart / scan idle state |
| Mockup 02 path | Waiting | Filled cart / product scanned state |
| Mockup 03 path | Waiting | Payment modal / badge scan state |
| Mockup 04 path | Optional | Overflow cart / edge case state |

## Asset Table

| Priority | Area | Screen | Asset ID | What it replaces or supports | Target size (px) | Output filename | Mockup ref | Status | Notes |
|---|---|---|---|---|---:|---|---|---|---|
| P1 | Scan panel | Scan idle | `scan_state_idle` | Replaces text-only empty scan state | 220x140 | `scan_state_idle.png` | Mockup 01 | Open | Show scanner + product movement, no text required |
| P1 | Scan panel | Scan success | `scan_state_success` | Replaces `Produkt gescannt!` feedback | 120x120 | `scan_state_success.png` | Mockup 02 | Open | Positive success cue, should work without reading |
| P1 | Product hero | Scan | `product_hero_frame` | Supports the large left product card | 240x240 | `product_hero_frame.png` | Mockup 01-02 | Open | Optional decorative frame if plain white card feels too technical |
| P1 | Cart state | Empty cart | `cart_empty_state` | Replaces `Noch keine Produkte` | 160x160 | `cart_empty_state.png` | Mockup 01 | Open | Large, friendly empty-basket illustration |
| P1 | Cart header | Cart | `cart_header_icon` | Supports or replaces `WARENKORB` title | 56x56 | `cart_header_icon.png` | Mockup 01-02 | Open | Basket icon, should still read well at small size |
| P1 | Quantity control | Cart row | `quantity_minus_button` | Replaces small `-` control | 72x72 | `quantity_minus_button.png` | Mockup 02-04 | Open | Must be touch-friendly and visually unambiguous |
| P1 | Quantity control | Cart row | `quantity_plus_button` | Replaces small `+` control | 72x72 | `quantity_plus_button.png` | Mockup 02-04 | Open | Same family as minus button |
| P1 | Primary action | Cart footer | `pay_button_primary` | Replaces current text-heavy green button | 320x96 | `pay_button_primary.png` | Mockup 02-04 | Open | Main CTA, must stay clear on light background |
| P1 | Payment modal | Checkout overlay | `badge_scan_modal_hero` | Replaces emoji + instruction-heavy badge scan state | 240x240 | `badge_scan_modal_hero.png` | Mockup 03 | Open | Show badge + scanner relation visually |
| P1 | Shell action | Shared shell | `close_button_x` | Replaces small close affordance | 72x72 | `close_button_x.png` | Mockup 01-04 | Open | Large tap target; graphic should fit blue frame |
| P1 | Total display | Cart footer | `total_coin_badge` | Replaces text-heavy `GESAMT: ... Taler` | 220x72 | `total_coin_badge.png` | Mockup 02-04 | Open | Should support number overlay in code |
| P1 | Error state | Not enough balance | `insufficient_funds_state` | Supports insufficient funds popup | 220x160 | `insufficient_funds_state.png` | Mockup 04 | Open | Prefer visual comparison cue over explanation text |
| P1 | Success state | Checkout success | `checkout_success_state` | Supports receipt/success overlay | 180x180 | `checkout_success_state.png` | Mockup 03-04 | Open | Friendly completion cue |
| P2 | Product tile | Cart row | `product_thumbnail_frame` | Optional support frame for cart row product image | 64x64 | `product_thumbnail_frame.png` | Mockup 02-04 | Open | Only needed if row images need a consistent container |
| P2 | Scroll control | Cart list | `scroll_up_button` | Replaces ambiguous small top scroll element | 64x64 | `scroll_up_button.png` | Mockup 04 | Open | Only needed if explicit scroll buttons remain |
| P2 | Scroll control | Cart list | `scroll_down_button` | Replaces ambiguous small bottom scroll element | 64x64 | `scroll_down_button.png` | Mockup 04 | Open | Same family as scroll up button |
| P2 | Footer support | Shell footer | `coin_balance_icon` | Possible refinement of current coin icon | 48x48 | `coin_balance_icon.png` | Mockup 01-04 | Open | Keep only if existing asset no longer matches new visual language |
| P2 | Footer support | Shell footer | `balance_count_badge` | Optional support for current numeric balance | 160x56 | `balance_count_badge.png` | Mockup 01-04 | Open | Use only if plain number feels too raw next to new footer UI |

## Mockup Slots

| Mockup | Purpose | Expected content | Local path |
|---|---|---|---|
| Mockup 01 | Idle state | Empty cart, idle scanner, no product scanned | `TBD` |
| Mockup 02 | Active shopping state | Product scanned, populated cart, visible pay area | `TBD` |
| Mockup 03 | Payment modal state | Badge scan overlay, clear primary action hierarchy | `TBD` |
| Mockup 04 | Overflow edge state | Many cart rows, scroll/navigation state, error or funds edge case | `TBD` |

## Implementation Notes For Later

- First implementation wave should refactor the checkout core only.
- Recipe should stay out of the first UI wave and be revisited after the scan/cart/checkout architecture is stable.
- All new UI code should move toward shared layout primitives, shared modal rendering, and consistent font usage.
- Touch targets should be designed for children first, not for desktop precision.
