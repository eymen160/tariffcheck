RESULT_KEYS = {
    "row_id", "status", "current_code", "current_code_found", "description",
    "declared_value", "origin", "current_rate", "section_301_rate",
    "total_current_rate", "issue", "suggested_code", "suggested_rate",
    "total_suggested_rate", "estimated_savings", "confidence", "verified", "note",
    # ACE ES-003 / entry-summary passthrough + remedy routing (additive)
    "entry_no", "line_no", "entry_date", "liquidation_status",
    "protest_by", "protest_days_left", "protest_window_open",
    "remedy_vehicle", "spi_claimed", "duty_paid", "origin_normalized",
}

CONTRACT_ROWS = {
    "rows": [
        {"row_id": 1, "hts_code": "9403.40.9060", "description": "Wooden kitchen cabinets",
         "declared_value": 12000, "origin": "China"},
        {"row_id": 2, "hts_code": "6109.90.1090", "description": "Men's cotton t-shirts",
         "declared_value": 8000, "origin": "Vietnam"},
    ]
}


def test_contract_example_shape(client):
    res = client.post("/api/analyze-batch", json=CONTRACT_ROWS)
    assert res.status_code == 200
    body = res.get_json()
    assert set(body) == {"summary", "results"}
    summary = body["summary"]
    assert summary["rows"] == 2
    assert summary["source"] == "USITC HTS 2026 (29,755 codes)"
    assert "disclaimer" in summary
    assert isinstance(summary["flagged"], int)
    assert isinstance(summary["total_estimated_exposure"], (int, float))
    for row in body["results"]:
        assert set(row) == RESULT_KEYS
        assert row["status"] in ("flagged", "ok", "error")
        assert row["verified"] is True


def test_flagged_misclassification_row(client):
    # Cotton t-shirts declared under the synthetic code — curated pattern:
    # 6109.90 (32%) → 6109.10.0012 (16.5%); Vietnam: no 301, no FTA.
    res = client.post("/api/analyze-batch", json=CONTRACT_ROWS)
    row = res.get_json()["results"][1]
    assert row["row_id"] == 2
    assert row["status"] == "flagged"
    assert row["issue"] == "possible_misclassification"
    assert row["current_code"] == "6109.90.10.90"
    assert row["current_code_found"] is True
    assert row["total_current_rate"] == 32.0
    assert row["suggested_code"] == "6109.10.00.12"
    assert row["total_suggested_rate"] == 16.5
    # (32.0 - 16.5)/100 * 8000 = 1240.00
    assert row["estimated_savings"] == 1240.0
    assert "misclassification pattern" in row["note"]


def test_ok_row(client):
    res = client.post("/api/analyze-batch", json={"rows": [
        {"row_id": "a", "hts_code": "9403.40.9060", "description": "Wooden kitchen cabinets",
         "declared_value": 12000, "origin": "Vietnam"},
    ]})
    row = res.get_json()["results"][0]
    assert row["row_id"] == "a"
    assert row["status"] == "ok"
    assert row["issue"] is None
    assert row["suggested_code"] is None
    assert row["estimated_savings"] == 0
    assert row["confidence"] == "high"
    assert row["note"] is None


def test_missed_fta_row(client):
    # 8708.99.8180 = 2.5% MFN, KORUS special rate 0 → missed_fta for Korea.
    res = client.post("/api/analyze-batch", json={"rows": [
        {"row_id": 1, "hts_code": "8708.99.8180", "description": "Transmission housings",
         "declared_value": 10000, "origin": "South Korea"},
    ]})
    row = res.get_json()["results"][0]
    assert row["status"] == "flagged"
    assert row["issue"] == "missed_fta"
    assert row["suggested_code"] == row["current_code"]
    assert row["suggested_rate"] == 0.0
    # (2.5 - 0)/100 * 10000 = 250.00
    assert row["estimated_savings"] == 250.0
    assert "KORUS" in row["note"]


def test_code_not_found_row(client):
    res = client.post("/api/analyze-batch", json={"rows": [
        {"row_id": 1, "hts_code": "9999.99.9999", "declared_value": 5000},
    ]})
    row = res.get_json()["results"][0]
    assert row["status"] == "flagged"
    assert row["issue"] == "code_not_found"
    assert row["current_code"] == "9999.99.9999"
    assert row["current_code_found"] is False
    assert row["suggested_code"] is None
    assert row["estimated_savings"] == 0


def test_structurally_invalid_code_is_error_row(client):
    res = client.post("/api/analyze-batch", json={"rows": [
        {"row_id": 1, "hts_code": "not-a-code"},
        {"row_id": 2, "hts_code": "94"},
    ]})
    body = res.get_json()
    assert res.status_code == 200
    assert all(r["status"] == "error" for r in body["results"])
    assert body["summary"]["flagged"] == 0


def test_no_rows_400(client):
    for payload in ({}, {"rows": []}, None):
        res = client.post("/api/analyze-batch", json=payload)
        assert res.status_code == 400
        assert res.get_json()["error"] == "no_rows"


def test_too_many_rows_400(client):
    rows = [{"row_id": i, "hts_code": "9403.40.9060"} for i in range(101)]
    res = client.post("/api/analyze-batch", json={"rows": rows})
    assert res.status_code == 400
    assert res.get_json()["error"] == "too_many_rows"


def test_missing_hts_code_400(client):
    res = client.post("/api/analyze-batch", json={"rows": [
        {"row_id": 1, "hts_code": "9403.40.9060"},
        {"row_id": 2, "hts_code": "6109.90.1090"},
        {"row_id": 3, "description": "no code here"},
    ]})
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_row"
    assert body["message"] == "Row 3: hts_code is required."


def test_100_rows_succeeds(client):
    rows = [{"row_id": i, "hts_code": "6109.90.1090", "description": "cotton tees",
             "declared_value": 1000, "origin": "Vietnam"} for i in range(100)]
    res = client.post("/api/analyze-batch", json={"rows": rows})
    assert res.status_code == 200
    body = res.get_json()
    assert body["summary"]["rows"] == 100
    assert body["summary"]["flagged"] == 100
