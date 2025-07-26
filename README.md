# 📝 AutoTstory - 블로그 자동 생성기

AI 기반 블로그 콘텐츠 자동 생성 웹 애플리케이션입니다.

## 🚀 주요 기능

- **🤖 AI 기반 콘텐츠 생성**: OpenAI GPT 모델을 활용한 고품질 블로그 글 생성
- **📝 SEO 최적화**: 검색엔진 최적화된 제목과 키워드 자동 생성
- **📊 구조화된 글 작성**: 서론, 본론, 결론이 체계적으로 구성된 글
- **🏷️ 메타데이터 자동 생성**: 키워드와 태그 자동 생성
- **📱 모바일 최적화**: 반응형 디자인으로 모든 디바이스에서 최적 경험
- **💾 다양한 형식 다운로드**: JSON, HTML, 텍스트 파일로 다운로드 가능

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **AI**: OpenAI GPT-4o-mini
- **Backend**: Python
- **Deployment**: Streamlit Cloud

## 📦 설치 및 실행

### 로컬 실행

1. **저장소 클론**
```bash
git clone <repository-url>
cd DeploybyStreamlit
```

2. **의존성 설치**
```bash
pip install -r requirements.txt
```

3. **환경 변수 설정**
```bash
# .env 파일 생성
OPENAI_API_KEY=your_openai_api_key_here
```

4. **앱 실행**
```bash
streamlit run app.py
```

### Streamlit Cloud 배포

1. **GitHub에 코드 푸시**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Streamlit Cloud에서 배포**
   - [share.streamlit.io](https://share.streamlit.io/) 접속
   - GitHub 계정 연결
   - 저장소 선택
   - 배포 설정 완료

## 🎯 사용 방법

### 1. 기본 사용법

1. **주제 입력**: 블로그 글의 주제를 입력합니다
2. **요구사항 추가** (선택사항): 특별한 관점이나 추가 요구사항을 입력합니다
3. **생성 모드 선택**: AI 기반 생성 또는 기본 템플릿 생성 중 선택
4. **생성 버튼 클릭**: 블로그 콘텐츠를 생성합니다

### 2. 생성된 콘텐츠 활용

- **전체 보기**: 생성된 글의 전체 내용을 확인
- **구조 보기**: 제목, 서론, 본론, 결론을 개별적으로 확인
- **메타데이터**: 키워드와 태그 정보 확인
- **다운로드**: JSON, HTML, 텍스트 파일로 다운로드

## ⚙️ 설정

### OpenAI API 키 설정

AI 기반 생성 기능을 사용하려면 OpenAI API 키가 필요합니다:

1. [OpenAI](https://platform.openai.com/)에서 API 키 발급
2. 앱의 사이드바에서 API 키 입력
3. AI 기반 생성 모드 선택

### 환경 변수

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## 📁 프로젝트 구조

```
DeploybyStreamlit/
├── app.py                 # 메인 Streamlit 앱
├── requirements.txt       # Python 의존성
├── README.md            # 프로젝트 문서
└── .env                 # 환경 변수 (로컬용)
```

## 🔧 주요 함수

### `generate_blog_content(topic, custom_angle, use_ai)`
- 주제와 요구사항을 받아 블로그 콘텐츠를 생성
- AI 모드와 기본 템플릿 모드 지원

### `generate_basic_content(topic, custom_angle)`
- AI 없이 기본 템플릿을 사용한 콘텐츠 생성

### `parse_text_content(content_text, topic)`
- AI 응답을 파싱하여 구조화된 데이터로 변환

### `generate_html_content(content_data)`
- 생성된 콘텐츠를 HTML 형식으로 변환

## 🎨 UI/UX 특징

- **반응형 디자인**: 모바일, 태블릿, 데스크톱 최적화
- **직관적인 인터페이스**: 사용자 친화적인 UI/UX
- **실시간 피드백**: 생성 과정과 결과를 실시간으로 확인
- **탭 기반 레이아웃**: 콘텐츠를 체계적으로 구분하여 표시

## 🚀 배포 가이드

### Streamlit Cloud 배포

1. **GitHub 저장소 준비**
   - 모든 파일이 올바른 위치에 있는지 확인
   - requirements.txt가 최신 상태인지 확인

2. **Streamlit Cloud 설정**
   - GitHub 계정 연결
   - 저장소 선택
   - 메인 파일 경로: `app.py`
   - Python 버전: 3.9+

3. **환경 변수 설정**
   - Streamlit Cloud 대시보드에서 환경 변수 설정
   - `OPENAI_API_KEY` 추가

### 로컬 개발

```bash
# 개발 서버 실행
streamlit run app.py --server.port 8501

# 디버그 모드
streamlit run app.py --logger.level debug
```

## 🔒 보안 고려사항

- API 키는 환경 변수로 관리
- 사용자 입력 데이터 검증
- HTTPS 통신 보장

## 📊 성능 최적화

- **캐싱**: 세션 상태를 활용한 결과 캐싱
- **비동기 처리**: 대용량 데이터 처리 최적화
- **메모리 관리**: 효율적인 메모리 사용

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요.

---

**AutoTstory** - AI 기반 블로그 자동 생성기 🚀 