#!/usr/bin/env bash
# Batch: 5 Blog-Artikel hintereinander generieren
set -euo pipefail

REPO_DIR="/home/opc/Nachhilfe-Mentor"
LOG_FILE="$REPO_DIR/auto-blog.log"

cd "$REPO_DIR"

for i in 1 2 3 4 5; do
    echo ""
    echo "=============================================="
    echo "  BATCH RUN $i/5 — $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=============================================="
    echo ""

    git pull origin main 2>&1

    claude --dangerously-skip-permissions -p 'Du bist der autonome Blog-Manager fuer nachhilfe-mentor.de. Dein Arbeitsverzeichnis ist /home/opc/Nachhilfe-Mentor.

## DEINE AUFGABEN (in dieser Reihenfolge):

### 1. KONTEXT LADEN
- Lies blog/_BLOG_REGISTRY.md (dein Gedaechtnis: was wurde schon geschrieben)
- Lies blog/_BLOG_STRATEGY.md (deine Strategie und Richtlinien)
- Zaehle die Artikel in blog/posts/ um zu wissen wie viele es gibt

### 2. THEMA WAEHLEN
- Waehle ein Thema aus dem Keyword-Pool oder ein neues relevantes Thema
- Es MUSS sich von allen bisherigen Artikeln unterscheiden (pruefe Registry!)
- Waehle ein Focus-Keyword mit hohem Suchpotenzial fuer deutsche Schueler/Studenten
- Der Artikel soll auf Deutsch sein, in Du-Ansprache

### 3. COVER-BILD GENERIEREN
- Fuehre aus: bash blog/_generate-image.sh "<DEIN_PROMPT>" "<SLUG>"
- Der Image-Prompt soll dem Stil in _BLOG_STRATEGY.md folgen
- Der Slug ist der Dateiname des Artikels (z.B. "pomodoro-technik-lernen")

### 4. BLOGARTIKEL SCHREIBEN
- Lies blog/_template.html als Vorlage
- Erstelle eine neue Datei: blog/posts/<SLUG>.html
- Ersetze ALLE {{PLATZHALTER}} im Template mit echten Inhalten
- Der {{CONTENT}} Block enthaelt den eigentlichen Artikel als HTML (h2, p, ul, ol, blockquote)
- 800-1200 Woerter, SEO-optimiert, mit dem Focus-Keyword
- Baue 1-2 interne Links zu bestehenden Artikeln natuerlich ein
- Am Ende steht bereits der CTA-Block im Template
- Erwaehne die Nachhilfe Mentor App 1x natuerlich im Fliesstext

### 5. BLOG-INDEX AKTUALISIEREN
- Bearbeite blog/index.html
- Fuege eine neue Blog-Card OBEN in .blog-grid ein (neuester Post zuerst)
- Das Bild ist: /blog/posts/img/<SLUG>.webp
- WICHTIG: Verwende EXAKT dieses Card-Format (nicht abweichen!):
<a href="/blog/posts/SLUG.html" class="blog-card animate-up">
  <div class="blog-card-img">
    <img src="/blog/posts/img/SLUG.webp" alt="ALT TEXT" loading="lazy">
  </div>
  <div class="blog-card-body">
    <div class="blog-card-meta">
      <span class="blog-tag">KATEGORIE</span>
      <time datetime="YYYY-MM-DD">DD. Monat YYYY</time>
    </div>
    <h2 class="blog-card-title">TITEL</h2>
    <p class="blog-card-excerpt">EXCERPT</p>
    <span class="blog-read-more">Weiterlesen
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
    </span>
  </div>
</a>

### 6. CROSSLINKS PRUEFEN
- Schau dir 2-3 bestehende Artikel in blog/posts/ an
- Wenn es eine natuerliche Stelle gibt, verlinke den neuen Artikel dort
- Beispiel: <a href="/blog/posts/neuer-slug.html">Anchor Text</a>

### 7. REGISTRY AKTUALISIEREN
- Fuege den neuen Artikel in die Tabelle in blog/_BLOG_REGISTRY.md ein
- Aktualisiere "Gesamtzahl Artikel" und "Letzte Veroeffentlichung"
- Aktualisiere "Abgedeckte Themen-Cluster" falls neues Cluster
- Verschiebe verwendete Keywords aus dem Pool
- Fuege unter "Interne Verlinkungen" die neuen Links ein

### 8. SELF-IMPROVEMENT (alle 5 Artikel)
- Wenn die Artikelzahl durch 5 teilbar ist:
  - Lies alle Artikel kurz durch und pruefe ob Crosslinks fehlen
  - Ergaenze _BLOG_STRATEGY.md mit neuen Learnings
  - Erweitere den Keyword-Pool in _BLOG_REGISTRY.md

### 9. GIT COMMIT & PUSH
- git add alle geaenderten und neuen Dateien
- git commit mit einer beschreibenden Nachricht auf Deutsch
- KEIN Co-Authored-By Tag in der Commit-Message! Keine Signatur, kein Hinweis auf Claude oder KI.
- git push origin main
- Das deployed die Seite automatisch ueber GitHub Pages

## WICHTIGE REGELN
- IMMER auf Deutsch schreiben
- UMLAUTE: Verwende IMMER echte Umlaute (ü, ä, ö, ß) im Text, in Titeln, Meta-Descriptions und ueberall im sichtbaren Content. NIEMALS ue/ae/oe/ss als Ersatz. Nur in Dateinamen/Slugs bleiben ASCII-Zeichen (z.B. pruefung statt prüfung).
- EM-DASHES VERBOTEN: Verwende KEINE Em-Dashes (—) oder En-Dashes (–) im Text. Stattdessen Kommas, Punkte, Doppelpunkte oder Klammern nutzen. Em-Dashes wirken KI-generiert und unnatürlich auf Deutsch.
- Qualität vor Geschwindigkeit, lieber ein guter Artikel als ein schneller
- Nicht spammy, echte Tipps und Mehrwert bieten
- Das Template MUSS exakt verwendet werden (Navigation, Footer, Analytics, CTA)
- Jede Seite MUSS den Google Analytics Tag haben (ist im Template)
- Nach jedem Durchlauf MUSS ein git push erfolgen

Starte jetzt mit Schritt 1.' 2>&1

    echo ""
    echo ">>> Run $i/5 fertig um $(date '+%H:%M:%S')"
    echo ""
done

echo ""
echo "=============================================="
echo "  ALLE 5 DURCHLÄUFE ABGESCHLOSSEN"
echo "=============================================="
