import os
import json
import requests
import urllib.parse
import hashlib
from http.server import BaseHTTPRequestHandler
from google import genai
from google.genai import types

def send_webhook_alert(query, results_count):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return
    data = {
        "content": f"🔍 **[저기요.ai] 새로운 검색 유입!**\n- 검색어: `{query}`\n- 교차 검증 통과 맛집 수: {results_count}곳"
    }
    try:
        requests.post(webhook_url, json=data, timeout=2)
    except Exception as e:
        print(f"웹훅 전송 실패: {e}")

def get_naver_image(query):
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    url = "https://openapi.naver.com/v1/search/image"
    # 깨진 이미지가 많을 것을 대비해 15장을 먼저 가져옵니다.
    params = {"query": query, "display": 15} 
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    
    try:
        res = requests.get(url, params=params, headers=headers, timeout=3)
        if res.status_code == 200:
            items = res.json().get('items', [])
            valid_images = []
            
            # 봇(Bot) 차단을 막기 위해 일반 브라우저인 것처럼 위장합니다.
            img_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            
            for item in items:
                img_url = item['link']
                try:
                    # stream=True 옵션으로 이미지를 다 다운받지 않고 '존재 여부'만 빠르게 확인합니다.
                    check = requests.get(img_url, headers=img_headers, stream=True, timeout=1.5)
                    
                    # 200 OK 상태이고, 내용물이 'image'인 경우에만 통과시킵니다.
                    if check.status_code == 200 and check.headers.get('Content-Type', '').startswith('image/'):
                        valid_images.append(img_url)
                except Exception:
                    # 에러가 나거나 타임아웃이 발생한 이미지는 가차없이 버립니다.
                    continue
                
                # 유효한 이미지를 5장 찾으면 즉시 종료합니다.
                if len(valid_images) >= 5:
                    break
                    
            if valid_images:
                return valid_images
    except Exception as e:
        print(f"이미지 검색 에러: {e}")
        
    return ["https://via.placeholder.com/300?text=No+Image"]

def get_ai_recommendations(user_input):
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # ── 네이버 교차 검증 로직 (환각 방지) ──
    def verify_restaurant(place):
        client_id = os.getenv("NAVER_CLIENT_ID")
        client_secret = os.getenv("NAVER_CLIENT_SECRET")
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }
        url = "https://openapi.naver.com/v1/search/local.json"
        
        # 검색어는 식당명과 주소 앞부분을 조합하여 정확도 상승
        search_query = f"{place.get('name')} {place.get('address', '').split(' ')[0]}"
        params = {"query": search_query, "display": 1}
        
        try:
            res = requests.get(url, params=params, headers=headers, timeout=3)
            return len(res.json().get('items', [])) > 0
        except Exception:
            return False 

    system_instruction = (
        "당신은 한국의 실제 존재하는 맛집 정보만 제공하는 엄격한 검증기입니다. "
        "사용자가 입력한 지역과 조건에 맞는 '실제로 존재하는' 맛집을 최대 8곳 찾아주세요. "
        "1. 반드시 '네이버 지도'나 '카카오맵'에 실존하는 매장만 추천하세요. 가상의 식당을 지어내면 절대 안 됩니다. "
        "2. search_keyword는 네이버 이미지 검색의 정확도를 높이기 위해 '동네이름 + 식당명'으로만 심플하게 작성하세요. (예: '강남역 땀땀', '홍대 쵸쵸') "
        "3. 결과는 오직 아래 JSON 배열로만 출력하세요."
        '[{"name": "식당명", "search_keyword": "동네이름 식당명", "desc": "메뉴 및 특징", "address": "실제 주소", "category": "음식 분류"}]'
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
    
    try:
        places = json.loads(response.text)
    except json.JSONDecodeError:
        return [] # JSON 파싱 실패 시 빈 배열 리턴
    
    # ── [핵심 수정] 검증 통과한 맛집만 verified_places에 담기 ──
    verified_places = []
    
    for place in places:
        # 1. 실존 여부 팩트 체크
        if verify_restaurant(place):
            unique_str = f"{place.get('name')}{place.get('address')}"
            place['id'] = hashlib.md5(unique_str.encode()).hexdigest()
            
            search_query = place.get('search_keyword') or f"{place.get('name', '')}"
            place['images'] = get_naver_image(search_query)
            place['link'] = f"https://m.search.naver.com/search.naver?query={urllib.parse.quote(search_query)}"
            
            verified_places.append(place)
            
            # 최종 5개만 채우면 루프 조기 종료 (속도 최적화)
            if len(verified_places) >= 5:
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