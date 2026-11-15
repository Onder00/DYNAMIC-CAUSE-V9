# DYNAMIC CAUSE V9 🛰️
**NASA Space Apps Challenge Sivas 2026** — **DYNAMIC TEAM**

**Challenge:** Create Health Monitoring Software for Astronauts on Space Missions

## The problem
A change in a crew member's reported sleep, fatigue, or well-being may trigger an alert, but that warning alone does not identify a cause or show the limitations of available evidence.

## Our research prototype
DYNAMIC CAUSE V9 combines a real ESP32 + Arduino Uno demonstration, local light (LDR ADC) and touch-event (TTP223) logs, historical NASA RR-28 environmental records, synthetic/manual crew check-ins, an explainable rules dashboard and structured evidence reports.

**This is not a medical device or a trained AI diagnostic system.** The NASA environmental observations are historical, not live ISS telemetry or astronaut vital signs. The prototype does not infer that RR-28 environmental observations cause the self-reported health changes.

## What is included
- `dynamic_cause_v9_panel.py`: original V9 Streamlit dashboard.
- `nasa_data/RR28_temizle.py`: original NASA RR-28 preprocessing script (Python standard library).
- `nasa_data/quality/`: first-pass QA summary, audit and cleaning report.
- `docs/`: architecture, source provenance, local deployment instructions and missing-original-source checklist.
- `requirements.txt` and `scripts/verify_nasa_data.py`.

**Source release status:** The original `esp32_veri_toplama_v3.py` serial collector and Arduino ESP32 V8 / Uno V7 .ino files have not yet been recovered from the Windows/Arduino IDE working session. They have intentionally NOT been replaced with fabricated firmware. Thus the complete live hardware stack is not yet reproducible from this repository alone.

## Installation
```bash
python -m pip install -r requirements.txt
python -m streamlit run dynamic_cause_v9_panel.py --server.port 8509
```

The NASA original RR-28 EDA CSV is preserved in **8 byte-exact parts** in `nasa_data/raw_parts/` to enable GitHub connector upload while retaining its integrity. **First run:**

```bash
python scripts/restore_nasa_data.py
```

This reconstructs `nasa_data/RR-28_EDA_Telemetry_data.csv`, validates its original SHA-256, executes the preserved `nasa_data/RR28_temizle.py` processing, validates the resulting `nasa_data/RR28_temiz_veri.csv`, and installs the cleaned CSV at project root as `RR28_temiz_veri.csv` for the V9 dashboard. No manual NASA download is needed. The dashboard can demonstrate check-in rules independently of live sensor acquisition.

## NASA RR-28 preprocessing
**Official NASA OSDR Environmental Data Application:** https://visualization.osdr.nasa.gov/eda/

Source CSV: `RR-28_EDA_Telemetry_data.csv` (historical ISS and ground telemetry, March–May 2024).

```bash
python nasa_data/RR28_temizle.py nasa_data/RR-28_EDA_Telemetry_data.csv
```

The pipeline normalizes missing markers, validates timestamps and numeric fields, groups duplicate timestamp records without averaging contradictory measurements, saves duplicate source rows for audit, flags QA conditions, and preserves time gaps and ISS-versus-ground distinction. Recorded results: 61,488 original rows → 61,481 unique timestamp rows. The original raw CSV is present in eight verified, reassemblable parts; the complete processed CSV is regenerated deterministically with the included preprocessing script and integrity checker.

## Project demonstration
[7-slide English presentation — public Google Drive PDF](https://drive.google.com/file/d/1VpdU-SmF0JiuM-h8tUiJZa540GpTCflh/view?usp=sharing)

Synthetic six-record demonstration: sleep 7.5→5.0 hours, fatigue 3→8/10, well-being 7→3/10; seven illustrative flags (four fixed rules and three baseline change flags). **Not clinically validated.**

## Team
- Önder Keskin — Team Leader; Molecular Biologist; Bioinformatics MSc Student
- Prof. Dr. Serkan Akkoyun — Professor; Nuclear Physicist
- Nisa Yılmaz — Third-year Physics Undergraduate Student

## AI use disclosure
ChatGPT assisted with planning, coding/debugging and documentation; Canva AI assisted presentation design. Team members selected the approach, assembled and tested the hardware, and are responsible for scientific claims. AI-generated artwork in external slides is subject to competition disclosure/watermark rules.

## Scientific limitations
- No direct physiological sensor for pulse, SpO₂ or astronaut vital signs.
- No trained predictive ML/AI clinical model.
- Local LDR/touch signals are not human health signals.
- NASA RR-28 data are historical rodent research environmental context, not contemporary astronaut measurements.
- Environmental and crew check-in records are **not** timestamp-aligned; no causal inference is supported.
- This is a research demonstrator, not a certified clinical or spaceflight safety system.

All rights for original team code and media reserved pending an explicit team licensing decision; NASA source attribution is retained.