# Spezifikation und Datenarchitektur für die Type-Ahead- und Kategorisierungsfunktion einer intelligenten Einkaufslisten-Applikation

## 1. Einleitung und architektonischer Kontext

Die Entwicklung moderner, nutzerzentrierter Einkaufslisten-Applikationen erfordert eine hochgradig strukturierte Datenarchitektur im Hintergrund, die in der Lage ist, natürliche Spracheingaben in Echtzeit zu verarbeiten, semantisch zu klassifizieren und mit kontextuellen Metadaten anzureichern. Die vorliegende Spezifikation definiert die architektonischen, logischen und datenstrukturellen Anforderungen zur Erweiterung einer bestehenden Applikation um eine prädiktive "Type-Ahead"-Funktion (Autovervollständigung), ein dynamisches Tagging-System für Mengen und Ausprägungen sowie eine automatisierte, tiefgreifende Warengruppen-Kategorisierung.

Das System wird unter der spezifischen Prämisse entworfen, dass die Implementierung durch "Google Jules" erfolgt. Google Jules operiert als autonomer, asynchroner KI-Coding-Agent, der sich direkt in bestehende Repositories integriert, den vollständigen Kontext der Codebasis analysiert und Aufgaben wie die Implementierung neuer Features in einer sicheren Cloud-Umgebung ausführt. Jules nutzt sandboxed Environments (virtuelle Maschinen), um Code-Änderungen zu generieren und Pull Requests (PRs) zu erstellen, ohne die Produktionszweige vor einer expliziten Freigabe zu tangieren. Die vorliegende Dokumentation dient als detailliertes Pflichtenheft und Datengrundlage, um den Jules-Agenten via Command-Line-Interface (CLI) präzise zu steuern und das komplexe Datenmodell der deutschen Lebensmittel- und Drogerielandschaft in relationale oder dokumentenbasierte Datenbankstrukturen zu überführen.

## 2. Technische Spezifikation der Type-Ahead-Funktion

Die Type-Ahead-Funktion zielt darauf ab, die kognitive Belastung des Nutzers und die Interaktionszeit drastisch zu reduzieren, indem proaktiv Vorschläge unterbreitet werden. Dies erfordert eine hochperformante Suchinfrastruktur, die auf einer lokalen Datenbankinstanz (Edge Computing auf dem Endgerät, z.B. SQLite, Room oder Realm) operiert, um Netzwerklatenzen zu eliminieren.

### 2.1 Trigger-Logik, Debouncing und Fuzzy Matching

Um die Performance zu optimieren und unnötige Re-Renders der Benutzeroberfläche zu vermeiden, unterliegt der Auslöser der Suche strikten algorithmischen Restriktionen:

*   **Schwellenwert (Threshold):** Die Query-Execution wird exakt ab der Eingabe des dritten Zeichens (`length >= 3`) initiiert. Tippt der Nutzer "Was", triggert das System den Suchlauf und liefert Ergebnisse wie "Wasser", "Waschmittel" oder "Wassermelone" zurück.
*   **Debouncing-Intervall:** Da Nutzer in unterschiedlichen Geschwindigkeiten tippen, muss ein Debounce-Intervall von 250 bis 300 Millisekunden implementiert werden. Der Such-Algorithmus pausiert, bis der Nutzer für diesen Zeitraum keine weitere Taste drückt, wodurch eine Flut an asynchronen Datenbankabfragen verhindert wird.
*   **Fuzzy Search und phonetische Algorithmen:** Die Suche muss eine hohe Fehlertoleranz aufweisen. Eine Implementierung der Levenshtein-Distanz (Toleranz von 1-2 Operationen) ist zwingend, sodass die Eingabe von "Tomta" sofort den Vorschlag "Tomate" generiert. Für den deutschen Markt ist zudem die Integration der Kölner Phonetik empfehlenswert, um gleichklingende, aber anders geschriebene Artikel (z.B. "Zeleri" statt "Sellerie") korrekt aufzulösen.

### 2.2 UI-Präsentation: Das Vorschlags-Modal (Popup)

Anstelle einer flachen In-Line-Liste erfordert die Architektur ein dediziertes Interaktionsfenster.

*   **Darstellungsebene:** Sobald der Nutzer den Button "Neuen Artikel hinzufügen" betätigt, wird ein neues modales Overlay (Popup) initialisiert. Das Eingabefeld erhält sofort den Fokus (Autofocus).
*   **Vorschlags-Rendering:** Die Suchergebnisse werden als antippbare Kacheln (List Items) innerhalb des Popups gerendert. Die maximale Anzahl der sichtbaren Vorschläge sollte auf acht bis zehn limitiert werden, um den kognitiven Overhead zu minimieren (Hick'sches Gesetz).
*   **Typografisches Highlighting:** Die übereinstimmende Zeichenfolge aus der Suchanfrage muss in den Vorschlagswerten visuell hervorgehoben werden (z.B. durch Fettdruck: **Was**ser).

## 3. Datenmodellierung: Das Tagging-System und die Kachel-UI

Ein zentrales Feature der erweiterten Applikation ist die sofortige Anreicherung eines ausgewählten Artikels mit spezifischen Metadaten. Die Analyse der bereitgestellten UI-Mockups offenbart ein hochentwickeltes Tagging-System. Sobald ein Artikel aus dem Type-Ahead-Popup selektiert wird, muss das System nahtlos in eine Detail-Auswahl übergehen, bevor das Element final auf der Einkaufsliste als Kachel (Tile) persistiert wird.

### 3.1 Analyse der Tag-Strukturen (Referenz: "Details zu Milch")

Das zweite visuelle Referenzdokument ("Details zu Milch") definiert die funktionale Tiefe dieses Systems. Es zeigt eine Matrix aus vorausgewählten, kontextsensitiven Buttons, die sich in verschiedene semantische Klassen unterteilen lassen:

1.  **Numerische Quantifikatoren (Stückzahl/Gebinde):** `1`, `2`, `3`, `4`, `6`, `12`.
2.  **Volumen/Gewicht-Spezifikatoren:** `1l`.
3.  **Produktspezifische Eigenschaften (Fettgehalt bei Milch):** `0,1%`, `0,7%`, `1,5%`, `3,5%`, `3,8%`.
4.  **Ernährungs- und Qualitätsprädikate:** `Bio`, `Soja`, `Hafer`, `Reis`.
5.  **Verarbeitungszustand:** `haltbar` (H-Milch).
6.  **Globale Einkaufs-Prioritäten (Meta-Tags):** `Dringend` (mit rennendem Männchen-Icon), `Angebot` (mit Prozent-Icon), `Wenn's passt` (mit Regal-Icon).
7.  **Freitext-Feld:** `Eigene Details notieren`.

### 3.2 Polymorphe Architektur der Tags

Die Implementierung dieser Funktionalität erfordert ein polymorphes Datenbankschema. Nicht jeder Artikel kann mit jedem Tag kombiniert werden (die Option "3,8%" ergibt bei "Toilettenpapier" keinen Sinn). Die Architektur erfordert daher die Unterscheidung in drei Tag-Klassen:

*   **Klasse A: Globale Meta-Tags.** Diese stehen bei absolut *jedem* Artikel zur Verfügung. Hierzu gehören die Prioritäten (`Dringend`, `Wenn's passt`) sowie preisliche Konstellationen (`Angebot`, `XXL-Packung`).
*   **Klasse B: Warengruppen-Tags.** Diese Tags sind an eine gesamte Kategorie gebunden. Alle Artikel der Kategorie "Obst & Gemüse" erhalten standardmäßig das Tag `Bio` und `Regional`. Alle flüssigen Artikel erhalten Volumen-Tags (`0,5l`, `1l`, `1,5l`).
*   **Klasse C: Artikel-spezifische Tags.** Diese sind hochgradig granular und exklusiv an einen Datenbankeintrag (SKU) gebunden. Nur der Artikel "Milch" (und Derivate) triggert die Fettgehalt-Tags (`1,5%`, `3,8%`). Nur "Kaffee" triggert `Ganze Bohnen` oder `Gemahlen`.

Sobald der Nutzer diese Tags antippt, verfärben sie sich (Active State). Beim Bestätigen werden diese Attribute in der JSON-Payload des Artikels gespeichert und direkt als kleine "Pills" auf der Kachel des Artikels in der Hauptansicht der Applikation gerendert, was eine optimale visuelle Erfassung beim Gang durch den Supermarkt gewährleistet.

## 4. Neu-Definition der Taxonomie und automatische Kategorisierung

Die automatische Zuweisung eines hinzugefügten Artikels zu einer bestimmten Kategorie ist entscheidend, um die Einkaufsliste nach den logischen Laufwegen eines Supermarktes zu sortieren, was Laufwege minimiert und Frustration verhindert.

### 4.1 Kritik an der bestehenden Kategorisierung

Das erste visuelle Referenzdokument zeigt eine bestehende, unzureichende Kategorisierung: `Obst & Gemüse`, `Backwaren`, `Allgemein`, `Getränke`, `Kühlregal`, `Fleisch & Fisch`, `Drogerie`.
Diese Struktur verletzt das Prinzip der gegenseitigen Ausschließlichkeit (Mutually Exclusive, Collectively Exhaustive - MECE). Der Begriff `Kühlregal` beschreibt einen physikalischen Ort, keine Warengruppe. Ein Steak (Fleisch & Fisch) oder ein Joghurt (Kühlregal) lassen sich hier nicht eindeutig trennen, was algorithmisch zu Konflikten führt. Die Kategorie `Allgemein` ist ein Anti-Pattern im Daten-Design, das unweigerlich zu einer unstrukturierten Restmenge führt.

### 4.2 Das konsolidierte deutsche LEH-Kategorienmodell

Basierend auf gängigen Supermarkt-Layouts und zur Reduzierung der Komplexität für den Endnutzer, wird die Taxonomie auf 8 essenzielle Hauptkategorien verdichtet. Diese bilden einen logischen Einkaufsweg ab und minimieren Sortieraufwand:

1. Obst & Gemüse
2. Brot & Backwaren
3. Fleisch & Fisch
4. Milchprodukte & Tiefkühlkost
5. Vorratskammer (Trockensortiment, Konserven & Snacks)
6. Getränke & Genussmittel
7. Drogerie, Haushalt & Tierbedarf
8. Sonstiges (Für unklare oder artikelübergreifende Waren)

## 5. Master-Taxonomie: Die exhaustive Datenbank deutscher Artikel

Der Kernauftrag dieser Spezifikation ist die Bereitstellung eines ausnahmslos vollständigen Datensatzes für den deutschen Markt zur Initialisierung der Type-Ahead-Datenbank. Die folgenden Tabellen definieren die Seed-Data, einsortiert in die 8 Hauptkategorien. Die Spalte "Typische Mengen-Tags" und "Spezifische Konstellations-Tags" spiegeln exakt die Logik des "Details zu Milch"-Popups wider.

*Hinweis zur Datenverarbeitung für Google Jules: Die Tags `Dringend`, `Angebot` und `Wenn's passt` gelten global für alle folgenden Einträge und werden in der Tabellenstruktur als implizit vorhanden vorausgesetzt, um Redundanzen zu vermeiden.*

### 5.1 Kategorie 1: Obst & Gemüse
Diese Kategorie bildet meist den Eingangsbereich von Supermärkten.

| Artikelbezeichnung (Type-Ahead Ziel) | Primäre Warengruppe | Typische Mengen-Tags (Numerisch / Gebinde) | Spezifische Konstellations-Tags (Ausprägungen) |
| :--- | :--- | :--- | :--- |
| Apfel / Äpfel | Obst & Gemüse | 1, 2, 3, 4, 5, 6, 1kg Netz, 2kg Netz | Bio, Regional, Braeburn, Elstar, Pink Lady, Streuobst, Lose |
| Banane / Bananen | Obst & Gemüse | 1, 2, 3, 4, 5, Staude, 1kg | Bio, Fairtrade, Chiquita, Essreif |
| Birne / Birnen | Obst & Gemüse | 1, 2, 3, 4, 500g, 1kg | Bio, Regional, Abate Fetel, Conference, Lose |
| Erdbeeren | Obst & Gemüse | 1, 2, 250g Schale, 500g Schale | Bio, Regional, Süß, Gewaschen |
| Himbeeren | Obst & Gemüse | 1, 2, 125g Schale, 250g Schale | Bio, Regional |
| Heidelbeeren / Blaubeeren | Obst & Gemüse | 1, 2, 125g, 300g, 500g Schale | Bio, Kulturheidelbeeren, Waldheidelbeeren |
| Brombeeren | Obst & Gemüse | 1, 2, 125g Schale | Bio, Regional |
| Johannisbeeren | Obst & Gemüse | 1, 2, 250g Schale | Rot, Schwarz, Bio |
| Weintrauben / Trauben | Obst & Gemüse | 1, 500g Schale, 1kg | Hell, Dunkel, Kernlos, Bio, Süß |
| Wassermelone | Obst & Gemüse | 1, 1/2 Stück, 1/4 Stück | Kernarm, Bio, Mini-Melone |
| Zuckermelone (Galia/Honig) | Obst & Gemüse | 1, 2 | Essreif, Bio |
| Orange / Apfelsine | Obst & Gemüse | 1, 2, 3, 1kg Netz, 2kg Netz, 3kg | Bio, Saftorangen, Unbehandelte Schale |
| Mandarine / Clementine | Obst & Gemüse | 1, 2, 1kg Netz, 1,5kg Netz | Bio, Kernlos, Blattmandarinen |
| Zitrone | Obst & Gemüse | 1, 2, 3, 4, 3er Netz, 500g | Bio, Unbehandelte Schale, Saft |
| Limette | Obst & Gemüse | 1, 2, 3, 4, 4er Netz | Bio, Unbehandelte Schale |
| Grapefruit / Pampelmuse | Obst & Gemüse | 1, 2, 3 | Bio, Rosa, Weiß |
| Pfirsich | Obst & Gemüse | 1, 2, 3, 4, 500g Schale | Plattpfirsich, Bio, Regional, Lose |
| Nektarine | Obst & Gemüse | 1, 2, 3, 4, 500g Schale | Weißfleischig, Gelbfleischig, Bio |
| Pflaume / Zwetschge | Obst & Gemüse | 1, 2, 500g, 1kg | Bio, Regional |
| Süßkirschen | Obst & Gemüse | 1, 500g Schale, 1kg | Bio, Regional, Knorpelkirschen |
| Kiwi | Obst & Gemüse | 1, 2, 3, 4, 4er Pack, 1kg Korb | Bio, Gold (Gelb), Grün, Essreif |
| Mango | Obst & Gemüse | 1, 2, 3 | Essreif, Bio, Flugmango |
| Avocado | Obst & Gemüse | 1, 2, 3, 2er Netz | Hass, Essreif, Bio, Fuerte |
| Ananas | Obst & Gemüse | 1, 2 | Extra Sweet, Essreif, Geschält (To-Go) |
| Granatapfel | Obst & Gemüse | 1, 2, 3 | Essreif, Bio |
| Papaya | Obst & Gemüse | 1, 2 | Essreif |
| Feige (frisch) | Obst & Gemüse | 1, 2, 3, 4, 5 | Bio, Blau, Grün |
| Kaki / Persimon | Obst & Gemüse | 1, 2, 3, 4 | Bio, Kernlos |
| Tomate / Rispentomaten | Obst & Gemüse | 1, 2, 3, 4, 500g Rispe, 1kg | Bio, Regional, Holland, Lose |
| Cherrytomaten | Obst & Gemüse | 1, 2, 250g Schale, 500g Schale | Bio, Datteltomaten, Süß, Snacktomaten |
| Fleischtomaten | Obst & Gemüse | 1, 2, 3, 4 | Bio, Ochsenherz |
| Salatgurke | Obst & Gemüse | 1, 2, 3 | Bio, Regional, Minigurken, Snackgurken |
| Paprika | Obst & Gemüse | 1, 2, 3, 4, 3er Mix (500g) | Rot, Gelb, Grün, Spitzpaprika, Bio, Lose |
| Kartoffeln | Obst & Gemüse | 1kg, 1,5kg, 2kg, 2,5kg, 5kg Sack | Bio, Festkochend, Vorwiegend festk., Mehlig |
| Süßkartoffel | Obst & Gemüse | 1, 2, 3, 1kg, Lose | Bio |
| Zwiebeln | Obst & Gemüse | 1, 2, 3, 1kg Netz, 2kg Netz | Gemüsezwiebeln, Rote Zwiebeln, Bio, Schalotten |
| Knoblauch | Obst & Gemüse | 1, 2, 3 Knollen, 3er Netz, 200g | Bio, Frischer Knoblauch, Solo-Knoblauch |
| Karotten / Möhren | Obst & Gemüse | 1, 2, 1kg Bund, 1kg Sack, 2kg Sack | Bio, Bundmöhren (mit Grün), Waschmöhren |
| Eisbergsalat | Obst & Gemüse | 1, 2 | Bio, Regional |
| Kopfsalat | Obst & Gemüse | 1, 2 | Bio, Freiland, Gewächshaus |
| Lollo Rosso / Lollo Bionda | Obst & Gemüse | 1, 2 | Bio, Regional |
| Rucola / Rauke | Obst & Gemüse | 1, 2, 125g Schale | Bio, Gewaschen |
| Feldsalat | Obst & Gemüse | 1, 2, 150g Schale | Bio, Gewaschen, Wurzel-frei |
| Romana-Salat / Salatherzen | Obst & Gemüse | 1, 2, 2er Pack, 3er Pack | Bio, Mini-Romana |
| Spinat (frisch) | Obst & Gemüse | 1, 2, 500g Beutel, 250g | Babyspinat, Bio, Gewaschen |
| Zucchini | Obst & Gemüse | 1, 2, 3, 4, 500g, 1kg | Bio, Regional, Grün, Gelb |
| Aubergine | Obst & Gemüse | 1, 2, 3 | Bio, Regional |
| Brokkoli | Obst & Gemüse | 1, 2, 3, 500g | Bio, Regional |
| Blumenkohl / Karfiol | Obst & Gemüse | 1, 2 | Bio, Regional |
| Kohlrabi | Obst & Gemüse | 1, 2, 3, 4 | Bio, Mit Laub |
| Rotkohl / Blaukraut (frisch) | Obst & Gemüse | 1, 2 | Bio, Regional |
| Weißkohl | Obst & Gemüse | 1, 2 | Bio, Regional |
| Spitzkohl | Obst & Gemüse | 1, 2 | Bio, Regional |
| Wirsing | Obst & Gemüse | 1, 2 | Bio, Regional |
| Rosenkohl (frisch) | Obst & Gemüse | 1, 2, 500g Netz, 750g | Bio, Regional |
| Grünkohl (frisch) | Obst & Gemüse | 1, 500g Beutel, 1kg Sack | Bio, Gerupft, Am Strunk |
| Lauch / Porree | Obst & Gemüse | 1, 2, 3 Stangen | Bio, Regional |
| Knollensellerie | Obst & Gemüse | 1, 2 | Bio |
| Staudensellerie | Obst & Gemüse | 1, 2 | Bio, Regional |
| Radieschen | Obst & Gemüse | 1, 2, 3 Bund | Bio, Regional |
| Rettich (Weiß / Schwarz) | Obst & Gemüse | 1, 2 | Bio, Regional |
| Rote Bete (frisch) | Obst & Gemüse | 1, 2, 500g, 1kg | Bio, Gekocht (vakuum) |
| Spargel | Obst & Gemüse | 1, 2, 500g Bund, 1kg | Weiß, Grün, Regional, Bio, Geschält |
| Fenchel | Obst & Gemüse | 1, 2, 3 | Bio |
| Kürbis | Obst & Gemüse | 1, 2 | Hokkaido, Butternut, Bio, Regional |
| Champignons (Pilze) | Obst & Gemüse | 1, 2, 250g Schale, 400g Schale | Weiß, Braun, Bio, Riesenchampignons |
| Pfifferlinge (frisch) | Obst & Gemüse | 1, 2, 200g, 400g Korb | Bio, Saison |
| Kräuter (Petersilie / Schnittlauch)| Obst & Gemüse | 1, 2, 3 Bund, 1 Topf | Glatt, Kraus, Bio, Regional |
| Kräuter (Basilikum / Minze)| Obst & Gemüse | 1, 2, 3 Bund, 1 Topf | Bio |
| Ingwer (frisch) | Obst & Gemüse | 1, 2, 100g, 250g | Bio |
| Kurkuma (frisch) | Obst & Gemüse | 1, 2, 100g | Bio |
| Chili / Peperoni (frisch) | Obst & Gemüse | 1, 2, 3, 50g Schale | Rot, Grün, Bio, Scharf |

### 5.2 Kategorie 2: Brot & Backwaren

| Artikelbezeichnung (Type-Ahead Ziel) | Primäre Warengruppe | Typische Mengen-Tags (Numerisch / Gebinde) | Spezifische Konstellations-Tags (Ausprägungen) |
| :--- | :--- | :--- | :--- |
| Brot (Allgemein) | Brot & Backwaren | 1, 2, 500g, 750g, 1kg | Laib, Geschnitten, Frisch, Aufback |
| Vollkornbrot / Schwarzbrot | Brot & Backwaren | 1, 2, 500g Packung | Bio, Sauerteig, Abgepackt, Ohne Hefe |
| Weizenmischbrot / Graubrot | Brot & Backwaren | 1, 2, 500g, 750g, 1kg | Laib, Geschnitten, Frisch (Bäcker) |
| Toastbrot | Brot & Backwaren | 1, 2, 250g, 500g, 750g | Vollkorn, Buttertoast, Sandwich, Dreikorn |
| Brötchen / Semmeln | Brot & Backwaren | 1, 2, 3, 4, 5, 6, 8, 10, 5er Pack | Weizen, Körner, Aufbackbrötchen, Frisch, Bio |
| Laugengebäck (Brezel/Stange) | Brot & Backwaren | 1, 2, 3, 4, 5, 6, 2er Pack, TK 10er | Frisch, Tiefkühl zum Aufbacken, Bäcker, Salz |
| Croissant | Brot & Backwaren | 1, 2, 3, 4, 4er Pack, 6er Pack | Butter, Schoko, Lauge, Frisch, Aufback |
| Baguette / Ciabatta | Brot & Backwaren | 1, 2, 3, 2er Pack | Französisch, Aufback, Knoblauch, Vollkorn |
| Fladenbrot | Brot & Backwaren | 1, 2 | Sesam, Schwarzkümmel, Frisch |
| Wrap / Tortilla | Brot & Backwaren | 1, 2, 6er Pack, 8er Pack | Weizen, Vollkorn, Mais, Glutenfrei |
| Knäckebrot | Brot & Backwaren | 1, 2, 200g, 250g Packung | Roggen, Sesam, Bio, Ballaststoffreich |
| Pumpernickel | Brot & Backwaren | 1, 2, 250g, 500g | Bio, Dose, Packung |
| Zwieback | Brot & Backwaren | 1, 2, 225g, 500g | Vollkorn, Zuckerfrei, Bio |
| Reiswaffeln / Maiswaffeln | Brot & Backwaren | 1, 2, 100g, 130g Rolle | Bio, Ungesalzen, Mit Schokolade |
| Kuchen / Torte | Brot & Backwaren | 1 Stück, Ganzer Kuchen, 400g | Rührkuchen, Tiefkühl, Obstboden |

### 5.3 Kategorie 3: Fleisch & Fisch

| Artikelbezeichnung (Type-Ahead Ziel) | Primäre Warengruppe | Typische Mengen-Tags (Numerisch / Gebinde) | Spezifische Konstellations-Tags (Ausprägungen) |
| :--- | :--- | :--- | :--- |
| Hackfleisch (Gemischt) | Fleisch & Fisch | 1, 2, 300g, 400g, 500g, 1kg | Rind & Schwein, Bio, Haltungsform 4, SB, Theke |
| Rinderhackfleisch | Fleisch & Fisch | 1, 2, 400g, 500g | Bio, Mager, Haltungsform 4, SB, Theke |
| Schweineschnitzel | Fleisch & Fisch | 1, 2, 3, 4, 400g, 500g, 2 Stk | Bio, SB-Packung, Theke, Paniert |
| Schweinefilet | Fleisch & Fisch | 1, 2, 500g, 1kg | Am Stück, Medaillons, Bio |
| Schweinebraten | Fleisch & Fisch | 1, 1kg, 1,5kg | Krustenbraten, Nacken, Bio |
| Rindersteak / Rumpsteak | Fleisch & Fisch | 1, 2, 3, 4, 200g, 400g | Dry Aged, Bio, Theke, SB |
| Rindergulasch | Fleisch & Fisch | 1, 2, 400g, 500g, 1kg | Handgeschnitten, Bio, Theke |
| Rinderbraten | Fleisch & Fisch | 1, 1kg, 1,5kg | Schulter, Tafelspitz, Bio |
| Hähnchenbrustfilet | Fleisch & Fisch | 1, 2, 400g, 600g, 1kg | Bio, Natur, Mariniert, Haltungsform 4, Theke |
| Hähnchenschenkel / Keulen | Fleisch & Fisch | 1, 2, 600g, 1kg | Bio, Gewürzt, Ohne Knochen |
| Hähnchen (Ganzes Tier) | Fleisch & Fisch | 1, 2, 1kg, 1,2kg | Bio, TK, Frisch, Kikok |
| Putenbrust / Putenschnitzel | Fleisch & Fisch | 1, 2, 400g, 500g | Bio, Natur, SB, Theke |
| Entenbrust / Gans | Fleisch & Fisch | 1, 2, 400g, 1kg, Ganzer Vogel| TK, Frisch, Weihnachten (Saison) |
| Lammkeule / Lammfilet | Fleisch & Fisch | 1, 2, 300g, 1kg | Neuseeland, Bio, Theke |
| Bratwurst | Fleisch & Fisch | 1, 2, 3, 4, 4er Pack, 5er Pack, 400g | Schwein, Geflügel, Nürnberger, Thüringer, Grill |
| Salami (Aufschnitt) | Fleisch & Fisch | 1, 2, 100g, 150g, 200g | Bio, Geflügel, Paprika, Theke, SB, Luftgetrocknet |
| Kochschinken | Fleisch & Fisch | 1, 2, 100g, 150g, 200g | Bio, Hauchdünn, Theke, SB |
| Rohschinken / Parmaschinken | Fleisch & Fisch | 1, 2, 80g, 100g | Luftgetrocknet, Geräuchert, Serrano, Schwarzwälder |
| Leberwurst | Fleisch & Fisch | 1, 2, 125g, 150g, 250g | Kalb, Pfälzer, Bio, Grob, Fein, Im Naturdarm |
| Fleischwurst / Lyoner | Fleisch & Fisch | 1, 2, 1 Ring, 200g, 400g | Geflügel, Mit Knoblauch, Theke, Bio |
| Mortadella | Fleisch & Fisch | 1, 2, 100g, 150g | Geflügel, Pistazien, Bärchenwurst |
| Speck / Bacon | Fleisch & Fisch | 1, 2, 100g, 150g, Würfel | Geräuchert, Frühstücksspeck, SB |
| Wiener Würstchen | Fleisch & Fisch | 1, 2, 4er, 6er Pack, Glas | Geflügel, Bio, Knackwurst, Kalb |
| Bockwurst | Fleisch & Fisch | 1, 2, 4er Pack, Glas | Bio, Geflügel |
| Teewurst | Fleisch & Fisch | 1, 2, 125g | Grob, Fein, Rügenwalder (Marke) |
| Mettwurst / Zwiebelmettwurst | Fleisch & Fisch | 1, 2, 150g, 200g | Bio, Geflügel |
| Lachsfilet (Frisch / TK) | Fleisch & Fisch | 1, 2, 200g, 250g, 500g | Bio, ASC, MSC, Norwegen, Wildlachs |
| Räucherlachs | Fleisch & Fisch | 1, 2, 100g, 200g | Bio, MSC, Graved Lachs, Stremellachs |
| Forelle | Fleisch & Fisch | 1, 2, 3, 4 Stk | Frisch, Geräuchert, Bio |
| Kabeljau / Dorsch | Fleisch & Fisch | 1, 2, 250g, 400g | Frisch, TK, MSC |
| Seelachs | Fleisch & Fisch | 1, 2, 400g, 800g (TK) | MSC, Paniert, Natur |
| Fischstäbchen | Fleisch & Fisch | 1, 2, 10er, 15er Pack (450g) | TK, MSC, Omega-3, Lachs, Iglo (Marke) |
| Schlemmerfilet (Bordelaise) | Fleisch & Fisch | 1, 2, 400g | TK, MSC, Iglo, Frosta |
| Garnelen / Shrimps | Fleisch & Fisch | 1, 2, 100g, 250g, 500g | TK, Frisch, Bio, ASC, Mariniert, Geschält |
| Tintenfisch / Calamari | Fleisch & Fisch | 1, 2, 500g | TK, Ringe, Natur |
| Muscheln (Miesmuscheln) | Fleisch & Fisch | 1, 2, 1kg, 2kg | Frisch, Vakuum, Saison |

### 5.4 Kategorie 4: Milchprodukte & Tiefkühlkost
Beinhaltet Milch, Käse, Eier, pflanzliche Frische-Alternativen sowie generelle TK-Kost.

| Artikelbezeichnung (Type-Ahead Ziel) | Primäre Warengruppe | Typische Mengen-Tags (Numerisch / Gebinde) | Spezifische Konstellations-Tags (Ausprägungen) |
| :--- | :--- | :--- | :--- |
| Milch (Kuhmilch) | Milch & Tiefkühl | 1, 2, 3, 4, 6, 12, 1l | 0,1%, 0,7%, 1,5%, 3,5%, 3,8%, Bio, haltbar (H-Milch), Frisch, Laktosefrei |
| Pflanzliche Milch (Drink) | Milch & Tiefkühl | 1, 2, 3, 4, 6, 12, 1l | Soja, Hafer, Reis, Mandel, Kokos, Bio, Barista, Ungesüßt, Alpro/Oatly |
| Joghurt (Natur) | Milch & Tiefkühl | 1, 2, 3, 4, 150g, 500g Becher | 0,1%, 1,5%, 3,5%, 10% (Griechisch), Bio, Laktosefrei, Vegan (Soja/Hafer) |
| Fruchtjoghurt | Milch & Tiefkühl | 1, 2, 3, 4, 150g, 250g | Erdbeer, Kirsch, Pfirsich, Stracciatella, Bio, Vegan |
| Quark / Speisequark | Milch & Tiefkühl | 1, 2, 3, 250g, 500g | Magerstufe (0,2%), 20%, 40% Fett, Bio, Laktosefrei |
| Kräuterquark | Milch & Tiefkühl | 1, 2, 150g, 200g | Milram (Marke), Bio |
| Sahne / Schlagsahne | Milch & Tiefkühl | 1, 2, 3, 4, 200g, 250g Becher | Min. 30% Fett, Bio, Laktosefrei, haltbar (H-Sahne), Vegan |
| Saure Sahne | Milch & Tiefkühl | 1, 2, 3, 200g Becher | 10% Fett, Bio |
| Schmand | Milch & Tiefkühl | 1, 2, 3, 200g Becher | 24% Fett, Bio |
| Crème Fraîche | Milch & Tiefkühl | 1, 2, 150g Becher | Natur (30%), Kräuter, Bio |
| Mascarpone | Milch & Tiefkühl | 1, 2, 250g, 500g | Bio, Italienisch |
| Buttermilch | Milch & Tiefkühl | 1, 2, 3, 500g Becher, 1l | Natur, Frucht (Erdbeer, Zitrone), Bio |
| Kefir | Milch & Tiefkühl | 1, 2, 3, 500g Becher | Natur, Bio |
| Pudding (Kühlregal) | Milch & Tiefkühl | 1, 2, 3, 4, 150g, 200g, 500g | Schoko, Vanille, High Protein, Grießpudding |
| Gouda | Milch & Tiefkühl | 1, 2, 150g, 200g, 400g | Jung, Mittelalt, Alt, Scheiben, Am Stück, Gerieben, Bio |
| Emmentaler | Milch & Tiefkühl | 1, 2, 150g, 200g, 400g | Scheiben, Am Stück, Gerieben, Bio |
| Edamer / Butterkäse | Milch & Tiefkühl | 1, 2, 150g, 200g, 400g | Scheiben, Am Stück, Bio |
| Mozzarella | Milch & Tiefkühl | 1, 2, 3, 4, 125g (Kugel), 200g | Kuhmilch, Büffelmozzarella, Bio, Gerieben (Pizzakäse) |
| Feta / Schafskäse | Milch & Tiefkühl | 1, 2, 3, 200g, 250g | Schafmilch, Bio, Griechisch |
| Hirtenkäse | Milch & Tiefkühl | 1, 2, 3, 200g, 250g | Kuhmilch (Feta-Art), Leicht |
| Camembert / Brie | Milch & Tiefkühl | 1, 2, 125g, 200g, 250g | Rahmstufe, Französisch, Bio, Rustique |
| Parmesan | Milch & Tiefkühl | 1, 2, 150g, 200g | Am Stück, Gerieben, 24 Monate gereift |
| Frischkäse | Milch & Tiefkühl | 1, 2, 3, 150g, 200g, 300g | Natur, Kräuter, Laktosefrei, Bio, Philadelphia, Vegan |
| Harzer Käse / Handkäse | Milch & Tiefkühl | 1, 2, 200g Rolle | Proteinreich, Fettarm, Kümmel |
| Hüttenkäse | Milch & Tiefkühl | 1, 2, 3, 200g Becher | Proteinreich, Fettarm, Bio |
| Eier (Hühnereier) | Milch & Tiefkühl | 1, 2, 3, 4, 6er Pack, 10er Pack | Bio (0), Freiland (1), Bodenhaltung (2), Größe M, L |
| Butter | Milch & Tiefkühl | 1, 2, 3, 4, 250g, 500g | Süßrahm, Sauerrahm, Mildgesäuert, Bio, Streichzart |
| Margarine | Milch & Tiefkühl | 1, 2, 3, 250g, 500g, 750g | Vegan, Lätta/Rama (Marke), Omega-3 |
| Tofu (Natur / Geräuchert) | Milch & Tiefkühl | 1, 2, 3, 200g, 400g | Vegan, Bio, Taifun (Marke), Seidentofu |
| Veganes Hack | Milch & Tiefkühl | 1, 2, 3, 250g, 275g, 400g | Vegan, Bio, Erbsenprotein, Sojaprotein |
| Vegane Wurst/Schnitzel | Milch & Tiefkühl | 1, 2, 3, 150g, 2 Stk | Vegan, Rügenwalder (Marke) |
| Blätterteig | Milch & Tiefkühl | 1, 2, 1 Rolle, 275g | Frischteig, Vegan, Butter |
| Pizzateig / Flammkuchenteig | Milch & Tiefkühl | 1, 2, 1 Rolle, 400g | Frischteig, XXL, Mit Tomatensauce (Set) |
| Tiefkühl-Pizza | Milch & Tiefkühl | 1, 2, 3, 4, 2er Pack, 3er | Salami, Margherita, Speciale, Wagner, Dr. Oetker, Vegan |
| Pommes Frites (TK) | Milch & Tiefkühl | 1, 2, 750g, 1kg | Feinschnitt, Wellenschnitt, Backofen-Pommes |
| Tiefkühl-Gemüse (Erbsen/Spinat)| Milch & Tiefkühl | 1, 2, 3, 400g, 750g, 1kg | Bio, Iglo, Rahmspinat, Junge Erbsen |
| Tiefkühl-Kräuter | Milch & Tiefkühl | 1, 2, 3, 50g, 75g | 8-Kräuter, Petersilie, Schnittlauch, Bio |
| Tiefkühl-Beeren | Milch & Tiefkühl | 1, 2, 3, 300g, 500g | Bio, Waldbeeren, Ungesüßt |
| Speiseeis / Eiscreme | Milch & Tiefkühl | 1, 2, 3, 500ml, 1l, 3er Pack| Vanille, Schoko, Magnum, Ben & Jerry's, Vegan |
| Eiswürfel | Milch & Tiefkühl | 1, 2, 3, 1kg, 2kg Sack | Crushed Ice, Würfel |

### 5.5 Kategorie 5: Vorratskammer (Trockensortiment, Konserven & Snacks)
Diese Kategorie bündelt alle haltbaren Lebensmittel (Nährmittel, Gewürze, Saucen, Süßwaren, Knabberartikel).

| Artikelbezeichnung (Type-Ahead Ziel) | Primäre Warengruppe | Typische Mengen-Tags (Numerisch / Gebinde) | Spezifische Konstellations-Tags (Ausprägungen) |
| :--- | :--- | :--- | :--- |
| Nudeln / Pasta (Hartweizen) | Vorratskammer | 1, 2, 3, 4, 500g, 1kg | Spaghetti, Fusilli, Penne, Farfalle, Barilla (Marke) |
| Nudeln (Vollkorn / Dinkel) | Vorratskammer | 1, 2, 3, 500g | Bio, Spaghetti, Penne |
| Reis | Vorratskammer | 1, 2, 3, 500g, 1kg, 2kg | Basmati, Jasmin, Parboiled, Vollkorn, Kochbeutel, Bio |
| Milchreis / Risottoreis | Vorratskammer | 1, 2, 500g, 1kg | Arborio, Bio |
| Mehl (Weizen) | Vorratskammer | 1, 2, 3, 4, 1kg, 2,5kg | Typ 405, Typ 550, Typ 1050, Bio |
| Mehl (Dinkel / Roggen) | Vorratskammer | 1, 2, 3, 1kg | Dinkel Typ 630, Roggen Typ 1150, Vollkornmehl, Bio |
| Zucker | Vorratskammer | 1, 2, 3, 4, 500g, 1kg | Raffinade, Rohrrohzucker (Bio), Puderzucker, Würfelzucker |
| Haferflocken | Vorratskammer | 1, 2, 3, 4, 500g, 1kg | Zart, Kernig, Bio, Glutenfrei, Kölln (Marke) |
| Linsen | Vorratskammer | 1, 2, 3, 500g (Getrocknet), 400g (Dose)| Rote Linsen, Tellerlinsen, Belugalinsen, Bio |
| Kichererbsen | Vorratskammer | 1, 2, 3, 500g (Getr.), 400g (Dose)| Bio, Vorgekocht |
| Bohnen (Getrocknet/Dose) | Vorratskammer | 1, 2, 3, 400g (Dose) | Kidneybohnen, Weiße Bohnen, Schwarze Bohnen, Bio |
| Quinoa / Amaranth | Vorratskammer | 1, 2, 500g | Bio, Weiß, Tricolor |
| Couscous / Bulgur | Vorratskammer | 1, 2, 500g | Bio |
| Sojagranulat / Sojaschnetzel | Vorratskammer | 1, 2, 250g, 500g | Bio, Getrocknet |
| Kartoffelpüree-Pulver | Vorratskammer | 1, 2, 3x3 Portionen | Bio, Pfanni (Marke) |
| Paniermehl / Semmelbrösel | Vorratskammer | 1, 2, 400g, 500g | Bio |
| Grieß / Polenta | Vorratskammer | 1, 2, 500g | Weichweizengrieß, Hartweizengrieß, Maisgrieß, Bio |
| Salz | Vorratskammer | 1, 2, 500g, 1kg | Jodsalz, Meersalz, Fluorid, Grob (Mühle), Bad Reichenhaller |
| Pfeffer | Vorratskammer | 1, 2, 50g, 100g (Mühle) | Schwarz, Weiß, Bunt, Ganze Körner, Gemahlen |
| Paprikapulver | Vorratskammer | 1, 2, 40g, 50g, 100g | Edelsüß, Rosenscharf, Geräuchert (Smoked) |
| Currypulver | Vorratskammer | 1, 2, 40g, 50g | Mild, Scharf, Bio, Englisch |
| Oregano / Basilikum (Getr.) | Vorratskammer | 1, 2, 15g, 20g (Glas) | Gerebelt, Bio |
| Brühe (Gemüse, Huhn, Rind) | Vorratskammer | 1, 2, Glas, Würfel | Bio, Hefeextraktfrei, Maggi/Knorr (Marke), Pulver |
| Olivenöl | Vorratskammer | 1, 2, 500ml, 750ml | Nativ Extra, Bio, Italienisch, Spanisch, Griechisch |
| Sonnenblumenöl / Rapsöl | Vorratskammer | 1, 2, 750ml, 1l | Raffiniert (zum Braten), Kaltgepresst |
| Essig (Balsamico) | Vorratskammer | 1, 2, 500ml | Aceto Balsamico di Modena, Bianco, Bio, Crema |
| Ketchup | Vorratskammer | 1, 2, 3, 500ml, 800ml | Tomatenketchup, Curryketchup, Bio, Heinz (Marke) |
| Mayonnaise / Remoulade | Vorratskammer | 1, 2, 250ml, 500ml | 80% Fett, Salatmayonnaise (50%), Vegan, Thomy (Marke) |
| Senf | Vorratskammer | 1, 2, 3, 200ml (Tube/Glas)| Mittelscharf, Scharf, Süß, Dijon, Bautz'ner |
| Sojasauce | Vorratskammer | 1, 2, 150ml, 250ml | Bio, Weniger Salz, Kikkoman (Marke) |
| Tomatenmark | Vorratskammer | 1, 2, 3, 200g (Tube) | 3-fach konzentriert, 2-fach, Bio, Oro di Parma |
| Passierte Tomaten (Passata) | Vorratskammer | 1, 2, 3, 4, 500g (Tetrapak)| Bio, Mit Kräutern |
| Stückige Tomaten | Vorratskammer | 1, 2, 3, 4, 400g (Dose) | Bio, Mutti (Marke) |
| Pesto | Vorratskammer | 1, 2, 3, 190g (Glas) | Verde (Basilikum), Rosso (Tomate), Barilla (Marke), Bio |
| Backpulver / Hefe | Vorratskammer | 1, 2, 3, 3er Pack, 4er | Trockenhefe, Frische Hefe, Bio |
| Mais (Dose) | Vorratskammer | 1, 2, 3, 4, 300g, 3x 150g | Bio, Supersweet |
| Gewürzgurken / Essiggurken | Vorratskammer | 1, 2, 3, 720ml (Glas) | Cornichons, Mild, Scharf, Kühne (Marke) |
| Thunfisch (Konserve) | Vorratskammer | 1, 2, 3, 150g | In Sonnenblumenöl, Im eigenen Saft, MSC |
| Müsli | Vorratskammer | 1, 2, 3, 500g, 750g | Schoko, Früchte, Knusper/Crunchy, Ohne Zuckerzusatz, Bio |
| Cornflakes / Cerealien | Vorratskammer | 1, 2, 3, 500g | Kellogg's, Smacks, Choco Krispies, Bio |
| Marmelade / Konfitüre | Vorratskammer | 1, 2, 3, 340g, 450g (Glas)| Erdbeer, Himbeer, Aprikose, Bio, Weniger Zucker |
| Honig | Vorratskammer | 1, 2, 3, 500g (Glas/Spender)| Blütenhonig, Waldhonig, Bio, Fairtrade |
| Nuss-Nougat-Creme (Nutella) | Vorratskammer | 1, 2, 3, 450g, 750g, 1kg | Nutella, Bio, Vegan, Ohne Palmöl, Nudossi |
| Schokolade (Tafel) | Vorratskammer | 1, 2, 3, 4, 100g, 300g | Vollmilch, Zartbitter, Weiß, Vegan, Milka, Ritter Sport |
| Gummibärchen / Fruchtgummi | Vorratskammer | 1, 2, 3, 175g, 200g, 300g | Haribo, Katjes, Vegan, Sauer, Lakritz |
| Kekse / Plätzchen | Vorratskammer | 1, 2, 3, 150g, 200g, 300g | Butterkeks, Schokokeks, Prinzenrolle, Leibniz, Oreo |
| Chips / Kartoffelchips | Vorratskammer | 1, 2, 3, 4, 150g, 175g | Paprika, Salt & Vinegar, Funny Frisch, Pringles, Chio |
| Erdnüsse | Vorratskammer | 1, 2, 3, 150g, 200g (Dose) | Geröstet, Gesalzen, Ungesalzen, Bio, Ültje |
| Cashewkerne / Pistazien | Vorratskammer | 1, 2, 3, 150g, 200g | Geröstet, Gesalzen, Natur, Bio |

### 5.6 Kategorie 6: Getränke & Genussmittel

| Artikelbezeichnung (Type-Ahead Ziel) | Primäre Warengruppe | Typische Mengen-Tags (Numerisch / Gebinde) | Spezifische Konstellations-Tags (Ausprägungen) |
| :--- | :--- | :--- | :--- |
| Mineralwasser | Getränke | 1, 2, 6er Träger, 12er Kasten, 1l, 1,5l | Sprudel (Classic), Medium, Still (Naturelle), PET, Glas, Bio |
| Apfelsaft | Getränke | 1, 2, 3, 1l, 6er Kasten | Naturtrüb, Klar, Direktsaft, Konzentrat, Bio, Schorle |
| Orangensaft | Getränke | 1, 2, 3, 1l, 6er Kasten | Direktsaft, Mit Fruchtfleisch, Bio, Hohes C, Valensina |
| Cola | Getränke | 1, 2, 6er Träger, 1l, 1,5l, 0,33l Dose | Coca-Cola (Marke), Pepsi, Zero, Light, Zuckerfrei |
| Limonade (Fanta / Sprite) | Getränke | 1, 2, 6er Träger, 1l, 1,5l | Orange, Zitrone, Zero |
| Eistee | Getränke | 1, 2, 3, 1l, 1,5l (Tetrapak) | Pfirsich, Zitrone, Lipton, Pfanner, Volvic |
| Kaffee | Getränke | 1, 2, 3, 500g, 1kg | Ganze Bohnen, Gemahlen, Bio, Fairtrade, Entkoffeiniert |
| Kaffeepads / Kapseln | Getränke | 1, 2, 16er, 36er Pack | Senseo, Nespresso-kompatibel, Bio |
| Tee (Beutel / Lose) | Getränke | 1, 2, 3, 20er Packung, 100g | Kamille, Pfefferminz, Schwarztee, Grüntee, Bio |
| Kakao / Kaba (Pulver) | Getränke | 1, 2, 400g, 500g, 800g | Bio, Fairtrade, Nesquik, Kaba |
| Bier | Getränke | 1, 2, 6er Träger, 20er Kasten, 24er, 0,5l, 0,33l | Pils, Helles, Weizen, Alkoholfrei, Radler, Export |
| Wein (Weißwein) | Getränke | 1, 2, 3, 6, 0,75l | Trocken, Halbtrocken, Lieblich, Riesling, Grauburgunder, Bio |
| Wein (Rotwein) | Getränke | 1, 2, 3, 6, 0,75l | Trocken, Halbtrocken, Merlot, Dornfelder, Bio |
| Sekt / Schaumwein | Getränke | 1, 2, 3, 6, 0,75l | Brut, Trocken, Halbtrocken, Rotkäppchen, Freixenet, Alkoholfrei |
| Wodka / Rum / Gin | Getränke | 1, 2, 0,7l | Absolut, Havana Club, Bombay, Gordon's |

### 5.7 Kategorie 7: Drogerie, Haushalt & Tierbedarf

| Artikelbezeichnung (Type-Ahead Ziel) | Primäre Warengruppe | Typische Mengen-Tags (Numerisch / Gebinde) | Spezifische Konstellations-Tags (Ausprägungen) |
| :--- | :--- | :--- | :--- |
| Windeln | Drogerie & Haushalt | 1, 2, Mega-Pack, Jumbo-Pack | Größe 1, 2, 3, 4, 5, 6, Pampers, Babylove, Pants |
| Feuchttücher (Baby) | Drogerie & Haushalt | 1, 2, 3, 4, 4er Pack, 80er | Sensitiv, Wasserstoff, Bio |
| Babynahrung (Gläschen / Pulver) | Drogerie & Haushalt | 1, 2, 3, 4, 190g, 600g | Bio, Pre, Folgemilch 1, Ab 4. Monat, Hipp |
| Duschgel | Drogerie & Haushalt | 1, 2, 3, 250ml, 300ml | pH-hautneutral, Männer, Naturkosmetik, Bio, Nivea, Balea |
| Shampoo | Drogerie & Haushalt | 1, 2, 3, 250ml, 300ml | Für trockenes Haar, Anti-Schuppen, Naturkosmetik |
| Seife (Flüssig / Stück) | Drogerie & Haushalt | 1, 2, 3, 300ml (Spender), 500ml (Nachfüll), 100g | Arztseife, Sensitiv, Bio |
| Deodorant (Deo) | Drogerie & Haushalt | 1, 2, 3, 150ml (Spray), 50ml (Roll-on)| Ohne Aluminium, Naturkosmetik, Nivea, Rexona |
| Rasierklingen / Einwegrasierer | Drogerie & Haushalt | 1, 2, 4er, 8er Pack | Männer, Frauen, Gillette, Venus |
| Zahnpasta | Drogerie & Haushalt | 1, 2, 3, 4, 75ml, 100ml | Mit Fluorid, Ohne Fluorid, Sensitiv, Weißmachend, Elmex |
| Zahnbürste / Aufsteckbürsten | Drogerie & Haushalt | 1, 2, 3, 4, 2er Pack, 4er Pack | Weich, Mittel, Hart, Elektrisch, Oral-B |
| Toilettenpapier | Drogerie & Haushalt | 1, 2, 3, 8 Rollen, 10 Rollen, 16 Rollen | 3-lagig, 4-lagig, 5-lagig, Recycling, Zewa |
| Küchenrolle / Haushaltspapier | Drogerie & Haushalt | 1, 2, 3, 4 Rollen, 8 Rollen | 3-lagig, Recycling, Zewa, Küchentücher |
| Taschentücher | Drogerie & Haushalt | 1, 2, 3, 10x10er, 30x10er, Box (100er) | 4-lagig, Recycling, Balsam, Tempo |
| Tampons / Binden | Drogerie & Haushalt | 1, 2, 3, 16er, 32er, 56er Pack | Normal, Super, Nacht, Bio-Baumwolle, O.b., Always |
| Waschmittel (Flüssig / Pulver) | Drogerie & Haushalt | 1, 2, 20 Wl, 40 Wl, 80 Wl, 100 Wl | Color, Vollwaschmittel, Sensitiv, Pods/Caps, Ariel, Persil |
| Weichspüler | Drogerie & Haushalt | 1, 2, 3, 1l, 1,5l | Sensitiv, Lenor, Vernel |
| Spülmittel (Hand) | Drogerie & Haushalt | 1, 2, 3, 500ml, 900ml | Konzentrat, Balsam, Öko, Pril, Fairy |
| Spülmaschinentabs | Drogerie & Haushalt | 1, 2, 40er, 60er, 100er Pack | All-in-One, Classic, Öko, Somat, Finish |
| Allzweckreiniger / Glasreiniger | Drogerie & Haushalt | 1, 2, 1l, 500ml, 750ml (Spray) | Öko, Citrus, Streifenfrei |
| Müllbeutel | Drogerie & Haushalt | 1, 2, 3, 4, 10l, 20l, 35l, 60l, 120l| Mit Zugband, Kompostierbar (Bio), 20er Rolle, Reißfest |
| Alufolie / Frischhaltefolie | Drogerie & Haushalt | 1, 2, 3, 20m, 30m, 50m | Recycling-Alu, Extra stark, PVC-frei |
| Backpapier | Drogerie & Haushalt | 1, 2, 3, 30 Zuschnitte, 1 Rolle| Ungebleicht, Kompostierbar, Dauerbackfolie |
| Schwamm / Spültuch | Drogerie & Haushalt | 1, 2, 3, 3er, 6er Pack | Öko, Kratzfrei, Topfreiniger, Microfaser |
| Batterien (AA / AAA) | Drogerie & Haushalt | 1, 2, 3, 4er, 8er Pack | Alkaline, Akkus (Wiederaufladbar), Varta, Duracell |
| Katzenfutter (Nass / Trocken) | Drogerie & Haushalt | 1, 2, 3, 4, 6, 12, 100g, 400g, 1kg | Gelee, Sauce, Bio, Getreidefrei, Adult, Senior, Kitten |
| Katzenstreu | Drogerie & Haushalt | 1, 2, 3, 10l, 20l | Klumpstreu, Silikat, Naturfaser (z.B. Cats Best), Staubarm |
| Hundefutter (Nass / Trocken) | Drogerie & Haushalt | 1, 2, 3, 4, 6, 400g, 800g, 5kg | Rind, Geflügel, Getreidefrei, Adult, Puppy, Senior |
| Leckerlis (Hund / Katze) | Drogerie & Haushalt | 1, 2, 3, 50g, 100g, 200g | Zahnpflege (Dentastix), Kausnack, Sticks |
| Pflaster / Verbandszeug | Drogerie & Haushalt | 1, 2, 1 Packung | Wasserfest, Sensitiv, Kinderpflaster |
| Vitamine / Nahrungsergänzung | Drogerie & Haushalt | 1, 2, 30 Stk, 60 Stk, Brausetabletten | Vitamin C, Magnesium, Zink, Multivitamin |

### 5.8 Kategorie 8: Sonstiges
Diese Kategorie fängt unklare Artikel und Zusatzverkäufe auf, die sich in keine der obigen Strukturen eingliedern lassen.

| Artikelbezeichnung (Type-Ahead Ziel) | Primäre Warengruppe | Typische Mengen-Tags (Numerisch / Gebinde) | Spezifische Konstellations-Tags (Ausprägungen) |
| :--- | :--- | :--- | :--- |
| Zeitschriften / Magazine | Sonstiges | 1, 2, 3 | Fernsehzeitung, Klatsch, Rätselheft |
| Tageszeitung | Sonstiges | 1, 2 | Lokal, Überregional |
| Briefmarken | Sonstiges | 1, 2, 3, 10er Set | Standardbrief, Postkarte |
| Gutscheinkarten / Giftcards | Sonstiges | 1, 2, 3, 15€, 25€, 50€ | Amazon, iTunes, Google Play, PlayStation, Wunschgutschein |
| Tabakwaren / Zigaretten | Sonstiges | 1, 2, 3, 4, 1 Schachtel | Filter, Stopftabak |
| Blumenstrauß / Topfpflanze | Sonstiges | 1, 2, 3 | Fairtrade, Regional, Orchidee, Rosen |
| Müllmarken / Wertstoffsäcke | Sonstiges | 1, 2, 3, 1 Rolle | Gelber Sack, Restmüll |
| Saisonartikel (Weihnachten/Ostern)| Sonstiges | 1, 2, 3, 4 | Deko, Baumschmuck, Ostereierfarben |
| Brennholz / Grillkohle | Sonstiges | 1, 2, 3, 2,5kg, 5kg | Briketts, Holzkohle, FSC-Zertifiziert |
| Streusalz | Sonstiges | 1, 2, 5kg, 10kg | |
