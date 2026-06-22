from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils import DATA_DIR, STEAMSPY_CSV, fetch_json_with_retry, write_csv


STORE_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"
STORE_COLUMNS = ["appid", "name", "is_free", "price", "genres", "release_date"]


def normalize_price(data: dict[str, object]) -> float | None:
    if data.get("is_free") is True:
        return 0.0

    overview = data.get("price_overview")
    if not isinstance(overview, dict):
        return None

    final = overview.get("final")
    if final is None:
        return None

    try:
        return float(final) / 100
    except (TypeError, ValueError):
        return None


def parse_store_response(appid: int, payload: dict[str, object]) -> dict[str, object] | None:
    entry = payload.get(str(appid))
    if not isinstance(entry, dict) or not entry.get("success"):
        return None

    data = entry.get("data")
    if not isinstance(data, dict) or data.get("type") != "game":
        return None

    genres = data.get("genres")
    genre_text = ""
    if isinstance(genres, list):
        genre_text = ";".join(
            str(genre.get("description"))
            for genre in genres
            if isinstance(genre, dict) and genre.get("description")
        )

    release_date = data.get("release_date")
    release_text = ""
    if isinstance(release_date, dict):
        release_text = str(release_date.get("date") or "")

    return {
        "appid": appid,
        "name": data.get("name") or "",
        "is_free": bool(data.get("is_free")),
        "price": normalize_price(data),
        "genres": genre_text,
        "release_date": release_text,
    }


def chunk_output_path(output_dir: Path, chunk_number: int) -> Path:
    return output_dir / f"steam_store_games_{chunk_number:03d}.csv"


def collect_store_chunk(appids: pd.Series, delay: float = 0.35) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for index, appid in enumerate(appids.dropna().astype(int), start=1):
        payload = fetch_json_with_retry(
            STORE_APPDETAILS_URL,
            params={"appids": appid, "cc": "KR", "l": "korean"},
            retries=3,
            delay=1.0,
        )
        row = parse_store_response(appid, payload)
        if row:
            rows.append(row)

        if index % 50 == 0:
            print(f"Fetched {index} app details in current chunk, kept {len(rows)} games.")
        time.sleep(delay)

    return rows


def collect_store(
    input_csv: Path = STEAMSPY_CSV,
    output_dir: Path = DATA_DIR,
    chunk_size: int = 200,
    delay: float = 0.35,
    overwrite: bool = False,
) -> list[Path]:
    steamspy = pd.read_csv(input_csv)
    appids = steamspy["appid"].dropna().astype(int)
    output_paths: list[Path] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for chunk_index, start in enumerate(range(0, len(appids), chunk_size), start=1):
        output_path = chunk_output_path(output_dir, chunk_index)
        output_paths.append(output_path)

        if output_path.exists() and not overwrite:
            print(f"Skipped chunk {chunk_index}: {output_path} already exists.")
            continue

        chunk_appids = appids.iloc[start : start + chunk_size]
        print(f"Collecting chunk {chunk_index}: source rows {start + 1}-{start + len(chunk_appids)}")
        rows = collect_store_chunk(chunk_appids, delay=delay)
        write_csv(output_path, rows, STORE_COLUMNS)
        print(f"Saved {len(rows)} Store rows to {output_path}")

    return output_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Steam Store app details.")
    parser.add_argument("--input", default=str(STEAMSPY_CSV), help="SteamSpy CSV path.")
    parser.add_argument("--output-dir", default=str(DATA_DIR), help="Output directory for chunk CSV files.")
    parser.add_argument("--chunk-size", type=int, default=200, help="Number of source appids per output CSV.")
    parser.add_argument("--delay", type=float, default=0.35, help="Delay between requests in seconds.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing chunk CSV files.")
    args = parser.parse_args()

    paths = collect_store(
        input_csv=Path(args.input),
        output_dir=Path(args.output_dir),
        chunk_size=args.chunk_size,
        delay=args.delay,
        overwrite=args.overwrite,
    )
    print(f"Store chunk files: {len(paths)}")


if __name__ == "__main__":
    main()
