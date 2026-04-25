from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

LOGGER = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised for invalid configuration scenarios."""


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML parsing error in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"Expected top-level object in {path} to be a mapping")

    return data


def load_region_config(path: Path) -> dict[str, Any]:
    config = load_yaml_file(path)

    if "regions" not in config or not isinstance(config["regions"], dict):
        raise ConfigError("Region config must contain a 'regions' mapping")

    config.setdefault("country_to_region", {})
    config.setdefault("defaults", {})

    return config


def resolve_region(location_input: str, region_config: dict[str, Any]) -> str:
    """Resolve free-form location/region text to canonical region key."""
    if not location_input:
        raise ConfigError("Region or country input cannot be empty")

    normalized = location_input.strip().lower()
    regions: dict[str, Any] = region_config["regions"]
    aliases = region_config.get("country_to_region", {})

    # Direct region key match
    for region_key in regions:
        if normalized == region_key.lower():
            return region_key

    # Match by aliases configured per region
    for region_key, region_data in regions.items():
        for alias in region_data.get("aliases", []):
            if normalized == str(alias).strip().lower():
                return region_key

    # Match by country map
    for country_name, mapped_region in aliases.items():
        if normalized == str(country_name).strip().lower():
            if mapped_region not in regions:
                raise ConfigError(
                    f"country_to_region maps '{country_name}' to unknown region '{mapped_region}'"
                )
            return mapped_region

    valid_regions = ", ".join(regions.keys())
    raise ConfigError(
        f"Could not resolve location '{location_input}' to a configured region. "
        f"Try one of: {valid_regions}"
    )


def get_region_sites(region_key: str, region_config: dict[str, Any]) -> list[str]:
    region_data = region_config["regions"].get(region_key, {})
    sites = region_data.get("sites", [])
    if not sites:
        LOGGER.warning("No hiring sites configured for region '%s'", region_key)
    return [str(site).strip() for site in sites if str(site).strip()]
