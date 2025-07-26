# 티스토리 자동 포스팅 시스템

AI 기반 티스토리 블로그 자동 포스팅 웹 애플리케이션입니다.

## 주요 기능

- 🤖 OpenAI GPT를 활용한 AI 콘텐츠 자동 생성
- 🖼️ Unsplash API를 통한 고품질 이미지 자동 검색
- 📝 티스토리 자동 로그인 및 포스팅
- 📱 모바일 친화적 웹 인터페이스
- 🔐 보안 로그인 시스템

## 배포 방법

### Railway 배포 (추천)

1. [Railway](https://railway.app)에 가입
2. GitHub 계정으로 로그인
3. "New Project" → "Deploy from GitHub repo" 선택
4. 이 레포지토리 선택
5. 환경 변수 설정:
   ```
   OPENAI_API_KEY=your_openai_api_key
   UNSPLASH_ACCESS_KEY=your_unsplash_key
   TISTORY_USERNAME=your_tistory_username
   TISTORY_PASSWORD=your_tistory_password
   TISTORY_BLOG_NAME=your_blog_name
   WEB_PASSWORD=your_web_password
   ```

### 환경 변수 설명

- `OPENAI_API_KEY`: OpenAI API 키
- `UNSPLASH_ACCESS_KEY`: Unsplash API 액세스 키
- `TISTORY_USERNAME`: 티스토리 로그인 이메일
- `TISTORY_PASSWORD`: 티스토리 로그인 비밀번호
- `TISTORY_BLOG_NAME`: 티스토리 블로그 이름
- `WEB_PASSWORD`: 웹 애플리케이션 접근 비밀번호

## 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python
- **AI**: OpenAI GPT-4o
- **Image API**: Unsplash
- **Automation**: Selenium WebDriver
- **Deployment**: Railway/Heroku/Render

## 사용법

1. 배포된 웹사이트에 접속
2. 설정된 비밀번호로 로그인
3. 원하는 주제 입력
4. 이미지 개수, 표 생성, FAQ 옵션 선택
5. "포스팅 실행" 버튼 클릭
6. 자동으로 티스토리에 포스팅 완료

## 보안

- 웹 애플리케이션 접근은 비밀번호로 보호
- 모든 API 키는 환경 변수로 안전하게 관리
- HTTPS 자동 적용

## 지원 플랫폼

- Railway (무료/유료)
- Heroku (유료)
- Render (무료/유료)
- 기타 Python 지원 클라우드 플랫폼