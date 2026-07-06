import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import datetime

import httpx

from config import settings
from src.logger import mask_username, setup_logger
from src.models import PlatformHit, ScanResult, ScanSummary
from src.rate_limiter import AsyncRateLimiter
from src.sherlock_engine import SherlockEngine

logger = setup_logger("smft.scanner")


class Scanner:
    """Orchestrates concurrent social footprint scans across target platforms."""

    def __init__(self, engine: SherlockEngine):
        """Initializes the Scanner.

        Args:
            engine: The platform detection engine.
        """
        self.engine = engine
        self.rate_limiter = AsyncRateLimiter(settings.RATE_LIMIT_PER_SECOND)

    async def scan_username(
        self,
        username: str,
        platforms: list[str] | None = None,
        progress_callback: Callable[[PlatformHit], Awaitable[None]] | None = None,
    ) -> ScanResult:
        """Runs concurrent searches for a given username.

        Args:
            username: Target username to search.
            platforms: Subset of platforms to scan. If None, scans all supported platforms.
            progress_callback: Optional async function called as each platform completes.

        Returns:
            ScanResult: Object containing all platform hits and analytics.
        """
        target_platforms = platforms if platforms else self.engine.get_supported_platforms()
        masked_user = mask_username(username)
        logger.info(
            f"Starting scan for username: {masked_user} across {len(target_platforms)} platforms."
        )

        start_time = time.perf_counter()
        hits: list[PlatformHit] = []

        # Limit parallel connections via asyncio.Semaphore
        semaphore = asyncio.Semaphore(settings.MAX_THREADS)

        async with httpx.AsyncClient() as client:
            tasks = [
                self._bounded_site_check(
                    client=client,
                    semaphore=semaphore,
                    site_name=site,
                    username=username,
                    progress_callback=progress_callback,
                )
                for site in target_platforms
            ]

            # Wait for all checks to complete concurrently
            hits = await asyncio.gather(*tasks)

        total_duration = time.perf_counter() - start_time
        summary = self._calculate_summary(username, hits, total_duration)

        logger.info(
            f"Finished scan for username: {masked_user}. "
            f"Found: {summary.total_found}/{summary.total_checked} profiles."
        )
        return ScanResult(summary=summary, hits=hits)

    async def _bounded_site_check(
        self,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore,
        site_name: str,
        username: str,
        progress_callback: Callable[[PlatformHit], Awaitable[None]] | None = None,
    ) -> PlatformHit:
        """Executes a rate-limited, semaphore-bounded individual check on a platform.

        Args:
            client: Shared HTTPX Async Client.
            semaphore: Connection semaphore.
            site_name: Platform target name.
            username: Target username.
            progress_callback: Progress notifier function.

        Returns:
            PlatformHit: Finished check data.
        """
        # Apply rate limits
        await self.rate_limiter.acquire()

        async with semaphore:
            hit = await self.engine.check_username_on_site(
                client=client,
                site_name=site_name,
                username=username,
                timeout_seconds=settings.TIMEOUT_SECONDS,
            )

            if progress_callback:
                try:
                    await progress_callback(hit)
                except Exception as e:
                    logger.error(f"Error in scanner progress callback: {e}")

            return hit

    def _calculate_summary(
        self, username: str, hits: list[PlatformHit], duration_seconds: float
    ) -> ScanSummary:
        """Computes statistical metrics and aggregates responses.

        Args:
            username: Scanned target username.
            hits: Resulting records.
            duration_seconds: Scan execution elapsed time.

        Returns:
            ScanSummary: Analytical summary values.
        """
        total_checked = len(hits)
        total_found = 0
        total_not_found = 0
        total_errors = 0
        total_skipped = 0

        fastest_platform = None
        fastest_time = float("inf")
        slowest_platform = None
        slowest_time = 0.0

        category_breakdown: dict[str, int] = {}

        for hit in hits:
            # Stats updates
            if hit.status == "FOUND":
                total_found += 1
                cat = hit.category
                category_breakdown[cat] = category_breakdown.get(cat, 0) + 1
            elif hit.status == "NOT_FOUND":
                total_not_found += 1
            elif hit.status == "SKIPPED":
                total_skipped += 1
            else:
                total_errors += 1

            # Time statistics
            if hit.status in ("FOUND", "NOT_FOUND"):
                if hit.response_time_ms < fastest_time:
                    fastest_time = hit.response_time_ms
                    fastest_platform = hit.platform_name
                if hit.response_time_ms > slowest_time:
                    slowest_time = hit.response_time_ms
                    slowest_platform = hit.platform_name

        success_rate = (total_found / total_checked * 100.0) if total_checked > 0 else 0.0

        return ScanSummary(
            username=username,
            timestamp=datetime.utcnow(),
            total_checked=total_checked,
            total_found=total_found,
            total_not_found=total_not_found,
            total_errors=total_errors,
            total_skipped=total_skipped,
            success_rate_pct=round(success_rate, 2),
            fastest_platform=fastest_platform,
            fastest_time_ms=round(fastest_time, 2) if fastest_time != float("inf") else 0.0,
            slowest_platform=slowest_platform,
            slowest_time_ms=round(slowest_time, 2),
            total_duration_seconds=round(duration_seconds, 2),
            category_breakdown=category_breakdown,
        )


class BatchScanner:
    """Handles serial scans of multiple target usernames."""

    def __init__(self, scanner: Scanner):
        """Initializes BatchScanner.

        Args:
            scanner: Single-user scan orchestrator.
        """
        self.scanner = scanner

    async def scan_multiple(
        self,
        usernames: list[str],
        progress_callback_factory: Callable[[str], Callable[[PlatformHit], Awaitable[None]]],
    ) -> list[ScanResult]:
        """Scans multiple usernames sequentially.

        Args:
            usernames: List of usernames to analyze.
            progress_callback_factory: Produces callback functions for each username.

        Returns:
            List[ScanResult]: List of all finished scan results.
        """
        results: list[ScanResult] = []
        for username in usernames:
            callback = progress_callback_factory(username)
            res = await self.scanner.scan_username(username=username, progress_callback=callback)
            results.append(res)
        return results
