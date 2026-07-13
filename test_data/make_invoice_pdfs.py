#!/usr/bin/env python3
"""Render the CROSS-rulings dataset as realistic commercial invoice PDFs.

Reads cross_rulings_dataset.json (real CBP-ruled product descriptions + HTS
codes) and emits one PDF per origin-country group under pdf_invoices/.
Every one of the dataset's rows appears in exactly one PDF, so the PDFs
together exercise the full 240+ record set through /api/analyze.

Sellers/buyers are fictional; line items (description, HTS code) are real,
traceable to the CBP ruling number printed on each line.
"""
import json
import random
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

HERE = Path(__file__).parent
OUT = HERE / "pdf_invoices"
OUT.mkdir(exist_ok=True)

ITEMS_PER_INVOICE = 10

CITY = {
    "China": "Shenzhen, Guangdong, China",
    "Vietnam": "Ho Chi Minh City, Vietnam",
    "South Korea": "Busan, South Korea",
    "Canada": "Mississauga, ON, Canada",
    "Mexico": "Monterrey, NL, Mexico",
    "India": "Mumbai, Maharashtra, India",
    "Taiwan": "Taichung, Taiwan",
    "Germany": "Hamburg, Germany",
    "Italy": "Milan, Italy",
    "Cambodia": "Phnom Penh, Cambodia",
}
SELLER_STEM = ["Pacific", "Golden Bridge", "Summit", "Orient Star", "Blue Harbor",
               "Crescent", "Northgate", "Silverline", "Eastwind", "Meridian"]
SELLER_KIND = ["Trading Co., Ltd.", "Industrial Co., Ltd.", "Manufacturing Ltd.",
               "Exports Pvt. Ltd.", "International Corp."]
BUYERS = [
    ("Peachtree Imports LLC", "245 Peachtree Center Ave, Atlanta, GA 30303, USA"),
    ("Harborview Distribution Inc.", "1800 Bayport Blvd, Houston, TX 77058, USA"),
    ("Great Lakes Wholesale Co.", "600 W Fulton St, Chicago, IL 60661, USA"),
    ("Coastline Retail Group", "355 S Grand Ave, Los Angeles, CA 90071, USA"),
]


def money(x):
    return f"${x:,.2f}"


def main():
    rows = json.loads((HERE / "cross_rulings_dataset.json").read_text())
    rng = random.Random(2026)

    # group by origin; rows with no origin go into a mixed group
    groups = {}
    for r in rows:
        groups.setdefault(r["origin"] or "Various", []).append(r)

    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=10)
    cell = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8.5, leading=11)
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=16, spaceAfter=2)

    made, covered = 0, 0
    for origin, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        for part_no, start in enumerate(range(0, len(items), ITEMS_PER_INVOICE), 1):
            chunk = items[start:start + ITEMS_PER_INVOICE]
            seller = f"{rng.choice(SELLER_STEM)} {rng.choice(SELLER_KIND)}"
            seller_addr = CITY.get(origin, f"{origin}" if origin != "Various" else "Multiple origins")
            buyer, buyer_addr = rng.choice(BUYERS)
            inv_no = f"CI-2026-{rng.randrange(10000, 99999)}"
            slug = re.sub(r"\W+", "_", origin.lower()).strip("_")
            path = OUT / f"invoice_{slug}_{part_no}.pdf"

            doc = SimpleDocTemplate(str(path), pagesize=LETTER,
                                    leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                                    topMargin=0.6 * inch, bottomMargin=0.6 * inch)
            story = [Paragraph("COMMERCIAL INVOICE", h1), Spacer(1, 8)]

            head = Table([
                [Paragraph(f"<b>Seller / Exporter</b><br/>{seller}<br/>{seller_addr}", cell),
                 Paragraph(f"<b>Buyer / Importer of Record</b><br/>{buyer}<br/>{buyer_addr}", cell)],
                [Paragraph(f"<b>Invoice No:</b> {inv_no}<br/><b>Invoice Date:</b> July 10, 2026<br/>"
                           f"<b>Country of Origin:</b> {origin}", cell),
                 Paragraph("<b>Incoterms:</b> FOB Port of Loading<br/><b>Payment:</b> Net 30<br/>"
                           "<b>Currency:</b> USD", cell)],
            ], colWidths=[3.55 * inch, 3.55 * inch])
            head.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.75, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story += [head, Spacer(1, 12)]

            data = [["#", "Description of Goods", "HTS Code", "Qty", "Unit Price", "Amount"]]
            total = 0.0
            for j, r in enumerate(chunk, 1):
                amount = float(r["declared_value"])
                if r.get("price_real"):
                    qty_str = f"{r['qty']:,} {r['qty_unit']}"
                    unit = r["unit_price"]
                    src = "unit value: US import avg 2024"
                else:
                    qty = rng.choice([50, 100, 200, 250, 500])
                    qty_str = f"{qty:,}"
                    unit = amount / qty
                    src = "unit value: estimated"
                total += amount
                desc = r["description"][0].upper() + r["description"][1:]
                data.append([
                    str(j),
                    Paragraph(f"{desc}<br/><font size=7 color=grey>Ref. CBP ruling "
                              f"{r['ruling_number']} ({r['ruling_date']}); {src}</font>", cell),
                    r["hts_code"], qty_str, money(unit), money(amount),
                ])
                covered += 1
            data.append(["", "", "", "", "TOTAL", money(total)])

            tbl = Table(data, colWidths=[0.3 * inch, 3.05 * inch, 1.05 * inch,
                                         0.95 * inch, 0.85 * inch, 0.95 * inch],
                        repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2e4a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
                ("BOX", (0, -1), (-1, -1), 0.75, colors.black),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story += [tbl, Spacer(1, 14)]
            story.append(Paragraph(
                "We certify that this invoice is true and correct and that the goods described "
                "are of the origin stated. HTS classifications shown are as declared by the exporter. "
                "Line items reference public CBP CROSS rulings; unit prices are 2024 US import "
                "average unit values (UN Comtrade). Test data.", small))
            doc.build(story)
            made += 1
            print(f"{path.name}: {len(chunk)} items, total {money(total)}")

    print(f"\n{made} PDF invoices, {covered} line items covered (dataset has {len(rows)})")


if __name__ == "__main__":
    main()
