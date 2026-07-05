# 🚀 [가이드] 도커(Docker)부터 Vercel 배포까지 한 번에 끝내기

이 문서는 AI 웹 서비스를 개발하고 배포하는 전체 과정을 초보자의 눈높이에서 설명합니다.

---

## 1. 준비 단계 (가입 및 설치)

성공적인 배포를 위해 아래 항목들을 먼저 준비해 주세요.

- **필수 계정:** [GitHub](https://github.com/), [Vercel](https://vercel.com/) (GitHub 계정으로 Vercel 가입 권장)
- **필수 설치:** [Docker Desktop](https://www.docker.com/products/docker-desktop/), [VS Code](https://code.visualstudio.com/), [Git](https://git-scm.com/)
- **AI API 키:** OpenAI 또는 Anthropic API 키 (카드 등록 및 충전 필요)

---

## 2. 프로젝트 구조 (Folder Structure)

Vercel은 특정 폴더 구조를 기준으로 동작합니다. 아래 구조를 반드시 지켜주세요.

```text
my-ai-app/
├── api/                # 🐍 백엔드 (Python 서버 코드)
│   └── index.py        # Vercel이 인식하는 메인 파일
├── public/             # 🎨 프론트엔드 (HTML, CSS, JS)
│   └── index.html
├── .gitignore          # GitHub에 올리지 않을 파일 목록 (.env 등)
├── .env                # API 키 저장 (로컬 테스트용)
├── requirements.txt    # 필요한 파이썬 라이브러리 목록
├── Dockerfile          # 도커 이미지 설정
└── docker-compose.yml  # 도커 컨테이너 실행 설정
```

## 3. 도커(Docker) 설정 내 컴퓨터의 환경에 상관없이 동일하게 개발하기 위해 도커를 사용합니다.

① Dockerfile dockerfile

```
# 파이썬 3.9 이미지 사용
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /app

# 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 코드 복사
COPY . .

# 서버 실행 (로컬 테스트용)
CMD ["python", "api/index.py"]
```

② docker-compose.yml

```
version: '3.8'
services:
 web:
   build: .
   ports:
     - "8000:8000"
   volumes:
     - .:/app
   env_file:
     - .env
```

## 4. 백엔드 코드 작성 (Python/Flask)

① requirements.txt

```
flask
openai
python-dotenv
```

② api/index.py - 예제

```
from flask import Flask, request, jsonify
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_message}]
    )

    return jsonify({"reply": response.choices[0].message.content})

if __name__ == "__main__":
    app.run(port=8000)
```

## 5. GitHub에 코드 올리기

.gitignore 파일 생성: 아래 내용을 적어 API 키가 유출되지 않게 합니다.

```
.env
__pycache__/
*.pyc
```

터미널 명령 실행:

```
git init
git add .
git commit -m "Initial Commit"
git branch -M main
git remote add origin [내_저장소_주소]
git push -u origin main
```

## 6. Vercel 배포 및 환경 변수 설정

Vercel 접속: Vercel Dashboard에서 Add New -> Project.

Import: 내 GitHub 저장소를 선택하여 Import 버튼 클릭.

Environment Variables (중요):

- Settings -> Environment Variables 메뉴로 이동.

* Key: OPENAI_API_KEY
* Value: sk-xxxx... (내 실제 API 키)
* Add 버튼 클릭.

Deploy: 하단의 Deploy 버튼 클릭! 1~2분 뒤 배포된 URL이 생성됩니다.
