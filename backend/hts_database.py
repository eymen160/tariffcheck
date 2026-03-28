HTS_RATES = {
    "9403.10": {"description": "Metal furniture of a kind used in offices", "general_rate": 0.0},
    "9403.20": {"description": "Other metal furniture", "general_rate": 0.0},
    "9403.30": {"description": "Wooden furniture, office kind", "general_rate": 0.0},
    "9403.50": {"description": "Wooden furniture, bedroom", "general_rate": 4.0},
    "9403.60": {"description": "Other wooden furniture", "general_rate": 0.0},
    "9403.90": {"description": "Furniture, other (general)", "general_rate": 5.3},
    "8471.30": {"description": "Portable computers (laptops)", "general_rate": 0.0},
    "8471.41": {"description": "Other automatic data processing machines", "general_rate": 0.0},
    "8471.49": {"description": "Other computers", "general_rate": 0.0},
    "8517.12": {"description": "Smartphones, cellular network telephones", "general_rate": 0.0},
    "8528.72": {"description": "Color TV reception apparatus", "general_rate": 0.0},
    "8516.50": {"description": "Microwave ovens", "general_rate": 2.0},
    "8415.10": {"description": "Air conditioning machines", "general_rate": 0.0},
    "6109.10": {"description": "T-shirts, singlets, knitted cotton", "general_rate": 16.5},
    "6109.90": {"description": "T-shirts, singlets, other textiles", "general_rate": 32.0},
    "6110.20": {"description": "Jerseys, pullovers, cotton knitted", "general_rate": 16.5},
    "6110.30": {"description": "Jerseys, pullovers, man-made fibres", "general_rate": 32.0},
    "6204.62": {"description": "Women's trousers, cotton", "general_rate": 16.6},
    "6204.69": {"description": "Women's trousers, other textiles", "general_rate": 28.6},
    "6203.42": {"description": "Men's trousers, cotton", "general_rate": 16.6},
    "6404.11": {"description": "Sports footwear, outer sole rubber", "general_rate": 20.0},
    "6403.99": {"description": "Footwear, outer sole rubber, upper leather", "general_rate": 10.0},
    "4202.92": {"description": "Trunks, handbags, other materials", "general_rate": 17.6},
    "4202.12": {"description": "Trunks, suitcases, leather outer surface", "general_rate": 20.0},
    "9503.00": {"description": "Toys, puzzles, scale models", "general_rate": 0.0},
    "8708.29": {"description": "Parts for motor vehicles", "general_rate": 2.5},
    "3004.90": {"description": "Medicaments for therapeutic use, other", "general_rate": 0.0},
    "9401.71": {"description": "Seats with metal frames, upholstered", "general_rate": 0.0},
    "9401.79": {"description": "Other seats with metal frames", "general_rate": 0.0},
    "7318.15": {"description": "Screws and bolts, iron or steel", "general_rate": 8.6},
    "8501.10": {"description": "Motors, output not exceeding 37.5W", "general_rate": 6.7},
    "8544.42": {"description": "Electric conductors, fitted connectors", "general_rate": 2.6},
    "3926.90": {"description": "Articles of plastics, other", "general_rate": 5.3},
    "0901.11": {"description": "Coffee, not roasted", "general_rate": 0.0},
    "1806.90": {"description": "Chocolate and cocoa food preparations", "general_rate": 6.0},
    "2204.21": {"description": "Wine of fresh grapes", "general_rate": 6.3},
    "8704.31": {"description": "Motor vehicles for goods, petrol, GVW not over 5t", "general_rate": 25.0},
    "9018.90": {"description": "Medical instruments and appliances", "general_rate": 0.0},
    "7601.10": {"description": "Aluminium, not alloyed", "general_rate": 0.0},
    "7606.12": {"description": "Aluminium plates, sheets, alloy", "general_rate": 3.0},
    "7408.11": {"description": "Copper wire, refined copper", "general_rate": 0.0},
    "5209.11": {"description": "Woven fabrics of cotton, denim", "general_rate": 8.1},
    "2710.12": {"description": "Light petroleum oils", "general_rate": 5.25},
    "9506.62": {"description": "Inflatable balls", "general_rate": 4.9},
    "9506.91": {"description": "Articles for gymnastics or athletics", "general_rate": 4.6},
    "8542.31": {"description": "Electronic integrated circuits, processors", "general_rate": 0.0},
    "8532.22": {"description": "Aluminum electrolytic capacitors", "general_rate": 0.0},
    "4819.10": {"description": "Cartons, boxes of corrugated paper", "general_rate": 0.0},
    "9021.10": {"description": "Orthopaedic appliances", "general_rate": 0.0},
    "6305.33": {"description": "Sacks and bags, polyethylene", "general_rate": 6.4},
}

FTA_COUNTRIES = {
    "canada": "USMCA",
    "mexico": "USMCA",
    "south korea": "KORUS",
    "korea": "KORUS",
    "australia": "US-Australia FTA",
    "chile": "US-Chile FTA",
    "singapore": "US-Singapore FTA",
    "israel": "US-Israel FTA",
    "jordan": "US-Jordan FTA",
    "morocco": "US-Morocco FTA",
    "colombia": "US-Colombia FTA",
    "peru": "US-Peru FTA",
    "panama": "US-Panama FTA",
    "oman": "US-Oman FTA",
}

COMMON_MISCLASSIFICATIONS = {
    "9403.90": {
        "if_contains": "metal",
        "suggest": "9403.10",
        "reason": "Metal office furniture → 9403.10 at 0% vs 9403.90 at 5.3%"
    },
    "6109.90": {
        "if_contains": "cotton",
        "suggest": "6109.10",
        "reason": "Cotton knit shirts → 6109.10 at 16.5% vs 6109.90 at 32%"
    },
    "6204.69": {
        "if_contains": "cotton",
        "suggest": "6204.62",
        "reason": "Cotton women's trousers → 6204.62 at 16.6% vs 6204.69 at 28.6%"
    },
}


def lookup_hts(code):
    """Look up HTS code in database, try partial matches."""
    if not code:
        return None
    clean = str(code).strip().replace(" ", "")
    if clean in HTS_RATES:
        return HTS_RATES[clean]
    # Try 6-digit prefix
    prefix6 = clean[:6] if len(clean) >= 6 else clean
    for key in HTS_RATES:
        if key.startswith(prefix6[:4]):
            return HTS_RATES[key]
    return None


def check_fta(country_of_origin):
    """Check if country qualifies for FTA treatment. Returns (fta_name, rate)."""
    if not country_of_origin:
        return None, None
    country_lower = str(country_of_origin).lower().strip()
    for country, fta in FTA_COUNTRIES.items():
        if country in country_lower:
            return fta, 0.0
    return None, None


def get_misclassification_hint(hts_code, description=""):
    """Check if a common misclassification pattern applies."""
    code_prefix = str(hts_code)[:7] if hts_code else ""
    for code, pattern in COMMON_MISCLASSIFICATIONS.items():
        if code_prefix.startswith(code[:6]):
            if pattern["if_contains"] in description.lower():
                return pattern["suggest"], pattern["reason"]
    return None, None
