# 프로젝트 명세서

## 프로젝트 주제

Steam 게임의 가격과 인기도의 상관관계 분석

---

## 프로젝트 개요

본 프로젝트는 Steam Store API와 SteamSpy API에서 수집한 데이터를 App ID(appid)를 기준으로 통합하여 게임 가격, 장르, 사용자 평가, 인기도 간의 관계를 분석하는 것을 목표로 한다.

분석 결과는 Python을 활용하여 시각화하며, 무료 게임과 유료 게임의 차이, 가격과 사용자 평가의 관계, 장르별 가성비 등을 탐구한다.

---

## 데이터셋

### 데이터셋 1 : Steam Store API

엔드포인트

```http
GET https://store.steampowered.com/api/appdetails?appids={appid}&cc=KR&l=korean
```

수집 컬럼

* appid
* name
* is_free
* price
* genres
* release_date

저장 파일

```text
steam_store_games.csv
```

---

### 데이터셋 2 : SteamSpy API

엔드포인트

```http
GET https://steamspy.com/api.php?request=all
```

수집 컬럼

* appid
* name
* owners
* positive
* negative
* average_forever

저장 파일

```text
steamspy_games.csv
```

---

## 데이터 통합

통합 기준

```text
appid
```

예시

```python
merged = steam_store_df.merge(
    steamspy_df,
    on="appid",
    how="inner"
)
```

통합 결과 파일

```text
merged_games.csv
```

---

## 파생 컬럼 생성

### 긍정률

```python
positive_rate = (
    positive /
    (positive + negative)
) * 100
```

---

### 총 리뷰 수

```python
review_count = positive + negative
```

---

### 가성비 지표

```python
value_score = (
    positive_rate *
    average_forever
) / price
```

가격이 0인 무료 게임은 별도 처리한다.

---

## 분석 목표

### 1. 무료 게임은 정말 더 인기 있을까?

사용 데이터

* is_free
* owners
* positive_rate

분석 내용

* 무료/유료 게임 평균 소유자 수 비교
* 무료/유료 게임 평균 긍정률 비교
* 무료 게임의 인기도 분석

시각화

* 막대그래프
* 박스플롯

---

### 2. 게임 가격과 유저 평가는 어떤 관계가 있을까?

사용 데이터

* price
* positive_rate

분석 내용

* 가격과 긍정률의 상관관계
* 가격대별 평균 긍정률 비교

시각화

* 산점도
* 회귀선

---

### 3. 어떤 장르가 가장 가성비가 좋을까?

사용 데이터

* genres
* price
* positive_rate
* average_forever

분석 내용

* 장르별 평균 가격
* 장르별 평균 긍정률
* 장르별 평균 플레이타임
* 장르별 가성비 비교

시각화

* 막대그래프
* 히트맵

---

## 구현 요구사항

### 데이터 수집

1. SteamSpy API에서 게임 목록 수집
2. 상위 1000~3000개 게임 선정
3. 각 게임의 appid 확보
4. Steam Store API에서 상세 정보 수집

### 데이터 처리

1. pandas 사용
2. CSV 저장
3. 결측치 제거
4. appid 기준 병합
5. 파생 컬럼 생성

### 데이터 분석

1. 상관계수 계산
2. 그룹별 평균 계산
3. 시각화 생성

### 시각화 라이브러리

* pandas
* matplotlib
* seaborn

---

## 프로젝트 폴더 구조

```text
project/
│
├── data/
│   ├── steam_store_games.csv
│   ├── steamspy_games.csv
│   └── merged_games.csv
│
├── src/
│   ├── api/
│   │   ├── collect_steamspy.py
│   │   └── collect_store.py
│   ├── merge_data.py
│   └── analysis.py
│
├── outputs/
│   ├── chart_free_vs_paid.png
│   ├── chart_price_vs_rating.png
│   └── chart_genre_value.png
│
└── report.md
```
