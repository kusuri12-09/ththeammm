from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

from utils import MERGED_CSV, OUTPUT_DIR, ensure_dirs, resolve_data_file, split_genres

MPL_CONFIG_DIR = OUTPUT_DIR / ".matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

import matplotlib.pyplot as plt
import seaborn as sns


sns.set_theme(style="whitegrid")
plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans", "Arial"]
plt.rcParams["axes.unicode_minus"] = False


# 병합된 CSV를 읽고 분석에 필요한 컬럼 타입을 정리한다.
def load_dataset(path: Path = MERGED_CSV) -> pd.DataFrame:
    path = resolve_data_file(path)
    df = pd.read_csv(path)
    for column in ["price", "owners_avg", "positive_rate", "average_forever", "review_count", "value_score"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["is_free"] = df["is_free"].astype(str).str.lower().isin(["true", "1", "yes"])
    return df.dropna(subset=["price", "owners_avg", "positive_rate", "genres"])

# topic 1. 무료 게임은 정말 더 인기 있을까?
# 무료/유료 게임의 평균 소유자 수와 긍정률을 비교하는 막대 그래프 생성
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

# topic 2. 게임 가격과 유저 평가는 어떤 관계가 있을까?
# 유료 게임만 대상으로 가격과 긍정률의 관계를 산점도와 회귀선으로 표시한다.
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

# 여러 장르가 들어 있는 한 게임을 장르별 행으로 펼친다.
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

# topic 3. 어떤 장르가 가장 가성비가 좋을까?
# 장르별 가성비 점수를 집계하고 상위 장르 막대 그래프와 히트맵을 만든다.
def make_genre_value_chart(df: pd.DataFrame) -> tuple[Path, pd.DataFrame]:
    genres = genre_frame(df)
    paid_genres = genres.dropna(subset=["value_score"])

    # 평균은 극단값 영향을 받기 쉬워 순위는 중앙값 기준으로 정한다.
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

    # 서로 단위가 다른 지표를 같은 색상 범위에서 비교할 수 있도록 표준화한다.
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


# 전체 분석 흐름을 실행하고 생성된 차트 위치와 핵심 상관계수를 출력한다.
def analyze(input_csv: Path = MERGED_CSV) -> None:
    ensure_dirs()
    df = load_dataset(input_csv)
    make_free_vs_paid_chart(df)
    make_price_vs_rating_chart(df)
    make_genre_value_chart(df)

    price_corr = df.loc[df["price"] > 0, ["price", "positive_rate"]].corr().iloc[0, 1]
    print(f"Price/positive-rate correlation: {price_corr:.4f}")
    print(f"Charts saved to {OUTPUT_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze merged Steam game dataset.")
    parser.add_argument("--input", default=str(MERGED_CSV), help="Merged CSV path.")
    args = parser.parse_args()
    analyze(Path(args.input))


if __name__ == "__main__":
    main()
