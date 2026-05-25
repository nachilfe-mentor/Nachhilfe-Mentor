from __future__ import annotations


def scan_placeholder(keyword: str) -> dict:
    return {
        "keyword": keyword,
        "provider": None,
        "serp_weakness_score": 0.3,
        "note": "No SERP provider configured; aggressive scraping is blocked.",
    }
