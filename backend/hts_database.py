# TariffCheck HTS Database v2.0
# Sources: USITC HTS 2026 Rev2, CBP Rulings, USTR Section 301 Lists
# Last verified: May 2026

# ─────────────────────────────────────────────
# CHAPTER 94 — FURNITURE (Cabinet/Closet Importers)
# Most critical chapter for cabinet importers from Vietnam & China
# ─────────────────────────────────────────────
# KEY CLASSIFICATION RULES FOR CHAPTER 94:
# 9403.40 = Kitchen furniture (permanently installed cabinets, kitchen sets)
# 9403.50 = Bedroom furniture (dressers, nightstands, bedroom wardrobes)
# 9403.60 = Other wooden furniture (living room, dining, bookcases, media)
# 9403.89 = Other wooden furniture NEC (closet organizers, wardrobes, pantry)
# 9403.90 = Parts of furniture (drawer slides, cabinet doors sold separately)
# COMMON MISTAKE: Brokers use 9403.60 or 9403.90 as catch-all for everything

HTS_RATES = {

    # KITCHEN CABINETS & VANITIES
    "9403.40.9060": {
        "description": "Kitchen cabinets and bathroom vanities, wooden, for permanent installation",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "notes": "Correct code for RTA kitchen cabinets, bathroom vanities. Vietnam: 0%. China: 25% Section 301 List 3.",
        "chapter": "94"
    },
    "9403.40.9080": {
        "description": "Other wooden furniture of a kind used in kitchens (modular/freestanding)",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "notes": "Freestanding kitchen furniture. Vietnam: 0%. China: +25% Section 301.",
        "chapter": "94"
    },

    # BEDROOM FURNITURE
    "9403.50.9042": {
        "description": "Bedroom wardrobes and armoires, wooden, with one or more doors",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "notes": "Wardrobes/armoires for bedroom use. Distinguished from closet organizers.",
        "chapter": "94"
    },
    "9403.50.9045": {
        "description": "Bedroom dressers, chests of drawers, wooden",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "chapter": "94"
    },
    "9403.50.9080": {
        "description": "Other wooden bedroom furniture (nightstands, headboards, bedroom sets)",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "chapter": "94"
    },

    # CLOSET ORGANIZERS & STORAGE SYSTEMS
    "9403.89.6010": {
        "description": "Closet organizers and wardrobe systems, wooden, freestanding or modular",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "notes": "CRITICAL: Freestanding closet systems go here, NOT 9403.50. Common misclassification.",
        "chapter": "94"
    },
    "9403.89.6020": {
        "description": "Wooden storage shelving units, modular closet systems, pantry organizers",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "chapter": "94"
    },
    "9403.20.0015": {
        "description": "Metal closet organizers and shelving systems (wire/steel closet systems)",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "notes": "Metal closet organizers — Chapter 94 metal furniture, NOT Chapter 83 hardware.",
        "chapter": "94"
    },

    # LIVING/DINING/OTHER WOODEN FURNITURE
    "9403.60.8040": {
        "description": "Other wooden furniture: media consoles, TV stands, entertainment centers",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "chapter": "94"
    },
    "9403.60.8080": {
        "description": "Other wooden furniture: bathroom vanity (without sink), bookcases, shelving",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "notes": "CBP Ruling N024951: Bathroom vanity sets (wooden) go here. Rate: Free + Section 301 if China.",
        "chapter": "94"
    },
    "9403.60.8093": {
        "description": "Other wooden furniture: dining tables, coffee tables, side tables",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "chapter": "94"
    },

    # METAL FURNITURE
    "9403.10.0000": {
        "description": "Metal office furniture: desks, workstations, filing cabinets",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "chapter": "94"
    },
    "9403.20.0030": {
        "description": "Other metal furniture: metal bookcases, shelving units, racking",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "chapter": "94"
    },

    # FURNITURE PARTS (very commonly misclassified)
    "9403.90.7080": {
        "description": "Furniture parts of metal: drawer slides, hinges sold as furniture parts",
        "general_rate": 3.7,
        "section_301_china": 25.0,
        "notes": "Parts must be identifiable as furniture parts. Generic hardware goes to Ch.83.",
        "chapter": "94"
    },
    "9403.90.8041": {
        "description": "Furniture parts of wood: cabinet doors, drawer fronts, face frames",
        "general_rate": 4.3,
        "section_301_china": 25.0,
        "notes": "CBP Ruling HQ954220: Cabinet doors/drawer fronts/faceframes = 9403.90 parts.",
        "chapter": "94"
    },
    "9403.91.0080": {
        "description": "Parts of furniture (other materials): plastic furniture components",
        "general_rate": 3.8,
        "section_301_china": 25.0,
        "chapter": "94"
    },

    # SEATING
    "9401.61.0010": {
        "description": "Upholstered seats with wooden frames: sofas, sectionals, loveseats",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "chapter": "94"
    },
    "9401.69.6010": {
        "description": "Other seats with wooden frames: dining chairs, accent chairs",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "chapter": "94"
    },
    "9401.71.0010": {
        "description": "Seats with metal frames, upholstered: office chairs, metal-frame sofas",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "chapter": "94"
    },
    "9401.79.0045": {
        "description": "Other seats with metal frames: metal dining chairs, barstools",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "chapter": "94"
    },

    # ─────────────────────────────────────────────
    # CHAPTER 68 — STONE, MARBLE, GRANITE, TRAVERTINE
    # Critical for countertop/flooring importers
    # ─────────────────────────────────────────────
    # CLASSIFICATION RULES:
    # 6802.21 = Marble/travertine/alabaster, simply cut/sawn, flat surface (slabs unpolished)
    # 6802.91 = Marble/travertine/alabaster, further worked (polished countertops, finished)
    # 6802.23 = Granite, simply cut/sawn
    # 6802.93 = Granite, further worked (polished)
    # 6802.29 = Other calcareous stone (limestone, etc.)
    # 6810 = Articles of cement/concrete (NOT natural stone)
    # COMMON MISTAKE: Polished marble countertops under 6802.21 instead of 6802.91

    "6802.21.1000": {
        "description": "Travertine, simply cut or sawn with flat/even surface (raw slabs, unpolished)",
        "general_rate": 4.2,
        "section_301_china": 0.0,
        "notes": "Unpolished travertine slabs. If polished/finished → 6802.91. Vietnam/China: no Section 301 on stone.",
        "chapter": "68"
    },
    "6802.21.5000": {
        "description": "Marble and alabaster, simply cut or sawn, flat surface (unpolished slabs)",
        "general_rate": 1.9,
        "section_301_china": 0.0,
        "notes": "Raw/unpolished marble slabs. Polished countertops → 6802.91.0500.",
        "chapter": "68"
    },
    "6802.91.0500": {
        "description": "Marble, travertine, alabaster — further worked/polished (countertops, finished tile, mantels)",
        "general_rate": 4.9,
        "section_301_china": 0.0,
        "notes": "MOST COMMON for polished marble countertops. Higher rate than 6802.21. Common to misuse 6802.21 for finished product.",
        "chapter": "68"
    },
    "6802.91.2500": {
        "description": "Travertine, further worked — polished countertops, floor tiles over 7cm",
        "general_rate": 4.2,
        "section_301_china": 0.0,
        "chapter": "68"
    },
    "6802.23.0000": {
        "description": "Granite, simply cut or sawn with flat/even surface (granite slabs, raw)",
        "general_rate": 3.7,
        "section_301_china": 0.0,
        "chapter": "68"
    },
    "6802.93.0010": {
        "description": "Granite, further worked — polished granite countertops, finished granite",
        "general_rate": 3.7,
        "section_301_china": 0.0,
        "notes": "Polished granite countertops. No Section 301 on granite from China.",
        "chapter": "68"
    },
    "6802.93.0020": {
        "description": "Granite, cut to size, one or more faces worked, thickness over 1.5cm",
        "general_rate": 3.7,
        "section_301_china": 0.0,
        "chapter": "68"
    },
    "6802.29.0000": {
        "description": "Other calcareous stone: limestone slabs, alabaster, other building stone",
        "general_rate": 6.0,
        "section_301_china": 0.0,
        "chapter": "68"
    },
    "6802.10.0000": {
        "description": "Stone tiles, cubes, mosaic — largest surface fits in square under 7cm",
        "general_rate": 4.9,
        "section_301_china": 0.0,
        "notes": "Small mosaic tiles. Larger finished tiles → 6802.91.",
        "chapter": "68"
    },
    "6810.11.0010": {
        "description": "Concrete/cement tiles for flooring (NOT natural stone — common confusion)",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "notes": "Cement/concrete tiles misclassified as stone tiles. Different chapter entirely.",
        "chapter": "68"
    },

    # ─────────────────────────────────────────────
    # CHAPTER 61/62 — APPAREL (T-shirt/E-commerce)
    # ─────────────────────────────────────────────
    # CLASSIFICATION RULES:
    # Chief weight determines classification: >50% cotton → cotton code (lower rate)
    # 6109.10 = Cotton knit t-shirts (16.5%) vs 6109.90 = Other/synthetic (32%)
    # BIGGEST SAVINGS OPPORTUNITY: polyester-blend shirts misclassified as synthetic

    "6109.10.0012": {
        "description": "Men's/boys' cotton t-shirts and undershirts, knitted (chief weight cotton)",
        "general_rate": 16.5,
        "section_301_china": 7.5,
        "notes": "If fabric is >50% cotton by weight → this code. Common error: using 6109.90 for blends.",
        "chapter": "61"
    },
    "6109.10.0045": {
        "description": "Women's/girls' cotton t-shirts, tank tops, knitted (chief weight cotton)",
        "general_rate": 16.5,
        "section_301_china": 7.5,
        "chapter": "61"
    },
    "6109.90.1007": {
        "description": "T-shirts of man-made fibers (polyester, nylon — chief weight synthetic)",
        "general_rate": 32.0,
        "section_301_china": 7.5,
        "notes": "Only use if truly >50% synthetic. Cotton blends often misput here — huge overpayment.",
        "chapter": "61"
    },
    "6110.20.2079": {
        "description": "Cotton sweatshirts, hoodies, pullovers, knitted (chief weight cotton)",
        "general_rate": 16.5,
        "section_301_china": 7.5,
        "chapter": "61"
    },
    "6110.30.3059": {
        "description": "Polyester/synthetic sweatshirts, hoodies, pullovers, knitted",
        "general_rate": 28.2,
        "section_301_china": 7.5,
        "chapter": "61"
    },
    "6203.42.4011": {
        "description": "Men's cotton trousers, jeans, shorts, woven",
        "general_rate": 16.6,
        "section_301_china": 7.5,
        "chapter": "62"
    },
    "6204.62.4021": {
        "description": "Women's cotton trousers, jeans, capris, woven",
        "general_rate": 16.6,
        "section_301_china": 7.5,
        "chapter": "62"
    },
    "6211.33.0090": {
        "description": "Men's polyester athletic/performance wear, track suits, joggers",
        "general_rate": 16.0,
        "section_301_china": 7.5,
        "chapter": "62"
    },
    "6211.43.0090": {
        "description": "Women's polyester athletic wear, yoga pants, leggings",
        "general_rate": 16.0,
        "section_301_china": 7.5,
        "chapter": "62"
    },
    "6505.00.6090": {
        "description": "Baseball caps, trucker hats, knitted or woven",
        "general_rate": 6.8,
        "section_301_china": 7.5,
        "notes": "Caps from China: 6.8% + 7.5% Section 301 = 14.3% total.",
        "chapter": "65"
    },

    # ─────────────────────────────────────────────
    # CHAPTER 73/96 — TUMBLERS & DRINKWARE
    # ─────────────────────────────────────────────
    # CLASSIFICATION RULES:
    # 7323.93 = Stainless steel household articles (most stainless tumblers) — 2%
    # 9617.00 = Vacuum insulated bottles/flasks — 7.2% (higher but more specific)
    # COMMON MISTAKE: All insulated tumblers put under 9617 when 7323.93 is correct
    # KEY TEST: Does it have a vacuum insulation layer? If yes → consider 9617.
    # But: CBP rulings show most "tumblers" stay in 7323.93

    "7323.93.0060": {
        "description": "Stainless steel tumblers, cups, mugs, household kitchenware (non-vacuum or single-wall)",
        "general_rate": 2.0,
        "section_301_china": 25.0,
        "notes": "Most powder-coated stainless tumblers. China: 2% + 25% = 27% total. Often misclassified as 9617.",
        "chapter": "73"
    },
    "7323.99.9080": {
        "description": "Other household articles of iron/steel: steel water bottles, steel containers (non-stainless)",
        "general_rate": 3.4,
        "section_301_china": 25.0,
        "notes": "Common catch-all. Often 7323.93 is more accurate for stainless items.",
        "chapter": "73"
    },
    "9617.00.1000": {
        "description": "Vacuum flasks with glass inners (traditional thermos with glass liner)",
        "general_rate": 7.2,
        "section_301_china": 0.0,
        "notes": "Glass-lined vacuum flasks only. Most modern stainless tumblers do NOT go here.",
        "chapter": "96"
    },
    "9617.00.9000": {
        "description": "Other vacuum insulated containers and flasks (stainless double-wall vacuum)",
        "general_rate": 7.2,
        "section_301_china": 0.0,
        "notes": "True vacuum-insulated double-wall flasks. ONLY if vacuum-sealed. Rate HIGHER than 7323.93 — misclassifying here = overpayment.",
        "chapter": "96"
    },

    # ─────────────────────────────────────────────
    # CHAPTER 83 — HARDWARE & CABINET HARDWARE
    # ─────────────────────────────────────────────
    "8302.10.3000": {
        "description": "Cabinet hinges, butt hinges, base metal (sold separately as hardware)",
        "general_rate": 5.7,
        "section_301_china": 25.0,
        "notes": "Hinges sold as hardware. If shipped as furniture parts → 9403.90.",
        "chapter": "83"
    },
    "8302.41.6080": {
        "description": "Cabinet pulls, knobs, handles, base metal mountings for furniture",
        "general_rate": 3.0,
        "section_301_china": 25.0,
        "chapter": "83"
    },
    "8302.42.3015": {
        "description": "Door closers and soft-close mechanisms for cabinets",
        "general_rate": 3.5,
        "section_301_china": 25.0,
        "chapter": "83"
    },
    "8302.49.6055": {
        "description": "Drawer slides, runners, glides for furniture/cabinets",
        "general_rate": 3.9,
        "section_301_china": 25.0,
        "notes": "If sold with cabinets as parts → 9403.90.7080. If sold separately → 8302.",
        "chapter": "83"
    },

    # ─────────────────────────────────────────────
    # CHAPTER 44 — WOOD PRODUCTS (Cabinet components)
    # ─────────────────────────────────────────────
    "4418.99.9095": {
        "description": "Builders' woodwork: cabinet door panels, wooden cabinet components for installation",
        "general_rate": 3.2,
        "section_301_china": 25.0,
        "notes": "CBP Ruling HQ954220: Cabinet doors/drawer fronts built into walls → 4418, not 9403.",
        "chapter": "44"
    },
    "4418.20.8000": {
        "description": "Wooden doors for cabinet use (hollow or non-hollow)",
        "general_rate": 4.8,
        "section_301_china": 25.0,
        "chapter": "44"
    },
    "4412.31.0560": {
        "description": "Plywood with tropical wood face ply (cabinet box material)",
        "general_rate": 8.0,
        "section_301_china": 25.0,
        "chapter": "44"
    },
    "4412.33.5765": {
        "description": "Other plywood, hardwood face (birch/maple ply for cabinet boxes)",
        "general_rate": 8.0,
        "section_301_china": 25.0,
        "chapter": "44"
    },

    # ─────────────────────────────────────────────
    # CHAPTER 39 — PLASTICS
    # ─────────────────────────────────────────────
    "3924.10.4000": {
        "description": "Plastic tableware, kitchenware, household articles",
        "general_rate": 3.4,
        "section_301_china": 7.5,
        "chapter": "39"
    },
    "3926.90.9990": {
        "description": "Other plastic articles NEC (catch-all)",
        "general_rate": 5.3,
        "section_301_china": 7.5,
        "chapter": "39"
    },
    "3923.10.0000": {
        "description": "Plastic boxes, cases, crates for packaging",
        "general_rate": 3.0,
        "section_301_china": 7.5,
        "chapter": "39"
    },

    # ─────────────────────────────────────────────
    # CHAPTER 42 — BAGS & ACCESSORIES
    # ─────────────────────────────────────────────
    "4202.92.3031": {
        "description": "Backpacks, knapsacks, textile outer surface",
        "general_rate": 17.6,
        "section_301_china": 7.5,
        "chapter": "42"
    },
    "4202.92.9026": {
        "description": "Tote bags, pouches, textile outer surface",
        "general_rate": 17.6,
        "section_301_china": 7.5,
        "chapter": "42"
    },
    "4202.12.2020": {
        "description": "Suitcases, travel bags, plastic/textile outer surface",
        "general_rate": 20.0,
        "section_301_china": 7.5,
        "chapter": "42"
    },

    # ─────────────────────────────────────────────
    # CHAPTER 84/85 — ELECTRONICS
    # ─────────────────────────────────────────────
    "8471.30.0100": {
        "description": "Laptops and portable computers",
        "general_rate": 0.0,
        "section_301_china": 0.0,
        "notes": "Exempted from Section 301.",
        "chapter": "84"
    },
    "8517.12.0000": {
        "description": "Smartphones and mobile phones",
        "general_rate": 0.0,
        "section_301_china": 0.0,
        "chapter": "85"
    },
    "8543.70.9860": {
        "description": "Other electrical machines NEC",
        "general_rate": 0.0,
        "section_301_china": 0.0,
        "chapter": "85"
    },

    # ─────────────────────────────────────────────
    # FOOTWEAR (Chapter 64)
    # ─────────────────────────────────────────────
    "6404.11.2060": {
        "description": "Sports footwear, rubber/plastic outer sole, textile upper",
        "general_rate": 20.0,
        "section_301_china": 7.5,
        "chapter": "64"
    },
    "6404.19.3560": {
        "description": "Other footwear, rubber outer sole, textile upper (non-sport)",
        "general_rate": 37.5,
        "section_301_china": 7.5,
        "chapter": "64"
    },
    "6403.99.6050": {
        "description": "Footwear with leather upper, rubber/plastic outer sole",
        "general_rate": 10.0,
        "section_301_china": 7.5,
        "chapter": "64"
    },

    # ─────────────────────────────────────────────
    # AUTO PARTS (Chapter 87)
    # ─────────────────────────────────────────────
    "8708.99.8180": {
        "description": "Other parts for motor vehicles: transmission housings, cast parts",
        "general_rate": 2.5,
        "section_301_china": 25.0,
        "chapter": "87"
    },
    "8483.40.5000": {
        "description": "Gear boxes and speed reducers for automotive",
        "general_rate": 2.8,
        "section_301_china": 25.0,
        "chapter": "87"
    },

    # ─────────────────────────────────────────────
    # MISCELLANEOUS
    # ─────────────────────────────────────────────
    "7318.15.2095": {
        "description": "Screws and bolts, iron or steel",
        "general_rate": 8.6,
        "section_301_china": 25.0,
        "chapter": "73"
    },
    "9018.90.8000": {
        "description": "Medical instruments and appliances NEC",
        "general_rate": 0.0,
        "section_301_china": 0.0,
        "chapter": "90"
    },
    "8419.89.1000": {
        "description": "Industrial machinery for processing by temperature change (roasters, dryers)",
        "general_rate": 4.5,
        "section_301_china": 25.0,
        "chapter": "84"
    },
    "8479.89.9499": {
        "description": "Other machines for specific industrial uses (pharmaceutical processing)",
        "general_rate": 0.0,
        "section_301_china": 25.0,
        "chapter": "84"
    },
}

# ─────────────────────────────────────────────
# SECTION 301 CHINA TARIFF RATES BY CHAPTER
# Source: USTR Lists 1-4A, verified January 2026
# ─────────────────────────────────────────────
# List 3 (25%): Furniture (94), steel/hardware (73,83), wood (44), stone (no)
# List 4A (7.5%): Apparel (61,62,63,65), plastics (39), bags (42), footwear (64)
# Exempted: Electronics (84,85 most), pharmaceuticals, natural stone (68)

SECTION_301_BY_CHAPTER = {
    "94": 25.0,   # Furniture — List 3
    "44": 25.0,   # Wood products — List 3
    "73": 25.0,   # Steel articles (tumblers) — List 3
    "83": 25.0,   # Hardware — List 3
    "87": 25.0,   # Auto parts — List 3
    "72": 25.0,   # Iron/steel — List 3
    "61": 7.5,    # Knit apparel — List 4A
    "62": 7.5,    # Woven apparel — List 4A
    "63": 7.5,    # Textile articles — List 4A
    "65": 7.5,    # Headwear — List 4A
    "64": 7.5,    # Footwear — List 4A
    "42": 7.5,    # Bags/luggage — List 4A
    "39": 7.5,    # Plastics — List 4A
    "68": 0.0,    # Natural stone — NOT on Section 301 lists
    "84": 0.0,    # Most computers/machinery — largely exempted
    "85": 0.0,    # Most electronics — largely exempted
    "90": 0.0,    # Medical instruments — exempted
    "96": 0.0,    # Vacuum flasks (Ch.96) — not on 301 lists
}

# ─────────────────────────────────────────────
# FTA COUNTRIES
# ─────────────────────────────────────────────
FTA_COUNTRIES = {
    "canada": {"name": "USMCA", "form": "CBP Form 434", "rate": 0.0},
    "mexico": {"name": "USMCA", "form": "CBP Form 434", "rate": 0.0},
    "south korea": {"name": "KORUS", "form": "CBP Form 3461 with KORUS cert", "rate": 0.0},
    "korea": {"name": "KORUS", "form": "CBP Form 3461 with KORUS cert", "rate": 0.0},
    "australia": {"name": "US-Australia FTA", "form": "Importer certification", "rate": 0.0},
    "chile": {"name": "US-Chile FTA", "form": "Importer certification", "rate": 0.0},
    "singapore": {"name": "US-Singapore FTA", "form": "Importer certification", "rate": 0.0},
    "israel": {"name": "US-Israel FTA", "form": "Form A or importer cert", "rate": 0.0},
    "jordan": {"name": "US-Jordan FTA", "form": "Importer certification", "rate": 0.0},
    "morocco": {"name": "US-Morocco FTA", "form": "Importer certification", "rate": 0.0},
    "colombia": {"name": "US-Colombia CTPA", "form": "Importer certification", "rate": 0.0},
    "peru": {"name": "US-Peru FTA", "form": "Importer certification", "rate": 0.0},
    "panama": {"name": "US-Panama FTA", "form": "Importer certification", "rate": 0.0},
    "oman": {"name": "US-Oman FTA", "form": "Importer certification", "rate": 0.0},
    "bahrain": {"name": "US-Bahrain FTA", "form": "Importer certification", "rate": 0.0},
    "el salvador": {"name": "CAFTA-DR", "form": "Importer certification", "rate": 0.0},
    "guatemala": {"name": "CAFTA-DR", "form": "Importer certification", "rate": 0.0},
    "honduras": {"name": "CAFTA-DR", "form": "Importer certification", "rate": 0.0},
    "nicaragua": {"name": "CAFTA-DR", "form": "Importer certification", "rate": 0.0},
    "costa rica": {"name": "CAFTA-DR", "form": "Importer certification", "rate": 0.0},
    "dominican republic": {"name": "CAFTA-DR", "form": "Importer certification", "rate": 0.0},
}

# Countries with NO FTA (important to flag explicitly)
NON_FTA_COUNTRIES = {
    "vietnam": "No US FTA. No Section 301. Only base MFN rate applies.",
    "china": "No FTA. Section 301 tariffs apply (25% List 3, 7.5% List 4A).",
    "bangladesh": "No FTA. No Section 301. Only base MFN rate applies.",
    "india": "No FTA. No Section 301 (most products). Only base MFN rate.",
    "indonesia": "No FTA. No Section 301. Only base MFN rate applies.",
    "taiwan": "No FTA. No Section 301 (Taiwan is NOT China for tariff purposes).",
    "thailand": "No FTA. No Section 301. Only base MFN rate applies.",
    "malaysia": "No FTA. No Section 301. Only base MFN rate applies.",
}

# ─────────────────────────────────────────────
# COMMON MISCLASSIFICATION PATTERNS
# Research-backed, based on CBP rulings and broker errors
# ─────────────────────────────────────────────
COMMON_MISCLASSIFICATIONS = {
    # FURNITURE MISCLASSIFICATIONS
    "9403.60.8080": {
        "if_contains": ["kitchen", "cabinet", "vanity", "kitchen cabinet"],
        "suggest": "9403.40.9060",
        "reason": "Kitchen cabinets and bathroom vanities have specific code 9403.40.9060, not general 9403.60",
        "savings_direction": "classification_risk"
    },
    "9403.60.8040": {
        "if_contains": ["kitchen", "cabinet"],
        "suggest": "9403.40.9060",
        "reason": "Kitchen cabinets → 9403.40.9060 is the specific code per CBP rulings",
        "savings_direction": "classification_risk"
    },
    "9403.90.8040": {
        "if_contains": ["metal", "office", "steel"],
        "suggest": "9403.10.0000",
        "reason": "Metal office furniture → 9403.10.0000 at 0% is more specific than 9403.90 catch-all",
        "savings_direction": "savings"
    },
    "9403.89.6020": {
        "if_contains": ["closet", "wardrobe", "bedroom"],
        "suggest": "9403.50.9042",
        "reason": "Bedroom wardrobes/armoires → 9403.50, not 9403.89 general storage",
        "savings_direction": "classification_risk"
    },
    # STONE MISCLASSIFICATIONS
    "6802.21.5000": {
        "if_contains": ["polished", "countertop", "finished", "honed"],
        "suggest": "6802.91.0500",
        "reason": "Polished/finished marble → 6802.91 (further worked), not 6802.21 (simply cut). Different rate.",
        "savings_direction": "savings"
    },
    "9617.00.9000": {
        "if_contains": ["tumbler", "cup", "mug", "stainless"],
        "suggest": "7323.93.0060",
        "reason": "Most stainless tumblers → 7323.93 at 2%, not 9617 vacuum flask at 7.2%. Overpayment of 5.2%.",
        "savings_direction": "savings"
    },
    # APPAREL MISCLASSIFICATIONS
    "6109.90.1007": {
        "if_contains": ["cotton", "60% cotton", "chief weight cotton"],
        "suggest": "6109.10.0012",
        "reason": "Cotton chief weight (>50% cotton) t-shirts → 6109.10 at 16.5%, not 6109.90 at 32%",
        "savings_direction": "savings"
    },
}


def lookup_hts(code):
    """Look up HTS code. Try exact match, then 7-digit, then 6-digit prefix."""
    if not code:
        return None
    clean = str(code).strip().replace(" ", "").replace("-", "")
    if clean in HTS_RATES:
        return {**HTS_RATES[clean], "code": clean}
    for length in [9, 7, 6, 4]:
        prefix = clean[:length]
        for key, val in HTS_RATES.items():
            if key.replace(".", "").startswith(prefix.replace(".", "")):
                return {**val, "code": key, "note": f"Matched from prefix {prefix}"}
    return None


def get_section_301_rate(hts_code, country_of_origin):
    """Get Section 301 rate for China-origin goods."""
    if not country_of_origin or "china" not in str(country_of_origin).lower():
        return 0.0
    if not hts_code:
        return 0.0
    code_data = lookup_hts(hts_code)
    if code_data and "section_301_china" in code_data:
        return code_data["section_301_china"]
    chapter = str(hts_code)[:2]
    return SECTION_301_BY_CHAPTER.get(chapter, 0.0)


def check_fta(country_of_origin):
    """Check FTA eligibility. Returns (fta_name, preferential_rate, form_required) or None."""
    if not country_of_origin:
        return None, None, None
    country_lower = str(country_of_origin).lower().strip()
    for country, data in FTA_COUNTRIES.items():
        if country in country_lower:
            return data["name"], data["rate"], data["form"]
    return None, None, None


def get_misclassification_hints(hts_code, description=""):
    """Check common misclassification patterns. Returns list of hints."""
    hints = []
    desc_lower = str(description).lower()
    for code, pattern in COMMON_MISCLASSIFICATIONS.items():
        if str(hts_code).startswith(code[:7]):
            for keyword in pattern["if_contains"]:
                if keyword in desc_lower:
                    hints.append({
                        "suggest": pattern["suggest"],
                        "reason": pattern["reason"],
                        "type": pattern["savings_direction"]
                    })
                    break
    return hints


# Backwards-compatible alias for older imports
def get_misclassification_hint(hts_code, description=""):
    """Returns (suggested_code, reason) tuple for first matching hint, or (None, None)."""
    hints = get_misclassification_hints(hts_code, description)
    if hints:
        return hints[0]["suggest"], hints[0]["reason"]
    return None, None
