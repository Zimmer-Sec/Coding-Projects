from __future__ import annotations

from typing import Iterable


def chunk_list(items: list[str], chunk_size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), chunk_size):
        yield items[i : i + chunk_size]


def generate_google_dorks(
    targets: list[str],
    sites: list[str],
    extra_terms: list[str] | None = None,
    per_query_site_limit: int = 8,
) -> list[str]:
    """
    Build Google dorks using target keywords and region-specific hiring sites.

    Example query output:
      intext:"Acme" (site:linkedin.com OR site:indeed.com) (jobs OR careers)
    """
    if not targets:
        return []

    clean_targets = [t.strip() for t in targets if t and t.strip()]
    clean_sites = [s.strip() for s in sites if s and s.strip()]

    if not clean_targets or not clean_sites:
        return []

    extra_terms = extra_terms or ["job", "jobs", "career", "careers", "hiring"]
    terms_clause = " OR ".join(extra_terms)

    queries: list[str] = []
    for target in clean_targets:
        target_clause = f'intext:"{target}"'
        for site_group in chunk_list(clean_sites, max(1, per_query_site_limit)):
            sites_clause = " OR ".join(f"site:{domain}" for domain in site_group)
            query = f"{target_clause} ({sites_clause}) ({terms_clause})"
            queries.append(query)

    return queries
