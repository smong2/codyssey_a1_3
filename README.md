# A1-3. **AI 도움을 받아 내 아이디어를 실제 웹사이트로 만들기**



# 🍽️ 저기요.ai (Jogiyo.ai) - AI 맛집 추천 서비스

> "오늘 뭐 먹지? 고민할 시간에 AI에게 물어보세요!" 
>
>
>
>  사용자가 원하는 조건(위치, 분위기, 가성비 등)을 입력하면 AI가 상황에 맞는 **실존 맛집**을 추천해 주는 웹 서비스입니다.

**🔗 배포 URL**: `[여기에 Vercel 배포 URL을 입력하세요. 예: https://jogiyo-ai.vercel.app]`

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
  - 이미지 검색 실패 시 기본 대체 이미지(`via.placeholder.com`) 제공.

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



Vercel 환경 실행

[https://codyssey-a1-3-h7m29cs3u-smong2.vercel.app](https://codyssey-a1-3-h7m29cs3u-smong2.vercel.app/#)