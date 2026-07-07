import os
import json
import requests
from google import genai
from google.genai import types

# ── 1. 네이버 이미지 검색 함수 ──
def get_naver_image(query):
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    url = "https://openapi.naver.com/v1/search/image"
    params = {"query": query, "display": 1}
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    
    try:
        res = requests.get(url, params=params, headers=headers, timeout=5)
        if res.status_code == 200:
            items = res.json().get('items', [])
            return items[0]['link'] if items else "default_image_url"
    except:
        pass
    return "default_image_url"

# ── 2. AI 추천 로직 (프롬프트 관리 및 처리) ──
def get_ai_recommendations(user_input):
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # 역할을 분리하여 프롬프트 구성
    system_instruction = (
        "당신은 도보 이동 반경 내의 맛집 전문가입니다. "
        "사용자가 입력한 지역(위치)과 음식 종류를 바탕으로 도보로 걸어가기 무리 없는 거리의 맛집 5곳을 추천하세요. "
        "반드시 아래 JSON 배열 형식으로만 응답하세요: "
        '[{"name": "식당명", "description": "메뉴 및 특징", "location": "동네/위치", "category": "음식 분류"}]'
    )
    
    prompt_text = f'사용자 요청: "{user_input}"\n\n위 조건에 맞는 맛집을 추천해주세요.'

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt_text,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
        ),
    )
    
    # 데이터 파싱 및 이미지 결합
    places = json.loads(response.text)
    for place in places:
        search_query = f"{place.get('location', '')} {place.get('name', '')}"
        place['image_url'] = get_naver_image(search_query)
        
    return places

# ── 3. Vercel 핸들러 (역할: 입출력 관리) ──
def handler(request):
    try:
        # 1. 입력 처리
        if request.method == 'POST':
            body = json.loads(request.data.decode('utf-8'))
            user_input = body.get('user_input', '맛집 추천해줘')
        else:
            user_input = '맛집 추천해줘'

        # 2. 비즈니스 로직 호출
        results = get_ai_recommendations(user_input)

        # 3. 성공 응답
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(results, ensure_ascii=False)
        }

    except Exception as e:
        # 4. 에러 처리
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }