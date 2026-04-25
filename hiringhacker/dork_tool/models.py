from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class SearchResult:
    """A raw web search result returned from a search engine."""

    query: str
    title: str
    snippet: str
    url: str
    source_engine: str = "google"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ParsedJobRecord:
    """Structured, downstream-friendly record built from a raw search result."""

    originating_site: str
    company_name: str
    position: str
    description: str
    url: str
    date_found: str
    region: str

    @staticmethod
    def now_utc_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
