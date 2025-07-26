# 클라우드 배포 가이드

이 프로젝트는 여러 클라우드 플랫폼에 배포할 수 있습니다.

## Railway 배포 (추천 - 무료 티어 제공)

### 1단계: Railway 계정 생성
- https://railway.app 접속
- GitHub 계정으로 로그인

### 2단계: 프로젝트 배포
1. "New Project" → "Deploy from GitHub repo" 선택
2. 이 레포지토리 선택
3. 자동 배포 시작됨

### 3단계: 환경 변수 설정
Railway 대시보드에서 다음 환경 변수들을 추가:
```
OPENAI_API_KEY=your_openai_api_key
UNSPLASH_ACCESS_KEY=your_unsplash_key
TISTORY_USERNAME=your_tistory_username
TISTORY_PASSWORD=your_tistory_password
TISTORY_BLOG_NAME=your_blog_name
WEB_PASSWORD=your_web_password
```

### 4단계: 도메인 확인
- Railway가 자동으로 HTTPS 도메인 제공
- 핸드폰에서 접속하여 실제 포스팅 테스트

## Heroku 배포

### 1단계: Heroku 계정 생성
- https://heroku.com 가입

### 2단계: Heroku CLI 또는 웹 배포
1. GitHub 연동 활성화
2. 이 레포지토리 연결
3. 자동 배포 설정

### 3단계: Buildpack 설정
```bash
heroku buildpacks:add --index 1 heroku/python
heroku buildpacks:add --index 2 https://github.com/heroku/heroku-buildpack-chromedriver
heroku buildpacks:add --index 3 https://github.com/heroku/heroku-buildpack-google-chrome
```

### 4단계: 환경 변수 설정
Heroku 대시보드 또는 CLI로 동일한 환경 변수들 추가

## Render 배포

### 1단계: Render 계정 생성
- https://render.com 가입

### 2단계: Web Service 생성
1. "New" → "Web Service" 선택
2. GitHub 레포지토리 연결
3. 빌드 명령: `pip install -r requirements.txt`
4. 시작 명령: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

## 중요 사항

### Chrome WebDriver 설정
클라우드 환경에서는 다음 Chrome 옵션이 필수:
- `--no-sandbox`
- `--disable-dev-shm-usage`
- `--headless`
- `--disable-gpu`

### 보안
- 모든 API 키와 비밀번호는 환경 변수로 설정
- `.env` 파일은 로컬 개발용이며 배포 시 사용 안 됨

### 테스트
배포 후 핸드폰에서 접속하여:
1. 로그인 테스트
2. 콘텐츠 생성 테스트
3. 실제 티스토리 포스팅 테스트

### 비용
- Railway: 월 $5 (512MB RAM, 1GB 네트워크)
- Heroku: 월 $7 (Eco dyno)
- Render: 월 $7 (Starter plan)