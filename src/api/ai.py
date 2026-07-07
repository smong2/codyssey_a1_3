import os
import json
import requests
from http.server import BaseHTTPRequestHandler
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
            return items[0]['link'] if items else "https://via.placeholder.com/300?text=No+Image"
    except:
        pass
    return "https://via.placeholder.com/300?text=No+Image"

# ── 2. AI 추천 로직 ──
def get_ai_recommendations(user_input):
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # JS가 기대하는 키값(id, desc)에 맞춰 프롬프트를 수정했습니다.
    system_instruction = (
        "당신은 도보 이동 반경 내의 맛집 전문가입니다. "
        "사용자가 입력한 지역(위치)과 음식 종류를 바탕으로 맛집 5곳을 추천하세요. "
        "반드시 아래 JSON 배열 형식으로만 응답하세요: "
        '[{"id": "고유식별자(예: rest-1)", "name": "식당명", "desc": "메뉴 및 특징", "location": "동네/위치", "category": "음식 분류"}]'
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
    
    # 데이터 파싱
    places = json.loads(response.text)
    
    for place in places:
        search_query = f"{place.get('location', '')} {place.get('name', '')}"
        # JS 코드에서 store.images.map()을 사용하므로, 리스트(배열) 형태로 넣어줍니다.
        place['images'] = [get_naver_image(search_query)]
        
    return places

# ── 3. Vercel 핸들러 (클래스 형태 필수!) ──
class handler(BaseHTTPRequestHandler):
    # do_POST 메서드가 있어야 405 Method Not Allowed 에러가 나지 않습니다.
    def do_POST(self):
        try:
            # 1. 입력 처리 (Vercel Python 규격)
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            # JS에서 넘겨준 키 이름은 'query' 입니다.
            user_input = body.get('query', '맛집 추천해줘')

            # 2. 비즈니스 로직 호출
            results = get_ai_recommendations(user_input)

            # 3. 성공 응답
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # 한글이 깨지지 않도록 ensure_ascii=False 사용
            self.wfile.write(json.dumps(results, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            # 4. 에러 처리
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))