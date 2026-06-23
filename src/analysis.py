from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

from utils import MERGED_CSV, OUTPUT_DIR, REPORT_MD, ensure_dirs, resolve_data_file, split_genres

MPL_CONFIG_DIR = OUTPUT_DIR / ".matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

import matplotlib.pyplot as plt
import seaborn as sns


sns.set_theme(style="whitegrid")
plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans", "Arial"]
plt.rcParams["axes.unicode_minus"] = False


def markdown_table(df: pd.DataFrame, columns: list[str] | None = None) -> str:
    table = df.reset_index() if df.index.name else df.copy()
    if columns is not None:
        table = table[columns]

    header = "| " + " | ".join(str(column) for column in table.columns) + " |"
    divider = "| " + " | ".join("---" for _ in table.columns) + " |"
    rows = [
        "| " + " | ".join("" if pd.isna(value) else str(value) for value in row) + " |"
        for row in table.itertuples(index=False, name=None)
    ]
    return "\n".join([header, divider, *rows])


def load_dataset(path: Path = MERGED_CSV) -> pd.DataFrame:
    path = resolve_data_file(path)
    df = pd.read_csv(path)
    for column in ["price", "owners_avg", "positive_rate", "average_forever", "review_count", "value_score"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["is_free"] = df["is_free"].astype(str).str.lower().isin(["true", "1", "yes"])
    return df.dropna(subset=["price", "owners_avg", "positive_rate", "genres"])


def make_free_vs_paid_chart(df: pd.DataFrame) -> Path:
    summary = (
        df.assign(type=df["is_free"].map({True: "Free", False: "Paid"}))
        .groupby("type", as_index=False)
        .agg(mean_owners=("owners_avg", "mean"), mean_positive_rate=("positive_rate", "mean"))
    )

    output = OUTPUT_DIR / "chart_free_vs_paid.png"
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    sns.barplot(data=summary, x="type", y="mean_owners", ax=axes[0])
    axes[0].set_title("Average Owners")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Owners estimate")

    sns.barplot(data=summary, x="type", y="mean_positive_rate", ax=axes[1])
    axes[1].set_title("Average Positive Rate")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Positive rate (%)")
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def make_price_vs_rating_chart(df: pd.DataFrame) -> Path:
    paid = df[(df["price"] > 0) & df["positive_rate"].notna()].copy()
    output = OUTPUT_DIR / "chart_price_vs_rating.png"

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.regplot(
        data=paid,
        x="price",
        y="positive_rate",
        scatter_kws={"alpha": 0.35, "s": 20},
        line_kws={"color": "#d62728"},
        ax=ax,
    )
    ax.set_title("Price vs Positive Rate")
    ax.set_xlabel("Price (KRW)")
    ax.set_ylabel("Positive rate (%)")
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def genre_frame(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in df.iterrows():
        for genre in split_genres(row["genres"]):
            rows.append(
                {
                    "genre": genre,
                    "price": row["price"],
                    "positive_rate": row["positive_rate"],
                    "average_forever": row["average_forever"],
                    "value_score": row["value_score"],
                    "review_count": row["review_count"],
                }
            )
    return pd.DataFrame(rows)


def make_genre_value_chart(df: pd.DataFrame) -> tuple[Path, pd.DataFrame]:
    genres = genre_frame(df)
    paid_genres = genres.dropna(subset=["value_score"])

    summary = (
        paid_genres.groupby("genre", as_index=False)
        .agg(
            game_count=("genre", "size"),
            mean_price=("price", "mean"),
            mean_positive_rate=("positive_rate", "mean"),
            mean_playtime=("average_forever", "mean"),
            mean_value_score=("value_score", "mean"),
            median_value_score=("value_score", "median"),
        )
        .query("game_count >= 5")
        .sort_values("median_value_score", ascending=False)
        .head(12)
    )

    output = OUTPUT_DIR / "chart_genre_value.png"
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=summary, y="genre", x="median_value_score", ax=ax)
    ax.set_title("Top Genres by Median Value Score")
    ax.set_xlabel("Median value score")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)

    heatmap_data = summary.set_index("genre")[
        ["mean_price", "mean_positive_rate", "mean_playtime", "median_value_score"]
    ]
    if not heatmap_data.empty:
        scaled = (heatmap_data - heatmap_data.mean()) / heatmap_data.std(ddof=0).replace(0, 1)
        fig, ax = plt.subplots(figsize=(9, 6))
        sns.heatmap(scaled, cmap="viridis", annot=False, ax=ax)
        ax.set_title("Genre Metrics Heatmap (standardized)")
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / "chart_genre_heatmap.png", dpi=160)
        plt.close(fig)

    return output, summary


def write_report(df: pd.DataFrame, genre_summary: pd.DataFrame) -> None:
    free_paid = (
        df.assign(type=df["is_free"].map({True: "무료", False: "유료"}))
        .groupby("type")
        .agg(
            game_count=("appid", "size"),
            mean_owners=("owners_avg", "mean"),
            mean_positive_rate=("positive_rate", "mean"),
        )
        .round(2)
    )
    price_corr = df.loc[df["price"] > 0, ["price", "positive_rate"]].corr().iloc[0, 1]

    top_genres = markdown_table(genre_summary[["genre", "game_count", "median_value_score"]].round(2))

    REPORT_MD.write_text(
        "\n".join(
            [
                "# Steam 게임 가격과 인기도 상관관계 분석",
                "",
                "## 데이터 개요",
                f"- 분석 게임 수: {len(df):,}개",
                f"- 무료 게임 수: {int(df['is_free'].sum()):,}개",
                f"- 유료 게임 수: {int((~df['is_free']).sum()):,}개",
                "",
                "## 무료/유료 비교",
                markdown_table(free_paid),
                "",
                "## 가격과 긍정률",
                f"- 유료 게임 가격과 긍정률의 상관계수: {price_corr:.4f}",
                "",
                "## 장르별 가성비 상위",
                top_genres,
                "",
                "## 생성된 시각화",
                "- outputs/chart_free_vs_paid.png",
                "- outputs/chart_price_vs_rating.png",
                "- outputs/chart_genre_value.png",
                "- outputs/chart_genre_heatmap.png",
            ]
        ),
        encoding="utf-8",
    )


def analyze(input_csv: Path = MERGED_CSV) -> None:
    ensure_dirs()
    df = load_dataset(input_csv)
    make_free_vs_paid_chart(df)
    make_price_vs_rating_chart(df)
    _, genre_summary = make_genre_value_chart(df)
    write_report(df, genre_summary)

    price_corr = df.loc[df["price"] > 0, ["price", "positive_rate"]].corr().iloc[0, 1]
    print(f"Price/positive-rate correlation: {price_corr:.4f}")
    print(f"Charts saved to {OUTPUT_DIR}")
    print(f"Report saved to {REPORT_MD}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze merged Steam game dataset.")
    parser.add_argument("--input", default=str(MERGED_CSV), help="Merged CSV path.")
    args = parser.parse_args()
    analyze(Path(args.input))


if __name__ == "__main__":
    main()
