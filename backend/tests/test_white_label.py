"""White-label protest drafts + API-key/CORS hardening (v3.2).

White-label is an Enterprise/pilot feature: a valid X-API-Key identifies the
firm, and that firm's name appears as the preparing office on the generated
letter. Anonymous requests always get the plain TariffCheck draft — letterhead
cannot be forged by an unauthenticated caller.
"""
import pytest


FINDING = {
    "verified": True,
    "savings": 1200.0,
    "remedy": "1514",
    "hts_code": "9403.90.8040",
    "suggested_code": "9403.10.0000",
}


# ── generate_protest_letter(preparer_firm=...) ──────────────────────────────

def test_letter_default_has_no_letterhead(app_module):
    letter = app_module.generate_protest_letter([FINDING], 1200.0)
    assert "Prepared by" not in letter
    assert "TariffCheck does not file" in letter


def test_letter_with_preparer_firm_carries_letterhead(app_module):
    letter = app_module.generate_protest_letter(
        [FINDING], 1200.0, preparer_firm="Acme Customs Brokerage LLC")
    assert "Acme Customs Brokerage LLC" in letter
    # The non-filer disclaimer must survive white-labeling — it is a legal
    # statement, not branding.
    assert "does not file" in letter


def test_letter_fta_only_still_letterheaded(app_module):
    fta = {**FINDING, "remedy": "1520d"}
    letter = app_module.generate_protest_letter(
        [fta], 1200.0, preparer_firm="Acme Customs Brokerage LLC")
    assert "Acme Customs Brokerage LLC" in letter
    assert "1520(d)" in letter


def test_letter_preparer_firm_is_sanitized(app_module):
    # Control characters / newlines cannot break the letter structure.
    letter = app_module.generate_protest_letter(
        [FINDING], 1200.0, preparer_firm="Evil\nFirm\r\x00Name   ")
    assert "Evil Firm Name" in letter
    assert "Evil\nFirm" not in letter


# ── api_key_firm: constant-time compare, unchanged behavior ────────────────

@pytest.fixture
def keyed_env(monkeypatch, app_module):
    monkeypatch.setenv(
        "TARIFFCHECK_API_KEYS", "sk-alpha:Alpha Brokers,sk-beta:Beta LLC")
    return app_module


def test_api_key_lookup_valid(keyed_env, client):
    with keyed_env.app.test_request_context(
            headers={"X-API-Key": "sk-beta"}):
        assert keyed_env.api_key_firm() == "Beta LLC"


def test_api_key_lookup_invalid(keyed_env, client):
    with keyed_env.app.test_request_context(
            headers={"X-API-Key": "sk-wrong"}):
        assert keyed_env.api_key_firm() is None


def test_api_key_lookup_uses_hmac(keyed_env):
    # Guard against regression to `==`: the module must route key comparison
    # through hmac.compare_digest.
    import inspect
    src = inspect.getsource(keyed_env.api_key_firm)
    assert "compare_digest" in src


# ── CORS origin resolution ─────────────────────────────────────────────────

def test_origins_explicit_env_wins(app_module):
    assert app_module._resolve_origins(
        "https://a.com, https://b.com", "production"
    ) == ["https://a.com", "https://b.com"]


def test_origins_production_defaults_to_prod_domain(app_module):
    # On Vercel production with no ALLOWED_ORIGINS, CORS must pin to the
    # product origin — never fall open to "*".
    origins = app_module._resolve_origins("", "production")
    assert origins != "*"
    assert "https://tariffcheck-zeta.vercel.app" in origins


def test_origins_dev_stays_open(app_module):
    assert app_module._resolve_origins("", "") == "*"
