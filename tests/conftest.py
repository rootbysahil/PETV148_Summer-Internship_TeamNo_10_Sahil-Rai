import json
import pytest
from pathlib import Path
from src.models import ScanResult, ScanSummary, PlatformHit
from datetime import datetime

@pytest.fixture
def sample_scan_result() -> ScanResult:
    """Provides a sample populated ScanResult model."""
    summary = ScanSummary(
        username="testuser",
        timestamp=datetime.fromisoformat("2026-07-03T12:00:00"),
        total_checked=3,
        total_found=2,
        total_not_found=1,
        total_errors=0,
        total_skipped=0,
        success_rate_pct=66.67,
        fastest_platform="GitHub",
        fastest_time_ms=120.5,
        slowest_platform="Reddit",
        slowest_time_ms=350.2,
        total_duration_seconds=1.5,
        category_breakdown={"coding": 1, "social": 1}
    )
    hits = [
        PlatformHit(
            platform_name="GitHub",
            category="coding",
            profile_url="https://github.com/testuser",
            status="FOUND",
            http_status=200,
            response_time_ms=120.5
        ),
        PlatformHit(
            platform_name="Reddit",
            category="social",
            profile_url="https://www.reddit.com/user/testuser",
            status="FOUND",
            http_status=200,
            response_time_ms=350.2
        ),
        PlatformHit(
            platform_name="Instagram",
            category="social",
            profile_url="https://www.instagram.com/testuser/",
            status="NOT_FOUND",
            http_status=404,
            response_time_ms=210.1
        )
    ]
    return ScanResult(summary=summary, hits=hits)

@pytest.fixture
def mock_platforms_json(tmp_path: Path) -> Path:
    """Creates a temporary mock platforms.json file."""
    data = {
        "MockSite1": {
            "errorType": "status_code",
            "url": "https://mocksite1.com/{}",
            "urlMain": "https://mocksite1.com/",
            "category": "social",
            "errorStatus": 404
        },
        "MockSite2": {
            "errorType": "message",
            "url": "https://mocksite2.com/user/{}",
            "urlMain": "https://mocksite2.com/",
            "category": "coding",
            "errorMsg": "not found"
        }
    }
    file_path = tmp_path / "test_platforms.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return file_path
