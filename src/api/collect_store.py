from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils import STEAMSPY_CSV, STORE_CSV, fetch_json_with_retry, write_csv


STORE_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"


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


def collect_store(input_csv: Path = STEAMSPY_CSV, delay: float = 0.35) -> list[dict[str, object]]:
    steamspy = pd.read_csv(input_csv)
    rows: list[dict[str, object]] = []

    for index, appid in enumerate(steamspy["appid"].dropna().astype(int), start=1):
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
            print(f"Fetched {index} app details, kept {len(rows)} games.")
        time.sleep(delay)

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Steam Store app details.")
    parser.add_argument("--input", default=str(STEAMSPY_CSV), help="SteamSpy CSV path.")
    parser.add_argument("--output", default=str(STORE_CSV), help="Output CSV path.")
    parser.add_argument("--delay", type=float, default=0.35, help="Delay between requests in seconds.")
    args = parser.parse_args()

    rows = collect_store(input_csv=Path(args.input), delay=args.delay)
    write_csv(
        Path(args.output),
        rows,
        ["appid", "name", "is_free", "price", "genres", "release_date"],
    )
    print(f"Saved {len(rows)} Store rows to {args.output}")


if __name__ == "__main__":
    main()
