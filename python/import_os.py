import os

FOLDERS = [
    "data/raw",
    "data/processed",
    "database",
    "power bi",
    "python",
    "sql",
    "visualisations",
]

for folder in FOLDERS:
    os.makedirs(folder, exist_ok=True)

print("Folder structure created:")

for folder in FOLDERS:
    print(f" - {os.path.abspath(folder)}")
