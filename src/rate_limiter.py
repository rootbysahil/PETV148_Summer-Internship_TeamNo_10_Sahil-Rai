import asyncio
import time


class AsyncRateLimiter:
    """A thread-safe, async rate limiter implementing the token bucket algorithm."""

    def __init__(self, rate_limit_per_second: float):
        """Initializes the rate limiter.

        Args:
            rate_limit_per_second: The max number of requests allowed per second.
        """
        self.rate_limit = rate_limit_per_second
        self.max_tokens = max(1.0, rate_limit_per_second)
        self.tokens = self.max_tokens
        self.last_updated = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquires a token. Blocks if no tokens are available."""
        async with self.lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_updated
                self.last_updated = now

                # Add new tokens based on elapsed time
                self.tokens = min(self.max_tokens, self.tokens + elapsed * self.rate_limit)

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return

                # Sleep for the duration needed to generate the next token
                needed_tokens = 1.0 - self.tokens
                sleep_time = needed_tokens / self.rate_limit
                await asyncio.sleep(sleep_time)
        return
