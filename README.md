# Carolin's Kasse 🛒

A DIY self-checkout register for kids — because every child deserves their own barcode scanner.

---

## 📖 About

My daughter Carolin loves playing store. Like *really* loves it. And if you've ever been to a supermarket with a preschooler, you know the magnetic pull of those self-checkout scanners. She'd scan groceries all day if we let her.

So for her 4th birthday, I'm building her the real thing: a fully functional toy cash register with an actual barcode scanner, running on a Raspberry Pi, housed in a custom wooden case.

**The Goal:** Let kids play store while sneaking in some early math — adding prices, counting items, following recipe checklists, grouping products. All the intuitive mental models that make numbers click, wrapped in the joy of *beep beep beep*.

I couldn't find anything like this on the market. Toy registers exist, but none with real scanning, real products, and educational depth. So here we are.

---

## ✨ Features

- **Barcode Scanning** — Real USB scanner, real product lookups
- **Shopping Mode** — Scan items, manage cart, checkout
- **Recipe Mode** — Follow ingredient checklists (learning to read lists)
- **Math Games** — Practice addition & subtraction with prices
- **Multi-User** — Each child gets their own card, balance, and color theme
- **Touch + Numpad** — Works with touchscreen or physical numpad input

---

## 🔧 Hardware

| Component | Model |
|-----------|-------|
| Computer | Raspberry Pi Zero 2 W |
| Display | Elecrow 7" IPS Touch (1024×600) |
| Power | Anker 20K 87W (~20h runtime) |
| Scanner | USB Barcode Scanner |
| Input | USB Numpad |
| Case | Custom wooden housing (WIP) |

The whole setup runs on battery power — no cables, fully portable. Perfect for living room floor deployment.

---

## 🏗️ Tech Stack

- **Python 3.12+** with [pygame](https://www.pygame.org/) for graphics
- **SQLite** for products, users, and transactions
- **uv** for dependency management

```
src/
├── scenes/       # Screen states (menu, scan, recipe, etc.)
├── components/   # Reusable UI elements (buttons, badges)
└── utils/        # Helpers (assets, database)
```

---

## 🚀 Getting Started

```bash
# Clone
git clone https://github.com/dweigend/carolins_kasse.git
cd carolins_kasse

# Install dependencies
uv sync

# Run
uv run python main.py
```

**Note:** Runs windowed on desktop, fullscreen (KMSDRM) on Pi.

---

## 🤝 Want to Build One?

If you're interested in building something similar for your kids, feel free to reach out! I'm happy to share hardware tips, case designs, and lessons learned.

- **GitHub:** [@dweigend](https://github.com/dweigend)
- **Website:** [weigend.studio](https://weigend.studio)

---

## 📄 License

MIT — do whatever you want with it. If you build one, send pictures!

---

*Built with ❤️ for Carolin's 4th birthday.*
