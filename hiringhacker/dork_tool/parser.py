from __future__ import annotations

import re
from urllib.parse import urlparse

from .models import ParsedJobRecord, SearchResult

SEPARATORS = r"[\-|–|—|:|\|]"


def _extract_domain(url: str) -> str:
    netloc = urlparse(url).netloc.lower().strip()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def _guess_position(title: str, snippet: str) -> str:
    if not title and not snippet:
        return "unknown"

    title = title.strip()
    if title:
        first_split = re.split(SEPARATORS, title, maxsplit=1)
        candidate = first_split[0].strip()
        if 2 <= len(candidate) <= 120:
            return candidate

    snippet = snippet.strip()
    if snippet:
        return snippet[:120]

    return "unknown"


def parse_search_results(
    search_results: list[SearchResult],
    target_keywords: list[str],
    region: str,
) -> list[ParsedJobRecord]:
    parsed_records: list[ParsedJobRecord] = []

    # Preserve deterministic company label while still handling multi-keyword input.
    company_label = " / ".join(target_keywords)

    for result in search_results:
        origin = _extract_domain(result.url)
        description = result.snippet or result.title
        position = _guess_position(result.title, result.snippet)

        record = ParsedJobRecord(
            originating_site=origin,
            company_name=company_label,
            position=position,
            description=description,
            url=result.url,
            date_found=ParsedJobRecord.now_utc_iso(),
            region=region,
        )
        parsed_records.append(record)

    return parsed_records
