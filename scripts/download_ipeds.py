"""Download the IPEDS complete data files this project uses and unzip them.

Run from the repo root: python scripts/download_ipeds.py
The files are large, so data/raw/ipeds/ is git-ignored and rebuilt by this script.
"""
from pathlib import Path
import urllib.request
import zipfile

BASE = "https://nces.ed.gov/ipeds/datacenter/data/{}.zip"
YEARS = range(2019, 2024)
OUT = Path("data/raw/ipeds")
UNZ = OUT / "unz"
UNZ.mkdir(parents=True, exist_ok=True)

for year in YEARS:
    for stem in (f"HD{year}", f"EF{year}A", f"EF{year}D", f"GR{year}"):
        target = OUT / f"{stem}.zip"
        if not target.exists():
            request = urllib.request.Request(BASE.format(stem), headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=180) as response:
                target.write_bytes(response.read())
            print("downloaded", target.name)
        with zipfile.ZipFile(target) as archive:
            archive.extractall(UNZ)
