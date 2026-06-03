# Strategy Snapshot

Current priority:

- keep the existing Blog Agent stable;
- measure active content inventory;
- use PostHog and GA4/GSC signals when configured;
- prioritize conversion-relevant education clusters;
- create useful non-blog tools only after quality checks pass;
- prefer queueing evidence-backed Blog Agent tasks over direct blog edits.

Primary clusters:

- schreibaufgaben
- lernmethoden
- pruefungsvorbereitung
- mathematik
- motivation
- ki-und-bildung

## Published Lernmaterialien (live, indexiert)

Stand: 2026-06-03. Alle unter /lernmaterialien/ veröffentlicht, noindex entfernt,
Sitemap aktualisiert, IndexNow-Ping gesendet.

### Physik- und Chemie-Simulationen (Priorität 1)
- `/lernmaterialien/rutherford-streuversuch-simulation.html`
  Keyword: „Rutherford Streuversuch Simulation"
  Klasse 10–13 · Physik · Kernmodell, Coulomb-Ablenkung, Histogramm, 2 Vorhersage-Aufgaben
- `/lernmaterialien/galvanische-zelle-simulator.html`
  Keyword: „galvanische Zelle Simulator"
  Klasse 10–13 · Chemie · Anode/Kathode-Wahl, E°-Berechnung, Elektronen-/Ionenfluss-Animation
- `/lernmaterialien/teilchenbewegung-temperatur-simulation.html`
  Keyword: „Teilchenbewegung Temperatur Simulation"
  Klasse 10–13 · Physik · Maxwell-Boltzmann-Verteilung, kinetische Gastheorie, Boyle/Gay-Lussac/Avogadro

### Mathe-Trainer (Priorität 2)
- `/lernmaterialien/lineare-gleichungen-trainer.html`
  Keyword: „lineare Gleichungen Trainer"
  Klasse 7–10 · Mathematik · 3 Stufen (ax+b=c bis ax+b=cx+d), prozedural generierte Aufgaben, vollständiger Lösungsweg
- `/lernmaterialien/bruchrechnung-trainer.html`
  Keyword: „Bruchrechnung Trainer"
  Klasse 5–8 · Mathematik · 4 Rechenarten (gleichnamig, ungleichnamig, Multiplikation, Division), Fehlkonzept-Hinweise

### Übersichtsseite
- `/lernmaterialien/` (index.html)
  CollectionPage-Schema, alle 5 Tools verlinkt, interne Verlinkung zu Blog-Artikeln

### Empfehlung für neue Lernmaterialien
Vor dem Bauen: Spec nach /lernmaterialien/entwuerfe/ (gitignored).
Prototypen nach /lernmaterialien/lernsimulationen/ (gitignored, noindex).
Promotion erst nach Qualitätsgate → dann zu /lernmaterialien/<slug>.html.
