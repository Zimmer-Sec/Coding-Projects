from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from .api_framework import APIIntegrationManager
from .config_loader import ConfigError, get_region_sites, load_region_config, resolve_region
from .dork_generator import generate_google_dorks
from .output_writer import write_parsed_results, write_raw_results
from .parser import parse_search_results
from .search_executor import GoogleSearchExecutor

LOGGER = logging.getLogger("hiring_dork_tool")


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _parse_targets(target_inputs: list[str]) -> list[str]:
    normalized: list[str] = []
    for entry in target_inputs:
        parts = [p.strip() for p in entry.split(",") if p.strip()]
        normalized.extend(parts)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_targets: list[str] = []
    for target in normalized:
        key = target.lower()
        if key not in seen:
            seen.add(key)
            unique_targets.append(target)
    return unique_targets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Google Dorking tool for job-posting reconnaissance",
    )
    parser.add_argument(
        "-t",
        "--target",
        action="append",
        required=True,
        help="Target company keyword/name. Repeat for multiple values or pass comma-separated keywords.",
    )
    parser.add_argument(
        "-l",
        "--location",
        required=True,
        help="Region or country (e.g. US, Germany, APAC, Brazil, UAE)",
    )
    parser.add_argument(
        "--config",
        default="config/regions.yaml",
        help="Path to region/site config file",
    )
    parser.add_argument(
        "--api-config",
        default="config/api_integrations.example.yaml",
        help="Path to API integration config placeholder file",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.5,
        help="Base delay in seconds between queries",
    )
    parser.add_argument(
        "--jitter",
        type=float,
        default=0.75,
        help="Random jitter in seconds added to each delay",
    )
    parser.add_argument(
        "--max-results-per-query",
        type=int,
        default=20,
        help="Maximum results to parse per query",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory where raw and parsed outputs are written",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate dorks and config resolution only; do not execute searches",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(verbose=args.verbose)

    targets = _parse_targets(args.target)
    if not targets:
        LOGGER.error("No valid targets were provided.")
        return 2

    try:
        region_config_path = Path(args.config)
        region_config = load_region_config(region_config_path)
        resolved_region = resolve_region(args.location, region_config)
        sites = get_region_sites(resolved_region, region_config)
        per_query_site_limit = int(region_config.get("defaults", {}).get("per_query_site_limit", 8))
        if not sites:
            LOGGER.error("Resolved region '%s' has no configured sites.", resolved_region)
            return 2
    except (ConfigError, ValueError) as exc:
        LOGGER.error("Configuration error: %s", exc)
        return 2

    LOGGER.info("Targets: %s", targets)
    LOGGER.info("Input location '%s' mapped to region '%s'", args.location, resolved_region)
    LOGGER.info("Loaded %d hiring sites for region", len(sites))
    LOGGER.info("Per-query site chunk size: %d", max(1, per_query_site_limit))

    queries = generate_google_dorks(
        targets=targets,
        sites=sites,
        per_query_site_limit=max(1, per_query_site_limit),
    )
    if not queries:
        LOGGER.error("No queries generated. Check your targets and config.")
        return 2

    LOGGER.info("Generated %d dork query(ies)", len(queries))
    for q in queries:
        LOGGER.debug("Dork: %s", q)

    # Load API integration placeholders for future extension visibility.
    api_manager = APIIntegrationManager(Path(args.api_config))
    api_manager.load()
    enabled = api_manager.get_enabled_providers()
    LOGGER.info("API integration providers configured: %d enabled", len(enabled))

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_root = Path(args.output_dir)
    raw_path = output_root / "raw" / f"raw_results_{timestamp}.json"
    parsed_path = output_root / "parsed" / f"parsed_results_{timestamp}.json"

    if args.dry_run:
        LOGGER.info("Dry run enabled; skipping network search execution.")
        write_raw_results(raw_path, queries, [])
        write_parsed_results(parsed_path, [])
        LOGGER.info("Wrote dry-run outputs to %s and %s", raw_path, parsed_path)
        return 0

    executor = GoogleSearchExecutor(delay_seconds=args.delay, jitter_seconds=args.jitter)
    raw_results = executor.run_queries(queries, max_results_per_query=args.max_results_per_query)

    parsed_records = parse_search_results(
        search_results=raw_results,
        target_keywords=targets,
        region=resolved_region,
    )

    write_raw_results(raw_path, queries, raw_results)
    write_parsed_results(parsed_path, parsed_records)

    LOGGER.info("Saved raw results: %s", raw_path)
    LOGGER.info("Saved parsed results: %s", parsed_path)
    LOGGER.info("Finished. Parsed %d record(s).", len(parsed_records))

    return 0


if __name__ == "__main__":
    sys.exit(main())
