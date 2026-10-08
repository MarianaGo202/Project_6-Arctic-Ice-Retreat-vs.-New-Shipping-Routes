import glob
import os
from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio
import xarray as xr

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"

print("1. NSIDC SEA ICE INDEX - LONG-TERM MAY EXTENT (CSV)")

extent_csv = RAW_DIR / "N_05_extent_v4.0.csv"

extent_df = pd.read_csv(extent_csv, skipinitialspace=True)
extent_df.columns = [c.strip() for c in extent_df.columns]

print(extent_df.head())
print("\nShape:", extent_df.shape)
print("Year range:", extent_df["year"].min(), "-", extent_df["year"].max())
print("Source datasets used:", extent_df["source_dataset"].unique())
print("Missing values:\n", extent_df.isnull().sum())

print("\n2. NSIDC MONTHLY SHAPEFILES - ICE EXTENT GEOMETRY")

shapefiles = {
    "extent_polygon": (
        RAW_DIR
        / "extent_N_202505_polygon_v4.0"
        / "extent_N_202505_polygon_v4.0.shp"
    ),
    "extent_polyline": (
        RAW_DIR
        / "extent_N_202505_polyline_v4.0"
        / "extent_N_202505_polyline_v4.0.shp"
    ),
    "median_extent_1981_2010": (
        RAW_DIR
        / "median_extent_N_05_1981-2010_polyline_v4.0"
        / "median_extent_N_05_1981-2010_polyline_v4.0.shp"
    ),
}

for name, path in shapefiles.items():

    if not path.exists():
        print(f"\nWARNING: File not found for {name}")
        print("Expected path:", path)
        continue

    gdf = gpd.read_file(path)

    print(f"\n--- {name} ---")
    print("CRS:", gdf.crs)
    print("Geometry type:", gdf.geom_type.unique())
    print("Number of features:", len(gdf))
    print("Bounds:", gdf.total_bounds)
    print("Columns:", list(gdf.columns))

print("\n3. KAPSAR ET AL. VESSEL TRAFFIC RASTERS (GeoTIFF)")

rasters = sorted(
    glob.glob(str(RAW_DIR / "Raster_*.tif"))
)

print(f"Found {len(rasters)} raster files")

summary = []

for path in rasters:
    file_name = os.path.basename(path)
    with rasterio.open(path) as src:
        band = src.read(1, masked=True)
        summary.append({
            "file": file_name,
            "crs": src.crs.to_string() if src.crs else None,
            "width": src.width,
            "height": src.height,
            "resolution_m": src.res,
            "nodata": src.nodata,
            "mean": float(band.mean()) if band.count() > 0 else None,
            "max": float(band.max()) if band.count() > 0 else None,
        })

rasters_df = pd.DataFrame(summary)

if rasters_df.empty:
    print("No raster files found matching: Raster_*.tif")
else:
    print(rasters_df.to_string(index=False))

    resolutions = rasters_df["resolution_m"].astype(str).unique()

    if len(resolutions) > 1:
        print(
            f"\nWARNING: rasters found at more than one resolution: "
            f"{resolutions}"
        )
        print(
            "Standardize on one resolution before running "
            "extract_traffic.py"
        )


print("\n4. COPERNICUS ARCTIC SEA ICE AGE (NetCDF)")

# Daily files, one per day, organized in year folders:
# data/raw/arctic_ice_age/may2023/*.nc, may2024/*.nc, etc.
ice_age_dir = RAW_DIR / "arctic_ice_age"

netcdf_files = sorted(ice_age_dir.glob("may*/*.nc"))

if not netcdf_files:
    print(f"No NetCDF files found under {ice_age_dir}/may*/.")
    print("Update the path above to match your downloaded folder layout.")

else:

    # One daily file per day - inspect just the first file from each
    # year folder, since they all share the same structure.
    seen_folders = set()

    for path in netcdf_files:
        year_folder = path.parent.name
        if year_folder in seen_folders:
            continue
        seen_folders.add(year_folder)
        print(f"\n--- {year_folder}: {path.name} ---")
        dataset = xr.open_dataset(path)
        print("Dimensions:", dict(dataset.sizes))
        print("Data variables:", list(dataset.data_vars))
        print("Coordinates:", list(dataset.coords))
        for variable in dataset.data_vars:
            missing_values = dataset[variable].isnull().sum().item()
            print(
                f"  {variable}: "
                f"{missing_values} missing values"
            )
        dataset.close()
    print(
        f"\nTotal daily files found across {len(seen_folders)} "
        f"year folder(s): {len(netcdf_files)}"
    )

print("\nInspection complete.")