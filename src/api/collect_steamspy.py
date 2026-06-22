from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils import STEAMSPY_CSV, fetch_json_with_retry, parse_owners_range, write_csv


STEAMSPY_ALL_URL = "https://steamspy.com/api.php"


def collect_steamspy(limit: int = 1000) -> list[dict[str, object]]:
    payload = fetch_json_with_retry(STEAMSPY_ALL_URL, params={"request": "all"})
    games = list(payload.values())

    games.sort(
        key=lambda item: (
            int(item.get("positive") or 0) + int(item.get("negative") or 0),
            int(item.get("ccu") or 0),
        ),
        reverse=True,
    )

    rows: list[dict[str, object]] = []
    for item in games[:limit]:
        owners_min, owners_max, owners_avg = parse_owners_range(item.get("owners"))
        rows.append(
            {
                "appid": int(item.get("appid") or 0),
                "name": item.get("name") or "",
                "owners": item.get("owners") or "",
                "owners_min": owners_min,
                "owners_max": owners_max,
                "owners_avg": owners_avg,
                "positive": int(item.get("positive") or 0),
                "negative": int(item.get("negative") or 0),
                "average_forever": int(item.get("average_forever") or 0),
            }
        )

    return [row for row in rows if row["appid"]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect SteamSpy game data.")
    parser.add_argument("--limit", type=int, default=2000, help="Number of top games to save.")
    parser.add_argument("--output", default=str(STEAMSPY_CSV), help="Output CSV path.")
    args = parser.parse_args()

    rows = collect_steamspy(limit=args.limit)
    write_csv(
        Path(args.output),
        rows,
        ["appid", "name", "owners", "owners_min", "owners_max", "owners_avg", "positive", "negative", "average_forever"],
    )
    print(f"Saved {len(rows)} SteamSpy rows to {args.output}")


if __name__ == "__main__":
    main()
