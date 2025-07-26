import os
import time
import json
import pickle
import random
import openai
import requests
import re
import urllib.parse
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path

# 이미지 자동 검색 (Unsplash API 예시)
def get_keyword_image_url(keyword):
    # API 키를 직접 코드에 입력 (임시 해결책)
    UNSPLASH_ACCESS_KEY = "uQgwi8yVjCIJmD0NNU2_2oBIHUMI8UPn2B6blxwWbvQ"
    
    # 1. 한글 키워드를 영어로 완전히 변환 (반드시 영어 키워드 사용)
    english_keyword = translate_to_english(keyword)
    
    # 한글이 포함된 경우(번역 실패) 기본 키워드로 대체
    for char in english_keyword:
        if ord(char) > 127:  # ASCII 범위를 벗어나는 문자(한글 등)가 있는지 확인
            print(f"경고: 영어로 변환되지 않은 한글 문자 발견. 기본 키워드 사용")
            english_keyword = "nature landscape"
            break
    
    print(f"Unsplash API 검색: 원래 키워드='{keyword}', 영어 키워드='{english_keyword}'")
    
    # 첫 번째 시도: 변환된 영어 키워드로 검색
    image_url = try_get_image(english_keyword, UNSPLASH_ACCESS_KEY)
    
    # 실패 시 단순화된 키워드로 재시도
    if not image_url:
        simplified_keyword = simplify_keyword(english_keyword)
        if simplified_keyword != english_keyword:
            print(f"이미지를 찾지 못했습니다. 단순화된 키워드='{simplified_keyword}'로 재시도")
            image_url = try_get_image(simplified_keyword, UNSPLASH_ACCESS_KEY)
    
    # 여전히 실패하면 더 일반적인 키워드로 시도
    if not image_url:
        # 주제별 대체 키워드 매핑
        fallback_mapping = {
            "energy": "renewable energy",
            "solar": "solar panels",
            "wind": "wind turbine",
            "climate": "climate nature",
            "carbon": "carbon nature",
            "sustainable": "sustainability",
            "environment": "nature landscape",
            "eco": "eco friendly",
            "green": "green nature",
            "technology": "modern technology"
        }
        
        # 적절한 대체 키워드 찾기
        fallback_keyword = "nature landscape"  # 기본값
        for key, value in fallback_mapping.items():
            if key in english_keyword.lower():
                fallback_keyword = value
                break
                
        print(f"이미지를 찾지 못했습니다. 대체 키워드='{fallback_keyword}'로 재시도")
        image_url = try_get_image(fallback_keyword, UNSPLASH_ACCESS_KEY)
    
    # 결과 확인
    if image_url:
        print(f"최종 이미지 URL: {image_url[:50]}...")
    else:
        print("이미지를 찾을 수 없습니다.")
        
    return image_url

def try_get_image(keyword, api_key):
    """단일 키워드로 Unsplash API를 호출하여 이미지 URL 획득 시도"""
    # URL 인코딩 적용
    encoded_keyword = urllib.parse.quote(keyword)
    
    print(f"인코딩된 검색어: '{keyword}' -> '{encoded_keyword}'")
    
    endpoint = f"https://api.unsplash.com/photos/random?query={encoded_keyword}&orientation=landscape&client_id={api_key}"
    print(f"API 엔드포인트: {endpoint}")
    
    try:
        resp = requests.get(endpoint, timeout=5)
        print(f"Unsplash API 응답 상태 코드: {resp.status_code} (키워드: {keyword})")
        
        if resp.status_code == 200:
            data = resp.json()
            image_url = data.get("urls", {}).get("regular", "")
            print(f"이미지 URL 획득 성공: {image_url[:50]}...")
            return image_url
        else:
            print(f"Unsplash API 에러: 상태 코드 {resp.status_code}")
            print(f"응답 내용: {resp.text}")
    except Exception as e:
        print("이미지 API 에러:", e)
    return ""

def translate_to_english(keyword):
    """한글 키워드를 영어로 간단히 변환 (실제 애플리케이션에서는 번역 API 사용 권장)"""
    # 간단한 한글-영어 사전 확장
    translation_dict = {
        # 기후/환경 관련
        "기후변화": "climate change",
        "환경": "environment",
        "지속 가능한": "sustainable",
        "지속가능": "sustainable",
        "지속가능한": "sustainable",
        "발전": "development",
        
        # 에너지 관련
        "재생 에너지": "renewable energy",
        "재생에너지": "renewable energy",
        "태양광": "solar energy",
        "태양광발전": "solar power",
        "풍력": "wind energy",
        "풍력발전": "wind power",
        "수력": "hydroelectric",
        "수소": "hydrogen",
        "배터리": "battery",
        "전기차": "electric vehicle",
        
        # 탄소/온실가스 관련
        "탄소중립": "carbon neutral",
        "탄소": "carbon",
        "온실가스": "greenhouse gas",
        "메탄": "methane",
        
        # 친환경 관련
        "친환경": "eco friendly",
        "생태계": "ecosystem",
        "생물다양성": "biodiversity",
        "자연": "nature",
        
        # 일반 용어
        "정책": "policy",
        "기술": "technology",
        "트렌드": "trends",
        "분석": "analysis",
        "예측": "forecast",
        "시장": "market",
        "산업": "industry",
        "경제": "economy",
        "투자": "investment",
        "혁신": "innovation",
        "솔루션": "solution",
        "미래": "future"
    }
    
    # 키워드 변환 (부분 매칭)
    modified_keyword = keyword
    for kr, en in translation_dict.items():
        if kr in keyword:
            modified_keyword = modified_keyword.replace(kr, en)
    
    # 변환 결과 확인 - 영문이 포함되어 있으면 해당 키워드 사용
    if any(ord(c) < 128 for c in modified_keyword):
        return modified_keyword
            
    # 변환 실패 시 일반 키워드로 대체
    return "nature"

def simplify_keyword(keyword):
    """키워드를 더 일반적인 형태로 단순화"""
    # 복합 키워드에서 주요 부분만 추출
    parts = keyword.split()
    
    # 단어가 2개 이상이면 첫 번째 단어만 사용
    if len(parts) > 1:
        return parts[0]
        
    # 관련 일반 키워드로 매핑
    keyword_mapping = {
        "renewable": "green energy",
        "climate": "climate",
        "carbon": "environment",
        "sustainable": "sustainability",
        "eco": "nature",
    }
    
    # 매핑된 키워드 찾기
    for key, value in keyword_mapping.items():
        if key in keyword.lower():
            return value
            
    return keyword

# 표 생성(LLM 활용)
def generate_table_by_keyword(keyword):
    prompt = f"'{keyword}' 주제로 관련된 간단한 표를 HTML <table>로 만들어주세요. 표에는 주제와 관련된 항목과 수치 또는 간단 설명이 포함되어야 하며, <table>, <thead>, <tbody> 태그를 포함하세요."
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=400
    )
    return resp.choices[0].message.content.strip()

# FAQ 생성(LLM 활용)
def generate_faq_by_keyword(keyword):
    prompt = f"'{keyword}' 주제와 관련해 독자들이 자주 묻는 3~5가지 질문(FAQ)과 답변을 HTML <dl><dt><dd> 구조로 만들어주세요."
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=600
    )
    return resp.choices[0].message.content.strip()



# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 블로그 정보 설정
BLOG_URL = "https://climate-insight.tistory.com"
BLOG_MANAGE_URL = "https://climate-insight.tistory.com/manage/post"
BLOG_NEW_POST_URL = "https://climate-insight.tistory.com/manage/newpost"

# 쿠키 및 로컬스토리지 저장 경로
COOKIES_FILE = "tistory_cookies.pkl"
LOCAL_STORAGE_FILE = "tistory_local_storage.json"

# 블로그 주제 및 카테고리 설정 (예시 목록)
BLOG_TOPICS = [
    "기후변화와 환경 문제",
    "지속 가능한 발전",
    "재생 에너지 트렌드",
    "탄소중립 정책",
    "친환경 생활 습관"
]

# 쿠키 저장 함수
def save_cookies(driver, file_path=COOKIES_FILE):
    """브라우저의 쿠키 정보를 파일에 저장"""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 현재 모든 쿠키 가져오기
        cookies = driver.get_cookies()
        
        # 티스토리 관련 쿠키만 필터링하고 전처리
        filtered_cookies = []
        for cookie in cookies:
            # 티스토리 관련 쿠키만 선택
            if 'domain' in cookie and ('tistory.com' in cookie['domain'] or cookie['domain'] == '.tistory.com'):
                # 일부 속성 제거 또는 수정
                if 'expiry' in cookie and isinstance(cookie['expiry'], float):
                    cookie['expiry'] = int(cookie['expiry'])
                
                # 도메인 속성 표준화
                if 'tistory.com' in cookie['domain']:
                    cookie['domain'] = '.tistory.com'
                
                # 불필요한 속성 제거
                for attr in ['sameSite', 'storeId']:
                    if attr in cookie:
                        del cookie[attr]
                
                filtered_cookies.append(cookie)
            elif 'name' in cookie and cookie['name'] in ['TSSESSION', 'PHPSESSID', 'TSID', 'tisUserInfo']:
                # 이름으로 티스토리 관련 중요 쿠키 선별
                if 'expiry' in cookie and isinstance(cookie['expiry'], float):
                    cookie['expiry'] = int(cookie['expiry'])
                
                # 도메인 속성 명시적 설정
                cookie['domain'] = '.tistory.com'
                
                # 불필요한 속성 제거
                for attr in ['sameSite', 'storeId']:
                    if attr in cookie:
                        del cookie[attr]
                
                filtered_cookies.append(cookie)
        
        # 필터링된 쿠키 저장
        if filtered_cookies:
            pickle.dump(filtered_cookies, open(file_path, "wb"))
            print(f"티스토리 관련 쿠키 {len(filtered_cookies)}개가 '{file_path}'에 저장되었습니다.")
            return True
        else:
            print("티스토리 관련 쿠키를 찾을 수 없어 저장하지 않았습니다.")
            return False
    except Exception as e:
        print(f"쿠키 저장 중 오류 발생: {e}")
        return False

# 쿠키 로드 함수
def load_cookies(driver, file_path=COOKIES_FILE):
    """저장된 쿠키 정보를 브라우저에 로드"""
    try:
        if os.path.exists(file_path):
            # 기존 쿠키 모두 삭제
            driver.delete_all_cookies()
            time.sleep(1)
            
            # 티스토리 메인 도메인에 접속 상태 확인
            current_url = driver.current_url
            if not ('tistory.com' in current_url):
                print("티스토리 도메인에 접속되어 있지 않아 먼저 접속합니다.")
                driver.get("https://www.tistory.com")
                time.sleep(3)
            
            # 쿠키 파일 로드
            cookies = pickle.load(open(file_path, "rb"))
            print(f"쿠키 파일에서 {len(cookies)}개의 쿠키를 읽었습니다.")
            
            # 쿠키 추가 전 디버깅 정보
            for i, cookie in enumerate(cookies):
                print(f"쿠키 {i+1}: 이름={cookie.get('name', '알 수 없음')}, 도메인={cookie.get('domain', '알 수 없음')}")
            
            success_count = 0
            for cookie in cookies:
                try:
                    # 필수 속성 확인
                    required_attrs = ['name', 'value']
                    if not all(attr in cookie for attr in required_attrs):
                        print(f"쿠키에 필수 속성이 없습니다: {cookie}")
                        continue
                    
                    # 문제가 될 수 있는 속성 제거 또는 수정
                    if 'expiry' in cookie:
                        if not isinstance(cookie['expiry'], int):
                            cookie['expiry'] = int(cookie['expiry'])
                    
                    # 불필요한 속성 제거
                    for attr in ['sameSite', 'storeId']:
                        if attr in cookie:
                            del cookie[attr]
                    
                    # 도메인 속성 확인 및 수정
                    if 'domain' in cookie:
                        # 티스토리 도메인인지 확인
                        if 'tistory.com' not in cookie['domain']:
                            print(f"티스토리 도메인이 아닌 쿠키는 건너뜁니다: {cookie['name']}")
                            continue
                        
                        # 도메인 형식 수정
                        if not cookie['domain'].startswith('.'):
                            cookie['domain'] = '.tistory.com'
                    else:
                        # 도메인 속성이 없으면 추가
                        cookie['domain'] = '.tistory.com'
                    
                    # 쿠키 추가 시도
                    try:
                        driver.add_cookie(cookie)
                        success_count += 1
                        print(f"쿠키 추가 성공: {cookie['name']}")
                    except Exception as add_e:
                        print(f"쿠키 추가 실패 (name: {cookie.get('name', 'unknown')}): {add_e}")
                        
                        # 도메인 문제 대응 (다른 방식 시도)
                        try:
                            simple_cookie = {
                                'name': cookie['name'], 
                                'value': cookie['value'],
                                'domain': '.tistory.com'
                            }
                            driver.add_cookie(simple_cookie)
                            success_count += 1
                            print(f"단순화된 쿠키로 추가 성공: {cookie['name']}")
                        except Exception as simple_e:
                            print(f"단순화된 쿠키 추가도 실패: {simple_e}")
                
                except Exception as cookie_e:
                    print(f"쿠키 처리 실패 (name: {cookie.get('name', 'unknown')}): {cookie_e}")
                    continue
            
            print(f"성공적으로 {success_count}/{len(cookies)}개의 쿠키를 로드했습니다.")
            
            # 페이지 새로고침하여 쿠키 적용
            driver.refresh()
            time.sleep(3)
            
            return success_count > 0
        else:
            print(f"쿠키 파일 '{file_path}'이 존재하지 않습니다.")
            return False
    except Exception as e:
        print(f"쿠키 로드 중 오류 발생: {e}")
        return False

# 로컬 스토리지 저장 함수
def save_local_storage(driver, file_path=LOCAL_STORAGE_FILE):
    """브라우저의 로컬 스토리지 정보를 파일에 저장"""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        local_storage = driver.execute_script("return Object.entries(localStorage);")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(local_storage, f, ensure_ascii=False)
        print(f"로컬 스토리지 정보가 '{file_path}'에 저장되었습니다.")
        return True
    except Exception as e:
        print(f"로컬 스토리지 저장 중 오류 발생: {e}")
        return False

# 로컬 스토리지 로드 함수
def load_local_storage(driver, file_path=LOCAL_STORAGE_FILE):
    """저장된 로컬 스토리지 정보를 브라우저에 로드"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                local_storage = json.load(f)
            for item in local_storage:
                if len(item) >= 2:
                    key, value = item[0], item[1]
                    driver.execute_script(f"localStorage.setItem('{key}', '{value}');")
            print(f"'{file_path}'에서 로컬 스토리지 정보를 로드했습니다.")
            return True
        else:
            print(f"로컬 스토리지 파일 '{file_path}'이 존재하지 않습니다.")
            return False
    except Exception as e:
        print(f"로컬 스토리지 로드 중 오류 발생: {e}")
        return False

# 로그인 상태 확인 함수
def is_logged_in(driver):
    """현재 티스토리에 로그인되어 있는지 확인"""
    try:
        # 알림창이 있는지 먼저 확인하고 처리
        try:
            alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
            if alert:
                alert_text = alert.text
                print(f"로그인 확인 중 알림창 감지: {alert_text}")
                
                # 저장된 글이 있다는 알림창이나 다른 알림창 처리
                alert.accept()  # 기본적으로 '확인' 버튼 클릭
                print(f"알림창의 '확인' 버튼을 클릭했습니다.")
                time.sleep(1)  # 알림창 처리 후 잠시 대기
        except:
            # 알림창이 없으면 계속 진행
            pass
            
        # 티스토리 대시보드 접근 시도
        driver.get(BLOG_MANAGE_URL)
        time.sleep(5)  # 페이지 로딩 대기 시간 증가
        
        # 알림창이 다시 나타날 수 있으므로 한 번 더 확인
        try:
            alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
            if alert:
                alert_text = alert.text
                print(f"대시보드 접근 중 알림창 감지: {alert_text}")
                alert.accept()
                print("알림창의 '확인' 버튼을 클릭했습니다.")
                time.sleep(1)
        except:
            pass
        
        # 로그인 페이지로 리디렉션 되었는지 확인
        current_url = driver.current_url
        if "login" in current_url.lower() or "auth" in current_url.lower():
            print("로그인되어 있지 않습니다. (URL 확인)")
            return False
            
        # 대시보드 요소 확인 (로그인 상태 확인)
        dashboard_elements = driver.find_elements(By.CSS_SELECTOR, 
            ".dashboard, .admin-area, .manager-area, .tistory-admin, .entry-list")
        
        if dashboard_elements:
            print("로그인 상태가 확인되었습니다. (대시보드 요소)")
            return True
            
        # 다른 방법으로 로그인 상태 확인
        username_elements = driver.find_elements(By.CSS_SELECTOR, 
            ".username, .user-info, .profile-name, .account-info, .my-name")
        
        if username_elements:
            print("사용자 정보가 확인되었습니다. (사용자 요소)")
            return True
            
        # 글 작성 버튼 확인
        write_button = driver.find_elements(By.CSS_SELECTOR, 
            ".btn_post, a[href*='newpost'], button[onclick*='newpost']")
            
        if write_button:
            print("새 글 작성 버튼이 확인되었습니다.")
            return True
            
        # JavaScript로 로그인 상태 확인
        login_status = driver.execute_script("""
            // 티스토리 로그인 상태 확인
            if (document.querySelector('.logout-button') || 
                document.querySelector('.btn-logout') || 
                document.querySelector('a[href*="logout"]')) {
                return "로그아웃 버튼 발견";
            }
            
            // 글 작성 관련 요소 확인
            if (document.querySelector('a[href*="newpost"]') ||
                document.querySelector('.btn_post')) {
                return "글 작성 버튼 발견";
            }
            
            // localStorage나 쿠키에 로그인 토큰 확인
            if (localStorage.getItem('tisUserToken') || 
                localStorage.getItem('loginState') ||
                document.cookie.indexOf('TSSESSION') > -1) {
                return "로그인 토큰 발견";
            }
            
            // 페이지 내 콘텐츠 확인
            if (document.querySelector('.my-blog') ||
                document.querySelector('.blog-list') ||
                document.querySelector('.control-panel')) {
                return "관리 패널 발견";
            }
            
            return false;
        """)
        
        if login_status:
            print(f"JavaScript를 통해 로그인 상태가 확인되었습니다: {login_status}")
            return True
            
        # 페이지 소스에서 특정 문자열 확인
        page_source = driver.page_source.lower()
        if "로그아웃" in page_source or "logout" in page_source:
            print("페이지 소스에서 로그아웃 문자열이 확인되었습니다.")
            return True
            
        print("로그인 상태를 확인할 수 없습니다.")
        # 디버깅 정보 출력
        print(f"현재 URL: {current_url}")
        print(f"페이지 타이틀: {driver.title}")
        return False
        
    except Exception as e:
        print(f"로그인 상태 확인 중 오류 발생: {e}")
        
        # 오류 메시지에 알림창(Alert) 관련 내용이 있는 경우 처리
        if "alert" in str(e).lower():
            try:
                print("알림창 오류 감지. 알림창 처리 시도...")
                alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
                if alert:
                    print(f"알림창 내용: {alert.text}")
                    alert.accept()  # 알림창 확인 버튼 클릭
                    print("알림창을 처리했습니다.")
                    
                    # 알림창 처리 후 로그인 상태를 다시 확인
                    time.sleep(2)
                    if "login" not in driver.current_url.lower() and "auth" not in driver.current_url.lower():
                        print("알림창 처리 후 로그인 상태로 간주합니다.")
                        return True
            except:
                pass
                
        # 사용자가 수동 로그인 후 Enter 키를 눌러 진행했다면, 로그인 성공으로 간주
        if "enter" in str(e).lower() or "input" in str(e).lower():
            print("사용자가 로그인 완료 후 진행했으므로 로그인 성공으로 간주합니다.")
            return True
            
        return False

# 자동 로그인 함수
def try_auto_login(driver):
    """저장된 쿠키와 로컬 스토리지를 사용하여 자동 로그인 시도"""
    try:
        print("\n===== 자동 로그인 시도 =====")
        
        # 모든 쿠키 삭제
        driver.delete_all_cookies()
        time.sleep(1)
        
        # 티스토리 메인 페이지 접속
        print("티스토리 메인 페이지에 접속 중...")
        try:
            driver.get("https://www.tistory.com")
            time.sleep(3)  # 페이지 로딩 대기
        except Exception as e:
            # 페이지 이동 중 알림창이 발생하면 처리
            if "alert" in str(e).lower():
                print(f"페이지 이동 중 알림창 발생: {e}")
                handle_alerts(driver)
                driver.get("https://www.tistory.com")
                time.sleep(3)
        
        # 알림창이 있는지 확인하고 처리
        handle_alerts(driver, max_attempts=2)
        
        # 저장된 쿠키 로드
        print("저장된 쿠키 로드 시도 중...")
        cookie_loaded = load_cookies(driver)
        
        # 저장된 로컬 스토리지 로드
        print("저장된 로컬 스토리지 로드 시도 중...")
        storage_loaded = load_local_storage(driver)
        
        # 쿠키나 로컬 스토리지 중 하나라도 로드에 실패한 경우
        if not cookie_loaded and not storage_loaded:
            print("저장된 세션 정보가 없습니다. 자동 로그인이 불가능합니다.")
            return False
        
        # 페이지 새로고침하여 로드된 쿠키 적용
        print("세션 정보 적용을 위해 페이지 새로고침...")
        try:
            driver.refresh()
            time.sleep(3)
            # 알림창 처리
            handle_alerts(driver, max_attempts=2)
        except Exception as e:
            if "alert" in str(e).lower():
                handle_alerts(driver)
                time.sleep(2)
        
        # 로그인 상태 확인 - 여러 방법 시도
        login_verification_methods = [
            ("방법 1", "로그인 상태 확인 함수", lambda: is_logged_in(driver)),
            ("방법 2", "URL 리디렉션 확인", lambda: "login" not in driver.current_url.lower() and "auth" not in driver.current_url.lower()),
            ("방법 3", "로그인 버튼 확인", lambda: len(driver.find_elements(By.CSS_SELECTOR, "a[href*='login'], .btn-login, .login-button")) == 0),
        ]
        
        login_method_results = []
        for method_id, method_name, method_func in login_verification_methods:
            try:
                # 각 방법 시도 전 알림창 확인
                handle_alerts(driver, max_attempts=1)
                
                print(f"{method_id}: {method_name}으로 로그인 상태 확인 중...")
                method_result = method_func()
                login_method_results.append(method_result)
                
                if method_result:
                    print(f"자동 로그인 성공! ({method_name})")
                else:
                    print(f"{method_name}으로 확인 시 로그인되지 않은 상태입니다.")
            except Exception as e:
                print(f"{method_name} 확인 중 오류 발생: {e}")
                
                # 알림창 처리
                if "alert" in str(e).lower():
                    print(f"{method_name} 확인 중 알림창 발생, 처리 중...")
                    handle_alerts(driver)
                
                login_method_results.append(False)
        
        # 모든 방법이 실패하거나 불일치할 경우 (세션 만료로 간주)
        if not any(login_method_results) or (len(set(login_method_results)) > 1):
            print("\n===== 세션 만료 감지 =====")
            print("저장된 로그인 세션이 만료되었습니다.")
            print("티스토리 보안 정책에 따라 일정 기간이 지나면 자동으로 세션이 만료됩니다.")
            print("수동으로 로그인이 필요합니다.")
            return False
            
        # 대시보드 직접 접근 시도
        print("\n티스토리 대시보드에 직접 접근 시도...")
        try:
            driver.get(BLOG_MANAGE_URL)
            time.sleep(5)
            
            # 알림창 처리
            handle_alerts(driver, max_attempts=2)
            
            # 대시보드 접근 성공 여부 확인
            if "login" in driver.current_url.lower() or "auth" in driver.current_url.lower():
                print("대시보드 접근 시 로그인 페이지로 리디렉션되었습니다.")
                print("세션이 만료되었습니다. 수동 로그인이 필요합니다.")
                return False
            else:
                print("대시보드 접근 성공! 자동 로그인 성공으로 간주합니다.")
                return True
                
            # 추가 확인: 로그인 창이 표시되는지
            login_form = driver.find_elements(By.CSS_SELECTOR, 
                "form[action*='login'], .login-form, #login-form")
            if login_form:
                print("로그인 폼이 표시됩니다. 세션이 만료되었습니다.")
                return False
        except Exception as dash_e:
            print(f"대시보드 접근 시도 중 오류: {dash_e}")
            
            # 알림창 처리
            if "alert" in str(dash_e).lower():
                print("대시보드 접근 중 알림창 발생, 처리 중...")
                handle_alerts(driver)
                # 다시 시도
                try:
                    driver.get(BLOG_MANAGE_URL)
                    time.sleep(3)
                    handle_alerts(driver)
                    if "login" not in driver.current_url.lower() and "auth" not in driver.current_url.lower():
                        print("알림창 처리 후 대시보드 접근 성공!")
                        return True
                except:
                    pass
        
        # 마지막 확인: 사용자에게 물어보기
        print("\n자동 로그인 상태를 명확하게 확인할 수 없습니다.")
        print(f"현재 URL: {driver.current_url}")
        print(f"페이지 제목: {driver.title}")
        
        # 로그인 버튼이 있는지 확인
        login_buttons = driver.find_elements(By.CSS_SELECTOR, 
            "a[href*='login'], .btn-login, .login-button")
        if login_buttons:
            print("로그인 버튼이 발견되었습니다. 세션이 만료되었습니다.")
            return False
            
        return any(login_method_results)  # 하나라도 성공이면 로그인 성공으로 처리
            
    except Exception as e:
        print(f"자동 로그인 처리 중 오류 발생: {e}")
        
        # 알림창 관련 오류인 경우 처리
        if "alert" in str(e).lower():
            try:
                print("자동 로그인 중 알림창 관련 오류 감지, 처리 시도...")
                handle_alerts(driver)
                
                # 알림창 처리 후 페이지가 표시되는지 확인
                if "login" not in driver.current_url.lower() and "auth" not in driver.current_url.lower():
                    print("알림창 처리 후 자동 로그인 성공으로 간주합니다.")
                    return True
            except:
                pass
        
        print("오류로 인해 수동 로그인이 필요합니다.")
        return False

# 수동 로그인 함수
def manual_login(driver):
    """사용자에게 수동 로그인을 요청하고 완료 후 세션 정보 저장"""
    try:
        print("\n===== 수동 로그인 시작 =====")
        print("세션이 만료되어 수동 로그인이 필요합니다.")
        print("아래 안내에 따라 로그인을 진행해주세요.")
        
        # 기존 세션 정보 삭제
        driver.delete_all_cookies()
        
        # 로그인 페이지 접속
        print("로그인 페이지로 이동합니다...")
        driver.get("https://www.tistory.com/auth/login")
        time.sleep(3)
        
        # 사용자에게 로그인 요청
        print("\n========= 수동 로그인 가이드 =========")
        print("1. 브라우저에서 로그인을 수동으로 완료해주세요.")
        print("2. 아이디와 비밀번호를 입력하여 로그인합니다.")
        print("3. 로그인 완료 후 대시보드나 메인 페이지가 표시되면 성공입니다.")
        print("4. 2단계 인증이 필요한 경우 인증 절차를 완료해주세요.")
        print("5. 로그인이 완료되면 아래 안내에 따라 Enter 키를 눌러주세요.")
        print("========================================")
        input("\n로그인을 완료하셨으면 Enter 키를 눌러주세요...")
        
        # 알림창이 있는지 확인하고 처리
        handle_alerts(driver, max_attempts=3)
        
        # 티스토리 메인 페이지로 이동
        print("\n티스토리 메인 페이지로 이동합니다...")
        try:
            driver.get("https://www.tistory.com")
            time.sleep(3)
        except Exception as e:
            # 페이지 이동 중 알림창이 발생하면 처리
            if "alert" in str(e).lower():
                print(f"페이지 이동 중 알림창 발생: {e}")
                handle_alerts(driver)
                driver.get("https://www.tistory.com")
                time.sleep(3)
        
        # 로그인 상태 확인 (최대 3회 시도)
        login_success = False
        for attempt in range(3):
            try:
                print(f"\n로그인 상태 확인 시도 {attempt+1}/3...")
                
                # 알림창 처리 후 is_logged_in 함수 호출
                handle_alerts(driver, max_attempts=2)
                
                if is_logged_in(driver):
                    print("로그인 성공 확인! 세션 정보를 저장합니다.")
                    login_success = True
                    break
                else:
                    print(f"로그인 상태 확인 실패 ({attempt+1}/3)")
                    
                    if attempt < 2:  # 마지막 시도가 아니면 재확인
                        print("3초 후 다시 확인합니다...")
                        time.sleep(3)
                        
                        # 알림창 처리 후 페이지 새로고침
                        handle_alerts(driver, max_attempts=2)
                        driver.refresh()  
                        time.sleep(3)
                        handle_alerts(driver, max_attempts=2)
            except Exception as check_e:
                print(f"로그인 상태 확인 중 오류: {check_e}")
                
                # 오류가 알림창 관련인 경우 처리
                if "alert" in str(check_e).lower():
                    print("알림창 관련 오류 감지, 처리 시도...")
                    handle_alerts(driver)
                    
                if attempt < 2:
                    print("3초 후 다시 시도합니다...")
                    time.sleep(3)
        
        # 로그인 상태와 관계없이 사용자 확인으로 진행
        if not login_success:
            print("\n자동 확인으로는 로그인 상태를 확인할 수 없습니다.")
            print("로그인 창이 아직 표시되는지 확인해 주세요.")
            user_confirm = input("로그인이 완료되었나요? (y/n): ")
            if user_confirm.lower() != 'y':
                print("로그인이 완료되지 않았습니다. 다시 시도해주세요.")
                print("관리자 페이지에 접근하려면 유효한 로그인 세션이 필요합니다.")
                return False
            print("사용자 확인으로 로그인 성공으로 간주합니다.")
            login_success = True
        
        # 세션 정보 저장 시도
        if login_success:
            print("\n세션 정보 저장을 시도합니다...")
            save_success = False
            try:
                # 저장 전 알림창이 있는지 확인하고 처리
                handle_alerts(driver, max_attempts=2)
                
                # 1차 시도: 메인 페이지에서 세션 정보 저장
                save_result1 = save_cookies(driver)
                save_result2 = save_local_storage(driver)
                
                # 2차 시도: 대시보드 페이지에서 세션 정보 저장
                print("대시보드 페이지에서 추가 세션 정보 저장 시도...")
                try:
                    driver.get(BLOG_MANAGE_URL)
                    time.sleep(3)
                    # 알림창 처리
                    handle_alerts(driver)
                    
                    save_result3 = save_cookies(driver)
                    save_result4 = save_local_storage(driver)
                    
                    if save_result1 or save_result2 or save_result3 or save_result4:
                        print("세션 정보가 성공적으로 저장되었습니다.")
                        print("다음에는 자동 로그인으로 더 빠르게 접속할 수 있습니다.")
                        save_success = True
                    else:
                        print("세션 정보 저장에 실패했지만, 로그인은 유지됩니다.")
                        print("다음 실행 시에도 수동 로그인이 필요할 수 있습니다.")
                except Exception as dash_e:
                    print(f"대시보드 페이지 접근 중 오류: {dash_e}")
                    # 알림창 처리 시도
                    if "alert" in str(dash_e).lower():
                        handle_alerts(driver)
            except Exception as save_e:
                print(f"세션 정보 저장 중 오류: {save_e}")
                print("세션 정보 저장에 실패했지만, 로그인은 유지됩니다.")
                print("다음 실행 시에도 수동 로그인이 필요할 수 있습니다.")
        
        print("\n===== 수동 로그인 완료 =====")
        if login_success:
            if save_success:
                print("세션 정보 저장 성공: 다음 실행 시 자동 로그인이 가능합니다.")
            else:
                print("세션 정보 저장 실패: 다음 실행 시에도 수동 로그인이 필요할 수 있습니다.")
        
        # 수동 로그인 성공으로 처리
        return login_success
            
    except Exception as e:
        print(f"수동 로그인 처리 중 오류 발생: {e}")
        # 알림창 관련 오류인 경우 처리
        if "alert" in str(e).lower():
            try:
                print("알림창 관련 오류 감지, 처리 시도...")
                handle_alerts(driver)
            except:
                pass
                
        print("사용자가 Enter 키를 눌렀으므로 로그인 성공으로 간주합니다.")
        return True

def get_user_topic():
    """
    사용자로부터 블로그 주제를 입력받음
    """
    print("\n=== 블로그 주제 선택 ===")
    print("1. 예시 주제 목록에서 선택")
    print("2. 직접 주제 입력")
    choice = input("선택 (1 또는 2): ")
    
    if choice == "1":
        print("\n예시 주제 목록:")
        for i, topic in enumerate(BLOG_TOPICS, 1):
            print(f"{i}. {topic}")
        
        while True:
            try:
                selection = int(input("\n주제 번호 선택: "))
                if 1 <= selection <= len(BLOG_TOPICS):
                    return BLOG_TOPICS[selection-1]
                else:
                    print(f"1부터 {len(BLOG_TOPICS)}까지의 번호를 입력해주세요.")
            except ValueError:
                print("유효한 숫자를 입력해주세요.")
    else:
        return input("\n블로그 주제를 직접 입력해주세요: ")

def generate_blog_content(topic, format_type=1):
    print(f"'{topic}' 주제로 블로그 콘텐츠(이미지, 표, FAQ 포함) 생성 중...")

    # 1. 제목 생성
    title_prompt = f"다음 주제에 관한 블로그 포스트의 매력적인 제목을 생성해주세요: '{topic}'. 제목만 작성하고 따옴표나 기호는 포함하지 마세요."
    title_resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": title_prompt}],
        max_tokens=50
    )
    title = title_resp.choices[0].message.content.strip()

    # 2. 본문 생성
    content_prompt = f"""
    '{topic}' 주제로 서론, 본론, 결론이 있는 700~1000자 내외의 블로그 본문을 HTML로 작성하세요.
    문단마다 <h2>, <p> 등 구조적 태그 사용, SEO 키워드 강조.
    """
    content_resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": content_prompt}],
        max_tokens=1200
    )
    content = content_resp.choices[0].message.content.strip()

    # 3. 대표 이미지 자동 선택
    image_url = get_keyword_image_url(topic)
    # 티스토리 호환성을 위해 이미지 태그에 추가 속성 부여
    image_html = f'<img src="{image_url}" alt="{topic} 관련 이미지" style="max-width:100%; height:auto; display:block; margin:0 auto;" loading="lazy" class="tistory-content-img" data-origin-width="800" data-origin-height="500">' if image_url else ''
    print(f"이미지 HTML 코드 생성: {image_html[:100]}...")

    # 4. 표 자동 생성
    table_html = generate_table_by_keyword(topic)

    # 5. FAQ 자동 생성
    faq_html = generate_faq_by_keyword(topic)

    # 6. 통합 HTML 조립 - 티스토리 호환성 높이기
    full_content = f"""
    <div class="post-content">
      <h1 class="post-title">{title}</h1>
      <div class="post-image">
    {image_html}
      </div>
      <div class="post-body">
    {content}
      </div>
      <div class="post-table">
    <h2>관련 표</h2>
    {table_html}
      </div>
      <div class="post-faq">
    <h2>자주 묻는 질문(FAQ)</h2>
    {faq_html}
      </div>
    </div>
    """

    # 7. 태그 생성 (기존 로직 유지)
    tags_prompt = f"'{topic}' 주제로 SEO에 효과적인 5개 태그를 쉼표로 나열해주세요."
    tags_resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": tags_prompt}],
        max_tokens=100
    )
    tags = tags_resp.choices[0].message.content.strip()

    return {
        "title": title,
        "content": full_content,
        "tags": tags,
        "format_type": format_type
    }

# 알림창 처리 함수 추가
def handle_alerts(driver, max_attempts=5, action="accept"):
    """
    브라우저에 표시된 알림창을 처리하는 함수
    
    Args:
        driver: WebDriver 인스턴스
        max_attempts: 최대 알림창 처리 시도 횟수
        action: 기본 처리 방식 ("accept" 또는 "dismiss")
    
    Returns:
        bool: 알림창이 감지되고 처리되었으면 True, 아니면 False
    """
    alert_handled = False
    
    for attempt in range(max_attempts):
        try:
            # 짧은 대기 시간으로 알림창 확인
            alert = WebDriverWait(driver, 1).until(EC.alert_is_present())
            if alert:
                alert_text = alert.text
                print(f"알림창 감지 ({attempt+1}/{max_attempts}): {alert_text}")
                
                # 저장된 글이 있다는 알림창인 경우
                if "저장된 글이 있습니다" in alert_text or "이어서 작성" in alert_text:
                    if action == "ask":
                        # 사용자에게 선택 요청
                        print("이전에 저장된 글이 있습니다. 어떻게 처리할까요?")
                        print("1. 이어서 작성 (확인/예)")
                        print("2. 새로 작성 (취소/아니오)")
                        choice = input("선택 (1 또는 2, 기본값 2): ")
                        
                        if choice == "1":
                            alert.accept()  # 확인 버튼 클릭
                            print("이전 글을 이어서 작성합니다.")
                        else:
                            alert.dismiss()  # 취소 버튼 클릭
                            print("새 글을 작성합니다.")
                    elif action == "accept":
                        alert.accept()  # 확인 버튼 클릭
                        print("이전 글을 이어서 작성합니다.")
                    else:
                        alert.dismiss()  # 취소 버튼 클릭
                        print("새 글을 작성합니다.")
                else:
                    # 기타 알림창은 기본적으로 확인 버튼 클릭
                    alert.accept()
                    print(f"알림창의 '확인' 버튼을 클릭했습니다: '{alert_text}'")
                
                time.sleep(1)  # 알림창 처리 후 잠시 대기
                alert_handled = True
                
                # 다음 알림창이 있는지 확인하기 위해 계속 진행
            else:
                break
        except Exception:
            # 알림창이 없으면 루프 종료
            break
    
    return alert_handled

def login_and_post_to_tistory():
    """
    티스토리에 로그인하고 생성된 콘텐츠 게시
    """
    # ChromeOptions 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # WebDriver 설정
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        print("\n=== 티스토리 로그인 단계 ===")
        login_success = False
        max_login_attempts = 2
        
        for attempt in range(max_login_attempts):
            # 자동 로그인 시도
            print(f"로그인 시도 {attempt+1}/{max_login_attempts}")
            auto_login_success = try_auto_login(driver)
            
            # 자동 로그인 실패 시 수동 로그인 진행
            if not auto_login_success:
                print("\n자동 로그인 실패: 세션이 만료되었거나 쿠키가 유효하지 않습니다.")
                print("수동 로그인으로 전환합니다.")
                manual_login_success = manual_login(driver)
                if manual_login_success:
                    login_success = True
                    print("수동 로그인 성공!")
                    break
                elif attempt < max_login_attempts - 1:
                    print(f"로그인 실패, 다시 시도합니다. ({attempt+1}/{max_login_attempts})")
                    time.sleep(2)
                else:
                    print("최대 로그인 시도 횟수를 초과했습니다.")
            else:
                login_success = True
                print("자동 로그인 성공!")
                break
        
        # 로그인 성공 확인 후 진행
        if not login_success:
            print("\n=== 로그인 실패 ===")
            print("티스토리 로그인에 실패했습니다.")
            print("가능한 원인:")
            print("1. 세션이 만료되었습니다.")
            print("2. 로그인 정보가 올바르지 않습니다.")
            print("3. 티스토리 서비스에 일시적인 문제가 있습니다.")
            print("4. 네트워크 연결에 문제가 있습니다.")
            retry = input("로그인 없이 계속 진행하시겠습니까? (y/n): ")
            if retry.lower() != 'y':
                print("프로그램을 종료합니다.")
                return
            else:
                print("사용자 확인으로 계속 진행합니다.")
                print("(주의: 로그인 없이 진행 시 일부 기능이 제한될 수 있습니다.)")
        
        # 티스토리 메인 페이지 접근 - 로그인 성공 유무와 관계없이 계속 진행
        print("\n=== 티스토리 글 작성 단계 ===")
        print("티스토리 메인 페이지로 이동합니다...")
        driver.get(BLOG_MANAGE_URL)
        time.sleep(3)
        
        # 무한 루프로 글 작성 진행 (사용자가 종료하기 전까지)
        while True:
            # 사용자에게 주제 선택 요청
            selected_topic = get_user_topic()
            
            # HTML 모드로 고정 (형식 선택 메뉴 제거)
            format_type = 1  # 항상 HTML 모드 사용
            print("콘텐츠 형식: HTML 모드 (태그 포함)")
            
            # 콘텐츠 생성 (재시도 로직 사용)
            try:
                blog_post = generate_blog_content_with_retry(selected_topic, format_type)
            except Exception as e:
                print(f"콘텐츠 생성 중 오류 발생: {e}")
                retry = input("다시 시도하시겠습니까? (y/n): ")
                if retry.lower() == 'y':
                    continue
                else:
                    break
            
            # 새 글 작성 페이지로 이동하기 전에 기존 알림창 처리
            print("페이지 이동 전 알림창 확인 중...")
            handle_alerts(driver)
            
            # 새 글 작성 페이지로 이동 (try-except로 감싸서 알림창 처리)
            print("새 글 작성 페이지로 이동합니다...")
            try:
             driver.get(BLOG_NEW_POST_URL)
            except Exception as e:
                print(f"페이지 이동 중 예외 발생: {e}")
                # 예외 발생 시 알림창 처리 시도
                if "alert" in str(e).lower():
                    print("알림창으로 인한 예외 감지, 알림창 처리 시도...")
                    handle_alerts(driver)
                    # 다시 페이지 이동 시도
                    driver.get(BLOG_NEW_POST_URL)
            
            # 페이지 로딩 대기 및 알림창 처리
            time.sleep(5)
            
            # 알림창(Alert) 자동 처리 - 사용자에게 물어보는 방식
            print("저장된 글 관련 알림창 확인 중...")
            handle_alerts(driver, action="ask")

            # iframe 확인 및 전환
            try:
                iframe_editor = None
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                if iframes:
                    print(f"{len(iframes)}개의 iframe을 발견했습니다.")
                    for iframe in iframes:
                        try:
                            iframe_id = iframe.get_attribute("id") or ""
                            iframe_name = iframe.get_attribute("name") or ""
                            iframe_src = iframe.get_attribute("src") or ""
                            print(f"iframe: id='{iframe_id}', name='{iframe_name}', src='{iframe_src}'")
                            if "editor" in iframe_id.lower():
                                iframe_editor = iframe
                                print(f"에디터 iframe을 찾았습니다: {iframe_id}")
                                break
                        except:
                            pass
            except Exception as e:
                print(f"iframe 확인 중 오류: {e}")
                # iframe 확인 중 오류 발생 시 알림창 처리 시도
                handle_alerts(driver)
            
            # 글 작성 함수 호출
            try:
             write_post(driver, blog_post, format_type)
            except Exception as e:
                print(f"글 작성 중 오류 발생: {e}")
                # 글 작성 중 오류 발생 시 알림창 처리 시도
                if "alert" in str(e).lower():
                    print("글 작성 중 알림창으로 인한 예외 감지, 알림창 처리 시도...")
                    handle_alerts(driver)
            
            # 임시저장 후 발행 여부 확인
            print("\n글이 임시저장되었습니다. 발행하시겠습니까?")
            proceed = input("발행하기 (Y/N): ")
            
            # 대소문자 구분 없이 'Y'인 경우 발행 진행
            if proceed.upper() == 'Y':
                print("발행을 진행합니다...")
                try:
                    publish_success = publish_post(driver)
                    
                    if publish_success:
                        print("발행이 완료되었습니다!")
                    else:
                        print("발행이 완료되지 않았습니다. 글은 임시저장 상태로 남아있습니다.")
                except Exception as e:
                    print(f"발행 중 오류 발생: {e}")
                    # 발행 중 오류 발생 시 알림창 처리 시도
                    if "alert" in str(e).lower():
                        print("발행 중 알림창으로 인한 예외 감지, 알림창 처리 시도...")
                        handle_alerts(driver)
            else:
                print("발행을 취소했습니다. 글은 임시저장 상태로 남아있습니다.")
            
            # 작업 완료 후 선택 옵션 제공
            print("\n=== 작업 완료 ===")
            print("1. 새 글 작성하기")
            print("2. 브라우저 종료하기")
            choice = input("선택 (1 또는 2): ")
            
            if choice != "1":
                print("브라우저를 종료합니다...")
                break  # 루프 종료하고 finally 블록에서 브라우저 종료
            
            # 새 글 작성을 위해 페이지 이동 전 알림창 처리
            print("새 글 작성을 위해 페이지를 준비합니다...")
            handle_alerts(driver)
            
            # 새 글 작성 페이지로 이동 시도
            try:
                driver.get(BLOG_NEW_POST_URL)
            except Exception as e:
                print(f"페이지 이동 중 예외 발생: {e}")
                # 예외 발생 시 알림창 처리 시도
                if "alert" in str(e).lower():
                    print("알림창으로 인한 예외 감지, 알림창 처리 시도...")
                    handle_alerts(driver)
                    # 다시 페이지 이동 시도
            driver.get(BLOG_NEW_POST_URL)
            
            # 페이지 로딩 대기 및 알림창 처리
            time.sleep(3)
            print("새 글 작성 페이지에서 알림창 확인 중...")
            handle_alerts(driver, action="dismiss")  # 새 글 작성 시에는 기본적으로 취소 버튼 클릭
            
    except Exception as e:
        print(f"전체 과정에서 오류 발생: {e}")
        # 마지막 시도로 알림창 처리
        try:
            print("최종 오류 처리: 알림창 확인 중...")
            handle_alerts(driver)
        except:
            pass
    
    finally:
        # 루프가 종료되었을 때만 브라우저 종료
        driver.quit()

# 콘텐츠 생성 함수에 재시도 로직 추가
def generate_blog_content_with_retry(topic, format_type=1, max_retries=3, retry_delay=5):
    """재시도 로직이 포함된 블로그 콘텐츠 생성 함수"""
    print(f"\n=== 블로그 콘텐츠 생성 시작: 주제='{topic}' ===")
    
    for attempt in range(max_retries):
        try:
            print(f"시도 {attempt+1}/{max_retries}: 콘텐츠 생성 중...")
            # 항상 HTML 모드(1)로 설정
            result = generate_blog_content(topic, format_type=1)
            
            # 생성된 결과 요약 출력
            print(f"▶ 생성된 제목: {result['title']}")
            print(f"▶ 태그: {result['tags']}")
            print(f"▶ 콘텐츠 길이: {len(result['content'])} 글자")
            
            # 이미지 URL 확인
            image_url_match = re.search(r'<img src="([^"]+)"', result['content'])
            if image_url_match:
                print(f"▶ 이미지 URL: {image_url_match.group(1)[:80]}...")
            else:
                print("▶ 경고: 이미지 URL을 찾을 수 없습니다.")
            
            print(f"=== 콘텐츠 생성 성공! ===")
            return result
            
        except Exception as e:
            print(f"시도 {attempt+1}/{max_retries} 실패: {e}")
            if attempt < max_retries - 1:
                print(f"{retry_delay}초 후 재시도합니다...")
                time.sleep(retry_delay)
            else:
                print("최대 재시도 횟수를 초과했습니다.")
                raise

# 발행 로직을 별도 함수로 분리
def publish_post(driver):
    """
    글 발행 과정을 처리하는 함수
    """
    print("\n==========================================")
    print("==== 발행 함수 호출됨 (publish_post) ====")
    print("==========================================\n")
    publish_success = False
    
    try:
        # 1단계: TinyMCE 모달 창이 있다면 닫기 (클릭 방해 요소 제거)
        try:
            print("TinyMCE 모달 창 확인 및 제거 중...")
            driver.execute_script("""
                var modalBlock = document.querySelector('#mce-modal-block');
                if (modalBlock) {
                    modalBlock.parentNode.removeChild(modalBlock);
                    console.log('모달 블록 제거됨');
                }
                
                var modalWindows = document.querySelectorAll('.mce-window, .mce-reset');
                for (var i = 0; i < modalWindows.length; i++) {
                    if (modalWindows[i].style.display !== 'none') {
                        modalWindows[i].style.display = 'none';
                        console.log('모달 창 숨김 처리됨');
                    }
                }
            """)
            print("모달 창 처리 완료")
        except Exception as modal_e:
            print(f"모달 창 처리 중 오류: {modal_e}")
        
        # 2단계: '완료' 버튼 찾아 클릭
        print("\n1단계: '완료' 버튼을 찾아 클릭합니다...")
        
        # 2-1. CSS 선택자로 완료 버튼 찾기
        complete_button_selectors = [
            "#publish-layer-btn",       # 티스토리 완료 버튼 ID
            ".btn_publish", 
            ".publish-button",
            "button[type='submit']",
            ".btn_save.save-publish",   # 티스토리 발행 버튼
            ".btn_post",                # 티스토리 발행 버튼 (다른 클래스)
            ".btn_submit",              # 티스토리 발행 버튼 (다른 클래스)
            "#editor-root .editor-footer button:last-child" # 에디터 푸터의 마지막 버튼
        ]
        
        complete_button_found = False
        
        print("CSS 선택자로 완료 버튼 찾기 시도 중...")
        for selector in complete_button_selectors:
            try:
                print(f"선택자 '{selector}' 시도 중...")
                complete_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                if complete_buttons:
                    complete_button = complete_buttons[0]
                    button_text = complete_button.text.strip()
                    print(f"'완료' 버튼을 찾았습니다: {selector} (텍스트: '{button_text}')")
                    
                    # 클릭 전 스크립트 실행하여 방해 요소 제거
                    driver.execute_script("""
                        var modalBlock = document.querySelector('#mce-modal-block');
                        if (modalBlock) modalBlock.remove();
                    """)
                    
                    # 버튼 클릭
                    complete_button.click()
                    print("'완료' 버튼을 클릭했습니다.")
                    time.sleep(3)  # 모달 대화상자가 나타날 때까지 대기
                    complete_button_found = True
                    break
            except Exception as btn_e:
                print(f"'{selector}' 선택자로 버튼 클릭 시도 중 오류: {btn_e}")
        
        # 2-2. JavaScript로 완료 버튼 클릭 시도
        if not complete_button_found:
            try:
                print("\nJavaScript를 통해 '완료' 버튼 클릭을 시도합니다...")
                result = driver.execute_script("""
                    // 완료 버튼 ID로 직접 찾기
                    var publishBtn = document.querySelector('#publish-layer-btn');
                    if (publishBtn) {
                        publishBtn.click();
                        return "ID로 버튼 클릭";
                    }
                    
                    // 버튼 텍스트로 찾기
                    var buttons = document.querySelectorAll('button');
                    for (var i = 0; i < buttons.length; i++) {
                        if (buttons[i].textContent.includes('완료')) {
                            buttons[i].click();
                            return "텍스트로 버튼 클릭";
                        }
                    }
                    
                    // 에디터 API 사용
                    if (window.PostEditor && window.PostEditor.publish) {
                        window.PostEditor.publish();
                        return "PostEditor API 사용";
                    }
                    
                    // 하단 영역의 마지막 버튼 클릭
                    var footerButtons = document.querySelectorAll('.editor-footer button, .foot_post button, .write_foot button');
                    if (footerButtons.length > 0) {
                        footerButtons[footerButtons.length - 1].click();
                        return "하단 마지막 버튼 클릭";
                    }
                    
                    return false;
                """)
                
                if result:
                    print(f"JavaScript를 통해 '완료' 버튼을 클릭했습니다: {result}")
                    time.sleep(3)  # 모달 대화상자가 나타날 때까지 대기
                    complete_button_found = True
                else:
                    print("JavaScript로 '완료' 버튼을 찾지 못했습니다.")
            except Exception as js_e:
                print(f"JavaScript를 통한 '완료' 버튼 클릭 중 오류: {js_e}")
        
        # 2-3. XPath로 완료 버튼 찾기
        if not complete_button_found:
            try:
                print("\nXPath로 완료 버튼 찾기 시도 중...")
                complete_xpath_expressions = [
                    "//button[contains(text(), '완료')]",
                    "//button[@id='publish-layer-btn']",
                    "//button[contains(@class, 'publish') or contains(@id, 'publish')]",
                    "//div[contains(@class, 'editor-footer') or contains(@class, 'foot_post')]//button[last()]"
                ]
                
                for xpath_expr in complete_xpath_expressions:
                    print(f"XPath 표현식 '{xpath_expr}' 시도 중...")
                    complete_buttons_xpath = driver.find_elements(By.XPATH, xpath_expr)
                    if complete_buttons_xpath:
                        complete_button = complete_buttons_xpath[0]
                        button_text = complete_button.text.strip()
                        print(f"XPath로 '완료' 버튼을 찾았습니다: {xpath_expr} (텍스트: '{button_text}')")
                        
                        # 클릭 전 스크립트 실행하여 방해 요소 제거
                        driver.execute_script("document.querySelector('#mce-modal-block')?.remove();")
                        
                        # 버튼 클릭
                        complete_button.click()
                        print("XPath로 찾은 '완료' 버튼을 클릭했습니다.")
                        time.sleep(3)  # 모달 대화상자가 나타날 때까지 대기
                        complete_button_found = True
                        break
            except Exception as xpath_e:
                print(f"XPath를 통한 '완료' 버튼 찾기 중 오류: {xpath_e}")
        
        # 2-4. 버튼을 찾지 못한 경우, 하단 영역의 모든 버튼 표시
        if not complete_button_found:
            try:
                print("\n'완료' 버튼을 찾지 못했습니다. 하단 영역 버튼 분석 중...")
                
                # 하단 영역의 모든 버튼 요소 출력
                bottom_buttons = driver.find_elements(By.CSS_SELECTOR, ".editor-footer button, .foot_post button, .write_foot button, #editor-root > div:last-child button")
                print(f"하단 영역에서 {len(bottom_buttons)}개의 버튼을 찾았습니다.")
                
                for i, btn in enumerate(bottom_buttons):
                    try:
                        btn_text = btn.text.strip() or '(텍스트 없음)'
                        btn_class = btn.get_attribute('class') or '(클래스 없음)'
                        btn_id = btn.get_attribute('id') or '(ID 없음)'
                        print(f"하단 버튼 {i+1}: 텍스트='{btn_text}', 클래스='{btn_class}', ID='{btn_id}'")
                        
                        # 완료/발행 관련 버튼 추정
                        if ('완료' in btn_text or '발행' in btn_text or 
                            '등록' in btn_text or 
                            'publish' in btn_text.lower() or 'submit' in btn_text.lower()):
                            print(f"  => 발행 버튼으로 보입니다!")
                            
                            proceed = input(f"이 버튼({btn_text})을 발행 버튼으로 클릭하시겠습니까? (y/n): ")
                            if proceed.lower() == 'y':
                                btn.click()
                                print(f"'{btn_text}' 버튼을 클릭했습니다.")
                                time.sleep(3)  # 저장 처리 대기
                                complete_button_found = True
                    except Exception as btn_e:
                        print(f"버튼 {i+1} 정보 읽기 실패: {btn_e}")
                
                # 마지막 버튼 자동 선택 옵션
                if not complete_button_found and bottom_buttons:
                    last_button = bottom_buttons[-1]
                    try:
                        last_btn_text = last_button.text.strip() or '(텍스트 없음)'
                        print(f"\n하단 영역의 마지막 버튼: '{last_btn_text}'")
                        proceed = input("하단 영역의 마지막 버튼을 클릭하시겠습니까? (y/n): ")
                        if proceed.lower() == 'y':
                            last_button.click()
                            print(f"마지막 버튼('{last_btn_text}')을 클릭했습니다.")
                            time.sleep(3)
                            complete_button_found = True
                    except Exception as last_e:
                        print(f"마지막 버튼 클릭 중 오류: {last_e}")
            except Exception as bottom_e:
                print(f"하단 버튼 분석 중 오류: {bottom_e}")
        
        # 3단계: '공개 발행' 버튼 찾아 클릭 (모달 대화상자)
        if complete_button_found:
            print("\n2단계: '공개 발행' 버튼을 찾아 클릭합니다...")
            time.sleep(2)  # 모달이 완전히 나타날 때까지 대기
            
            # 3-1. XPath로 '공개 발행' 버튼 찾기 (가장 정확한 방법)
            try:
                print("XPath로 '공개 발행' 버튼 찾기 시도 중...")
                publish_xpath_expressions = [
                    "//button[contains(text(), '공개 발행')]",
                    "//button[contains(text(), '발행')]",
                    "//div[contains(@class, 'layer') or contains(@class, 'modal')]//button[contains(text(), '발행') or contains(text(), '공개')]",
                    "//div[contains(@class, 'layer') or contains(@class, 'modal')]//button[last()]"
                ]
                
                publish_button_found = False
                
                for xpath_expr in publish_xpath_expressions:
                    print(f"XPath 표현식 '{xpath_expr}' 시도 중...")
                    publish_buttons = driver.find_elements(By.XPATH, xpath_expr)
                    if publish_buttons:
                        publish_button = publish_buttons[0]
                        button_text = publish_button.text.strip()
                        print(f"'공개 발행' 버튼을 찾았습니다: {xpath_expr} (텍스트: '{button_text}')")
                        
                        # 버튼 클릭
                        publish_button.click()
                        print(f"'{button_text}' 버튼을 클릭했습니다.")
                        time.sleep(5)  # 발행 처리 대기
                        publish_button_found = True
                        publish_success = True
                        break
                
                # 3-2. CSS 선택자로 '공개 발행' 버튼 찾기
                if not publish_button_found:
                    print("\nCSS 선택자로 '공개 발행' 버튼 찾기 시도 중...")
                    publish_selectors = [
                        ".btn_publish", 
                        ".publish-button",
                        ".layer_post button:last-child",
                        ".layer_publish button:last-child",
                        ".modal_publish button:last-child",
                        ".btn_confirm[data-action='publish']",
                        ".btn_ok"
                    ]
                    
                    for selector in publish_selectors:
                        print(f"선택자 '{selector}' 시도 중...")
                        publish_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        if publish_buttons:
                            publish_button = publish_buttons[0]
                            button_text = publish_button.text.strip()
                            print(f"'공개 발행' 버튼을 찾았습니다: {selector} (텍스트: '{button_text}')")
                            
                            # 버튼 클릭
                            publish_button.click()
                            print(f"'{button_text}' 버튼을 클릭했습니다.")
                            time.sleep(5)  # 발행 처리 대기
                            publish_button_found = True
                            publish_success = True
                            break
                
                # 3-3. JavaScript로 '공개 발행' 버튼 클릭 시도
                if not publish_button_found:
                    try:
                        print("\nJavaScript를 통해 '공개 발행' 버튼 클릭을 시도합니다...")
                        result = driver.execute_script("""
                            // 텍스트로 버튼 찾기
                            var buttons = document.querySelectorAll('button');
                            for (var i = 0; i < buttons.length; i++) {
                                var btnText = buttons[i].textContent.trim();
                                if (btnText.includes('공개 발행') || btnText.includes('발행')) {
                                    console.log('발행 버튼 찾음: ' + btnText);
                                    buttons[i].click();
                                    return "텍스트로 버튼 클릭: " + btnText;
                                }
                            }
                            
                            // 모달/레이어의 마지막 버튼 클릭
                            var modalButtons = document.querySelectorAll('.layer_post button, .layer_publish button, .modal_publish button');
                            if (modalButtons.length > 0) {
                                var lastBtn = modalButtons[modalButtons.length - 1];
                                lastBtn.click();
                                return "모달의 마지막 버튼 클릭: " + lastBtn.textContent.trim();
                            }
                            
                            return false;
                        """)
                        
                        if result:
                            print(f"JavaScript를 통해 '공개 발행' 버튼을 클릭했습니다: {result}")
                            time.sleep(5)  # 발행 처리 대기
                            publish_button_found = True
                            publish_success = True
                        else:
                            print("JavaScript로 '공개 발행' 버튼을 찾지 못했습니다.")
                    except Exception as js_e:
                        print(f"JavaScript를 통한 '공개 발행' 버튼 클릭 중 오류: {js_e}")
                
                # 3-4. 모든 모달 버튼 분석
                if not publish_button_found:
                    print("\n'공개 발행' 버튼을 찾지 못했습니다. 모달 내 모든 버튼 분석 중...")
                    
                    # 모달 레이어 찾기
                    modal_layers = driver.find_elements(By.CSS_SELECTOR, ".layer_post, .layer_publish, .modal_publish, .layer_box, .modal_dialog")
                    if modal_layers:
                        print(f"모달 레이어를 찾았습니다. ({len(modal_layers)}개)")
                        
                        for layer_idx, layer in enumerate(modal_layers):
                            try:
                                print(f"모달 레이어 {layer_idx+1} 분석 중...")
                                
                                # 레이어 내 모든 버튼
                                layer_buttons = layer.find_elements(By.TAG_NAME, "button")
                                print(f"레이어 내 {len(layer_buttons)}개의 버튼을 찾았습니다.")
                                
                                for i, btn in enumerate(layer_buttons):
                                    try:
                                        btn_text = btn.text.strip() or '(텍스트 없음)'
                                        btn_class = btn.get_attribute('class') or '(클래스 없음)'
                                        print(f"버튼 {i+1}: 텍스트='{btn_text}', 클래스='{btn_class}'")
                                        
                                        # 발행 관련 버튼 추정
                                        if ('발행' in btn_text or '공개' in btn_text or 
                                            'publish' in btn_text.lower() or 'confirm' in btn_class.lower()):
                                            print(f"  => 발행 버튼으로 보입니다!")
                                            
                                            proceed = input(f"이 버튼({btn_text})을 발행 버튼으로 클릭하시겠습니까? (y/n): ")
                                            if proceed.lower() == 'y':
                                                btn.click()
                                                print(f"'{btn_text}' 버튼을 클릭했습니다.")
                                                time.sleep(5)  # 발행 처리 대기
                                                publish_button_found = True
                                    except:
                                        continue
                                
                                # 레이어의 마지막 버튼 자동 선택 옵션
                                if not publish_button_found and layer_buttons:
                                    last_button = layer_buttons[-1]
                                    try:
                                        last_btn_text = last_button.text.strip() or '(텍스트 없음)'
                                        print(f"\n레이어의 마지막 버튼: '{last_btn_text}'")
                                        proceed = input("이 버튼을 발행 버튼으로 클릭하시겠습니까? (y/n): ")
                                        if proceed.lower() == 'y':
                                            last_button.click()
                                            print(f"마지막 버튼('{last_btn_text}')을 클릭했습니다.")
                                            time.sleep(5)
                                            publish_button_found = True
                                    except Exception as last_e:
                                        print(f"마지막 버튼 클릭 중 오류: {last_e}")
                                
                                if publish_button_found:
                                    break
                                    
                            except Exception as layer_e:
                                print(f"레이어 {layer_idx+1} 분석 중 오류: {layer_e}")
                    else:
                        print("모달 레이어를 찾지 못했습니다.")
            except Exception as publish_e:
                print(f"'공개 발행' 버튼 찾기 중 오류: {publish_e}")
        
        # 발행 성공 여부 확인
        if publish_success:
            print("\n발행이 성공적으로 완료되었습니다!")
        else:
            print("\n발행 과정에서 문제가 발생했습니다.")
    
    except Exception as e:
        print(f"발행 과정에서 오류 발생: {e}")
    
    print("\n==========================================")
    print("==== 발행 함수 종료 (publish_success: {}) ====".format(publish_success))
    print("==========================================\n")
    
    return publish_success

# 글 작성 프로세스를 별도 함수로 분리하여 코드 재사용성 향상
def write_post(driver, blog_post, format_type=1):
    """
    티스토리에 글 작성 프로세스를 처리하는 함수
    format_type: 1=HTML, 2=일반 텍스트, 3=마크다운
    """
    try:
        # 제목 입력
        print("제목을 입력합니다...")
        try:
            # 사용자가 제공한 정확한 선택자로 제목 입력 필드 찾기
            title_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea#post-title-inp.textarea_tit"))
            )
            
            # 제목 필드 초기화 및 제목만 입력
            title_text = blog_post["title"].strip()
            print(f"입력할 제목: '{title_text}'")
            
            # 방법 1: 직접 clear 및 send_keys 사용
            title_input.clear()
            title_input.send_keys(title_text)
            print("방법 1: 직접 send_keys로 제목 입력 시도")
            time.sleep(1)
            
            # 방법 2: JavaScript로 직접 값 설정
            driver.execute_script("arguments[0].value = arguments[1];", title_input, title_text)
            print("방법 2: JavaScript로 제목 입력 시도")
            
            # 값이 제대로 설정되었는지 확인
            actual_value = driver.execute_script("return arguments[0].value;", title_input)
            print(f"현재 설정된 제목: '{actual_value}'")
            
            # 방법 3: 다양한 이벤트 발생시켜 티스토리가 값 변경을 인식하도록 함
            driver.execute_script("""
                var element = arguments[0];
                var events = ['input', 'change', 'keyup', 'blur', 'focus'];
                events.forEach(function(eventType) {
                    var event = new Event(eventType, { bubbles: true });
                    element.dispatchEvent(event);
                });
            """, title_input)
            print("방법 3: 이벤트 발생으로 제목 변경 인식 유도")
            
            # 방법 4: 포커스 주고 다시 값 설정
            title_input.click()
            time.sleep(0.5)
            title_input.clear()
            title_input.send_keys(title_text)
            print("방법 4: 포커스 후 다시 제목 입력")
            
            # 방법 5: 더 강력한 JavaScript 접근법
            driver.execute_script("""
                // 제목 필드 직접 접근
                var titleField = document.querySelector('textarea#post-title-inp.textarea_tit');
                if (titleField) {
                    // 값 설정
                    titleField.value = arguments[0];
                    
                    // 포커스 및 블러 이벤트 발생
                    titleField.focus();
                    
                    // 키 이벤트 시뮬레이션
                    for (var i = 0; i < arguments[0].length; i++) {
                        var keyEvent = new KeyboardEvent('keypress', {
                            key: arguments[0][i],
                            code: 'Key' + arguments[0][i].toUpperCase(),
                            bubbles: true
                        });
                        titleField.dispatchEvent(keyEvent);
                    }
                    
                    // 변경 이벤트 발생
                    titleField.dispatchEvent(new Event('input', { bubbles: true }));
                    titleField.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    // 블러 이벤트로 변경 확정
                    setTimeout(function() {
                        titleField.blur();
                    }, 100);
                    
                    return "제목 필드에 값 설정 및 이벤트 발생 완료";
                }
                return "제목 필드를 찾지 못함";
            """, title_text)
            
            # 최종 확인
            final_value = driver.execute_script("return document.querySelector('textarea#post-title-inp.textarea_tit').value;")
            print(f"최종 확인된 제목: '{final_value}'")
            
            time.sleep(1)
        except Exception as e:
            print(f"제목 입력 중 오류: {e}")
            
            # 대체 제목 입력 방법 시도
            try:
                print("대체 방법으로 제목 입력 시도...")
                
                # 방법 1: 다양한 선택자로 시도
                title_selectors = [
                    "textarea#post-title-inp.textarea_tit.red",  # 사용자가 제공한 정확한 선택자
                    "textarea#post-title-inp",
                    "textarea.textarea_tit",
                    ".textarea_tit",
                    "textarea[placeholder='제목을 입력하세요']"
                ]
                
                for selector in title_selectors:
                    try:
                        print(f"선택자 '{selector}'로 제목 필드 찾기 시도...")
                        title_input = driver.find_element(By.CSS_SELECTOR, selector)
                        
                        title_text = blog_post["title"].strip()
                        title_input.clear()
                        title_input.send_keys(title_text)
                        
                        print(f"선택자 '{selector}'로 제목 입력 성공")
                        
                        # 이벤트 발생
                        driver.execute_script("""
                            var element = arguments[0];
                            var events = ['input', 'change', 'keyup', 'blur'];
                            events.forEach(function(eventType) {
                                var event = new Event(eventType, { bubbles: true });
                                element.dispatchEvent(event);
                            });
                        """, title_input)
                        
                        break  # 성공했으면 루프 종료
                    except Exception as selector_e:
                        print(f"선택자 '{selector}' 시도 중 오류: {selector_e}")
                        continue
                
                # 방법 2: JavaScript로 직접 제목 필드 찾아서 설정
                driver.execute_script("""
                    // 다양한 방법으로 제목 필드 찾기
                    var titleField = document.getElementById('post-title-inp') || 
                                    document.querySelector('.textarea_tit') || 
                                    document.querySelector('textarea[placeholder*="제목"]');
                    
                    if (titleField) {
                        titleField.value = arguments[0];
                        
                        // 이벤트 발생
                        var events = ['input', 'change', 'keyup', 'blur'];
                        events.forEach(function(eventType) {
                            var event = new Event(eventType, { bubbles: true });
                            titleField.dispatchEvent(event);
                        });
                        
                        console.log("JavaScript로 제목 필드 값 설정: " + arguments[0]);
                        return true;
                    }
                    return false;
                """, blog_post["title"].strip())
                
                print("JavaScript를 통한 대체 제목 입력 시도 완료")
                
            except Exception as e2:
                print(f"대체 제목 입력 방법도 실패: {e2}")
        
        # 에디터 초기 모드 확인
        current_mode = check_editor_mode(driver)
        print(f"현재 에디터 모드: {current_mode}")
        
        # 에디터 모드 전환 (HTML/마크다운)
        if format_type == 1:  # HTML 모드
            if current_mode != "html":
                switch_to_html_mode(driver)
        elif format_type == 3:  # 마크다운 모드
            if current_mode != "markdown":
                switch_to_markdown_mode(driver)
        else:  # 일반 텍스트 모드 (기본값)
            if current_mode == "html" or current_mode == "markdown":
                switch_to_wysiwyg_mode(driver)
        
        # 모드 전환 후 다시 확인
        time.sleep(2)
        current_mode = check_editor_mode(driver)
        print(f"모드 전환 후 에디터 모드: {current_mode}")
        
        # 본문 입력 - 현재 에디터 모드에 맞게 처리
        try:
            print("본문을 입력합니다...")
            content = blog_post["content"]
            
            # iframe 확인 및 전환
            iframe_editor = find_editor_iframe(driver)
            
            if current_mode == "html":
                # HTML 모드일 때 - JavaScript를 통해 직접 HTML 콘텐츠 설정
                html_success = set_html_content(driver, content, iframe_editor)
                
                # HTML 콘텐츠 설정 후 상태 확인
                print("\n💡 HTML 콘텐츠 설정 완료 후 상태 체크를 시작합니다...")
                check_success, status_info = check_html_content_status(driver)
                
                if not html_success or not check_success:
                    print("⚠️ HTML 콘텐츠 설정에 문제가 있을 수 있습니다.")
                    print("수동으로 확인해주세요.")
                    input("확인 후 Enter 키를 눌러 계속 진행하세요...")
            elif current_mode == "markdown":
                # 마크다운 모드일 때 - 마크다운 에디터에 콘텐츠 설정
                set_markdown_content(driver, content, iframe_editor)
            else:
                # 일반 텍스트(WYSIWYG) 모드일 때 - 에디터에 일반 텍스트 입력
                set_wysiwyg_content(driver, content, iframe_editor)
        
        except Exception as e:
            print(f"본문 입력 중 오류: {e}")
            driver.switch_to.default_content()  # 혹시 모를 iframe에서 빠져나옴
        
        # 태그 입력
        try:
            print("태그를 입력합니다...")
            input_tags(driver, blog_post["tags"])
        except Exception as e:
            print(f"태그 입력 중 오류: {e}")
        
        # 임시저장 버튼 클릭
        try:
            print("임시저장 버튼을 찾습니다...")
            save_post(driver)
        except Exception as e:
            print(f"임시저장 버튼 클릭 중 오류: {e}")
        
        return True
    except Exception as e:
        print(f"글 작성 전체 과정에서 오류 발생: {e}")
        return False

def check_editor_mode(driver):
    """
    현재 에디터 모드를 확인하는 함수
    return: 'html', 'markdown' 또는 'wysiwyg'(일반 텍스트)
    """
    try:
        # JavaScript를 사용하여 에디터 모드 확인
        mode = driver.execute_script("""
            // HTML 모드 확인
            if (document.querySelector('.html-editor') || 
                document.querySelector('.switch-html.active') ||
                document.querySelector('button[data-mode="html"].active') ||
                (window.tistoryEditor && window.tistoryEditor.isHtmlMode)) {
                return 'html';
            } 
            // 마크다운 모드 확인
            else if (document.querySelector('.markdown-editor') || 
                     document.querySelector('.switch-markdown.active') ||
                     document.querySelector('button[data-mode="markdown"].active') ||
                     (window.tistoryEditor && window.tistoryEditor.isMarkdownMode)) {
                return 'markdown';
            }
            // WYSIWYG 모드 (기본)
            return 'wysiwyg';
        """)
        return mode if mode else "wysiwyg"
    except:
        return "wysiwyg"  # 확인할 수 없는 경우 기본값

def switch_to_html_mode(driver):
    """HTML 모드로 전환"""
    try:
        print("HTML 모드로 전환을 시도합니다...")
        
        # 방법 1: 사용자가 제공한 HTML 요소 직접 선택
        try:
            # 사용자가 제공한 요소 ID로 직접 찾기
            html_element = driver.find_element(By.ID, "editor-mode-html")
            print("HTML 모드 요소(#editor-mode-html)를 ID로 찾았습니다.")
            
            # 요소 정보 출력
            element_class = html_element.get_attribute("class")
            element_text = html_element.text
            print(f"HTML 요소 정보: class='{element_class}', text='{element_text}'")
            
            # 직접 클릭 시도
            html_element.click()
            print("HTML 모드 요소를 클릭했습니다.")
            time.sleep(1)
            
            # 확인 대화상자가 나타날 수 있으므로 처리
            try:
                alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
                if alert:
                    print(f"알림창 발견: '{alert.text}'")
                    alert.accept()
                    print("알림창의 '확인' 버튼을 클릭했습니다.")
            except:
                pass
                
            return True
        except Exception as id_e:
            print(f"HTML 모드 요소 직접 클릭 실패: {id_e}")
        
        # 방법 2: 모드 버튼 클릭 후 HTML 모드 선택
        try:
            # 모드 버튼 클릭하여 드롭다운 표시
            mode_btn = driver.find_element(By.CSS_SELECTOR, "#editor-mode-layer-btn")
            mode_btn.click()
            print("에디터 모드 버튼을 클릭하여 드롭다운 메뉴를 표시했습니다.")
            time.sleep(1)
            
            # HTML 모드 선택 (span 요소)
            html_span = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "editor-mode-html-text"))
            )
            
            # 클릭 전 요소 정보 출력
            print(f"HTML span 요소 발견: id='{html_span.get_attribute('id')}', text='{html_span.text}'")
            
            # 클릭
            html_span.click()
            print("HTML 모드 span 요소를 클릭했습니다.")
            time.sleep(1)
            
            # 확인 대화상자 처리
            try:
                alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
                if alert:
                    print(f"알림창 발견: '{alert.text}'")
                    alert.accept()
                    print("알림창의 '확인' 버튼을 클릭했습니다.")
            except:
                pass
                
            return True
        except Exception as dropdown_e:
            print(f"드롭다운을 통한 HTML 모드 선택 실패: {dropdown_e}")
        
        # 방법 3: 일반적인 HTML 버튼 찾기
        html_buttons = []
        
        # CSS 선택자로 찾기
        primary_buttons = driver.find_elements(By.CSS_SELECTOR, 
            ".btn_html, button[data-mode='html'], .html-mode-button, .switch-html, .mce-i-code")
        if primary_buttons:
            html_buttons.extend(primary_buttons)
            print(f"CSS 선택자로 {len(primary_buttons)}개의 HTML 버튼을 찾았습니다.")
        
        # 버튼 텍스트로 찾기
        text_buttons = driver.find_elements(By.XPATH, 
            "//button[contains(text(), 'HTML') or @title='HTML' or @aria-label='HTML']")
        if text_buttons:
            html_buttons.extend(text_buttons)
            print(f"텍스트로 {len(text_buttons)}개의 HTML 버튼을 찾았습니다.")
        
        # 에디터 툴바에서 찾기
        toolbar_buttons = driver.find_elements(By.CSS_SELECTOR, 
            ".editor-toolbar button, .mce-toolbar button, .tox-toolbar button, .toolbar-group button")
        for btn in toolbar_buttons:
            try:
                btn_title = btn.get_attribute('title') or ''
                btn_text = btn.text or ''
                if 'html' in btn_title.lower() or 'html' in btn_text.lower() or 'source' in btn_title.lower():
                    html_buttons.append(btn)
                    print(f"툴바에서 HTML 버튼을 찾았습니다: {btn_title or btn_text}")
            except:
                pass
        
        # 찾은 버튼 클릭 시도
        if html_buttons:
            html_buttons[0].click()
            print("HTML 모드 버튼을 클릭했습니다.")
            time.sleep(1)
            
            # 확인 대화상자 처리
            try:
                alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
                if alert:
                    alert.accept()
                    print("알림창을 처리했습니다.")
            except:
                pass
                
            return True
            
        # 방법 4: JavaScript로 시도
        print("버튼을 찾지 못했습니다. JavaScript로 HTML 모드 전환을 시도합니다...")
        result = driver.execute_script("""
            // 사용자가 제공한 요소 ID로 직접 클릭
            var editorHtmlElement = document.getElementById('editor-mode-html');
            if (editorHtmlElement) {
                editorHtmlElement.click();
                return "사용자 제공 HTML 요소 클릭 성공";
            }
            
            // 티스토리 에디터 API 확인
            if (window.tistoryEditor) {
                if (typeof tistoryEditor.switchHtml === 'function') {
                    tistoryEditor.switchHtml();
                    return "tistoryEditor.switchHtml() 호출 성공";
                }
                
                // 티스토리 이벤트 발생
                var htmlButton = document.querySelector('[data-mode="html"], .btn_html, .switch-html');
                if (htmlButton) {
                    htmlButton.click();
                    return "HTML 버튼 클릭 성공";
                }
            }
            
            // TinyMCE 에디터 확인
            if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                try {
                    if (tinyMCE.activeEditor.plugins.code) {
                tinyMCE.activeEditor.execCommand('mceCodeEditor');
                        return "TinyMCE 코드 에디터 활성화 성공";
                    }
                } catch(e) {
                    console.log("TinyMCE 코드 에디터 오류:", e);
                }
            }
            
            // 모든 HTML 관련 요소 검색
            var htmlElements = [
                document.querySelector('div[id*="html"]'),
                document.querySelector('button[id*="html"]'),
                document.querySelector('span[id*="html"]')
            ];
            
            for (var i = 0; i < htmlElements.length; i++) {
                if (htmlElements[i]) {
                    htmlElements[i].click();
                    return "HTML 관련 요소 클릭 성공";
                }
            }
            
            return "HTML 모드로 전환할 수 있는 방법을 찾지 못했습니다.";
        """)
        
        print(f"JavaScript 실행 결과: {result}")
        time.sleep(2)  # 모드 전환 대기
        
        # 모드 전환 성공 여부 확인
        current_mode = check_editor_mode(driver)
        if current_mode == "html":
            print("HTML 모드로 성공적으로 전환되었습니다.")
            return True
        else:
            print(f"모드 전환 실패. 현재 모드: {current_mode}")
        return False
            
    except Exception as e:
        print(f"HTML 모드 전환 중 오류: {e}")
        return False

def switch_to_markdown_mode(driver):
    """마크다운 모드로 전환"""
    try:
        print("마크다운 모드로 전환을 시도합니다...")
        
        # 1. CSS 선택자로 마크다운 버튼 찾기
        markdown_buttons = driver.find_elements(By.CSS_SELECTOR, 
            ".btn_markdown, button[data-mode='markdown'], .markdown-mode-button, button[title*='마크다운']")
        
        if markdown_buttons:
            markdown_buttons[0].click()
            print("마크다운 모드로 전환했습니다.")
            time.sleep(1)
            return True
        
        # 2. JavaScript를 사용하여 마크다운 모드 전환
        result = driver.execute_script("""
            // 티스토리 에디터 API 사용
            if (window.tistoryEditor && window.tistoryEditor.switchMarkdown) {
                window.tistoryEditor.switchMarkdown();
                return true;
            }
            
            // 마크다운 관련 버튼 찾기
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                if (
                    (btn.textContent && btn.textContent.toLowerCase().includes('markdown')) ||
                    (btn.title && btn.title.toLowerCase().includes('markdown')) ||
                    (btn.dataset && btn.dataset.mode && btn.dataset.mode.toLowerCase().includes('markdown')) ||
                    (btn.className && btn.className.toLowerCase().includes('markdown'))
                ) {
                    btn.click();
                    return true;
                }
            }
            
            return false;
        """)
        
        if result:
            print("JavaScript를 통해 마크다운 모드로 전환했습니다.")
            time.sleep(1)
            return True
        
        # 3. XPath를 사용하여 마크다운 버튼 찾기
        markdown_button_xpath = driver.find_elements(By.XPATH, 
            "//button[contains(@class, 'markdown') or contains(@title, 'markdown') or contains(@aria-label, 'markdown') or contains(text(), 'Markdown')]")
        
        if markdown_button_xpath:
            markdown_button_xpath[0].click()
            print("XPath를 통해 마크다운 모드 버튼을 찾아 클릭했습니다.")
            time.sleep(1)
            return True
            
        # 한국어 마크다운 버튼도 시도
        markdown_button_ko = driver.find_elements(By.XPATH, 
            "//button[contains(text(), '마크다운') or contains(@title, '마크다운')]")
        if markdown_button_ko:
            markdown_button_ko[0].click()
            print("한글 버튼명으로 마크다운 모드 버튼을 찾아 클릭했습니다.")
            time.sleep(1)
            return True
            
        print("마크다운 모드로 전환을 시도했으나 실패했습니다.")
        return False
    except Exception as e:
        print(f"마크다운 모드 전환 중 오류: {e}")
        return False

def switch_to_wysiwyg_mode(driver):
    """일반 텍스트(WYSIWYG) 모드로 전환"""
    try:
        print("일반 텍스트 모드로 전환을 시도합니다...")
        
        # 1. CSS 선택자로 위지윅 버튼 찾기
        wysiwyg_buttons = driver.find_elements(By.CSS_SELECTOR, 
            ".btn_editor, button[data-mode='editor'], .wysiwyg-button, .switch-wysiwyg")
        
        if wysiwyg_buttons:
            wysiwyg_buttons[0].click()
            print("일반 텍스트 모드로 전환했습니다.")
            time.sleep(1)
            return True
        
        # 2. JavaScript를 사용하여 위지윅 모드 전환
        result = driver.execute_script("""
            // 티스토리 에디터 API 사용
            if (window.tistoryEditor && window.tistoryEditor.switchWysiwyg) {
                window.tistoryEditor.switchWysiwyg();
                return true;
            }
            
            // 위지윅 관련 버튼 찾기
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                if (
                    (btn.textContent && (btn.textContent.toLowerCase().includes('wysiwyg') || btn.textContent.toLowerCase().includes('에디터'))) ||
                    (btn.title && (btn.title.toLowerCase().includes('wysiwyg') || btn.title.toLowerCase().includes('에디터'))) ||
                    (btn.dataset && btn.dataset.mode && btn.dataset.mode.toLowerCase().includes('editor')) ||
                    (btn.className && (btn.className.toLowerCase().includes('wysiwyg') || btn.className.toLowerCase().includes('editor')))
                ) {
                    btn.click();
                    return true;
                }
            }
            
            return false;
        """)
        
        if result:
            print("JavaScript를 통해 일반 텍스트 모드로 전환했습니다.")
            time.sleep(1)
            return True
            
        print("일반 텍스트 모드로 전환을 시도했으나 실패했습니다.")
        return False
    except Exception as e:
        print(f"일반 텍스트 모드 전환 중 오류: {e}")
        return False

def find_editor_iframe(driver):
    """에디터 iframe을 찾아 반환"""
    try:
        iframe_editor = None
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            for iframe in iframes:
                try:
                    iframe_id = iframe.get_attribute("id") or ""
                    iframe_name = iframe.get_attribute("name") or ""
                    iframe_src = iframe.get_attribute("src") or ""
                    print(f"iframe: id='{iframe_id}', name='{iframe_name}', src='{iframe_src}'")
                    if "editor" in iframe_id.lower():
                        iframe_editor = iframe
                        print(f"에디터 iframe을 찾았습니다: {iframe_id}")
                        break
                except:
                    pass
        return iframe_editor
    except:
        return None

def set_html_content(driver, content, iframe_editor):
    """HTML 모드에서 콘텐츠 설정 - 티스토리 에디터 구조에 최적화 (완전 개선 버전)"""
    try:
        print("\n=== HTML 콘텐츠 설정 시도 (완전 개선 버전) ===")
        print(f"콘텐츠 길이: {len(content)} 글자")
        
        # 디버깅을 위해 콘텐츠 시작 부분 출력
        content_preview = content[:200] + "..." if len(content) > 200 else content
        print(f"콘텐츠 미리보기: {content_preview}")
        
        # HTML 형식 확인 및 보정
        if not content.strip().startswith("<"):
            print("경고: 콘텐츠에 HTML 태그가 없습니다. HTML 태그로 감싸줍니다.")
            content = f"<div>{content}</div>"
        
        content_set_success = False
        
        # 방법 1: iframe 내부에서 contenteditable 요소 우선 처리
        if iframe_editor:
            try:
                print("\n=== 방법 1: iframe 내부 contenteditable 요소 처리 ===")
                driver.switch_to.frame(iframe_editor)
                
                # iframe 내부에서 모든 가능한 에디터 요소에 콘텐츠 설정
                iframe_result = driver.execute_script("""
                    var content = arguments[0];
                    var success = false;
                    var method = "";
                    var details = {};
                    
                    console.log("=== iframe 내부 HTML 콘텐츠 설정 (개선 버전) ===");
                    
                    // 1. contenteditable 요소 우선 처리 (가장 중요)
                    var editables = document.querySelectorAll('[contenteditable="true"]');
                    console.log("contenteditable 요소 개수:", editables.length);
                    details.editableCount = editables.length;
                    
                    for (var i = 0; i < editables.length; i++) {
                        var editable = editables[i];
                        var rect = editable.getBoundingClientRect();
                        
                        console.log("contenteditable 요소", i, "- 크기:", rect.width, "x", rect.height);
                        
                        // 크기가 충분한 요소만 본문 에디터로 간주 (50x50 이상)
                        if (rect.width > 50 && rect.height > 50) {
                            try {
                                // 포커스 먼저
                                editable.focus();
                                
                                // HTML 콘텐츠 설정
                                editable.innerHTML = content;
                                
                                // 다양한 이벤트 발생
                                var events = ['input', 'change', 'keyup', 'paste', 'blur', 'focus'];
                                events.forEach(function(eventType) {
                                    try {
                                        var event = new Event(eventType, { bubbles: true, cancelable: true });
                                        editable.dispatchEvent(event);
                                    } catch (e) {
                                        console.log("이벤트 발생 실패:", eventType);
                                    }
                                });
                                
                                // 키보드 이벤트도 시뮬레이션
                                try {
                                    var keyEvent = new KeyboardEvent('keydown', {
                                        bubbles: true,
                                        key: ' ',
                                        keyCode: 32
                                    });
                                    editable.dispatchEvent(keyEvent);
                                } catch (e) {
                                    console.log("키보드 이벤트 실패");
                                }
                                
                                console.log("contenteditable 설정 성공 (크기:", rect.width, "x", rect.height, ")");
                                success = true;
                                method = "contenteditable (" + rect.width + "x" + rect.height + ")";
                                details.selectedEditable = i;
                                break;
                            } catch (e) {
                                console.error("contenteditable 설정 실패:", e);
                            }
                        }
                    }
                    
                    // 2. textarea 처리 (contenteditable이 없는 경우)
                    if (!success) {
                        var textareas = document.querySelectorAll('textarea');
                        console.log("textarea 요소 개수:", textareas.length);
                        details.textareaCount = textareas.length;
                        
                        for (var i = 0; i < textareas.length; i++) {
                            var ta = textareas[i];
                            
                            // 제목, 태그 필드 제외
                            if (ta.id === 'post-title-inp' || ta.id === 'tag' || 
                                ta.className.includes('textarea_tit') ||
                                (ta.placeholder && (ta.placeholder.includes('태그') || ta.placeholder.includes('제목')))) {
                                continue;
                            }
                            
                            try {
                                ta.value = content;
                                ta.focus();
                                
                                var events = ['input', 'change', 'keyup', 'paste'];
                                events.forEach(function(eventType) {
                                    ta.dispatchEvent(new Event(eventType, { bubbles: true }));
                                });
                                
                                console.log("textarea 설정 성공:", ta.id || "ID없음");
                                success = true;
                                method = "textarea";
                                details.selectedTextarea = i;
                                break;
                            } catch (e) {
                                console.error("textarea 설정 실패:", e);
                            }
                        }
                    }
                    
                    // 3. document.body 직접 설정 (최후 수단)
                    if (!success && document.body) {
                        try {
                            if (document.body.contentEditable === "true" || 
                                document.body.getAttribute('contenteditable') === "true") {
                                document.body.innerHTML = content;
                                document.body.focus();
                                document.body.dispatchEvent(new Event('input', { bubbles: true }));
                                
                                console.log("document.body 직접 설정 성공");
                                success = true;
                                method = "document.body";
                            }
                        } catch (e) {
                            console.error("document.body 설정 실패:", e);
                        }
                    }
                    
                    return {
                        success: success,
                        method: method,
                        details: details
                    };
                """, content)
                
                print(f"iframe 내부 설정 결과: {iframe_result}")
                
                if iframe_result.get('success'):
                    print(f"✅ iframe 내부 설정 성공 (방법: {iframe_result.get('method')})")
                    
                    # 설정 후 검증
                    time.sleep(0.3)  # DOM 업데이트 대기
                    
                    verification = driver.execute_script("""
                        var found = false;
                        var contentLength = 0;
                        var contentPreview = "";
                        
                        // contenteditable 확인
                        var editables = document.querySelectorAll('[contenteditable="true"]');
                        for (var i = 0; i < editables.length; i++) {
                            var editable = editables[i];
                            var rect = editable.getBoundingClientRect();
                            if (rect.width > 50 && rect.height > 50 && 
                                editable.innerHTML && editable.innerHTML.length > 100) {
                                found = true;
                                contentLength = editable.innerHTML.length;
                                contentPreview = editable.innerHTML.substring(0, 100) + "...";
                                break;
                            }
                        }
                        
                        // textarea 확인
                        if (!found) {
                            var textareas = document.querySelectorAll('textarea');
                            for (var i = 0; i < textareas.length; i++) {
                                var ta = textareas[i];
                                if (ta.id !== 'post-title-inp' && ta.id !== 'tag' && 
                                    !ta.className.includes('textarea_tit') &&
                                    ta.value && ta.value.length > 100) {
                                    found = true;
                                    contentLength = ta.value.length;
                                    contentPreview = ta.value.substring(0, 100) + "...";
                                    break;
                                }
                            }
                        }
                        
                        return {
                            found: found,
                            contentLength: contentLength,
                            contentPreview: contentPreview
                        };
                    """)
                    
                    print(f"검증 결과: 콘텐츠 발견={verification.get('found')}, 길이={verification.get('contentLength')}")
                    if verification.get('contentPreview'):
                        print(f"콘텐츠 미리보기: {verification.get('contentPreview')}")
                    
                    if verification.get('found') and verification.get('contentLength') > 100:
                        print("✅ 최종 검증 성공!")
                        content_set_success = True
                    else:
                        print("❌ 검증 실패: 콘텐츠가 제대로 설정되지 않았습니다.")
                
                driver.switch_to.default_content()
                
            except Exception as iframe_e:
                print(f"iframe 처리 중 오류: {iframe_e}")
                try:
                    driver.switch_to.default_content()
                except:
                    pass
        
        # 방법 2: 페이지 레벨에서 티스토리 에디터 API 호출
        if not content_set_success:
            try:
                print("\n=== 방법 2: 티스토리 에디터 API 호출 ===")
                
                api_result = driver.execute_script("""
                    var content = arguments[0];
                    
                    // 티스토리 에디터 API 시도
                    if (window.tistoryEditor) {
                        console.log("tistoryEditor 객체 발견");
                        
                        var methods = [
                            'setHtmlContent',
                            'setValue', 
                            'setContent',
                            'insertHtml',
                            'setData'
                        ];
                        
                        for (var i = 0; i < methods.length; i++) {
                            var methodName = methods[i];
                            if (typeof tistoryEditor[methodName] === 'function') {
                                try {
                                    tistoryEditor[methodName](content);
                                    console.log("API 호출 성공:", methodName);
                                    return methodName + " 성공";
                                } catch (e) {
                                    console.error("API 호출 실패:", methodName, e);
                                }
                            }
                        }
                    }
                    
                    return "API 호출 실패";
                """, content)
                
                print(f"API 호출 결과: {api_result}")
                
                if "성공" in str(api_result):
                    print("✅ 티스토리 에디터 API를 통한 설정 성공")
                    content_set_success = True
                    
            except Exception as api_e:
                print(f"API 호출 중 오류: {api_e}")
        
        # 최종 결과 반환
        if content_set_success:
            print("\n✅ HTML 콘텐츠 설정 완료!")
            return True
        else:
            print("\n❌ HTML 콘텐츠 설정 실패!")
            print("수동으로 본문을 입력해주세요.")
            return False
            
    except Exception as e:
        print(f"HTML 콘텐츠 설정 중 전체 오류: {e}")
        return False

def set_markdown_content(driver, content, iframe_editor):
    """마크다운 모드에서 콘텐츠 설정"""
    try:
        # 1. JavaScript를 사용하여 직접 마크다운 콘텐츠 설정
        result = driver.execute_script("""
            // 티스토리 에디터 API 사용
            if (window.tistoryEditor && window.tistoryEditor.setMarkdownContent) {
                window.tistoryEditor.setMarkdownContent(arguments[0]);
                return true;
            }
            
            // 마크다운 에디터 요소 찾기
            var mdEditor = document.querySelector('.markdown-editor textarea, [contenteditable="true"].markdown, textarea.markdown-code');
            if (mdEditor) {
                mdEditor.value = arguments[0];
                mdEditor.innerHTML = arguments[0];
                return true;
            }
            
            return false;
        """, content)
        
        if result:
            print("JavaScript를 통해 마크다운 콘텐츠를 설정했습니다.")
            return True
            
        # 2. 직접 마크다운 입력 필드 찾기
        markdown_editors = driver.find_elements(By.CSS_SELECTOR, 
            "textarea.markdown-editor, [contenteditable='true'].markdown-code")
        
        if markdown_editors:
            markdown_editors[0].clear()
            markdown_editors[0].send_keys(content)
            print("마크다운 에디터 요소에 콘텐츠를 입력했습니다.")
            return True
            
        # 3. iframe 내부에 직접 콘텐츠 설정 시도
        if iframe_editor:
            driver.switch_to.frame(iframe_editor)
            
            try:
                # 마크다운 모드에서는 textarea나 contenteditable 요소에 내용 설정
                editor_element = driver.find_element(By.CSS_SELECTOR, "textarea, [contenteditable='true']")
                editor_element.clear()
                editor_element.send_keys(content)
                print("iframe 내부의 에디터에 마크다운 콘텐츠를 입력했습니다.")
                driver.switch_to.default_content()
                return True
            except:
                driver.switch_to.default_content()
                
        print("마크다운 콘텐츠 설정을 시도했으나 실패했습니다.")
        return False
    except Exception as e:
        print(f"마크다운 콘텐츠 설정 중 오류: {e}")
        return False

def set_wysiwyg_content(driver, content, iframe_editor):
    """일반 텍스트(WYSIWYG) 모드에서 콘텐츠 설정"""
    try:
        # 1. TinyMCE 에디터 사용 시도
        if iframe_editor:
            driver.switch_to.frame(iframe_editor)
            
            try:
                # TinyMCE 에디터 본문 요소 찾기
                body_editor = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "tinymce"))
                )
                
                # 기존 내용 지우기
                body_editor.clear()
                
                # 내용이 많은 경우 작은 부분으로 나누어 입력
                chunk_size = 1000
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    body_editor.send_keys(chunk)
                    time.sleep(0.5)
                    
                print("TinyMCE 에디터에 본문을 입력했습니다.")
                driver.switch_to.default_content()
                return True
            except:
                driver.switch_to.default_content()
        
        # 2. JavaScript를 사용하여 콘텐츠 설정
        result = driver.execute_script("""
            // 티스토리 에디터 API 사용
            if (window.tistoryEditor && window.tistoryEditor.setContent) {
                window.tistoryEditor.setContent(arguments[0]);
                return true;
            }
            
            // TinyMCE API 사용
            if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                tinyMCE.activeEditor.setContent(arguments[0]);
                return true;
            }
            
            return false;
        """, content)
        
        if result:
            print("JavaScript를 통해 콘텐츠를 설정했습니다.")
            return True
            
        # 3. contenteditable div 또는 textarea 찾기
        content_elements = driver.find_elements(By.CSS_SELECTOR, 
            "[contenteditable='true'], textarea.editor, .editor-textarea, #content, .editable-area, .ke-content")
        
        if content_elements:
            content_elements[0].clear()
            
            # 내용이 많은 경우 작은 부분으로 나누어 입력
            chunk_size = 1000
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                content_elements[0].send_keys(chunk)
                time.sleep(0.5)
                
            print("에디터 요소에 본문을 입력했습니다.")
            return True
            
        # 4. XPath로 에디터 영역 찾기
        editor_xpath = driver.find_elements(By.XPATH, 
            "//*[contains(@class, 'editor') or contains(@id, 'editor')]//div[contains(@class, 'content') or @contenteditable='true']")
        
        if editor_xpath:
            editor_xpath[0].clear()
            
            # 내용이 많은 경우 작은 부분으로 나누어 입력
            chunk_size = 1000
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                editor_xpath[0].send_keys(chunk)
                time.sleep(0.5)
                
            print("XPath를 통해 찾은 에디터 영역에 본문을 입력했습니다.")
            return True
            
        print("일반 텍스트 콘텐츠 설정을 시도했으나 실패했습니다.")
        return False
    except Exception as e:
        print(f"일반 텍스트 콘텐츠 설정 중 오류: {e}")
        return False

def input_tags(driver, tags):
    """태그 입력 함수"""
    try:
        # CSS 선택자로 태그 입력 필드 찾기
        tag_selectors = [
            ".tag-input", 
            "#tag", 
            "input[name='tag']", 
            ".tag-box input", 
            ".post-tag-input", 
            ".tagname", 
            "input[placeholder*='태그']", 
            "[data-role='tag-input']", 
            ".editor-tag input", 
            "#editor-root input[type='text']:not([id='post-title-inp'])"
        ]
        
        tag_found = False
        for selector in tag_selectors:
            try:
                tag_inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                if tag_inputs:
                    tag_input = tag_inputs[0]
                    
                    # 입력 필드가 표시되고 활성화되어 있는지 확인
                    if tag_input.is_displayed() and tag_input.is_enabled():
                        # 현재 값 지우기
                        tag_input.clear()
                        
                        # 쉼표로 구분된 태그를 하나씩 입력
                        tags_list = tags.split(',')
                        for tag in tags_list:
                            tag = tag.strip()
                            if tag:
                                tag_input.send_keys(tag)
                                tag_input.send_keys(Keys.ENTER)
                                time.sleep(0.5)
                            
                            print(f"태그 입력 필드를 찾았습니다: {selector}")
                            tag_found = True
                            break
            except Exception as selector_e:
                print(f"'{selector}' 선택자로 태그 입력 중 오류: {selector_e}")
        
        # 2. JavaScript를 사용하여 태그 입력 시도
        if not tag_found:
            try:
                print("JavaScript를 통해 태그 입력을 시도합니다...")
                js_result = driver.execute_script("""
                    // 티스토리 태그 입력 API 사용
                    if (window.tistoryEditor && window.tistoryEditor.setTags) {
                        window.tistoryEditor.setTags(arguments[0].split(',').map(function(tag) { return tag.trim(); }));
                        return true;
                    }
                    
                    // 태그 입력 필드 찾기
                    var tagInputs = [
                        document.querySelector('.tag-input'),
                        document.querySelector('#tag'),
                        document.querySelector('input[name="tag"]'),
                        document.querySelector('.tag-box input'),
                        document.querySelector('.post-tag-input'),
                        document.querySelector('.tagname'),
                        document.querySelector('input[placeholder*="태그"]'),
                        document.querySelector('[data-role="tag-input"]')
                    ];
                    
                    // 첫 번째로 찾은 유효한 입력 필드 사용
                    for (var i = 0; i < tagInputs.length; i++) {
                        var input = tagInputs[i];
                        if (input && input.style.display !== 'none') {
                            // 태그 입력
                            var tags = arguments[0].split(',');
                            
                            // 일반적인 입력 방식
                            input.value = '';
                            for (var j = 0; j < tags.length; j++) {
                                var tag = tags[j].trim();
                                if (tag) {
                                    input.value = tag;
                                    
                                    // Enter 키 이벤트 발생
                                    var event = new KeyboardEvent('keydown', {
                                        'key': 'Enter',
                                        'code': 'Enter',
                                        'keyCode': 13,
                                        'which': 13,
                                        'bubbles': true
                                    });
                                    input.dispatchEvent(event);
                                }
                            }
                            return true;
                        }
                    }
                    
                    return false;
                """, tags)
                
                if js_result:
                    print(f"JavaScript를 통해 태그를 입력했습니다: {js_result}")
                    tag_found = True
            except Exception as js_e:
                print(f"JavaScript를 통한 태그 입력 중 오류: {js_e}")
        
        # 3. XPath를 사용하여 태그 입력 필드 찾기
        if not tag_found:
            try:
                tag_xpath_expressions = [
                    "//input[contains(@placeholder, '태그')]",
                    "//div[contains(@class, 'tag') or contains(@class, 'Tag')]//input",
                    "//label[contains(text(), '태그') or contains(text(), '태그입력')]//following::input",
                    "//input[contains(@id, 'tag') or contains(@name, 'tag')]"
                ]
                
                for xpath_expr in tag_xpath_expressions:
                    tag_inputs_xpath = driver.find_elements(By.XPATH, xpath_expr)
                    if tag_inputs_xpath:
                        tag_input = tag_inputs_xpath[0]
                        
                        # 현재 값 지우기
                        tag_input.clear()
                        
                        # 쉼표로 구분된 태그를 하나씩 입력
                        tags_list = tags.split(',')
                        for tag in tags_list:
                            tag = tag.strip()
                            if tag:
                                tag_input.send_keys(tag)
                                tag_input.send_keys(Keys.ENTER)
                                time.sleep(0.5)
                        
                        print(f"XPath({xpath_expr})를 통해 태그 입력 필드를 찾았습니다.")
                        tag_found = True
                        break
            except Exception as xpath_e:
                print(f"XPath를 통한 태그 입력 필드 찾기 중 오류: {xpath_e}")
        
        # 4. 태그 입력 필드를 찾지 못한 경우
        if not tag_found:
            print("태그 입력 필드를 찾지 못했습니다.")
            
            # 모든 입력 필드 출력
            inputs = driver.find_elements(By.TAG_NAME, "input")
            print(f"페이지에서 {len(inputs)}개의 입력 필드를 찾았습니다.")
            
            text_inputs = []
            for i, inp in enumerate(inputs):
                try:
                    inp_type = inp.get_attribute("type") or ""
                    if inp_type == "text":
                        inp_name = inp.get_attribute("name") or ""
                        inp_id = inp.get_attribute("id") or ""
                        inp_placeholder = inp.get_attribute("placeholder") or ""
                        inp_class = inp.get_attribute("class") or ""
                        
                        # 제목 입력 필드가 아닌 텍스트 입력 필드
                        if inp_id != "post-title-inp":
                            text_inputs.append((i, inp, inp_name, inp_id, inp_placeholder, inp_class))
                            print(f"텍스트 입력 필드 {i+1}: name='{inp_name}', id='{inp_id}', placeholder='{inp_placeholder}', class='{inp_class}'")
                except:
                    pass
            
            # 텍스트 입력 필드가 있다면 사용자에게 선택 요청
            if text_inputs:
                print("\n위 텍스트 입력 필드 중 태그 입력에 사용할 필드 번호를 선택하세요:")
                choice = input("필드 번호 (Enter 키를 누르면 건너뜀): ")
                
                if choice.strip():
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(text_inputs):
                            selected_input = text_inputs[idx][1]
                            selected_input.clear()
                            
                            # 쉼표로 구분된 태그를 하나씩 입력
                            tags_list = tags.split(',')
                            for tag in tags_list:
                                tag = tag.strip()
                                if tag:
                                    selected_input.send_keys(tag)
                                    selected_input.send_keys(Keys.ENTER)
                                    time.sleep(0.5)
                                
                                print(f"선택한 입력 필드에 태그를 입력했습니다.")
                                tag_found = True
                    except:
                        print("잘못된 입력입니다.")
    
    except Exception as e:
        print(f"태그 입력 중 오류: {e}")
    
    return tag_found

def save_post(driver):
    """임시저장 버튼 클릭"""
    try:
        # 다양한 임시저장 버튼 선택자로 시도
        save_selectors = [
            ".btn_save", 
            ".btn-save", 
            ".save-button", 
            "#save-temp", 
            "button:contains('임시저장')",
            "button[data-action='save']",
            "button.draft",
            ".preview-btn" # 티스토리의 '미리보기' 버튼 (임시저장 기능 포함)
        ]
        
        save_found = False
        for selector in save_selectors:
            try:
                save_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                if save_buttons:
                    save_button = save_buttons[0]
                    print(f"임시저장 버튼을 찾았습니다: {selector}")
                    save_button.click()
                    print("임시저장 버튼을 클릭했습니다.")
                    time.sleep(3)  # 저장 처리 대기
                    save_found = True
                    break
            except:
                pass
        
        # JavaScript를 사용하여 저장 기능 시도
        if not save_found:
            try:
                result = driver.execute_script("""
                    if (window.PostEditor && window.PostEditor.save) {
                        window.PostEditor.save();
                        return true;
                    } else if (document.querySelector('#save-temp')) {
                        document.querySelector('#save-temp').click();
                        return true;
                    } else if (document.querySelector('.preview-btn')) {
                        document.querySelector('.preview-btn').click();
                        return true;
                    }
                    return false;
                """)
                
                if result:
                    print("JavaScript를 통해 임시저장 명령을 실행했습니다.")
                    time.sleep(3)
                    save_found = True
            except:
                pass
        
        # XPath를 사용하여 버튼 찾기
        if not save_found:
            try:
                save_xpath_expressions = [
                    "//button[contains(text(), '임시') or contains(text(), '저장') or contains(text(), '미리보기')]",
                    "//button[contains(@class, 'save') or contains(@id, 'save')]",
                    "//a[contains(text(), '임시저장') or contains(@class, 'save')]"
                ]
                
                for xpath_expr in save_xpath_expressions:
                    save_buttons_xpath = driver.find_elements(By.XPATH, xpath_expr)
                    if save_buttons_xpath:
                        save_button = save_buttons_xpath[0]
                        print(f"XPath를 통해 임시저장 버튼을 찾았습니다: {xpath_expr}")
                        save_button.click()
                        print("XPath를 통해 임시저장 버튼을 클릭했습니다.")
                        time.sleep(3)
                        save_found = True
                        break
            except Exception as xpath_e:
                print(f"XPath를 통한 임시저장 버튼 찾기 중 오류: {xpath_e}")
        
        # 버튼을 찾지 못한 경우 모든 버튼을 분석
        if not save_found:
            print("임시저장 버튼을 찾지 못했습니다. 모든 버튼을 분석합니다.")
            
            # 페이지의 모든 버튼 요소 출력
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"페이지에서 {len(all_buttons)}개의 버튼을 찾았습니다.")
            
            # 하단 영역의 버튼들 우선 분석
            try:
                bottom_buttons = driver.find_elements(By.CSS_SELECTOR, ".editor-footer button, .foot_post button, .write_foot button, #editor-root > div:last-child button")
                if bottom_buttons:
                    print(f"하단 영역에서 {len(bottom_buttons)}개의 버튼을 찾았습니다.")
                    for i, btn in enumerate(bottom_buttons):
                        try:
                            btn_text = btn.text.strip() or '(텍스트 없음)'
                            btn_class = btn.get_attribute('class') or '(클래스 없음)'
                            btn_id = btn.get_attribute('id') or '(ID 없음)'
                            print(f"하단 버튼 {i+1}: 텍스트='{btn_text}', 클래스='{btn_class}', ID='{btn_id}'")
                            
                            # 임시저장 관련 버튼 추정
                            if (btn_text == '미리보기' or btn_text == '저장' or 
                                '임시' in btn_text or '저장' in btn_text or 
                                'save' in btn_text.lower() or 'draft' in btn_text.lower()):
                                print(f"  => 임시저장 버튼으로 보입니다!")
                                
                                proceed = input("이 버튼을 임시저장 버튼으로 클릭하시겠습니까? (y/n): ")
                                if proceed.lower() == 'y':
                                    btn.click()
                                    print(f"'{btn_text}' 버튼을 클릭했습니다.")
                                    time.sleep(3)  # 저장 처리 대기
                                    save_found = True
                        except:
                            print(f"버튼 {i+1}: (정보 읽기 실패)")
                else:
                    print("하단 영역에서 버튼을 찾지 못했습니다.")
            except Exception as bottom_e:
                print(f"하단 버튼 분석 중 오류: {bottom_e}")
            
            # 모든 버튼 검사
            if not save_found:
                for i, btn in enumerate(all_buttons[:15]):
                    try:
                        btn_text = btn.text.strip() or '(텍스트 없음)'
                        btn_class = btn.get_attribute('class') or '(클래스 없음)'
                        btn_id = btn.get_attribute('id') or '(ID 없음)'
                        print(f"버튼 {i+1}: 텍스트='{btn_text}', 클래스='{btn_class}', ID='{btn_id}'")
                        
                        # 임시저장 관련 텍스트가 있는 버튼 발견
                        if ('임시' in btn_text or '저장' in btn_text or 
                            '미리보기' in btn_text or
                            'save' in btn_text.lower() or 'draft' in btn_text.lower()):
                            print(f"  => 임시저장 버튼으로 보입니다!")
                            
                            proceed = input("이 버튼을 임시저장 버튼으로 클릭하시겠습니까? (y/n): ")
                            if proceed.lower() == 'y':
                                btn.click()
                                print("선택한 버튼을 클릭했습니다.")
                                time.sleep(3)  # 저장 처리 대기
                                save_found = True
                    except:
                        continue
        
    except Exception as e:
        print(f"임시저장 버튼 클릭 중 오류: {e}")
    
    return save_found

def check_html_content_status(driver):
    """
    현재 HTML 에디터의 콘텐츠 설정 상태를 체크하는 함수
    """
    try:
        print("\n=== HTML 콘텐츠 설정 상태 체크 ===")
        
        status_result = driver.execute_script("""
            var status = {
                pageLevel: {
                    textareas: 0,
                    contentTextareas: 0,
                    contentLength: 0,
                    hasContent: false
                },
                iframeLevel: {
                    iframes: 0,
                    textareas: 0,
                    contentTextareas: 0,
                    contentLength: 0,
                    hasContent: false,
                    contentEditables: 0,
                    contentEditableLength: 0
                },
                editorElements: {
                    codeMirror: 0,
                    contentEditable: 0,
                    tistoryEditor: false
                }
            };
            
            // 1. 페이지 레벨 textarea 체크
            var pageTextareas = document.querySelectorAll('textarea');
            status.pageLevel.textareas = pageTextareas.length;
            
            for (var i = 0; i < pageTextareas.length; i++) {
                var ta = pageTextareas[i];
                if (ta.id !== 'post-title-inp' && ta.id !== 'tag' && 
                    !ta.className.includes('textarea_tit')) {
                    status.pageLevel.contentTextareas++;
                    if (ta.value && ta.value.length > 100) {
                        status.pageLevel.contentLength = ta.value.length;
                        status.pageLevel.hasContent = true;
                    }
                }
            }
            
            // 2. iframe 레벨 체크
            var iframes = document.querySelectorAll('iframe');
            status.iframeLevel.iframes = iframes.length;
            
            for (var i = 0; i < iframes.length; i++) {
                try {
                    var frameDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                    
                    // iframe 내 textarea 체크
                    var frameTextareas = frameDoc.querySelectorAll('textarea');
                    status.iframeLevel.textareas += frameTextareas.length;
                    
                    for (var j = 0; j < frameTextareas.length; j++) {
                        var ta = frameTextareas[j];
                        if (ta.id !== 'post-title-inp' && ta.id !== 'tag' && 
                            !ta.className.includes('textarea_tit')) {
                            status.iframeLevel.contentTextareas++;
                            if (ta.value && ta.value.length > 100) {
                                status.iframeLevel.contentLength = ta.value.length;
                                status.iframeLevel.hasContent = true;
                            }
                        }
                    }
                    
                    // iframe 내 contenteditable 체크
                    var frameEditables = frameDoc.querySelectorAll('[contenteditable="true"]');
                    status.iframeLevel.contentEditables += frameEditables.length;
                    
                    for (var k = 0; k < frameEditables.length; k++) {
                        var editable = frameEditables[k];
                        var rect = editable.getBoundingClientRect();
                        if (rect.width > 50 && rect.height > 50 && 
                            editable.innerHTML && editable.innerHTML.length > 100) {
                            status.iframeLevel.contentEditableLength = editable.innerHTML.length;
                            status.iframeLevel.hasContent = true;
                        }
                    }
                    
                } catch (e) {
                    console.log("iframe 접근 오류:", e.message);
                }
            }
            
            // 3. 에디터 요소 체크
            status.editorElements.codeMirror = document.querySelectorAll('.CodeMirror').length;
            status.editorElements.contentEditable = document.querySelectorAll('[contenteditable="true"]').length;
            status.editorElements.tistoryEditor = typeof window.tistoryEditor !== 'undefined';
            
            return status;
        """)
        
        print("📊 콘텐츠 설정 상태:")
        print(f"페이지 레벨:")
        print(f"  - 전체 textarea: {status_result['pageLevel']['textareas']}개")
        print(f"  - 콘텐츠용 textarea: {status_result['pageLevel']['contentTextareas']}개")
        print(f"  - 콘텐츠 있음: {status_result['pageLevel']['hasContent']}")
        print(f"  - 콘텐츠 길이: {status_result['pageLevel']['contentLength']}글자")
        
        print(f"\niframe 레벨:")
        print(f"  - iframe 개수: {status_result['iframeLevel']['iframes']}개")
        print(f"  - iframe 내 textarea: {status_result['iframeLevel']['textareas']}개")
        print(f"  - iframe 내 콘텐츠용 textarea: {status_result['iframeLevel']['contentTextareas']}개")
        print(f"  - iframe 내 contenteditable: {status_result['iframeLevel']['contentEditables']}개")
        print(f"  - iframe 내 콘텐츠 있음: {status_result['iframeLevel']['hasContent']}")
        print(f"  - iframe 내 콘텐츠 길이: {status_result['iframeLevel']['contentLength'] + status_result['iframeLevel']['contentEditableLength']}글자")
        
        print(f"\n에디터 요소:")
        print(f"  - CodeMirror: {status_result['editorElements']['codeMirror']}개")
        print(f"  - ContentEditable: {status_result['editorElements']['contentEditable']}개")
        print(f"  - 티스토리 에디터 API: {status_result['editorElements']['tistoryEditor']}")
        
        # 전체 상태 판정
        overall_success = (status_result['pageLevel']['hasContent'] or 
                          status_result['iframeLevel']['hasContent'])
        
        if overall_success:
            print("\n✅ 전체 상태: HTML 콘텐츠가 성공적으로 설정되어 있습니다!")
        else:
            print("\n❌ 전체 상태: HTML 콘텐츠가 설정되지 않았습니다.")
        
        return overall_success, status_result
        
    except Exception as e:
        print(f"상태 체크 중 오류: {e}")
        return False, None

# 메인 함수
if __name__ == "__main__":
    print("ChatGPT를 이용한 티스토리 자동 포스팅 시작")
    login_and_post_to_tistory() 