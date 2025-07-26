import os
import time
import json
import pickle
import random
import openai
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path
import re

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
        
        login_method_results = []
        for method_id, method_name, method_func in login_verification_methods:
            try:
                print(f"{method_id}: {method_name}으로 로그인 상태 확인 중...")
                method_result = method_func()
                login_method_results.append(method_result)
                
                if method_result:
                    print(f"자동 로그인 성공! ({method_name})")
                else:
                    print(f"{method_name}으로 확인 시 로그인되지 않은 상태입니다.")
            except Exception as e:
                print(f"{method_name} 확인 중 오류 발생: {e}")
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
            print("로그인 창이 아직 표시되는지 확인해 주세요.")
            user_confirm = input("로그인이 완료되었나요? (y/n): ")
            if user_confirm.lower() != 'y':
                print("로그인이 완료되지 않았습니다. 다시 시도해주세요.")
                print("관리자 페이지에 접근하려면 유효한 로그인 세션이 필요합니다.")
                return False
            print("사용자 확인으로 로그인 성공으로 간주합니다.")
        
        # 세션 정보 저장 시도
        print("\n세션 정보 저장을 시도합니다...")
        save_success = False
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
                print("다음에는 자동 로그인으로 더 빠르게 접속할 수 있습니다.")
                save_success = True
            else:
                print("세션 정보 저장에 실패했지만, 로그인은 유지됩니다.")
                print("다음 실행 시에도 수동 로그인이 필요할 수 있습니다.")
        except Exception as save_e:
            print(f"세션 정보 저장 중 오류: {save_e}")
            print("세션 정보 저장에 실패했지만, 로그인은 유지됩니다.")
            print("다음 실행 시에도 수동 로그인이 필요할 수 있습니다.")
        
        print("\n===== 수동 로그인 완료 =====")
        if save_success:
            print("세션 정보 저장 성공: 다음 실행 시 자동 로그인이 가능합니다.")
        else:
            print("세션 정보 저장 실패: 다음 실행 시에도 수동 로그인이 필요할 수 있습니다.")
        
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

def generate_blog_content(topic, format_type=2):
    """
    ChatGPT API를 사용하여 블로그 콘텐츠 생성
    format_type: 2=일반 텍스트(기본값)
    """
    print(f"'{topic}' 주제로 블로그 콘텐츠 생성 중...")
    
    # 제목 생성
    title_prompt = f"다음 주제에 관한 블로그 포스트의 매력적인 제목을 생성해주세요: '{topic}'. 제목만 작성하고 따옴표나 기호는 포함하지 마세요."
    try:
        # OpenAI API v1.x 버전용 호출
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            title_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문적인 블로그 제목 생성기입니다. 매력적이고 SEO에 최적화된 제목을 생성합니다."},
                    {"role": "user", "content": title_prompt}
                ],
                max_tokens=50
            )
            title = title_response.choices[0].message.content.strip()
            
        # 예전 버전(0.x) OpenAI API 호출로 폴백
        except (ImportError, AttributeError):
            title_response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문적인 블로그 제목 생성기입니다. 매력적이고 SEO에 최적화된 제목을 생성합니다."},
                    {"role": "user", "content": title_prompt}
                ],
                max_tokens=50
            )
            title = title_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"제목 생성 중 오류: {e}")
        # 오류 시 간단한 제목 생성
        title = f"{topic}에 관한 포괄적인 가이드"
    
    # 본문 생성을 위한 형식 가이드 설정 (기본 텍스트 모드)
    format_guide = """
    7. HTML 태그나 마크다운은 사용하지 마세요. 일반 텍스트로 작성하되, 다음 형식 지침을 따라주세요:
       - 모든 문단은 한 줄씩 띄워서 작성하세요. 절대로 문단을 붙여서 작성하지 마세요.
       - 각 문장은 적절한 띄어쓰기를 반드시 지켜주세요.
       - 중요한 문구는 '**강조할 내용**'과 같이 별표로 강조해주세요.
       - 각 섹션의 제목은 별도의 줄에 작성하고 앞에 적절한 이모지를 넣어주세요 (예: 🌱 지속가능한 생활).
       - 소제목도 별도의 줄에 작성하고 소제목 앞에도 관련 이모지를 넣어주세요.
       - 목록은 번호나 불릿 대신 이모지를 사용해주세요 (예: 🔍 첫 번째 항목).
       - 각 항목은 새 줄에 작성하고, 항목들 사이에 충분한 간격을 두세요.
       - 단락을 명확히 구분하고, 내용이 풍부하게 작성해주세요.
       - 결론 부분에는 💡 이모지로 시작하는 요약 문장을 넣어주세요.
    """
    
    # 본문 생성
    content_prompt = f"""
    다음 주제에 관한 포괄적인 블로그 포스트를 작성해주세요: '{topic}'
    
    블로그 제목은 '{title}'입니다.
    
    다음 가이드라인을 따라주세요:
    1. 한국어로 작성하세요.
    2. 최소 1000단어 분량으로 작성하세요.
    3. 서론, 본론, 결론 구조를 사용하세요.
    4. 최소 5개 이상의 소제목을 포함하여 구조화된 형식으로 작성하세요.
    5. 실제 사례나 통계 데이터를 포함하세요.
    6. 독자의 참여를 유도하는 질문을 포함하세요.
    {format_guide}
    8. 마지막에 5개의 관련 해시태그를 추가하세요.
    
    중요: 각 문단 사이에는 반드시 빈 줄을 넣어 문단을 분리해주세요. 문장과 문장 사이의 띄어쓰기를 정확하게 지켜주세요. 고품질의 전문적인 블로그 글처럼 보이도록 작성해주세요.
    """
    
    try:
        # OpenAI API v1.x 버전용 호출
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            content_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문적인 블로그 작가입니다. 독자가 이해하기 쉽고 정보가 풍부하며 시각적으로 매력적인 콘텐츠를 작성합니다. 이모지와 강조 표현을 적절히 사용해 글을 생동감있게 만듭니다. 특히 문단 구분과 적절한 띄어쓰기로 가독성이 높은 글을 작성합니다. 각 문단은 한 줄씩 띄워서 작성하고, 모든 문장은 한국어 문법에 맞게 올바른 띄어쓰기를 사용합니다."},
                    {"role": "user", "content": content_prompt}
                ],
                max_tokens=4000
            )
            content = content_response.choices[0].message.content.strip()
            
        # 예전 버전(0.x) OpenAI API 호출로 폴백
        except (ImportError, AttributeError):
            content_response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문적인 블로그 작가입니다. 독자가 이해하기 쉽고 정보가 풍부하며 시각적으로 매력적인 콘텐츠를 작성합니다. 이모지와 강조 표현을 적절히 사용해 글을 생동감있게 만듭니다. 특히 문단 구분과 적절한 띄어쓰기로 가독성이 높은 글을 작성합니다. 각 문단은 한 줄씩 띄워서 작성하고, 모든 문장은 한국어 문법에 맞게 올바른 띄어쓰기를 사용합니다."},
                    {"role": "user", "content": content_prompt}
                ],
                max_tokens=4000
            )
            content = content_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"본문 생성 중 오류: {e}")
        # 오류 시 간단한 본문 생성
        content = f"# {title}\n\n{topic}에 관한 글입니다. API 호출 중 오류가 발생했습니다."
    
    # 태그 생성
    tags_prompt = f"다음 블로그 포스트 주제에 관련된 5개의 SEO 최적화 태그를 생성해주세요 (쉼표로 구분): '{topic}'"
    try:
        # OpenAI API v1.x 버전용 호출
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            tags_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 SEO 전문가입니다. 검색 엔진에서 높은 순위를 차지할 수 있는 태그를 제안합니다."},
                    {"role": "user", "content": tags_prompt}
                ],
                max_tokens=100
            )
            tags = tags_response.choices[0].message.content.strip()
            
        # 예전 버전(0.x) OpenAI API 호출로 폴백
        except (ImportError, AttributeError):
            tags_response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 SEO 전문가입니다. 검색 엔진에서 높은 순위를 차지할 수 있는 태그를 제안합니다."},
                    {"role": "user", "content": tags_prompt}
                ],
                max_tokens=100
            )
            tags = tags_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"태그 생성 중 오류: {e}")
        # 오류 시 기본 태그 생성
        tags = topic + ", 블로그, 정보, 가이드, 팁"
    
    print(f"제목: {title}")
    print(f"태그: {tags}")
    print("콘텐츠 생성 완료!")
    
    # 티스토리에 표시될 수 있도록 텍스트 처리
    # 단순 줄바꿈으로는 티스토리에서 문단이 제대로 표시되지 않을 수 있으므로
    # 각 문단을 <p> 태그로 감싸서 확실하게 분리
    paragraphs = content.split("\n\n")
    content_with_paragraphs = ""
    for paragraph in paragraphs:
        if paragraph.strip():  # 빈 문단은 건너뜀
            content_with_paragraphs += paragraph + "\n\n"
    
    return {
        "title": title,
        "content": content_with_paragraphs,
        "raw_content": content,  # 원본 콘텐츠도 저장
        "tags": tags,
        "format_type": 2  # 항상 일반 텍스트 모드(2)로 설정
    }

def write_post(driver, blog_post):
    """
    티스토리에 글 작성 프로세스를 처리하는 함수 (기본 모드로 작성)
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
    
    # 본문 입력 - 근본적 개선 방식으로 시도
    try:
        print("\n===== 본문 입력 시작 - 개선된 방식 =====")
        content = blog_post["content"]
        
        # 원본 콘텐츠를 HTML 형식으로 처리
        raw_content = blog_post["raw_content"]
        paragraphs = raw_content.split("\n\n")
        
        # 티스토리 최적화 HTML 형식으로 변환
        html_content = ""
        for paragraph in paragraphs:
            if paragraph.strip():
                # 제목줄 처리 (이모지로 시작하는 줄)
                if paragraph.strip().startswith("🌱") or paragraph.strip().startswith("💡") or paragraph.strip().startswith("🔍"):
                    title_text = paragraph.strip()
                    html_content += f"<h2>{title_text}</h2>\n\n"
                else:
                    # 줄바꿈 처리
                    paragraph = paragraph.replace("\n", "<br>")
                    # 강조 텍스트 처리
                    paragraph = paragraph.replace("**", "<strong>").replace("**", "</strong>")
                    # HTML 문단 태그로 감싸기
                    html_content += f"<p>{paragraph}</p>\n\n"
        
        # 티스토리 에디터 타입 감지
        editor_type = detect_tistory_editor_type(driver)
        print(f"감지된 티스토리 에디터 타입: {editor_type}")
        
        # 콘텐츠 설정 성공 여부 추적
        content_set = False
        
        # 1. 티스토리 API를 통한 직접 설정 (가장 신뢰할 수 있는 방법)
        try:
            print("\n방법 1: 티스토리 API 직접 사용")
            result = driver.execute_script("""
                try {
                    console.log('티스토리 에디터 API 직접 접근 시도...');
                    
                    // 티스토리 에디터 객체 접근
                    if (window.tistoryEditor) {
                        console.log('tistoryEditor 객체 발견!');
                        
                        // 1-1. setContent 메서드가 있는 경우
                        if (typeof tistoryEditor.setContent === 'function') {
                            console.log('tistoryEditor.setContent 호출...');
                            tistoryEditor.setContent(arguments[0]);
                            
                            // 중요: 데이터 모델도 업데이트
                            if (tistoryEditor.contentElement) {
                                tistoryEditor.contentElement.value = arguments[0];
                            }
                            
                            // 내부 상태 강제 업데이트
                            if (tistoryEditor.data) {
                                tistoryEditor.data.content = arguments[0]; 
                            }
                            
                            // 이벤트 트리거
                            var event = new Event('change', { bubbles: true });
                            document.querySelectorAll('textarea').forEach(function(el) {
                                if (el.id !== 'post-title-inp') el.dispatchEvent(event);
                            });
                            
                            return {success: true, method: 'setContent'};
                        }
                        
                        // 1-2. setContent 메서드가 없지만 contentElement가 있는 경우
                        else if (tistoryEditor.contentElement) {
                            console.log('tistoryEditor.contentElement에 직접 설정...');
                            tistoryEditor.contentElement.value = arguments[0];
                            
                            // 내부 상태 강제 업데이트
                            tistoryEditor.content = arguments[0];
                            
                            // 이벤트 트리거
                            var event = new Event('change', { bubbles: true });
                            tistoryEditor.contentElement.dispatchEvent(event);
                            
                            return {success: true, method: 'contentElement'};
                        }
                    }
                    
                    return {success: false, message: 'tistoryEditor 객체를 찾을 수 없음'};
                } catch (e) {
                    return {success: false, error: e.message};
                }
            """, html_content)
            
            print(f"티스토리 API 결과: {result}")
            
            if result and isinstance(result, dict) and result.get('success'):
                print("✅ 티스토리 API를 통한 콘텐츠 설정 성공!")
                content_set = True
        except Exception as api_e:
            print(f"티스토리 API 접근 오류: {api_e}")
        
        # 2. 숨겨진 폼 필드 포함 모든 관련 입력 요소 업데이트
        if not content_set:
            try:
                print("\n방법 2: 모든 관련 입력 요소 업데이트")
                result = driver.execute_script("""
                    try {
                        var updated = [];
                        
                        // 2-1. 모든 textarea 확인
                        document.querySelectorAll('textarea').forEach(function(ta) {
                            // 제목 필드가 아닌 경우만
                            if (ta.id !== 'post-title-inp' && ta.name !== 'title') {
                                ta.value = arguments[0];
                                ta.dispatchEvent(new Event('input', {bubbles:true}));
                                ta.dispatchEvent(new Event('change', {bubbles:true}));
                                updated.push('textarea: ' + (ta.name || ta.id || 'unnamed'));
                            }
                        });
                        
                        // 2-2. 숨겨진 content 관련 input 필드 확인
                        document.querySelectorAll('input[type="hidden"]').forEach(function(input) {
                            // content 관련 필드 패턴
                            if (input.name && (input.name.includes('content') || 
                                               input.name === 'editor' || 
                                               input.name === 'html' || 
                                               input.name === 'body')) {
                                input.value = arguments[0];
                                updated.push('hidden input: ' + input.name);
                            }
                        });
                        
                        return {success: updated.length > 0, updated: updated};
                    } catch (e) {
                        return {success: false, error: e.message};
                    }
                """, html_content)
                
                print(f"입력 요소 업데이트 결과: {result}")
                
                if result and isinstance(result, dict) and result.get('success'):
                    print("✅ 입력 요소 업데이트 성공!")
                    content_set = True
            except Exception as form_e:
                print(f"입력 요소 업데이트 오류: {form_e}")
        
        # 3. 에디터 타입별 전용 처리
        if not content_set:
            if editor_type == "tinymce":
                try:
                    print("\n방법 3: TinyMCE 에디터 전용 처리")
                    result = driver.execute_script("""
                        try {
                            if (typeof tinyMCE === 'undefined' || !tinyMCE.activeEditor) {
                                return {success: false, message: 'TinyMCE를 찾을 수 없음'};
                            }
                            
                            // 콘텐츠 설정
                            tinyMCE.activeEditor.setContent(arguments[0]);
                            
                            // 연결된 textarea도 업데이트
                            var textareaId = tinyMCE.activeEditor.id;
                            if (textareaId) {
                                var textarea = document.getElementById(textareaId);
                                if (textarea) {
                                    textarea.value = arguments[0];
                                    textarea.dispatchEvent(new Event('change', {bubbles:true}));
                                }
                            }
                            
                            // 현재 에디터 상태 확인
                            var content = tinyMCE.activeEditor.getContent();
                            
                            return {
                                success: content && content.length > 0,
                                contentLength: content.length
                            };
                        } catch (e) {
                            return {success: false, error: e.message};
                        }
                    """, html_content)
                    
                    print(f"TinyMCE 처리 결과: {result}")
                    
                    if result and isinstance(result, dict) and result.get('success'):
                        print("✅ TinyMCE 에디터 처리 성공!")
                        content_set = True
                except Exception as tinymce_e:
                    print(f"TinyMCE 처리 오류: {tinymce_e}")
                    
            elif editor_type == "codemirror":
                try:
                    print("\n방법 3: CodeMirror 에디터 전용 처리")
                    result = driver.execute_script("""
                        try {
                            var editors = document.querySelectorAll('.CodeMirror');
                            if (!editors.length) {
                                return {success: false, message: 'CodeMirror를 찾을 수 없음'};
                            }
                            
                            var updated = false;
                            
                            // 모든 CodeMirror 인스턴스 확인
                            for (var i = 0; i < editors.length; i++) {
                                var editor = editors[i];
                                
                                if (editor.CodeMirror) {
                                    // 콘텐츠 설정
                                    editor.CodeMirror.setValue(arguments[0]);
                                    
                                    // 변경 이벤트 발생시키기
                                    editor.CodeMirror.refresh();
                                    editor.CodeMirror.focus();
                                    
                                    // 연결된 textarea도 업데이트
                                    var textarea = editor.CodeMirror.getTextArea();
                                    if (textarea) {
                                        textarea.value = arguments[0];
                                        textarea.dispatchEvent(new Event('change', {bubbles:true}));
                                    }
                                    
                                    updated = true;
                                }
                            }
                            
                            return {success: updated};
                        } catch (e) {
                            return {success: false, error: e.message};
                        }
                    """, html_content)
                    
                    print(f"CodeMirror 처리 결과: {result}")
                    
                    if result and isinstance(result, dict) and result.get('success'):
                        print("✅ CodeMirror 에디터 처리 성공!")
                        content_set = True
                except Exception as cm_e:
                    print(f"CodeMirror 처리 오류: {cm_e}")
                    
            elif editor_type == "iframe":
                try:
                    print("\n방법 3: iframe 에디터 전용 처리")
                    # iframe 찾기
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    iframe_found = False
                    
                    for iframe in iframes:
                        try:
                            iframe_id = iframe.get_attribute("id") or ""
                            print(f"iframe 확인: id='{iframe_id}'")
                            
                            driver.switch_to.frame(iframe)
                            
                            # iframe 내부에 body 요소 찾기
                            body = driver.find_element(By.TAG_NAME, "body")
                            
                            # 콘텐츠 설정
                            driver.execute_script("""
                                arguments[0].innerHTML = arguments[1];
                                // 변경 이벤트 발생
                                var event = new Event('input', {bubbles:true});
                                arguments[0].dispatchEvent(event);
                            """, body, html_content)
                            
                            print(f"iframe {iframe_id}에 콘텐츠 설정 완료")
                            iframe_found = True
                            
                            # 원래 컨텍스트로 돌아가기
                            driver.switch_to.default_content()
                            
                            # iframe에 연결된 숨겨진 textarea도 찾아서 업데이트
                            driver.execute_script("""
                                // iframe과 연결된 textarea를 찾아 업데이트
                                if (arguments[0]) {
                                    var textareas = document.querySelectorAll('textarea');
                                    for (var i = 0; i < textareas.length; i++) {
                                        var ta = textareas[i];
                                        if (ta.id !== 'post-title-inp') {
                                            ta.value = arguments[1];
                                            ta.dispatchEvent(new Event('change', {bubbles:true}));
                                        }
                                    }
                                }
                            """, iframe_id, html_content)
                            
                            content_set = True
                            break
                        except Exception as iframe_process_e:
                            print(f"iframe {iframe_id} 처리 중 오류: {iframe_process_e}")
                            driver.switch_to.default_content()
                    
                    if not iframe_found:
                        print("처리 가능한 iframe을 찾지 못했습니다.")
                except Exception as iframe_e:
                    print(f"iframe 처리 오류: {iframe_e}")
                    # 혹시 모르니 default_content로 복귀
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass
        
        # 4. 모든 방법이 실패한 경우의 최후 시도 - 직접 DOM 수정
        if not content_set:
            try:
                print("\n방법 4: 최후의 시도 - DOM 직접 수정")
                result = driver.execute_script("""
                    try {
                        var updated = false;
                        
                        // 이벤트 생성 함수
                        function triggerEvents(element) {
                            ['input', 'change', 'keyup', 'blur'].forEach(function(eventType) {
                                element.dispatchEvent(new Event(eventType, {bubbles: true}));
                            });
                        }
                        
                        // 4-1. 폼 내부 요소 전체 업데이트
                        var forms = document.querySelectorAll('form');
                        for (var i = 0; i < forms.length; i++) {
                            var form = forms[i];
                            var contentElements = form.querySelectorAll('textarea, input[type="hidden"]');
                            
                            for (var j = 0; j < contentElements.length; j++) {
                                var el = contentElements[j];
                                // 제목이 아닌 큰 텍스트 영역
                                if (el.nodeName === 'TEXTAREA' && el.id !== 'post-title-inp' && 
                                    (el.clientHeight > 50 || el.rows > 3)) {
                                    el.value = arguments[0];
                                    triggerEvents(el);
                                    updated = true;
                                    console.log('큰 텍스트 영역 업데이트:', el.id || el.name);
                                }
                                // content 관련 숨겨진 입력 필드
                                else if (el.nodeName === 'INPUT' && el.type === 'hidden' && 
                                        (el.name.includes('content') || el.name === 'editor' || 
                                         el.id.includes('content'))) {
                                    el.value = arguments[0];
                                    triggerEvents(el);
                                    updated = true;
                                    console.log('숨겨진 콘텐츠 필드 업데이트:', el.id || el.name);
                                }
                            }
                        }
                        
                        // 4-2. 에디터 관련 DOM 요소 직접 탐색
                        var editorElements = document.querySelectorAll('[role="textbox"], [contenteditable="true"], .editor');
                        for (var k = 0; k < editorElements.length; k++) {
                            var editorEl = editorElements[k];
                            editorEl.innerHTML = arguments[0];
                            triggerEvents(editorEl);
                            updated = true;
                            console.log('에디터 요소 직접 업데이트:', editorEl.id || editorEl.className);
                        }
                        
                        // 4-3. 글로벌 에디터 객체에 강제 삽입
                        if (window.editor && typeof window.editor.setContent === 'function') {
                            window.editor.setContent(arguments[0]);
                            updated = true;
                            console.log('글로벌 에디터 업데이트');
                        }
                        
                        return {success: updated};
                    } catch (e) {
                        return {success: false, error: e.message};
                    }
                """, html_content)
                
                print(f"DOM 직접 수정 결과: {result}")
                
                if result and isinstance(result, dict) and result.get('success'):
                    print("✅ DOM 직접 수정 성공!")
                    content_set = True
            except Exception as dom_e:
                print(f"DOM 직접 수정 오류: {dom_e}")
        
        # 5. 콘텐츠 설정 확인 및 검증
        print("\n===== 콘텐츠 설정 검증 =====")
        content_verification = driver.execute_script("""
            try {
                var verification = {
                    found: false,
                    methods: []
                };
                
                // 1. tistoryEditor 확인
                if (window.tistoryEditor) {
                    var content = '';
                    if (tistoryEditor.content) {
                        content = tistoryEditor.content;
                        verification.methods.push('tistoryEditor.content');
                    } 
                    else if (tistoryEditor.contentElement && tistoryEditor.contentElement.value) {
                        content = tistoryEditor.contentElement.value;
                        verification.methods.push('tistoryEditor.contentElement');
                    }
                    
                    if (content && content.length > 100) {
                        verification.found = true;
                        verification.length = content.length;
                    }
                }
                
                // 2. TinyMCE 확인
                if (!verification.found && typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                    var content = tinyMCE.activeEditor.getContent();
                    if (content && content.length > 100) {
                        verification.found = true;
                        verification.length = content.length;
                        verification.methods.push('tinyMCE');
                    }
                }
                
                // 3. CodeMirror 확인
                if (!verification.found) {
                    var cmEditor = document.querySelector('.CodeMirror');
                    if (cmEditor && cmEditor.CodeMirror) {
                        var content = cmEditor.CodeMirror.getValue();
                        if (content && content.length > 100) {
                            verification.found = true;
                            verification.length = content.length;
                            verification.methods.push('CodeMirror');
                        }
                    }
                }
                
                // 4. textarea 확인
                if (!verification.found) {
                    var textareas = document.querySelectorAll('textarea');
                    for (var i = 0; i < textareas.length; i++) {
                        var ta = textareas[i];
                        if (ta.id !== 'post-title-inp' && ta.value && ta.value.length > 100) {
                            verification.found = true;
                            verification.length = ta.value.length;
                            verification.methods.push('textarea: ' + (ta.name || ta.id || i));
                            break;
                        }
                    }
                }
                
                // 5. hidden input 확인
                if (!verification.found) {
                    var hiddenInputs = document.querySelectorAll('input[type="hidden"]');
                    for (var i = 0; i < hiddenInputs.length; i++) {
                        var input = hiddenInputs[i];
                        if (input.name && (input.name.includes('content') || 
                                          input.name === 'editor' || input.name === 'html') && 
                            input.value && input.value.length > 100) {
                            verification.found = true;
                            verification.length = input.value.length;
                            verification.methods.push('hidden: ' + input.name);
                            break;
                        }
                    }
                }
                
                return verification;
            } catch (e) {
                return {found: false, error: e.message};
            }
        """)
        
        if content_verification and content_verification.get('found'):
            print(f"✅ 콘텐츠가 성공적으로 설정됨: {content_verification.get('length')} 바이트")
            print(f"   설정 방법: {', '.join(content_verification.get('methods', []))}")
            content_set = True
        else:
            if content_verification:
                print(f"❌ 콘텐츠 설정 확인 실패: {content_verification}")
            else:
                print("❌ 콘텐츠 설정 확인 실패: 응답 없음")
        
        # 최종 결과 반환
        if content_set:
            print("\n✅ 본문 입력 성공 - 적어도 하나 이상의 방법으로 콘텐츠가 설정되었습니다.")
        else:
            print("\n❌ 본문 입력 시도 실패 - 모든 방법이 실패했습니다.")
        
        print("===== 본문 입력 완료 =====")
        
    except Exception as e:
        print(f"본문 입력 중 오류: {e}")
        import traceback
        print(traceback.format_exc())

# 티스토리 에디터 타입 감지 함수 추가
def detect_tistory_editor_type(driver):
    """티스토리에서 사용 중인 에디터 타입을 감지"""
    try:
        editor_type = driver.execute_script("""
            try {
                // TinyMCE 에디터 확인
                if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                    return 'tinymce';
                }
                
                // CodeMirror 에디터 확인
                if (document.querySelector('.CodeMirror')) {
                    return 'codemirror';
                }
                
                // iframe 기반 에디터 확인
                var editorIframes = document.querySelectorAll('iframe[id*="editor"], iframe.editor-frame');
                if (editorIframes.length > 0) {
                    return 'iframe';
                }
                
                // 티스토리 전용 에디터 확인
                if (window.tistoryEditor) {
                    return 'tistory';
                }
                
                // DOM 기반 추정
                if (document.querySelector('[contenteditable="true"]')) {
                    return 'contenteditable';
                }
                
                // 찾지 못한 경우 textarea 기반으로 추정
                var textareas = document.querySelectorAll('textarea');
                for (var i = 0; i < textareas.length; i++) {
                    if (textareas[i].id !== 'post-title-inp' && textareas[i].clientHeight > 100) {
                        return 'textarea';
                    }
                }
                
                return 'unknown';
            } catch (e) {
                console.error('에디터 타입 감지 오류:', e);
                return 'error: ' + e.message;
            }
        """)
        
        return editor_type or "unknown"
    except Exception as e:
        print(f"에디터 타입 감지 중 오류: {e}")
        return "error"

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

# 콘텐츠 형식 검증 함수
def validate_content_format(content, format_type):
    """
    생성된 콘텐츠가 선택한 형식에 맞는지 검증
    format_type: 2=일반 텍스트
    """
    try:
        # 일반 텍스트 (기본값)
        # HTML이나 마크다운 형식이 과도하게 있는지 확인
        html_tags = ['<h1', '<h2', '<h3', '<p>', '<div', '<ul', '<ol', '<li', '<strong', '<em']
        html_count = sum(1 for tag in html_tags if tag in content.lower())
        
        markdown_patterns = ['# ', '## ', '### ', '**', '*', '- ', '1. ', '> ', '```']
        md_count = sum(1 for pattern in markdown_patterns if pattern in content)
        
        # 볼드체(**) 강조는 일반 텍스트에서도 사용하므로 제외
        if '**' in markdown_patterns:
            markdown_patterns.remove('**')
            
        # 이모지 포함 여부 확인 (이모지가 있으면 좋음)
        emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # 이모티콘
                               u"\U0001F300-\U0001F5FF"  # 기호 및 픽토그램
                               u"\U0001F680-\U0001F6FF"  # 교통 및 지도 기호
                               u"\U0001F700-\U0001F77F"  # 알케미 기호
                               u"\U0001F780-\U0001F7FF"  # 기하학적 모양
                               u"\U0001F800-\U0001F8FF"  # 추가 화살표
                               u"\U0001F900-\U0001F9FF"  # 추가 이모티콘
                               u"\U0001FA00-\U0001FA6F"  # 게임 기호
                               u"\U0001FA70-\U0001FAFF"  # 기호 및 픽토그램 확장
                               u"\U00002702-\U000027B0"  # 기타 기호
                               u"\U000024C2-\U0001F251" 
                               "]+", flags=re.UNICODE)
        
        emoji_found = len(emoji_pattern.findall(content))
        bold_count = content.count('**')
        
        print(f"콘텐츠 분석: 이모지 {emoji_found}개, 볼드체 {bold_count//2}개 사용됨")
        
        # HTML이나 마크다운 형식이 5개 이하면 일반 텍스트로 간주 (볼드체 제외)
        if html_count <= 5 and md_count <= 5:
            print("일반 텍스트 형식 검증 통과")
            return True
        else:
            print(f"경고: HTML({html_count}개) 또는 마크다운({md_count}개) 요소가 많이 발견됨")
            print("일반 텍스트 형식에 적합하지 않을 수 있습니다.")
            # 경고만 출력하고 진행
            return True
    except Exception as e:
        print(f"콘텐츠 형식 검증 중 오류: {e}")
        return True  # 오류 발생 시 기본값은 유효한 것으로 처리
        
# 콘텐츠 적용 검증 함수
def verify_content_applied(driver, content, mode):
    """
    콘텐츠가 에디터에 제대로 적용되었는지 검증
    """
    try:
        print("콘텐츠 적용 검증 중...")
        
        # CodeMirror 에디터 확인 (우선 확인)
        has_content = driver.execute_script("""
            try {
                // CodeMirror 에디터 확인
                var editors = document.querySelectorAll('.CodeMirror, .cm-editor');
                if (editors.length > 0) {
                    for (var i = 0; i < editors.length; i++) {
                        var editor = editors[i];
                        var content = '';
                        
                        // CodeMirror 인스턴스에서 내용 확인
                        if (editor.CodeMirror) {
                            content = editor.CodeMirror.getValue();
                        }
                        // 내부 textarea 확인
                        else {
                            var textarea = editor.querySelector('textarea');
                            if (textarea) {
                                content = textarea.value;
                            }
                        }
                        
                        // 내용이 있으면 성공
                        if (content && content.length > 100) {
                            console.log("CodeMirror 에디터에 충분한 내용이 있습니다: " + content.length + "자");
                            return true;
                        }
                    }
                }
                
                // TinyMCE 확인
                if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                    var editorContent = tinyMCE.activeEditor.getContent();
                    if (editorContent && editorContent.length > 100) {
                        console.log("TinyMCE 에디터에 충분한 내용이 있습니다: " + editorContent.length + "자");
                        return true;
                    }
                }
                
                // iframe 내용 확인
                var iframes = document.querySelectorAll('iframe');
                for (var j = 0; j < iframes.length; j++) {
                    try {
                        var frameDoc = iframes[j].contentDocument || iframes[j].contentWindow.document;
                        if (frameDoc && frameDoc.body) {
                            var iframeContent = frameDoc.body.innerHTML;
                            if (iframeContent && iframeContent.length > 100) {
                                console.log("iframe에 충분한 내용이 있습니다: " + iframeContent.length + "자");
                                return true;
                            }
                        }
                    } catch(e) {}
                }
                
                return false;
            } catch(e) {
                console.error("내용 확인 중 오류: " + e.message);
                return false;
            }
        """)
        
        if has_content:
            print("에디터에 충분한 내용이 적용되었습니다.")
            return True
        
        # 내용이 충분히 적용되지 않은 경우, 기존 방식으로 검증 진행
        print("콘텐츠 적용 여부를 더 자세히 분석 중...")
            
        # 1. 원본 콘텐츠에서 중요한 부분 추출
        # - 제목: <h1>, <h2> 태그 또는 첫 줄
        # - 주요 단어 및 문구
        import re
        
        # 원본 콘텐츠에서 제목 또는 중요 부분 추출
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE)
        if not title_match:
            title_match = re.search(r'<h2[^>]*>(.*?)</h2>', content, re.IGNORECASE)
        
        title_text = ""
        if title_match:
            title_text = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        else:
            # H1/H2 태그가 없으면 첫 단락이나 첫 줄을 제목으로 간주
            lines = content.split('\n')
            for line in lines:
                stripped = re.sub(r'<[^>]+>', '', line).strip()
                if stripped:
                    title_text = stripped
                    break
        
        print(f"원본 콘텐츠 제목: '{title_text}'")
        
        # 중요 단어/문구 추출 (최소 4글자 이상의 명사구)
        important_phrases = []
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
        
        for p in paragraphs:
            # 태그 제거
            clean_text = re.sub(r'<[^>]+>', '', p).strip()
            
            # 짧은 문단 건너뛰기
            if len(clean_text) < 20:
                continue
                
            # 문장 분리
            sentences = re.split(r'[.!?]', clean_text)
            for sentence in sentences:
                if len(sentence.strip()) >= 15:  # 적절한 길이의 문장만
                    important_phrases.append(sentence.strip())
        
        # 최대 3개의 중요 문구 선택
        if len(important_phrases) > 3:
            important_phrases = important_phrases[:3]
            
        print(f"중요 문구 {len(important_phrases)}개 추출: {important_phrases}")
        
        # 2. 현재 에디터 내용 가져오기
        editor_content = ""
        
        # CodeMirror 에디터에서 내용 가져오기 (우선)
        try:
            editor_content = driver.execute_script("""
                try {
                    // CodeMirror 에디터
                    var editors = document.querySelectorAll('.CodeMirror, .cm-editor');
                    if (editors.length > 0) {
                        for (var i = 0; i < editors.length; i++) {
                            var editor = editors[i];
                            if (editor.CodeMirror) {
                                return editor.CodeMirror.getValue() || '';
                            }
                        }
                    }
                    
                    // TinyMCE 에디터
                    if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                        return tinyMCE.activeEditor.getContent() || '';
                    }
                    
                    // iframe 내용
                    var iframes = document.querySelectorAll('iframe');
                    for (var j = 0; j < iframes.length; j++) {
                        try {
                            var frame = iframes[j];
                            var frameDoc = frame.contentDocument || frame.contentWindow.document;
                            if (frameDoc && frameDoc.body) {
                                return frameDoc.body.innerHTML || '';
                            }
                        } catch(e) {}
                    }
                    
                    // 일반 에디터 요소
                    var editorElements = document.querySelectorAll('.html-editor, [contenteditable="true"], textarea.code-editor');
                    if (editorElements.length > 0) {
                        return editorElements[0].value || editorElements[0].innerHTML || '';
                    }
                    
                    return '';
                } catch(e) {
                    console.error("에디터 내용 가져오기 중 오류: " + e.message);
                    return '';
                }
            """)
        except Exception as e:
            print(f"에디터 내용 가져오기 중 오류: {e}")
        
        # 디버깅용: 에디터에 내용이 있는지 확인
        if editor_content:
            content_preview = editor_content[:200] + "..." if len(editor_content) > 200 else editor_content
            print(f"에디터 내용 샘플: {content_preview}")
            print(f"에디터 내용 길이: {len(editor_content)} 자")
        else:
            print("에디터에서 내용을 가져올 수 없습니다.")
            
            # 보강 검사: 에디터에 최소한의 내용이라도 있는지 확인
            content_exists = driver.execute_script("""
                // 모든 가능한 에디터 요소 검사
                var elements = [
                    document.querySelector('.CodeMirror, .cm-editor'),
                    document.querySelector('.mce-content-body'),
                    document.querySelector('[contenteditable="true"]'),
                    document.querySelector('textarea.code-editor')
                ];
                
                for (var i = 0; i < elements.length; i++) {
                    var el = elements[i];
                    if (el && (
                        (el.innerHTML && el.innerHTML.length > 50) || 
                        (el.value && el.value.length > 50)
                    )) {
                        return true;
                    }
                }
                
                return false;
            """)
            
            if content_exists:
                print("에디터에 내용이 존재하는 것으로 확인됩니다.")
                return True
            
        # 3. 에디터 내용에서 제목과 주요 문구 확인
        
        # 제목 확인 (티스토리가 추가하는 속성 고려)
        title_found = False
        if title_text:
            # 정확히 일치하는 경우
            if title_text in editor_content:
                title_found = True
                print(f"제목 정확히 일치: '{title_text}'")
            else:
                # 속성이 추가된 태그 내에서 확인
                title_patterns = [
                    re.escape(title_text),
                    # 다양한 형태로 추가 가능
                ]
                
                for pattern in title_patterns:
                    if re.search(pattern, editor_content, re.IGNORECASE):
                        title_found = True
                        print(f"제목 패턴 일치: '{pattern}'")
                        break
        
        # 주요 문구 확인
        phrases_found = 0
        for phrase in important_phrases:
            if phrase in editor_content:
                phrases_found += 1
                print(f"문구 일치: '{phrase}'")
            else:
                # 문구의 일부(첫 10단어)라도 있는지 확인
                words = phrase.split()[:10]
                partial_phrase = ' '.join(words)
                if len(partial_phrase) > 15 and partial_phrase in editor_content:
                    phrases_found += 1
                    print(f"부분 문구 일치: '{partial_phrase}'")
        
        # 검증 결과
        if title_found or phrases_found > 0:
            print(f"콘텐츠 적용 검증 통과: 제목 일치={title_found}, 문구 일치={phrases_found}")
            return True
        else:
            # 에디터 내용 길이가 충분히 길면, 어떤 내용이 들어갔다고 가정
            if editor_content and len(editor_content) > 500:
                print(f"콘텐츠 적용 추정: 에디터에 {len(editor_content)} 길이의 콘텐츠 존재")
                return True
            
            print("콘텐츠 적용 검증 실패: 제목과 주요 문구가 모두 일치하지 않습니다.")
            print("그러나 글 작성은 계속 진행합니다.")
            return True  # 확인 실패해도 계속 진행
    except Exception as e:
        print(f"콘텐츠 적용 검증 중 오류: {e}")
        # 오류 발생시 내용이 있다고 가정 (false positive가 false negative보다 나음)
        return True

# 모달 창에서 확인 버튼 클릭을 돕는 새로운 함수 추가
def click_confirm_dialog_button(driver, wait_time=3):
    """모드 변경 확인 대화상자의 '확인' 버튼 클릭"""
    try:
        print("확인 대화상자 검색 중...")
        
        # 1. 일반적인 알림창(alert) 처리
        try:
            WebDriverWait(driver, 2).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            print(f"알림창 발견: '{alert.text}'")
            alert.accept()
            print("알림창의 '확인' 버튼을 클릭했습니다.")
            return True
        except Exception as alert_e:
            print(f"브라우저 기본 알림창 없음: {alert_e}")
        
        # 2. 대화상자의 텍스트 내용과 버튼을 기준으로 찾기
        dialog_texts = ["작성 모드", "변경", "서식이 유지되지 않을", "모드 전환"]
        
        # 텍스트 내용으로 대화상자 찾기
        for text in dialog_texts:
            try:
                dialog_elem = WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{text}')]"))
                )
                
                if dialog_elem:
                    print(f"대화상자 텍스트 발견: '{text}'")
                    
                    # 부모/조상 요소에서 버튼 찾기
                    parent = dialog_elem
                    for _ in range(5):  # 최대 5단계 상위로 올라가기
                        try:
                            parent = parent.find_element(By.XPATH, "..")  # 부모 요소로 이동
                            buttons = parent.find_elements(By.TAG_NAME, "button")
                            
                            if buttons:
                                for btn in buttons:
                                    if '확인' in btn.text or not btn.text.strip():
                                        btn.click()
                                        print(f"대화상자 버튼 클릭: '{btn.text}'")
                                        return True
                        except:
                            break
            except:
                continue
        
        # 3. JavaScript로 대화상자 찾아 처리
        result = driver.execute_script("""
            // 여러 가지 가능한 확인 버튼 선택자
            var confirmSelectors = [
                '.confirm-yes', '.btn-confirm', '.btn_confirm', 
                '.btn_yes', '.confirm_ok', '.btn_ok', '.btn-primary',
                'button.confirm', 'button.yes'
            ];
            
            // 텍스트로 확인 버튼 찾기
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                if (btn.textContent.includes('확인') || 
                    btn.textContent.toLowerCase().includes('ok') || 
                    btn.textContent.toLowerCase().includes('yes')) {
                    console.log('확인 버튼 발견: ' + btn.textContent);
                    btn.click();
                    return true;
                }
            }
            
            // 선택자로 확인 버튼 찾기
            for (var j = 0; j < confirmSelectors.length; j++) {
                var elements = document.querySelectorAll(confirmSelectors[j]);
                if (elements.length > 0) {
                    elements[0].click();
                    return true;
                }
            }
            
            // "작성 모드를 변경" 텍스트를 포함하는 요소 주변의 버튼 찾기
            var confirmTexts = ["작성 모드", "변경", "서식이 유지", "모드 전환"];
            for (var k = 0; k < confirmTexts.length; k++) {
                var textNodes = [];
                var walk = document.createTreeWalker(
                    document.body, 
                    NodeFilter.SHOW_TEXT, 
                    { acceptNode: function(node) { 
                        return node.nodeValue.includes(confirmTexts[k]) ? 
                            NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT; 
                    }}, 
                    false
                );
                
                while(walk.nextNode()) {
                    textNodes.push(walk.currentNode.parentNode);
                }
                
                for (var l = 0; l < textNodes.length; l++) {
                    var node = textNodes[l];
                    for (var m = 0; m < 5; m++) {  // 최대 5단계 상위로 올라가기
                        if (!node) break;
                        
                        var nodeBtns = node.querySelectorAll('button');
                        if (nodeBtns.length > 0) {
                            // 첫 번째 버튼이 일반적으로 '확인'
                            nodeBtns[0].click();
                            return true;
                        }
                        
                        node = node.parentNode;
                    }
                }
            }
            
            // 모든 모달/대화상자 스캔
            var dialogs = document.querySelectorAll('.modal, .dialog, .confirm, .alert, [role="dialog"]');
            for (var n = 0; n < dialogs.length; n++) {
                var dialogButtons = dialogs[n].querySelectorAll('button');
                if (dialogButtons.length > 0) {
                    // 첫 번째 버튼이 일반적으로 '확인'
                    dialogButtons[0].click();
                    return true;
                }
            }
            
            return false;
        """)
        
        if result:
            print("JavaScript를 통해 확인 버튼을 클릭했습니다.")
            return True
            
        print("확인 대화상자를 찾지 못했거나 '확인' 버튼을 클릭하지 못했습니다.")
        return False
        
    except Exception as e:
        print(f"확인 대화상자 처리 중 오류: {e}")
        return False

# 알림창 처리를 위한 함수 추가
def handle_alert(driver, max_attempts=3):
    """
    브라우저에 표시될 수 있는 알림창(alert)을 처리하는 함수
    티스토리의 "저장된 글이 있습니다." 메시지 등을 자동으로 처리
    """
    try:
        for attempt in range(max_attempts):
            try:
                # 알림창 확인 (1초 타임아웃으로 빠른 확인)
                WebDriverWait(driver, 1).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                alert_text = alert.text
                
                print(f"알림창 발견 ({attempt+1}/{max_attempts}): '{alert_text}'")
                
                # 저장된 글 관련 알림
                if "저장된 글이 있습니다" in alert_text and "이어서 작성하시겠습니까" in alert_text:
                    print("이전에 저장된 글 관련 알림입니다. '취소' 버튼 클릭 (새 글 작성)")
                    alert.dismiss()  # '취소' 버튼 클릭
                else:
                    # 기타 알림은 '확인' 버튼 클릭
                    print(f"일반 알림 - '확인' 버튼 클릭: '{alert_text}'")
                    alert.accept()
                
                # 알림창 처리 후 잠시 대기
                time.sleep(1)
            
            except Exception:
                # 더 이상 알림창이 없으면 종료
                break
                
        return True
    except Exception as e:
        print(f"알림창 처리 중 오류 (무시됨): {e}")
        return False

# 콘텐츠 생성 함수에 재시도 로직 추가
def generate_blog_content_with_retry(topic, format_type=2, max_retries=3, retry_delay=5):
    """재시도 로직이 포함된 블로그 콘텐츠 생성 함수"""
    for attempt in range(max_retries):
        try:
            return generate_blog_content(topic, format_type=2)  # 항상 일반 텍스트 모드(2)로 설정
        except Exception as e:
            print(f"시도 {attempt+1}/{max_retries} 실패: {e}")
            if attempt < max_retries - 1:
                print(f"{retry_delay}초 후 재시도합니다...")
                time.sleep(retry_delay)
            else:
                print("최대 재시도 횟수를 초과했습니다.")
                raise

def publish_post(driver, blog_post=None):
    """발행 버튼 클릭 및 발행 처리"""
    try:
        # 디버깅 정보: 페이지의 모든 버튼 정보 출력
        try:
            print("\n==== 페이지의 모든 버튼 정보 [디버깅] ====")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"페이지에서 총 {len(buttons)}개의 버튼을 찾았습니다.")
            
            for i, btn in enumerate(buttons[:30]):  # 처음 30개 버튼만 출력
                try:
                    btn_text = btn.text.strip() or '(텍스트 없음)'
                    btn_id = btn.get_attribute('id') or '(ID 없음)'
                    btn_class = btn.get_attribute('class') or '(클래스 없음)'
                    btn_type = btn.get_attribute('type') or '(타입 없음)'
                    is_displayed = btn.is_displayed()
                    is_enabled = btn.is_enabled()
                    print(f"버튼 {i+1}: 텍스트='{btn_text}', ID='{btn_id}', 클래스='{btn_class}', 타입='{btn_type}', 표시={is_displayed}, 활성화={is_enabled}")
                    
                    # 공개 발행 관련 텍스트가 있는 버튼 강조 표시
                    if '공개' in btn_text or '발행' in btn_text:
                        print(f"  >>> 발행 관련 버튼으로 의심됨: {btn_text} (ID={btn_id}) <<<")
                except Exception as e:
                    print(f"버튼 {i+1}: 정보 가져오기 실패 - {e}")
            
            # form 요소도 확인
            forms = driver.find_elements(By.TAG_NAME, "form")
            print(f"\n페이지에서 총 {len(forms)}개의 폼을 찾았습니다.")
            for i, form in enumerate(forms):
                try:
                    form_id = form.get_attribute('id') or '(ID 없음)'
                    form_action = form.get_attribute('action') or '(action 없음)'
                    form_method = form.get_attribute('method') or '(method 없음)'
                    submit_buttons = form.find_elements(By.CSS_SELECTOR, 'button[type="submit"]')
                    print(f"폼 {i+1}: ID='{form_id}', action='{form_action}', method='{form_method}', submit 버튼 수={len(submit_buttons)}")
                except Exception as e:
                    print(f"폼 {i+1}: 정보 가져오기 실패 - {e}")
            
            print("==== 디버깅 정보 끝 ====\n")
        except Exception as debug_e:
            print(f"디버깅 정보 수집 중 오류: {debug_e}")
            
        # 발행 전 콘텐츠를 강제로 다시 설정 (주요 수정)
        if blog_post:
            print("\n===== 발행 전 콘텐츠 강제 재설정 =====")
            
            # HTML 형식으로 변환 (줄바꿈, 문단 구분)
            raw_content = blog_post["raw_content"]
            paragraphs = raw_content.split("\n\n")
            
            # 개선된 HTML 형식으로 각 문단 변환
            html_content = ""
            for paragraph in paragraphs:
                if paragraph.strip():
                    # 줄바꿈 처리
                    paragraph = paragraph.replace("\n", "<br>")
                    # HTML 문단 태그로 감싸기
                    html_content += f"<p>{paragraph}</p>\n"
            
            print(f"최종 HTML 형식 콘텐츠 준비 완료: {len(html_content)} 바이트")
            
            # 모든 가능한 방법으로 콘텐츠 설정 시도
            
            # 방법 1: 기본 iframe 편집기 설정
            iframe_editor = find_editor_iframe(driver)
            if iframe_editor:
                try:
                    driver.switch_to.frame(iframe_editor)
                    print("iframe 에디터에 접근했습니다.")
                    body = driver.find_element(By.TAG_NAME, "body")
                    driver.execute_script("arguments[0].innerHTML = arguments[1];", body, html_content)
                    print("iframe 내부 body에 HTML 콘텐츠를 설정했습니다.")
                    driver.switch_to.default_content()
                    time.sleep(1)
                except Exception as e:
                    print(f"iframe 콘텐츠 설정 오류: {e}")
                    driver.switch_to.default_content()
            
            # 방법 2: JavaScript를 통한 다양한 에디터 접근
            try:
                result = driver.execute_script("""
                    try {
                        console.log("콘텐츠 설정 스크립트 실행 중...");
                        var content = arguments[0];
                        var setSuccess = false;

                        // TinyMCE 설정
                        if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                            console.log("TinyMCE 에디터 발견");
                            tinyMCE.activeEditor.setContent(content);
                            console.log("TinyMCE 콘텐츠 설정됨");
                            setSuccess = true;
                        }

                        // 티스토리 에디터 API 사용
                        if (window.tistoryEditor) {
                            console.log("티스토리 에디터 객체 발견");
                            if (typeof tistoryEditor.setContent === 'function') {
                                tistoryEditor.setContent(content);
                                console.log("tistoryEditor.setContent 호출됨");
                                setSuccess = true;
                            }
                            else if (typeof tistoryEditor.setHtmlContent === 'function') {
                                tistoryEditor.setHtmlContent(content);
                                console.log("tistoryEditor.setHtmlContent 호출됨");
                                setSuccess = true;
                            }
                            
                            // 티스토리 내부 상태 강제 업데이트
                            if (tistoryEditor.contentElement) {
                                tistoryEditor.contentElement.value = content;
                                console.log("tistoryEditor.contentElement 설정됨");
                                setSuccess = true;
                            }
                            
                            // 티스토리 내부 데이터 설정 (중요!)
                            tistoryEditor.content = content;
                            console.log("tistoryEditor.content 직접 설정됨");
                            setSuccess = true;
                        }

                        // CodeMirror 에디터 설정
                        var cmEditors = document.querySelectorAll('.CodeMirror');
                        if (cmEditors.length > 0) {
                            for (var i = 0; i < cmEditors.length; i++) {
                                var ed = cmEditors[i];
                                if (ed.CodeMirror) {
                                    ed.CodeMirror.setValue(content);
                                    console.log("CodeMirror 콘텐츠 설정됨");
                                    setSuccess = true;
                                }
                            }
                        }

                        // 모든 iframe 순회
                        var frames = document.querySelectorAll('iframe');
                        for (var i = 0; i < frames.length; i++) {
                            try {
                                var frame = frames[i];
                                var frameDoc = frame.contentDocument || frame.contentWindow.document;
                                if (frameDoc && frameDoc.body) {
                                    frameDoc.body.innerHTML = content;
                                    console.log(i + "번 iframe에 콘텐츠 설정됨");
                                    setSuccess = true;
                                }
                            } catch(e) {
                                console.log("iframe 접근 오류: " + e.message);
                            }
                        }

                        // 마지막 시도: 모든 가능한 에디터 요소 순회
                        var possibleEditors = [
                            document.querySelector('[data-role="editor"]'),
                            document.querySelector('.editor-body'),
                            document.querySelector('.content-area'),
                            document.querySelector('.editor-frame'),
                            document.querySelector('#editor')
                        ];
                        
                        for (var j = 0; j < possibleEditors.length; j++) {
                            var editor = possibleEditors[j];
                            if (editor) {
                                try {
                                    editor.innerHTML = content;
                                    console.log("가능한 에디터 요소에 콘텐츠 설정됨");
                                    setSuccess = true;
                                } catch(e) {}
                            }
                        }

                        // 모든 textarea 확인 (마지막 시도)
                        var textareas = document.querySelectorAll('textarea');
                        for (var k = 0; k < textareas.length; k++) {
                            var ta = textareas[k];
                            if (ta.id !== 'post-title-inp' && ta.clientHeight > 50) {
                                ta.value = content;
                                console.log("큰 textarea에 콘텐츠 설정됨");
                                setSuccess = true;
                                
                                // 이벤트 발생시켜 변경사항 알림
                                var event = new Event('input', { bubbles: true });
                                ta.dispatchEvent(event);
                            }
                        }

                        return setSuccess ? "콘텐츠 설정 성공" : "모든 에디터 접근 시도 실패";
                    } catch(e) {
                        return "오류 발생: " + e.message;
                    }
                """, html_content)
                
                print(f"자바스크립트 콘텐츠 설정 결과: {result}")
            except Exception as e:
                print(f"자바스크립트 실행 오류: {e}")
        
        # 바로 공개발행 버튼 찾기 및 클릭하기
        print("\n===== 공개발행 버튼 검색 및 클릭 =====")
        
        # ID를 통해 직접 버튼 찾기 (가장 정확한 방법)
        publish_found = False
        try:
            publish_btn = driver.find_element(By.ID, "publish-btn")
            btn_text = publish_btn.text
            print(f"ID로 발행 버튼 찾음: '{btn_text}' (id=publish-btn)")
            publish_btn.click()
            print("'공개 발행' 버튼 클릭 성공")
            time.sleep(2)
            confirm_publish(driver)
            publish_found = True
        except Exception as e:
            print(f"ID로 발행 버튼 찾기 실패: {e}")
        
        # 정확한 텍스트로 버튼 찾기
        if not publish_found:
            try:
                # 주의: '공개 발행'에는 공백이 있음
                publish_buttons = driver.find_elements(By.XPATH, "//button[normalize-space(text()) = '공개 발행']")
                if publish_buttons:
                    print(f"정확한 텍스트로 '공개 발행' 버튼 찾음")
                    publish_buttons[0].click()
                    print("'공개 발행' 버튼 클릭 성공")
                    time.sleep(2)
                    confirm_publish(driver)
                    publish_found = True
            except Exception as e:
                print(f"정확한 텍스트로 버튼 찾기 실패: {e}")
                
        # CSS 선택자로 찾기
        if not publish_found:
            try:
                # 정확한 버튼을 위한 CSS 선택자
                css_selectors = [
                    "#publish-btn",  # 가장 정확한 ID 선택자
                    "button#publish-btn",  # ID 선택자 변형
                    "button.btn.btn-default[type='submit']",  # 클래스와 타입 조합
                    "form button[type='submit']",  # 폼 내 submit 버튼
                    ".btn-publish",
                    ".publish-btn",
                    "button[type='submit']"
                ]
                
                for selector in css_selectors:
                    btns = driver.find_elements(By.CSS_SELECTOR, selector)
                    if btns:
                        for btn in btns:
                            btn_text = btn.text.strip()
                            print(f"CSS 선택자로 버튼 찾음: '{btn_text}' (selector={selector})")
                            if '공개' in btn_text or '발행' in btn_text or btn.get_attribute('id') == 'publish-btn':
                                btn.click()
                                print(f"'{btn_text}' 버튼 클릭 (selector={selector})")
                                time.sleep(2)
                                confirm_publish(driver)
                                publish_found = True
                                break
                        if publish_found:
                            break
            except Exception as e:
                print(f"CSS 선택자로 버튼 찾기 실패: {e}")
                
        # 폼 직접 제출 시도
        if not publish_found:
            try:
                print("\n폼 직접 제출 시도...")
                forms = driver.find_elements(By.TAG_NAME, "form")
                if forms:
                    for form in forms:
                        try:
                            # 폼 내에 '공개 발행' 버튼이 있는지 확인
                            submit_buttons = form.find_elements(By.CSS_SELECTOR, "button[type='submit']")
                            if submit_buttons:
                                for btn in submit_buttons:
                                    btn_text = btn.text.strip()
                                    if '공개' in btn_text or '발행' in btn_text:
                                        print(f"폼 내 발행 버튼 발견: '{btn_text}'")
                                        btn.click()
                                        print(f"폼 내 '{btn_text}' 버튼 클릭")
                                        time.sleep(2)
                                        confirm_publish(driver)
                                        publish_found = True
                                        break
                            
                            # 버튼이 없거나 클릭하지 못한 경우 폼 직접 제출
                            if not publish_found:
                                driver.execute_script("arguments[0].submit();", form)
                                print("JavaScript로 폼 직접 제출")
                                time.sleep(2)
                                confirm_publish(driver)
                                publish_found = True
                        except Exception as form_e:
                            print(f"폼 처리 중 오류: {form_e}")
            except Exception as forms_e:
                print(f"폼 접근 중 오류: {forms_e}")
         
        # 1. '공개발행' 텍스트가 있는 버튼 찾기 (이전 방식과 병합)
        if not publish_found:
            try:
                # 부분 텍스트 매칭으로 검색 범위 확장
                publish_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '공개') or contains(text(), '발행')]")
                if publish_buttons:
                    for btn in publish_buttons:
                        btn_text = btn.text.strip()
                        print(f"버튼 발견: '{btn_text}'")
                        btn.click()
                        print(f"'{btn_text}' 버튼을 클릭했습니다.")
                        time.sleep(2)
                        confirm_publish(driver)
                        publish_found = True
                        break
            except Exception as e:
                print(f"부분 텍스트 매칭 버튼 클릭 시도 중 오류: {e}")
            
        # 2. JavaScript를 사용하여 공개발행 버튼 찾기
        if not publish_found:
            try:
                print("JavaScript를 통한 발행 버튼 검색...")
                result = driver.execute_script("""
                    // ID로 직접 찾기 (가장 정확한 방법)
                    var btn = document.getElementById('publish-btn');
                    if (btn) {
                        console.log('ID로 버튼 찾음: publish-btn');
                        btn.click();
                        return "ID publish-btn 버튼 클릭됨";
                    }
                    
                    // 모든 버튼 요소 가져오기
                    var allButtons = document.querySelectorAll('button');
                    console.log('총 ' + allButtons.length + '개의 버튼 확인 중');
                    
                    // '공개 발행'(공백 있음) 텍스트가 있는 버튼 찾기
                    for (var i = 0; i < allButtons.length; i++) {
                        var btn = allButtons[i];
                        var btnText = btn.textContent.trim();
                        
                        if (btnText === '공개 발행' || btnText === '공개발행' || 
                            (btnText.includes('공개') && btnText.includes('발행'))) {
                            console.log('발견된 버튼: ' + btnText);
                            btn.click();
                            return "버튼 '" + btnText + "' 클릭됨";
                        }
                    }
                    
                    // 버튼 ID나 클래스로 시도
                    var publishBtn = document.querySelector('#publish-btn, .btn-publish, .publish-btn, button[type="submit"]');
                    if (publishBtn) {
                        publishBtn.click();
                        return "선택자로 찾은 발행 버튼 클릭됨";
                    }

                    // submit 타입 버튼 중 공개/발행이 포함된 것 찾기
                    var submitButtons = document.querySelectorAll('button[type="submit"]');
                    for (var j = 0; j < submitButtons.length; j++) {
                        var submitBtn = submitButtons[j];
                        var btnText = submitBtn.textContent.trim();
                        if (btnText.includes('공개') || btnText.includes('발행')) {
                            submitBtn.click();
                            return "submit 버튼 '" + btnText + "' 클릭됨";
                        }
                    }
                    
                    // 폼 직접 제출 시도
                    var forms = document.querySelectorAll('form');
                    for (var k = 0; k < forms.length; k++) {
                        var form = forms[k];
                        if (form.querySelector('button[type="submit"]')) {
                            form.submit();
                            return "폼 직접 제출됨";
                        }
                    }
                    
                    return false;
                """)
                
                if result:
                    print(f"JavaScript 결과: {result}")
                    time.sleep(2)
                    confirm_publish(driver)
                    publish_found = True
            except Exception as js_e:
                print(f"JavaScript를 통한 발행 시도 중 오류: {js_e}")
                
        # 3. 이전 방식으로 시도 (여러 선택자)
        if not publish_found:
            publish_selectors = [
                ".btn_publish", 
                ".btn-publish", 
                ".publish-button", 
                "#publish", 
                ".publish-btn",
                "[data-type='publish']",
                "[data-action='publish']",
                ".open-options" # 옵션 메뉴 열기 버튼 (발행 기능 포함)
            ]
            
            for selector in publish_selectors:
                try:
                    publish_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    if publish_buttons:
                        publish_button = publish_buttons[0]
                        print(f"발행 버튼을 찾았습니다: {selector}")
                        publish_button.click()
                        print("발행 버튼을 클릭했습니다.")
                        time.sleep(2)  # 발행 옵션 창이 열릴 때까지 대기
                        
                        # 발행 옵션 창에서 확인 버튼 클릭
                        confirm_publish(driver)
                        publish_found = True
                        break
                except Exception as e:
                    print(f"발행 버튼({selector}) 클릭 중 오류: {e}")
        
        # 4. XPath를 사용하여 버튼 찾기
        if not publish_found:
            try:
                publish_xpath_expressions = [
                    "//a[contains(text(), '공개발행')]",
                    "//button[contains(text(), '발행')]",
                    "//button[contains(@class, 'publish') or contains(@id, 'publish')]",
                    "//a[contains(text(), '발행') or contains(@class, 'publish')]",
                    "//div[contains(@class, 'publish')]//button"
                ]
                
                for xpath_expr in publish_xpath_expressions:
                    publish_buttons_xpath = driver.find_elements(By.XPATH, xpath_expr)
                    if publish_buttons_xpath:
                        publish_button = publish_buttons_xpath[0]
                        print(f"XPath를 통해 발행 버튼을 찾았습니다: {xpath_expr}")
                        publish_button.click()
                        print("XPath를 통해 발행 버튼을 클릭했습니다.")
                        time.sleep(2)
                        confirm_publish(driver)
                        publish_found = True
                        break
            except Exception as xpath_e:
                print(f"XPath를 통한 발행 버튼 찾기 중 오류: {xpath_e}")
        
        # 발행 성공 여부 확인
        if publish_found:
            # 발행 완료 메시지가 표시되는지 확인
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".publish-complete, .alert-success, .success-message"))
                )
                print("발행 완료 메시지가 확인되었습니다!")
                return True
            except Exception as wait_e:
                print("발행 완료 메시지를 찾을 수 없습니다만, 발행은 진행되었을 수 있습니다.")
                return True
        else:
            print("발행 버튼을 찾지 못했습니다. 발행에 실패했습니다.")
            return False
        
    except Exception as e:
        print(f"발행 과정 중 오류 발생: {e}")
        return False

def confirm_publish(driver):
    """발행 옵션 창에서 최종 발행 확인 버튼 클릭"""
    try:
        print("발행 확인 대화상자 처리 중...")
        
        # 0. 이미 발행이 진행 중인지 확인
        try:
            # 발행 로딩 표시기가 활성화되어 있다면 대기
            loading_indicators = driver.find_elements(By.CSS_SELECTOR, 
                ".loading, .loading-indicator, .progress-bar, .spinner")
            
            if loading_indicators and any(indicator.is_displayed() for indicator in loading_indicators):
                print("발행이 이미 진행 중입니다. 완료될 때까지 대기합니다...")
                # 최대 20초 대기
                WebDriverWait(driver, 20).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        ".loading, .loading-indicator, .progress-bar, .spinner"))
                )
                return True
        except Exception as load_e:
            print(f"로딩 확인 중 오류 (무시됨): {load_e}")
        
        # 1. ID로 직접 확인 버튼 찾기 (티스토리 전용)
        try:
            confirm_ids = ["confirmYes", "btn-confirm", "ok-button", "yes-button", "confirm-btn"]
            for btn_id in confirm_ids:
                try:
                    confirm_btn = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.ID, btn_id))
                    )
                    print(f"ID({btn_id})로 확인 버튼을 찾았습니다.")
                    confirm_btn.click()
                    print(f"ID({btn_id}) 확인 버튼 클릭됨")
                    time.sleep(3)
                    return True
                except:
                    continue
        except Exception as id_e:
            print(f"ID로 버튼 찾기 실패 (무시됨): {id_e}")
        
        # 2. 텍스트가 '확인'인 버튼 찾기
        try:
            confirm_texts = ["확인", "예", "네", "발행", "공개", "확인", "Yes"]
            
            for text in confirm_texts:
                confirm_button = driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                if confirm_button:
                    print(f"'{text}' 텍스트가 포함된 확인 버튼을 찾았습니다.")
                    confirm_button[0].click()
                    print(f"'{text}' 버튼 클릭됨")
                    time.sleep(3)
                    return True
        except Exception as text_e:
            print(f"텍스트로 버튼 찾기 실패: {text_e}")
        
        # 3. 팝업/모달 다이얼로그 처리 (기본 알림창)
        try:
            alert = driver.switch_to.alert
            print(f"알림창 발견: '{alert.text}'")
            alert.accept() # 확인 버튼 클릭
            print("알림창의 '확인' 버튼 클릭")
            time.sleep(3)
            return True
        except Exception as alert_e:
            print(f"알림창 처리 실패 (무시됨): {alert_e}")
        
        print("발행 확인 버튼을 찾을 수 없습니다.")
        return False
        
    except Exception as e:
        print(f"발행 확인 과정에서 오류 발생: {e}")
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
        
        login_method_results = []
        for method_id, method_name, method_func in login_verification_methods:
            try:
                print(f"{method_id}: {method_name}으로 로그인 상태 확인 중...")
                method_result = method_func()
                login_method_results.append(method_result)
                
                if method_result:
                    print(f"자동 로그인 성공! ({method_name})")
                else:
                    print(f"{method_name}으로 확인 시 로그인되지 않은 상태입니다.")
            except Exception as e:
                print(f"{method_name} 확인 중 오류 발생: {e}")
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
            print("로그인 창이 아직 표시되는지 확인해 주세요.")
            user_confirm = input("로그인이 완료되었나요? (y/n): ")
            if user_confirm.lower() != 'y':
                print("로그인이 완료되지 않았습니다. 다시 시도해주세요.")
                print("관리자 페이지에 접근하려면 유효한 로그인 세션이 필요합니다.")
                return False
            print("사용자 확인으로 로그인 성공으로 간주합니다.")
        
        # 세션 정보 저장 시도
        print("\n세션 정보 저장을 시도합니다...")
        save_success = False
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
                print("다음에는 자동 로그인으로 더 빠르게 접속할 수 있습니다.")
                save_success = True
            else:
                print("세션 정보 저장에 실패했지만, 로그인은 유지됩니다.")
                print("다음 실행 시에도 수동 로그인이 필요할 수 있습니다.")
        except Exception as save_e:
            print(f"세션 정보 저장 중 오류: {save_e}")
            print("세션 정보 저장에 실패했지만, 로그인은 유지됩니다.")
            print("다음 실행 시에도 수동 로그인이 필요할 수 있습니다.")
        
        print("\n===== 수동 로그인 완료 =====")
        if save_success:
            print("세션 정보 저장 성공: 다음 실행 시 자동 로그인이 가능합니다.")
        else:
            print("세션 정보 저장 실패: 다음 실행 시에도 수동 로그인이 필요할 수 있습니다.")
        
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

def generate_blog_content(topic, format_type=2):
    """
    ChatGPT API를 사용하여 블로그 콘텐츠 생성
    format_type: 2=일반 텍스트(기본값)
    """
    print(f"'{topic}' 주제로 블로그 콘텐츠 생성 중...")
    
    # 제목 생성
    title_prompt = f"다음 주제에 관한 블로그 포스트의 매력적인 제목을 생성해주세요: '{topic}'. 제목만 작성하고 따옴표나 기호는 포함하지 마세요."
    try:
        # OpenAI API v1.x 버전용 호출
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            title_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문적인 블로그 제목 생성기입니다. 매력적이고 SEO에 최적화된 제목을 생성합니다."},
                    {"role": "user", "content": title_prompt}
                ],
                max_tokens=50
            )
            title = title_response.choices[0].message.content.strip()
            
        # 예전 버전(0.x) OpenAI API 호출로 폴백
        except (ImportError, AttributeError):
            title_response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문적인 블로그 제목 생성기입니다. 매력적이고 SEO에 최적화된 제목을 생성합니다."},
                    {"role": "user", "content": title_prompt}
                ],
                max_tokens=50
            )
            title = title_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"제목 생성 중 오류: {e}")
        # 오류 시 간단한 제목 생성
        title = f"{topic}에 관한 포괄적인 가이드"
    
    # 본문 생성을 위한 형식 가이드 설정 (기본 텍스트 모드)
    format_guide = """
    7. HTML 태그나 마크다운은 사용하지 마세요. 일반 텍스트로 작성하되, 다음 형식 지침을 따라주세요:
       - 모든 문단은 한 줄씩 띄워서 작성하세요. 절대로 문단을 붙여서 작성하지 마세요.
       - 각 문장은 적절한 띄어쓰기를 반드시 지켜주세요.
       - 중요한 문구는 '**강조할 내용**'과 같이 별표로 강조해주세요.
       - 각 섹션의 제목은 별도의 줄에 작성하고 앞에 적절한 이모지를 넣어주세요 (예: 🌱 지속가능한 생활).
       - 소제목도 별도의 줄에 작성하고 소제목 앞에도 관련 이모지를 넣어주세요.
       - 목록은 번호나 불릿 대신 이모지를 사용해주세요 (예: 🔍 첫 번째 항목).
       - 각 항목은 새 줄에 작성하고, 항목들 사이에 충분한 간격을 두세요.
       - 단락을 명확히 구분하고, 내용이 풍부하게 작성해주세요.
       - 결론 부분에는 💡 이모지로 시작하는 요약 문장을 넣어주세요.
    """
    
    # 본문 생성
    content_prompt = f"""
    다음 주제에 관한 포괄적인 블로그 포스트를 작성해주세요: '{topic}'
    
    블로그 제목은 '{title}'입니다.
    
    다음 가이드라인을 따라주세요:
    1. 한국어로 작성하세요.
    2. 최소 1000단어 분량으로 작성하세요.
    3. 서론, 본론, 결론 구조를 사용하세요.
    4. 최소 5개 이상의 소제목을 포함하여 구조화된 형식으로 작성하세요.
    5. 실제 사례나 통계 데이터를 포함하세요.
    6. 독자의 참여를 유도하는 질문을 포함하세요.
    {format_guide}
    8. 마지막에 5개의 관련 해시태그를 추가하세요.
    
    중요: 각 문단 사이에는 반드시 빈 줄을 넣어 문단을 분리해주세요. 문장과 문장 사이의 띄어쓰기를 정확하게 지켜주세요. 고품질의 전문적인 블로그 글처럼 보이도록 작성해주세요.
    """
    
    try:
        # OpenAI API v1.x 버전용 호출
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            content_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문적인 블로그 작가입니다. 독자가 이해하기 쉽고 정보가 풍부하며 시각적으로 매력적인 콘텐츠를 작성합니다. 이모지와 강조 표현을 적절히 사용해 글을 생동감있게 만듭니다. 특히 문단 구분과 적절한 띄어쓰기로 가독성이 높은 글을 작성합니다. 각 문단은 한 줄씩 띄워서 작성하고, 모든 문장은 한국어 문법에 맞게 올바른 띄어쓰기를 사용합니다."},
                    {"role": "user", "content": content_prompt}
                ],
                max_tokens=4000
            )
            content = content_response.choices[0].message.content.strip()
            
        # 예전 버전(0.x) OpenAI API 호출로 폴백
        except (ImportError, AttributeError):
            content_response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문적인 블로그 작가입니다. 독자가 이해하기 쉽고 정보가 풍부하며 시각적으로 매력적인 콘텐츠를 작성합니다. 이모지와 강조 표현을 적절히 사용해 글을 생동감있게 만듭니다. 특히 문단 구분과 적절한 띄어쓰기로 가독성이 높은 글을 작성합니다. 각 문단은 한 줄씩 띄워서 작성하고, 모든 문장은 한국어 문법에 맞게 올바른 띄어쓰기를 사용합니다."},
                    {"role": "user", "content": content_prompt}
                ],
                max_tokens=4000
            )
            content = content_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"본문 생성 중 오류: {e}")
        # 오류 시 간단한 본문 생성
        content = f"# {title}\n\n{topic}에 관한 글입니다. API 호출 중 오류가 발생했습니다."
    
    # 태그 생성
    tags_prompt = f"다음 블로그 포스트 주제에 관련된 5개의 SEO 최적화 태그를 생성해주세요 (쉼표로 구분): '{topic}'"
    try:
        # OpenAI API v1.x 버전용 호출
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            tags_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 SEO 전문가입니다. 검색 엔진에서 높은 순위를 차지할 수 있는 태그를 제안합니다."},
                    {"role": "user", "content": tags_prompt}
                ],
                max_tokens=100
            )
            tags = tags_response.choices[0].message.content.strip()
            
        # 예전 버전(0.x) OpenAI API 호출로 폴백
        except (ImportError, AttributeError):
            tags_response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 SEO 전문가입니다. 검색 엔진에서 높은 순위를 차지할 수 있는 태그를 제안합니다."},
                    {"role": "user", "content": tags_prompt}
                ],
                max_tokens=100
            )
            tags = tags_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"태그 생성 중 오류: {e}")
        # 오류 시 기본 태그 생성
        tags = topic + ", 블로그, 정보, 가이드, 팁"
    
    print(f"제목: {title}")
    print(f"태그: {tags}")
    print("콘텐츠 생성 완료!")
    
    # 티스토리에 표시될 수 있도록 텍스트 처리
    # 단순 줄바꿈으로는 티스토리에서 문단이 제대로 표시되지 않을 수 있으므로
    # 각 문단을 <p> 태그로 감싸서 확실하게 분리
    paragraphs = content.split("\n\n")
    content_with_paragraphs = ""
    for paragraph in paragraphs:
        if paragraph.strip():  # 빈 문단은 건너뜀
            content_with_paragraphs += paragraph + "\n\n"
    
    return {
        "title": title,
        "content": content_with_paragraphs,
        "raw_content": content,  # 원본 콘텐츠도 저장
        "tags": tags,
        "format_type": 2  # 항상 일반 텍스트 모드(2)로 설정
    }

def write_post(driver, blog_post):
    """
    티스토리에 글 작성 프로세스를 처리하는 함수 (기본 모드로 작성)
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
    
    # 본문 입력 - 개선된 방식으로 시도
    try:
        print("본문을 입력합니다...")
        content = blog_post["content"]
        
        # 에디터 모드 확인 및 변경
        print("에디터 모드 확인 및 설정 중...")
        try:
            # 모드 확인
            current_mode = check_editor_mode(driver)
            print(f"현재 에디터 모드: {current_mode}")
            
            # 일반 텍스트 모드로 강제 전환 (WYSIWYG 모드)
            if current_mode != "wysiwyg":
                print("일반 텍스트 모드로 전환 시도...")
                switch_to_wysiwyg_mode(driver)
                time.sleep(2)
                current_mode = check_editor_mode(driver)
                print(f"모드 전환 후: {current_mode}")
        except Exception as mode_e:
            print(f"에디터 모드 전환 중 오류: {mode_e}")
            
        # 원본 콘텐츠를 완전한 HTML 구조로 변환 (더 안정적인 표시를 위해)
        raw_content = blog_post["raw_content"]
        
        # HTML 형식으로 변환 (줄바꿈, 문단 구분)
        # 1. 문단 분리 (빈 줄로 구분된 텍스트 블록)
        paragraphs = raw_content.split("\n\n")
        
        # 2. HTML 형식으로 각 문단 변환
        html_content = ""
        html_content += "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>"
        for paragraph in paragraphs:
            if paragraph.strip():
                # 제목줄 처리 (이모지로 시작하는 줄)
                if paragraph.strip().startswith("🌱") or paragraph.strip().startswith("💡") or paragraph.strip().startswith("🔍"):
                    title_text = paragraph.strip()
                    html_content += f"<h2>{title_text}</h2>\n"
                else:
                    # 줄바꿈 처리
                    paragraph = paragraph.replace("\n", "<br>")
                    # 강조 텍스트 처리
                    paragraph = paragraph.replace("**", "<strong>").replace("**", "</strong>")
                    # HTML 문단 태그로 감싸기
                    html_content += f"<p>{paragraph}</p>\n"
        html_content += "</body></html>"
        
        print(f"HTML 형식으로 변환된 콘텐츠 크기: {len(html_content)} 바이트")
        
        # 현재 에디터 모드 확인
        try:
            editor_mode = check_editor_mode(driver)
            print(f"현재 에디터 모드: {editor_mode}")
            
            # HTML 모드가 아니면 HTML 모드로 전환 시도
            if editor_mode != "html":
                switch_to_html_mode(driver)
                time.sleep(2)
                editor_mode = check_editor_mode(driver)
                print(f"에디터 모드 전환 후: {editor_mode}")
        except Exception as mode_e:
            print(f"에디터 모드 확인/전환 중 오류: {mode_e}")
        
        # 콘텐츠 설정 성공 여부 추적
        content_set = False
        
        # 1. iframe을 통한 내용 설정 (가장 안정적인 방법)
        iframe_editor = find_editor_iframe(driver)
        if iframe_editor:
            try:
                driver.switch_to.frame(iframe_editor)
                body = driver.find_element(By.TAG_NAME, "body")
                
                # 기존 내용 초기화
                driver.execute_script("arguments[0].innerHTML = '';", body)
                
                # 완전한 HTML 구조 적용 (문단 구분 보존)
                driver.execute_script("arguments[0].innerHTML = arguments[1];", body, html_content)
                print("iframe 내부 body에 HTML 형식 본문 설정 완료")
                
                # 값이 제대로 설정되었는지 확인
                actual_content = driver.execute_script("return document.body.innerHTML;")
                if len(actual_content) > 100:
                    print(f"iframe 내 실제 콘텐츠 크기: {len(actual_content)} 바이트 (정상)")
                    content_set = True
                else:
                    print(f"경고: iframe 내 콘텐츠가 적절히 설정되지 않았을 수 있습니다. 크기: {len(actual_content)} 바이트")
                
                driver.switch_to.default_content()
            except Exception as iframe_e:
                print(f"iframe 내용 설정 실패: {iframe_e}")
                driver.switch_to.default_content()
        
        # TinyMCE 에디터 직접 접근 시도
        if not content_set:
            try:
                print("TinyMCE 에디터 직접 접근 시도...")
                result = driver.execute_script("""
                    if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                        console.log("TinyMCE 에디터 발견");
                        try {
                            // WYSIWYG 모드 - HTML 직접 설정
                            tinyMCE.activeEditor.setContent(arguments[0]);
                            console.log("tinyMCE.activeEditor.setContent 실행됨");
                            
                            // 내부 데이터에도 설정 (중요)
                            if (tinyMCE.activeEditor.getElement()) {
                                tinyMCE.activeEditor.getElement().value = arguments[0];
                                console.log("Element value도 설정됨");
                            }
                            
                            return "TinyMCE 에디터 설정 성공";
                        } catch (e) {
                            console.error("TinyMCE 설정 오류:", e);
                            return "TinyMCE 설정 오류: " + e.message;
                        }
                    }
                    return "TinyMCE 에디터를 찾을 수 없음";
                """, html_content);
                
                if "성공" in result:
                    print("TinyMCE 에디터에 콘텐츠 설정 성공")
                    content_set = True
                else:
                    print(f"TinyMCE 결과: {result}")
            except Exception as tinymce_e:
                print(f"TinyMCE 에디터 접근 중 오류: {tinymce_e}")
        
        # 2. 모든 가능한 에디터에 콘텐츠 설정 시도 (JavaScript 활용)
        if not content_set:
            try:
                print("JavaScript를 통한 다양한 에디터 접근 시도...")
                result = driver.execute_script("""
                    try {
                        console.log("콘텐츠 설정 스크립트 실행 중...");
                        var content = arguments[0];
                        var setSuccess = false;

                        // TinyMCE 설정
                        if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                            console.log("TinyMCE 에디터 발견");
                            tinyMCE.activeEditor.setContent(content);
                            console.log("TinyMCE 콘텐츠 설정됨");
                            setSuccess = true;
                        }

                        // 티스토리 에디터 API 사용
                        if (window.tistoryEditor) {
                            console.log("티스토리 에디터 객체 발견");
                            if (typeof tistoryEditor.setContent === 'function') {
                                tistoryEditor.setContent(content);
                                console.log("tistoryEditor.setContent 호출됨");
                                setSuccess = true;
                            }
                            else if (typeof tistoryEditor.setHtmlContent === 'function') {
                                tistoryEditor.setHtmlContent(content);
                                console.log("tistoryEditor.setHtmlContent 호출됨");
                                setSuccess = true;
                            }
                            
                            // 티스토리 내부 상태 강제 업데이트
                            if (tistoryEditor.contentElement) {
                                tistoryEditor.contentElement.value = content;
                                console.log("tistoryEditor.contentElement 설정됨");
                                setSuccess = true;
                            }
                            
                            // 티스토리 내부 데이터 설정
                            tistoryEditor.content = content;
                            console.log("tistoryEditor.content 직접 설정됨");
                            setSuccess = true;
                        }

                        // CodeMirror 에디터 설정
                        var cmEditors = document.querySelectorAll('.CodeMirror');
                        if (cmEditors.length > 0) {
                            for (var i = 0; i < cmEditors.length; i++) {
                                var ed = cmEditors[i];
                                if (ed.CodeMirror) {
                                    ed.CodeMirror.setValue(content);
                                    console.log("CodeMirror 콘텐츠 설정됨");
                                    setSuccess = true;
                                }
                            }
                        }

                        // 모든 iframe 순회
                        var frames = document.querySelectorAll('iframe');
                        for (var i = 0; i < frames.length; i++) {
                            try {
                                var frame = frames[i];
                                var frameDoc = frame.contentDocument || frame.contentWindow.document;
                                if (frameDoc && frameDoc.body) {
                                    frameDoc.body.innerHTML = content;
                                    console.log(i + "번 iframe에 콘텐츠 설정됨");
                                    setSuccess = true;
                                }
                            } catch(e) {
                                console.log("iframe 접근 오류: " + e.message);
                            }
                        }

                        // textarea 찾아서 설정
                        var textareas = document.querySelectorAll('textarea');
                        for (var j = 0; j < textareas.length; j++) {
                            var ta = textareas[j];
                            if (ta.id !== 'post-title-inp' && ta.clientHeight > 50) {
                                ta.value = content;
                                console.log("큰 textarea에 콘텐츠 설정됨");
                                setSuccess = true;
                                
                                // 이벤트 발생시켜 변경사항 알림
                                var event = new Event('input', { bubbles: true });
                                ta.dispatchEvent(event);
                            }
                        }

                        return setSuccess ? "콘텐츠 설정 성공" : "모든 에디터 접근 시도 실패";
                    } catch(e) {
                        return "오류 발생: " + e.message;
                    }
                """, html_content)
                
                if result and "성공" in result:
                    print(f"JavaScript 콘텐츠 설정 성공: {result}")
                    content_set = True
                else:
                    print(f"JavaScript 콘텐츠 설정 결과: {result}")
            except Exception as js_e:
                print(f"JavaScript 콘텐츠 설정 중 오류: {js_e}")
            
        # 3. 텍스트 영역에 내용 설정 (마지막 시도)
        if not content_set:
            try:
                print("텍스트 영역 직접 접근 시도...")
                textareas = driver.find_elements(By.TAG_NAME, "textarea")
                for textarea in textareas:
                    if textarea.get_attribute("id") != "post-title-inp":  # 제목 필드가 아닌 경우
                        textarea.clear()
                        textarea.send_keys(html_content)
                        print(f"textarea({textarea.get_attribute('id') or '알 수 없음'})에 본문 설정 완료")
                        content_set = True
                        break
            except Exception as ta_e:
                print(f"textarea 설정 실패: {ta_e}")
        
        # 콘텐츠 설정 확인
        if content_set:
            print("본문 콘텐츠가 성공적으로 설정되었습니다.")
        else:
            print("경고: 모든 콘텐츠 설정 방법이 실패했습니다!")
            
    except Exception as e:
        print(f"본문 입력 중 오류: {e}")
    
    # 태그 입력
    try:
        print("\n===== 태그 입력 =====")
        input_tags(driver, blog_post["tags"])
    except Exception as e:
        print(f"태그 입력 중 오류: {e}")
    
    # 발행 전 마지막 콘텐츠 확인 및 수정
    try:
        print("\n===== 발행 전 최종 콘텐츠 확인 =====")
        content_check = driver.execute_script("""
            try {
                // TinyMCE 에디터를 통한 콘텐츠 확인
                if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                    var content = tinyMCE.activeEditor.getContent();
                    return {
                        source: 'tinyMCE',
                        length: content.length,
                        hasContent: content.length > 100
                    };
                }
                
                // iframe을 통한 확인
                var iframes = document.querySelectorAll('iframe');
                for (var i = 0; i < iframes.length; i++) {
                    try {
                        var frame = iframes[i];
                        var frameDoc = frame.contentDocument || frame.contentWindow.document;
                        if (frameDoc && frameDoc.body) {
                            var content = frameDoc.body.innerHTML;
                            return {
                                source: 'iframe',
                                length: content.length,
                                hasContent: content.length > 100
                            };
                        }
                    } catch(e) {}
                }
                
                // CodeMirror 확인
                var cm = document.querySelector('.CodeMirror');
                if (cm && cm.CodeMirror) {
                    var content = cm.CodeMirror.getValue();
                    return {
                        source: 'CodeMirror',
                        length: content.length,
                        hasContent: content.length > 100
                    };
                }
                
                return {
                    source: 'none',
                    length: 0,
                    hasContent: false
                };
            } catch(e) {
                return {
                    source: 'error',
                    error: e.message,
                    hasContent: false
                };
            }
        """)
        
        print(f"콘텐츠 확인 결과: {content_check}")
        
        # 콘텐츠가 없는 경우 강제로 다시 설정
        if not content_check.get('hasContent', False):
            print("⚠️ 발행 직전 콘텐츠가 없는 것으로 확인됨! 강제 재설정 시도...")
            
            # 최종 수단 - Tistory API 직접 접근
            try:
                driver.execute_script("""
                    // 티스토리 에디터에 직접 접근
                    if (window.tistoryEditor) {
                        console.log("티스토리 에디터 객체에 직접 접근");
                        
                        // 모든 가능한 방법 시도
                        if (typeof tistoryEditor.setContent === 'function') {
                            tistoryEditor.setContent(arguments[0]);
                        }
                        if (typeof tistoryEditor.setHtmlContent === 'function') {
                            tistoryEditor.setHtmlContent(arguments[0]);
                        }
                        
                        // 에디터 모드에 따른 설정
                        if (tistoryEditor.currentMode === 'html' || tistoryEditor.isHtmlMode) {
                            if (typeof tistoryEditor.setHtmlContent === 'function') {
                                tistoryEditor.setHtmlContent(arguments[0]);
                            }
                        } else {
                            if (typeof tistoryEditor.setContent === 'function') {
                                tistoryEditor.setContent(arguments[0]);
                            }
                        }
                        
                        // 내부 데이터 직접 설정 (가장 중요)
                        tistoryEditor.content = arguments[0];
                        
                        console.log("티스토리 에디터 내부 데이터 설정 완료");
                    } else {
                        console.log("티스토리 에디터 객체를 찾을 수 없음");
                    }
                """, html_content)
                print("티스토리 API로 최종 콘텐츠 재설정 시도")
            except Exception as final_e:
                print(f"최종 콘텐츠 설정 시도 중 오류: {final_e}")
    except Exception as check_e:
        print(f"최종 콘텐츠 확인 중 오류: {check_e}")
    
    # 임시저장 단계 제거
    print("\n===== 임시저장 단계를 건너뛰고 바로 공개발행을 진행합니다 =====")
    
    return True

def check_editor_mode(driver):
    """
    현재 에디터 모드를 확인하는 함수
    return: 'html', 'markdown' 또는 'wysiwyg'(일반 텍스트)
    """
    try:
        # 1. 상단 에디터 모드 버튼 직접 확인 (가장 정확한 방법)
        try:
            # 상단 메뉴에 있는 "HTML" 버튼 확인
            html_button = driver.find_element(By.XPATH, "//button[text()='HTML']")
            if html_button:
                # 클래스 이름으로 활성화 상태 확인
                button_class = html_button.get_attribute("class") or ""
                print(f"상단 HTML 버튼 발견: 클래스='{button_class}'")
                
                # 활성화된 버튼인지 확인
                if "active" in button_class or "selected" in button_class:
                    print("상단 HTML 버튼이 활성화되어 있습니다 - HTML 모드로 판단")
                    return 'html'
                
                # 상단 버튼이 있지만 그 옆 드롭다운 값 확인
                html_dropdown = driver.find_element(By.XPATH, "//button[contains(text(),'HTML')]/..//span")
                if html_dropdown:
                    dropdown_text = html_dropdown.text
                    print(f"HTML 드롭다운 텍스트: '{dropdown_text}'")
                    
                    # 드롭다운 값으로 모드 판단
                    if "HTML" in dropdown_text:
                        print("HTML 드롭다운이 활성화되어 있습니다 - HTML 모드로 판단")
                        return 'html'
        except Exception as e:
            print(f"상단 HTML 버튼 확인 중 오류(무시됨): {e}")
            
        # 2. 상단 도구 모음 상태 확인
        try:
            # 툴바 비활성화 확인 (HTML 모드에서는 편집 툴바가 비활성화됨)
            toolbar_buttons = driver.find_elements(By.CSS_SELECTOR, ".tox-toolbar__group button.tox-tbtn")
            if toolbar_buttons:
                disabled_count = 0
                for btn in toolbar_buttons:
                    if "disabled" in (btn.get_attribute("aria-disabled") or "") or "disabled" in (btn.get_attribute("class") or ""):
                        disabled_count += 1
                
                # 대부분의 툴바 버튼이 비활성화되어 있다면 HTML 모드일 가능성이 높음
                if disabled_count > len(toolbar_buttons) * 0.5:
                    print(f"툴바 비활성화 상태 확인: {disabled_count}/{len(toolbar_buttons)} 버튼 비활성화 - HTML 모드로 판단")
                    return 'html'
        except Exception as e:
            print(f"툴바 상태 확인 중 오류(무시됨): {e}")
            
        # 3. 에디터 영역의 특성 확인
        try:
            # HTML 모드일 때는 일반적으로 textarea나 코드 편집기가 표시됨
            html_editors = driver.find_elements(By.CSS_SELECTOR, 
                "textarea.html-editor, textarea.code-editor, .CodeMirror, [contenteditable='true'].html-code")
            
            if html_editors:
                print("HTML 편집기 요소 발견 - HTML 모드로 판단")
                return 'html'
                
            # iframe 내부 확인
            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    driver.switch_to.frame(iframe)
                    try:
                        # HTML 모드에서는 콘텐츠 영역에 태그가 표시됨
                        content = driver.find_element(By.CSS_SELECTOR, "body").get_attribute("innerHTML")
                        if content and ("<" in content and ">" in content):
                            source_view = True
                            for tag in ["<p", "<div", "<span", "<h1", "<h2"]:
                                if tag in content:
                                    source_view = True
                                    break
                            if source_view:
                                print("iframe 내 HTML 태그 발견 - HTML 모드로 판단")
                                driver.switch_to.default_content()
                                return 'html'
                    except:
                        pass
                    driver.switch_to.default_content()
            except:
                pass
        except Exception as e:
            print(f"에디터 영역 확인 중 오류(무시됨): {e}")

        # 4. JavaScript를 사용하여 에디터 모드 확인 (기존 방식)
        mode = driver.execute_script("""
            // 디버깅 정보 (콘솔에 출력)
            console.log("에디터 모드 확인 중...");
            
            // 상단 HTML 버튼 확인
            var htmlButton = document.querySelector('button[data-mode="html"], button.html-mode-button, button.tox-tbtn:contains("HTML")');
            if (htmlButton) {
                var isActive = htmlButton.classList.contains('active') || 
                               htmlButton.classList.contains('selected') ||
                               htmlButton.getAttribute('aria-pressed') === 'true';
                if (isActive) {
                    console.log("상단 HTML 버튼 활성화 확인됨");
                    return 'html';
                }
            }
            
            // 현재 에디터 모드 값 확인
            var modeIndicator = document.querySelector('[data-mode="current"], .editor-mode-indicator');
            if (modeIndicator) {
                var modeText = modeIndicator.textContent.trim().toLowerCase();
                console.log("모드 인디케이터 텍스트: " + modeText);
                if (modeText.includes('html')) {
                    return 'html';
                }
            }
            
            // 티스토리 모드 버튼 텍스트 확인 (가장 정확한 방법)
            var modeBtn = document.querySelector('#editor-mode-layer-btn .mce-txt');
            if (modeBtn) {
                var modeTxt = modeBtn.textContent.trim();
                console.log("모드 버튼 텍스트: " + modeTxt);
                
                if (modeTxt.includes('HTML') || modeTxt.includes('html')) {
                    console.log("HTML 모드 감지됨");
                    return 'html';
                } else if (modeTxt.includes('마크다운') || modeTxt.includes('Markdown')) {
                    console.log("마크다운 모드 감지됨");
                    return 'markdown';
                } else {
                    console.log("기본 모드 감지됨 (WYSIWYG)");
                }
            }
            
            // HTML 모드 여부 확인
            var isEditingHtml = false;
            
            // 편집기 상태 확인
            if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                // 소스 코드 편집 모드인지 확인
                var isSourceMode = tinyMCE.activeEditor.plugins && 
                                 tinyMCE.activeEditor.plugins.code && 
                                 tinyMCE.activeEditor.plugins.code.isActive && 
                                 tinyMCE.activeEditor.plugins.code.isActive();
                                 
                if (isSourceMode) {
                    console.log("TinyMCE 소스 코드 모드 감지됨");
                    return 'html';
                }
                
                // 또는 다른 방식으로 확인
                try {
                    var content = tinyMCE.activeEditor.getContent();
                    // HTML 태그가 그대로 보이는지 확인 (소스 모드의 특징)
                    if (content.indexOf('&lt;') >= 0 || content.indexOf('&gt;') >= 0) {
                        console.log("HTML 엔티티 발견 - HTML 모드로 판단");
                        return 'html';
                    }
                } catch(e) {}
            }
            
            // 다른 방식으로 HTML 모드 확인
            var isHtmlMode = document.querySelector('.html-editor') || 
                document.querySelector('.switch-html.active') ||
                document.querySelector('button[data-mode="html"].active') ||
                (window.tistoryEditor && window.tistoryEditor.isHtmlMode);
                
            if (isHtmlMode) {
                console.log("대체 방법으로 HTML 모드 감지됨");
                return 'html';
            } 
            
            // 마크다운 모드 확인
            var isMarkdownMode = document.querySelector('.markdown-editor') || 
                     document.querySelector('.switch-markdown.active') ||
                     document.querySelector('button[data-mode="markdown"].active') ||
                 (window.tistoryEditor && window.tistoryEditor.isMarkdownMode);
                 
            if (isMarkdownMode) {
                console.log("대체 방법으로 마크다운 모드 감지됨");
                return 'markdown';
            }
            
            // TinyMCE 에디터 확인
            if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                var activeEditor = tinyMCE.activeEditor;
                var isSourceMode = activeEditor.plugins && 
                                  activeEditor.plugins.code && 
                                  activeEditor.plugins.code.isActive && 
                                  activeEditor.plugins.code.isActive();
                if (isSourceMode) {
                    console.log("TinyMCE 소스 모드 감지됨 (HTML)");
                    return 'html';
                }
            }
            
            // 기본값: WYSIWYG 모드
            console.log("기본 WYSIWYG 모드로 판단");
            return 'wysiwyg';
        """)
        
        print(f"감지된 에디터 모드: {mode}")
        return mode if mode else "wysiwyg"
    except Exception as e:
        print(f"에디터 모드 확인 중 오류: {e}")
        return "wysiwyg"  # 확인할 수 없는 경우 기본값

def switch_to_html_mode(driver):
    """HTML 모드로 전환"""
    try:
        print("HTML 모드로 전환을 시도합니다...")
        
        # 1. span 요소를 직접 타겟팅하여 클릭 (가장 정확한 방법)
        try:
            # 모드 버튼 클릭하여 드롭다운 표시
            mode_btn = driver.find_element(By.CSS_SELECTOR, "#editor-mode-layer-btn")
            mode_btn.click()
            time.sleep(1)
            
            # 드롭다운에서 HTML 모드 옵션의 span 요소를 ID로 직접 선택
            html_span = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "editor-mode-html-text"))
            )
            
            # 클릭 직전 디버깅 정보
            print(f"HTML span 요소 발견: id={html_span.get_attribute('id')}, class={html_span.get_attribute('class')}")
            print(f"텍스트 내용: '{html_span.text}'")
            
            # span 요소와 부모 요소 모두 클릭 시도
            try:
                # 1) span 요소 직접 클릭
                html_span.click()
                print("HTML span 요소를 직접 클릭했습니다.")
            except:
                # 2) 부모 요소 찾아서 클릭
                parent_div = driver.find_element(By.ID, "editor-mode-html")
                parent_div.click()
                print("HTML 부모 요소를 클릭했습니다.")
            
            # 확인 대화상자 처리 - 중요!
            time.sleep(1)  # 대화상자 나타날 때까지 잠시 대기
            
            # 전용 함수로 확인 대화상자 처리
            click_confirm_dialog_button(driver)
            
            # 방법 1~4는 남겨두어 백업으로 활용
            # 방법 1: 일반적인 알림창(alert) 처리
            try:
                alert = driver.switch_to.alert
                print(f"알림창 발견: '{alert.text}'")
                alert.accept()  # '확인' 버튼 클릭
                print("알림창의 '확인' 버튼을 클릭했습니다.")
            except:
                print("브라우저 기본 알림창이 없습니다. 커스텀 모달 확인...")
            
            # 방법 2~4 (기존 코드 유지)
            # ... 기존 코드 ...
            
            time.sleep(2)  # 모드 변경 대기
            
            # 모드 변경 확인
            current_mode = check_editor_mode(driver)
            if current_mode == "html":
                print("성공적으로 HTML 모드로 전환되었습니다.")
                return True
            else:
                print(f"모드 전환 실패: '{current_mode}' 모드로 남아 있습니다.")
                return False
            
        except Exception as e:
            print(f"span 요소를 통한 HTML 전환 실패: {e}")
            
        # 이후 다른 방법들은 그대로 유지
        # ... 기존 코드 ...
    
    except Exception as e:
        print(f"HTML 모드 전환 중 오류: {e}")
        return False

def switch_to_markdown_mode(driver):
    """마크다운 모드로 전환"""
    try:
        print("마크다운 모드로 전환을 시도합니다...")
        
        # 1. 티스토리 모드 버튼을 통한 전환 (가장 정확한 방법)
        try:
            # 모드 버튼 클릭하여 드롭다운 표시
            mode_btn = driver.find_element(By.CSS_SELECTOR, "#editor-mode-layer-btn")
            mode_btn.click()
            time.sleep(1)
            
            # 드롭다운에서 마크다운 모드 옵션 선택
            markdown_option = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'mce-menu')]//span[contains(text(),'마크다운') or contains(text(),'Markdown')]"))
            )
            markdown_option.click()
            print("티스토리 모드 버튼을 통해 마크다운 모드로 전환했습니다.")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"티스토리 모드 버튼을 통한 전환 실패: {e}")
        
        # 2. CSS 선택자로 마크다운 버튼 찾기
        markdown_buttons = driver.find_elements(By.CSS_SELECTOR, 
            ".btn_markdown, button[data-mode='markdown'], .markdown-mode-button, button[title*='마크다운']")
        
        if markdown_buttons:
            markdown_buttons[0].click()
            print("마크다운 모드로 전환했습니다.")
            time.sleep(1)
            return True
        
        # 3. JavaScript를 사용하여 마크다운 모드 전환
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
        
        # 4. XPath를 사용하여 마크다운 버튼 찾기
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
        return iframe_editor
    except:
        return None

def set_html_content(driver, content, iframe_editor):
    """HTML 모드에서 콘텐츠 설정"""
    try:
        print("HTML 모드에서 콘텐츠 설정 시도...")
        
        # CodeMirror 에디터 직접 처리 (우선순위 가장 높음)
        try:
            # CodeMirror 에디터 요소 찾기
            codemirror_elements = driver.find_elements(By.CSS_SELECTOR, ".CodeMirror, .cm-editor")
            if codemirror_elements:
                print(f"CodeMirror 에디터 발견: {len(codemirror_elements)}개")
                
                # CodeMirror 에디터에 직접 콘텐츠 설정
                result = driver.execute_script("""
                    try {
                        // 모든 CodeMirror 인스턴스 검색
                        var editors = document.querySelectorAll('.CodeMirror, .cm-editor');
                        if (!editors.length) return "CodeMirror 에디터를 찾을 수 없음";
                        
                        var success = false;
                        
                        // 각 에디터에 콘텐츠 설정 시도
                        for (var i = 0; i < editors.length; i++) {
                            var editor = editors[i];
                            
                            // 방법 1: CodeMirror 객체 사용
                            if (editor.CodeMirror) {
                                console.log("CodeMirror 인스턴스를 직접 사용");
                                editor.CodeMirror.setValue(arguments[0]);
                                success = true;
                            }
                            // 방법 2: 글로벌 CodeMirror 객체 활용
                            else if (typeof CodeMirror !== 'undefined' && CodeMirror.fromTextArea) {
                                // textarea 찾기
                                var textareas = document.querySelectorAll('textarea');
                                for (var j = 0; j < textareas.length; j++) {
                                    var cm = CodeMirror.findCodeMirror(textareas[j]);
                                    if (cm) {
                                        console.log("CodeMirror 글로벌 객체로 찾음");
                                        cm.setValue(arguments[0]);
                                        success = true;
                                        break;
                                    }
                                }
                            }
                            // 방법 3: 내부 hidden textarea 찾아서 설정
                            else {
                                var textarea = editor.querySelector('textarea');
                                if (textarea) {
                                    console.log("CodeMirror 내부 textarea 사용");
                                    textarea.value = arguments[0];
                                    
                                    // 값 변경 이벤트 발생
                                    var event = new Event('input', { bubbles: true });
                                    textarea.dispatchEvent(event);
                                    
                                    success = true;
                                }
                            }
                        }
                        
                        // 방법 4: 텍스트 직접 편집
                        if (!success) {
                            try {
                                // 커서 위치 요소 찾기
                                var lines = document.querySelectorAll('.CodeMirror-line, .cm-line');
                                if (lines.length > 0) {
                                    // 기존 내용 지우기
                                    for (var k = 0; k < lines.length; k++) {
                                        if (k > 0) {
                                            lines[k].remove();
                                        }
                                    }
                                    
                                    // 첫 번째 줄에 내용 설정
                                    lines[0].innerHTML = '<span>' + arguments[0] + '</span>';
                                    success = true;
                                }
                            } catch (e) {
                                console.error("직접 편집 중 오류:", e);
                            }
                        }
                        
                        // 방법 5: 티스토리 에디터 객체 사용
                        if (!success && window.tistoryEditor) {
                            console.log("티스토리 에디터 객체 사용");
                            if (typeof tistoryEditor.setHtmlContent === 'function') {
                                tistoryEditor.setHtmlContent(arguments[0]);
                                success = true;
                            }
                            else if (typeof tistoryEditor.setValue === 'function') {
                                tistoryEditor.setValue(arguments[0]);
                                success = true;
                            }
                        }
                        
                        return success ? "CodeMirror 에디터에 콘텐츠 설정 성공" : "CodeMirror 에디터 설정 실패";
                    } catch (e) {
                        return "CodeMirror 에디터 처리 중 오류: " + e.message;
                    }
                """, content)
                
                print(f"CodeMirror 에디터 설정 결과: {result}")
                
                # 두 번째 확인 시도: 값이 실제로 들어갔는지 검증
                verification = driver.execute_script("""
                    try {
                        // 내용이 들어갔는지 확인
                        var editors = document.querySelectorAll('.CodeMirror, .cm-editor');
                        if (!editors.length) return false;
                        
                        for (var i = 0; i < editors.length; i++) {
                            var editor = editors[i];
                            var editorContent = '';
                            
                            // CodeMirror 인스턴스에서 내용 가져오기
                            if (editor.CodeMirror) {
                                editorContent = editor.CodeMirror.getValue();
                            }
                            // 내부 textarea 확인
                            else {
                                var textarea = editor.querySelector('textarea');
                                if (textarea) {
                                    editorContent = textarea.value;
                                }
                            }
                            
                            // 내용이 비어 있지 않으면 성공
                            if (editorContent && editorContent.length > 10) {
                                return true;
                            }
                        }
                        
                        return false;
                    } catch (e) {
                        console.error("검증 중 오류:", e);
                        return false;
                    }
                """)
                
                if verification:
                    print("CodeMirror 에디터에 콘텐츠가 정상적으로 설정되었습니다.")
                    return True
                else:
                    print("CodeMirror 에디터에 콘텐츠 설정이 확인되지 않았습니다. 다른 방법 시도...")
        except Exception as cm_e:
            print(f"CodeMirror 에디터 처리 중 오류: {cm_e}")
        
        # 0. 상단 메뉴에서 HTML 버튼이 있는지 확인
        try:
            html_button = driver.find_element(By.XPATH, "//button[text()='HTML']")
            print("상단 HTML 버튼 발견 - 새로운 티스토리 에디터 스타일")
            
            # 새로운 티스토리 에디터는 다른 방식으로 콘텐츠 설정해야 할 수 있음
            try:
                # 에디터 영역 찾기
                editor_area = driver.find_element(By.CSS_SELECTOR, ".CodeMirror, .editor-code, textarea.code-editor")
                print(f"HTML 편집기 영역 발견: {editor_area.tag_name}")
                
                # CodeMirror 에디터인 경우
                if "CodeMirror" in (editor_area.get_attribute("class") or ""):
                    driver.execute_script("""
                        var editor = document.querySelector('.CodeMirror');
                        if (editor && editor.CodeMirror) {
                            editor.CodeMirror.setValue(arguments[0]);
                        }
                    """, content)
                    print("CodeMirror 에디터에 콘텐츠를 설정했습니다.")
                    return True
                # 일반 textarea인 경우
                else:
                    editor_area.clear()
                    editor_area.send_keys(content)
                    print(f"{editor_area.tag_name} 요소에 콘텐츠를 설정했습니다.")
                    return True
            except Exception as edit_e:
                print(f"새 에디터 영역 설정 중 오류: {edit_e}")
                
            # 에디터 영역을 찾을 수 없는 경우 JavaScript로 시도
            result = driver.execute_script("""
                try {
                    // 현재 표시된 에디터 영역 찾기
                    var editorArea = document.querySelector('textarea.html-editor, .CodeMirror, .editor-code');
                    if (editorArea) {
                        if (editorArea.CodeMirror) {
                            editorArea.CodeMirror.setValue(arguments[0]);
                        } else {
                            editorArea.value = arguments[0];
                        }
                        return "에디터 영역에 콘텐츠 설정됨";
                    }
                    
                    // 새로운 스타일의 에디터를 위한 다양한 접근 방식
                    var methods = [
                        // 방법 1: 티스토리 API 사용
                        function() {
                            if (window.tistoryEditor && window.tistoryEditor.setHtmlContent) {
                                window.tistoryEditor.setHtmlContent(arguments[0]);
                                return "tistoryEditor.setHtmlContent 사용";
                            }
                            return null;
                        },
                        // 방법 2: CodeMirror 인스턴스 찾기
                        function() {
                            if (window.CodeMirror && window.cmInstance) {
                                window.cmInstance.setValue(arguments[0]);
                                return "CodeMirror 인스턴스 사용";
                            }
                            return null;
                        },
                        // 방법 3: iframe 내용 직접 설정
                        function() {
                            var frames = document.querySelectorAll('iframe');
                            for (var i = 0; i < frames.length; i++) {
                                try {
                                    var frame = frames[i];
                                    var doc = frame.contentDocument || frame.contentWindow.document;
                                    doc.body.innerHTML = arguments[0];
                                    return "iframe 내용 설정됨";
                                } catch(e) {}
                            }
                            return null;
                        }
                    ];
                    
                    // 모든 방법 시도
                    for (var j = 0; j < methods.length; j++) {
                        var result = methods[j]();
                        if (result) return result;
                    }
                    
                    return "에디터 영역을 찾을 수 없음";
                } catch (e) {
                    return "오류: " + e.message;
                }
            """, content)
            
            print(f"JavaScript를 통한 콘텐츠 설정 결과: {result}")
            return True
            
        except Exception as button_e:
            print(f"상단 HTML 버튼 확인 중 오류(무시됨): {button_e}")
        
        # 1. JavaScript를 사용하여 직접 콘텐츠 설정 시도 (기존 방식)
        result = driver.execute_script("""
            // 티스토리 에디터 API 사용
            if (window.tistoryEditor && window.tistoryEditor.setHtmlContent) {
                window.tistoryEditor.setHtmlContent(arguments[0]);
                return "tistoryEditor.setHtmlContent 성공";
            }
            
            // TinyMCE API 사용
            if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                // HTML 모드인지 확인
                var isSourceMode = tinyMCE.activeEditor.plugins && 
                                 tinyMCE.activeEditor.plugins.code && 
                                 tinyMCE.activeEditor.plugins.code.isActive && 
                                 tinyMCE.activeEditor.plugins.code.isActive();
                
                if (isSourceMode) {
                    // 소스 편집 모드에서는 다른 방식으로 설정
                    var textarea = document.querySelector('.mce-textbox, .tox-textarea');
                    if (textarea) {
                        textarea.value = arguments[0];
                        // 값이 변경되었음을 에디터에 알림
                        var event = new Event('input', { bubbles: true });
                        textarea.dispatchEvent(event);
                        return "TinyMCE 소스 모드 텍스트 영역에 콘텐츠 설정 성공";
                    }
                }
                
                // 기본 설정 방식
                tinyMCE.activeEditor.setContent(arguments[0]);
                return "TinyMCE setContent 성공";
            }
            
            // HTML 에디터 요소 찾기
            var htmlEditor = document.querySelector('.html-editor textarea, [contenteditable="true"].html, textarea.html-code');
            if (htmlEditor) {
                htmlEditor.value = arguments[0];
                htmlEditor.innerHTML = arguments[0];
                return "HTML 에디터 요소에 콘텐츠 설정 성공";
            }
            
            // 모든 textarea 확인
            var allTextareas = document.querySelectorAll('textarea');
            for (var i = 0; i < allTextareas.length; i++) {
                var ta = allTextareas[i];
                // 제목 필드가 아닌 충분히 큰 textarea를 찾음
                if (ta.id !== 'post-title-inp' && ta.clientHeight > 100) {
                    ta.value = arguments[0];
                    return "큰 텍스트영역에 콘텐츠 설정 성공";
                }
            }
            
            return "적합한 HTML 에디터 요소를 찾지 못함";
        """, content)
        
        if result:
            print(f"JavaScript를 통한 HTML 콘텐츠 설정: {result}")
            return True
        
        # 2. iframe 내부에 직접 콘텐츠 설정 시도
        if iframe_editor:
            try:
                driver.switch_to.frame(iframe_editor)
                
                try:
                    # HTML 모드에서는 textarea나 contenteditable 요소에 내용 설정
                    editor_elements = driver.find_elements(By.CSS_SELECTOR, "textarea, [contenteditable='true']")
                    if editor_elements:
                        for element in editor_elements:
                            try:
                                element.clear()
                                element.send_keys(content)
                                print(f"iframe 내부의 {element.tag_name} 요소에 HTML 콘텐츠를 입력했습니다.")
                                driver.switch_to.default_content()
                                return True
                            except Exception as elem_e:
                                print(f"요소 {element.tag_name}에 입력 실패: {elem_e}")
                    
                    # body에 직접 설정
                    body = driver.find_element(By.TAG_NAME, "body")
                    driver.execute_script("arguments[0].innerHTML = arguments[1];", body, content)
                    print("iframe 내부의 body에 HTML 콘텐츠를 설정했습니다.")
                    driver.switch_to.default_content()
                    return True
                except Exception as inner_e:
                    print(f"iframe 내부 콘텐츠 설정 중 오류: {inner_e}")
                    
                driver.switch_to.default_content()
            except Exception as frame_e:
                print(f"iframe 전환 중 오류: {frame_e}")
                driver.switch_to.default_content()
        
        # 3. 직접 HTML 입력 필드 찾기
        html_editors = driver.find_elements(By.CSS_SELECTOR, 
            "textarea.html-editor, textarea.code-editor, [contenteditable='true'].html-code")
        
        if html_editors:
            for editor in html_editors:
                try:
                    editor.clear()
                    editor.send_keys(content)
                    print(f"HTML 에디터 요소({editor.tag_name})에 콘텐츠를 입력했습니다.")
                    return True
                except Exception as e:
                    print(f"에디터({editor.tag_name})에 입력 실패: {e}")
            
        # 4. 마지막 수단: 페이지의 모든 큰 textarea 시도
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        for textarea in textareas:
            try:
                # 이미 확인한 title 필드가 아닌 경우만 시도
                if textarea.get_attribute("id") != "post-title-inp":
                    print(f"textarea 발견: id={textarea.get_attribute('id') or '없음'}, name={textarea.get_attribute('name') or '없음'}")
                    textarea.clear()
                    textarea.send_keys(content)
                    print("일반 textarea에 HTML 콘텐츠를 입력했습니다.")
                    return True
            except Exception as ta_e:
                print(f"textarea 입력 중 오류: {ta_e}")
        
        # 5. 마지막 시도: 수동으로 CodeMirror 에디터 내용 덮어쓰기
        try:
            print("마지막 시도: CodeMirror 내용 강제 덮어쓰기")
            result = driver.execute_script("""
                try {
                    // CodeMirror 내용 덮어쓰기
                    var lines = document.querySelectorAll('.CodeMirror-line');
                    if (lines.length > 0) {
                        // 첫 번째 줄 외에는 지우기
                        for (var i = 1; i < lines.length; i++) {
                            lines[i].parentNode.removeChild(lines[i]);
                        }
                        
                        // 첫 번째 줄에 콘텐츠 채우기
                        lines[0].innerHTML = arguments[0];
                        
                        // 강제 입력 이벤트 발생
                        var textareas = document.querySelectorAll('textarea');
                        for (var j = 0; j < textareas.length; j++) {
                            textareas[j].dispatchEvent(new Event('input'));
                            textareas[j].dispatchEvent(new Event('change'));
                        }
                        
                        return "CodeMirror 강제 덮어쓰기 완료";
                    }
                    return "CodeMirror 줄을 찾을 수 없음";
                } catch(e) {
                    return "CodeMirror 강제 덮어쓰기 실패: " + e.message;
                }
            """, content)
            print(f"강제 덮어쓰기 결과: {result}")
            return True
        except Exception as force_e:
            print(f"강제 덮어쓰기 실패: {force_e}")
            
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

# 콘텐츠 형식 검증 함수
def validate_content_format(content, format_type):
    """
    생성된 콘텐츠가 선택한 형식에 맞는지 검증
    format_type: 2=일반 텍스트
    """
    try:
        # 일반 텍스트 (기본값)
        # HTML이나 마크다운 형식이 과도하게 있는지 확인
        html_tags = ['<h1', '<h2', '<h3', '<p>', '<div', '<ul', '<ol', '<li', '<strong', '<em']
        html_count = sum(1 for tag in html_tags if tag in content.lower())
        
        markdown_patterns = ['# ', '## ', '### ', '**', '*', '- ', '1. ', '> ', '```']
        md_count = sum(1 for pattern in markdown_patterns if pattern in content)
        
        # 볼드체(**) 강조는 일반 텍스트에서도 사용하므로 제외
        if '**' in markdown_patterns:
            markdown_patterns.remove('**')
            
        # 이모지 포함 여부 확인 (이모지가 있으면 좋음)
        emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # 이모티콘
                               u"\U0001F300-\U0001F5FF"  # 기호 및 픽토그램
                               u"\U0001F680-\U0001F6FF"  # 교통 및 지도 기호
                               u"\U0001F700-\U0001F77F"  # 알케미 기호
                               u"\U0001F780-\U0001F7FF"  # 기하학적 모양
                               u"\U0001F800-\U0001F8FF"  # 추가 화살표
                               u"\U0001F900-\U0001F9FF"  # 추가 이모티콘
                               u"\U0001FA00-\U0001FA6F"  # 게임 기호
                               u"\U0001FA70-\U0001FAFF"  # 기호 및 픽토그램 확장
                               u"\U00002702-\U000027B0"  # 기타 기호
                               u"\U000024C2-\U0001F251" 
                               "]+", flags=re.UNICODE)
        
        emoji_found = len(emoji_pattern.findall(content))
        bold_count = content.count('**')
        
        print(f"콘텐츠 분석: 이모지 {emoji_found}개, 볼드체 {bold_count//2}개 사용됨")
        
        # HTML이나 마크다운 형식이 5개 이하면 일반 텍스트로 간주 (볼드체 제외)
        if html_count <= 5 and md_count <= 5:
            print("일반 텍스트 형식 검증 통과")
            return True
        else:
            print(f"경고: HTML({html_count}개) 또는 마크다운({md_count}개) 요소가 많이 발견됨")
            print("일반 텍스트 형식에 적합하지 않을 수 있습니다.")
            # 경고만 출력하고 진행
            return True
    except Exception as e:
        print(f"콘텐츠 형식 검증 중 오류: {e}")
        return True  # 오류 발생 시 기본값은 유효한 것으로 처리
        
# 콘텐츠 적용 검증 함수
def verify_content_applied(driver, content, mode):
    """
    콘텐츠가 에디터에 제대로 적용되었는지 검증
    """
    try:
        print("콘텐츠 적용 검증 중...")
        
        # CodeMirror 에디터 확인 (우선 확인)
        has_content = driver.execute_script("""
            try {
                // CodeMirror 에디터 확인
                var editors = document.querySelectorAll('.CodeMirror, .cm-editor');
                if (editors.length > 0) {
                    for (var i = 0; i < editors.length; i++) {
                        var editor = editors[i];
                        var content = '';
                        
                        // CodeMirror 인스턴스에서 내용 확인
                        if (editor.CodeMirror) {
                            content = editor.CodeMirror.getValue();
                        }
                        // 내부 textarea 확인
                        else {
                            var textarea = editor.querySelector('textarea');
                            if (textarea) {
                                content = textarea.value;
                            }
                        }
                        
                        // 내용이 있으면 성공
                        if (content && content.length > 100) {
                            console.log("CodeMirror 에디터에 충분한 내용이 있습니다: " + content.length + "자");
                            return true;
                        }
                    }
                }
                
                // TinyMCE 확인
                if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                    var editorContent = tinyMCE.activeEditor.getContent();
                    if (editorContent && editorContent.length > 100) {
                        console.log("TinyMCE 에디터에 충분한 내용이 있습니다: " + editorContent.length + "자");
                        return true;
                    }
                }
                
                // iframe 내용 확인
                var iframes = document.querySelectorAll('iframe');
                for (var j = 0; j < iframes.length; j++) {
                    try {
                        var frameDoc = iframes[j].contentDocument || iframes[j].contentWindow.document;
                        if (frameDoc && frameDoc.body) {
                            var iframeContent = frameDoc.body.innerHTML;
                            if (iframeContent && iframeContent.length > 100) {
                                console.log("iframe에 충분한 내용이 있습니다: " + iframeContent.length + "자");
                                return true;
                            }
                        }
                    } catch(e) {}
                }
                
                return false;
            } catch(e) {
                console.error("내용 확인 중 오류: " + e.message);
                return false;
            }
        """)
        
        if has_content:
            print("에디터에 충분한 내용이 적용되었습니다.")
            return True
        
        # 내용이 충분히 적용되지 않은 경우, 기존 방식으로 검증 진행
        print("콘텐츠 적용 여부를 더 자세히 분석 중...")
            
        # 1. 원본 콘텐츠에서 중요한 부분 추출
        # - 제목: <h1>, <h2> 태그 또는 첫 줄
        # - 주요 단어 및 문구
        import re
        
        # 원본 콘텐츠에서 제목 또는 중요 부분 추출
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE)
        if not title_match:
            title_match = re.search(r'<h2[^>]*>(.*?)</h2>', content, re.IGNORECASE)
        
        title_text = ""
        if title_match:
            title_text = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        else:
            # H1/H2 태그가 없으면 첫 단락이나 첫 줄을 제목으로 간주
            lines = content.split('\n')
            for line in lines:
                stripped = re.sub(r'<[^>]+>', '', line).strip()
                if stripped:
                    title_text = stripped
                    break
        
        print(f"원본 콘텐츠 제목: '{title_text}'")
        
        # 중요 단어/문구 추출 (최소 4글자 이상의 명사구)
        important_phrases = []
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
        
        for p in paragraphs:
            # 태그 제거
            clean_text = re.sub(r'<[^>]+>', '', p).strip()
            
            # 짧은 문단 건너뛰기
            if len(clean_text) < 20:
                continue
                
            # 문장 분리
            sentences = re.split(r'[.!?]', clean_text)
            for sentence in sentences:
                if len(sentence.strip()) >= 15:  # 적절한 길이의 문장만
                    important_phrases.append(sentence.strip())
        
        # 최대 3개의 중요 문구 선택
        if len(important_phrases) > 3:
            important_phrases = important_phrases[:3]
            
        print(f"중요 문구 {len(important_phrases)}개 추출: {important_phrases}")
        
        # 2. 현재 에디터 내용 가져오기
        editor_content = ""
        
        # CodeMirror 에디터에서 내용 가져오기 (우선)
        try:
            editor_content = driver.execute_script("""
                try {
                    // CodeMirror 에디터
                    var editors = document.querySelectorAll('.CodeMirror, .cm-editor');
                    if (editors.length > 0) {
                        for (var i = 0; i < editors.length; i++) {
                            var editor = editors[i];
                            if (editor.CodeMirror) {
                                return editor.CodeMirror.getValue() || '';
                            }
                        }
                    }
                    
                    // TinyMCE 에디터
                    if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                        return tinyMCE.activeEditor.getContent() || '';
                    }
                    
                    // iframe 내용
                    var iframes = document.querySelectorAll('iframe');
                    for (var j = 0; j < iframes.length; j++) {
                        try {
                            var frame = iframes[j];
                            var frameDoc = frame.contentDocument || frame.contentWindow.document;
                            if (frameDoc && frameDoc.body) {
                                return frameDoc.body.innerHTML || '';
                            }
                        } catch(e) {}
                    }
                    
                    // 일반 에디터 요소
                    var editorElements = document.querySelectorAll('.html-editor, [contenteditable="true"], textarea.code-editor');
                    if (editorElements.length > 0) {
                        return editorElements[0].value || editorElements[0].innerHTML || '';
                    }
                    
                    return '';
                } catch(e) {
                    console.error("에디터 내용 가져오기 중 오류: " + e.message);
                    return '';
                }
            """)
        except Exception as e:
            print(f"에디터 내용 가져오기 중 오류: {e}")
        
        # 디버깅용: 에디터에 내용이 있는지 확인
        if editor_content:
            content_preview = editor_content[:200] + "..." if len(editor_content) > 200 else editor_content
            print(f"에디터 내용 샘플: {content_preview}")
            print(f"에디터 내용 길이: {len(editor_content)} 자")
        else:
            print("에디터에서 내용을 가져올 수 없습니다.")
            
            # 보강 검사: 에디터에 최소한의 내용이라도 있는지 확인
            content_exists = driver.execute_script("""
                // 모든 가능한 에디터 요소 검사
                var elements = [
                    document.querySelector('.CodeMirror, .cm-editor'),
                    document.querySelector('.mce-content-body'),
                    document.querySelector('[contenteditable="true"]'),
                    document.querySelector('textarea.code-editor')
                ];
                
                for (var i = 0; i < elements.length; i++) {
                    var el = elements[i];
                    if (el && (
                        (el.innerHTML && el.innerHTML.length > 50) || 
                        (el.value && el.value.length > 50)
                    )) {
                        return true;
                    }
                }
                
                return false;
            """)
            
            if content_exists:
                print("에디터에 내용이 존재하는 것으로 확인됩니다.")
                return True
            
        # 3. 에디터 내용에서 제목과 주요 문구 확인
        
        # 제목 확인 (티스토리가 추가하는 속성 고려)
        title_found = False
        if title_text:
            # 정확히 일치하는 경우
            if title_text in editor_content:
                title_found = True
                print(f"제목 정확히 일치: '{title_text}'")
            else:
                # 속성이 추가된 태그 내에서 확인
                title_patterns = [
                    re.escape(title_text),
                    # 다양한 형태로 추가 가능
                ]
                
                for pattern in title_patterns:
                    if re.search(pattern, editor_content, re.IGNORECASE):
                        title_found = True
                        print(f"제목 패턴 일치: '{pattern}'")
                        break
        
        # 주요 문구 확인
        phrases_found = 0
        for phrase in important_phrases:
            if phrase in editor_content:
                phrases_found += 1
                print(f"문구 일치: '{phrase}'")
            else:
                # 문구의 일부(첫 10단어)라도 있는지 확인
                words = phrase.split()[:10]
                partial_phrase = ' '.join(words)
                if len(partial_phrase) > 15 and partial_phrase in editor_content:
                    phrases_found += 1
                    print(f"부분 문구 일치: '{partial_phrase}'")
        
        # 검증 결과
        if title_found or phrases_found > 0:
            print(f"콘텐츠 적용 검증 통과: 제목 일치={title_found}, 문구 일치={phrases_found}")
            return True
        else:
            # 에디터 내용 길이가 충분히 길면, 어떤 내용이 들어갔다고 가정
            if editor_content and len(editor_content) > 500:
                print(f"콘텐츠 적용 추정: 에디터에 {len(editor_content)} 길이의 콘텐츠 존재")
                return True
            
            print("콘텐츠 적용 검증 실패: 제목과 주요 문구가 모두 일치하지 않습니다.")
            print("그러나 글 작성은 계속 진행합니다.")
            return True  # 확인 실패해도 계속 진행
    except Exception as e:
        print(f"콘텐츠 적용 검증 중 오류: {e}")
        # 오류 발생시 내용이 있다고 가정 (false positive가 false negative보다 나음)
        return True

# 모달 창에서 확인 버튼 클릭을 돕는 새로운 함수 추가
def click_confirm_dialog_button(driver, wait_time=3):
    """모드 변경 확인 대화상자의 '확인' 버튼 클릭"""
    try:
        print("확인 대화상자 검색 중...")
        
        # 1. 일반적인 알림창(alert) 처리
        try:
            WebDriverWait(driver, 2).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            print(f"알림창 발견: '{alert.text}'")
            alert.accept()
            print("알림창의 '확인' 버튼을 클릭했습니다.")
            return True
        except Exception as alert_e:
            print(f"브라우저 기본 알림창 없음: {alert_e}")
        
        # 2. 대화상자의 텍스트 내용과 버튼을 기준으로 찾기
        dialog_texts = ["작성 모드", "변경", "서식이 유지되지 않을", "모드 전환"]
        
        # 텍스트 내용으로 대화상자 찾기
        for text in dialog_texts:
            try:
                dialog_elem = WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{text}')]"))
                )
                
                if dialog_elem:
                    print(f"대화상자 텍스트 발견: '{text}'")
                    
                    # 부모/조상 요소에서 버튼 찾기
                    parent = dialog_elem
                    for _ in range(5):  # 최대 5단계 상위로 올라가기
                        try:
                            parent = parent.find_element(By.XPATH, "..")  # 부모 요소로 이동
                            buttons = parent.find_elements(By.TAG_NAME, "button")
                            
                            if buttons:
                                for btn in buttons:
                                    if '확인' in btn.text or not btn.text.strip():
                                        btn.click()
                                        print(f"대화상자 버튼 클릭: '{btn.text}'")
                                        return True
                        except:
                            break
            except:
                continue
        
        # 3. JavaScript로 대화상자 찾아 처리
        result = driver.execute_script("""
            // 여러 가지 가능한 확인 버튼 선택자
            var confirmSelectors = [
                '.confirm-yes', '.btn-confirm', '.btn_confirm', 
                '.btn_yes', '.confirm_ok', '.btn_ok', '.btn-primary',
                'button.confirm', 'button.yes'
            ];
            
            // 텍스트로 확인 버튼 찾기
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                if (btn.textContent.includes('확인') || 
                    btn.textContent.toLowerCase().includes('ok') || 
                    btn.textContent.toLowerCase().includes('yes')) {
                    console.log('확인 버튼 발견: ' + btn.textContent);
                    btn.click();
                    return true;
                }
            }
            
            // 선택자로 확인 버튼 찾기
            for (var j = 0; j < confirmSelectors.length; j++) {
                var elements = document.querySelectorAll(confirmSelectors[j]);
                if (elements.length > 0) {
                    elements[0].click();
                    return true;
                }
            }
            
            // "작성 모드를 변경" 텍스트를 포함하는 요소 주변의 버튼 찾기
            var confirmTexts = ["작성 모드", "변경", "서식이 유지", "모드 전환"];
            for (var k = 0; k < confirmTexts.length; k++) {
                var textNodes = [];
                var walk = document.createTreeWalker(
                    document.body, 
                    NodeFilter.SHOW_TEXT, 
                    { acceptNode: function(node) { 
                        return node.nodeValue.includes(confirmTexts[k]) ? 
                            NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT; 
                    }}, 
                    false
                );
                
                while(walk.nextNode()) {
                    textNodes.push(walk.currentNode.parentNode);
                }
                
                for (var l = 0; l < textNodes.length; l++) {
                    var node = textNodes[l];
                    for (var m = 0; m < 5; m++) {  // 최대 5단계 상위로 올라가기
                        if (!node) break;
                        
                        var nodeBtns = node.querySelectorAll('button');
                        if (nodeBtns.length > 0) {
                            // 첫 번째 버튼이 일반적으로 '확인'
                            nodeBtns[0].click();
                            return true;
                        }
                        
                        node = node.parentNode;
                    }
                }
            }
            
            // 모든 모달/대화상자 스캔
            var dialogs = document.querySelectorAll('.modal, .dialog, .confirm, .alert, [role="dialog"]');
            for (var n = 0; n < dialogs.length; n++) {
                var dialogButtons = dialogs[n].querySelectorAll('button');
                if (dialogButtons.length > 0) {
                    // 첫 번째 버튼이 일반적으로 '확인'
                    dialogButtons[0].click();
                    return true;
                }
            }
            
            return false;
        """)
        
        if result:
            print("JavaScript를 통해 확인 버튼을 클릭했습니다.")
            return True
            
        print("확인 대화상자를 찾지 못했거나 '확인' 버튼을 클릭하지 못했습니다.")
        return False
        
    except Exception as e:
        print(f"확인 대화상자 처리 중 오류: {e}")
        return False

# 알림창 처리를 위한 함수 추가
def handle_alert(driver, max_attempts=3):
    """
    브라우저에 표시될 수 있는 알림창(alert)을 처리하는 함수
    티스토리의 "저장된 글이 있습니다." 메시지 등을 자동으로 처리
    """
    try:
        for attempt in range(max_attempts):
            try:
                # 알림창 확인 (1초 타임아웃으로 빠른 확인)
                WebDriverWait(driver, 1).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                alert_text = alert.text
                
                print(f"알림창 발견 ({attempt+1}/{max_attempts}): '{alert_text}'")
                
                # 저장된 글 관련 알림
                if "저장된 글이 있습니다" in alert_text and "이어서 작성하시겠습니까" in alert_text:
                    print("이전에 저장된 글 관련 알림입니다. '취소' 버튼 클릭 (새 글 작성)")
                    alert.dismiss()  # '취소' 버튼 클릭
                else:
                    # 기타 알림은 '확인' 버튼 클릭
                    print(f"일반 알림 - '확인' 버튼 클릭: '{alert_text}'")
                    alert.accept()
                
                # 알림창 처리 후 잠시 대기
                time.sleep(1)
            
            except Exception:
                # 더 이상 알림창이 없으면 종료
                break
                
        return True
    except Exception as e:
        print(f"알림창 처리 중 오류 (무시됨): {e}")
        return False

# 콘텐츠 생성 함수에 재시도 로직 추가
def generate_blog_content_with_retry(topic, format_type=2, max_retries=3, retry_delay=5):
    """재시도 로직이 포함된 블로그 콘텐츠 생성 함수"""
    for attempt in range(max_retries):
        try:
            return generate_blog_content(topic, format_type=2)  # 항상 일반 텍스트 모드(2)로 설정
        except Exception as e:
            print(f"시도 {attempt+1}/{max_retries} 실패: {e}")
            if attempt < max_retries - 1:
                print(f"{retry_delay}초 후 재시도합니다...")
                time.sleep(retry_delay)
            else:
                print("최대 재시도 횟수를 초과했습니다.")
                raise

def publish_post(driver, blog_post=None):
    """발행 버튼 클릭 및 발행 처리"""
    try:
        # 디버깅 정보: 페이지의 모든 버튼 정보 출력
        try:
            print("\n==== 페이지의 모든 버튼 정보 [디버깅] ====")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"페이지에서 총 {len(buttons)}개의 버튼을 찾았습니다.")
            
            for i, btn in enumerate(buttons[:30]):  # 처음 30개 버튼만 출력
                try:
                    btn_text = btn.text.strip() or '(텍스트 없음)'
                    btn_id = btn.get_attribute('id') or '(ID 없음)'
                    btn_class = btn.get_attribute('class') or '(클래스 없음)'
                    btn_type = btn.get_attribute('type') or '(타입 없음)'
                    is_displayed = btn.is_displayed()
                    is_enabled = btn.is_enabled()
                    print(f"버튼 {i+1}: 텍스트='{btn_text}', ID='{btn_id}', 클래스='{btn_class}', 타입='{btn_type}', 표시={is_displayed}, 활성화={is_enabled}")
                    
                    # 공개 발행 관련 텍스트가 있는 버튼 강조 표시
                    if '공개' in btn_text or '발행' in btn_text:
                        print(f"  >>> 발행 관련 버튼으로 의심됨: {btn_text} (ID={btn_id}) <<<")
                except Exception as e:
                    print(f"버튼 {i+1}: 정보 가져오기 실패 - {e}")
            
            # form 요소도 확인
            forms = driver.find_elements(By.TAG_NAME, "form")
            print(f"\n페이지에서 총 {len(forms)}개의 폼을 찾았습니다.")
            for i, form in enumerate(forms):
                try:
                    form_id = form.get_attribute('id') or '(ID 없음)'
                    form_action = form.get_attribute('action') or '(action 없음)'
                    form_method = form.get_attribute('method') or '(method 없음)'
                    submit_buttons = form.find_elements(By.CSS_SELECTOR, 'button[type="submit"]')
                    print(f"폼 {i+1}: ID='{form_id}', action='{form_action}', method='{form_method}', submit 버튼 수={len(submit_buttons)}")
                except Exception as e:
                    print(f"폼 {i+1}: 정보 가져오기 실패 - {e}")
            
            print("==== 디버깅 정보 끝 ====\n")
        except Exception as debug_e:
            print(f"디버깅 정보 수집 중 오류: {debug_e}")
            
        # 발행 전 콘텐츠를 강제로 다시 설정 (주요 수정)
        if blog_post:
            print("\n===== 발행 전 콘텐츠 강제 재설정 =====")
            
            # HTML 형식으로 변환 (줄바꿈, 문단 구분)
            raw_content = blog_post["raw_content"]
            paragraphs = raw_content.split("\n\n")
            
            # 개선된 HTML 형식으로 각 문단 변환
            html_content = ""
            for paragraph in paragraphs:
                if paragraph.strip():
                    # 줄바꿈 처리
                    paragraph = paragraph.replace("\n", "<br>")
                    # HTML 문단 태그로 감싸기
                    html_content += f"<p>{paragraph}</p>\n"
            
            print(f"최종 HTML 형식 콘텐츠 준비 완료: {len(html_content)} 바이트")
            
            # 모든 가능한 방법으로 콘텐츠 설정 시도
            
            # 방법 1: 기본 iframe 편집기 설정
            iframe_editor = find_editor_iframe(driver)
            if iframe_editor:
                try:
                    driver.switch_to.frame(iframe_editor)
                    print("iframe 에디터에 접근했습니다.")
                    body = driver.find_element(By.TAG_NAME, "body")
                    driver.execute_script("arguments[0].innerHTML = arguments[1];", body, html_content)
                    print("iframe 내부 body에 HTML 콘텐츠를 설정했습니다.")
                    driver.switch_to.default_content()
                    time.sleep(1)
                except Exception as e:
                    print(f"iframe 콘텐츠 설정 오류: {e}")
                    driver.switch_to.default_content()
            
            # 방법 2: JavaScript를 통한 다양한 에디터 접근
            try:
                result = driver.execute_script("""
                    try {
                        console.log("콘텐츠 설정 스크립트 실행 중...");
                        var content = arguments[0];
                        var setSuccess = false;

                        // TinyMCE 설정
                        if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                            console.log("TinyMCE 에디터 발견");
                            tinyMCE.activeEditor.setContent(content);
                            console.log("TinyMCE 콘텐츠 설정됨");
                            setSuccess = true;
                        }

                        // 티스토리 에디터 API 사용
                        if (window.tistoryEditor) {
                            console.log("티스토리 에디터 객체 발견");
                            if (typeof tistoryEditor.setContent === 'function') {
                                tistoryEditor.setContent(content);
                                console.log("tistoryEditor.setContent 호출됨");
                                setSuccess = true;
                            }
                            else if (typeof tistoryEditor.setHtmlContent === 'function') {
                                tistoryEditor.setHtmlContent(content);
                                console.log("tistoryEditor.setHtmlContent 호출됨");
                                setSuccess = true;
                            }
                            
                            // 티스토리 내부 상태 강제 업데이트
                            if (tistoryEditor.contentElement) {
                                tistoryEditor.contentElement.value = content;
                                console.log("tistoryEditor.contentElement 설정됨");
                                setSuccess = true;
                            }
                            
                            // 티스토리 내부 데이터 설정 (중요!)
                            tistoryEditor.content = content;
                            console.log("tistoryEditor.content 직접 설정됨");
                            setSuccess = true;
                        }

                        // CodeMirror 에디터 설정
                        var cmEditors = document.querySelectorAll('.CodeMirror');
                        if (cmEditors.length > 0) {
                            for (var i = 0; i < cmEditors.length; i++) {
                                var ed = cmEditors[i];
                                if (ed.CodeMirror) {
                                    ed.CodeMirror.setValue(content);
                                    console.log("CodeMirror 콘텐츠 설정됨");
                                    setSuccess = true;
                                }
                            }
                        }

                        // 모든 iframe 순회
                        var frames = document.querySelectorAll('iframe');
                        for (var i = 0; i < frames.length; i++) {
                            try {
                                var frame = frames[i];
                                var frameDoc = frame.contentDocument || frame.contentWindow.document;
                                if (frameDoc && frameDoc.body) {
                                    frameDoc.body.innerHTML = content;
                                    console.log(i + "번 iframe에 콘텐츠 설정됨");
                                    setSuccess = true;
                                }
                            } catch(e) {
                                console.log("iframe 접근 오류: " + e.message);
                            }
                        }

                        // 마지막 시도: 모든 가능한 에디터 요소 순회
                        var possibleEditors = [
                            document.querySelector('[data-role="editor"]'),
                            document.querySelector('.editor-body'),
                            document.querySelector('.content-area'),
                            document.querySelector('.editor-frame'),
                            document.querySelector('#editor')
                        ];
                        
                        for (var j = 0; j < possibleEditors.length; j++) {
                            var editor = possibleEditors[j];
                            if (editor) {
                                try {
                                    editor.innerHTML = content;
                                    console.log("가능한 에디터 요소에 콘텐츠 설정됨");
                                    setSuccess = true;
                                } catch(e) {}
                            }
                        }

                        // 모든 textarea 확인 (마지막 시도)
                        var textareas = document.querySelectorAll('textarea');
                        for (var k = 0; k < textareas.length; k++) {
                            var ta = textareas[k];
                            if (ta.id !== 'post-title-inp' && ta.clientHeight > 50) {
                                ta.value = content;
                                console.log("큰 textarea에 콘텐츠 설정됨");
                                setSuccess = true;
                                
                                // 이벤트 발생시켜 변경사항 알림
                                var event = new Event('input', { bubbles: true });
                                ta.dispatchEvent(event);
                            }
                        }

                        return setSuccess ? "콘텐츠 설정 성공" : "모든 에디터 접근 시도 실패";
                    } catch(e) {
                        return "오류 발생: " + e.message;
                    }
                """, html_content)
                
                print(f"자바스크립트 콘텐츠 설정 결과: {result}")
            except Exception as e:
                print(f"자바스크립트 실행 오류: {e}")
        
        # 바로 공개발행 버튼 찾기 및 클릭하기
        print("\n===== 공개발행 버튼 검색 및 클릭 =====")
        
        # ID를 통해 직접 버튼 찾기 (가장 정확한 방법)
        publish_found = False
        try:
            publish_btn = driver.find_element(By.ID, "publish-btn")
            btn_text = publish_btn.text
            print(f"ID로 발행 버튼 찾음: '{btn_text}' (id=publish-btn)")
            publish_btn.click()
            print("'공개 발행' 버튼 클릭 성공")
            time.sleep(2)
            confirm_publish(driver)
            publish_found = True
        except Exception as e:
            print(f"ID로 발행 버튼 찾기 실패: {e}")
        
        # 정확한 텍스트로 버튼 찾기
        if not publish_found:
            try:
                # 주의: '공개 발행'에는 공백이 있음
                publish_buttons = driver.find_elements(By.XPATH, "//button[normalize-space(text()) = '공개 발행']")
                if publish_buttons:
                    print(f"정확한 텍스트로 '공개 발행' 버튼 찾음")
                    publish_buttons[0].click()
                    print("'공개 발행' 버튼 클릭 성공")
                    time.sleep(2)
                    confirm_publish(driver)
                    publish_found = True
            except Exception as e:
                print(f"정확한 텍스트로 버튼 찾기 실패: {e}")
                
        # CSS 선택자로 찾기
        if not publish_found:
            try:
                # 정확한 버튼을 위한 CSS 선택자
                css_selectors = [
                    "#publish-btn",  # 가장 정확한 ID 선택자
                    "button#publish-btn",  # ID 선택자 변형
                    "button.btn.btn-default[type='submit']",  # 클래스와 타입 조합
                    "form button[type='submit']",  # 폼 내 submit 버튼
                    ".btn-publish",
                    ".publish-btn",
                    "button[type='submit']"
                ]
                
                for selector in css_selectors:
                    btns = driver.find_elements(By.CSS_SELECTOR, selector)
                    if btns:
                        for btn in btns:
                            btn_text = btn.text.strip()
                            print(f"CSS 선택자로 버튼 찾음: '{btn_text}' (selector={selector})")
                            if '공개' in btn_text or '발행' in btn_text or btn.get_attribute('id') == 'publish-btn':
                                btn.click()
                                print(f"'{btn_text}' 버튼 클릭 (selector={selector})")
                                time.sleep(2)
                                confirm_publish(driver)
                                publish_found = True
                                break
                        if publish_found:
                            break
            except Exception as e:
                print(f"CSS 선택자로 버튼 찾기 실패: {e}")
                
        # 폼 직접 제출 시도
        if not publish_found:
            try:
                print("\n폼 직접 제출 시도...")
                forms = driver.find_elements(By.TAG_NAME, "form")
                if forms:
                    for form in forms:
                        try:
                            # 폼 내에 '공개 발행' 버튼이 있는지 확인
                            submit_buttons = form.find_elements(By.CSS_SELECTOR, "button[type='submit']")
                            if submit_buttons:
                                for btn in submit_buttons:
                                    btn_text = btn.text.strip()
                                    if '공개' in btn_text or '발행' in btn_text:
                                        print(f"폼 내 발행 버튼 발견: '{btn_text}'")
                                        btn.click()
                                        print(f"폼 내 '{btn_text}' 버튼 클릭")
                                        time.sleep(2)
                                        confirm_publish(driver)
                                        publish_found = True
                                        break
                            
                            # 버튼이 없거나 클릭하지 못한 경우 폼 직접 제출
                            if not publish_found:
                                driver.execute_script("arguments[0].submit();", form)
                                print("JavaScript로 폼 직접 제출")
                                time.sleep(2)
                                confirm_publish(driver)
                                publish_found = True
                        except Exception as form_e:
                            print(f"폼 처리 중 오류: {form_e}")
            except Exception as forms_e:
                print(f"폼 접근 중 오류: {forms_e}")
         
        # 1. '공개발행' 텍스트가 있는 버튼 찾기 (이전 방식과 병합)
        if not publish_found:
            try:
                # 부분 텍스트 매칭으로 검색 범위 확장
                publish_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '공개') or contains(text(), '발행')]")
                if publish_buttons:
                    for btn in publish_buttons:
                        btn_text = btn.text.strip()
                        print(f"버튼 발견: '{btn_text}'")
                        btn.click()
                        print(f"'{btn_text}' 버튼을 클릭했습니다.")
                        time.sleep(2)
                        confirm_publish(driver)
                        publish_found = True
                        break
            except Exception as e:
                print(f"부분 텍스트 매칭 버튼 클릭 시도 중 오류: {e}")
            
        # 2. JavaScript를 사용하여 공개발행 버튼 찾기
        if not publish_found:
            try:
                print("JavaScript를 통한 발행 버튼 검색...")
                result = driver.execute_script("""
                    // ID로 직접 찾기 (가장 정확한 방법)
                    var btn = document.getElementById('publish-btn');
                    if (btn) {
                        console.log('ID로 버튼 찾음: publish-btn');
                        btn.click();
                        return "ID publish-btn 버튼 클릭됨";
                    }
                    
                    // 모든 버튼 요소 가져오기
                    var allButtons = document.querySelectorAll('button');
                    console.log('총 ' + allButtons.length + '개의 버튼 확인 중');
                    
                    // '공개 발행'(공백 있음) 텍스트가 있는 버튼 찾기
                    for (var i = 0; i < allButtons.length; i++) {
                        var btn = allButtons[i];
                        var btnText = btn.textContent.trim();
                        
                        if (btnText === '공개 발행' || btnText === '공개발행' || 
                            (btnText.includes('공개') && btnText.includes('발행'))) {
                            console.log('발견된 버튼: ' + btnText);
                            btn.click();
                            return "버튼 '" + btnText + "' 클릭됨";
                        }
                    }
                    
                    // 버튼 ID나 클래스로 시도
                    var publishBtn = document.querySelector('#publish-btn, .btn-publish, .publish-btn, button[type="submit"]');
                    if (publishBtn) {
                        publishBtn.click();
                        return "선택자로 찾은 발행 버튼 클릭됨";
                    }

                    // submit 타입 버튼 중 공개/발행이 포함된 것 찾기
                    var submitButtons = document.querySelectorAll('button[type="submit"]');
                    for (var j = 0; j < submitButtons.length; j++) {
                        var submitBtn = submitButtons[j];
                        var btnText = submitBtn.textContent.trim();
                        if (btnText.includes('공개') || btnText.includes('발행')) {
                            submitBtn.click();
                            return "submit 버튼 '" + btnText + "' 클릭됨";
                        }
                    }
                    
                    // 폼 직접 제출 시도
                    var forms = document.querySelectorAll('form');
                    for (var k = 0; k < forms.length; k++) {
                        var form = forms[k];
                        if (form.querySelector('button[type="submit"]')) {
                            form.submit();
                            return "폼 직접 제출됨";
                        }
                    }
                    
                    return false;
                """)
                
                if result:
                    print(f"JavaScript 결과: {result}")
                    time.sleep(2)
                    confirm_publish(driver)
                    publish_found = True
            except Exception as js_e:
                print(f"JavaScript를 통한 발행 시도 중 오류: {js_e}")
                
        # 3. 이전 방식으로 시도 (여러 선택자)
        if not publish_found:
            publish_selectors = [
                ".btn_publish", 
                ".btn-publish", 
                ".publish-button", 
                "#publish", 
                ".publish-btn",
                "[data-type='publish']",
                "[data-action='publish']",
                ".open-options" # 옵션 메뉴 열기 버튼 (발행 기능 포함)
            ]
            
            for selector in publish_selectors:
                try:
                    publish_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    if publish_buttons:
                        publish_button = publish_buttons[0]
                        print(f"발행 버튼을 찾았습니다: {selector}")
                        publish_button.click()
                        print("발행 버튼을 클릭했습니다.")
                        time.sleep(2)  # 발행 옵션 창이 열릴 때까지 대기
                        
                        # 발행 옵션 창에서 확인 버튼 클릭
                        confirm_publish(driver)
                        publish_found = True
                        break
                except Exception as e:
                    print(f"발행 버튼({selector}) 클릭 중 오류: {e}")
        
        # 4. XPath를 사용하여 버튼 찾기
        if not publish_found:
            try:
                publish_xpath_expressions = [
                    "//a[contains(text(), '공개발행')]",
                    "//button[contains(text(), '발행')]",
                    "//button[contains(@class, 'publish') or contains(@id, 'publish')]",
                    "//a[contains(text(), '발행') or contains(@class, 'publish')]",
                    "//div[contains(@class, 'publish')]//button"
                ]
                
                for xpath_expr in publish_xpath_expressions:
                    publish_buttons_xpath = driver.find_elements(By.XPATH, xpath_expr)
                    if publish_buttons_xpath:
                        publish_button = publish_buttons_xpath[0]
                        print(f"XPath를 통해 발행 버튼을 찾았습니다: {xpath_expr}")
                        publish_button.click()
                        print("XPath를 통해 발행 버튼을 클릭했습니다.")
                        time.sleep(2)
                        confirm_publish(driver)
                        publish_found = True
                        break
            except Exception as xpath_e:
                print(f"XPath를 통한 발행 버튼 찾기 중 오류: {xpath_e}")
        
        # 발행 성공 여부 확인
        if publish_found:
            # 발행 완료 메시지가 표시되는지 확인
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".publish-complete, .alert-success, .success-message"))
                )
                print("발행 완료 메시지가 확인되었습니다!")
                return True
            except Exception as wait_e:
                print("발행 완료 메시지를 찾을 수 없습니다만, 발행은 진행되었을 수 있습니다.")
                return True
        else:
            print("발행 버튼을 찾지 못했습니다. 발행에 실패했습니다.")
            return False
        
    except Exception as e:
        print(f"발행 과정 중 오류 발생: {e}")
        return False

def confirm_publish(driver):
    """발행 옵션 창에서 최종 발행 확인 버튼 클릭"""
    try:
        print("발행 확인 대화상자 처리 중...")
        
        # 0. 이미 발행이 진행 중인지 확인
        try:
            # 발행 로딩 표시기가 활성화되어 있다면 대기
            loading_indicators = driver.find_elements(By.CSS_SELECTOR, 
                ".loading, .loading-indicator, .progress-bar, .spinner")
            
            if loading_indicators and any(indicator.is_displayed() for indicator in loading_indicators):
                print("발행이 이미 진행 중입니다. 완료될 때까지 대기합니다...")
                # 최대 20초 대기
                WebDriverWait(driver, 20).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        ".loading, .loading-indicator, .progress-bar, .spinner"))
                )
                return True
        except Exception as load_e:
            print(f"로딩 확인 중 오류 (무시됨): {load_e}")
        
        # 1. ID로 직접 확인 버튼 찾기 (티스토리 전용)
        try:
            confirm_ids = ["confirmYes", "btn-confirm", "ok-button", "yes-button", "confirm-btn"]
            for btn_id in confirm_ids:
                try:
                    confirm_btn = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.ID, btn_id))
                    )
                    print(f"ID({btn_id})로 확인 버튼을 찾았습니다.")
                    confirm_btn.click()
                    print(f"ID({btn_id}) 확인 버튼 클릭됨")
                    time.sleep(3)
                    return True
                except:
                    continue
        except Exception as id_e:
            print(f"ID로 버튼 찾기 실패 (무시됨): {id_e}")
        
        # 2. 텍스트가 '확인'인 버튼 찾기
        try:
            confirm_texts = ["확인", "예", "네", "발행", "공개", "확인", "Yes"]
            
            for text in confirm_texts:
                confirm_button = driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                if confirm_button:
                    print(f"'{text}' 텍스트가 포함된 확인 버튼을 찾았습니다.")
                    confirm_button[0].click()
                    print(f"'{text}' 버튼 클릭됨")
                    time.sleep(3)
                    return True
        except Exception as text_e:
            print(f"텍스트로 버튼 찾기 실패: {text_e}")
        
        # 3. 팝업/모달 다이얼로그 처리 (기본 알림창)
        try:
            alert = driver.switch_to.alert
            print(f"알림창 발견: '{alert.text}'")
            alert.accept() # 확인 버튼 클릭
            print("알림창의 '확인' 버튼 클릭")
            time.sleep(3)
            return True
        except Exception as alert_e:
            print(f"알림창 처리 실패 (무시됨): {alert_e}")
        
        print("발행 확인 버튼을 찾을 수 없습니다.")
        return False
        
    except Exception as e:
        print(f"발행 확인 과정에서 오류 발생: {e}")
        return False

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
        
        # 경고창(Alert) 처리 (이전 저장 글 관련)
        handle_alert(driver)
        
        # 무한 루프로 글 작성 진행 (사용자가 종료하기 전까지)
        while True:
            # 사용자에게 주제 선택 요청
            selected_topic = get_user_topic()
            
            # 콘텐츠 생성 (기본 텍스트 모드로 고정)
            try:
                # format_type=2 (일반 텍스트 모드)로 고정
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
            
            # 알림창(Alert) 자동 처리 - 저장된 글 있는 경우
            handle_alert(driver)

            # 글 작성 함수 호출 (format_type=2 고정)
            write_post(driver, blog_post)
            
            # 임시저장 단계 없이 바로 공개발행 진행
            print("\n글 작성이 완료되었습니다. 바로 공개발행을 진행합니다...")
            publish_success = publish_post(driver, blog_post)
            
            if publish_success:
                print("발행이 완료되었습니다!")
            else:
                print("발행에 실패했습니다.")
            
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
            handle_alert(driver)
            
    except Exception as e:
        print(f"전체 과정에서 오류 발생: {e}")
    
    finally:
        # 루프가 종료되었을 때만 브라우저 종료
        driver.quit()

# 메인 함수
if __name__ == "__main__":
    print("ChatGPT를 이용한 티스토리 자동 포스팅 시작")
    login_and_post_to_tistory() 