import os
import time
import json
import pickle
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

# 환경변수 로드
load_dotenv()

# 설정
BLOG_MANAGE_URL = "https://climate-insight.tistory.com/manage/post"
COOKIES_FILE = "tistory_cookies.pkl"
LOCAL_STORAGE_FILE = "tistory_local_storage.json"

class TistoryAutoLogin:
    def __init__(self, headless=False):
        """티스토리 자동 로그인 클래스 초기화"""
        self.driver = None
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        """웹드라이버 설정"""
        options = webdriver.ChromeOptions()
        
        if self.headless:
            options.add_argument("--headless")
        
        # 자동화 감지 우회 설정
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # 추가 안정성 옵션
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # 자동화 감지 우회 스크립트 실행
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ 웹드라이버 설정 완료")
    
    def save_cookies(self):
        """쿠키 저장"""
        try:
            Path(COOKIES_FILE).parent.mkdir(parents=True, exist_ok=True)
            cookies = self.driver.get_cookies()
            
            # 티스토리 관련 쿠키만 필터링
            filtered_cookies = []
            for cookie in cookies:
                if 'domain' in cookie and ('tistory.com' in cookie['domain'] or cookie['domain'] == '.tistory.com'):
                    # 문제가 될 수 있는 속성 제거
                    clean_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': '.tistory.com',
                        'path': cookie.get('path', '/'),
                        'secure': cookie.get('secure', False),
                        'httpOnly': cookie.get('httpOnly', False)
                    }
                    
                    if 'expiry' in cookie:
                        clean_cookie['expiry'] = int(cookie['expiry'])
                    
                    filtered_cookies.append(clean_cookie)
            
            if filtered_cookies:
                pickle.dump(filtered_cookies, open(COOKIES_FILE, "wb"))
                print(f"✅ 티스토리 쿠키 {len(filtered_cookies)}개 저장 완료")
                return True
            else:
                print("❌ 저장할 티스토리 쿠키가 없습니다")
                return False
                
        except Exception as e:
            print(f"❌ 쿠키 저장 실패: {e}")
            return False
    
    def load_cookies(self):
        """쿠키 로드"""
        try:
            if not os.path.exists(COOKIES_FILE):
                print("❌ 쿠키 파일이 존재하지 않습니다")
                return False
            
            # 티스토리 메인 페이지 접속
            self.driver.get("https://www.tistory.com")
            time.sleep(2)
            
            # 기존 쿠키 삭제
            self.driver.delete_all_cookies()
            
            # 저장된 쿠키 로드
            cookies = pickle.load(open(COOKIES_FILE, "rb"))
            print(f"📁 쿠키 파일에서 {len(cookies)}개 로드")
            
            success_count = 0
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                    success_count += 1
                except Exception as e:
                    print(f"⚠️  쿠키 추가 실패: {cookie.get('name', 'unknown')} - {e}")
            
            print(f"✅ {success_count}/{len(cookies)}개 쿠키 로드 성공")
            
            # 페이지 새로고침하여 쿠키 적용
            self.driver.refresh()
            time.sleep(3)
            
            return success_count > 0
            
        except Exception as e:
            print(f"❌ 쿠키 로드 실패: {e}")
            return False
    
    def save_local_storage(self):
        """로컬 스토리지 저장"""
        try:
            Path(LOCAL_STORAGE_FILE).parent.mkdir(parents=True, exist_ok=True)
            local_storage = self.driver.execute_script("return Object.entries(localStorage);")
            
            with open(LOCAL_STORAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(local_storage, f, ensure_ascii=False)
            
            print(f"✅ 로컬 스토리지 저장 완료")
            return True
            
        except Exception as e:
            print(f"❌ 로컬 스토리지 저장 실패: {e}")
            return False
    
    def load_local_storage(self):
        """로컬 스토리지 로드"""
        try:
            if not os.path.exists(LOCAL_STORAGE_FILE):
                print("❌ 로컬 스토리지 파일이 존재하지 않습니다")
                return False
            
            with open(LOCAL_STORAGE_FILE, 'r', encoding='utf-8') as f:
                local_storage = json.load(f)
            
            for item in local_storage:
                if len(item) >= 2:
                    key, value = item[0], item[1]
                    self.driver.execute_script(f"localStorage.setItem('{key}', '{value}');")
            
            print("✅ 로컬 스토리지 로드 완료")
            return True
            
        except Exception as e:
            print(f"❌ 로컬 스토리지 로드 실패: {e}")
            return False
    
    def is_logged_in(self):
        """로그인 상태 확인"""
        try:
            # 알림창 처리
            self.handle_alerts()
            
            # 대시보드 접근 시도
            self.driver.get(BLOG_MANAGE_URL)
            time.sleep(5)
            
            # 알림창 다시 처리
            self.handle_alerts()
            
            current_url = self.driver.current_url
            
            # URL 기반 확인
            if "login" in current_url.lower() or "auth" in current_url.lower():
                print("❌ 로그인 페이지로 리디렉션됨")
                return False
            
            # JavaScript로 추가 확인
            login_indicators = self.driver.execute_script("""
                var indicators = [];
                
                // 로그아웃 버튼 확인
                if (document.querySelector('.logout-button, .btn-logout, a[href*="logout"]')) {
                    indicators.push('logout_button');
                }
                
                // 글 작성 버튼 확인
                if (document.querySelector('a[href*="newpost"], .btn_post')) {
                    indicators.push('write_button');
                }
                
                // 관리 패널 확인
                if (document.querySelector('.my-blog, .blog-list, .control-panel, .dashboard')) {
                    indicators.push('admin_panel');
                }
                
                // 사용자 정보 확인
                if (document.querySelector('.username, .user-info, .profile-name')) {
                    indicators.push('user_info');
                }
                
                return indicators;
            """)
            
            if login_indicators:
                print(f"✅ 로그인 상태 확인됨: {', '.join(login_indicators)}")
                return True
            else:
                print("❌ 로그인 상태 확인 실패")
                return False
                
        except Exception as e:
            print(f"❌ 로그인 상태 확인 중 오류: {e}")
            return False
    
    def handle_alerts(self):
        """알림창 자동 처리"""
        try:
            alert = WebDriverWait(self.driver, 2).until(EC.alert_is_present())
            if alert:
                alert_text = alert.text
                print(f"🔔 알림창 감지: {alert_text}")
                alert.accept()  # 자동으로 확인 버튼 클릭
                print("✅ 알림창 처리 완료")
                time.sleep(1)
        except:
            pass  # 알림창이 없으면 무시
    
    def login_with_credentials(self):
        """아이디/비밀번호로 로그인"""
        try:
            # 환경변수에서 로그인 정보 가져오기
            username = os.getenv("TISTORY_USERNAME")
            password = os.getenv("TISTORY_PASSWORD")
            
            if not username or not password:
                print("❌ 환경변수에 TISTORY_USERNAME, TISTORY_PASSWORD가 설정되지 않았습니다")
                print("💡 .env 파일에 다음과 같이 설정하세요:")
                print("   TISTORY_USERNAME=your_username")
                print("   TISTORY_PASSWORD=your_password")
                return False
            
            print("🔑 환경변수에서 로그인 정보 로드 완료")
            
            # 로그인 페이지 접속
            print("🌐 로그인 페이지 접속 중...")
            self.driver.get("https://www.tistory.com/auth/login")
            time.sleep(5)  # 페이지 로딩 시간 증가
            
            # 페이지 분석 - 현재 로그인 페이지 구조 파악
            print("🔍 페이지 구조 분석 중...")
            page_analysis = self.driver.execute_script("""
                var analysis = {
                    title: document.title,
                    url: window.location.href,
                    loginButtons: [],
                    inputFields: [],
                    forms: []
                };
                
                // 로그인 버튼들 찾기
                var loginBtns = document.querySelectorAll('a, button');
                for (var i = 0; i < loginBtns.length; i++) {
                    var btn = loginBtns[i];
                    var text = btn.textContent || btn.innerText || '';
                    var href = btn.href || '';
                    var className = btn.className || '';
                    
                    if (text.includes('카카오') || text.includes('로그인') || 
                        href.includes('kakao') || className.includes('kakao') ||
                        href.includes('login') || className.includes('login')) {
                        analysis.loginButtons.push({
                            tag: btn.tagName,
                            text: text.trim(),
                            href: href,
                            className: className,
                            id: btn.id || ''
                        });
                    }
                }
                
                // 입력 필드들 찾기
                var inputs = document.querySelectorAll('input');
                for (var i = 0; i < inputs.length; i++) {
                    var input = inputs[i];
                    analysis.inputFields.push({
                        type: input.type,
                        name: input.name || '',
                        id: input.id || '',
                        placeholder: input.placeholder || '',
                        className: input.className || ''
                    });
                }
                
                // 폼 찾기
                var forms = document.querySelectorAll('form');
                for (var i = 0; i < forms.length; i++) {
                    var form = forms[i];
                    analysis.forms.push({
                        action: form.action || '',
                        method: form.method || '',
                        className: form.className || '',
                        id: form.id || ''
                    });
                }
                
                return analysis;
            """)
            
            print(f"📄 페이지 제목: {page_analysis['title']}")
            print(f"🌐 현재 URL: {page_analysis['url']}")
            print(f"🔘 로그인 버튼 {len(page_analysis['loginButtons'])}개 발견")
            print(f"📝 입력 필드 {len(page_analysis['inputFields'])}개 발견")
            
            # 로그인 버튼 정보 출력
            for i, btn in enumerate(page_analysis['loginButtons'][:5]):  # 상위 5개만
                print(f"  버튼 {i+1}: {btn['tag']} - '{btn['text'][:30]}' (class: {btn['className'][:20]})")
            
            # 입력 필드 정보 출력
            for i, field in enumerate(page_analysis['inputFields'][:10]):  # 상위 10개만
                print(f"  필드 {i+1}: {field['type']} - name:{field['name']} id:{field['id']} placeholder:{field['placeholder'][:20]}")
            
            # 카카오 로그인 버튼 클릭 시도 (다양한 방법)
            kakao_login_success = False
            
            # 방법 1: 다양한 선택자로 카카오 로그인 버튼 찾기
            kakao_selectors = [
                "a[href*='kakao']",
                "button[data-service='kakao']", 
                ".btn_login[data-service='kakao']",
                ".login_kakao",
                "a[title*='카카오']",
                "a[alt*='카카오']",
                ".kakao",
                "[class*='kakao']",
                "a[href*='accounts.kakao.com']",
                "a.link_kakao",
                ".btn-kakao"
            ]
            
            for selector in kakao_selectors:
                try:
                    kakao_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if kakao_elements:
                        kakao_btn = kakao_elements[0]
                        print(f"🎯 카카오 로그인 버튼 발견: {selector}")
                        kakao_btn.click()
                        print("✅ 카카오 로그인 버튼 클릭 성공")
                        time.sleep(5)
                        kakao_login_success = True
                        break
                except Exception as e:
                    continue
            
            # 방법 2: JavaScript로 카카오 로그인 버튼 찾기
            if not kakao_login_success:
                print("🔍 JavaScript로 카카오 로그인 버튼 찾기 시도...")
                js_result = self.driver.execute_script("""
                    var buttons = document.querySelectorAll('a, button');
                    for (var i = 0; i < buttons.length; i++) {
                        var btn = buttons[i];
                        var text = (btn.textContent || btn.innerText || '').toLowerCase();
                        var href = (btn.href || '').toLowerCase();
                        var className = (btn.className || '').toLowerCase();
                        
                        if (text.includes('카카오') || text.includes('kakao') || 
                            href.includes('kakao') || className.includes('kakao')) {
                            btn.click();
                            return {success: true, method: 'text_search', text: text, href: href};
                        }
                    }
                    return {success: false};
                """)
                
                if js_result and js_result.get('success'):
                    print(f"✅ JavaScript로 카카오 로그인 버튼 클릭: {js_result.get('method')}")
                    time.sleep(5)
                    kakao_login_success = True
                else:
                    print("⚠️ 카카오 로그인 버튼을 찾지 못했습니다. 직접 로그인 시도...")
            
            # 로그인 필드 입력 시도 (다양한 선택자)
            username_selectors = [
                "#loginKey",
                "#loginId", 
                "input[name='loginId']",
                "input[name='username']",
                "input[name='email']",
                "input[type='email']",
                "input[type='text']",
                "input[placeholder*='아이디']",
                "input[placeholder*='이메일']",
                "input[placeholder*='ID']",
                ".input_id",
                ".login_input",
                "#id",
                "#email"
            ]
            
            username_input_success = False
            
            print("🔍 아이디 입력 필드 찾기 시도...")
            for selector in username_selectors:
                try:
                    username_fields = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if username_fields:
                        # 보이는 필드만 선택
                        for field in username_fields:
                            if field.is_displayed() and field.is_enabled():
                                field.clear()
                                field.send_keys(username)
                                print(f"✏️ 아이디 입력 성공: {selector}")
                                username_input_success = True
                                break
                        if username_input_success:
                            break
                except Exception as e:
                    continue
            
            if not username_input_success:
                print("❌ 아이디 입력 필드를 찾을 수 없습니다")
                
                # 모든 입력 필드 다시 분석
                print("🔍 모든 입력 필드 재분석...")
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                visible_inputs = []
                
                for i, inp in enumerate(all_inputs):
                    try:
                        if inp.is_displayed() and inp.is_enabled():
                            inp_type = inp.get_attribute("type") or "text"
                            inp_name = inp.get_attribute("name") or ""
                            inp_id = inp.get_attribute("id") or ""
                            inp_placeholder = inp.get_attribute("placeholder") or ""
                            
                            visible_inputs.append({
                                'index': i,
                                'element': inp,
                                'type': inp_type,
                                'name': inp_name,
                                'id': inp_id,
                                'placeholder': inp_placeholder
                            })
                            
                            print(f"  가능한 필드 {i}: type={inp_type}, name={inp_name}, id={inp_id}, placeholder={inp_placeholder}")
                    except:
                        continue
                
                # 첫 번째 보이는 텍스트 필드에 시도
                if visible_inputs:
                    for inp_info in visible_inputs:
                        if inp_info['type'] in ['text', 'email']:
                            try:
                                inp_info['element'].clear()
                                inp_info['element'].send_keys(username)
                                print(f"✏️ 첫 번째 텍스트 필드에 아이디 입력 성공")
                                username_input_success = True
                                break
                            except:
                                continue
            
            if not username_input_success:
                print("❌ 아이디 입력 완전 실패")
                return False
            
            time.sleep(1)
            
            # 비밀번호 입력 시도
            password_selectors = [
                "#password",
                "input[name='password']",
                "input[type='password']",
                "input[placeholder*='비밀번호']",
                "input[placeholder*='Password']",
                ".input_password",
                ".login_password",
                "#pw"
            ]
            
            password_input_success = False
            
            print("🔍 비밀번호 입력 필드 찾기 시도...")
            for selector in password_selectors:
                try:
                    password_fields = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if password_fields:
                        for field in password_fields:
                            if field.is_displayed() and field.is_enabled():
                                field.clear()
                                field.send_keys(password)
                                print(f"🔒 비밀번호 입력 성공: {selector}")
                                password_input_success = True
                                break
                        if password_input_success:
                            break
                except Exception as e:
                    continue
            
            if not password_input_success:
                # 모든 password 타입 필드에 시도
                password_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
                for field in password_fields:
                    try:
                        if field.is_displayed() and field.is_enabled():
                            field.clear()
                            field.send_keys(password)
                            print("🔒 비밀번호 입력 성공 (타입 기반)")
                            password_input_success = True
                            break
                    except:
                        continue
            
            if not password_input_success:
                print("❌ 비밀번호 입력 실패")
                return False
            
            time.sleep(1)
            
            # 로그인 버튼 클릭 시도
            login_button_selectors = [
                "button[type='submit']",
                ".btn_login",
                ".btn_confirm", 
                ".submit",
                "button.login",
                "input[type='submit']",
                ".login_btn",
                ".btn-login",
                "button[onclick*='login']",
                "form button"
            ]
            
            login_button_success = False
            
            print("🔍 로그인 버튼 찾기 시도...")
            for selector in login_button_selectors:
                try:
                    login_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if login_buttons:
                        for btn in login_buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                btn.click()
                                print(f"🚀 로그인 버튼 클릭 성공: {selector}")
                                login_button_success = True
                                break
                        if login_button_success:
                            break
                except Exception as e:
                    continue
            
            if not login_button_success:
                # JavaScript로 폼 제출 시도
                print("🔍 JavaScript로 폼 제출 시도...")
                form_submit_result = self.driver.execute_script("""
                    var forms = document.querySelectorAll('form');
                    for (var i = 0; i < forms.length; i++) {
                        try {
                            forms[i].submit();
                            return {success: true, method: 'form_submit'};
                        } catch(e) {
                            continue;
                        }
                    }
                    
                    // 버튼 클릭 시도
                    var buttons = document.querySelectorAll('button, input[type="submit"]');
                    for (var i = 0; i < buttons.length; i++) {
                        try {
                            if (buttons[i].offsetParent !== null) { // 보이는 버튼만
                                buttons[i].click();
                                return {success: true, method: 'button_click'};
                            }
                        } catch(e) {
                            continue;
                        }
                    }
                    
                    return {success: false};
                """)
                
                if form_submit_result and form_submit_result.get('success'):
                    print(f"✅ JavaScript로 로그인 시도: {form_submit_result.get('method')}")
                    login_button_success = True
                else:
                    print("❌ 로그인 버튼 클릭 실패")
                    return False
            
            # 로그인 결과 확인
            print("⏳ 로그인 처리 대기 중...")
            time.sleep(8)  # 로그인 처리 시간 증가
            
            # 2단계 인증이나 추가 확인 처리
            self.handle_alerts()
            
            # 현재 URL 확인
            current_url = self.driver.current_url
            print(f"🌐 로그인 후 URL: {current_url}")
            
            # 로그인 성공 여부 다양한 방법으로 확인
            login_success_indicators = []
            
            # URL 기반 확인
            if "login" not in current_url.lower() and "auth" not in current_url.lower():
                login_success_indicators.append("url_check")
            
            # 페이지 요소 확인
            success_elements = self.driver.execute_script("""
                var indicators = [];
                
                // 로그아웃 버튼 확인
                if (document.querySelector('a[href*="logout"], .logout, .btn-logout')) {
                    indicators.push('logout_button');
                }
                
                // 사용자 정보 확인
                if (document.querySelector('.user-info, .username, .profile')) {
                    indicators.push('user_info');
                }
                
                // 티스토리 관리 메뉴 확인
                if (document.querySelector('.admin, .manage, .dashboard')) {
                    indicators.push('admin_menu');
                }
                
                // 글쓰기 버튼 확인
                if (document.querySelector('a[href*="newpost"], .write, .post')) {
                    indicators.push('write_button');
                }
                
                return indicators;
            """)
            
            login_success_indicators.extend(success_elements)
            
            if login_success_indicators:
                print(f"✅ 로그인 성공! 확인 요소: {', '.join(login_success_indicators)}")
                
                # 세션 정보 저장
                self.save_cookies()
                self.save_local_storage()
                
                return True
            else:
                print("❌ 로그인 실패 - 성공 지표를 찾을 수 없음")
                
                # 오류 메시지 확인
                error_messages = self.driver.execute_script("""
                    var errors = [];
                    var errorElements = document.querySelectorAll('.error, .alert, .warning, [class*="error"]');
                    for (var i = 0; i < errorElements.length; i++) {
                        var text = errorElements[i].textContent || errorElements[i].innerText;
                        if (text && text.trim()) {
                            errors.push(text.trim());
                        }
                    }
                    return errors;
                """)
                
                if error_messages:
                    print(f"⚠️ 오류 메시지: {', '.join(error_messages[:3])}")
                
                return False
                
        except Exception as e:
            print(f"❌ 자동 로그인 중 전체 오류 발생: {e}")
            return False
    
    def try_auto_login(self):
        """저장된 세션으로 자동 로그인 시도"""
        print("\n🔄 자동 로그인 시도 중...")
        
        # 쿠키와 로컬 스토리지 로드
        cookie_loaded = self.load_cookies()
        storage_loaded = self.load_local_storage()
        
        if not cookie_loaded and not storage_loaded:
            print("❌ 저장된 세션 정보가 없습니다")
            return False
        
        # 로그인 상태 확인
        if self.is_logged_in():
            print("✅ 자동 로그인 성공!")
            return True
        else:
            print("❌ 세션이 만료되었습니다")
            return False
    
    def full_auto_login(self):
        """완전 자동 로그인 (세션 -> 자격 증명 순서)"""
        print("\n🚀 완전 자동 로그인 시작")
        
        # 1단계: 저장된 세션으로 시도
        if self.try_auto_login():
            return True
        
        # 2단계: 자격 증명으로 로그인
        print("\n🔑 자격 증명으로 로그인 시도...")
        if self.login_with_credentials():
            return True
        
        print("❌ 모든 자동 로그인 방법이 실패했습니다")
        return False
    
    def test_login_status(self):
        """현재 로그인 상태 테스트"""
        print("\n🔍 로그인 상태 테스트 중...")
        
        if self.is_logged_in():
            print("✅ 현재 로그인 상태입니다")
            
            # 추가 정보 수집
            try:
                page_title = self.driver.title
                current_url = self.driver.current_url
                print(f"📄 페이지 제목: {page_title}")
                print(f"🌐 현재 URL: {current_url}")
                
                # 사용자 정보 확인
                user_info = self.driver.execute_script("""
                    var userElements = document.querySelectorAll('.username, .user-info, .profile-name, .my-name');
                    if (userElements.length > 0) {
                        return userElements[0].textContent.trim();
                    }
                    return null;
                """)
                
                if user_info:
                    print(f"👤 사용자 정보: {user_info}")
                
            except Exception as e:
                print(f"⚠️  추가 정보 수집 실패: {e}")
                
            return True
        else:
            print("❌ 현재 로그인되어 있지 않습니다")
            return False
    
    def close(self):
        """웹드라이버 종료"""
        if self.driver:
            self.driver.quit()
            print("🔚 웹드라이버 종료")

def main():
    """테스트 메인 함수"""
    print("=" * 50)
    print("🤖 티스토리 자동 로그인 테스트")
    print("=" * 50)
    
    # 헤드리스 모드 선택
    headless_mode = input("헤드리스 모드로 실행하시겠습니까? (y/n, 기본값: n): ").lower() == 'y'
    
    auto_login = TistoryAutoLogin(headless=headless_mode)
    
    try:
        # 테스트 메뉴
        while True:
            print("\n" + "=" * 40)
            print("📋 테스트 메뉴")
            print("=" * 40)
            print("1. 완전 자동 로그인 테스트")
            print("2. 저장된 세션으로 로그인 테스트")
            print("3. 자격 증명으로 로그인 테스트")
            print("4. 현재 로그인 상태 확인")
            print("5. 쿠키 저장")
            print("6. 쿠키 로드")
            print("0. 종료")
            
            choice = input("\n선택하세요 (0-6): ").strip()
            
            if choice == '1':
                auto_login.full_auto_login()
            elif choice == '2':
                auto_login.try_auto_login()
            elif choice == '3':
                auto_login.login_with_credentials()
            elif choice == '4':
                auto_login.test_login_status()
            elif choice == '5':
                auto_login.save_cookies()
                auto_login.save_local_storage()
            elif choice == '6':
                auto_login.load_cookies()
                auto_login.load_local_storage()
            elif choice == '0':
                print("👋 테스트를 종료합니다")
                break
            else:
                print("❌ 잘못된 선택입니다")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다")
    
    finally:
        auto_login.close()

if __name__ == "__main__":
    main() 