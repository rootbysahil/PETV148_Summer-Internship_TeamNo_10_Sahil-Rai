from pathlib import Path
from config import settings

def test_config_defaults():
    assert settings.TIMEOUT_SECONDS == 10
    assert settings.ENABLE_COLORS is True
    assert settings.MAX_THREADS == 20
    assert settings.LOG_LEVEL == "INFO"
    assert settings.OUTPUT_DIR == Path("reports")
    assert settings.LOG_DIR == Path("logs")
