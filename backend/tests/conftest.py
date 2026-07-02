import sys
from pathlib import Path

import pytest

# Make backend/ importable regardless of where pytest is invoked from.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture
def app_module(monkeypatch):
    """The app module with no API key and a clean rate-limit bucket."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import app as app_mod
    app_mod._RATE_BUCKETS.clear()
    return app_mod


@pytest.fixture
def client(app_module):
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client
