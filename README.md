# Steam 게임 가격과 인기도 분석

SteamSpy API와 Steam Store API 데이터를 `appid` 기준으로 병합해 가격, 무료 여부, 장르, 사용자 평가, 인기도의 관계를 분석하는 프로젝트입니다.

## 설치

```powershell
pip install -r requirements.txt
```

## 실행 순서

```powershell
python src/api/collect_steamspy.py
python src/api/collect_store.py
python src/merge_data.py
python src/analysis.py
```

## 생성 파일

- `data/steamspy_games.csv`
- `data/steam_store_games_001.csv` ~ `data/steam_store_games_005.csv`
- `data/merged_games.csv`
- `outputs/chart_free_vs_paid.png`
- `outputs/chart_price_vs_rating.png`
- `outputs/chart_genre_value.png`
- `outputs/chart_genre_heatmap.png`
