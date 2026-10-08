from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.plot import show
from rasterio.warp import calculate_default_transform, reproject, Resampling

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"

VISUALISATIONS_DIR = PROJECT_DIR / "visualisations"
VISUALISATIONS_DIR.mkdir(parents=True, exist_ok=True)

albers_kapsar = (
    "+proj=aea +lat_1=55 +lat_2=65 +lat_0=50 +lon_0=-154 "
    "+x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"
)

extent_2025_file = RAW_DIR / "extent_N_202505_polygon_v4.0" / "extent_N_202505_polygon_v4.0.shp"
historical_median_file = (
    RAW_DIR / "median_extent_N_05_1981-2010_polyline_v4.0" / "median_extent_N_05_1981-2010_polyline_v4.0.shp"
)

if not extent_2025_file.exists():
    raise FileNotFoundError(f"2025 ice extent file not found:\n{extent_2025_file}")

if not historical_median_file.exists():
    raise FileNotFoundError(f"Historical median file not found:\n{historical_median_file}")

print("CRITICAL ARCTIC TRAFFIC MAP")

print("\n2025 ice extent:")
print(extent_2025_file.relative_to(PROJECT_DIR))
print("\nHistorical median:")
print(historical_median_file.relative_to(PROJECT_DIR))

print("\nLoading ice extent layers...")

extent_2025 = gpd.read_file(extent_2025_file)
historical_median = gpd.read_file(historical_median_file)

extent_2025 = extent_2025.to_crs(albers_kapsar)
historical_median = historical_median.to_crs(albers_kapsar)

traffic_dir = RAW_DIR / "arctic_marine_vessel_traffic" / "25km"

if not traffic_dir.exists():
    raise FileNotFoundError(f"Traffic raster directory not found:\n{traffic_dir}")

vessel_types = ["Cargo", "Fishing", "Tanker", "Other"]

total_2020 = None
traffic_transform = None
traffic_crs = None
traffic_width = None
traffic_height = None

for vessel_type in vessel_types:
    raster_file = traffic_dir / f"Raster_2020_05_{vessel_type}_25km.tif"

    if not raster_file.exists():
        raise FileNotFoundError(f"Traffic raster not found:\n{raster_file}")

    print(f"\nLoading traffic raster: {raster_file.name}")

    with rasterio.open(raster_file) as src:
        data = src.read(1, masked=True)

        if total_2020 is None:
            total_2020 = data.astype("float64")
            traffic_transform = src.transform
            traffic_crs = src.crs
            traffic_width = src.width
            traffic_height = src.height
        else:
            if data.shape != total_2020.shape:
                raise ValueError("Traffic rasters have different dimensions.")
            total_2020 = total_2020 + data

print(f"\nTraffic CRS: {traffic_crs}")
print(f"Ice extent CRS: {extent_2025.crs}")

if str(traffic_crs) != str(extent_2025.crs):
    print("\nReprojecting traffic raster to Kapsar Albers...")

    left, bottom, right, top = rasterio.transform.array_bounds(
        traffic_height, traffic_width, traffic_transform
    )

    new_transform, new_width, new_height = calculate_default_transform(
        traffic_crs, albers_kapsar, traffic_width, traffic_height, left, bottom, right, top
    )

    source_data = total_2020.filled(0)
    destination_data = np.zeros((new_height, new_width), dtype="float64")

    reproject(
        source=source_data,
        destination=destination_data,
        src_transform=traffic_transform,
        src_crs=traffic_crs,
        dst_transform=new_transform,
        dst_crs=albers_kapsar,
        resampling=Resampling.bilinear,
    )

    total_2020 = np.ma.masked_equal(destination_data, 0)
    traffic_transform = new_transform

traffic_plot = np.ma.array(np.log1p(total_2020.data), mask=total_2020.mask)

fig, ax = plt.subplots(figsize=(10, 10))

show(traffic_plot, transform=traffic_transform, ax=ax, cmap="YlOrRd")

extent_2025.boundary.plot(ax=ax, color="deepskyblue", linewidth=2, label="May 2025 extent")

historical_median.plot(
    ax=ax, color="white", linewidth=1.5, linestyle="--", label="1981-2010 median extent"
)

ax.set_title(
    "Bering Strait / Chukchi Sea: May 2020 vessel traffic\n"
    "vs. sea ice extent (2025 vs. 1981-2010 median)"
)

ax.legend(loc="lower left")

ax.set_axis_off()

output_file = VISUALISATIONS_DIR / "critical_map_bering_chukchi.png"

plt.tight_layout()
plt.savefig(output_file, dpi=300, bbox_inches="tight")
plt.show()

print("MAP CREATED SUCCESSFULLY")

print(f"\nSaved:\n{output_file}")