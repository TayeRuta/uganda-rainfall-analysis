"""
Download the two ocean climate indices used in Part 3 and save them as tidy CSVs.

Usage (from anywhere):
    python scripts/fetch_climate_indices.py

Output (written to data/external/):
    dmi_monthly.csv — Indian Ocean Dipole Mode Index (HadISST1.1), NOAA PSL
                      columns: year, month, dmi
    oni_seasonal.csv — Oceanic Niño Index (ERSSTv5), NOAA CPC
                       columns: season, year, oni   (3-month running means: DJF, JFM, ...)
"""
import io
import urllib.request
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'external'

DMI_URL = 'https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data'
ONI_URL = 'https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt'
MISSING = -9999


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode('utf-8')


def parse_dmi(text):
    # PSL format: a "first_year last_year" header, then one row per year with
    # 12 monthly values, then a missing-value line and free-text notes.
    lines = text.splitlines()
    first, last = map(int, lines[0].split())
    rows = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) != 13 or not parts[0].isdigit():
            continue
        year = int(parts[0])
        if not first <= year <= last:
            continue
        for month, v in enumerate(parts[1:], start=1):
            v = float(v)
            if v > MISSING:
                rows.append({'year': year, 'month': month, 'dmi': v})
    return pd.DataFrame(rows)


def parse_oni(text):
    df = pd.read_csv(io.StringIO(text), sep=r'\s+')
    return df.rename(columns={'SEAS': 'season', 'YR': 'year', 'ANOM': 'oni'})[['season', 'year', 'oni']]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dmi = parse_dmi(fetch(DMI_URL))
    oni = parse_oni(fetch(ONI_URL))
    dmi.to_csv(OUT / 'dmi_monthly.csv', index=False)
    oni.to_csv(OUT / 'oni_seasonal.csv', index=False)
    print(f'DMI: {len(dmi)} months, {dmi.year.min()}–{dmi.year.max()}')
    print(f'ONI: {len(oni)} seasons, {oni.year.min()}–{oni.year.max()}')


if __name__ == '__main__':
    main()
