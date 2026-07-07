# Blog Context Notes

Kurze, manuell oder automatisch gepflegte Zusatznotizen fuer den Blog-Agenten.
Nur wirklich neue Erkenntnisse eintragen, maximal wenige Bulletpoints pro Lauf.

- 2026-07-07: Traffic-Wachstum war seit Mitte Juni geplateaut (GA4-Sessions/Woche
  stagnierten bei ~500-600), obwohl GSC-Impressions weiter stiegen. Ursache war
  CTR (~0.8% statt erwarteten ~2%) durch generische Titel/Metas, plus echte
  Keyword-Kannibalisierung (karikatur-analysieren-tipps vs.
  karikaturanalyse-schreiben-tipps, Position schwankte 3<->12). Beide Probleme
  wurden gefixt: Redirect/Merge des schwaecheren Artikels, Title/Meta-Rewrite
  der Top-5-CTR-Seiten. Seitdem gilt: Konsolidieren hat Vorrang vor neuem
  Content (siehe auto-blog.sh Schritt 2).
