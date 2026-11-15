# NASA RR-28 Data Provenance and Preprocessing

**Repository:** NASA Open Science Data Repository (OSDR), Environmental Data Application (EDA).
**Mission:** Rodent Research-28 (RR-28).
**Data portal:** https://visualization.osdr.nasa.gov/eda/
**Historical period:** 2024-03-21 00:00 through 2024-05-06 13:16 GMT.

## Variables
- `Controller_Time_GMT`: controller timestamp
- `Temp_degC_Ground`, `Temp_degC_ISS`: temperature (°C)
- `RH_percent_Ground`, `RH_percent_ISS`: relative humidity (%)
- `CO2_ppm_Ground`, `CO2_ppm_ISS`: CO₂ (ppm)

## Reproducible preprocessing
`RR-28_EDA_Telemetry_data.csv` → `RR28_temizle.py` → `RR28_temiz_veri.csv` plus `RR28_tekrar_kayitlari.csv` and `RR28_temizlik_raporu.txt`.

1. Keep original NASA CSV intact.
2. Normalize missing markers (e.g., `NaN`) to blank cells.
3. Validate measurement fields as finite numbers and validate timestamps.
4. Group equal timestamps. Retain non-conflicting measurements; leave conflicting ones blank, not averaged.
5. Preserve originals in a duplicate-audit CSV.
6. Keep ISS and ground columns distinct.
7. Annotate missing measurements, conflicts, merged timestamps and gaps using `QA_*` columns.
8. Do not interpolate temporal gaps or silently exclude elevated CO₂ measurements.

## Recorded results
| Metric | Value |
|---|---:|
| Original rows | 61,488 |
| Unique timestamp rows | 61,481 |
| Duplicate timestamp groups | 7 |
| Original duplicate rows audited | 14 |
| Conflicting measurement cells | 13 |
| Raw missing cells | 6 |
| Clean missing cells | 19 |
| Time gaps >1 minute | 20 |
| Largest gap | 5,537 minutes |

The prepared NASA data are **not** live ISS telemetry and do **not** represent astronaut physiological measurements. No direct causal connection to synthetic or self-reported check-ins has been tested.

**Repository completion note:** CSV datasets should be placed under `nasa_data/`; the full source and prepared datasets are not yet present in this initial code/documentation upload.