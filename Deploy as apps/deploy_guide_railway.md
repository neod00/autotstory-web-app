# Railway 배포 실행 가이드

## 즉시 배포 방법

### 방법 1: GitHub 연동 배포 (추천)

1. **GitHub 레포지토리 생성**
   - GitHub에서 새 레포지토리 생성
   - 이 프로젝트의 모든 파일을 업로드

2. **Railway 배포**
   - https://railway.app 접속
   - GitHub으로 로그인
   - "New Project" → "Deploy from GitHub repo"
   - 생성한 레포지토리 선택

### 방법 2: Railway CLI 배포

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login

# 프로젝트 초기화
railway init

# 배포
railway up
```

### 방법 3: 직접 파일 업로드

1. Railway에서 "Empty Project" 생성
2. 로컬에서 파일들을 압축
3. Railway 대시보드에서 직접 업로드

## 환경 변수 설정 (필수)

Railway 프로젝트의 Variables 탭에서 설정:

```
OPENAI_API_KEY=sk-proj-[실제 키 값]
UNSPLASH_ACCESS_KEY=uQgwi8yVjCIJmD0NNU2_2oBIHUMI8UPn2B6blxwWbvQ
TISTORY_USERNAME=neod00@hanmail.net
TISTORY_PASSWORD=eInnern7305@
TISTORY_BLOG_NAME=climate-insight
WEB_PASSWORD=eInnern7305@
TEST_MODE=false
SESSION_TIMEOUT_HOURS=24
```

## 배포 후 확인사항

1. **도메인 확인**
   - Railway에서 자동 생성된 URL 확인
   - 형태: `https://your-app-name.up.railway.app`

2. **기능 테스트**
   - 웹사이트 접속 확인
   - 로그인 기능 확인
   - AI 콘텐츠 생성 테스트
   - 실제 티스토리 포스팅 테스트

## 예상 배포 시간

- 자동 빌드: 3-5분
- Chrome/ChromeDriver 설치: 2-3분
- Python 패키지 설치: 1-2분
- **총 예상 시간: 6-10분**

## 배포 성공 신호

✅ Build 완료
✅ Deploy 완료  
✅ 도메인 활성화
✅ Health Check 통과

## 문제 해결

**빌드 실패 시:**
- nixpacks.toml 설정 확인
- Python 버전 호환성 확인

**환경 변수 오류 시:**
- 모든 필수 변수 설정 확인
- 특수문자 이스케이프 확인

**Chrome 드라이버 오류 시:**
- nixpacks.toml의 chrome/chromedriver 설정 확인
- headless 모드 설정 확인