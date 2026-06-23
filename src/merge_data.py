from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from utils import MERGED_CSV, STEAMSPY_CSV, STORE_CSV, ensure_dirs, resolve_data_file


def load_store_dataset(store_csv: Path) -> pd.DataFrame:
    store_csv = resolve_data_file(store_csv)
    chunk_paths = sorted(store_csv.parent.glob(f"{store_csv.stem}_*.csv"))
    if chunk_paths:
        return pd.concat((pd.read_csv(path) for path in chunk_paths), ignore_index=True)

    if store_csv.exists():
        return pd.read_csv(store_csv)

    raise FileNotFoundError(f"No Store CSV found: {store_csv} or {store_csv.stem}_*.csv")


def merge_data(
    store_csv: Path = STORE_CSV,
    steamspy_csv: Path = STEAMSPY_CSV,
    output_csv: Path = MERGED_CSV,
) -> pd.DataFrame:
    ensure_dirs()
    steamspy_csv = resolve_data_file(steamspy_csv)
    output_csv = resolve_data_file(output_csv)

    store_df = load_store_dataset(store_csv)
    steamspy_df = pd.read_csv(steamspy_csv)

    merged = store_df.merge(steamspy_df, on="appid", how="inner", suffixes=("_store", "_steamspy"))
    if "name_store" in merged.columns:
        merged["name"] = merged["name_store"].fillna(merged.get("name_steamspy"))

    numeric_columns = ["price", "owners_avg", "positive", "negative", "average_forever"]
    for column in numeric_columns:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")

    merged = merged.dropna(subset=["appid", "name", "is_free", "price", "genres", "owners_avg"])
    merged = merged[(merged["positive"] + merged["negative"]) > 0].copy()
    merged["review_count"] = merged["positive"] + merged["negative"]
    merged["positive_rate"] = (merged["positive"] / merged["review_count"]) * 100
    merged["value_score"] = pd.NA
    paid_mask = merged["price"] > 0
    playtime_mask = merged["average_forever"] > 0
    if playtime_mask.any():
        merged.loc[paid_mask & playtime_mask, "value_score"] = (
            merged.loc[paid_mask & playtime_mask, "positive_rate"]
            * merged.loc[paid_mask & playtime_mask, "average_forever"]
        ) / merged.loc[paid_mask & playtime_mask, "price"]
    else:
        merged.loc[paid_mask, "value_score"] = (
            merged.loc[paid_mask, "positive_rate"] * np.log1p(merged.loc[paid_mask, "review_count"])
        ) / (merged.loc[paid_mask, "price"] / 10000)

    columns = [
        "appid",
        "name",
        "is_free",
        "price",
        "genres",
        "release_date",
        "owners",
        "owners_min",
        "owners_max",
        "owners_avg",
        "positive",
        "negative",
        "average_forever",
        "review_count",
        "positive_rate",
        "value_score",
    ]
    merged = merged[columns].sort_values("owners_avg", ascending=False)
    merged.to_csv(output_csv, index=False, encoding="utf-8-sig")

    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge Steam Store and SteamSpy datasets.")
    parser.add_argument("--store", default=str(STORE_CSV), help="Steam Store CSV path.")
    parser.add_argument("--steamspy", default=str(STEAMSPY_CSV), help="SteamSpy CSV path.")
    parser.add_argument("--output", default=str(MERGED_CSV), help="Merged CSV path.")
    args = parser.parse_args()

    merged = merge_data(Path(args.store), Path(args.steamspy), Path(args.output))
    print(f"Saved {len(merged)} merged rows to {resolve_data_file(args.output)}")


if __name__ == "__main__":
    main()
