# A1-3. **AI 도움을 받아 내 아이디어를 실제 웹사이트로 만들기**

# 🍽️ 저기요.ai (Jogiyo.ai) - AI 맛집 추천 서비스

> "오늘 뭐 먹지? 고민할 시간에 AI에게 물어보세요!"
>
> 사용자가 원하는 조건(위치, 분위기, 가성비 등)을 입력하면 AI가 상황에 맞는 **실존 맛집**을 추천해 주는 웹 서비스입니다.

**🔗 배포 URL**: `[https://codyssey-a1-3-guapbrjby-smong2.vercel.app]`

## 💡 서비스 개요 및 타겟 사용자

매일 점심 메뉴를 고민하는 직장인 및 학생, 낯선 동네에서 빠르게 맛집을 찾고 싶은 여행객, 특정 목적(데이트, 회식 등)에 맞는 식당을 찾는 모든 사용자의 시간을 단축시켜 줍니다.

## 🛠️ 기술 스택 (Tech Stack)

- **Frontend**: HTML5, CSS3, Vanilla JavaScript (프레임워크 미사용)
- **Backend**: Vercel Serverless Functions (Python)
- **AI & API**: Google Gemini API, Naver Search API (Image/Local)
- **Deployment**: Vercel

## ✨ 핵심 기능 및 UX/운영 고도화

1. **자연어 기반 AI 맛집 추천**: "비 오는 날 어울리는 신촌 파전집" 등 자연어로 검색하면 AI가 문맥을 파악해 실존하는 매장 5곳을 찾아줍니다.
2. **실제 매장 이미지 매칭**: 백엔드에서 네이버 이미지 검색 API를 2차로 호출하여 실제 매장/음식 사진을 함께 제공합니다.
3. **즐겨찾기 (Local Storage)**: 마음에 드는 식당을 브라우저 로컬 스토리지에 영구 보관하고 모아볼 수 있습니다.
4. **UX 고도화**:

- **다크모드 지원**: 눈 피로도를 줄이기 위한 테마 변경 기능.
- **마이크로 인터랙션**: `alert()` 대신 자체 구현한 '토스트(Toast) 팝업'으로 부드러운 알림 제공.

5. **운영 자동화 (Discord 웹훅)**: 사용자가 검색을 수행할 때마다 관리자의 디스코드 채널로 검색어와 결과 수를 실시간 전송합니다.
6. **견고한 예외 처리 (Failover UX)**:

- 필수값 누락, 15초 타임아웃, 4xx/5xx API 오류 시 사용자 친화적인 안내 메시지 제공.

## 🔥 응용구현 추가 항목 : 트러블슈팅 및 기술적 주안점 (Advanced Features)

본 프로젝트는 단순한 API 호출을 넘어, 실제 서비스 수준의 UX 제공과 백엔드 최적화를 위해 다음과 같은 기술적 문제들을 해결했습니다.

### 1. Vercel Serverless 타임아웃(15초) 극복 및 병렬 처리 (Python)

- **문제**: AI가 추천한 식당의 실존 여부와 이미지 링크 유효성을 순차적(Sequential)으로 검증하다 보니, Vercel Serverless Function의 기본 제한 시간인 15초를 초과하여 타임아웃 에러가 빈번하게 발생했습니다.
- **해결**: Python의 `concurrent.futures.ThreadPoolExecutor`를 도입하여 **멀티 스레딩 기반의 병렬 처리 아키텍처**로 리팩토링했습니다. 15개의 후보 식당을 10개의 스레드가 동시에 검증하도록 하여 처리 시간을 **15초 이상에서 3~4초대로 획기적으로 단축**했습니다.

### 2. LLM 환각(Hallucination) 현상 방어를 위한 교차 검증 아키텍처

- **문제**: 생성형 AI(Gemini) 특성상 존재하지 않는 식당을 지어내거나 폐업한 식당을 추천하는 '환각 현상'이 발생하여 정보의 신뢰도가 떨어졌습니다.
- **해결**: 프롬프트 엔지니어링만으로 한계를 느끼고, 백엔드 로직에 **'네이버 Local Search API'를 활용한 교차 검증(Cross-Validation) 파이프라인**을 구축했습니다. AI가 반환한 결과를 곧바로 프론트엔드로 보내지 않고, 네이버 검색을 통해 실제 검색 결과(`items > 0`)가 존재하는 데이터만 필터링하여 사용자에게 100% 신뢰할 수 있는 실존 맛집만 제공하도록 무결성을 확보했습니다.

### 3. 고품질 이미지 렌더링 및 403 Forbidden 방어

- **문제**: 외부 블로그/카페의 이미지 링크를 가져올 때, 봇 접근 차단이나 삭제된 이미지로 인해 프론트엔드에서 엑스박스(Broken Image)가 빈번히 노출되었습니다.
- **해결**:
  1. **백엔드 사전 검증**: `requests` 모듈에 `stream=True`와 `timeout=0.5` 옵션을 주어 이미지를 다운로드하지 않고 HTTP Header 상태(Status 200 및 `Content-Type: image/`)만 초고속으로 검사해 유효한 링크만 선별했습니다.
  2. **프론트엔드 방어**: HTML `<head>`에 `<meta name="referrer" content="no-referrer" />`를 적용하여 타 사이트의 외부 링크 참조 차단 정책(403 Forbidden)을 우회하고, 검증 실패 시에는 레이아웃이 깨지지 않도록 "이미지 없음" Fallback UI를 구현했습니다.

### 4. 프론트엔드 상태 관리 및 UX 최적화 (Vanilla JS)

- **Client-Side 필터링**: API 통신 낭비를 막기 위해, 초기 로드된 `currentResults` 데이터를 전역 상태로 관리하여 카테고리 필터링 시 추가적인 서버 요청 없이 순수 자바스크립트의 `Array.prototype.filter()` 만으로 즉각적인 DOM 렌더링을 구현했습니다.
- **경쟁 상태(Race Condition) 제어**: 사용자의 중복 클릭 및 엔터 키 연타로 인한 API 중복 호출을 막기 위해, Promise 기반의 비동기 통신이 완료될 때까지 버튼 상태를 `disabled`로 잠그는 동시성 제어 로직을 적용했습니다.
- **Web Share API 및 통합 모달**: `navigator.share()`를 활용해 네이티브 공유 기능을 지원하고, 레이아웃을 깨뜨리지 않는 깔끔한 `iframe` 지도 모달과 다중 이미지 뷰어 슬라이드를 바닐라 자바스크립트만으로 구현했습니다.

## 🚀 프로젝트 구조

프론트엔드 정적 파일과 백엔드 API(Serverless)가 완벽히 분리된 구조입니다.

```
/
├── index.html       # 메인 프론트엔드 마크업 (SPA 구조)
├── css/
│   └── style.css    # 반응형 스타일 및 테마 (Dark/Light)
├── js/
│   └── script.js    # 프론트엔드 비즈니스 로직 (Fetch API, DOM 조작)
├── api/
│   └── ai.py        # Vercel Serverless 백엔드 로직 (Gemini & Naver API 통신)
├── requirements.txt # Python 패키지 의존성
└── vercel.json      # Vercel 배포 라우팅 설정 파일

```

## 🔒 환경 변수 설정 및 보안 (중요)

외부 API 통신은 보안을 위해 모두 백엔드(`api/ai.py`)에서 이루어지며, 브라우저(프론트엔드)에는 키가 절대 노출되지 않습니다. 로컬 실행 또는 Vercel 배포 시 아래 환경 변수를 반드시 등록해야 합니다.

```
# Google Gemini API
GEMINI_API_KEY="본인의_제미나이_API_키"
GEMINI_MODEL_NAME="gemini-3.1-flash-lite" # (또는 사용 모델)

# Naver API (이미지 검색용)
NAVER_CLIENT_ID="본인의_네이버_클라이언트_ID"
NAVER_CLIENT_SECRET="본인의_네이버_시크릿_키"

# (선택) Discord 웹훅 URL
DISCORD_WEBHOOK_URL="디스코드_웹훅_주소"

실제로는 이 항목은 vercel 에 등록해서 사용함.
```

⚠️ **보안 주의사항**: API 키가 GitHub 등에 노출될 경우 무단 사용으로 인한 요금 폭탄을 맞을 수 있습니다. 어떠한 경우에도 소스 코드 내부나 커밋 이력에 위 API 키를 직접 하드코딩하지 말고 `.env` 파일과 환경변수 시스템을 통해 안전하게 관리하세요.

## 배포/실행 방법

```
  Git hub 에 push 되면 vercel 에 hooking 으로 deployment 처리 됨
  deployment 이후 생성되는 url 로 서비스 접근 가능
```

## 스크린샷 증빙, 디스코드 알람(보너스과제 추가)

[스크린샷 페이지](./document/screenshot.md)
