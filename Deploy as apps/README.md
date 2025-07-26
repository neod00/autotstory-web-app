# 🚀 티스토리 자동 포스팅 시스템

AI 기반 티스토리 블로그 자동 포스팅 시스템입니다. OpenAI GPT-4와 Unsplash API를 활용하여 주제만 입력하면 완전한 블로그 포스트를 생성하고 티스토리에 자동으로 업로드합니다.

## ✨ 주요 기능

- 🤖 **AI 콘텐츠 생성**: GPT-4를 활용한 고품질 블로그 콘텐츠 자동 생성
- 🖼️ **스마트 이미지 검색**: Unsplash API를 통한 관련 이미지 자동 검색 및 삽입
- 📝 **완전 자동화**: 제목부터 본문, 결론까지 완전한 포스트 생성
- 🎨 **아름다운 HTML 포맷**: 시각적으로 매력적인 블로그 포스트 레이아웃
- 🔐 **보안 인증**: 패스워드 기반 접근 제어

## 🚀 Streamlit Share에서 배포하기

### 1. 저장소 준비
```bash
git clone [your-repository-url]
cd [repository-name]
```

### 2. Streamlit Share에서 앱 배포
1. [Streamlit Share](https://share.streamlit.io/)에 접속
2. GitHub 저장소와 연결
3. 배포할 저장소 선택
4. 메인 파일: `app.py`

### 3. 환경변수 설정
Streamlit Share의 Settings > Secrets에서 다음 값들을 설정:

```toml
# 앱 보안 패스워드
APP_PASSWORD = "your_secure_password"

# OpenAI API 키 (필수)
OPENAI_API_KEY = "sk-your-openai-api-key"

# Unsplash API 키 (필수)
UNSPLASH_ACCESS_KEY = "your-unsplash-access-key"

# 티스토리 계정 정보 (선택사항)
TISTORY_USERNAME = "your-email@example.com"
TISTORY_PASSWORD = "your-password"
BLOG_URL = "https://your-blog.tistory.com"

# 테스트 모드 (true: 실제 포스팅 없이 테스트)
TEST_MODE = "false"
```

## 📋 API 키 획득 방법

### OpenAI API 키
1. [OpenAI Platform](https://platform.openai.com/)에 가입
2. API Keys 섹션에서 새 키 생성
3. 결제 정보 등록 (GPT-4 사용 시 필요)

### Unsplash API 키
1. [Unsplash Developers](https://unsplash.com/developers)에 가입
2. 새 애플리케이션 생성
3. Access Key 복사

## 🎯 사용 방법

1. 배포된 앱에 접속
2. 설정한 패스워드로 로그인
3. 블로그 주제 입력 (예: "기후변화 대응책", "재생에너지 동향")
4. 포스팅 시작 버튼 클릭
5. AI가 자동으로 콘텐츠 생성 및 이미지 검색
6. 티스토리에 자동 포스팅 완료

## 🔧 고급 설정

- **이미지 개수**: 포스트에 포함될 이미지 수 조절
- **정보 표 생성**: 주제 관련 정보 표 자동 생성
- **FAQ 섹션**: 자주 묻는 질문 섹션 추가
- **테스트 모드**: 실제 포스팅 없이 기능 테스트

## 📁 파일 구조

```
├── app.py                 # 메인 Streamlit 앱
├── tistory_automation.py  # 티스토리 자동화 로직
├── auth.py               # 인증 시스템
├── requirements.txt      # Python 패키지 의존성
├── .streamlit/
│   ├── config.toml      # Streamlit 설정
│   └── secrets.toml     # 환경변수 템플릿
└── README.md            # 이 파일
```

## ⚠️ 주의사항

- OpenAI API 사용 시 비용이 발생할 수 있습니다
- 티스토리 로그인 정보는 안전하게 보관하세요
- 테스트 모드로 먼저 기능을 확인해보세요
- Selenium 기반 브라우저 자동화는 일부 환경에서 제한될 수 있습니다

## 🆘 문제 해결

### 일반적인 문제들
- **API 키 오류**: Secrets 설정을 다시 확인하세요
- **브라우저 자동화 실패**: 테스트 모드로 먼저 확인하세요
- **이미지 검색 실패**: Unsplash API 키와 한도를 확인하세요

### 지원
문제가 있으시면 이슈를 등록해주세요.

---

🔥 **이제 Streamlit Share에서 바로 배포하실 수 있습니다!**