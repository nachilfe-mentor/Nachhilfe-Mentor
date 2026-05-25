# Goal Agent: Subagents and Codex Coding Agent

## Architektur

Der Goal Agent ist kein normaler LLM-Caller. Der produktive Hauptpfad ist:

`Goal Orchestrator -> Subagenten -> Recommendations -> CodexTasks -> optionale Codex CLI -> Review/Safety -> Report`

Der bestehende Blog Agent bleibt getrennt und läuft weiter über `auto-blog.sh` mit Claude CLI. Er schreibt und veröffentlicht normale Blogartikel. Der Goal Agent darf bessere Blog-Briefings und Queue-Aufgaben erzeugen, schreibt aber keine normalen Blogartikel.

## Goal Orchestrator

Der Orchestrator sammelt Kontext aus Content-Scan, Sitemap, Blog-Queue, Blog-Guardian, PostHog/GSC-Signalen, Opportunities und Safety Gates. Danach ruft er deterministische Subagenten auf, konsolidiert deren Empfehlungen und erzeugt daraus priorisierte, sichere Codex Coding Tasks.

CLI:

```bash
python3 -m goal_agent.cli subagents run --cycle daily --dry-run
```

## Subagenten

Die Subagenten sind normale Python-Module unter `goal_agent/subagents/` und keine frei laufenden KI-Agenten.

- `SEOIntelligenceAgent`: Sitemap, GSC-Status, Content Scan, SEO-Chancen. GSC 403 bleibt non-fatal und wird als fehlender Search-Console-Zugriff berichtet.
- `ContentGapAgent`: Themenlücken, dünne Seiten, fehlende Übungen, Beispiele und Lösungen.
- `PracticeAssetAgent`: hochwertige Practice-first Assets wie Übungsseiten, Mini-Tests, Quiz, Worksheets und interaktive Aufgaben.
- `InternalLinkingAgent`: interne Linkchancen zwischen Blog, Lernseiten und Practice Assets.
- `BlogBriefAgent`: bessere Blog-Agent-Tasks und Briefings, ohne Artikel selbst zu schreiben.
- `QualityGuardianAgent`: blockiert dünne Seiten, Keyword Stuffing, schlechte Umlaute und Assets ohne Lernwert.
- `ReviewAgent`: prüft nach Coding-Läufen Git-Diff, Status, Tests und Safety-Verletzungen.

Recommendations werden in `subagent_recommendations` gespeichert und haben Priorität, Confidence, Safety-Risk, Publish-Entscheidung und Akzeptanzkriterien.

## CodexTask

Ein CodexTask ist eine sichere, überprüfbare Coding-Aufgabe für die lokal eingeloggte Codex CLI. Codex ist hier der ausführende Coding Agent: Repo lesen, Dateien ändern, Tests ausführen, Diff erzeugen, Ergebnis zusammenfassen.

Codex darf nicht automatisch pushen, deployen oder live veröffentlichen. Practice Pages werden standardmäßig nur als Draft, Spec oder `draft_noindex` Aufgabe erzeugt.

CLI:

```bash
python3 -m goal_agent.cli codex-tasks build --cycle daily
python3 -m goal_agent.cli codex-tasks list
python3 -m goal_agent.cli codex-tasks show --task-id <id>
python3 -m goal_agent.cli codex-tasks dry-run --task-id <id>
```

Manuelle Ausführung:

```bash
GOAL_AGENT_CODEX_ENABLED=true python3 -m goal_agent.cli codex-tasks run --task-id <id>
```

Bei einem schmutzigen Worktree wird die Ausführung standardmäßig blockiert. Nur bewusst über `--allow-dirty-worktree` oder `GOAL_AGENT_CODEX_ALLOW_DIRTY_WORKTREE=true` erlauben.

## ENV Variablen

```bash
GOAL_AGENT_CODEX_ENABLED=false
GOAL_AGENT_CODEX_BIN=codex
GOAL_AGENT_CODEX_TIMEOUT_SECONDS=900
GOAL_AGENT_CODEX_SANDBOX_MODE=workspace-write
GOAL_AGENT_CODEX_CREATE_BRANCH=false
GOAL_AGENT_CODEX_ALLOW_DIRTY_WORKTREE=false
GOAL_AGENT_CODEX_MAX_TASKS_PER_RUN=1
```

Die Codex CLI nutzt den lokalen Login. Es werden keine API Keys im Goal Agent hinterlegt.

## Safety Gates

Immer blockiert:

- `git push`
- Deploy- oder Live-Publish-Anweisungen
- Änderungen an `.env`, `/etc/nachhilfe-mentor`, Service-Account-Keys und `.git/`
- Secret-Ausgabe in Logs oder Reports
- Änderungen an `auto-blog.sh`, außer eine explizite Blog-Agent-Verbesserungsaufgabe erlaubt es
- direkte indexierbare Veröffentlichung von Practice Pages
- Löschen produktiver Daten
- ungeprüfte Shell Commands aus Subagenten-Texten

Erlaubt:

- Draft-Dateien
- Queue-Dateien
- Reports
- Tests
- interne Specs
- sichere Refactors
- Practice-Asset-Drafts
- Blog-Briefings für die bestehende Queue

## Modes

- `dry_run`: keine Codex-Ausführung, keine produktiven Writes.
- `queue_only`: Recommendations und Tasks queue'n, Codex nicht starten.
- `write_safe`: sichere Reports/Queues schreiben, Codex nur bei explizitem Task-Run.
- `autonomous_full`: darf CodexTasks erzeugen; Codex läuft trotzdem nur mit `GOAL_AGENT_CODEX_ENABLED=true` oder explizitem CLI-Flag.
- In `autonomous_full` wird pro Lauf standardmäßig höchstens ein CodexTask ausgeführt (`GOAL_AGENT_CODEX_MAX_TASKS_PER_RUN=1`).

Der bestehende Befehl bleibt kompatibel:

```bash
python3 -m goal_agent.cli run --cycle daily
```

Optional mit CodexTask-Erzeugung:

```bash
python3 -m goal_agent.cli run --cycle daily --queue-codex-tasks
```

## Reporting

Der Daily Report enthält Abschnitte für Subagenten und Codex Coding Agent:

- gelaufene Subagenten
- erzeugte und blockierte Recommendations
- Quality-Guardian-Entscheidungen
- Codex enabled/bin/mode
- Tasks created/runnable/blocked/executed
- letzte Exit Codes, geänderte Dateien und Safety Blocks

Vollständige Prompts und Secrets werden nicht in Reports geschrieben.

## GSC Status

Wenn der Service Account technisch konfiguriert ist, aber Search Console den Zugriff verweigert, bleibt der Lauf grün und berichtet:

`GSC configured, but service account lacks Search Console property access.`
