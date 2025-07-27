import streamlit as st
import openai
import requests
import json
import re
import time
from datetime import datetime
import os
from typing import List, Dict, Optional
import random
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# URL 콘텐츠 추출 모듈 import
try:
    from url_extractor import generate_blog_from_url, URLContentExtractor
    URL_CONTENT_AVAILABLE = True
except ImportError as e:
    URL_CONTENT_AVAILABLE = False
    st.warning(f"⚠️ URL 콘텐츠 추출 모듈 로드 실패: {e}")

# 이미지 생성 모듈 import
try:
    from image_generator import get_multiple_images_v2, generate_image_html
    IMAGE_GENERATOR_AVAILABLE = True
except ImportError as e:
    IMAGE_GENERATOR_AVAILABLE = False
    st.warning(f"⚠️ 이미지 생성 모듈 로드 실패: {e}")
except Exception as e:
    IMAGE_GENERATOR_AVAILABLE = False
    st.warning(f"⚠️ 이미지 생성 모듈 초기화 실패: {e}")

# 트렌드 분석 모듈 import
try:
    from trend_analyzer import TrendAnalyzer
    TREND_ANALYZER_AVAILABLE = True
except ImportError as e:
    TREND_ANALYZER_AVAILABLE = False
    st.warning(f"⚠️ 트렌드 분석 모듈 로드 실패: {e}")

# 페이지 설정
st.set_page_config(
    page_title="AutoTstory - 블로그 자동 생성기",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링 - 더 현대적이고 깔끔하게 개선
st.markdown("""
<style>
    /* 전체 페이지 스타일 */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        padding: 2rem 0;
    }
    
    /* 헤더 스타일 */
    .main-header {
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(45deg, #667eea, #764ba2, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        letter-spacing: -0.02em;
    }
    
    .sub-header {
        font-size: 1.4rem;
        color: rgba(255, 255, 255, 0.9);
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 400;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 메인 컨테이너 스타일 */
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 0 2rem;
    }
    
    /* 카드 스타일 */
    .content-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 2.5rem;
        margin: 2rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .content-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 30px 80px rgba(0, 0, 0, 0.15);
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        width: 100%;
        border-radius: 15px;
        font-weight: 600;
        font-size: 1.1rem;
        padding: 0.8rem 1.5rem;
        background: linear-gradient(45deg, #667eea, #764ba2);
        border: none;
        color: white;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* 입력 필드 스타일 */
    .stTextInput > div > div > input {
        border-radius: 15px;
        border: 2px solid #e1e5e9;
        padding: 0.8rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 15px;
        border: 2px solid #e1e5e9;
        padding: 0.8rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* 사이드바 스타일 */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        margin: 1rem;
        padding: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    /* 성공/경고 메시지 스타일 */
    .success-message {
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
    }
    
    .warning-message {
        background: linear-gradient(45deg, #ff9800, #f57c00);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(255, 152, 0, 0.3);
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 15px;
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 0.5rem 1rem;
        margin: 0.25rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
    }
    
    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2.2rem;
        }
        .sub-header {
            font-size: 1.4rem;
        }
        .feature-card {
            padding: 1rem;
        }
    }
    
    /* 로딩 애니메이션 */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255,255,255,.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'tistory_logged_in' not in st.session_state:
    st.session_state.tistory_logged_in = False

# 티스토리 로그인 클래스
class TistoryLogin:
    def __init__(self, driver_instance):
        self.driver = driver_instance
    
    def complete_login(self):
        """완전 자동 로그인"""
        try:
            username = os.getenv("TISTORY_USERNAME")
            password = os.getenv("TISTORY_PASSWORD")
            
            if not username or not password:
                st.error("❌ 환경변수 설정 필요: TISTORY_USERNAME, TISTORY_PASSWORD")
                return False
            
            # 1단계: 로그인 페이지 접속
            self.driver.get("https://www.tistory.com/auth/login")
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(3)
            
            # 2단계: 카카오 버튼 클릭
            try:
                kakao_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn_login.link_kakao_id"))
                )
                kakao_btn.click()
            except:
                js_result = self.driver.execute_script("""
                    var links = document.querySelectorAll('a');
                    for (var i = 0; i < links.length; i++) {
                        if (links[i].textContent.includes('카카오계정으로 로그인')) {
                            links[i].click();
                            return true;
                        }
                    }
                    return false;
                """)
                if not js_result:
                    return False
            
            # 3단계: 카카오 페이지 로딩 대기
            WebDriverWait(self.driver, 15).until(
                lambda driver: "kakao" in driver.current_url.lower() or 
                              len(driver.find_elements(By.CSS_SELECTOR, "input[name='loginId']")) > 0
            )
            time.sleep(3)
            
            # 4단계: 아이디/비밀번호 입력
            username_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='loginId']")
            username_field.clear()
            username_field.send_keys(username)
            
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(password)
            
            # 5단계: 로그인 버튼 클릭
            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
            
            # 6단계: 2단계 인증 처리
            time.sleep(5)
            current_url = self.driver.current_url
            
            if "tmsTwoStepVerification" in current_url or "verification" in current_url.lower():
                st.info("📱 2단계 인증 필요! 핸드폰에서 카카오톡 알림을 확인하여 로그인을 승인해주세요!")
                if self.wait_for_approval(max_wait_minutes=3):
                    st.success("✅ 2단계 인증 승인 완료!")
                else:
                    st.error("❌ 2단계 인증 승인 시간 초과")
                    return False
            
            # 7단계: OAuth 승인
            time.sleep(3)
            try:
                continue_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn_agree[name='user_oauth_approval'][value='true']")
                if continue_btn and continue_btn.is_displayed():
                    continue_btn.click()
            except:
                pass
            
            # 8단계: 최종 확인
            time.sleep(5)
            if self.check_login_success():
                st.success("🎉 티스토리 로그인 성공!")
                return True
            else:
                st.error("❌ 로그인 실패")
                return False
                
        except Exception as e:
            st.error(f"❌ 로그인 중 오류: {e}")
            return False
    
    def wait_for_approval(self, max_wait_minutes=3):
        """2단계 인증 대기"""
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            current_url = self.driver.current_url
            if "tmsTwoStepVerification" not in current_url and "verification" not in current_url.lower():
                return True
            time.sleep(5)
        return False
    
    def check_login_success(self):
        """로그인 성공 확인"""
        try:
            current_url = self.driver.current_url
            return "login" not in current_url.lower() and "auth" not in current_url.lower()
        except:
            return False

# 티스토리 포스팅 함수들
def handle_alerts(driver, max_attempts=5, action="accept"):
    """알림 처리"""
    for _ in range(max_attempts):
        try:
            alert = driver.switch_to.alert
            if action == "accept":
                alert.accept()
            else:
                alert.dismiss()
            return True
        except:
            time.sleep(1)
    return False

def write_post_to_tistory(driver, blog_post):
    """티스토리에 글 작성"""
    try:
        # 새 글 작성 페이지로 이동
        driver.get("https://climate-insight.tistory.com/manage/newpost")
        time.sleep(5)
        handle_alerts(driver, action="accept")
        
        # 에디터 초기화
        driver.execute_script("""
            console.log("=== 에디터 초기화 시작 ===");
            
            // CodeMirror 에디터 초기화
            var cmElements = document.querySelectorAll('.CodeMirror');
            if (cmElements.length > 0) {
                for (var i = 0; i < cmElements.length; i++) {
                    if (cmElements[i].CodeMirror) {
                        cmElements[i].CodeMirror.setValue("");
                    }
                }
            }
            
            // 본문용 textarea 초기화
            var textareas = document.querySelectorAll('textarea');
            for (var i = 0; i < textareas.length; i++) {
                var ta = textareas[i];
                if (ta.id !== 'post-title-inp' && 
                    !ta.className.includes('textarea_tit') && 
                    ta.id !== 'tagText') {
                    ta.value = "";
                }
            }
            
            // TinyMCE 에디터 초기화
            if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                tinyMCE.activeEditor.setContent("");
            }
        """)
        time.sleep(2)
        
        # 제목 입력
        try:
            title_field = driver.find_element(By.CSS_SELECTOR, "#post-title-inp")
            title_field.clear()
            title_field.send_keys(blog_post['title'])
        except:
            pass
        
        # HTML 콘텐츠 입력
        try:
            # HTML 모드로 전환
            html_btn = driver.find_element(By.CSS_SELECTOR, "button[data-ke-name='html']")
            html_btn.click()
            time.sleep(2)
            
            # iframe 찾기
            iframe = driver.find_element(By.CSS_SELECTOR, "iframe.iframe_editor")
            driver.switch_to.frame(iframe)
            
            # HTML 콘텐츠 입력
            editor = driver.find_element(By.CSS_SELECTOR, "body")
            driver.execute_script("arguments[0].innerHTML = arguments[1];", editor, blog_post['content'])
            
            driver.switch_to.default_content()
        except Exception as e:
            st.error(f"HTML 콘텐츠 입력 실패: {e}")
            return False
        
        # 태그 입력
        try:
            tag_field = driver.find_element(By.CSS_SELECTOR, "#tagText")
            tag_field.clear()
            tag_field.send_keys(blog_post['tags'])
        except:
            pass
        
        return True
        
    except Exception as e:
        st.error(f"글 작성 실패: {e}")
        return False

def publish_post(driver):
    """글 발행"""
    try:
        # 발행 버튼 클릭
        publish_btn = driver.find_element(By.CSS_SELECTOR, "button.btn_publish")
        publish_btn.click()
        time.sleep(3)
        
        # 발행 확인
        confirm_btn = driver.find_element(By.CSS_SELECTOR, "button.btn_confirm")
        confirm_btn.click()
        time.sleep(5)
        
        return True
        
    except Exception as e:
        st.error(f"발행 실패: {e}")
        return False

# 기존 함수들 (간소화)
def clean_generated_content(content):
    """생성된 콘텐츠 정리"""
    if not content:
        return ""
    
    # HTML 태그 제거
    content = re.sub(r'<[^>]+>', '', content)
    
    # 불필요한 공백 정리
    content = re.sub(r'\n\s*\n', '\n\n', content)
    content = re.sub(r' +', ' ', content)
    
    # 문단 구분 정리
    content = re.sub(r'([.!?])\s*\n', r'\1\n\n', content)
    
    return content.strip()

def generate_blog_content(topic: str, custom_angle: str = "", use_ai: bool = True) -> Dict:
    """블로그 콘텐츠 생성"""
    try:
        if not use_ai or not openai.api_key:
            return generate_basic_content(topic, custom_angle)
        
        # AI 기반 콘텐츠 생성
        prompt = f"""
'{topic}' 주제로 블로그 글을 작성해주세요.

요구사항:
1. 제목: SEO 최적화된 매력적인 제목
2. 서론: 500-600자, 독자 관심 유도
3. 본론: 2000-2500자, 실용적 정보 제공
4. 결론: 300-400자, 핵심 요약
5. 키워드: SEO용 키워드 5-8개
6. 태그: 관련 태그 3-5개

{custom_angle if custom_angle else ""}

JSON 형식으로 응답해주세요:
{{
    "title": "제목",
    "introduction": "서론",
    "main_content": "본론",
    "conclusion": "결론",
    "keywords": ["키워드1", "키워드2"],
    "tags": ["태그1", "태그2"]
}}
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000,
            temperature=0.7
        )
        
        content_text = response.choices[0].message.content.strip()
        
        # JSON 파싱 시도
        try:
            content_data = json.loads(content_text)
        except:
            content_data = parse_text_content(content_text, topic)
        
        return content_data
        
    except Exception as e:
        st.error(f"콘텐츠 생성 중 오류 발생: {str(e)}")
        return generate_basic_content(topic, custom_angle)

def generate_basic_content(topic: str, custom_angle: str = "") -> Dict:
    """기본 템플릿 기반 콘텐츠 생성"""
    title = f"{topic} 완벽 가이드"
    introduction = f"""
{topic}에 대해 알아보시나요? 이 글에서는 {topic}의 모든 것을 자세히 살펴보겠습니다.

현대 사회에서 {topic}의 중요성은 날로 증가하고 있습니다. 많은 사람들이 이 주제에 대해 궁금해하고 있지만, 정확한 정보를 찾기 어려운 상황입니다.

이 글을 통해 {topic}에 대한 완전한 이해를 얻으실 수 있습니다. 실용적인 정보와 함께 실제 적용 가능한 팁들도 함께 제공하겠습니다.
""".strip()

    main_content = f"""
## {topic}의 기본 개념

{topic}는 현대 사회에서 매우 중요한 역할을 하고 있습니다. 이 섹션에서는 {topic}의 기본적인 개념과 정의에 대해 알아보겠습니다.

### 핵심 요소들

{topic}를 이해하기 위해서는 몇 가지 핵심 요소들을 파악해야 합니다:

1. **기본 원리**: {topic}의 근본적인 원리와 작동 방식
2. **주요 특징**: 다른 개념들과 구별되는 특징들
3. **적용 분야**: 실제로 활용되는 다양한 분야들

### 실무 적용 방법

이론적 이해뿐만 아니라 실제로 적용할 수 있는 방법들도 알아보겠습니다:

- **단계별 접근**: 체계적인 방법으로 {topic} 적용하기
- **주의사항**: 실무에서 주의해야 할 점들
- **성공 사례**: 실제 성공한 사례들을 통한 학습

## 최신 트렌드와 동향

{topic} 분야의 최신 동향과 트렌드를 파악하는 것도 중요합니다:

### 현재 상황

- **시장 동향**: 현재 {topic} 시장의 상황
- **기술 발전**: 최신 기술과의 결합
- **미래 전망**: 앞으로의 발전 방향

### 전문가 조언

이 분야의 전문가들이 제시하는 조언들도 함께 살펴보겠습니다:

- **전략적 접근**: 효과적인 {topic} 활용 전략
- **리스크 관리**: 주의해야 할 위험 요소들
- **성장 방향**: 지속적인 발전을 위한 방향성
""".strip()

    conclusion = f"""
{topic}에 대한 포괄적인 가이드를 마쳤습니다. 이 글을 통해 {topic}의 기본 개념부터 실무 적용까지 모든 것을 이해하셨을 것입니다.

앞으로 {topic}와 관련된 새로운 정보나 트렌드가 나올 때마다 이 글을 참고하시면 도움이 될 것입니다. 지속적인 학습과 적용을 통해 더욱 전문적인 지식을 쌓아가시기 바랍니다.

{topic}에 대한 추가 질문이나 궁금한 점이 있으시면 언제든지 문의해 주세요.
""".strip()

    keywords = [topic, f"{topic} 가이드", f"{topic} 방법", f"{topic} 팁", f"{topic} 정보"]
    tags = [topic, "가이드", "정보", "팁"]

    # 이미지 검색
    images = []
    if IMAGE_GENERATOR_AVAILABLE:
        images = get_multiple_images_v2(keywords, count=3)
    
    return {
        "title": title,
        "introduction": introduction,
        "main_content": main_content,
        "conclusion": conclusion,
        "keywords": keywords,
        "tags": tags,
        "images": images
    }

def parse_text_content(content_text: str, topic: str) -> Dict:
    """텍스트 기반 콘텐츠 파싱"""
    lines = content_text.split('\n')
    
    title = f"{topic} 완벽 가이드"
    introduction = ""
    main_content = ""
    conclusion = ""
    
    current_section = "introduction"
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if "제목:" in line or "Title:" in line:
            title = line.split(":", 1)[1].strip()
        elif "서론:" in line or "Introduction:" in line:
            current_section = "introduction"
        elif "본론:" in line or "Main:" in line:
            current_section = "main_content"
        elif "결론:" in line or "Conclusion:" in line:
            current_section = "conclusion"
        else:
            if current_section == "introduction":
                introduction += line + "\n"
            elif current_section == "main_content":
                main_content += line + "\n"
            elif current_section == "conclusion":
                conclusion += line + "\n"
    
    return {
        "title": title,
        "introduction": introduction.strip(),
        "main_content": main_content.strip(),
        "conclusion": conclusion.strip(),
        "keywords": [topic, f"{topic} 가이드"],
        "tags": [topic, "가이드"]
    }

def generate_html_content(content_data: Dict) -> str:
    """HTML 형식의 콘텐츠 생성"""
    # 이미지 HTML 생성
    images_html = ""
    if 'images' in content_data and content_data['images']:
        if IMAGE_GENERATOR_AVAILABLE:
            images_html = generate_image_html(content_data['images'])
    
    html_content = f"""
<div class="blog-post">
    <h1>{content_data['title']}</h1>
    
    {images_html}
    
    <div class="introduction">
        <h2>서론</h2>
        {content_data['introduction'].replace('\n', '<br>')}
    </div>
    
    <div class="main-content">
        {content_data['main_content'].replace('\n', '<br>')}
    </div>
    
    <div class="conclusion">
        <h2>결론</h2>
        {content_data['conclusion'].replace('\n', '<br>')}
    </div>
    
    <div class="keywords">
        <h3>키워드</h3>
        <p>{', '.join(content_data['keywords'])}</p>
    </div>
    
    <div class="tags">
        <h3>태그</h3>
        <p>{', '.join(content_data['tags'])}</p>
    </div>
</div>
"""
    return html_content

def main():
    # 헤더
    st.markdown('<h1 class="main-header">📝 AutoTstory</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI 기반 블로그 자동 생성기</p>', unsafe_allow_html=True)
    
    # 사이드바 설정
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        
        # OpenAI API 키 설정
        api_key = st.text_input("OpenAI API 키", type="password", help="AI 기능을 사용하려면 API 키를 입력하세요")
        if api_key:
            openai.api_key = api_key
            st.success("✅ API 키가 설정되었습니다")
        
        # 티스토리 로그인 정보
        st.markdown("### 🔐 티스토리 로그인")
        tistory_username = st.text_input("티스토리 아이디", type="default")
        tistory_password = st.text_input("티스토리 비밀번호", type="password")
        
        if tistory_username and tistory_password:
            os.environ["TISTORY_USERNAME"] = tistory_username
            os.environ["TISTORY_PASSWORD"] = tistory_password
            st.success("✅ 티스토리 로그인 정보가 설정되었습니다")
        
        # 모드 선택
        generation_mode = st.selectbox(
            "생성 모드",
            ["AI 기반 생성", "기본 템플릿 생성"],
            help="AI 기반 생성은 더 품질 높은 콘텐츠를 제공합니다"
        )
        
        st.markdown("---")
        st.markdown("### 📊 통계")
        if st.session_state.generated_content:
            st.metric("생성된 글자 수", len(str(st.session_state.generated_content)))
    
    # 메인 컨텐츠 - 중앙 정렬된 단일 컬럼
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">🎯 블로그 콘텐츠 생성</h2>', unsafe_allow_html=True)
    
    # 생성 방식 선택
    generation_type = st.radio(
        "생성 방식 선택",
        ["📝 주제 기반 생성", "🔗 URL 기반 생성"],
        help="주제를 직접 입력하거나 URL에서 콘텐츠를 추출할 수 있습니다"
    )
    
    if generation_type == "📝 주제 기반 생성":
        # 주제 기반 생성
        topic = st.text_input("주제 입력", placeholder="예: 인공지능, 마케팅 전략, 건강 관리...")
        custom_angle = st.text_area("특별한 각도나 요구사항", placeholder="원하는 특별한 관점이나 추가 요구사항이 있다면 입력하세요...")
        
        # 생성 버튼
        if st.button("🚀 블로그 생성하기", type="primary"):
            if not topic:
                st.error("주제를 입력해주세요!")
            else:
                with st.spinner("블로그 콘텐츠를 생성하고 있습니다..."):
                    use_ai = generation_mode == "AI 기반 생성"
                    content_data = generate_blog_content(topic, custom_angle, use_ai)
                    
                    if content_data:
                        st.session_state.generated_content = content_data
                        st.session_state.current_step = 1
                        st.success("✅ 블로그 콘텐츠가 생성되었습니다!")
    
    else:
        # URL 기반 생성
        url = st.text_input("URL 입력", placeholder="예: https://youtube.com/watch?v=..., https://news.naver.com/...")
        custom_angle = st.text_area("특별한 각도나 요구사항", placeholder="원하는 특별한 관점이나 추가 요구사항이 있다면 입력하세요...")
        
        if st.button("🚀 URL에서 블로그 생성하기", type="primary"):
            if not url:
                st.error("URL을 입력해주세요!")
            else:
                with st.spinner("URL에서 콘텐츠를 추출하고 블로그를 생성하고 있습니다..."):
                    if URL_CONTENT_AVAILABLE:
                        content_data = generate_blog_from_url(url, custom_angle)
                        if content_data:
                            st.session_state.generated_content = content_data
                            st.session_state.current_step = 1
                            st.success("✅ URL 기반 블로그 콘텐츠가 생성되었습니다!")
                    else:
                        st.error("URL 콘텐츠 추출 기능을 사용할 수 없습니다.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 생성된 콘텐츠 표시
    if st.session_state.generated_content:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">📄 생성된 콘텐츠</h2>', unsafe_allow_html=True)
        content = st.session_state.generated_content

        # 탭으로 구분
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 전체 보기", "📋 구조 보기", "🏷️ 메타데이터", "💾 다운로드", "🚀 티스토리 업로드"])

        with tab1:
            st.markdown(f"## {content['title']}")
            if 'images' in content and content['images']:
                st.markdown("### 🖼️ 관련 이미지")
                for i, image in enumerate(content['images']):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.image(image['url'], caption=f"{image['alt_text']} (by {image['photographer']})", use_column_width=True)
                    with col2:
                        st.markdown(f"**촬영자:** {image['photographer']}")
                        st.markdown(f"**크기:** {image['width']}x{image['height']}")
                        st.markdown(f"[Unsplash에서 보기]({image['unsplash_url']})")
            st.markdown("### 서론")
            st.write(content['introduction'])
            st.markdown("### 본론")
            st.write(content['main_content'])
            st.markdown("### 결론")
            st.write(content['conclusion'])

        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 제목")
                st.info(content['title'])
                st.markdown("#### 서론")
                st.text_area("서론 내용", content['introduction'], height=200, disabled=True)
            with col2:
                st.markdown("#### 본론")
                st.text_area("본론 내용", content['main_content'], height=300, disabled=True)
                st.markdown("#### 결론")
                st.text_area("결론 내용", content['conclusion'], height=150, disabled=True)

        with tab3:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 키워드")
                for keyword in content['keywords']:
                    st.markdown(f"- {keyword}")
            with col2:
                st.markdown("#### 태그")
                for tag in content['tags']:
                    st.markdown(f"- {tag}")

        with tab4:
            st.markdown("### 다운로드 옵션")
            json_data = json.dumps(content, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 JSON 파일 다운로드",
                data=json_data,
                file_name=f"blog_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            html_content = generate_html_content(content)
            st.download_button(
                label="🌐 HTML 파일 다운로드",
                data=html_content,
                file_name=f"blog_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html"
            )
            text_content = f"""
{content['title']}

서론:
{content['introduction']}

본론:
{content['main_content']}

결론:
{content['conclusion']}

키워드: {', '.join(content['keywords'])}
태그: {', '.join(content['tags'])}
"""
            st.download_button(
                label="📝 텍스트 파일 다운로드",
                data=text_content,
                file_name=f"blog_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

        with tab5:
            st.markdown("### 🚀 티스토리 자동 업로드")
            
            if not os.getenv("TISTORY_USERNAME") or not os.getenv("TISTORY_PASSWORD"):
                st.warning("⚠️ 티스토리 로그인 정보를 사이드바에서 설정해주세요.")
            else:
                if st.button("🔐 티스토리 로그인 및 업로드", type="primary"):
                    with st.spinner("티스토리에 로그인하고 글을 업로드하고 있습니다..."):
                        try:
                            # ChromeOptions 설정
                            options = webdriver.ChromeOptions()
                            options.add_argument("--disable-blink-features=AutomationControlled")
                            options.add_experimental_option("excludeSwitches", ["enable-automation"])
                            options.add_experimental_option("useAutomationExtension", False)
                            
                            # WebDriver 설정
                            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                            
                            try:
                                # 로그인
                                login = TistoryLogin(driver)
                                login_success = login.complete_login()
                                
                                if login_success:
                                    st.session_state.tistory_logged_in = True
                                    
                                    # 글 작성
                                    write_success = write_post_to_tistory(driver, content)
                                    
                                    if write_success:
                                        st.success("✅ 글 작성 완료!")
                                        
                                        # 발행 여부 확인
                                        if st.button("🚀 글 발행하기", type="primary"):
                                            publish_success = publish_post(driver)
                                            if publish_success:
                                                st.success("🎉 글 발행 완료!")
                                            else:
                                                st.error("❌ 발행 실패")
                                        else:
                                            st.info("📝 임시저장 상태로 유지됩니다.")
                                    else:
                                        st.error("❌ 글 작성 실패")
                                else:
                                    st.error("❌ 티스토리 로그인 실패")
                                    
                            finally:
                                driver.quit()
                                
                        except Exception as e:
                            st.error(f"❌ 업로드 중 오류: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 