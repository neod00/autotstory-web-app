# 🚀 Streamlit Cloud 배포 가이드

AutoTstory 블로그 자동 생성기를 Streamlit Cloud에 배포하는 방법을 안내합니다.

## 📋 사전 준비사항

### 1. GitHub 계정 및 저장소
- GitHub 계정이 필요합니다
- 새로운 저장소를 생성하거나 기존 저장소를 사용합니다

### 2. OpenAI API 키
- [OpenAI Platform](https://platform.openai.com/)에서 API 키를 발급받습니다
- API 키는 `sk-`로 시작하는 형태입니다

## 🔧 로컬 개발 환경 설정

### 1. 프로젝트 클론
```bash
git clone <your-repository-url>
cd DeploybyStreamlit
```

### 2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가합니다:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. 로컬 테스트
```bash
streamlit run app.py
```

## 🌐 Streamlit Cloud 배포

### 1. GitHub에 코드 푸시

```bash
# Git 초기화 (필요한 경우)
git init

# 파일 추가
git add .

# 커밋
git commit -m "Initial commit: AutoTstory Streamlit app"

# 원격 저장소 추가 (필요한 경우)
git remote add origin <your-repository-url>

# 푸시
git push -u origin main
```

### 2. Streamlit Cloud 설정

1. **Streamlit Cloud 접속**
   - [share.streamlit.io](https://share.streamlit.io/) 접속
   - GitHub 계정으로 로그인

2. **새 앱 생성**
   - "New app" 버튼 클릭
   - GitHub 저장소 선택
   - 브랜치 선택 (보통 `main` 또는 `master`)

3. **앱 설정**
   - **Main file path**: `app.py`
   - **Python version**: 3.9 이상 선택
   - **App URL**: 자동 생성되거나 커스텀 설정

### 3. 환경 변수 설정

Streamlit Cloud 대시보드에서:

1. **Settings** 탭 클릭
2. **Secrets** 섹션에서 환경 변수 추가:
   ```
   OPENAI_API_KEY = your_openai_api_key_here
   ```

### 4. 배포 확인

- **Deploy** 버튼 클릭
- 배포 상태 확인
- 제공된 URL로 앱 접속 테스트

## 🔧 고급 설정

### 1. 커스텀 도메인 설정

Streamlit Cloud Pro 계정이 필요한 경우:
1. **Settings** → **Custom domain**
2. 도메인 이름 입력
3. DNS 설정 업데이트

### 2. 성능 최적화

```python
# app.py에 추가
import streamlit as st

# 캐싱 설정
@st.cache_data
def expensive_computation():
    # 비용이 많이 드는 계산
    pass

# 세션 상태 관리
if 'data' not in st.session_state:
    st.session_state.data = []
```

### 3. 보안 설정

```python
# secrets.toml 파일 (로컬 개발용)
[secrets]
OPENAI_API_KEY = "your-api-key-here"
```

## 🐛 문제 해결

### 일반적인 문제들

#### 1. 배포 실패
- **원인**: 의존성 문제
- **해결**: `requirements.txt` 확인 및 업데이트

#### 2. API 키 오류
- **원인**: 환경 변수 설정 오류
- **해결**: Streamlit Cloud Secrets 재설정

#### 3. 앱 로딩 실패
- **원인**: 파일 경로 오류
- **해결**: Main file path 확인

### 디버깅 방법

1. **로컬 테스트**
   ```bash
   streamlit run app.py --logger.level debug
   ```

2. **Streamlit Cloud 로그 확인**
   - 앱 대시보드에서 "Logs" 탭 확인

3. **의존성 확인**
   ```bash
   pip list
   ```

## 📊 모니터링 및 유지보수

### 1. 성능 모니터링
- Streamlit Cloud 대시보드에서 사용량 확인
- 응답 시간 및 오류율 모니터링

### 2. 정기 업데이트
```bash
# 로컬에서 테스트 후 배포
git add .
git commit -m "Update: 버그 수정 및 기능 개선"
git push origin main
```

### 3. 백업 및 복구
- 정기적으로 코드 백업
- 환경 변수 및 설정 백업

## 🔒 보안 고려사항

### 1. API 키 보안
- API 키를 코드에 직접 포함하지 않음
- 환경 변수 또는 Streamlit Secrets 사용
- 정기적으로 API 키 로테이션

### 2. 사용자 데이터 보호
- 민감한 정보 수집 금지
- 데이터 암호화 적용
- GDPR 준수

### 3. 접근 제어
- 필요한 경우 인증 시스템 구현
- API 사용량 제한 설정

## 📈 확장성 고려사항

### 1. 트래픽 증가 대응
- 캐싱 전략 구현
- CDN 활용
- 로드 밸런싱 고려

### 2. 기능 확장
- 모듈화된 구조 유지
- API 설계 고려
- 마이크로서비스 아키텍처 검토

## 🎯 최적화 팁

### 1. 로딩 속도 개선
```python
# 이미지 최적화
st.image(image, use_column_width=True)

# 데이터 캐싱
@st.cache_data
def load_data():
    return pd.read_csv('data.csv')
```

### 2. 사용자 경험 개선
```python
# 로딩 표시
with st.spinner('처리 중...'):
    result = process_data()

# 성공 메시지
st.success('완료되었습니다!')
```

### 3. 모바일 최적화
```python
# 반응형 레이아웃
col1, col2 = st.columns([2, 1])

# 터치 친화적 버튼
st.button("확인", type="primary")
```

## 📞 지원 및 문의

### 문제 발생 시
1. **GitHub Issues** 활용
2. **Streamlit Community** 포럼 검색
3. **공식 문서** 참조

### 유용한 링크
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Cloud](https://share.streamlit.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs)

---

**성공적인 배포를 위한 체크리스트:**

- [ ] GitHub 저장소 준비 완료
- [ ] 모든 파일이 올바른 위치에 있음
- [ ] requirements.txt 최신 상태
- [ ] 환경 변수 설정 완료
- [ ] 로컬 테스트 통과
- [ ] 배포 후 기능 테스트 완료

🚀 **배포 성공!** 이제 전 세계 어디서나 AutoTstory를 사용할 수 있습니다! 