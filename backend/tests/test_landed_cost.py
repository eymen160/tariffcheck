def test_contract_example_math(client):
    # 9403.40.9060 from China, $50,000, ocean:
    #   MFN Free → $0; Section 301 25% → $12,500;
    #   MPF 0.3464% → $173.20 (inside bounds); HMF 0.125% → $62.50
    #   total $12,735.70 → effective 25.47%
    res = client.get("/api/landed-cost?code=9403.40.9060&origin=China&value=50000&mode=ocean")
    assert res.status_code == 200
    assert "s-maxage=86400" in res.headers.get("Cache-Control", "")
    body = res.get_json()
    assert body["found"] is True
    assert body["code"] == "9403.40.90.60"
    assert body["mode"] == "ocean"
    b = body["breakdown"]
    assert b["mfn_rate"] == 0.0
    assert b["mfn_duty"] == 0.0
    assert b["mfn_rate_raw"] == "Free"
    assert b["section_301_rate"] == 25.0
    assert b["section_301_duty"] == 12500.0
    assert b["section_301_note"]
    assert b["mpf_rate"] == 0.3464
    assert b["mpf"] == 173.20
    assert b["mpf_min"] == 33.58
    assert b["mpf_max"] == 651.50
    assert b["hmf_rate"] == 0.125
    assert b["hmf"] == 62.50
    assert body["total_landed_duty"] == 12735.70
    assert body["effective_rate"] == 25.47
    assert body["fta"] is None            # China has no FTA program
    assert "disclaimer" in body


def test_mpf_clamped_to_minimum(client):
    # $1,000 * 0.3464% = $3.46 → clamps to $33.58
    res = client.get("/api/landed-cost?code=9403.40.9060&value=1000")
    assert res.get_json()["breakdown"]["mpf"] == 33.58


def test_mpf_clamped_to_maximum(client):
    # $1,000,000 * 0.3464% = $3,464 → clamps to $651.50
    res = client.get("/api/landed-cost?code=9403.40.9060&value=1000000")
    assert res.get_json()["breakdown"]["mpf"] == 651.50


def test_air_mode_has_no_hmf(client):
    res = client.get("/api/landed-cost?code=9403.40.9060&origin=China&value=50000&mode=air")
    body = res.get_json()
    assert body["mode"] == "air"
    assert body["breakdown"]["hmf"] == 0.0
    # total = 12500 + 173.20 (no HMF)
    assert body["total_landed_duty"] == 12673.20


def test_fta_block_for_korea(client):
    # 8708.99.8180 = 2.5% MFN, KORUS special rate 0%
    res = client.get("/api/landed-cost?code=8708.99.8180&origin=South Korea&value=10000")
    body = res.get_json()
    fta = body["fta"]
    assert fta is not None
    assert fta["eligible"] is True
    assert fta["name"] == "KORUS"
    assert fta["rate"] == 0.0
    assert fta["form"]
    # savings = MFN duty avoided = 2.5% * 10000 = 250
    assert fta["savings"] == 250.0
    assert round(fta["duty_with_fta"] + fta["savings"], 2) == body["total_landed_duty"]


def test_prefix_fallback_surfaces_matched_note(client):
    res = client.get("/api/landed-cost?code=9403.40&value=5000")
    body = res.get_json()
    assert body["found"] is True
    assert body["matched_note"]


def test_code_not_found_404(client):
    res = client.get("/api/landed-cost?code=9999.99.9999&value=5000")
    assert res.status_code == 404
    body = res.get_json()
    assert body["error"] == "code_not_found"
    assert body["found"] is False
    assert "message" in body


def test_invalid_params_400(client):
    for qs in ("", "code=9403.40.9060", "value=5000",
               "code=9403.40.9060&value=0", "code=9403.40.9060&value=abc",
               "code=9403.40.9060&value=-5"):
        res = client.get(f"/api/landed-cost?{qs}")
        assert res.status_code == 400
        assert res.get_json()["error"] == "invalid_params"
