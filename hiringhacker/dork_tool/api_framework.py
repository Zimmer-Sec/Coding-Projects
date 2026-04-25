from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config_loader import load_yaml_file

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class APIProviderConfig:
    name: str
    enabled: bool
    base_url: str
    auth_type: str
    notes: str = ""


class APIIntegrationManager:
    """
    Placeholder framework for paywalled/registration-only hiring sites.

    Community contributors can implement provider-specific clients in the future
    without changing the CLI contract.
    """

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.providers: dict[str, APIProviderConfig] = {}

    def load(self) -> None:
        if not self.config_path.exists():
            LOGGER.info("API integration config not found at %s. Skipping.", self.config_path)
            return

        raw = load_yaml_file(self.config_path)
        providers = raw.get("providers", {})
        if not isinstance(providers, dict):
            LOGGER.warning("Expected 'providers' mapping in API config.")
            return

        for provider_name, details in providers.items():
            if not isinstance(details, dict):
                continue
            cfg = APIProviderConfig(
                name=provider_name,
                enabled=bool(details.get("enabled", False)),
                base_url=str(details.get("base_url", "")),
                auth_type=str(details.get("auth_type", "none")),
                notes=str(details.get("notes", "")),
            )
            self.providers[provider_name] = cfg

    def get_enabled_providers(self) -> list[APIProviderConfig]:
        return [provider for provider in self.providers.values() if provider.enabled]

    def fetch_jobs(self, provider_name: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Placeholder method for future paywalled API integrations.

        Not implemented by design. Contributors should provide adapter modules that:
        - handle auth flows
        - request site-specific endpoints
        - normalize into the ParsedJobRecord schema
        """
        raise NotImplementedError(
            f"Provider '{provider_name}' is not implemented yet. "
            "Add an adapter in future community extension modules."
        )
