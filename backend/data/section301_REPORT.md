# Section 301 (China) Tariff Dataset — Verification Report

Generated 2026-07-13 for TariffCheck. Deliverables in this directory:

- `section301.json` — 10,391 8-digit HTS subheadings with the Section 301 additional duty rate in force as of July 2026, plus the Chapter 99 heading each maps to, list metadata, 14 partial-coverage entries, and 21 recorded spot checks.
- `exclusions.json` — 140 HTS statistical lines annotated with the active exclusion headings 9903.88.69 / 9903.88.70 (in effect through 2026-11-09).
- Working files: `hts_full.json` (USITC HTS export), `china_tariffs.pdf/.txt` (USITC consolidated table), `ch99.pdf`, `ch99_layout.txt`, `notes_parsed.json`, `built.json`, `china_tariffs_parsed.json`, USTR annex PDFs (`list2.pdf`, `list3.pdf`, `list4.pdf`).

## Sources and extraction method

Three independent encodings of the same legal state were extracted and diffed; a fourth (original USTR Federal Register annexes) was used for external spot checks.

1. **USITC "China Tariffs" consolidated table** (PRIMARY for `rates_by_hts8`)
   `https://hts.usitc.gov/reststop/file?release=currentRelease&filename=China+Tariffs`, last updated **2026-02-25**. An official USITC PDF listing every 8-digit subheading in chapters 01–97 covered by Section 301 and its applicable Chapter 99 heading. Parsed with pdftotext + regex: 10,391 rows, zero conflicting duplicates. Its preamble confirms effective dates for every heading and states that suspended provisions (9903.88.16 = List 4B; 9903.91.12/.14 maritime action, suspended until 2026-11-10) are excluded.

2. **USITC HTS JSON export, current release (2026 Revision 11)** (cross-check 1)
   `https://hts.usitc.gov/reststop/exportList?from=0101&to=9999&format=JSON` (35,669 records). Every covered tariff line carries a general-column footnote "See 9903.88.xx / 9903.91.xx". Extracted all such footnotes at 8- and 10-digit level and rolled up.

3. **U.S. notes 20 and 31 to subchapter III of Chapter 99** (cross-check 2)
   Chapter 99 PDF (`.../filename=Chapter%2099`), pdftotext -layout, subdivision boundaries located, subheading enumerations parsed for notes 20(b), 20(d), 20(f), 20(g), 20(s), 20(u) and 31(b)–(j).

4. **USTR Federal Register annexes** (external): List 2 final annex, List 3 annex (83 FR 47974), List 4A/4B annexes (84 FR 43304); USTR Sept 2024 four-year-review press release and 89 FR 76581 (via web search); 89 FR 101682 and 90 FR 48320 / 90 FR 50947 as cited in the HTS compiler notes.

### Heading → rate mapping in force July 2026

| Chapter 99 heading | Rate | Basis | Effective |
|---|---|---|---|
| 9903.88.01 (List 1) | +25% | note 20(a)/(b) | 2018-07-06 |
| 9903.88.02 (List 2) | +25% | note 20(c)/(d) | 2018-08-23 |
| 9903.88.03 (List 3) | +25% | note 20(e)/(f) | 2018-09-24 (25% from 2019-05-10) |
| 9903.88.04 (List 3 suppl.) | +25% | note 20(g) | 2018-09-24 |
| 9903.88.15 (List 4A) | +7.5% | note 20(r)/(s) | 2019-09-01 (7.5% from 2020-02-14) |
| 9903.88.16 (List 4B) | suspended | note 20(t)/(u) | never in force |
| 9903.91.01 | +25% | note 31(b) steel/alum, EV batteries+parts, minerals, facemasks(stat), etc. | 2024-09-27 |
| 9903.91.02 | +50% | note 31(c) solar cells 8541.42/.43 | 2024-09-27 |
| 9903.91.03 | +100% | note 31(d) EVs, syringes/needles | 2024-09-27 |
| 9903.91.05 | +50% | note 31(f) semiconductors, polysilicon, wafers | 2025-01-01 (increase set for 2027-06-23) |
| 9903.91.06 | +25% | note 31(g) graphite, permanent magnets, Li-ion batteries | 2026-01-01 |
| 9903.91.07 | +50% | note 31(h) respirators/facemasks (10-digit only) | 2026-01-01 |
| 9903.91.08 | +100% | note 31(i) medical/surgical rubber gloves 4015.12.10 | 2026-01-01 |
| 9903.91.11 | +25% | note 31(j) tungsten | 2025-01-01 |
| 9903.92.10 | +25% | ship-to-shore gantry cranes of 8426.19.00 only | 2024-09-27 |

Expired and correctly excluded: 9903.91.04 (facemasks 25%, 2025 only), 9903.91.10 (enteral syringe carve-out, ended 2026-01-01), all exclusion headings 9903.88.05–.68.

## Cross-verification results

- **China Tariffs table (10,391) vs HTS footnotes (10,402 rolled-up 8-digit): 0 heading mismatches.**
  - 2 codes in table but without HTS footnote: `04032050` (in note 20(s); treated as covered, apparent USITC annotation gap) and `84261900` (cranes; footnote only for the 9903.91.09 carve-out).
  - 13 codes with footnotes but not in the table: all statistical-level/partial coverage (note 20(g) 10-digit items, note 20(s)(ii) described items, facemask stat lines). These are in `partial_stat_level`, not asserted as full-subheading rates.
- **Note 20/31 enumerations vs footnotes:** after removing chapter-98/99 self-references, List 1 (856), List 2 (283), List 3 (5,906), 4A and note 31 sets matched the footnote-derived sets exactly except the same `04032050`/`85076000` items explained above. Note 31 counts: 31(b)=349→348 full (facemask line partial), 31(c)=2, 31(d)=10, 31(f)=18, 31(g)=5, 31(i)=1, 31(j)=3 — all match.

## Spot-check table (21 checks, 21/21 pass)

| HTS8 | Dataset rate | Source 1 | Source 2 | Match |
|---|---|---|---|---|
| 8407.34.05 | 25% (9903.88.02) | USITC China Tariffs table | USTR List 2 final annex PDF | PASS |
| 8407.34.48 | 25% (9903.88.03) | HTS footnote | USTR List 3 annex 83 FR 47974 | PASS |
| 9403.60.80 furniture | 25% (88.03) | China Tariffs table | USTR List 3 annex | PASS |
| 6802.93.00 granite | 25% (88.03) | China Tariffs table | USTR List 3 annex | PASS |
| 8517.13.00 smartphones | not covered | absent from table/notes 20(b,d,f,s) | USTR Annex C (List 4B, as 8517.12.00); 4B suspended 84 FR 69447 | PASS |
| 8471.30.01 laptops | not covered | absent from table; in note 20(u) | USTR Annex C | PASS |
| 9617.00.40 vacuum flasks >2L | 7.5% (88.15) | China Tariffs; note 20(s) | USTR Annex A (4A); CBP guidance | PASS |
| 9617.00.10 vacuum flasks ≤1L | not covered | in note 20(u) (4B) | USTR Annex C | PASS |
| 7323.93.00 SS kitchenware | not covered (List 4B, NOT List 3) | no footnote; in note 20(u) | USTR Annex C contains 7323.93.00 | PASS |
| 8703.80.00 EVs | 100% (91.03) | HTS footnote; note 31(d) | 89 FR 76581 / USTR press | PASS |
| 9018.31.00 syringes | 100% (91.03) | China Tariffs; note 31(d)(9) | USTR press (100% in 2024) | PASS |
| 8541.42.00 solar cells | 50% (91.02) | China Tariffs; note 31(c) | USTR press | PASS |
| 8507.60.00 Li-ion batteries | 25% (91.06, eff 2026-01-01) | China Tariffs; note 31(g)(5) | USTR press (non-EV Li-ion 25% in 2026) | PASS |
| 2504.90.00 graphite | 25% (91.06) | China Tariffs; note 31(g)(3) | USTR press | PASS |
| 4015.12.10 medical gloves | 100% (91.08, 2026; was 50% in 2025) | HTS footnote; note 31(i) | USTR press (50%→100%) | PASS |
| 2804.61.00 polysilicon | 50% (91.05) | China Tariffs; note 31(f) | 89 FR 101682 | PASS |
| 8542.31.00 semiconductors | 50% (91.05, eff 2025-01-01) | China Tariffs; note 31(f) | 89 FR 76581 | PASS |
| 8101.94.00 tungsten | 25% (91.11) | China Tariffs; note 31(j) | 89 FR 101682 | PASS |
| 8716.39.00 chassis/trailers | 25% (88.03) | China Tariffs; HTS footnote | USTR List 3 annex | PASS |
| 8426.19.00 STS cranes | 25% (92.10, partial — STS cranes only) | China Tariffs table | Ch.99 9903.92.10/.80, note 31(l); 90 FR 48320 | PASS |
| 0101.21.00 | 7.5% (88.15) | China Tariffs table | USTR Annex A | PASS |

Notes on prompt expectations that the sources contradicted: 8407.34.xx is List 2/List 3 (still 25%), not List 1; 7323.93.00 is List 4B (suspended, no duty), not List 3; 9617 is covered only for 9617.00.40 (4A, 7.5%) — 9617.00.10/.30/.60 are 4B.

## Known gaps and limitations

1. **8-digit granularity.** 14 subheadings have only statistical-level (10-digit) or description-limited coverage; they are in `partial_stat_level` with the potentially applicable rate, not in `rates_by_hts8` (except 84261900 and the flagged 63079098 caveat). Facemasks (6307.90.98xx, +50%) and 8426.19.00 cranes are the material cases.
2. **Exclusions.** 9903.88.69/.70 exclusions are active through 2026-11-09 and can zero the duty, but nearly all are limited by narrative product descriptions in notes 20(vvv)/(www). `exclusions.json` is a pointer index of the 140 annotated HTS lines, not the legal exclusion text.
3. **Upcoming changes not in this dataset (by design, as-of July 2026):** 2026-11-10 maritime action (9903.91.12 chassis; 9903.91.14 STS cranes 100%; 9903.91.15/.16 carve-outs) and the 2027-06-23 semiconductor increase.
4. **Program scope.** Section 301 only. IEEPA (fentanyl/reciprocal), Section 232, AD/CVD and MFN duties stack on top and are not included.
5. **Snapshot risk.** The China Tariffs table is dated 2026-02-25; the HTS export is the live current release (2026 Rev. 11) fetched 2026-07-13. The two agree, so no post-February line-level change was detected, but a USTR action published after Rev. 11 would not be reflected.
6. `04032050` is included at 7.5% on the strength of note 20(s) and the consolidated table despite a missing footnote annotation on the HTS line (documented single discrepancy).

## Confidence

**High** for `rates_by_hts8` (three-way agreement across independently parsed official USITC publications, zero mismatches, 21/21 external spot checks). **Medium-high** for `partial_stat_level` semantics (10-digit rollup logic inferred from footnote placement, verified case-by-case for the material items). **Medium** for `exclusions.json` completeness (index of USITC annotations only; the note 20(vvv) narrative descriptions were not individually extracted).
