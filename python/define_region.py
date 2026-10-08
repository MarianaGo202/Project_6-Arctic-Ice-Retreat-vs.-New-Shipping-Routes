import geopandas as gpd
from shapely.geometry import box

MIN_LON, MAX_LON = -180, -145
MIN_LAT, MAX_LAT = 55, 72

regiao_wgs84 = gpd.GeoDataFrame(
    {"name": ["bering_chukchi_study_region"]},
    geometry=[box(MIN_LON, MIN_LAT, MAX_LON, MAX_LAT)],
    crs="EPSG:4326",
)

regiao_wgs84.to_file("data/processed/study_region_wgs84.geojson", driver="GeoJSON")

print("Study region defined in EPSG:4326:")
print(regiao_wgs84.total_bounds)

albers_kapsar = (
    "+proj=aea +lat_1=55 +lat_2=65 +lat_0=50 +lon_0=-154 "
    "+x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"
)

regiao_albers = regiao_wgs84.to_crs(albers_kapsar)
regiao_albers.to_file("data/processed/study_region_albers.geojson", driver="GeoJSON")

print("\nReprojected to Kapsar Albers Equal Area:")
print(regiao_albers.total_bounds)

polar_stereo_nsidc = (
    "+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 "
    "+x_0=0 +y_0=0 +a=6378273 +b=6356889.449 +units=m +no_defs"
)

regiao_polar = regiao_wgs84.to_crs(polar_stereo_nsidc)
regiao_polar.to_file("data/processed/study_region_polar_stereo.geojson", driver="GeoJSON")

print("\nReprojected to NSIDC Polar Stereographic North:")
print(regiao_polar.total_bounds)

print("\nCopernicus CRS not yet confirmed -- check inspect_sources.py output")
print("before clipping the sea ice age NetCDF files.")
