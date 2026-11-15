#!/usr/bin/env python3
"""Reconstruct NASA RR-28 original CSV byte-for-byte, then reproduce cleaned output.

Uses only Python standard library. Run from any working directory:
    python scripts/restore_nasa_data.py
"""
from __future__ import annotations
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "nasa_data"
PARTS = DATA / "raw_parts"
RAW = DATA / "RR-28_EDA_Telemetry_data.csv"
CLEAN = DATA / "RR28_temiz_veri.csv"
ROOT_CLEAN = ROOT / "RR28_temiz_veri.csv"
SCRIPT = DATA / "RR28_temizle.py"
EXPECTED_RAW_SHA256 = "4bfaf470cae9cbb895969f2cdd9eb68983ad0a8e9cfb9a428cba9243f28e68d6"
EXPECTED_CLEAN_SHA256 = "80c6714b0d1c6360a865874adb7af0cda63fcb923a6ab675b0c7d38a0067c4a3"


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    expected_parts = [PARTS / f"RR28_raw_{i:02d}.part" for i in range(1, 9)]
    missing = [str(p) for p in expected_parts if not p.is_file()]
    if missing:
        raise SystemExit("Missing NASA raw data part(s):\n" + "\n".join(missing))
    with RAW.open("wb") as out:
        for path in expected_parts:
            with path.open("rb") as inp:
                shutil.copyfileobj(inp, out)

    raw_sha = checksum(RAW)
    if raw_sha != EXPECTED_RAW_SHA256:
        RAW.unlink(missing_ok=True)
        raise SystemExit(f"Original NASA CSV hash mismatch: {raw_sha}")
    print(f"PASS: original NASA source restored ({RAW.stat().st_size:,} bytes).")

    subprocess.run([sys.executable, str(SCRIPT), str(RAW)], check=True)
    clean_sha = checksum(CLEAN)
    if clean_sha != EXPECTED_CLEAN_SHA256:
        raise SystemExit(
            f"Clean-data checksum differs from preserved reference: {clean_sha}. "
            "Inspect platform line endings and preprocessing version before use."
        )
    shutil.copy2(CLEAN, ROOT_CLEAN)
    print("PASS: cleaned RR-28 dataset matches preserved reference SHA-256.")
    print(f"V9 dashboard NASA data ready: {ROOT_CLEAN}")


if __name__ == "__main__":
    main()
