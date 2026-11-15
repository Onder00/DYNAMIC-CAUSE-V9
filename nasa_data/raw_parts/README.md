# NASA RR-28 original CSV — byte-verified archival parts

The official historical `RR-28_EDA_Telemetry_data.csv` downloaded from the NASA OSDR Environmental Data Application was preserved unchanged, but divided into **8 sequential binary-safe text parts** for GitHub upload.

**Do not open or resave the parts in a spreadsheet application; their CRLF bytes are significant.**

Use the Python standard-library restoration script:

```bash
python scripts/restore_nasa_data.py
```

The script concatenates these files in numeric order, checks SHA-256 of the resulting original CSV, invokes the team's saved preprocessing code, validates the cleaned CSV, and copies it into the root folder for the V9 dashboard.

Original unmodified CSV: **4,422,233 bytes**, SHA-256:
`4bfaf470cae9cbb895969f2cdd9eb68983ad0a8e9cfb9a428cba9243f28e68d6`

Prepared CSV: **4,115,430 bytes**, SHA-256:
`80c6714b0d1c6360a865874adb7af0cda63fcb923a6ab675b0c7d38a0067c4a3`

Historical NASA RR-28 experimental telemetry; not real-time astronaut or ISS crew health measurements.

Source: https://visualization.osdr.nasa.gov/eda/
