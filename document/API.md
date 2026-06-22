# 데이터셋 통합 방법

본 프로젝트는 Steam Store API와 SteamSpy API에서 수집한 데이터를 App ID(appid)를 기준으로 통합한다.

Steam Store API에서는 게임의 가격, 무료 여부, 장르, 출시일 정보를 수집하며, SteamSpy API에서는 소유자 수 추정치, 긍정/부정 리뷰 수, 평균 플레이타임 정보를 수집한다.

이후 두 데이터셋을 appid를 기준으로 결합하여 가격, 평점, 장르, 인기도 간의 관계를 분석한다.

# 사용 API

본 프로젝트는 Steam 게임의 가격, 평점, 리뷰 수, 장르 등의 데이터를 수집하여 게임 가격과 인기도의 상관관계를 분석하기 위해 다음 API를 사용한다.

## 1. SteamSpy

### 개요

Steam 게임의 소유자 수 추정치, 리뷰 수, 평균 플레이타임, 장르 등의 데이터를 제공하는 제3자 API

### 엔드포인트

```http
GET https://steamspy.com/api.php?request=all
```

### 활용 목적

- Steam 게임 목록 수집
- App ID 확보
- 소유자 수 추정치 수집
- 긍정/부정 리뷰 수 수집
- 평균 플레이타임 수집

### 주요 응답 데이터

| 필드              | 설명          |
| --------------- | ----------- |
| appid           | 게임 고유 ID    |
| name            | 게임명         |
| owners          | 추정 소유자 수    |
| positive        | 긍정 리뷰 수     |
| negative        | 부정 리뷰 수     |
| average_forever | 평균 플레이타임(분) |

### 예시 응답

```json
{
  "730": {
    "appid": 730,
    "name": "Counter-Strike: Global Offensive",
    "developer": "Valve",
    "publisher": "Valve",
    "score_rank": "",
    "positive": 7642084,
    "negative": 1173003,
    "userscore": 0,
    "owners": "100,000,000 .. 200,000,000",
    "average_forever": 0,
    "average_2weeks": 0,
    "median_forever": 0,
    "median_2weeks": 0,
    "price": "0",
    "initialprice": "0",
    "discount": "0",
    "ccu": 1013936
  }
}
```

---

## 2. Steam Store API (appdetails)

### 개요

특정 게임의 상세 정보를 조회하기 위한 Steam Store API이다.

### 엔드포인트

```http
GET https://store.steampowered.com/api/appdetails
```

### 요청 예시

```http
GET https://store.steampowered.com/api/appdetails?appids=730&cc=KR&l=korean
```

### 활용 목적

* 게임 가격 수집
* 무료 게임 여부 확인
* 장르 정보 수집
* 출시일 수집

### 주요 응답 데이터

| 필드              | 설명    |
| --------------- | ----- |
| name            | 게임명   |
| is_free         | 무료 여부 |
| price_overview  | 가격 정보 |
| genres          | 장르    |
| release_date    | 출시일   |
| recommendations | 추천 수  |

---

# API 활용 계획

본 프로젝트에서는 다음과 같이 API를 활용한다.

| 분석 주제                     | 사용 데이터                |
| ------------------------- | --------------------- |
| 무료 게임은 정말 더 인기 있을까?       | 무료 여부, 소유자 수, 긍정률     |
| 게임 가격과 유저 평가는 어떤 관계가 있을까? | 가격, 긍정률               |
| 어떤 장르가 가장 가성비가 좋을까?       | 장르, 가격, 평균 플레이타임, 긍정률 |

이를 통해 게임 가격, 장르, 평점, 인기도 간의 관계를 시각화하고 분석한다.
