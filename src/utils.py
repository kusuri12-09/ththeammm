from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

STEAMSPY_CSV = DATA_DIR / "steamspy_games.csv"
STORE_CSV = DATA_DIR / "steam_store_games.csv"
MERGED_CSV = DATA_DIR / "merged_games.csv"
REPORT_MD = PROJECT_ROOT / "report.md"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)


def fetch_json(url: str, params: dict[str, Any] | None = None, timeout: int = 30) -> Any:
    response = requests.get(
        url,
        params=params,
        headers={
            "User-Agent": "steam-price-popularity-analysis/1.0",
            "Accept": "application/json",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def fetch_json_with_retry(
    url: str,
    params: dict[str, Any] | None = None,
    retries: int = 3,
    delay: float = 1.0,
    timeout: int = 30,
) -> Any:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            return fetch_json(url, params=params, timeout=timeout)
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
    raise RuntimeError(f"API request failed after {retries} attempts: {last_error}") from last_error


def parse_owners_range(value: str | float | int | None) -> tuple[int | None, int | None, int | None]:
    if value is None:
        return None, None, None

    text = str(value).replace(",", "").strip()
    if ".." not in text:
        return None, None, None

    left, right = [part.strip() for part in text.split("..", maxsplit=1)]
    try:
        low = int(left)
        high = int(right)
    except ValueError:
        return None, None, None

    return low, high, (low + high) // 2


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    ensure_dirs()
    pd.DataFrame(rows, columns=fieldnames).to_csv(path, index=False, encoding="utf-8-sig")


def split_genres(value: str | float | None) -> list[str]:
    if value is None:
        return []
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    return [genre.strip() for genre in text.split(";") if genre.strip()]
