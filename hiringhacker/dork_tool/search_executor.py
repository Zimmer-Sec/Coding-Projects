from __future__ import annotations

import logging
import random
import time
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from .models import SearchResult

LOGGER = logging.getLogger(__name__)


class SearchExecutionError(Exception):
    """Raised when search execution repeatedly fails."""


class GoogleSearchExecutor:
    """Simple HTML-based Google search executor with delay/retry behavior."""

    GOOGLE_URL = "https://www.google.com/search"

    def __init__(
        self,
        delay_seconds: float = 2.5,
        jitter_seconds: float = 0.75,
        timeout_seconds: int = 20,
        max_retries: int = 3,
        language: str = "en",
    ) -> None:
        self.delay_seconds = delay_seconds
        self.jitter_seconds = jitter_seconds
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.language = language
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            }
        )

    def _sleep(self) -> None:
        delay = self.delay_seconds + random.uniform(0, self.jitter_seconds)
        LOGGER.debug("Sleeping for %.2f seconds before next query", delay)
        time.sleep(delay)

    def _extract_google_redirect(self, href: str) -> str:
        parsed = urlparse(href)
        if parsed.path == "/url":
            q_values = parse_qs(parsed.query).get("q", [])
            if q_values:
                return q_values[0]
        return href

    def _parse_results(self, query: str, html: str) -> list[SearchResult]:
        soup = BeautifulSoup(html, "html.parser")

        parsed_results: list[SearchResult] = []
        seen_urls: set[str] = set()

        # Primary parse strategy.
        for card in soup.select("div.g"):
            anchor = card.select_one("a")
            if not anchor:
                continue
            href = anchor.get("href", "").strip()
            if not href:
                continue

            url = self._extract_google_redirect(href)
            if not url.startswith("http") or url in seen_urls:
                continue

            title_el = card.select_one("h3")
            snippet_el = card.select_one("div.VwiC3b, span.aCOpRe, div.IsZvec")

            title = title_el.get_text(" ", strip=True) if title_el else ""
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

            if not title and not snippet:
                continue

            parsed_results.append(SearchResult(query=query, title=title, snippet=snippet, url=url))
            seen_urls.add(url)

        # Fallback parse strategy if Google markup differs or primary strategy yields none.
        if not parsed_results:
            for anchor in soup.select("a[href^='/url?q=']"):
                href = anchor.get("href", "").strip()
                if not href:
                    continue

                url = self._extract_google_redirect(href)
                if not url.startswith("http") or url in seen_urls:
                    continue

                title = anchor.get_text(" ", strip=True)
                snippet = ""

                container = anchor.find_parent("div")
                if container:
                    snippet_el = container.select_one("div.VwiC3b, span.aCOpRe, div.IsZvec")
                    if snippet_el:
                        snippet = snippet_el.get_text(" ", strip=True)

                if not title and not snippet:
                    continue

                parsed_results.append(SearchResult(query=query, title=title, snippet=snippet, url=url))
                seen_urls.add(url)

        return parsed_results

    def run_query(self, query: str, max_results: int = 20) -> list[SearchResult]:
        """Execute one query with retries and minimal anti-block safeguards."""
        if not query.strip():
            return []

        params = {
            "q": query,
            "hl": self.language,
            "num": min(100, max(10, max_results)),
            "pws": "0",  # disable personalized results where possible
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                LOGGER.info("Running query (attempt %d/%d): %s", attempt, self.max_retries, query)
                response = self.session.get(
                    self.GOOGLE_URL,
                    params=params,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()

                html = response.text
                if "Our systems have detected unusual traffic" in html or "detected unusual traffic" in html:
                    raise SearchExecutionError(
                        "Google returned anti-bot page. Increase delay or reduce query frequency."
                    )

                results = self._parse_results(query=query, html=html)
                LOGGER.info("Found %d result(s) for query", len(results))
                self._sleep()
                return results[:max_results]

            except (requests.RequestException, SearchExecutionError) as exc:
                LOGGER.warning("Query failed on attempt %d: %s", attempt, exc)
                if attempt == self.max_retries:
                    raise SearchExecutionError(
                        f"Failed query after {self.max_retries} attempts: {query}"
                    ) from exc
                backoff = (2 ** (attempt - 1)) + random.uniform(0, 0.75)
                LOGGER.info("Backing off for %.2f seconds", backoff)
                time.sleep(backoff)

        return []

    def run_queries(self, queries: list[str], max_results_per_query: int) -> list[SearchResult]:
        all_results: list[SearchResult] = []
        for idx, query in enumerate(queries, start=1):
            LOGGER.info("Executing query %d/%d", idx, len(queries))
            try:
                query_results = self.run_query(query, max_results=max_results_per_query)
                all_results.extend(query_results)
            except SearchExecutionError as exc:
                LOGGER.error("Skipping query due to repeated failures: %s", exc)
        return all_results
