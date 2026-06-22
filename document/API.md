# 사용 API

본 프로젝트는 Steam 게임의 가격, 평점, 리뷰 수, 장르 등의 데이터를 수집하여 게임 가격과 인기도의 상관관계를 분석하기 위해 다음 API를 사용한다.

## 1. SteamSpy

### 개요

Steam에 등록된 전체 게임 목록을 조회하기 위한 공식 Steam Web API

### 엔드포인트

```http
GET https://steamspy.com/api.php?request=all
```

### 활용 목적

* Steam 게임 목록 수집
* App ID 확보
* 분석 대상 게임 선정

### 주요 응답 데이터

| 필드    | 설명       |
| ----- | -------- |
| appid | 게임 고유 ID |
| name  | 게임명      |

### 예시 응답

```json
{
  "applist": {
    "apps": [
      {
        "appid": 730,
        "name": "Counter-Strike 2"
      }
    ]
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

## 3. Steam Reviews API (appreviews)

### 개요

게임의 사용자 리뷰 정보를 조회하기 위한 API이다.

### 엔드포인트

```http
GET https://store.steampowered.com/appreviews/{appid}
```

### 요청 예시

```http
GET https://store.steampowered.com/appreviews/730?json=1
```

### 활용 목적

* 전체 리뷰 수 수집
* 긍정 리뷰 수 수집
* 부정 리뷰 수 수집
* 게임 평점 계산

### 주요 응답 데이터

| 필드             | 설명      |
| -------------- | ------- |
| total_reviews  | 전체 리뷰 수 |
| total_positive | 긍정 리뷰 수 |
| total_negative | 부정 리뷰 수 |

### 평점 계산식

```text
긍정률 = 긍정 리뷰 수 / 전체 리뷰 수 × 100
```

---

# API 활용 계획

본 프로젝트에서는 다음과 같이 API를 활용한다.

| 분석 주제                     | 사용 데이터            |
| ------------------------- | ----------------- |
| 무료 게임은 정말 더 인기 있을까?       | 무료 여부, 리뷰 수, 긍정률  |
| 게임 가격과 유저 평가는 어떤 관계가 있을까? | 가격, 리뷰 수, 긍정률     |
| 어떤 장르가 가장 가성비가 좋을까?       | 장르, 가격, 리뷰 수, 긍정률 |

이를 통해 게임 가격, 장르, 평점, 인기도 간의 관계를 시각화하고 분석한다.
