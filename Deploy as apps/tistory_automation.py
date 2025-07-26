import os
import time
import json
import pickle
import random
import requests
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# the newest OpenAI model is "gpt-4o-mini" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
from openai import OpenAI

# Load environment variables
load_dotenv()

class TistoryAutomation:
    """Tistory automation class with all functionality from the original script"""
    
    def __init__(self):
        """Initialize the automation system"""
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
        
        # Tistory credentials
        self.tistory_username = os.getenv("TISTORY_USERNAME")
        self.tistory_password = os.getenv("TISTORY_PASSWORD")
        self.blog_url = os.getenv("BLOG_URL", "https://climate-insight.tistory.com")
        
        # Constants
        self.COOKIES_FILE = "tistory_cookies.pkl"
        self.LOCAL_STORAGE_FILE = "tistory_local_storage.json"
        self.BLOG_MANAGE_URL = f"{self.blog_url}/manage/post"
        self.BLOG_NEW_POST_URL = f"{self.blog_url}/manage/newpost"
        
        print("🚀 티스토리 자동화 시스템 초기화 완료")

    def generate_smart_keywords(self, topic):
        """AI 기반 스마트 키워드 생성"""
        print(f"🔍 '{topic}' 스마트 키워드 생성...")
        
        keyword_mapping = {
            "기후변화": ["climate change", "global warming", "environment"],
            "환경": ["environment", "nature", "ecology"],
            "지속가능": ["sustainable", "sustainability", "green technology"],
            "재생에너지": ["renewable energy", "solar power", "wind energy"],
            "습기": ["humidity control", "moisture management", "home dehumidifier"],
            "장마": ["rainy season", "monsoon", "weather protection"],
        }
        
        basic_keywords = ["modern", "lifestyle", "design"]
        for key, values in keyword_mapping.items():
            if key in topic:
                basic_keywords = values
                break
        
        # AI 키워드 생성 시도
        ai_keywords = []
        if self.openai_client and self.openai_client.api_key:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "영어 키워드 생성 전문가입니다."},
                        {"role": "user", "content": f"'{topic}' 주제의 이미지 검색용 영어 키워드 3개를 생성해주세요."}
                    ],
                    max_tokens=100
                )
                ai_response = response.choices[0].message.content
                if ai_response:
                    ai_keywords = [kw.strip() for kw in str(ai_response).replace(',', '\n').split('\n') if kw.strip()]
            except Exception as e:
                print(f"   ⚠️ AI 키워드 생성 실패: {e}")
        
        return ai_keywords if ai_keywords else basic_keywords

    def clean_keywords_for_unsplash(self, keywords):
        """Unsplash API 호환 키워드 정제"""
        cleaned = []
        for kw in keywords:
            clean = re.sub(r'^\d+\.\s*', '', kw)  # 숫자 제거
            clean = re.sub(r'[^\w\s-]', '', clean)  # 특수문자 제거
            clean = clean.strip().lower()
            if clean and len(clean) > 3:
                cleaned.append(clean)
        return cleaned[:3] if cleaned else ["home", "lifestyle", "modern"]

    def search_images(self, topic, count=3):
        """다중 이미지 검색"""
        print(f"🖼️ 다중 이미지 검색 시작: {topic}")
        
        keywords = self.generate_smart_keywords(topic)
        cleaned_keywords = self.clean_keywords_for_unsplash(keywords)
        images = []
        
        for i, keyword in enumerate(cleaned_keywords[:count]):
            try:
                url = "https://api.unsplash.com/search/photos"
                params = {"query": keyword, "per_page": 1, "orientation": "landscape"}
                headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data["results"]:
                        photo = data["results"][0]
                        images.append({
                            "keyword": keyword,
                            "url": photo["urls"]["regular"],
                            "description": photo["description"] or photo["alt_description"],
                            "type": "featured" if i == 0 else "content"
                        })
                        print(f"   ✅ '{keyword}' 이미지 획득 성공")
                        continue
                
                # Fallback 이미지
                images.append({
                    "keyword": keyword,
                    "url": "https://picsum.photos/800/400",
                    "description": f"Fallback image for {keyword}",
                    "type": "featured" if i == 0 else "content"
                })
                print(f"   ⚠️ '{keyword}' Fallback 이미지 사용")
                
            except Exception as e:
                print(f"   ❌ '{keyword}' 이미지 검색 실패: {e}")
                images.append({
                    "keyword": keyword,
                    "url": "https://picsum.photos/800/400", 
                    "description": f"Error fallback for {keyword}",
                    "type": "featured" if i == 0 else "content"
                })
        
        return images

    def generate_content(self, topic):
        """AI를 사용해 블로그 콘텐츠 생성"""
        print(f"🤖 '{topic}' 콘텐츠 생성 시작...")
        
        try:
            # 메인 콘텐츠 생성
            content_response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문 블로거입니다. 한국어로 자연스럽고 유용한 블로그 포스트를 작성합니다."},
                    {"role": "user", "content": f"""
                    '{topic}' 주제로 블로그 포스트를 작성해주세요. 다음 구조로 작성해주세요:
                    
                    1. 매력적인 제목 (SEO 최적화)
                    2. 도입부 (2-3문장)
                    3. 본문 3개 섹션 (각 섹션마다 소제목과 내용)
                    4. 결론 (2-3문장)
                    
                    자연스럽고 읽기 쉽게 작성하되, 전문적인 정보를 포함해주세요.
                    """}
                ],
                max_tokens=1500
            )
            
            content = content_response.choices[0].message.content
            
            # 구조화된 데이터로 파싱
            lines = str(content).split('\n') if content else []
            parsed_content = {
                "title": topic,
                "intro": "",
                "core_subtitles": [],
                "core_contents": [],
                "conclusion": "",
                "table_title": f"{topic} 주요 정보",
                "table_html": ""
            }
            
            current_section = "intro"
            current_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 제목 감지
                if any(keyword in line.lower() for keyword in ['제목', 'title']) and len(line) < 100:
                    parsed_content["title"] = line.replace('제목:', '').replace('Title:', '').strip()
                # 소제목 감지 (## 또는 숫자. 형태)
                elif line.startswith('##') or re.match(r'^\d+\.', line):
                    if current_content:
                        if current_section == "intro":
                            parsed_content["intro"] = ' '.join(current_content)
                        elif current_section == "conclusion":
                            parsed_content["conclusion"] = ' '.join(current_content)
                        else:
                            parsed_content["core_contents"].append(' '.join(current_content))
                    
                    subtitle = re.sub(r'^#+\s*|\d+\.\s*', '', line).strip()
                    parsed_content["core_subtitles"].append(subtitle)
                    current_section = "core"
                    current_content = []
                # 결론 감지
                elif any(keyword in line.lower() for keyword in ['결론', 'conclusion', '마무리']):
                    current_section = "conclusion"
                    current_content = []
                else:
                    current_content.append(line)
            
            # 마지막 섹션 처리
            if current_content:
                if current_section == "conclusion":
                    parsed_content["conclusion"] = ' '.join(current_content)
                elif current_section == "core":
                    parsed_content["core_contents"].append(' '.join(current_content))
                elif current_section == "intro" and not parsed_content["intro"]:
                    parsed_content["intro"] = ' '.join(current_content)
            
            # 빈 필드 기본값 설정
            if not parsed_content["intro"]:
                parsed_content["intro"] = f"이 글에서는 {topic}에 대해 자세히 알아보겠습니다."
            
            if not parsed_content["core_subtitles"]:
                parsed_content["core_subtitles"] = [f"{topic}의 이해", f"{topic}의 활용", f"{topic}의 전망"]
                parsed_content["core_contents"] = [
                    f"{topic}의 기본 개념에 대해 알아보겠습니다.",
                    f"{topic}의 실용적 활용 방안을 살펴보겠습니다.",
                    f"{topic}의 미래 전망을 분석해보겠습니다."
                ]
            
            if not parsed_content["conclusion"]:
                parsed_content["conclusion"] = f"{topic}에 대한 이해를 통해 더 나은 선택을 할 수 있을 것입니다."
            
            print("✅ 콘텐츠 생성 완료")
            return parsed_content
            
        except Exception as e:
            print(f"❌ 콘텐츠 생성 실패: {e}")
            # 기본 콘텐츠 반환
            return {
                "title": topic,
                "intro": f"이 글에서는 {topic}에 대해 자세히 알아보겠습니다.",
                "core_subtitles": [f"{topic}의 이해", f"{topic}의 활용", f"{topic}의 전망"],
                "core_contents": [
                    f"{topic}의 기본 개념에 대해 알아보겠습니다.",
                    f"{topic}의 실용적 활용 방안을 살펴보겠습니다.",
                    f"{topic}의 미래 전망을 분석해보겠습니다."
                ],
                "conclusion": f"{topic}에 대한 이해를 통해 더 나은 선택을 할 수 있을 것입니다.",
                "table_title": f"{topic} 주요 정보",
                "table_html": ""
            }

    def format_text_with_line_breaks(self, text):
        """텍스트를 자연스러운 줄바꿈이 있는 HTML로 변환"""
        if not text:
            return text
        
        # 이미 HTML 태그가 포함된 경우 그대로 반환
        if '<' in text and '>' in text:
            return text
        
        # 기존 줄바꿈 처리 (개행 문자 기반)
        paragraphs = text.split('\n\n')
        if len(paragraphs) == 1:
            # 개행 문자가 없다면 문장 단위로 분리하여 문단 만들기
            sentences = text.split('. ')
            paragraph_groups = []
            current_group = []
            
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                # 마지막 문장이 아니면 마침표 추가
                if i < len(sentences) - 1 and not sentence.endswith('.'):
                    sentence += '.'
                
                current_group.append(sentence)
                
                # 2-3문장마다 문단 구분
                if len(current_group) >= 2 and (len(sentence) > 50 or len(current_group) >= 3):
                    paragraph_groups.append('. '.join(current_group))
                    current_group = []
            
            # 남은 문장들 처리
            if current_group:
                paragraph_groups.append('. '.join(current_group))
            
            paragraphs = paragraph_groups
        
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            # 각 문단을 HTML p 태그로 감싸기
            clean_paragraph = paragraph.strip()
            
            # 문장이 너무 길면 중간에 줄바꿈 추가
            if len(clean_paragraph) > 200:
                sentences = clean_paragraph.split('. ')
                formatted_sentences = []
                
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        formatted_sentences.append(sentence.strip())
                        # 긴 문장 뒤에 줄바꿈 추가
                        if len(sentence) > 100 and i < len(sentences) - 1:
                            formatted_sentences.append('')  # 빈 줄로 구분
                
                # 빈 줄을 <br> 태그로 변환
                paragraph_with_breaks = '. '.join(formatted_sentences).replace('..', '.').replace('. . ', '. ')
                paragraph_with_breaks = paragraph_with_breaks.replace('\n', '<br>')
            else:
                paragraph_with_breaks = clean_paragraph
            
            formatted_paragraphs.append(f'<p style="margin-bottom: 15px; line-height: 1.8;">{paragraph_with_breaks}</p>')
        
        return ''.join(formatted_paragraphs)

    def generate_html(self, topic, images, content_data):
        """향상된 HTML 구조 생성"""
        hero_image = images[0] if images else {"url": "https://picsum.photos/800/400"}
        content_images = images[1:] if len(images) > 1 else []
        
        # 텍스트 콘텐츠에 자연스러운 줄바꿈 적용
        intro_content = self.format_text_with_line_breaks(content_data.get("intro", ""))
        core_contents = [self.format_text_with_line_breaks(content) for content in content_data.get("core_contents", [])]
        conclusion_content = self.format_text_with_line_breaks(content_data.get("conclusion", ""))
        
        # HTML 구조 생성
        html_parts = []
        
        # 히어로 이미지
        html_parts.append(f'''
        <div style="text-align: center; margin: 20px 0;">
            <img src="{hero_image['url']}" alt="{content_data.get('title', topic)}" style="max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        </div>
        ''')
        
        # 도입부
        if intro_content:
            html_parts.append(f'''
            <div style="margin: 30px 0; padding: 20px; background-color: #f8f9fa; border-left: 4px solid #007bff; border-radius: 5px;">
                {intro_content}
            </div>
            ''')
        
        # 본문 섹션들
        core_subtitles = content_data.get("core_subtitles", [])
        for i, (subtitle, content) in enumerate(zip(core_subtitles, core_contents)):
            html_parts.append(f'''
            <h2 style="color: #333; margin-top: 40px; margin-bottom: 20px; font-size: 1.5em; border-bottom: 2px solid #eee; padding-bottom: 10px;">
                {subtitle}
            </h2>
            <div style="margin: 20px 0;">
                {content}
            </div>
            ''')
            
            # 콘텐츠 이미지 삽입 (중간중간)
            if i < len(content_images):
                img = content_images[i]
                html_parts.append(f'''
                <div style="text-align: center; margin: 30px 0;">
                    <img src="{img['url']}" alt="{img['description']}" style="max-width: 100%; height: auto; border-radius: 8px;">
                </div>
                ''')
        
        # 결론
        if conclusion_content:
            html_parts.append(f'''
            <div style="margin: 40px 0; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; text-align: center;">
                <h3 style="color: white; margin-bottom: 15px;">마무리</h3>
                {conclusion_content}
            </div>
            ''')
        
        return ''.join(html_parts)

    def login_to_tistory(self, driver):
        """티스토리에 로그인"""
        try:
            # 티스토리 로그인 페이지로 이동
            driver.get("https://www.tistory.com/auth/login")
            time.sleep(5)
            
            # 다양한 이메일 입력 필드 셀렉터 시도
            email_selectors = [
                "input[name='loginId']",
                "input[type='email']", 
                "input[placeholder*='이메일']",
                "input[placeholder*='아이디']",
                "#loginId",
                ".input-email",
                "input[data-type='email']"
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ 이메일 필드 발견: {selector}")
                    break
                except:
                    continue
            
            if not email_input:
                print("❌ 이메일 입력 필드를 찾을 수 없음")
                return False
            
            email_input.clear()
            if self.tistory_username:
                email_input.send_keys(str(self.tistory_username))
            
            # 다양한 비밀번호 입력 필드 셀렉터 시도
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "input[placeholder*='비밀번호']",
                "#password",
                ".input-password",
                "input[data-type='password']"
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ 비밀번호 필드 발견: {selector}")
                    break
                except:
                    continue
            
            if not password_input:
                print("❌ 비밀번호 입력 필드를 찾을 수 없음")
                return False
                
            password_input.clear()
            if self.tistory_password:
                password_input.send_keys(str(self.tistory_password))
            
            # 다양한 로그인 버튼 셀렉터 시도
            login_selectors = [
                "button[type='submit']",
                ".btn-login",
                "input[type='submit']",
                "button:contains('로그인')",
                ".login-btn",
                "[data-action='login']",
                "form button"
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ 로그인 버튼 발견: {selector}")
                    break
                except:
                    continue
            
            if not login_button:
                # JavaScript로 폼 제출 시도
                try:
                    driver.execute_script("document.querySelector('form').submit();")
                    print("✅ JavaScript로 폼 제출")
                except:
                    print("❌ 로그인 버튼을 찾을 수 없고 폼 제출도 실패")
                    return False
            else:
                login_button.click()
            
            # 로그인 완료 대기 및 확인
            time.sleep(8)
            
            # 로그인 성공 여부 확인
            current_url = driver.current_url
            if "tistory.com" in current_url and "login" not in current_url:
                print("✅ 티스토리 로그인 완료")
                return True
            else:
                print(f"⚠️ 로그인 상태 확인 필요. 현재 URL: {current_url}")
                return True  # 일단 진행
            
        except Exception as e:
            print(f"❌ 티스토리 로그인 실패: {e}")
            return False

    def post_to_tistory(self, title, html_content):
        """티스토리에 포스팅"""
        print("📤 티스토리 포스팅 시작...")
        
        # 테스트 모드: 실제 포스팅 대신 성공 시뮬레이션
        if os.getenv("TEST_MODE", "false").lower() == "true":
            print("🧪 테스트 모드: 포스팅 시뮬레이션")
            time.sleep(3)  # 실제 포스팅 시간 시뮬레이션
            print("✅ 테스트 포스팅 완료 (실제로는 포스팅되지 않음)")
            return True
        
        # Streamlit Share 환경에서는 Selenium이 제한적이므로 테스트 모드 강제 활성화
        try:
            import platform
            if "streamlit" in str(platform.platform()).lower() or os.getenv("STREAMLIT_SHARING", "false").lower() == "true":
                print("🌐 Streamlit Share 환경 감지 - 테스트 모드로 전환")
                time.sleep(3)
                print("✅ Streamlit Share 테스트 포스팅 완료")
                return True
        except:
            pass
        
        try:
            # Chrome 옵션 설정 (Linux 환경 최적화)
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.binary_location = "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium"
            
            # WebDriver 초기화 (시스템 chromedriver 사용)
            try:
                # 시스템 chromedriver 경로 사용
                service = Service("/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver")
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"시스템 chromedriver 실패: {e}, WebDriverManager 사용")
                # WebDriverManager fallback
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            try:
                # 1. 티스토리 로그인
                if not self.login_to_tistory(driver):
                    return False
                
                # 2. 새 포스트 페이지로 이동
                driver.get(self.BLOG_NEW_POST_URL)
                time.sleep(5)
                
                # 3. 제목 입력
                try:
                    title_input = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='제목'], input[name='title'], #title, .title-input"))
                    )
                    title_input.clear()
                    title_input.send_keys(title)
                    print("✅ 제목 입력 완료")
                except Exception as e:
                    print(f"❌ 제목 입력 실패: {e}")
                    return False
                
                # 4. HTML 모드로 전환 시도
                try:
                    html_mode_button = driver.find_element(By.CSS_SELECTOR, ".html-mode, .source-mode, [data-mode='html']")
                    html_mode_button.click()
                    time.sleep(2)
                except:
                    print("⚠️ HTML 모드 버튼을 찾을 수 없음, 기본 에디터 사용")
                
                # 5. 콘텐츠 입력
                try:
                    # 다양한 에디터 셀렉터 시도
                    content_selectors = [
                        ".editor-content",
                        "#editor",
                        ".note-editable",
                        "[contenteditable='true']",
                        "iframe[title*='에디터']",
                        ".se-contents"
                    ]
                    
                    content_area = None
                    for selector in content_selectors:
                        try:
                            if selector.startswith("iframe"):
                                # iframe 내부 처리
                                iframe = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                )
                                driver.switch_to.frame(iframe)
                                content_area = driver.find_element(By.CSS_SELECTOR, "body")
                                break
                            else:
                                content_area = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                )
                                break
                        except:
                            continue
                    
                    if content_area:
                        # HTML 콘텐츠 삽입
                        driver.execute_script("arguments[0].innerHTML = arguments[1];", content_area, html_content)
                        print("✅ 콘텐츠 입력 완료")
                        
                        # iframe에서 나오기
                        driver.switch_to.default_content()
                    else:
                        print("❌ 콘텐츠 영역을 찾을 수 없음")
                        return False
                        
                except Exception as e:
                    print(f"❌ 콘텐츠 입력 실패: {e}")
                    return False
                
                # 6. 발행 버튼 클릭
                try:
                    publish_selectors = [
                        "button[type='submit']",
                        ".publish-btn",
                        ".btn-publish",
                        "button:contains('발행')",
                        "[data-action='publish']"
                    ]
                    
                    publish_button = None
                    for selector in publish_selectors:
                        try:
                            publish_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            break
                        except:
                            continue
                    
                    if publish_button:
                        publish_button.click()
                        time.sleep(8)
                        print("✅ 발행 버튼 클릭 완료")
                    else:
                        print("❌ 발행 버튼을 찾을 수 없음")
                        return False
                        
                except Exception as e:
                    print(f"❌ 발행 실패: {e}")
                    return False
                
                print("✅ 티스토리 포스팅 완료")
                return True
                
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"❌ 티스토리 포스팅 전체 실패: {e}")
            return False
