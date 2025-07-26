import os
import time
import json
import pickle
import random
import openai
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# Unsplash API 키 설정
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

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
        # 티스토리 대시보드 접근 시도
        driver.get(BLOG_MANAGE_URL)
        time.sleep(5)  # 페이지 로딩 대기 시간 증가
        
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
        driver.get("https://www.tistory.com")
        time.sleep(3)  # 페이지 로딩 대기
        
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
        driver.refresh()
        time.sleep(3)
        
        # 로그인 상태 확인 - 여러 방법 시도
        login_verification_methods = [
            ("방법 1", "로그인 상태 확인 함수", lambda: is_logged_in(driver)),
            ("방법 2", "URL 리디렉션 확인", lambda: "login" not in driver.current_url.lower() and "auth" not in driver.current_url.lower()),
            ("방법 3", "로그인 버튼 확인", lambda: len(driver.find_elements(By.CSS_SELECTOR, "a[href*='login'], .btn-login, .login-button")) == 0),
        ]
        
        for method_id, method_name, method_func in login_verification_methods:
            try:
                print(f"{method_id}: {method_name}으로 로그인 상태 확인 중...")
                if method_func():
                    print(f"자동 로그인 성공! ({method_name})")
                    return True
                else:
                    print(f"{method_name}으로 확인 시 로그인되지 않은 상태입니다.")
            except Exception as e:
                print(f"{method_name} 확인 중 오류 발생: {e}")
        
        # 대시보드 직접 접근 시도
        print("\n티스토리 대시보드에 직접 접근 시도...")
        try:
            driver.get(BLOG_MANAGE_URL)
            time.sleep(5)
            
            # 대시보드 접근 성공 여부 확인
            if "login" in driver.current_url.lower() or "auth" in driver.current_url.lower():
                print("대시보드 접근 시 로그인 페이지로 리디렉션되었습니다.")
            else:
                print("대시보드 접근 성공! 자동 로그인 성공으로 간주합니다.")
                return True
                
            # 추가 확인: 로그인 창이 표시되는지
            login_form = driver.find_elements(By.CSS_SELECTOR, 
                "form[action*='login'], .login-form, #login-form")
            if login_form:
                print("로그인 폼이 표시됩니다. 자동 로그인 실패로 간주합니다.")
                return False
        except Exception as dash_e:
            print(f"대시보드 접근 시도 중 오류: {dash_e}")
        
        # 마지막 확인: 사용자에게 물어보기
        print("\n자동 로그인 상태를 명확하게 확인할 수 없습니다.")
        print(f"현재 URL: {driver.current_url}")
        print(f"페이지 제목: {driver.title}")
        
        user_confirm = input("화면을 확인했을 때 현재 로그인이 되어 있나요? (y/n): ")
        if user_confirm.lower() == 'y':
            print("사용자 확인으로 로그인 성공으로 처리합니다.")
            return True
        else:
            print("사용자 확인으로 로그인 실패로 처리합니다.")
            return False
        
    except Exception as e:
        print(f"자동 로그인 시도 중 오류 발생: {e}")
        return False

# 수동 로그인 함수
def manual_login(driver):
    """사용자에게 수동 로그인을 요청하고 완료 후 세션 정보 저장"""
    try:
        print("\n===== 수동 로그인 시작 =====")
        
        # 기존 세션 정보 삭제
        driver.delete_all_cookies()
        
        # 로그인 페이지 접속
        print("로그인 페이지로 이동합니다...")
        driver.get("https://www.tistory.com/auth/login")
        time.sleep(3)
        
        # 사용자에게 로그인 요청
        print("브라우저에서 로그인을 수동으로 완료해주세요.")
        print("  * 아이디와 비밀번호를 입력하여 로그인합니다.")
        print("  * 로그인 완료 후 대시보드나 메인 페이지가 표시되면 성공입니다.")
        input("\n로그인을 완료하셨으면 Enter 키를 눌러주세요...")
        
        # 티스토리 메인 페이지로 이동
        print("\n티스토리 메인 페이지로 이동합니다...")
        driver.get("https://www.tistory.com")
        time.sleep(3)
        
        # 로그인 상태 확인 (최대 3회 시도)
        login_success = False
        for attempt in range(3):
            try:
                print(f"\n로그인 상태 확인 시도 {attempt+1}/3...")
                if is_logged_in(driver):
                    print("로그인 성공 확인! 세션 정보를 저장합니다.")
                    login_success = True
                    break
                else:
                    print(f"로그인 상태 확인 실패 ({attempt+1}/3)")
                    
                    if attempt < 2:  # 마지막 시도가 아니면 재확인
                        print("3초 후 다시 확인합니다...")
                        time.sleep(3)
                        driver.refresh()  # 페이지 새로고침
                        time.sleep(3)
            except Exception as check_e:
                print(f"로그인 상태 확인 중 오류: {check_e}")
                if attempt < 2:
                    print("3초 후 다시 시도합니다...")
                    time.sleep(3)
        
        # 로그인 상태와 관계없이 사용자 확인으로 진행
        if not login_success:
            print("\n자동 확인으로는 로그인 상태를 확인할 수 없습니다.")
            user_confirm = input("로그인이 완료되었나요? (y/n): ")
            if user_confirm.lower() != 'y':
                print("로그인이 완료되지 않았습니다. 다시 시도해주세요.")
                return False
            print("사용자 확인으로 로그인 성공으로 간주합니다.")
        
        # 세션 정보 저장 시도
        print("\n세션 정보 저장을 시도합니다...")
        try:
            # 1차 시도: 메인 페이지에서 세션 정보 저장
            save_result1 = save_cookies(driver)
            save_result2 = save_local_storage(driver)
            
            # 2차 시도: 대시보드 페이지에서 세션 정보 저장
            print("대시보드 페이지에서 추가 세션 정보 저장 시도...")
            driver.get(BLOG_MANAGE_URL)
            time.sleep(3)
            
            save_result3 = save_cookies(driver)
            save_result4 = save_local_storage(driver)
            
            if save_result1 or save_result2 or save_result3 or save_result4:
                print("세션 정보가 성공적으로 저장되었습니다.")
            else:
                print("세션 정보 저장에 실패했지만, 로그인은 유지됩니다.")
        except Exception as save_e:
            print(f"세션 정보 저장 중 오류: {save_e}")
            print("세션 정보 저장에 실패했지만, 로그인은 유지됩니다.")
        
        # 수동 로그인 성공으로 처리
        return True
            
    except Exception as e:
        print(f"수동 로그인 처리 중 오류 발생: {e}")
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

def get_keyword_image_url(keyword, count=3):
    """
    Unsplash API를 사용하여 키워드 관련 이미지 URL을 가져옴
    """
    try:
        print(f"'{keyword}' 키워드로 이미지를 검색합니다...")
        
        headers = {
            'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
        }
        
        params = {
            'query': keyword,
            'per_page': count,
            'orientation': 'landscape'
        }
        
        response = requests.get('https://api.unsplash.com/search/photos', headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            images = []
            
            for photo in data['results']:
                image_info = {
                    'url': photo['urls']['regular'],
                    'alt': photo['alt_description'] or keyword,
                    'photographer': photo['user']['name'],
                    'photographer_url': photo['user']['links']['html']
                }
                images.append(image_info)
            
            print(f"{len(images)}개의 이미지를 찾았습니다.")
            return images
        else:
            print(f"이미지 검색 실패: {response.status_code}")
            return []
    
    except Exception as e:
        print(f"이미지 검색 중 오류 발생: {e}")
        return []

def generate_table_by_keyword(keyword):
    """
    OpenAI를 사용하여 키워드에 맞는 표를 생성
    """
    try:
        print(f"'{keyword}' 주제로 표를 생성합니다...")
        
        table_prompt = f"""
        '{keyword}' 주제와 관련된 유용한 정보를 담은 HTML 표를 생성해주세요.
        
        요구사항:
        1. HTML table 태그를 사용하여 작성
        2. 표는 최소 3행 4열 이상
        3. 헤더(thead)와 본문(tbody) 구분
        4. 실제 유용한 데이터 포함
        5. 표에는 border, padding 등 기본 스타일 적용
        6. 한국어로 작성
        
        예시 형식:
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <thead>
        <tr style="background-color: #f2f2f2;">
        <th style="padding: 10px;">컬럼1</th>
        <th style="padding: 10px;">컬럼2</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td style="padding: 10px;">데이터1</td>
        <td style="padding: 10px;">데이터2</td>
        </tr>
        </tbody>
        </table>
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 전문적인 HTML 표 생성기입니다. 주제에 맞는 유용하고 정확한 데이터를 담은 표를 생성합니다."},
                {"role": "user", "content": table_prompt}
            ],
            max_tokens=1500
        )
        
        table_html = response.choices[0].message.content.strip()
        print("표 생성이 완료되었습니다.")
        return table_html
        
    except Exception as e:
        print(f"표 생성 중 오류 발생: {e}")
        return ""

def generate_faq_by_keyword(keyword):
    """
    OpenAI를 사용하여 키워드에 맞는 FAQ를 생성
    """
    try:
        print(f"'{keyword}' 주제로 FAQ를 생성합니다...")
        
        faq_prompt = f"""
        '{keyword}' 주제와 관련된 자주 묻는 질문과 답변(FAQ)을 HTML 형식으로 생성해주세요.
        
        요구사항:
        1. 최소 5개 이상의 질문과 답변
        2. HTML 형식으로 작성 (div, h3, p 태그 등 사용)
        3. 질문은 h3 태그, 답변은 p 태그 사용
        4. 각 FAQ 항목은 div로 감싸기
        5. 실제 유용하고 정확한 정보 포함
        6. 한국어로 작성
        
        예시 형식:
        <div class="faq-section">
        <h2>자주 묻는 질문</h2>
        <div class="faq-item">
        <h3>Q: 질문 내용?</h3>
        <p>A: 답변 내용입니다.</p>
        </div>
        </div>
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 전문적인 FAQ 생성기입니다. 주제에 맞는 유용하고 정확한 질문과 답변을 생성합니다."},
                {"role": "user", "content": faq_prompt}
            ],
            max_tokens=2000
        )
        
        faq_html = response.choices[0].message.content.strip()
        print("FAQ 생성이 완료되었습니다.")
        return faq_html
        
    except Exception as e:
        print(f"FAQ 생성 중 오류 발생: {e}")
        return ""

def generate_blog_content(topic):
    """
    ChatGPT API를 사용하여 블로그 콘텐츠 생성 (HTML 형식으로만)
    """
    print(f"'{topic}' 주제로 블로그 콘텐츠 생성 중...")
    
    # 제목 생성
    title_prompt = f"다음 주제에 관한 블로그 포스트의 매력적인 제목을 생성해주세요: '{topic}'. 제목만 작성하고 따옴표나 기호는 포함하지 마세요."
    title_response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 전문적인 블로그 제목 생성기입니다. 매력적이고 SEO에 최적화된 제목을 생성합니다."},
            {"role": "user", "content": title_prompt}
        ],
        max_tokens=50
    )
    title = title_response.choices[0].message.content.strip()
    
    # 키워드 관련 이미지 가져오기
    images = get_keyword_image_url(topic)
    
    # 표 생성
    table_html = generate_table_by_keyword(topic)
    
    # FAQ 생성
    faq_html = generate_faq_by_keyword(topic)
    
    # 본문 생성
    content_prompt = f"""
    다음 주제에 관한 포괄적인 블로그 포스트를 HTML 형식으로 작성해주세요: '{topic}'
    
    블로그 제목은 '{title}'입니다.
    
    다음 가이드라인을 따라주세요:
    1. 한국어로 작성하세요.
    2. 최소 1500단어 분량으로 작성하세요.
    3. 완전한 HTML 형식으로 작성하세요 (h2, h3, p, ul, ol, strong, em 등 태그 사용).
    4. 서론, 본론, 결론 구조를 사용하세요.
    5. 소제목을 포함하여 구조화된 형식으로 작성하세요.
    6. 실제 사례나 통계 데이터를 포함하세요.
    7. 독자의 참여를 유도하는 질문을 포함하세요.
    8. 모든 내용은 유효한 HTML 태그로 감싸주세요.
    9. 이미지가 들어갈 자리에는 [IMAGE_PLACEHOLDER]를 넣어주세요.
    10. 표가 들어갈 자리에는 [TABLE_PLACEHOLDER]를 넣어주세요.
    11. FAQ가 들어갈 자리에는 [FAQ_PLACEHOLDER]를 넣어주세요.
    """
    
    content_response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 전문적인 블로그 작가입니다. 독자가 이해하기 쉽고 정보가 풍부한 HTML 콘텐츠를 작성합니다."},
            {"role": "user", "content": content_prompt}
        ],
        max_tokens=4000
    )
    content = content_response.choices[0].message.content.strip()
    
    # 이미지 HTML 생성
    image_html = ""
    if images:
        for i, img in enumerate(images[:2]):  # 최대 2개 이미지 사용
            image_html += f"""
            <div style="text-align: center; margin: 20px 0;">
                <img src="{img['url']}" alt="{img['alt']}" style="max-width: 100%; height: auto; border-radius: 8px;">
                <p style="font-size: 12px; color: #666; margin-top: 5px;">
                    Photo by <a href="{img['photographer_url']}" target="_blank">{img['photographer']}</a> on Unsplash
                </p>
            </div>
            """
    
    # 플레이스홀더 교체
    if "[IMAGE_PLACEHOLDER]" in content and image_html:
        content = content.replace("[IMAGE_PLACEHOLDER]", image_html, 1)
    
    if "[TABLE_PLACEHOLDER]" in content and table_html:
        content = content.replace("[TABLE_PLACEHOLDER]", f"<div style='margin: 20px 0;'>{table_html}</div>")
    
    if "[FAQ_PLACEHOLDER]" in content and faq_html:
        content = content.replace("[FAQ_PLACEHOLDER]", f"<div style='margin: 20px 0;'>{faq_html}</div>")
    
    # 태그 생성
    tags_prompt = f"다음 블로그 포스트 주제에 관련된 5개의 SEO 최적화 태그를 생성해주세요 (쉼표로 구분): '{topic}'"
    tags_response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 SEO 전문가입니다. 검색 엔진에서 높은 순위를 차지할 수 있는 태그를 제안합니다."},
            {"role": "user", "content": tags_prompt}
        ],
        max_tokens=100
    )
    tags = tags_response.choices[0].message.content.strip()
    
    print(f"제목: {title}")
    print(f"태그: {tags}")
    print("콘텐츠 생성 완료!")
    
    return {
        "title": title,
        "content": content,
        "tags": tags,
        "format_type": 1  # HTML 모드로 고정
    }

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
                print("자동 로그인 실패, 수동 로그인으로 전환합니다.")
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
            retry = input("로그인을 실패했습니다. 그래도 계속 진행하시겠습니까? (y/n): ")
            if retry.lower() != 'y':
                print("프로그램을 종료합니다.")
                return
            else:
                print("사용자 확인으로 계속 진행합니다.")
        
        # 티스토리 메인 페이지 접근 - 로그인 성공 유무와 관계없이 계속 진행
        print("\n=== 티스토리 글 작성 단계 ===")
        print("티스토리 메인 페이지로 이동합니다...")
        driver.get(BLOG_MANAGE_URL)
        time.sleep(3)
        
        # 무한 루프로 글 작성 진행 (사용자가 종료하기 전까지)
        while True:
            # 사용자에게 주제 선택 요청
            selected_topic = get_user_topic()
            
            # 콘텐츠 생성 (재시도 로직 사용)
            try:
                blog_post = generate_blog_content_with_retry(selected_topic)
            except Exception as e:
                print(f"콘텐츠 생성 중 오류 발생: {e}")
                retry = input("다시 시도하시겠습니까? (y/n): ")
                if retry.lower() == 'y':
                    continue
                else:
                    break
            
            # 새 글 작성 페이지로 이동
            print("새 글 작성 페이지로 이동합니다...")
            driver.get(BLOG_NEW_POST_URL)
            time.sleep(5)  # 페이지 로딩 대기
            
            # 알림창(Alert) 자동 처리
            try:
                # 알림창이 있는지 확인하고 있으면 수락
                alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
                if alert:
                    alert_text = alert.text
                    print(f"알림창 감지: {alert_text}")
                    alert.accept()  # '확인' 버튼 클릭
                    print("알림창을 자동으로 처리했습니다.")
                    time.sleep(1)
            except:
                # 알림창이 없으면 계속 진행
                pass
            
            # 글 작성 함수 호출 (HTML 모드로 고정)
            write_post(driver, blog_post)
            
            # 임시저장 후 발행 여부 확인
            print("\n글이 임시저장되었습니다. 발행하시겠습니까?")
            proceed = input("발행하기 (Y/N): ")
            
            # 대소문자 구분 없이 'Y'인 경우 발행 진행
            if proceed.upper() == 'Y':
                print("발행을 진행합니다...")
                publish_success = publish_post(driver)
                
                if publish_success:
                    print("발행이 완료되었습니다!")
                else:
                    print("발행이 완료되지 않았습니다. 글은 임시저장 상태로 남아있습니다.")
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
            
            # 새 글 작성을 위해 페이지 새로고침
            print("새 글 작성을 위해 페이지를 준비합니다...")
            driver.get(BLOG_NEW_POST_URL)
            
            # 알림창 처리
            try:
                alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
                if alert:
                    alert.accept()
                    print("알림창을 자동으로 처리했습니다.")
            except:
                pass
            
    except Exception as e:
        print(f"전체 과정에서 오류 발생: {e}")
    
    finally:
        # 루프가 종료되었을 때만 브라우저 종료
        driver.quit()

# 콘텐츠 생성 함수에 재시도 로직 추가
def generate_blog_content_with_retry(topic, max_retries=3, retry_delay=5):
    """재시도 로직이 포함된 블로그 콘텐츠 생성 함수"""
    for attempt in range(max_retries):
        try:
            return generate_blog_content(topic)
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
def write_post(driver, blog_post):
    """
    티스토리에 글 작성 프로세스를 처리하는 함수 (HTML 모드 전용)
    """
    try:
        # 제목 입력
        print("제목을 입력합니다...")
        title_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "post-title-inp"))
        )
        title_input.clear()
        title_input.send_keys(blog_post["title"])
        time.sleep(1)
    except Exception as e:
        print(f"제목 입력 중 오류: {e}")
        
        # 대체 제목 입력 필드 찾기
        try:
            title_inputs = driver.find_elements(By.CSS_SELECTOR, 
                "input[placeholder*='제목'], input.title, .title-input, .post-title input")
            if title_inputs:
                title_inputs[0].clear()
                title_inputs[0].send_keys(blog_post["title"])
                print("대체 제목 필드에 입력했습니다.")
        except Exception as e2:
            print(f"대체 제목 입력 중 오류: {e2}")
    
    # HTML 모드로 전환
    print("HTML 모드로 전환합니다...")
    switch_to_html_mode_specific(driver)
    
    # 본문 입력 - HTML 모드 전용
    try:
        print("본문을 입력합니다...")
        content = blog_post["content"]
        set_html_content_specific(driver, content)
    
    except Exception as e:
        print(f"본문 입력 중 오류: {e}")
    
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

def switch_to_html_mode_specific(driver):
    """특정 element를 사용하여 HTML 모드로 전환"""
    try:
        print("HTML 모드로 전환을 시도합니다...")
        
        # 지정된 HTML 모드 버튼 찾기
        html_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#editor-mode-html-text"))
        )
        
        html_button.click()
        print("HTML 모드로 전환했습니다.")
        time.sleep(2)  # 모드 전환 대기
        return True
        
    except Exception as e:
        print(f"지정된 HTML 모드 버튼을 찾지 못했습니다: {e}")
        
        # 대체 방법으로 HTML 모드 전환 시도
        try:
            html_buttons = driver.find_elements(By.CSS_SELECTOR, 
                "span.mce-text:contains('HTML'), .btn_html, button[data-mode='html']")
            
            for button in html_buttons:
                if "HTML" in button.text:
                    button.click()
                    print("대체 HTML 모드 버튼으로 전환했습니다.")
                    time.sleep(2)
                    return True
        except Exception as e2:
            print(f"대체 HTML 모드 전환 실패: {e2}")
        
        return False

def set_html_content_specific(driver, content):
    """특정 element를 사용하여 HTML 콘텐츠 설정"""
    try:
        # CodeMirror 에디터 영역 찾기
        print("CodeMirror 에디터 영역을 찾습니다...")
        
        # CodeMirror 에디터의 텍스트 입력 영역 찾기
        code_mirror_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".CodeMirror"))
        )
        
        # CodeMirror에 직접 내용 입력
        driver.execute_script("""
            var cm = document.querySelector('.CodeMirror').CodeMirror;
            if (cm) {
                cm.setValue(arguments[0]);
                console.log('CodeMirror에 내용을 설정했습니다.');
            }
        """, content)
        
        print("CodeMirror 에디터에 HTML 콘텐츠를 설정했습니다.")
        return True
        
    except Exception as e:
        print(f"CodeMirror 에디터 사용 실패: {e}")
        
        # 대체 방법으로 직접 클릭하여 입력
        try:
            print("대체 방법으로 HTML 콘텐츠 입력을 시도합니다...")
            
            # cm-text 요소 찾기 및 클릭
            cm_text_elements = driver.find_elements(By.CSS_SELECTOR, "span[cm-text]")
            if cm_text_elements:
                # 첫 번째 요소 클릭하여 포커스 설정
                cm_text_elements[0].click()
                time.sleep(1)
                
                # 전체 내용 삭제 후 새 내용 입력
                driver.execute_script("document.execCommand('selectAll', false, null);")
                time.sleep(0.5)
                
                # 내용을 작은 청크로 나누어 입력
                chunk_size = 500
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    driver.execute_script("document.execCommand('insertText', false, arguments[0]);", chunk)
                    time.sleep(0.2)
                
                print("대체 방법으로 HTML 콘텐츠를 입력했습니다.")
                return True
            
        except Exception as e2:
            print(f"대체 HTML 콘텐츠 입력 실패: {e2}")
        
        # 마지막 대체 방법
        try:
            print("마지막 대체 방법으로 JavaScript를 통한 직접 입력을 시도합니다...")
            
            result = driver.execute_script("""
                // HTML 에디터 textarea 찾기
                var textareas = document.querySelectorAll('textarea');
                for (var i = 0; i < textareas.length; i++) {
                    var textarea = textareas[i];
                    if (textarea.style.display !== 'none' && textarea.offsetParent !== null) {
                        textarea.value = arguments[0];
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        return true;
                    }
                }
                
                // contenteditable 요소 찾기
                var editables = document.querySelectorAll('[contenteditable="true"]');
                for (var i = 0; i < editables.length; i++) {
                    var editable = editables[i];
                    if (editable.style.display !== 'none' && editable.offsetParent !== null) {
                        editable.innerHTML = arguments[0];
                        editable.dispatchEvent(new Event('input', { bubbles: true }));
                        return true;
                    }
                }
                
                return false;
            """, content)
            
            if result:
                print("JavaScript를 통해 HTML 콘텐츠를 설정했습니다.")
                return True
                
        except Exception as e3:
            print(f"JavaScript를 통한 HTML 콘텐츠 설정 실패: {e3}")
        
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
        
        # 1. TinyMCE 에디터에서 HTML 버튼 찾기
        html_buttons = driver.find_elements(By.CSS_SELECTOR, 
            ".btn_html, button[data-mode='html'], .html-mode-button, .switch-html, .mce-i-code")
        
        if html_buttons:
            html_buttons[0].click()
            print("HTML 모드로 전환했습니다.")
            time.sleep(1)
            return True
            
        # 2. 직접 JavaScript 실행하여 전환 시도
        result = driver.execute_script("""
            // TinyMCE 에디터에서 HTML 모드 전환
            if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                tinyMCE.activeEditor.execCommand('mceCodeEditor');
                return true;
            }
            
            // 티스토리 에디터 API 사용
            if (window.tistoryEditor && window.tistoryEditor.switchHtml) {
                window.tistoryEditor.switchHtml();
                return true;
            }
            
            // HTML 버튼 찾아서 클릭
            var htmlBtns = document.querySelectorAll('.btn_html, button[data-mode="html"], .html-mode-button, .switch-html');
            if (htmlBtns.length > 0) {
                htmlBtns[0].click();
                return true;
            }
            
            return false;
        """)
        
        if result:
            print("JavaScript를 통해 HTML 모드로 전환했습니다.")
            time.sleep(1)
            return True
            
        # 3. XPath를 사용하여 HTML 버튼 찾기 시도
        html_button_xpath = driver.find_elements(By.XPATH, 
            "//button[contains(@class, 'html') or contains(@title, 'HTML') or contains(@aria-label, 'HTML') or contains(text(), 'HTML')]")
        if html_button_xpath:
            html_button_xpath[0].click()
            print("XPath를 통해 HTML 모드 버튼을 찾아 클릭했습니다.")
            time.sleep(1)
            return True
            
        print("HTML 모드로 전환을 시도했으나 실패했습니다.")
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
    """HTML 모드에서 콘텐츠 설정"""
    try:
        # 1. JavaScript를 사용하여 직접 콘텐츠 설정 시도
        result = driver.execute_script("""
            // 티스토리 에디터 API 사용
            if (window.tistoryEditor && window.tistoryEditor.setHtmlContent) {
                window.tistoryEditor.setHtmlContent(arguments[0]);
                return true;
            }
            
            // TinyMCE API 사용
            if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                tinyMCE.activeEditor.setContent(arguments[0]);
                return true;
            }
            
            // HTML 에디터 요소 찾기
            var htmlEditor = document.querySelector('.html-editor textarea, [contenteditable="true"].html, textarea.html-code');
            if (htmlEditor) {
                htmlEditor.value = arguments[0];
                htmlEditor.innerHTML = arguments[0];
                return true;
            }
            
            return false;
        """, content)
        
        if result:
            print("JavaScript를 통해 HTML 콘텐츠를 설정했습니다.")
            return True
        
        # 2. iframe 내부에 직접 콘텐츠 설정 시도
        if iframe_editor:
            driver.switch_to.frame(iframe_editor)
            
            try:
                # HTML 모드에서는 textarea나 contenteditable 요소에 내용 설정
                editor_element = driver.find_element(By.CSS_SELECTOR, "textarea, [contenteditable='true']")
                editor_element.clear()
                editor_element.send_keys(content)
                print("iframe 내부의 에디터에 HTML 콘텐츠를 입력했습니다.")
                driver.switch_to.default_content()
                return True
            except:
                driver.switch_to.default_content()
        
        # 3. 직접 HTML 입력 필드 찾기
        html_editors = driver.find_elements(By.CSS_SELECTOR, 
            "textarea.html-editor, textarea.code-editor, [contenteditable='true'].html-code")
        
        if html_editors:
            html_editors[0].clear()
            html_editors[0].send_keys(content)
            print("HTML 에디터 요소에 콘텐츠를 입력했습니다.")
            return True
            
        print("HTML 콘텐츠 설정을 시도했으나 실패했습니다.")
        return False
    except Exception as e:
        print(f"HTML 콘텐츠 설정 중 오류: {e}")
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

# 메인 함수
if __name__ == "__main__":
    print("ChatGPT를 이용한 티스토리 자동 포스팅 시작")
    login_and_post_to_tistory() 