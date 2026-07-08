import os
import json
import requests
import urllib.parse
from http.server import BaseHTTPRequestHandler
from google import genai
from google.genai import types

# ── 1. 네이버 이미지 검색 함수 (5장으로 확대) ──
def get_naver_image(query):
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    url = "https://openapi.naver.com/v1/search/image"
    params = {"query": query, "display": 5}  # 1장 -> 5장
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    
    try:
        res = requests.get(url, params=params, headers=headers, timeout=5)
        if res.status_code == 200:
            items = res.json().get('items', [])
            if items:
                # 최대 5장의 이미지 URL을 리스트로 반환
                return [item['link'] for item in items]
    except:
        pass
    return ["https://via.placeholder.com/300?text=No+Image"]

# ── 2. AI 추천 로직 ──
def get_ai_recommendations(user_input):
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # 주소(address) 필드를 명시적으로 분리
    system_instruction = (
        "당신은 도보 이동 반경 내의 맛집 전문가입니다. "
        "사용자가 입력한 지역(위치)과 음식 종류를 바탕으로 맛집 5곳을 추천하세요. "
        "반드시 아래 JSON 배열 형식으로만 응답하세요: "
        '[{"id": "고유식별자(예: rest-1)", "name": "식당명", "desc": "메뉴 및 특징", "address": "실제 주소 또는 상세 위치", "category": "음식 분류"}]'
    )
    
    prompt_text = f'사용자 요청: "{user_input}"\n\n위 조건에 맞는 맛집을 추천해주세요.'

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL_NAME"), 
        contents=prompt_text,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
        ),
    )
    
    places = json.loads(response.text)
    
    for place in places:
        search_query = f"{place.get('address', place.get('location', ''))} {place.get('name', '')}"
        
        # 이미지 5장 배열 추가
        place['images'] = get_naver_image(search_query)
        # 네이버 모바일 검색 링크 동적 생성
        place['link'] = f"https://m.search.naver.com/search.naver?query={urllib.parse.quote(search_query)}"
        
    return places

# ── 3. Vercel 핸들러 ──
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            user_input = body.get('query', '맛집 추천해줘')
            results = get_ai_recommendations(user_input)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(results, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))