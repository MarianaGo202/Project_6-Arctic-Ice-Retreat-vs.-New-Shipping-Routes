import glob
import os
import re

import pandas as pd
import xarray as xr

BASE_DIR = "data/raw/arctic_ice_age"

CONCENTRATION_VARIABLES = [
    "conc_1yi",
    "conc_2yi",
    "conc_3yi",
    "conc_4yi",
    "conc_5yi",
    "conc_6yi",
]

MIN_LON, MAX_LON = -180, -145
MIN_LAT, MAX_LAT = 55, 72

def find_lat_lon_names(dataset):
    lat_name = next((c for c in dataset.coords if "lat" in c.lower()), None)
    lon_name = next((c for c in dataset.coords if "lon" in c.lower()), None)

    if lat_name is None:
        lat_name = next((v for v in dataset.data_vars if "lat" in v.lower()), None)
    if lon_name is None:
        lon_name = next((v for v in dataset.data_vars if "lon" in v.lower()), None)

    return lat_name, lon_name

files = sorted(glob.glob(os.path.join(BASE_DIR, "may*", "*.nc")))

print(f"Found {len(files)} daily NetCDF files")

daily_records = []
skipped_files = []

for path in files:
    file_name = os.path.basename(path)
    date_match = re.search(r"(\d{8})\.nc$", file_name)

    if not date_match:
        skipped_files.append((file_name, "no date found in filename"))
        continue

    date_str = date_match.group(1)
    year = int(date_str[:4])

    dataset = xr.open_dataset(path)
    lat_name, lon_name = find_lat_lon_names(dataset)

    if lat_name is None or lon_name is None:
        skipped_files.append((
            file_name,
            f"no lat/lon found (coords: {list(dataset.coords)}, "
            f"data_vars: {list(dataset.data_vars)})",
        ))
        dataset.close()
        continue

    lat = dataset[lat_name]
    lon = dataset[lon_name]
    within_region = (lat >= MIN_LAT) & (lat <= MAX_LAT) & (lon >= MIN_LON) & (lon <= MAX_LON)

    row = {
        "date": pd.to_datetime(date_str, format="%Y%m%d"),
        "year": year,
        "mean_siage": float(dataset["siage"].where(within_region).mean().item()),
    }

    for variable in CONCENTRATION_VARIABLES:
        row[variable] = float(dataset[variable].where(within_region).mean().item())

    daily_records.append(row)
    dataset.close()

if skipped_files:
    print(f"\nSkipped {len(skipped_files)} file(s):")
    for file_name, reason in skipped_files[:10]:
        print(f" - {file_name}: {reason}")
    if len(skipped_files) > 10:
        print(f" ... and {len(skipped_files) - 10} more")

daily_df = pd.DataFrame(daily_records).sort_values("date")

print(f"\nProcessed {len(daily_df)} daily records")

daily_df.to_csv("data/processed/ice_age_daily_regional.csv", index=False)

annual_df = (
    daily_df.drop(columns=["date"])
    .groupby("year", as_index=False)
    .mean(numeric_only=True)
)

annual_df.to_csv("data/processed/ice_age_by_year.csv", index=False)

print("\nYearly regional means:")
print(annual_df)
