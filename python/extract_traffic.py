from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.mask import mask

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
TRAFFIC_DIR = RAW_DIR / "arctic_marine_vessel_traffic" / "25km"
PROCESSED_DIR = DATA_DIR / "processed"
REGION_FILE = PROCESSED_DIR / "study_region_albers.geojson"

VESSEL_TYPES = ["Cargo", "Fishing", "Tanker", "Other"]
YEARS = range(2015, 2021)
RESOLUTION = "25km"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

if not REGION_FILE.exists():
    raise FileNotFoundError(f"Study region not found:\n{REGION_FILE}")

region = gpd.read_file(REGION_FILE)

if region.empty:
    raise ValueError("The study region GeoJSON is empty.")

geometry = [region.geometry.iloc[0].__geo_interface__]

if not TRAFFIC_DIR.exists():
    raise FileNotFoundError(f"Traffic raster directory not found:\n{TRAFFIC_DIR}")

print("\nTraffic raster directory:")
print(TRAFFIC_DIR)
print("\nStudy region:")
print(REGION_FILE)

results = []
missing_files = []

for year in YEARS:
    for vessel_type in VESSEL_TYPES:
        file_name = f"Raster_{year}_05_{vessel_type}_{RESOLUTION}.tif"
        path = TRAFFIC_DIR / file_name
        if not path.exists():
            print(f"Missing: {file_name} -- skipped")
            missing_files.append(file_name)
            continue
        print(f"Processing: {file_name}")
        try:
            with rasterio.open(path) as src:
                clipped, _ = mask(src, geometry, crop=True, nodata=src.nodata)
                values = clipped[0]
                if src.nodata is not None:
                    values = values[values != src.nodata]
                values = values[~pd.isna(values)]
                if values.size > 0:
                    mean_traffic = float(values.mean())
                    sum_traffic = float(values.sum())
                    n_cells = int(values.size)
                else:
                    mean_traffic = None
                    sum_traffic = None
                    n_cells = 0
                results.append({
                    "year": year,
                    "vessel_type": vessel_type,
                    "mean_traffic": mean_traffic,
                    "sum_traffic": sum_traffic,
                    "n_cells": n_cells,
                })
        except Exception as error:
            print(f"Error processing {file_name}: {error}")

columns = ["year", "vessel_type", "mean_traffic", "sum_traffic", "n_cells"]
traffic_df = pd.DataFrame(results, columns=columns)

if traffic_df.empty:
    print("\nNo traffic rasters were found.")
    print(f"\nChecked directory:\n{TRAFFIC_DIR}")
    print(f"\nExpected filename pattern:\nRaster_YYYY_05_TYPE_{RESOLUTION}.tif")
    raise SystemExit(1)

long_output = PROCESSED_DIR / "traffic_by_year_type.csv"
traffic_df.to_csv(long_output, index=False)

print("TRAFFIC DATA")

print(traffic_df.to_string(index=False))

wide_df = (
    traffic_df
    .pivot(index="year", columns="vessel_type", values="mean_traffic")
    .reset_index()
)

for vessel_type in VESSEL_TYPES:
    if vessel_type not in wide_df.columns:
        wide_df[vessel_type] = 0

wide_df["total_traffic"] = wide_df[VESSEL_TYPES].fillna(0).sum(axis=1)

wide_df = wide_df[["year"] + VESSEL_TYPES + ["total_traffic"]]

wide_output = PROCESSED_DIR / "traffic_by_year_wide.csv"
wide_df.to_csv(wide_output, index=False)

print("WIDE FORMAT")

print(wide_df.to_string(index=False))

print("PROCESSING SUMMARY")

print(f"\nSaved:\n{long_output}")
print(f"\nSaved:\n{wide_output}")
print(f"\nProcessed rasters: {len(results)}")
print(f"Missing rasters: {len(missing_files)}")

if missing_files:
    print("\nMissing files:")
    for file_name in missing_files:
        print(f" - {file_name}")
else:
    print("\nAll expected rasters were found.")

print("\nProcessing completed successfully.")