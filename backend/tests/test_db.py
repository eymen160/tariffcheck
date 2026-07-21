"""Persistence layer (v3.5) — must be a perfect no-op without DATABASE_URL."""
import pytest


@pytest.fixture
def no_db(monkeypatch, app_module):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return app_module


def test_disabled_helpers_are_noops(no_db):
    import db
    assert db.db_enabled() is False
    assert db.record_lead({"email": "a@b.co"}) is False
    assert db.record_audit("analyze") is False
    assert db.lookup_api_key("sk-anything") is None


def test_env_api_keys_still_work_without_db(monkeypatch, no_db, client):
    monkeypatch.setenv("TARIFFCHECK_API_KEYS", "sk-a:Alpha")
    with no_db.app.test_request_context(headers={"X-API-Key": "sk-a"}):
        assert no_db.api_key_firm() == "Alpha"
    with no_db.app.test_request_context(headers={"X-API-Key": "sk-x"}):
        assert no_db.api_key_firm() is None


def test_db_key_checked_even_without_env_pairs(monkeypatch, no_db):
    # env TARIFFCHECK_API_KEYS unset → the DB lookup must still be consulted.
    monkeypatch.delenv("TARIFFCHECK_API_KEYS", raising=False)
    import db
    calls = []
    monkeypatch.setattr(db, "lookup_api_key",
                        lambda k: calls.append(k) or "DbFirm")
    with no_db.app.test_request_context(headers={"X-API-Key": "sk-db"}):
        assert no_db.api_key_firm() == "DbFirm"
    assert calls == ["sk-db"]


def test_leads_endpoint_survives_db_off(monkeypatch, no_db, client):
    import db
    monkeypatch.setattr(db, "record_lead", lambda p: False)
    res = client.post("/api/leads", json={"email": "broker@firm.com"})
    assert res.status_code == 200


def test_db_failure_never_raises(monkeypatch, no_db):
    import db
    monkeypatch.setenv(
        "DATABASE_URL", "postgres://u:p@nonexistent.invalid:5432/x")
    db._bootstrapped = False
    # Connecting to a nonexistent host must swallow and report False.
    assert db.record_audit("analyze") is False


def test_hash_key_stable(no_db):
    import db
    assert db.hash_key("abc") == db.hash_key("abc")
    assert db.hash_key("abc") != db.hash_key("abd")
