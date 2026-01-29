# Asset-Produktionsplan

**Display:** 1024 × 600 px | **Stil:** Paper-cut / Flat Design

---

## Ordnerstruktur

```
assets/
├── master/                    # Alle 600×600 Master-Dateien
│   ├── products/              # 87 Lebensmittel, Spielzeug, etc.
│   ├── icons/                 # 25 UI-Icons
│   ├── buttons/               # 6 Button-Grafiken
│   ├── avatars/               # 6 User-Avatare
│   ├── emojis/                # 6 Smileys
│   ├── digits/                # 18 Zahlen 0-9, Euro-Münzen
│   ├── frames/                # 4 Rahmen
│   └── recipes/               # 3 Rezeptbilder
├── export/                    # Generierte Exports (S/M/L)
├── fonts/
└── sounds/
```

---

## Design-System

**Basis-Einheit:** 60px (600px Höhe ÷ 10)

| Größe | Quadrat | Rechteck (2:1) | Radius | Verwendung |
|-------|---------|----------------|--------|------------|
| **S** | 60×60 | 120×60 | 12px | Icons, kleine Buttons (+/-) |
| **M** | 120×120 | 240×120 | 24px | Produkte, Standard-Buttons |
| **L** | 180×180 | 360×180 | 36px | Menu-Tiles, große Buttons |

**Master-Größe:** 600×600 px → Wird auf S/M/L skaliert

---

## Farbpalette

```
Background:     #FDF6EC (Cream)
Primary Orange: #F59E0B
Success Green:  #22C55E
Error Red:      #EF4444
Carolin Blue:   #3B82F6
Menu Blue:      #60A5FA
Menu Red:       #DC2626
Menu Green:     #16A34A
Menu Yellow:    #EAB308
Brown/Wood:     #92400E
Text Dark:      #1F2937
White:          #FFFFFF
```

---

## Asset-Status

### Icons (`master/icons/`) - 25 vorhanden

| Dateiname | Status | Beschreibung |
|-----------|--------|--------------|
| `icon_check.png` | ✅ | Grüner Haken |
| `icon_cross.png` | ✅ | Rotes X |
| `icon_checkbox_empty.png` | ✅ | Leere Checkbox |
| `icon_checkbox_checked.png` | ✅ | Checkbox mit Haken |
| `icon_checkbox_false.png` | ✅ | Checkbox mit X |
| `icon_home.png` | ✅ | Home-Icon |
| `icon_settings.png` | ✅ | Zahnrad |
| `icon_help.png` | ✅ | Fragezeichen |
| `icon_arrow_left.png` | ✅ | Pfeil links |
| `icon_arrow_right.png` | ✅ | Pfeil rechts |
| `icon_arrow_up.png` | ✅ | Pfeil oben |
| `icon_arrow_down.png` | ✅ | Pfeil unten |
| `icon_cart.png` | ✅ | Einkaufswagen |
| `icon_pot.png` | ✅ | Kochtopf |
| `icon_register.png` | ✅ | Kasse |
| `icon_moneybag.png` | ✅ | Geldsack |
| `icon_thumbs_up.png` | ✅ | Daumen hoch |
| `icon_thumbs_down.png` | ✅ | Daumen runter |
| `icon_star.png` | ✅ | Stern |
| `icon_search.png` | ✅ | Lupe |
| `icon_trash.png` | ✅ | Mülleimer |
| `icon_clock.png` | ✅ | Uhr |
| `icon_sound_mute.png` | ✅ | Ton aus |
| `icon_sound_quiet.png` | ✅ | Ton leise |
| `icon_sound_loud.png` | ✅ | Ton laut |

### Buttons (`master/buttons/`) - 6 vorhanden

| Dateiname | Status | Beschreibung |
|-----------|--------|--------------|
| `btn_green.png` | ✅ | Grüner Button |
| `btn_red.png` | ✅ | Roter Button |
| `btn_brown.png` | ✅ | Brauner Button |
| `btn_up.png` | ✅ | Button hoch |
| `btn_plus.png` | ✅ | Plus-Button |
| `btn_minus.png` | ✅ | Minus-Button |

### Avatare (`master/avatars/`) - 6 vorhanden

| Dateiname | Status | Beschreibung |
|-----------|--------|--------------|
| `avatar_carolin.png` | ✅ | Carolin |
| `avatar_annelie.png` | ✅ | Annelie |
| `avatar_admin.png` | ✅ | Admin-Badge |
| `avatar_child_blue.png` | ✅ | Kind blau |
| `avatar_child_green.png` | ✅ | Kind grün |
| `avatar_child_yellow.png` | ✅ | Kind gelb |

### Emojis (`master/emojis/`) - 6 vorhanden

| Dateiname | Status | Beschreibung |
|-----------|--------|--------------|
| `emoji_happy.png` | ✅ | 😊 Fröhlich |
| `emoji_laugh.png` | ✅ | 😂 Lachend |
| `emoji_sad.png` | ✅ | 😢 Traurig |
| `emoji_surprised.png` | ✅ | 😮 Überrascht |
| `emoji_neutral.png` | ✅ | 😐 Neutral |
| `emoji_unhappy.png` | ✅ | 😟 Unglücklich |

### Frames (`master/frames/`) - 4 vorhanden

| Dateiname | Status | Beschreibung |
|-----------|--------|--------------|
| `frame_blue.png` | ✅ | Blauer Rahmen |
| `frame_red.png` | ✅ | Roter Rahmen |
| `frame_purple.png` | ✅ | Lila Rahmen |
| `frame_orange.png` | ✅ | Oranger Rahmen |

### Digits (`master/digits/`) - 18 vorhanden

| Dateiname | Status | Beschreibung |
|-----------|--------|--------------|
| `digit_0.png` | ✅ | Ziffer 0 |
| `digit_1.png` | ✅ | Ziffer 1 |
| `digit_2.png` | ✅ | Ziffer 2 |
| `digit_3.png` | ✅ | Ziffer 3 |
| `digit_4.png` | ✅ | Ziffer 4 |
| `digit_5.png` | ✅ | Ziffer 5 |
| `digit_6.png` | ✅ | Ziffer 6 |
| `digit_7.png` | ✅ | Ziffer 7 |
| `digit_8.png` | ✅ | Ziffer 8 |
| `digit_9.png` | ✅ | Ziffer 9 |
| `digit_0_circle.png` | ✅ | Ziffer 0 rund |
| `digit_blank_red.png` | ✅ | Leere rote Ziffer |
| `coin_0_euro.png` | ✅ | 0 Euro Münze |
| `coin_1_euro.png` | ✅ | 1 Euro Münze |
| `coin_2_euro.png` | ✅ | 2 Euro Münze |
| `coin_3_euro.png` | ✅ | 3 Euro Münze |
| `coin_4_euro.png` | ✅ | 4 Euro Münze |
| `coin_5_euro.png` | ✅ | 5 Euro Münze |

### Rezepte (`master/recipes/`) - 3 vorhanden

| Dateiname | Status | Beschreibung |
|-----------|--------|--------------|
| `recipe_pancakes.png` | ✅ | Pfannkuchen |
| `recipe_scrambled_eggs.png` | ✅ | Rührei |
| `recipe_cheese_bread.png` | ✅ | Käsebrot |

### Produkte (`master/products/`) - 87 vorhanden

Siehe `dev/ASSET_CATALOG.md` für vollständige Liste.

---

## UI-Mockups

Alle Screen-Designs und Wireframes: **`dev/UI_SCREENS.md`**

| Datei | Screen |
|-------|--------|
| `ui/05_main_menu.png` | Hauptmenü |
| `ui/07_scan_screen_annelie.png` | Scan-Screen (Annelie) |
| `ui/08_scan_screen_carolin.png` | Scan-Screen (Carolin) |
| `ui/03_recipe_mode.png` | Rezept-Modus |
| `ui/06_product_picker.png` | Produkt-Picker |
| `ui/09_calculator_math_game.png` | Rechenspiel |

---

## Fehlende Assets

### 🔴 Hohe Priorität - Menu Tiles (180×180)

| Asset | Farbe | Screen | Beschreibung |
|-------|-------|--------|--------------|
| `tile_shopping.png` | #60A5FA (blau) | Hauptmenü | Einkaufswagen mit Gemüse |
| `tile_recipe.png` | #DC2626 (rot) | Hauptmenü | Kochtopf mit Dampf |
| `tile_math_game.png` | #16A34A (grün) | Hauptmenü | "1 2 3" Zahlen |
| `tile_cashier.png` | #EAB308 (gelb) | Hauptmenü | Kasse |

### 🟡 Mittlere Priorität - Buttons mit Text

| Asset | Text | Screen | Beschreibung |
|-------|------|--------|--------------|
| `btn_pay.png` | "BEZAHLEN" | Scan-Screen | Orange Button |
| `btn_add_to_cart.png` | "IN DEN KORB" | Produkt-Picker | Orange Button |
| `btn_back_to_store.png` | "ZURÜCK ZUM LADEN" | Rezept-Modus | Orange Button |
| `btn_finish_recipe.png` | "REZEPT FERTIGSTELLEN" | Rezept-Modus | Grau/Grün Button |
| `btn_calculate.png` | "BERECHNEN" | Rechenspiel | Orange Button |

### 🟢 Niedrige Priorität - Produkte

Aus Sprite-Referenz (`ui/04_product_sprites_reference.jpg`) fehlen:

| Asset | Deutsch | Kategorie |
|-------|---------|-----------|
| `cheese.png` | Käse | Dairy |
| `chicken.png` | Hähnchen | Meat |
| `fish.png` | Fisch | Meat |
| `rice.png` | Reis | Pantry |
| `pasta.png` | Nudeln | Pantry |
| `water.png` | Wasser | Drinks |
| `soda.png` | Limo | Drinks |

### ⚪ Optional

| Asset | Beschreibung |
|-------|--------------|
| `icon_barcode.png` | Barcode-Scanner Icon |
| `bg_main.png` | Haupthintergrund (1024×600) |
| `frame_green.png` | Grüner Rahmen (für Annelie) |

---

## Export

- **Format:** PNG-24, transparent
- **Farbprofil:** sRGB
- **Naming:** `category_name.png`
