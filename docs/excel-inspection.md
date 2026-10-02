# Synthetic Rev07-compatible workbook inspection

Source: `sample-data/Rev07_Sample_Catalog_60.xlsx`.

This workbook is a public-safe fixture generated from scratch by `scripts/generate_sample_catalog.py`. It is **not** an anonymized, perturbed, or lightly modified copy of the private film archive.

| Sheet | Data rows |
| --- | ---: |
| Rev07_Channel_Value_Ranking | 60 |
| Rev07_Taste_Fit_Ranking | 60 |
| Rev07_Viewing_Priority_Ranking | 60 |
| Rev07_Not_For_Channel | 8 |
| Rev07_Not_For_My_Taste | 7 |
| Rev07_Skip_For_Now | 10 |
| Rev07_Top_Content_Candidates | 12 |
| Rev07_Score_Audit | 12 |

The primary sheet contains exactly 60 records and the importer-facing columns required by the application: `Master ID`, `Title`, `Year`, `Director / Creator`, `Genre`, `Rev07 Channel`, `Rev07 Taste Fit`, `Rev07 Tier`, `Rev07 Viewing Priority`, `Analytical Note`, and `Rev07 Calibration Reason`. Master IDs are unique and fictional.

The fixture deliberately exercises title ambiguity and matching edge cases. Repeated-title groups include:

| Synthetic title | Years |
| --- | --- |
| Silent Harbor | 1968, 2011 |
| Glass Orchard | 2001, 2011 |
| The Witness Room | 1973, 2022 |
| Northbound Silence | 1992, 2003, 2024 |
| A Map of Ash | 2001, 2016, 2024 |

The sample also contains explicit series hints through fictional `Miniseries`, `TV Series`, and `Reality-TV` genre metadata. Independent flag sheets intentionally overlap so that flag membership is tested independently rather than treated as mutually exclusive classification.

Tier distribution in the generated primary sheet:

| Tier | Records |
| --- | ---: |
| S | 6 |
| A | 20 |
| B | 18 |
| C | 10 |
| D | 6 |

Viewing-priority distribution:

| Priority | Records |
| --- | ---: |
| 1 — Essential | 12 |
| 2 — High | 14 |
| 3 — Medium | 18 |
| 4 — Low | 11 |
| 5 — Skip for Now | 5 |

The two alternate ranking sheets contain the same source values as the primary catalog while changing row order only. Flag-sheet IDs refer to valid primary Master IDs. The score-audit sheet is synthetic historical fixture data and does not override the primary sheet.

Machine-readable structural evidence is in [excel-inspection.json](excel-inspection.json). The repeatable read-only inspector is `scripts/inspect_excel.py`.

This is a bounded fixture inspection for software validation. It makes no claim about the contents, rankings, or composition of the private archive.
