from datetime import datetime

from pydantic import BaseModel, Field


class PlatformHit(BaseModel):
    """Represents a single query result on a specific platform."""

    platform_name: str
    category: str
    profile_url: str
    status: str  # FOUND, NOT_FOUND, UNKNOWN, ERROR, SKIPPED
    http_status: int | None = None
    response_time_ms: float = 0.0
    error_message: str | None = None


class ScanSummary(BaseModel):
    """Contains statistical analytics of a complete footprint scan run."""

    username: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_checked: int = 0
    total_found: int = 0
    total_not_found: int = 0
    total_errors: int = 0
    total_skipped: int = 0
    success_rate_pct: float = 0.0
    fastest_platform: str | None = None
    fastest_time_ms: float = float("inf")
    slowest_platform: str | None = None
    slowest_time_ms: float = 0.0
    total_duration_seconds: float = 0.0
    category_breakdown: dict[str, int] = Field(default_factory=dict)


class ScanResult(BaseModel):
    """The aggregate response containing details of all hits and analytics summary."""

    summary: ScanSummary
    hits: list[PlatformHit] = Field(default_factory=list)
