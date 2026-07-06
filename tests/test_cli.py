import httpx
from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


class MockTransport(httpx.MockTransport):
    def __init__(self):
        super().__init__(self.handle_request)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=404, text="Not Found")


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scan" in result.output


def test_cli_scan_invalid_username():
    result = runner.invoke(app, ["scan", "invalid$user", "--accept-disclaimer"])
    assert result.exit_code != 0
    assert "invalid" in result.output.lower()


def test_cli_scan_disclaimer_refused():
    result = runner.invoke(app, ["scan", "testuser"], input="n\n")
    assert result.exit_code != 0
    assert "halted" in result.output.lower()


def test_cli_batch_file_not_found():
    result = runner.invoke(app, ["scan", "--input", "nonexistent_file.txt", "--accept-disclaimer"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_cli_scan_success(tmp_path, monkeypatch):
    # Setup directories mock inside config
    from config import settings

    monkeypatch.setattr(settings, "OUTPUT_DIR", tmp_path)

    # Mock httpx AsyncClient transport
    original_client_init = httpx.AsyncClient

    def mocked_client_init(*args, **kwargs):
        kwargs["transport"] = MockTransport()
        return original_client_init(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", mocked_client_init)

    # Run CLI command with disclaimer bypassed
    result = runner.invoke(app, ["scan", "testuser", "--accept-disclaimer"])
    assert result.exit_code == 0
    assert "Platform Scan Results" in result.output
    assert "Reports generated successfully" in result.output


def test_cli_platforms():
    result = runner.invoke(app, ["platforms"])
    assert result.exit_code == 0
    assert "Supported Platforms" in result.output
    assert "GitHub" in result.output
