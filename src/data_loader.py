from pathlib import Path
import json
import pandas as pd


def load_carpark_data(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8-sig") as f:
        raw = json.load(f)

    if "car_park" not in raw:
        raise ValueError("JSON does not contain 'car_park' key.")

    df = pd.DataFrame(raw["car_park"])

    if df.empty:
        raise ValueError("Car park dataset is empty.")

    keep_cols = [
        "park_id",
        "name_en",
        "displayAddress_en",
        "latitude",
        "longitude",
        "district_en",
        "opening_status",
        "height",
        "remark_en",
        "website_en",
        "carpark_photo",
    ]

    existing_cols = [col for col in keep_cols if col in df.columns]
    df = df[existing_cols].copy()

    rename_map = {
        "name_en": "name",
        "displayAddress_en": "address",
        "district_en": "district",
        "remark_en": "remark",
        "website_en": "website",
    }
    df = df.rename(columns=rename_map)

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["height"] = pd.to_numeric(df["height"], errors="coerce")

    df = df.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)

    return df