import os
import json
import requests
import urllib.parse
import hashlib
from http.server import BaseHTTPRequestHandler
from google import genai
from google.genai import types

def send_webhook_alert(query, results_count):
    # Vercel 환경 변수에 DISCORD_WEBHOOK_URL 을 설정해야 작동합니다.
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return
        
    data = {
        "content": f"🔍 **[저기요.ai] 새로운 검색 유입!**\n- 검색어: `{query}`\n- 반환된 맛집 수: {results_count}곳"
    }
    try:
        # 응답을 기다리지 않고 빠르게 전송 (timeout 2초)
        requests.post(webhook_url, json=data, timeout=2)
    except Exception as e:
        print(f"웹훅 전송 실패: {e}")

# ── 1. 네이버 이미지 검색 함수 (5장으로 확대) ──
def get_naver_image(query):
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    url = "https://openapi.naver.com/v1/search/image"
    # filter="all" 유지, 네이버 검색은 키워드 품질이 가장 중요합니다.
    params = {"query": query, "display": 5}
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

    def verify_restaurant(place):
        client_id = os.getenv("NAVER_CLIENT_ID")
        client_secret = os.getenv("NAVER_CLIENT_SECRET")
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }
        url = "https://openapi.naver.com/v1/search/local.json"
        params = {"query": f"{place.get('name')} {place.get('address')}", "display": 1}
        try:
            res = requests.get(url, params=params, headers=headers, timeout=3)
            return len(res.json().get('items', [])) > 0
        except Exception as e:
            print(f"네이버 검색 검증 실패: {e}")
            return False # API 통신 실패 시에는 안전하게 False 반환

    # [수정] 가짜 매장 생성 방지 및 search_keyword 필드 추가
    system_instruction = (
        "당신은 한국의 실제 존재하는 맛집 정보만 제공하는 검증기입니다. "
        "사용자가 입력한 지역과 조건에 맞는 '실제로 존재하는' 맛집 6곳을 추천하세요. 폐업했거나 가상의 식당을 지어내면 안 됩니다. "
        "1. 반드시 '네이버 지도'나 '카카오맵'에 등록된 매장만 추천하세요. "
        "2. 만약 해당 지역에 검색어에 맞는 유명한 맛집을 확신할 수 없다면, 가상의 이름을 지어내지 말고 '맛집 정보 없음'이라고 응답하세요. "
        "3. 결과는 오직 아래 JSON 배열로만 출력하세요."
        '[{"name": "식당명", "search_keyword": "동네이름 식당명 (예: 강남역 쉑쉑버거)", "desc": "메뉴 및 특징", "address": "실제 주소 또는 상세 위치", "category": "음식 분류"}]'

    )
    
    prompt_text = f'사용자 요청: "{user_input}"\n\n위 조건에 맞는 실존하는 맛집을 추천해주세요.'

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
        unique_str = f"{place.get('name')}{place.get('address')}"
        place['id'] = hashlib.md5(unique_str.encode()).hexdigest()
        
        # [수정] 긴 주소 대신 AI가 만든 최적화된 검색 키워드 사용
        search_query = place.get('search_keyword') or f"{place.get('name', '')}"
        place['images'] = get_naver_image(search_query)
        
        # [수정] 네이버 검색 링크도 최적화된 키워드로 전송 (타 지역 동명 이인 매장 방지)
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

            send_webhook_alert(user_input, len(results))

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