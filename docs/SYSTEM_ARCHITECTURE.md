# DYNAMIC CAUSE V9 — Implemented Architecture

## Local hardware
- ESP32 with LDR ambient-light ADC and TTP223 touch/event sensing.
- Arduino Uno and OLED/LCD visual outputs.
- MicroSD/CSV offline logging (in physical prototype).
- A separate V3 Python serial collector reads the hardware and records local CSV files.
- V9 Streamlit dashboard **reads** those files; it does not flash hardware or open COM ports.

## NASA OSDR RR-28
Historical ground/ISS CO₂, temperature and humidity CSV, prepared via `nasa_data/RR28_temizle.py`; visualized and QA-annotated. Not live crew telemetry.

## Crew check-in demonstration
Manual check-in or synthetic six-record scenario covering sleep, fatigue, well-being and symptoms. Transparent rule-based flags and comparisons with the median of five preceding records. No trained prediction model and no clinical validation.

## Evidence
Streamlit pages for live local sensing (when collector active), MicroSD, NASA environment, self-report decision support and downloadable structured JSON evidence.

## Scientific boundaries
Different sources are presented separately, rather than merged into temporally synchronized causal claims. Local light/touch values are **not** measurements of pulse, SpO₂ or astronaut health. The project is a research prototype.

## Original Windows execution
```powershell
cd "C:\Users\keski\OneDrive\Desktop\DYNAMIC_CAUSE"
.\.venv\Scripts\Activate.ps1
python esp32_veri_toplama_v3.py
```

In a second terminal:
```powershell
python -m streamlit run dynamic_cause_v9_panel.py --server.port 8509
```

The original serial collector and ESP32/Uno sketch source files must still be recovered from the Windows computer/Arduino IDE before a full hardware-reproducible release.