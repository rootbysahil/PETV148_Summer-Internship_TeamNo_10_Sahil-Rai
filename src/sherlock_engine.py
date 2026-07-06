import json
import time
from pathlib import Path
from typing import Any, cast

import httpx

from src.logger import setup_logger
from src.models import PlatformHit

logger = setup_logger("smft.engine")


class SherlockEngine:
    """Detects username existence across online platforms using signature rules."""

    def __init__(self, platforms_data_path: Path | None = None):
        """Initializes the engine with platform signatures.

        Args:
            platforms_data_path: Path to the JSON containing site signatures.
        """
        if platforms_data_path is None:
            # Resolve default path relative to this file
            platforms_data_path = Path(__file__).parent.parent / "data" / "platforms.json"

        self.platforms_data_path = platforms_data_path
        self.platforms = self._load_platforms()

    def _load_platforms(self) -> dict[str, dict[str, Any]]:
        """Loads platform JSON file into memory."""
        try:
            with open(self.platforms_data_path, encoding="utf-8") as f:
                data = json.load(f)
                logger.info(
                    f"Loaded {len(data)} platform signatures from {self.platforms_data_path}"
                )
                return cast(dict[str, dict[str, Any]], data)
        except Exception as e:
            logger.critical(f"Failed to load platforms from {self.platforms_data_path}: {e}")
            raise RuntimeError(f"Could not load site signatures database: {e}") from e

    async def check_username_on_site(
        self, client: httpx.AsyncClient, site_name: str, username: str, timeout_seconds: int = 10
    ) -> PlatformHit:
        """Probes a single site to check if the username exists.

        Args:
            client: Shared asynchronous HTTP client.
            site_name: The name of the platform (key in JSON database).
            username: Target username to search.
            timeout_seconds: Timeout for the request.

        Returns:
            PlatformHit: The parsed scan details.
        """
        site_info = self.platforms.get(site_name)
        if not site_info:
            return PlatformHit(
                platform_name=site_name,
                category="unknown",
                profile_url="",
                status="ERROR",
                error_message="Site signature info missing from database.",
            )

        category = site_info.get("category", "other")
        target_url = site_info["url"].format(username)
        error_type = site_info.get("errorType", "status_code")

        # User-agent configuration mimicking modern browser to reduce blocks
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

        start_time = time.perf_counter()
        try:
            # We perform a GET request similar to Sherlock
            # Set follow_redirects=True because some sites redirect deleted profiles to home pages
            response = await client.get(
                target_url, headers=headers, timeout=timeout_seconds, follow_redirects=True
            )
            elapsed_time_ms = (time.perf_counter() - start_time) * 1000.0

            http_status = response.status_code
            status = "FOUND"

            # Check response depending on signature detection rules
            if error_type == "status_code":
                # For status code match, check if response code matches signature errorStatus
                err_status = site_info.get("errorStatus", 404)
                if http_status == err_status or http_status >= 400:
                    status = "NOT_FOUND"
            elif error_type == "message":
                err_msg = site_info.get("errorMsg")
                if err_msg and err_msg in response.text:
                    status = "NOT_FOUND"
            elif error_type == "response_url":
                # Check if final redirect URL matches main homepage or a specific page
                main_url = site_info.get("urlMain", "")
                if main_url and str(response.url).rstrip("/") == main_url.rstrip("/"):
                    status = "NOT_FOUND"

            logger.debug(
                f"Platform check: {site_name} | Username: {username} | Status: {status} | HTTP: {http_status}"
            )
            return PlatformHit(
                platform_name=site_name,
                category=category,
                profile_url=target_url,
                status=status,
                http_status=http_status,
                response_time_ms=round(elapsed_time_ms, 2),
            )

        except httpx.TimeoutException:
            elapsed_time_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(f"Timeout checking platform {site_name} for username {username}")
            return PlatformHit(
                platform_name=site_name,
                category=category,
                profile_url=target_url,
                status="UNKNOWN",
                error_message="Connection timeout.",
                response_time_ms=round(elapsed_time_ms, 2),
            )
        except httpx.RequestError as e:
            elapsed_time_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                f"Network error checking platform {site_name} for username {username}: {e}"
            )
            return PlatformHit(
                platform_name=site_name,
                category=category,
                profile_url=target_url,
                status="ERROR",
                error_message=str(e),
                response_time_ms=round(elapsed_time_ms, 2),
            )
        except Exception as e:
            elapsed_time_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Unexpected error checking platform {site_name}: {e}")
            return PlatformHit(
                platform_name=site_name,
                category=category,
                profile_url=target_url,
                status="ERROR",
                error_message=f"Unexpected error: {e}",
                response_time_ms=round(elapsed_time_ms, 2),
            )

    def get_supported_platforms(self) -> list[str]:
        """Returns list of registered platform names."""
        return list(self.platforms.keys())
