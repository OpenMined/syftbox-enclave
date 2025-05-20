import os
from pathlib import Path
from sys import exit

import pandas as pd

DATA_DIR = os.environ["DATA_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

dataset_paths = [ Path(dataset_path) for dataset_path in DATA_DIR.split(",")]
total_carrots = 0
total_tomatoes = 0

for dataset_path in dataset_paths:
    if not dataset_path.exists():
        print("Warning: Dataset path does not exist:", dataset_path)
        exit(1)
    df = pd.read_csv(dataset_path / "crop_stock_data.csv")
    total_carrots += df[df["Product name"] == "Carrots"]["Quantity"].sum()
    total_tomatoes += df[df["Product name"] == "Tomatoes"]["Quantity"].sum()

with open(os.path.join(OUTPUT_DIR, "output.txt"), "w") as f:
    f.write(f"Total Carrots: {total_carrots}\n")
    f.write(f"Total Tomatoes: {total_tomatoes}\n")