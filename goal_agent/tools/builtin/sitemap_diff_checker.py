from __future__ import annotations


def diff_sitemap(content_rows: list[dict]) -> dict:
    indexable = [row["url_path"] for row in content_rows if row.get("content_type") in {"landing_page", "blog_index", "blog_article", "interactive_tool"}]
    missing = [row["url_path"] for row in content_rows if row["url_path"] in indexable and not row.get("is_in_sitemap")]
    return {"indexable_count": len(indexable), "missing_from_sitemap": missing}
