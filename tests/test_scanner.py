from pathlib import Path

import httpx
import pytest

from src.scanner import Scanner
from src.sherlock_engine import SherlockEngine


# Mock transport class to mock httpx AsyncClient queries response
class MockTransport(httpx.MockTransport):
    def __init__(self):
        super().__init__(self.handle_request)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        # Mock site rules
        if "mocksite1.com/valid" in url_str:
            return httpx.Response(status_code=200, text="Profile found")
        if "mocksite1.com/invalid" in url_str:
            return httpx.Response(status_code=404, text="Not Found")
        if "mocksite2.com/user/valid" in url_str:
            return httpx.Response(status_code=200, text="Welcome user!")
        if "mocksite2.com/user/invalid" in url_str:
            return httpx.Response(status_code=200, text="not found profile message")
        if "timeout" in url_str:
            raise httpx.TimeoutException("Mocked request timeout")
        return httpx.Response(status_code=500, text="Server Error")


@pytest.mark.asyncio
async def test_sherlock_engine_check(mock_platforms_json: Path):
    engine = SherlockEngine(platforms_data_path=mock_platforms_json)
    transport = MockTransport()

    async with httpx.AsyncClient(transport=transport) as client:
        # MockSite1 status code check - valid
        hit_1 = await engine.check_username_on_site(client, "MockSite1", "valid")
        assert hit_1.status == "FOUND"
        assert hit_1.http_status == 200

        # MockSite1 status code check - invalid
        hit_2 = await engine.check_username_on_site(client, "MockSite1", "invalid")
        assert hit_2.status == "NOT_FOUND"
        assert hit_2.http_status == 404

        # MockSite2 string message check - valid
        hit_3 = await engine.check_username_on_site(client, "MockSite2", "valid")
        assert hit_3.status == "FOUND"

        # MockSite2 string message check - invalid
        hit_4 = await engine.check_username_on_site(client, "MockSite2", "invalid")
        assert hit_4.status == "NOT_FOUND"


@pytest.mark.asyncio
async def test_scanner_orchestration(mock_platforms_json: Path):
    engine = SherlockEngine(platforms_data_path=mock_platforms_json)
    scanner = Scanner(engine)

    # Custom AsyncClient construction with transport mocking
    # Monkeypatch Scanner scan_username httpx.AsyncClient initialization
    original_client_init = httpx.AsyncClient

    def mocked_client_init(*args, **kwargs):
        kwargs["transport"] = MockTransport()
        return original_client_init(*args, **kwargs)

    import httpx as httpx_module

    httpx_module.AsyncClient = mocked_client_init

    try:
        result = await scanner.scan_username("valid")
        assert result.summary.total_checked == 2
        assert result.summary.total_found == 2
        assert result.summary.success_rate_pct == 100.0

        result_invalid = await scanner.scan_username("invalid")
        assert result_invalid.summary.total_found == 0
        assert result_invalid.summary.total_not_found == 2
    finally:
        # Restore client init
        httpx_module.AsyncClient = original_client_init
