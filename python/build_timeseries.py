import sqlite3

import numpy as np
import pandas as pd
from scipy import stats

extent_df = pd.read_csv("data/raw/N_05_extent_v4.0.csv", skipinitialspace=True)
extent_df.columns = [c.strip() for c in extent_df.columns]
extent_df = extent_df[["year", "extent"]].rename(columns={"extent": "extent_million_km2"})

extent_window = extent_df[(extent_df["year"] >= 2015) & (extent_df["year"] <= 2020)]
traffic_df = pd.read_csv("data/processed/traffic_by_year_wide.csv")
combined_df = extent_window.merge(traffic_df, on="year", how="inner")

print("Combined extent + traffic table:")
print(combined_df)

if len(combined_df) < 6:
    print(f"\n/!\\ WARNING: only {len(combined_df)} overlapping years -- "
          "treat any correlation below as indicative, not conclusive.")

r, p = stats.pearsonr(combined_df["extent_million_km2"], combined_df["total_traffic"])

print(f"\nExtent vs. total traffic: r = {r:.3f}, p = {p:.4f}")

for vessel_type in ["Cargo", "Fishing", "Tanker", "Other"]:
    r_type, p_type = stats.pearsonr(combined_df["extent_million_km2"], combined_df[vessel_type])
    print(f"Extent vs. {vessel_type.lower()}: r = {r_type:.3f}, p = {p_type:.4f}")
    
ice_age_df = pd.read_csv("data/processed/ice_age_by_year.csv")

connection = sqlite3.connect("database/arctic_shipping_routes.db")

extent_df.to_sql("ice_extent_long_term", connection, if_exists="replace", index=False)
combined_df.to_sql("ice_extent_vs_traffic", connection, if_exists="replace", index=False)
ice_age_df.to_sql("ice_age_recent", connection, if_exists="replace", index=False)

connection.close()

print("\nDatabase created: database/arctic_shipping_routes.db")
print("Tables: ice_extent_long_term, ice_extent_vs_traffic, ice_age_recent")
