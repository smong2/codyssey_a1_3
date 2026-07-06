import requests
import os
import sys
import json
import re
from dotenv import load_dotenv

from google import genai
from google.genai import types

from pathlib import Path

# ── 환경 변수 최상단 로드 ──────────────────────────────────
load_dotenv()

# 1. 네이버 이미지 검색 함수 (이미 만든 것 활용)
def get_naver_image(query):
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    url = "https://openapi.naver.com/v1/search/image"
    params = {"query": query, "display": 1} # 1개만 가져옴
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    
    res = requests.get(url, params=params, headers=headers)
    if res.status_code == 200:
        items = res.json().get('items', [])
        return items[0]['link'] if items else "default_image_url"
    return "default_image_url"

# 2. 메인 실행 함수 (AI 응답 처리 프로세스)

def get_final_recommendation(user_input):
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt_text = f'사용자 요청: "{user_input}"\n\n맛집 5곳을 추천해주세요.'

    for attempt in range(1, 3):
        try:
            print(f"  🤖 Gemini 호출 중... (시도 {attempt}/2)")
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "당신은 맛집 추천 전문가입니다. 반드시 JSON 배열로만 응답하세요. "
                        "형식: [{\"name\": \"식당명\", \"description\": \"한 줄 설명\", "
                        "\"location\": \"동네명\", \"category\": \"음식 카테고리\", "
                        "\"price_range\": \"가격대\"}]"
                    ),
                    response_mime_type="application/json",
                    temperature=0.7,
                ),
            )

            result = json.loads(response.text)

            # 필수 키 검증
            required = ["name", "description", "location", "category", "price_range"]
            for item in result:
                if not all(k in item for k in required):
                    raise ValueError(f"필수 키 누락: {item}")

            # 네이버 이미지 추가
            for place in result:
                search_query = f"{place['location']} {place['name']}"
                place['image_url'] = get_naver_image(search_query)

            print(f"  ✅ 추천 완료: {[p['name'] for p in result]}")
            return result

        except (json.JSONDecodeError, ValueError) as e:
            print(f"  ⚠️ 파싱 실패 (시도 {attempt}/2): {e}")
            if attempt == 1:
                prompt_text += "\n\n주의: 순수 JSON 배열만 출력하세요. 다른 텍스트 절대 금지."
                continue
            else:
                print("  ❌ 2차 실패, 빈 리스트 반환")
                return []

        except Exception as e:
            print(f"  ❌ API 오류: {e}")
            return []

# 실행 테스트
results = get_final_recommendation("개포동역 맛집 추천해줘")
print(json.dumps(results, indent=4, ensure_ascii=False))
