from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ParsedJobRecord, SearchResult


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_raw_results(path: Path, query_list: list[str], raw_results: list[SearchResult]) -> None:
    _ensure_parent_dir(path)
    payload: dict[str, Any] = {
        "queries": query_list,
        "result_count": len(raw_results),
        "results": [result.to_dict() for result in raw_results],
    }
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def write_parsed_results(path: Path, parsed_results: list[ParsedJobRecord]) -> None:
    _ensure_parent_dir(path)
    payload = {
        "record_count": len(parsed_results),
        "records": [record.to_dict() for record in parsed_results],
    }
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
