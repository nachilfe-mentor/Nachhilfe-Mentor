from __future__ import annotations

from .task_schema import CodingTask


def build_codex_prompt(task: CodingTask) -> str:
    allowed = "\n".join(f"- {item}" for item in task.allowed_paths)
    forbidden = "\n".join(f"- {item}" for item in task.forbidden_paths)
    criteria = "\n".join(f"- {item}" for item in task.acceptance_criteria)
    safety = "\n".join(f"- {item}" for item in task.safety_constraints)
    tests = "\n".join(f"- `{item}`" for item in task.test_commands) or "- No tests specified; add or run focused validation if appropriate."
    return f"""Du bist ein Coding Agent im Nachhilfe-Mentor-Repo.

Arbeite nicht als normaler Chat-LLM. Lies das Repo, ändere nur erlaubte Dateien, führe Tests aus und liefere eine kurze technische Zusammenfassung.

Task ID: {task.id}
Task type: {task.task_type}
Mode: {task.mode}
Publish policy: {task.publish_policy}

Ziel:
{task.goal}

Kontextzusammenfassung:
{task.context_summary[:2500]}

Erlaubte Dateien/Ordner:
{allowed}

Verbotene Dateien/Ordner:
{forbidden}

Safety Rules:
{safety}
- Kein Deploy.
- Kein Push.
- Keine Live-Veröffentlichung.
- Keine Secrets lesen, ausgeben oder in Reports schreiben.
- Keine .env-Dateien oder Service-Account-JSONs ausgeben.
- Keine indexierbaren Seiten veröffentlichen; Practice Pages nur als Draft/Spec/noindex.
- Bei Safety-Konflikt abbrechen und erklären.

Akzeptanzkriterien:
{criteria}

Testbefehle:
{tests}

Output-Erwartung:
- Kurze Zusammenfassung
- Geänderte Dateien
- Tests ausgeführt
- Offene Risiken/TODOs
- Ob ein Safety Gate blockiert hat
"""
