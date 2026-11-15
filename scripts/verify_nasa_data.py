#!/usr/bin/env python3
"""Smoke test for the documented RR-28 row counts and QA schema."""
import csv
from pathlib import Path
root = Path(__file__).resolve().parent.parent
raw = root / "nasa_data" / "RR-28_EDA_Telemetry_data.csv"
clean = root / "nasa_data" / "RR28_temiz_veri.csv"
with raw.open(encoding="utf-8-sig", newline="") as fh:
    n_raw = sum(1 for _ in csv.DictReader(fh))
with clean.open(encoding="utf-8-sig", newline="") as fh:
    reader = csv.DictReader(fh)
    fields = set(reader.fieldnames or [])
    n_clean = sum(1 for _ in reader)
required = {"Controller_Time_GMT", "CO2_ppm_ISS", "CO2_ppm_Ground", "QA_Status", "QA_Gap_Minutes_Before"}
assert required <= fields
assert n_raw == 61488, n_raw
assert n_clean == 61481, n_clean
print("PASS: NASA RR-28 source/clean counts and QA schema")