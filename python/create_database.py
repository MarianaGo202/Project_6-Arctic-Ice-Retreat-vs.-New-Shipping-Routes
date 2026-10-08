import os
import sqlite3
import pandas as pd

# Paths (relative to the project root)
CSV_PATH = "data/processed/arctic_sea_ice_sql.csv"
DB_PATH = "database/arctic_ice.db"
TABLE_NAME = "ice_concentration"

def load_csv(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from {csv_path}")
    print(df.head())
    return df

def save_to_sqlite(df: pd.DataFrame, db_path: str, table_name: str) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        df.to_sql(table_name, connection, if_exists="replace", index=False)

        # Read a few rows back as a sanity check that the write worked
        preview = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", connection)
        print(f"\nPreview of '{table_name}' in {db_path}:")
        print(preview)

def main():
    df = load_csv(CSV_PATH)
    save_to_sqlite(df, DB_PATH, TABLE_NAME)
    print(f"\nDatabase created successfully: {DB_PATH}")

if __name__ == "__main__":
    main()