# Raspberry Pi Setup

Diese Anleitung richtet einen Raspberry Pi Zero 2 W so ein, dass Carolin's
Kasse nach dem Boot automatisch startet und Updates über den Admin-Bereich
ausgelöst werden können.

## 1. SD-Karte flashen

1. Raspberry Pi Imager öffnen.
2. **Raspberry Pi OS Lite 64-bit** auswählen.
3. In den Imager-Einstellungen setzen:
   - Hostname: `carolins-kasse`
   - Benutzer: `kasse`
   - WLAN: Heimnetz
   - SSH: aktiviert
   - Locale/Timezone: Deutschland
4. Image auf die SD-Karte schreiben.
5. Die SD-Karte nach dem Schreiben gemountet lassen.

## 2. First-Boot-Installer vorbereiten

Auf dem Mac im Projektordner ausführen:

```bash
uv run python tools/pi_prepare_boot.py
```

Wenn die Boot-Partition nicht automatisch gefunden wird:

```bash
uv run python tools/pi_prepare_boot.py /Volumes/bootfs
```

Das Script schreibt einen einmaligen First-Boot-Hook auf `bootfs`. Es bricht ab,
wenn `cmdline.txt` bereits einen fremden `systemd.run`-Hook enthält. In diesem
Fall zuerst prüfen, ob der Raspberry Pi Imager noch eine eigene
Ersteinrichtung eingetragen hat.

## 3. Erster Boot

1. SD-Karte in den Raspi stecken.
2. Raspi starten.
3. Der erste Boot installiert nur den persistenten Installer und rebootet.
4. Nach dem Reboot installiert der Raspi automatisch:
   - minimale Systempakete
   - `uv`
   - das GitHub-Repo nach `/opt/carolins-kasse`
   - Python 3.13 und Projektabhängigkeiten
   - systemd Services
   - lokale Datenpfade und Admin-PIN
5. Danach startet `carolins-kasse.service` die Kasse.

Der Installationslog liegt auf dem Pi unter:

```bash
/var/lib/carolins-kasse/install.log
```

## 4. Zugriff und Debug

SSH:

```bash
ssh kasse@carolins-kasse.local
```

Diagnose per SSH:

```bash
cd /opt/carolins-kasse
.venv/bin/python tools/pi_debug.py
```

Der Web-Admin zeigt unter `/debug` Systemstatus, Git-Version, Dienste, Backups
und Logs. Der PIN liegt auf dem Pi unter:

```bash
/etc/carolins-kasse/admin-pin
```

Die Kasse selbst benötigt weiterhin nur die Admin-Karte.

## 5. Updates

Im Web-Admin unter **Debug** den PIN eingeben und **Update starten** wählen.

Der Update-Service macht:

1. Kasse stoppen
2. Datenbank sichern
3. `git pull --ff-only`
4. `uv sync --frozen --no-dev`
5. Compile-Check
6. Barcodes und Druck-PDFs regenerieren
7. Kasse neu starten

Manuell per SSH:

```bash
sudo systemctl start carolins-kasse-update.service
journalctl -u carolins-kasse-update.service -n 80 --no-pager
```

## 6. Backups

Die Runtime-Datenbank liegt auf dem Pi außerhalb des Git-Checkouts:

```bash
/var/lib/carolins-kasse/kasse.db
```

Backups liegen unter:

```bash
/var/backups/carolins-kasse/
```

Manuelles Backup:

```bash
sudo systemctl start carolins-kasse-backup.service
```

Der Timer `carolins-kasse-backup.timer` erstellt täglich ein Backup.

## 7. Hardware-Smoke-Test

Nach erfolgreicher Installation testen:

1. Kasse bootet automatisch.
2. Touch funktioniert auf dem 1024x600 Display.
3. Admin-Karte `2000000000046` öffnet den Kassen-Admin.
4. Kinderkarten scannen.
5. Produktlabels scannen.
6. Rezeptkarten scannen.
7. Checkout speichert Transaktionen.
8. Web-Admin per QR-Code öffnen.
9. Debug-PIN entsperrt `/debug`.
10. Update startet und erhält die Datenbank.
