import os
import json
import requests
import urllib.parse
import hashlib
import concurrent.futures
from http.server import BaseHTTPRequestHandler
from google import genai
from google.genai import types

def send_webhook_alert(query, results_count):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url: return
    data = {"content": f"🔍 **[저기요.ai] 새로운 검색 유입!**\n- 검색어: `{query}`\n- 교차 검증 통과 맛집 수: {results_count}곳"}
    try:
        requests.post(webhook_url, json=data, timeout=2)
    except Exception:
        pass

def get_naver_image(query):
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    url = "https://openapi.naver.com/v1/search/image"
    params = {"query": query, "display": 10}
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    
    try:
        res = requests.get(url, params=params, headers=headers, timeout=2)
        if res.status_code == 200:
            items = res.json().get('items', [])
            valid_images = []
            img_headers = {"User-Agent": "Mozilla/5.0"}
            
            for item in items:
                img_url = item['link']
                try:
                    check = requests.get(img_url, headers=img_headers, stream=True, timeout=0.5)
                    if check.status_code == 200 and check.headers.get('Content-Type', '').startswith('image/'):
                        valid_images.append(img_url)
                except:
                    continue
                if len(valid_images) >= 3:
                    break
            if valid_images:
                return valid_images
    except Exception:
        pass
        
    # [수정 3] 의미 없는 placeholder URL 대신 빈 배열 리턴
    return []

def get_ai_recommendations(user_input):
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    def verify_restaurant(place):
        client_id = os.getenv("NAVER_CLIENT_ID")
        client_secret = os.getenv("NAVER_CLIENT_SECRET")
        headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
        url = "https://openapi.naver.com/v1/search/local.json"
        
        # [수정 2] 정확도 향상을 위해 AI가 만든 search_keyword로 네이버 검증 수행
        search_query = place.get('search_keyword') or f"{place.get('name')}"
        params = {"query": search_query, "display": 1}
        
        try:
            res = requests.get(url, params=params, headers=headers, timeout=2)
            return len(res.json().get('items', [])) > 0
        except Exception:
            return False 

    def process_single_place(place):
        if verify_restaurant(place):
            unique_str = f"{place.get('name')}{place.get('address')}"
            place['id'] = hashlib.md5(unique_str.encode()).hexdigest()
            search_query = place.get('search_keyword') or f"{place.get('name', '')}"
            place['images'] = get_naver_image(search_query)
            place['link'] = f"https://m.search.naver.com/search.naver?query={urllib.parse.quote(search_query)}"
            return place
        return None

    # [수정 1] AI에게 15곳을 뽑으라고 지시하고, 유명한 곳 위주로 제약 강화
    system_instruction = (
        "당신은 한국의 실제 존재하는 맛집 정보만 제공하는 엄격한 검증기입니다. "
        "사용자가 입력한 지역과 조건에 맞는 '실제로 존재하는 유명 맛집'을 15곳 찾아주세요. "
        "1. 반드시 '네이버 지도'나 '카카오맵'에 등록된 리뷰가 많은 검증된 매장만 추천하세요. 절대로 가상의 식당을 지어내지 마세요. "
        "2. search_keyword는 네이버 검색이 잘 되도록 '동네이름 식당명'으로 심플하게 작성하세요. "
        "3. desc 필드에는 '매장 추천 이유'를 먼저 작성하고, 그 뒤에 HTML 줄바꿈 태그(<br>)를 넣은 후 '대표 메뉴 2~3가지와 가격'을 작성하세요. "
        "4. 결과는 오직 아래 JSON 배열로만 출력하세요."
        '[{"name": "식당명", "search_keyword": "동네이름 식당명", "desc": "추천이유<br>메뉴 및 가격", "address": "실제 주소", "category": "음식 분류"}]'
    )
    
    prompt_text = f'사용자 요청: "{user_input}"\n\n위 조건에 맞는 실존하는 유명 맛집을 추천해주세요.'

    try:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL_NAME"), 
            contents=prompt_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
            ),
        )
        places = json.loads(response.text)
    except Exception:
        return [] 
    
    verified_places = []
    
    # 15개의 식당을 10개의 스레드로 초고속 검증
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(process_single_place, places)
        
        for res in results:
            if res:
                verified_places.append(res)
            # 검증을 통과한 진짜 맛집이 8개가 모이면 프론트로 리턴! (풍성한 리스트)
            if len(verified_places) >= 8:
                break
                
    return verified_places

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