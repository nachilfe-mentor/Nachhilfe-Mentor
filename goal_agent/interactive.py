from __future__ import annotations

import html
import json
import re
from pathlib import Path

from .config import REPO_ROOT, Settings
from .quality import QualityResult, check_interactive_page_quality


GENERATED_DIR = REPO_ROOT / "lernmaterialien"

TOPIC_LABELS = {
    "pruefungsvorbereitung": "Prüfungsvorbereitung",
    "ki-und-bildung": "KI und Bildung",
    "lernmethoden": "Lernmethoden",
    "mathematik": "Mathematik",
    "sprachen": "Sprachen",
}

TOPIC_INTERNAL_LINKS = {
    "pruefungsvorbereitung": [
        ("/blog/posts/abitur-vorbereitung-tipps.html", "Abitur-Vorbereitung planen"),
        ("/blog/posts/klausur-letzte-nacht-lernen.html", "kurz vor der Klausur lernen"),
        ("/blog/posts/pruefungsangst-tipps.html", "Prüfungsangst reduzieren"),
    ],
    "lernmethoden": [
        ("/blog/posts/active-recall-lerntechnik.html", "Active Recall nutzen"),
        ("/blog/posts/lernplan-erstellen.html", "einen Lernplan erstellen"),
    ],
    "mathematik": [
        ("/blog/posts/binomische-formeln-lernen.html", "Binomische Formeln üben"),
        ("/blog/posts/kurvendiskussion-tipps.html", "Kurvendiskussion vorbereiten"),
    ],
    "sprachen": [
        ("/blog/posts/vokabeln-lernen-tipps.html", "Vokabeln lernen"),
        ("/blog/posts/englisch-grammatik-lernen.html", "Englisch-Grammatik wiederholen"),
    ],
}


def slugify(value: str) -> str:
    value = value.lower()
    value = value.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "seo-tool"


def display_topic(value: str) -> str:
    return TOPIC_LABELS.get(value, value.replace("-", " ").replace("_", " ").strip().title() or "Lernen")


def internal_links_html(topic_cluster: str) -> str:
    links = TOPIC_INTERNAL_LINKS.get(topic_cluster, TOPIC_INTERNAL_LINKS["lernmethoden"])
    items = "\n".join(f'        <li><a href="{html.escape(href)}">{html.escape(label)}</a></li>' for href, label in links)
    return f"""    <section>
      <h2>Passende nächste Übungen</h2>
      <p>Vertiefe das Thema mit passenden Erklärungen und Übungsstrategien:</p>
      <ul>
{items}
      </ul>
    </section>"""


def schema_markup(title: str, description: str, page_type: str) -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "name": title,
        "description": description,
        "learningResourceType": page_type,
        "inLanguage": "de",
        "isAccessibleForFree": True,
    }
    return '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False) + "</script>"


def render_interactive_page(
    title: str,
    description: str,
    page_type: str,
    topic_cluster: str,
    primary_keyword: str,
    subject: str = "allgemein",
    grade_level: str = "unknown",
    exam_type: str = "",
    difficulty: str = "mixed",
    solution_mode: str = "step_by_step",
    interaction_type: str = "self_check",
    expected_learning_outcome: str = "Learner can solve and explain the task type independently.",
    indexable: bool = True,
) -> str:
    safe_title = html.escape(title)
    safe_description = html.escape(description)
    safe_cluster = html.escape(topic_cluster)
    safe_keyword = html.escape(primary_keyword)
    links_html = internal_links_html(topic_cluster)
    schema = schema_markup(title, description, page_type)
    robots = "" if indexable else '  <meta name="robots" content="noindex,follow">\n'
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} | Nachhilfe Mentor</title>
  <meta name="description" content="{safe_description}">
{robots}  <meta name="quality-policy" content="quality-first, adaptive-publishing">
  <link rel="canonical" href="https://nachhilfe-mentor.de/lernmaterialien/{slugify(title)}.html">
  <link rel="stylesheet" href="/styles/modern-tech.css">
  {schema}
</head>
<body data-page-id="tool:{slugify(title)}" data-slug="{slugify(title)}" data-topic-cluster="{safe_cluster}" data-primary-keyword="{safe_keyword}" data-search-intent="informational" data-content-type="{html.escape(page_type)}" data-asset-type="{html.escape(page_type)}" data-subject="{html.escape(subject)}" data-grade-level="{html.escape(grade_level)}" data-exam-type="{html.escape(exam_type)}" data-difficulty="{html.escape(difficulty)}" data-solution-mode="{html.escape(solution_mode)}" data-interaction-type="{html.escape(interaction_type)}" data-expected-learning-outcome="{html.escape(expected_learning_outcome)}" data-template-version="interactive-v1">
  <main class="container" style="max-width: 920px; margin: 0 auto; padding: 48px 20px;">
    <h1>{safe_title}</h1>
    <p>{safe_description}</p>
    <section aria-labelledby="tool-heading">
      <h2 id="tool-heading">Aktive Übung</h2>
      <p>Löse zuerst selbst. Danach prüft die Seite deine Antwort, erklärt den nächsten Schritt und gibt dir eine passende Wiederholung.</p>
      <label for="difficulty">Niveau</label>
      <select id="difficulty">
        <option value="leicht">Leicht</option>
        <option value="mittel">Mittel</option>
        <option value="schwer">Schwer</option>
      </select>
      <label for="learner-answer">Deine Antwort</label>
      <input id="learner-answer" autocomplete="off" placeholder="Antwort oder Rechenweg eingeben">
      <button type="button" id="check-result">Antwort prüfen</button>
      <button type="button" id="show-solution">Hinweis anzeigen</button>
      <button type="button" id="retry-task">Ähnliche Aufgabe</button>
      <output id="result" aria-live="polite"></output>
    </section>
    <section>
      <h2>Beispielaufgabe mit Lösung</h2>
      <p><strong>Aufgabe:</strong> Erkläre den wichtigsten Schritt für: {safe_keyword}.</p>
      <p><strong>Lösung:</strong> Zerlege die Aufgabe in bekannte Teilregeln, prüfe jeden Schritt und formuliere am Ende einen kurzen Merksatz.</p>
      <p><strong>Typischer Fehler:</strong> Zu früh rechnen oder schreiben, ohne die Aufgabenstellung zu markieren.</p>
    </section>
    <section>
      <h2>So nutzt du das Ergebnis</h2>
      <p>Plane zuerst die unsicheren Themen, wiederhole sie kurz und prüfe danach mit einer kleinen Aufgabe, ob du den Schritt erklären kannst.</p>
      <ul>
        <li>Bei niedriger Sicherheit: Grundlagen wiederholen.</li>
        <li>Bei mittlerer Sicherheit: zwei gemischte Aufgaben lösen.</li>
        <li>Bei hoher Sicherheit: eine Prüfungsaufgabe unter Zeitdruck testen.</li>
      </ul>
      <p>Diese Reihenfolge verhindert, dass du nur Musterlösungen liest. Du übst zuerst das Erkennen der Aufgabe, dann den Rechen- oder Schreibweg und am Ende die Kontrolle. Genau diese Abfolge ist wichtig, wenn du später in einer Klassenarbeit, Klausur oder mündlichen Prüfung sicher reagieren willst.</p>
    </section>
    <section>
      <h2>Nächster Lernschritt</h2>
      <p>Notiere nach der Aufgabe einen Satz: Was war die Regel, woran hast du sie erkannt und welcher Fehler wäre typisch? Wenn du diesen Satz ohne Blick in die Lösung formulieren kannst, ist der Stoff bereit für gemischte Aufgaben. Wenn nicht, wiederhole zuerst ein leichteres Beispiel.</p>
      <p>In der Nachhilfe Mentor App kannst du diesen Lernschritt später mit passenden Wiederholungen verbinden, ohne deine Antworten hier auf der Webseite zu speichern.</p>
    </section>
{links_html}
  </main>
  <script src="/scripts/posthog-tracking.js" defer></script>
  <script>
    var practiceStarted = false;
    function capturePracticeStarted() {{
      if (practiceStarted) {{
        return;
      }}
      practiceStarted = true;
      if (window.posthog && window.posthog.capture) {{
        window.posthog.capture('practice_started', {{
          page_id: 'tool:{slugify(title)}',
          slug: '{slugify(title)}',
          asset_type: '{html.escape(page_type)}',
          subject: '{html.escape(subject)}',
          grade_level: '{html.escape(grade_level)}',
          exam_type: '{html.escape(exam_type)}',
          difficulty: document.getElementById('difficulty').value,
          interaction_type: '{html.escape(interaction_type)}'
        }});
      }}
    }}
    document.getElementById('check-result').addEventListener('click', function () {{
      capturePracticeStarted();
      var answer = document.getElementById('learner-answer').value.trim();
      var value = answer.length;
      var result = value < 4 ? 'Noch zu kurz. Schreibe mindestens den entscheidenden Schritt auf.' : value < 18 ? 'Guter Start. Ergänze jetzt Regel und Begründung.' : 'Richtig aufgebaut. Wiederhole nun eine ähnliche Aufgabe ohne Hinweis.';
      document.getElementById('result').textContent = result;
      if (window.posthog && window.posthog.capture) {{
        window.posthog.capture('{ "practice_completed" if page_type in {"practice_page", "mini_test", "worksheet", "quiz", "exam_simulator", "formula_practice", "grammar_drill"} else "seo_tool_completed" }', {{
          page_id: 'tool:{slugify(title)}',
          slug: '{slugify(title)}',
          asset_type: '{html.escape(page_type)}',
          subject: '{html.escape(subject)}',
          grade_level: '{html.escape(grade_level)}',
          exam_type: '{html.escape(exam_type)}',
          topic_cluster: '{safe_cluster}',
          primary_keyword: '{safe_keyword}',
          content_type: '{html.escape(page_type)}',
          tool_type: '{html.escape(page_type)}',
          difficulty_level: document.getElementById('difficulty').value,
          completion_status: value >= 18 ? 'completed' : 'needs_retry'
        }});
      }}
    }});
    document.getElementById('show-solution').addEventListener('click', function () {{
      capturePracticeStarted();
      document.getElementById('result').textContent = 'Hinweis: Markiere zuerst, welche Regel passt. Danach wendest du sie Schritt für Schritt an und prüfst das Ergebnis.';
      if (window.posthog && window.posthog.capture) {{
        window.posthog.capture('solution_revealed', {{
          page_id: 'tool:{slugify(title)}',
          slug: '{slugify(title)}',
          asset_type: '{html.escape(page_type)}',
          solution_mode: '{html.escape(solution_mode)}',
          question_type: 'worked_example'
        }});
      }}
    }});
    document.getElementById('retry-task').addEventListener('click', function () {{
      capturePracticeStarted();
      document.getElementById('learner-answer').value = '';
      document.getElementById('result').textContent = 'Neue Wiederholung: Löse eine ähnliche Aufgabe und schreibe den entscheidenden Zwischenschritt auf.';
      if (window.posthog && window.posthog.capture) {{
        window.posthog.capture('retry_clicked', {{
          page_id: 'tool:{slugify(title)}',
          slug: '{slugify(title)}',
          asset_type: '{html.escape(page_type)}'
        }});
      }}
    }});
  </script>
</body>
</html>
"""


def generate_page(
    settings: Settings,
    title: str,
    description: str,
    page_type: str,
    topic_cluster: str,
    primary_keyword: str,
    subject: str = "allgemein",
    grade_level: str = "unknown",
    exam_type: str = "",
    difficulty: str = "mixed",
    solution_mode: str = "step_by_step",
    interaction_type: str = "self_check",
    expected_learning_outcome: str = "Learner can solve and explain the task type independently.",
    indexable: bool = True,
) -> tuple[Path | None, QualityResult]:
    html_text = render_interactive_page(title, description, page_type, topic_cluster, primary_keyword, subject, grade_level, exam_type, difficulty, solution_mode, interaction_type, expected_learning_outcome, indexable=indexable)
    quality = check_interactive_page_quality(title, html_text, page_type)
    if not quality.ok:
        return None, quality
    if not settings.page_generation_enabled:
        return None, quality
    out_dir = GENERATED_DIR if indexable else GENERATED_DIR / "entwuerfe"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{slugify(title)}.html"
    path.write_text(html_text, encoding="utf-8")
    return path, quality
