# Carolin's Kasse - Projektziel

## Was ist das?

Dieses Projekt ist eine spielerische Kasse für meine Tochter Carolin. Die Kasse wird das Herzstück ihres neuen Kaufladens sein, der aus Holz gebaut wird. Die Idee orientiert sich an den Selbstbedienungskassen, wie man sie zum Beispiel in Supermärkten findet – Carolin liebt diese Selbstbedienungskassen!

Die gesamte Software läuft auf einem Raspberry Pi Zero. An der Kasse sind ein Barcode-Scanner und ein Nummernpad angeschlossen. Das Display ist ein 7-Zoll-Touchscreen.

## Die Spielidee

Im Kern funktioniert die Kasse wie eine echte Selbstbedienungskasse: Man kann mit dem Handscanner Waren einscannen, dann piept es und das eingescannte Produkt wird der Liste hinzugefügt. Für Obst und Gemüse gibt es auf dem Bildschirm separate Buttons – genau wie im echten Supermarkt. Klickt man auf "Gemüse", erscheinen verschiedene Gemüsesorten als Bilder, und man kann die gewünschte Anzahl festlegen. Das gleiche gilt für Obst und Backwaren wie Brötchen oder Croissants.

Obwohl die Kasse einer Selbstbedienungskasse nachempfunden ist, wird sie im Spiel eher wie ein klassischer Tante-Emma-Laden betrieben: Ein Kind ist die Kassiererin, die anderen Kinder oder Erwachsene sind die Kunden. Die Kassiererin sucht die gewünschten Waren heraus, scannt sie ein und kassiert am Ende das Geld.

## Der Rezept-Modus

Der besondere Clou ist der Rezept-Modus. Es gibt physische Rezept-Karten mit Strichcodes. Für jedes Rezept braucht es eine bestimmte Anzahl an Zutaten. Wenn ein Rezept mit dem Barcode-Scanner eingescannt wird, erscheint eine Liste der benötigten Zutaten auf dem Bildschirm.

Carolin kann dann in ihrem Kaufladen die nötigen Sachen heraussuchen und einscannen – entweder mit dem Barcode-Scanner oder über die Touch-Auswahl am Bildschirm. Die Reihenfolge ist dabei egal. Wenn sie ein falsches Produkt scannt, das nicht auf der Rezept-Liste steht, gibt es einen Fehlerton und einen Hinweis.

Wenn alle Zutaten gesammelt sind, macht es "Pling", ein Haken erscheint, und es gibt eine Belohnungs-Animation. Dann erscheint die Summe, die bezahlt werden muss.

Es gibt fünf einfache Rezepte mit je 3-5 Zutaten:
- **Pfannkuchen:** Milch, Eier, Mehl, Zucker
- **Nudeln mit Tomatensauce:** Nudeln, Tomaten, Käse
- **Nudeln mit Käsesauce:** Nudeln, Käse, Milch, Butter
- **Haferflocken mit Kirschen:** Haferflocken, Kirschen, Milch
- **Kuchen:** Mehl, Eier, Zucker, Butter, Milch

Neben dem Rezept-Modus gibt es auch einen freien Einkaufs-Modus: Dann wird einfach nur die Kundenkarte gescannt, und man kann kaufen, was man will – ohne Vorgaben.

## Das Bezahlkarten-System

Jedes Kind hat eine eigene Bezahlkarte mit einem Strichcode. Wenn man den Strichcode scannt, sieht man, wie viel Guthaben auf der Karte ist. Die Währung heißt "Taler" und jede Karte startet mit 10 Talern.

Die Preise sind bewusst günstig gehalten (0,5 bis 2 Taler pro Produkt), damit man für wenig Arbeit möglichst viel kaufen kann – es ist ja schließlich ein Spiel! Das Guthaben wird permanent in der Kasse gespeichert, so als wäre es auf der Karte selbst gespeichert. Jedes Mal wenn man die Kasse einschaltet, ist das alte Guthaben noch da.

Wenn das Geld nicht reicht, kann man die Sachen nicht kaufen – es gibt dann eine Fehlermeldung.

## Geld verdienen

Es gibt mehrere Möglichkeiten, neues Geld für die Bezahlkarte zu verdienen:

### Kassiererin-Arbeit
Als Kassiererin bekommt man einen Stundenlohn plus einen Bonus für jede erfolgreiche Transaktion. Wichtig: Wenn die Kasse nicht benutzt wird (Inaktivität), gibt es auch keinen Lohn – so kann man das System nicht "hacken". Der verdiente Lohn wird oben in der Ecke als Taler-Zähler visualisiert.

### Rechenspiele
Es gibt einfache Rechenspiele, die mit dem Nummernpad bedient werden. Die Spiele sind für die Altersgruppe 4-8 Jahre ausgelegt:

- **Für Carolin (4 Jahre):** Grundlegende Übungen wie Punkte zählen und einer Zahl zuordnen (●●●● = 4)
- **Einfache Rechenaufgaben:** 2 + 2 = ? (mit visueller Unterstützung durch Punkte)
- **Für ältere Kinder wie Annelie:** Schwierigere Aufgaben wie 5 + 5 oder 2 × 3
V
Die Schwierigkeit bestimmt die Belohnung: Schwierigere Aufgaben geben mehr Taler. So werden die Kinder motiviert, wirklich Mathe zu lernen und nicht nur einfache Aufgaben zu wiederholen. Die Schwierigkeitsstufe kann für jedes Kind individuell im Admin-Bereich eingestellt werden.

## Benutzer-Erkennung und Login

Wenn die Kinder spielen, sollen sie sich mit ihrer Karte einloggen. Der Login ist klar erkennbar:

- Wenn Carolin ihre Karte scannt, ist der Bildschirm mit einem **blauen Rand** umrandet
- Wenn Annelie ihre Karte scannt, ist der Bildschirm mit einem **roten Rand** umrandet
- Oben in der Ecke steht der Name und ein kleines Symbol, damit die Kinder wissen, wer gerade eingeloggt ist
- Beim Login erscheint kurz ein Pop-up: "Hallo Carolin!" oder "Hallo Annelie!"

Da jedes Kind ein eigenes Profil hat, bekommt Annelie auch andere (schwierigere) Rechenspiele als Carolin.

### Gast-Karten
Neben Carolin und Annelie gibt es auch Gast-Karten für andere Kinder. Diese starten immer mit 10 Talern und können zurückgesetzt werden. Beim ersten Scan einer Gast-Karte kann man vielleicht sogar seinen Namen eingeben.

## Admin-System

Es gibt eine spezielle Admin-Barcode-Karte für die Eltern. Wenn diese gescannt wird, kann man:

- Guthaben auf Karten aufladen
- Gast-Karten zurücksetzen
- Die Schwierigkeitsstufe der Rechenspiele pro Kind einstellen
- Die Produkt-Datenbank verwalten (Produkte hinzufügen, entfernen, Preise ändern)
- System-Einstellungen anpassen

## Technische Anforderungen

### Hardware
- Raspberry Pi Zero W (512MB RAM, Single Core)
- 7" Display (HDMI, 800×480px)
- USB Barcode-Scanner (emuliert Tastatur)
- USB Nummernpad
- Holz-Gehäuse (selbstgebaut)

### Software-Anforderungen
- Die Software muss mit den begrenzten Ressourcen des Pi Zero laufen
- Persistente Datenbank für Produkte, Benutzer und Guthaben
- Remote-Zugang über SSH für Wartung und Updates
- Barcode-Generator-Tool zum Erstellen und Drucken von Barcodes für die Spielwaren

### Produkt-Datenbank
Im Backend gibt es eine Datenbank mit allen Strichcodes und den damit verknüpften Produkten, sowie allen Produkten ohne Strichcode (wie Bananen). Diese Datenbank muss anpassbar sein, weil Spielzeug verloren gehen oder Neues hinzukommen kann.
