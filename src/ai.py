import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

import requests
import json

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
    # [STEP 1] AI에게 맛집 추천 요청 (가정: AI가 아래와 같은 JSON 리스트를 반환함)
    # 실제로는 openai.ChatCompletion.create() 등을 호출합니다.
    ai_suggested_restaurants = [
        {"name": "밀란국수", "description": "샤브샤브와 칼국수가 맛있는 가성비 맛집", "location": "개포동"},
        {"name": "리애", "description": "두툼한 고기 맛이 일품인 프리미엄 돈카츠", "location": "개포동"},
        {"name": "대치떡볶이", "description": "추억의 맛을 느낄 수 있는 동네 떡볶이", "location": "개포동"}
    ]
    
    # [STEP 2] 각 식당별로 이미지 URL 붙이기
    final_results = []
    for place in ai_suggested_restaurants:
        search_query = f"{place['location']} {place['name']}" # 예: 개포동 밀란국수 음식 메뉴
        image_url = get_naver_image(search_query)
        
        # 데이터 합치기
        place['image_url'] = image_url
        final_results.append(place)
    
    return final_results

# 실행 테스트
results = get_final_recommendation("개포동역 맛집 추천해줘")
print(json.dumps(results, indent=4, ensure_ascii=False))
