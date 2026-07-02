import io
import json

import anthropic
import httpx
import pytest

VALID_TEXT = (
    "COMMERCIAL INVOICE\n"
    "Item: Men's cotton t-shirts, 60% cotton 40% polyester\n"
    "HTS: 6109.90.1090  Value: $10,000  Origin: Bangladesh\n"
)


def _post_text(client, text=VALID_TEXT):
    return client.post("/api/analyze", json={"text": text})


def test_short_text_400(client):
    res = _post_text(client, "short")
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "text_too_short"
    assert "message" in body
    assert "findings" not in body
    assert "total_savings" not in body


def test_no_api_key_503(client):
    res = _post_text(client)
    assert res.status_code == 503
    body = res.get_json()
    assert body["error"] == "ai_unavailable"
    assert body["demo_available"] is True
    assert "findings" not in body
    assert "total_savings" not in body


def test_garbage_pdf_422(client):
    res = client.post("/api/analyze", data={
        "file": (io.BytesIO(b"\x00\x01this is not a pdf"), "invoice.pdf"),
    }, content_type="multipart/form-data")
    assert res.status_code == 422
    body = res.get_json()
    assert body["error"] == "unreadable_file"
    assert "findings" not in body


def test_filename_hijack_is_dead(client):
    # A file named mexico_invoice.pdf must run the real pipeline (503 with no
    # key), never return mock findings.
    pdf_like = b"%PDF-1.4 garbage that extracts no text"
    res = client.post("/api/analyze", data={
        "file": (io.BytesIO(pdf_like), "mexico_invoice.pdf"),
    }, content_type="multipart/form-data")
    assert res.status_code in (422, 503)
    assert "findings" not in res.get_json()

    # Same for a .txt named like a demo: real text → real pipeline → 503
    res = client.post("/api/analyze", data={
        "file": (io.BytesIO(VALID_TEXT.encode()), "mexico_invoice.txt"),
    }, content_type="multipart/form-data")
    assert res.status_code == 503
    assert res.get_json()["error"] == "ai_unavailable"


def test_demo_id_returns_verified_mock(client):
    res = client.post("/api/analyze", json={"demo_id": "3"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["meta"]["demo"] is True
    assert "latency_ms" in body["meta"]
    assert body["verification"]["source"] == "USITC HTS 2026 (29,755 codes)"
    assert all("verified" in f for f in body["findings"])


def test_demo_id_form_field(client):
    res = client.post("/api/analyze", data={"demo_id": "1"})
    assert res.status_code == 200
    assert res.get_json()["meta"]["demo"] is True


def test_get_demo_endpoint_unchanged(client):
    res = client.get("/api/demo/2")
    assert res.status_code == 200
    body = res.get_json()
    assert body["findings"]
    assert "meta" not in body   # meta only appears on /api/analyze responses


def test_success_path_is_verified(client, app_module, monkeypatch):
    def fake_claude(invoice_text):
        return {
            "findings": [{
                "hts_code": "6109.90.1090",
                "description": "Men's cotton t-shirts",
                "current_rate": 30.0,          # wrong on purpose — server fixes
                "suggested_code": "6109.10.0012",
                "suggested_rate": 16.5,
                "declared_value": 10000,
                "savings": 9999.0,             # wrong on purpose — server fixes
                "confidence": "high",
                "explanation": "chief weight cotton",
            }],
            "total_savings": 9999.0,
            "fta_eligible": False,
            "country_of_origin": "Bangladesh",
        }

    monkeypatch.setattr(app_module, "analyze_with_claude", fake_claude)
    res = _post_text(client)
    assert res.status_code == 200
    body = res.get_json()
    f = body["findings"][0]
    assert f["verified"] is True
    assert f["current_rate"] == 32.0                  # official schedule wins
    assert f["savings"] == 1550.0
    assert f["model_claimed_savings"] == 9999.0
    assert f["confidence"] == "medium"                # wrong math caps confidence
    assert body["total_savings"] == 1550.0
    assert body["verification"]["verified_count"] == 1
    assert body["meta"]["demo"] is False
    assert body["meta"]["model"]
    assert isinstance(body["meta"]["latency_ms"], int)
    # Protest letter contains only server-recomputed numbers
    assert "$1,550.00" in body["protest_letter"]
    assert "9,999" not in body["protest_letter"]


def _http_response(status, headers=None):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return httpx.Response(status, request=request, headers=headers or {})


@pytest.mark.parametrize("exc,status,code", [
    (lambda: anthropic.APITimeoutError(request=httpx.Request("POST", "https://x")),
     504, "model_timeout"),
    (lambda: anthropic.APIStatusError("boom", response=_http_response(500), body=None),
     502, "model_error"),
])
def test_typed_anthropic_errors_map_to_statuses(client, app_module, monkeypatch, exc, status, code):
    def raiser(invoice_text):
        raise exc()
    monkeypatch.setattr(app_module, "analyze_with_claude", raiser)
    res = _post_text(client)
    assert res.status_code == status
    body = res.get_json()
    assert body["error"] == code
    assert "findings" not in body


def test_upstream_rate_limit_maps_to_429_with_retry_after(client, app_module, monkeypatch):
    def raiser(invoice_text):
        raise anthropic.RateLimitError(
            "rate limited", response=_http_response(429, {"retry-after": "7"}), body=None)
    monkeypatch.setattr(app_module, "analyze_with_claude", raiser)
    res = _post_text(client)
    assert res.status_code == 429
    assert res.get_json()["error"] == "rate_limited"
    assert res.headers["Retry-After"] == "7"


def test_model_refusal_maps_to_502(client, app_module, monkeypatch):
    def raiser(invoice_text):
        raise app_module.ModelResponseError("refused")
    monkeypatch.setattr(app_module, "analyze_with_claude", raiser)
    res = _post_text(client)
    assert res.status_code == 502
    assert res.get_json()["error"] == "model_error"


def test_rate_limit_trips_after_10_and_sets_retry_after(client, app_module):
    for i in range(app_module.RATE_LIMIT_MAX):
        res = _post_text(client)
        assert res.status_code == 503, f"request {i} unexpectedly limited"
    res = _post_text(client)
    assert res.status_code == 429
    body = res.get_json()
    assert body["error"] == "rate_limited"
    assert int(res.headers["Retry-After"]) > 0


def test_demo_id_requests_exempt_from_rate_limit(client, app_module):
    for _ in range(app_module.RATE_LIMIT_MAX + 5):
        res = client.post("/api/analyze", json={"demo_id": "1"})
        assert res.status_code == 200


def test_leads_valid_email(client, caplog):
    import logging
    with caplog.at_level(logging.INFO):
        res = client.post("/api/leads", json={
            "email": "broker@firm.com", "source": "brokers_page", "context": "50 invoices/mo",
        })
    assert res.status_code == 200
    body = res.get_json()
    assert body["ok"] is True
    assert "message" in body
    assert "lead.captured" in caplog.text
    assert "broker@firm.com" in caplog.text


@pytest.mark.parametrize("email", ["", "garbage", "a@b", "no at sign.com", "a b@c.com"])
def test_leads_invalid_email_400(client, email):
    res = client.post("/api/leads", json={"email": email})
    assert res.status_code == 400
    assert res.get_json()["error"] == "invalid_email"
