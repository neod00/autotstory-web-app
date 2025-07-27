# AutoTstory - AI 기반 블로그 자동 생성기

트렌드에 맞게 세련되게 디자인된 AI 기반 블로그 자동 생성기입니다. 티스토리 자동 로그인 및 글 업로드 기능을 포함하고 있습니다.

## 🚀 주요 기능

### 🤖 AI 기반 콘텐츠 생성
- OpenAI GPT 모델을 활용한 고품질 블로그 글 생성
- SEO 최적화된 제목 및 키워드 자동 생성
- 구조화된 글 작성 (서론, 본론, 결론)

### 🔗 URL 기반 콘텐츠 추출
- YouTube 영상 자막 추출 및 블로그 글 변환
- 네이버 뉴스/블로그 콘텐츠 스크래핑
- 일반 웹사이트 콘텐츠 추출

### 🖼️ 이미지 자동 생성
- Unsplash API를 활용한 고품질 이미지 검색
- 키워드 기반 관련 이미지 자동 매칭
- 이미지 출처 및 저작권 정보 자동 포함

### 🔐 티스토리 자동 로그인
- 완전 자동화된 티스토리 로그인 시스템
- 카카오 계정 연동 지원
- 2단계 인증 자동 처리

### 🚀 자동 글 업로드
- 생성된 콘텐츠를 티스토리에 자동 업로드
- HTML 에디터 자동 전환 및 콘텐츠 입력
- 태그 및 메타데이터 자동 설정

### 📊 트렌드 분석
- 실시간 트렌드 키워드 수집
- 네이버/구글 트렌드 분석
- 계절별/카테고리별 맞춤 주제 제안

## 🎨 디자인 특징

### 세련된 UI/UX
- 그라데이션 배경과 모던한 카드 디자인
- 반응형 레이아웃 (모바일 최적화)
- 부드러운 애니메이션과 호버 효과
- 직관적인 탭 기반 인터페이스

### 사용자 친화적 기능
- 실시간 진행 상황 표시
- 에러 처리 및 복구 시스템
- 다운로드 옵션 (JSON, HTML, TXT)
- 미리보기 기능

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd DeploybyStreamlit
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정
`.env` 파일을 생성하고 다음 정보를 입력하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
TISTORY_USERNAME=your_tistory_username
TISTORY_PASSWORD=your_tistory_password
```

### 4. Streamlit 앱 실행
```bash
streamlit run app.py
```

## 🔧 사용 방법

### 1. 주제 기반 블로그 생성
1. 사이드바에서 OpenAI API 키 입력
2. "📝 주제 기반 생성" 선택
3. 블로그 주제 입력
4. 특별한 각도나 요구사항 입력 (선택사항)
5. "🚀 블로그 생성하기" 클릭

### 2. URL 기반 블로그 생성
1. "🔗 URL 기반 생성" 선택
2. YouTube, 네이버 뉴스, 블로그 URL 입력
3. 특별한 각도나 요구사항 입력 (선택사항)
4. "🚀 URL에서 블로그 생성하기" 클릭

### 3. 티스토리 자동 업로드
1. 사이드바에서 티스토리 로그인 정보 입력
2. 콘텐츠 생성 완료 후 "🚀 티스토리 업로드" 탭 선택
3. "🔐 티스토리 로그인 및 업로드" 클릭
4. 2단계 인증 승인 (필요시)
5. 글 발행 여부 선택

## 📁 파일 구조

```
DeploybyStreamlit/
├── app.py                 # 메인 Streamlit 앱
├── url_extractor.py       # URL 콘텐츠 추출 모듈
├── image_generator.py     # 이미지 생성 모듈
├── trend_analyzer.py      # 트렌드 분석 모듈
├── requirements.txt       # Python 의존성
└── README.md             # 프로젝트 문서
```

## 🔧 기술 스택

- **Frontend**: Streamlit
- **AI**: OpenAI GPT-4o-mini
- **Web Scraping**: Selenium, BeautifulSoup
- **Image API**: Unsplash API
- **Browser Automation**: Selenium WebDriver
- **Styling**: Custom CSS with modern design

## ⚠️ 주의사항

1. **API 키 보안**: OpenAI API 키와 티스토리 로그인 정보를 안전하게 보관하세요.
2. **사용량 제한**: OpenAI API와 Unsplash API의 사용량 제한을 확인하세요.
3. **웹 스크래핑**: 웹사이트의 이용약관을 준수하고 과도한 요청을 피하세요.
4. **자동화**: 티스토리 자동 업로드는 개인적인 용도로만 사용하세요.

## 🛠️ 개발 및 기여

### 로컬 개발 환경 설정
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
streamlit run app.py
```

### 코드 기여
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 지원

문제가 발생하거나 기능 요청이 있으시면 이슈를 생성해 주세요.

---

**AutoTstory** - AI로 더 스마트한 블로그 작성 🚀 