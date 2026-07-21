"""HS 2028 readiness check (v3.4) — WCO Table II correlations."""


def test_known_full_transfer(app_module):
    # 0306.15 → 0310.53, "(All goods...)" per WCO Table II.
    r = app_module.hs2028_check_code("0306.15")
    assert r["status"] == "renumbered"
    assert r["targets"][0]["code"] == "0310.53"


def test_known_split(app_module):
    # 0302.82 splits into rays vs ray fins in HS 2028.
    r = app_module.hs2028_check_code("0302.82.0000")
    assert r["status"] == "split"
    assert len(r["targets"]) >= 2
    assert "review" in r["message"].lower()


def test_unchanged_code(app_module):
    r = app_module.hs2028_check_code("9403.40.9060")
    assert r["status"] == "unchanged"
    # Honesty note: US suffixes may still move in the 2027 USITC schedule.
    assert "USITC" in r["message"]


def test_ten_digit_normalizes_to_subheading(app_module):
    assert app_module.hs2028_check_code("0306.15.0000")["status"] == "renumbered"


def test_invalid_code(app_module):
    assert app_module.hs2028_check_code("94")["status"] == "invalid"


def test_endpoint_single(client):
    res = client.get("/api/hs2028-check?code=0306.15")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "renumbered"
    assert "2028-01-01" == body["effective"]
    assert "s-maxage" in (res.headers.get("Cache-Control") or "")


def test_endpoint_single_missing(client):
    assert client.get("/api/hs2028-check").status_code == 400


def test_endpoint_batch(client):
    res = client.post("/api/hs2028-check-batch",
                      json={"codes": ["0306.15", "9403.40.9060", "xx"]})
    assert res.status_code == 200
    s = res.get_json()["summary"]
    assert s["codes"] == 3
    assert s["renumbered"] == 1
    assert s["unchanged"] == 1
    assert s["invalid"] == 1
    assert s["action_needed"] == 1


def test_endpoint_batch_caps_at_500(client):
    res = client.post("/api/hs2028-check-batch",
                      json={"codes": ["0306.15"] * 501})
    assert res.status_code == 400
    assert res.get_json()["error"] == "too_many_codes"
