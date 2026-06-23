# Steam 게임 가격과 인기도 상관관계 분석

## 데이터 개요
- 분석 게임 수: 875개
- 무료 게임 수: 149개
- 유료 게임 수: 726개

## 무료/유료 비교
| type | game_count | mean_owners | mean_positive_rate |
| --- | --- | --- | --- |
| 무료 | 149 | 10137583.89 | 78.57 |
| 유료 | 726 | 4949724.52 | 87.2 |

## 가격과 긍정률
- 유료 게임 가격과 긍정률의 상관계수: -0.1385

## 장르별 가성비 상위
| genre | game_count | median_value_score |
| --- | --- | --- |
| 캐주얼 | 73 | 1263.45 |
| 스포츠 | 15 | 987.24 |
| 인디 | 280 | 565.41 |
| 앞서 해보기 | 26 | 535.26 |
| 레이싱 | 16 | 529.83 |
| 시뮬레이션 | 146 | 489.96 |
| 액션 | 502 | 455.17 |
| 어드벤처 | 303 | 453.57 |
| RPG | 188 | 429.31 |
| 전략 | 146 | 426.99 |
| 대규모 멀티플레이어 | 30 | 398.02 |

## 생성된 시각화
- outputs/chart_free_vs_paid.png
- outputs/chart_price_vs_rating.png
- outputs/chart_genre_value.png
- outputs/chart_genre_heatmap.png