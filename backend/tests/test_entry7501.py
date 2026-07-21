"""CBP Form 7501 (Entry Summary) PDF ingestion: parser + /api/analyze-batch
multipart wiring. Test PDFs are built with raw PDF syntax (no PDF-writing
dependency exists in this project) — minimal one-font text pages that
pdfplumber/pdfminer extract exactly like the machine-generated ABI output the
parser targets."""
import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from entry7501 import parse_7501, NotA7501Error, NoExtractableTextError


# ── Minimal PDF builder ─────────────────────────────────────────────────────

def _pdf_escape(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def make_pdf(pages):
    """pages: list of pages, each a list of text lines. Returns valid PDF
    bytes with one Helvetica text object per line, top-down like a printout."""
    objs = []
    n_pages = len(pages)
    font_num = 3 + 2 * n_pages
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n_pages))
    objs.append((1, b"<< /Type /Catalog /Pages 2 0 R >>"))
    objs.append((2, f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>".encode()))
    for i, lines in enumerate(pages):
        page_num = 3 + 2 * i
        content_num = page_num + 1
        objs.append((page_num, (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_num} 0 R >> >> "
            f"/Contents {content_num} 0 R >>").encode()))
        ops = ["BT", "/F1 9 Tf"]
        y = 750
        for line in lines:
            ops.append(f"1 0 0 1 40 {y} Tm ({_pdf_escape(line)}) Tj")
            y -= 13
        ops.append("ET")
        stream = "\n".join(ops).encode()
        objs.append((content_num,
                     b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream)))
    objs.append((font_num, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"))

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = {}
    for num, body in objs:
        offsets[num] = out.tell()
        out.write(b"%d 0 obj\n" % num)
        out.write(body)
        out.write(b"\nendobj\n")
    xref_pos = out.tell()
    count = len(objs) + 1
    out.write(b"xref\n0 %d\n" % count)
    out.write(b"0000000000 65535 f \n")
    for num in sorted(offsets):
        out.write(b"%010d 00000 n \n" % offsets[num])
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
              % (count, xref_pos))
    return out.getvalue()


# ── Fixture pages (modeled on ABI-software 7501 printouts) ──────────────────

PAGE1 = [
    "DEPARTMENT OF HOMELAND SECURITY",
    "U.S. Customs and Border Protection",
    "ENTRY SUMMARY",
    "1. Entry Number 2. Entry Type 3. Summary Date",
    "231-1234567-8 01 ABI/A 07/02/2026",
    "5. Port Code 6. Entry Date",
    "2704 06/28/2026",
    "10. Country of Origin CN",
    "12. Importer No.",
    "12-3456789 00",
    "27. Line No 28. Description of Merchandise 32. Entered Value 33. HTSUS Rate 34. Duty and IR Tax",
    "001 WOODEN KITCHEN CABINETS SHAKER STYLE",
    "9403.40.9060 4,500 KG 320 NO 12,000 Free 0.00",
    "002 MENS COTTON T-SHIRTS CREW NECK",
    "6109.90.1090 800 KG 2,400 DOZ 8,000 32% 2,560.00",
]

PAGE2 = [
    "ENTRY SUMMARY CONTINUATION",
    "231-1234567-8",
    "003 TRANSMISSION HOUSINGS PRECISION MACHINED",
    "003 KR 8708.99.8180 2,000 KG 100 NO 10,000 2.5% 250.00",
]


def happy_pdf():
    return make_pdf([PAGE1])


def multipage_pdf():
    return make_pdf([PAGE1, PAGE2])


def garbage_pdf():
    return make_pdf([[
        "QUARTERLY MARKETING REPORT",
        "Revenue grew 12% over Q1 to 1,450,000 total.",
        "Meeting notes 07/02/2026 attendance 14 people.",
    ]])


def scanned_style_pdf():
    # A page object with no text operators at all — what a scanned/image
    # 7501 looks like to a text extractor.
    return make_pdf([[]])


# ── Parser: happy path ──────────────────────────────────────────────────────

def test_happy_path_header():
    parsed = parse_7501(happy_pdf())
    header = parsed["header"]
    assert header["entry_no"] == "231-1234567-8"
    assert header["entry_date"] == "2026-06-28"
    assert header["importer_no"] == "12-3456789 00"
    assert header["origin"] == "CN"
    assert parsed["warnings"] == []


def test_happy_path_rows_map_to_es003_schema():
    rows = parse_7501(happy_pdf())["rows"]
    assert len(rows) == 2
    r1, r2 = rows
    assert r1 == {
        "row_id": "1", "entry_no": "231-1234567-8", "line_no": "1",
        "hts_code": "9403.40.9060",
        "description": "WOODEN KITCHEN CABINETS SHAKER STYLE",
        "origin": "CN", "declared_value": 12000.0, "duty_paid": 0.0,
        "entry_date": "2026-06-28",
    }
    assert r2["line_no"] == "2"
    assert r2["hts_code"] == "6109.90.1090"
    assert r2["declared_value"] == 8000.0
    assert r2["duty_paid"] == 2560.0
    assert r2["origin"] == "CN"  # header block 10 fallback


def test_multipage_continuation_lines_are_parsed():
    parsed = parse_7501(multipage_pdf())
    rows = parsed["rows"]
    assert [r["line_no"] for r in rows] == ["1", "2", "3"]
    r3 = rows[2]
    assert r3["hts_code"] == "8708.99.8180"
    assert r3["origin"] == "KR"  # line-level origin overrides header CN
    assert r3["description"] == "TRANSMISSION HOUSINGS PRECISION MACHINED"
    assert r3["declared_value"] == 10000.0
    assert r3["duty_paid"] == 250.0
    assert r3["entry_no"] == "231-1234567-8"


# ── Parser: honest degradation ──────────────────────────────────────────────

def test_garbage_pdf_raises_not_a_7501():
    with pytest.raises(NotA7501Error):
        parse_7501(garbage_pdf())


def test_scanned_style_pdf_raises_no_extractable_text():
    with pytest.raises(NoExtractableTextError):
        parse_7501(scanned_style_pdf())


def test_malformed_hts_codes_become_warnings_not_rows():
    pdf = make_pdf([PAGE1 + [
        "004 MYSTERY GADGETS",
        "9403.6.80 1,000 NO 5,000 Free 0.00",   # 7 digits — not a 10-digit code
    ]])
    parsed = parse_7501(pdf)
    assert len(parsed["rows"]) == 2  # the malformed line produced no row
    assert any("9403.6.80" in w and "10-digit" in w for w in parsed["warnings"])
    assert all("page 1" in w for w in parsed["warnings"])


def test_missing_entered_value_warns_but_keeps_row():
    pdf = make_pdf([PAGE1[:11] + [
        "001 WIDGETS OF UNKNOWN VALUE",
        "9403.40.9060 Free",
    ]])
    parsed = parse_7501(pdf)
    assert len(parsed["rows"]) == 1
    assert parsed["rows"][0]["declared_value"] is None
    assert any("entered value" in w for w in parsed["warnings"])


def test_missing_header_fields_warn_and_rows_still_parse():
    pdf = make_pdf([[
        "SOME MINIMAL PRINTOUT",
        "001 STAINLESS TUMBLERS",
        "7323.93.0060 900 KG 22,500 2% 450.00",
    ]])
    parsed = parse_7501(pdf)
    assert parsed["header"]["entry_no"] is None
    assert parsed["header"]["entry_date"] is None
    assert any("entry number" in w for w in parsed["warnings"])
    assert any("entry date" in w for w in parsed["warnings"])
    row = parsed["rows"][0]
    assert row["hts_code"] == "7323.93.0060"
    assert row["entry_no"] is None
    assert row["origin"] is None


# ── Endpoint integration: POST PDF to /api/analyze-batch ────────────────────

def _post_pdf(client, pdf_bytes, filename="entry7501.pdf"):
    return client.post(
        "/api/analyze-batch",
        data={"file": (io.BytesIO(pdf_bytes), filename)},
        content_type="multipart/form-data",
    )


def test_endpoint_pdf_runs_batch_audit_with_source_block(client):
    res = _post_pdf(client, multipage_pdf())
    assert res.status_code == 200
    body = res.get_json()
    assert set(body) == {"summary", "results", "source"}
    assert body["source"] == {
        "type": "7501_pdf",
        "entry_no": "231-1234567-8",
        "rows_parsed": 3,
        "warnings": [],
    }
    assert body["summary"]["rows"] == 3
    results = body["results"]
    # Row 2: cotton tees under the synthetic code — curated pattern; savings
    # from actual duty paid ($2,560) minus corrected duty at the suggested
    # code's China effective rate (16.5% MFN + 7.5% Section 301 List 4A):
    # 2560 - 0.24 * 8000 = 640.
    r2 = results[1]
    assert r2["issue"] == "possible_misclassification"
    assert r2["suggested_code"] == "6109.10.00.12"
    assert r2["estimated_savings"] == 640.0
    assert r2["entry_no"] == "231-1234567-8"
    assert r2["entry_date"] == "2026-06-28"
    # Row 3: Korea-origin at 2.5% MFN with KORUS available → missed_fta.
    r3 = results[2]
    assert r3["issue"] == "missed_fta"
    assert r3["origin_normalized"] == "south korea"


def test_endpoint_garbage_pdf_422_not_a_7501(client):
    res = _post_pdf(client, garbage_pdf())
    assert res.status_code == 422
    body = res.get_json()
    assert body["error"] == "not_a_7501"
    assert "findings" not in body and "results" not in body


def test_endpoint_scanned_pdf_422_unreadable(client):
    res = _post_pdf(client, scanned_style_pdf())
    assert res.status_code == 422
    body = res.get_json()
    assert body["error"] == "unreadable_file"
    assert "scanned" in body["message"]


def test_endpoint_non_pdf_upload_422(client):
    res = _post_pdf(client, b"entry_no,hts_code\n231-1234567-8,9403.40.9060\n",
                    filename="rows.csv")
    assert res.status_code == 422
    assert res.get_json()["error"] == "unreadable_file"


def test_endpoint_json_path_unchanged_no_source_key(client):
    res = client.post("/api/analyze-batch", json={"rows": [
        {"row_id": 1, "hts_code": "9403.40.9060", "declared_value": 1000},
    ]})
    assert res.status_code == 200
    assert set(res.get_json()) == {"summary", "results"}


def test_endpoint_pdf_over_100_lines_maps_to_too_many_rows(client):
    lines = []
    for i in range(1, 102):
        lines.append(f"{i:03d} COTTON T-SHIRTS")
        lines.append("6109.90.1090 100 KG 1,000 32% 320.00")
    res = _post_pdf(client, make_pdf([PAGE1[:11]] + [lines[i:i + 40]
                                                     for i in range(0, len(lines), 40)]))
    assert res.status_code == 400
    assert res.get_json()["error"] == "too_many_rows"
