from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import REPO_ROOT, Settings
from .quality import QualityResult, check_interactive_page_quality


DRAFTS_DIR = REPO_ROOT / "lernmaterialien" / "entwuerfe"
PUBLISHED_DIR = REPO_ROOT / "lernmaterialien"


@dataclass(frozen=True)
class PromotionResult:
    draft_path: Path
    published_path: Path | None
    status: str
    quality: QualityResult
    reasons: list[str]


def _extract_title(html: str, fallback: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
    if not match:
        return fallback
    title = re.sub(r"\s*\|\s*Nachhilfe Mentor\s*$", "", match.group(1).strip())
    return re.sub(r"\s+", " ", title) or fallback


def _destination_for(draft_path: Path) -> Path:
    stem = draft_path.stem
    stem = re.sub(r"-(practice-)?draft$", "", stem)
    if not stem:
        stem = draft_path.stem
    return PUBLISHED_DIR / f"{stem}.html"


def _make_indexable(html: str, slug: str) -> str:
    html = re.sub(r'\s*<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex[^"\']*["\']\s*/?>', "", html, flags=re.I)
    html = re.sub(r'content=["\']Noindex-Draft\s+für\s+', 'content="', html, flags=re.I)
    html = re.sub(r"Draft/noindex practice asset", "Practice asset", html, flags=re.I)
    html = re.sub(r'content=["\']draft-only,\s*noindex,\s*practice-first["\']', 'content="quality-approved, practice-first"', html, flags=re.I)
    html = re.sub(r'content=["\']draft_noindex_only["\']', 'content="publish_indexable_after_quality_gate"', html, flags=re.I)
    html = re.sub(r"\s*<p\b[^>]*>[^<]*(?:Draft/noindex|noindex|nicht indexierbar|nicht live veröffentlicht|Sitemap)[\s\S]*?</p>", "", html, flags=re.I)
    html = re.sub(r"\s*<li\b[^>]*>[^<]*(?:Draft/noindex|noindex|nicht indexierbar|nicht live veröffentlicht|Sitemap)[\s\S]*?</li>", "", html, flags=re.I)
    html = "\n".join(
        line
        for line in html.splitlines()
        if not re.search(r"Draft/noindex|nicht indexierbar|nicht live veröffentlicht|Dieser Draft bleibt noindex|Sitemap oder indexierbare", line, flags=re.I)
    )
    if "rel=\"canonical\"" not in html and "rel='canonical'" not in html:
        html = html.replace(
            "</head>",
            f'  <link rel="canonical" href="https://nachhilfe-mentor.de/lernmaterialien/{slug}.html">\n</head>',
            1,
        )
    return html


def _promotion_reasons(html: str, quality: QualityResult, published_path: Path) -> list[str]:
    reasons: list[str] = []
    if not quality.ok:
        reasons.extend(quality.problems)
    if quality.score < 0.9:
        reasons.append(f"quality score below promotion threshold: {quality.score}")
    if not re.search(r"<a\s+[^>]*href=", html, flags=re.I):
        reasons.append("missing useful internal links")
    if not re.search(r"practice_started|practice_completed|solution_revealed|answer_checked", html):
        reasons.append("missing practice-safe tracking hooks")
    if published_path.exists():
        reasons.append("published target already exists")
    return reasons


def promote_drafts(settings: Settings, limit: int | None = None) -> list[PromotionResult]:
    if not settings.page_generation_enabled:
        return []
    drafts_dir = settings.repo_root / "lernmaterialien" / "entwuerfe"
    if not drafts_dir.exists():
        return []
    max_promotions = limit if limit is not None else settings.emergency_max_generated_pages_per_run
    results: list[PromotionResult] = []
    for draft_path in sorted(drafts_dir.glob("*.html")):
        if len([result for result in results if result.status == "promoted"]) >= max_promotions:
            break
        html = draft_path.read_text(encoding="utf-8", errors="ignore")
        title = _extract_title(html, draft_path.stem)
        page_type = "practice_page" if "practice" in html.lower() or "übung" in html.lower() else "learning_utility"
        quality = check_interactive_page_quality(title, html, page_type)
        published_path = settings.repo_root / _destination_for(draft_path).relative_to(REPO_ROOT)
        reasons = _promotion_reasons(html, quality, published_path)
        if reasons:
            results.append(PromotionResult(draft_path, None, "held", quality, reasons))
            continue
        published_path.parent.mkdir(parents=True, exist_ok=True)
        published_html = _make_indexable(html, published_path.stem)
        visible_text = re.sub(r"<script\b.*?</script>", " ", published_html, flags=re.I | re.S)
        visible_text = re.sub(r"<style\b.*?</style>", " ", visible_text, flags=re.I | re.S)
        visible_text = re.sub(r"<[^>]+>", " ", visible_text)
        if re.search(r"Draft/noindex|nicht indexierbar|nicht live veröffentlicht", visible_text, flags=re.I):
            results.append(PromotionResult(draft_path, None, "held", quality, ["visible draft/noindex warning remained after cleanup"]))
            continue
        final_quality = check_interactive_page_quality(title, published_html, page_type)
        if not final_quality.ok:
            results.append(PromotionResult(draft_path, None, "held", final_quality, final_quality.problems))
            continue
        published_path.write_text(published_html, encoding="utf-8")
        results.append(PromotionResult(draft_path, published_path, "promoted", final_quality, ["quality gate passed"]))
    return results
