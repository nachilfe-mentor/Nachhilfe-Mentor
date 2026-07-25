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
- 2026-07-24: GSC-Kannibalisierungsliste zeigt weiterhin karikatur-analysieren-tipps
  vs. karikaturanalyse-schreiben-tipps, das ist aber der bereits am 2026-07-07
  gesetzte Redirect (Datenbasis liegt teils davor) - keine erneute Aktion noetig.
  Uebrige Paare (formeller/persoenlicher Brief, Erlebnisbericht/-erzaehlung,
  Eroerterungs-Varianten, Formanalyse-Unterarten) sind inhaltlich echt
  unterschiedliche Textformen, keine Duplikate. CTR-Update stattdessen fuer
  elfchen-schreiben-tipps.html (impr 4368, ctr 0.62%, seit 17 Tagen nicht
  angefasst): Title/Meta auf konkrete Vorlage-zum-Ausfuellen-Hook umgestellt.
- 2026-07-25: Erneut kein neues Kannibalisierungspaar (alle Paare im Report
  sind Haupt- vs. Uebungsseite oder inhaltlich verschiedene Textformen, siehe
  Note vom 2026-07-24). CTR-Update fuer zeitungsartikel-schreiben-tipps.html
  (impr 3003, ctr 0.60%, pos 7.8, Title/Meta seit Erstellung nie ueberarbeitet):
  Title/Meta auf konkreten "6 W-Fragen + Pyramidenprinzip"-Hook umgestellt statt
  generischem "Aufbau, Tipps und haeufige Fehler".
