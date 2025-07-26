#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스마트 티스토리 로그인 테스트
분석 결과 기반으로 올바른 로그인 시퀀스 구현
"""

import os
import time
import pickle
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

class SmartTistoryLogin:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        """웹드라이버 설정"""
        options = webdriver.ChromeOptions()
        
        if self.headless:
            options.add_argument("--headless")
        
        # 자동화 감지 우회
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("✅ 웹드라이버 설정 완료")
    
    def smart_login(self):
        """스마트 로그인 프로세스"""
        try:
            username = os.getenv("TISTORY_USERNAME")
            password = os.getenv("TISTORY_PASSWORD")
            
            if not username or not password:
                print("❌ 환경변수 TISTORY_USERNAME, TISTORY_PASSWORD 설정 필요")
                return False
            
            print("🧠 스마트 로그인 시작")
            print("=" * 50)
            
            # 1단계: 티스토리 로그인 페이지 접속
            print("1️⃣ 티스토리 로그인 페이지 접속...")
            self.driver.get("https://www.tistory.com/auth/login")
            
            # 페이지 완전 로딩 대기 (JavaScript 실행까지)
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(5)  # 추가 안정성 대기
            
            print(f"📄 현재 페이지: {self.driver.title}")
            print(f"🌐 현재 URL: {self.driver.current_url}")
            
            # 2단계: 카카오 로그인 버튼 클릭 (분석 결과 기반)
            print("2️⃣ 카카오 로그인 버튼 클릭...")
            
            kakao_clicked = False
            
            # 방법 1: 분석에서 발견된 정확한 클래스 사용
            try:
                kakao_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn_login.link_kakao_id"))
                )
                kakao_btn.click()
                print("✅ 카카오 버튼 클릭 성공 (정확한 클래스)")
                kakao_clicked = True
            except Exception as e:
                print(f"방법 1 실패: {e}")
            
            # 방법 2: XPath로 텍스트 기반 검색
            if not kakao_clicked:
                try:
                    kakao_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '카카오계정으로 로그인')]"))
                    )
                    kakao_btn.click()
                    print("✅ 카카오 버튼 클릭 성공 (XPath)")
                    kakao_clicked = True
                except Exception as e:
                    print(f"방법 2 실패: {e}")
            
            # 방법 3: JavaScript 강제 클릭
            if not kakao_clicked:
                print("🔧 JavaScript로 카카오 버튼 찾기...")
                js_result = self.driver.execute_script("""
                    var links = document.querySelectorAll('a');
                    for (var i = 0; i < links.length; i++) {
                        var link = links[i];
                        var text = link.textContent || link.innerText || '';
                        var className = link.className || '';
                        
                        if (text.includes('카카오계정으로 로그인') || 
                            className.includes('link_kakao_id') ||
                            className.includes('btn_login')) {
                            
                            // 클릭 전 정보 수집
                            var info = {
                                text: text.trim(),
                                class: className,
                                href: link.href || ''
                            };
                            
                            link.click();
                            return {success: true, info: info};
                        }
                    }
                    return {success: false, message: 'No kakao button found'};
                """)
                
                if js_result and js_result.get('success'):
                    btn_info = js_result.get('info', {})
                    print(f"✅ JavaScript로 카카오 버튼 클릭:")
                    print(f"   텍스트: {btn_info.get('text', 'N/A')}")
                    print(f"   클래스: {btn_info.get('class', 'N/A')}")
                    kakao_clicked = True
                else:
                    print(f"❌ JavaScript 클릭 실패: {js_result.get('message', 'Unknown error')}")
            
            if not kakao_clicked:
                print("❌ 모든 방법으로 카카오 버튼 클릭 실패")
                return False
            
            # 3단계: 카카오 로그인 페이지로 이동 확인
            print("3️⃣ 카카오 로그인 페이지 로딩 대기...")
            
            # URL 변경 또는 새로운 페이지 로딩까지 대기
            WebDriverWait(self.driver, 15).until(
                lambda driver: "kakao" in driver.current_url.lower() or 
                              len(driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email']")) > 0
            )
            
            time.sleep(3)  # 추가 로딩 시간
            
            current_url = self.driver.current_url
            print(f"🌐 이동 후 URL: {current_url}")
            
            # 4단계: 현재 페이지 입력 필드 분석
            print("4️⃣ 입력 필드 분석...")
            
            input_fields = self.driver.execute_script("""
                var inputs = document.querySelectorAll('input');
                var result = [];
                
                for (var i = 0; i < inputs.length; i++) {
                    var input = inputs[i];
                    // 보이는 필드만 선택
                    if (input.offsetParent !== null && input.offsetWidth > 0 && input.offsetHeight > 0) {
                        result.push({
                            type: input.type || '',
                            name: input.name || '',
                            id: input.id || '',
                            placeholder: input.placeholder || '',
                            className: input.className || '',
                            index: i
                        });
                    }
                }
                return result;
            """)
            
            print(f"📝 발견된 입력 필드 {len(input_fields)}개:")
            for i, field in enumerate(input_fields):
                print(f"  필드 {i+1}: {field['type']} | name: '{field['name']}' | id: '{field['id']}' | placeholder: '{field['placeholder']}' | class: '{field['className']}'")
            
            if not input_fields:
                print("❌ 입력 필드를 찾을 수 없습니다")
                return False
            
            # 5단계: 아이디 필드 찾기 및 입력
            print("5️⃣ 아이디 입력...")
            
            # 스마트 아이디 필드 감지
            username_selectors = [
                "#loginId",
                "#loginKey", 
                "#id",
                "input[name='email']",
                "input[name='loginId']",
                "input[name='username']",
                "input[name='id']",
                "input[type='email']",
                "input[type='text']",
                "input[placeholder*='이메일']",
                "input[placeholder*='아이디']",
                "input[placeholder*='ID']"
            ]
            
            username_success = False
            
            # 정확한 선택자로 시도
            for selector in username_selectors:
                try:
                    username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if username_field and username_field.is_displayed() and username_field.is_enabled():
                        username_field.clear()
                        username_field.send_keys(username)
                        print(f"✅ 아이디 입력 성공: {selector}")
                        username_success = True
                        break
                except:
                    continue
            
            # 첫 번째 텍스트/이메일 필드에 시도
            if not username_success and input_fields:
                try:
                    first_text_field_index = 0
                    for field in input_fields:
                        if field['type'] in ['text', 'email', '']:
                            first_text_field_index = field['index']
                            break
                    
                    username_field = self.driver.find_elements(By.CSS_SELECTOR, "input")[first_text_field_index]
                    username_field.clear()
                    username_field.send_keys(username)
                    print("✅ 첫 번째 텍스트 필드에 아이디 입력")
                    username_success = True
                except Exception as e:
                    print(f"첫 번째 필드 입력 실패: {e}")
            
            if not username_success:
                print("❌ 아이디 입력 실패")
                return False
            
            time.sleep(1)
            
            # 6단계: 비밀번호 입력
            print("6️⃣ 비밀번호 입력...")
            
            password_selectors = [
                "#password",
                "input[name='password']",
                "input[type='password']",
                "input[placeholder*='비밀번호']"
            ]
            
            password_success = False
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_field and password_field.is_displayed() and password_field.is_enabled():
                        password_field.clear()
                        password_field.send_keys(password)
                        print(f"✅ 비밀번호 입력 성공: {selector}")
                        password_success = True
                        break
                except:
                    continue
            
            if not password_success:
                print("❌ 비밀번호 입력 실패")
                return False
            
            time.sleep(1)
            
            # 7단계: 로그인 버튼 클릭
            print("7️⃣ 로그인 버튼 클릭...")
            
            # 스마트 로그인 버튼 감지
            login_button_selectors = [
                "button[type='submit']",
                ".btn_confirm",
                ".btn-login",
                ".login-btn",
                "input[type='submit']",
                "button:contains('로그인')",
                ".submit",
                ".btn_submit"
            ]
            
            login_success = False
            
            # CSS 선택자로 시도
            for selector in login_button_selectors:
                try:
                    if "contains" in selector:
                        continue  # XPath는 나중에 처리
                    
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_btn and login_btn.is_displayed() and login_btn.is_enabled():
                        login_btn.click()
                        print(f"✅ 로그인 버튼 클릭 성공: {selector}")
                        login_success = True
                        break
                except:
                    continue
            
            # XPath로 시도
            if not login_success:
                try:
                    login_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '로그인')] | //input[@value='로그인']")
                    login_btn.click()
                    print("✅ 로그인 버튼 클릭 성공 (XPath)")
                    login_success = True
                except:
                    pass
            
            # JavaScript로 폼 제출 시도
            if not login_success:
                print("🔧 JavaScript로 폼 제출 시도...")
                js_submit = self.driver.execute_script("""
                    // 모든 폼을 찾아서 제출 시도
                    var forms = document.querySelectorAll('form');
                    for (var i = 0; i < forms.length; i++) {
                        try {
                            forms[i].submit();
                            return {success: true, method: 'form_submit', index: i};
                        } catch(e) {
                            continue;
                        }
                    }
                    
                    // 로그인 관련 버튼을 찾아서 클릭 시도
                    var buttons = document.querySelectorAll('button, input[type="submit"]');
                    for (var i = 0; i < buttons.length; i++) {
                        var btn = buttons[i];
                        var text = btn.textContent || btn.value || '';
                        
                        if (text.includes('로그인') || text.includes('Login') || btn.type === 'submit') {
                            try {
                                btn.click();
                                return {success: true, method: 'button_click', text: text};
                            } catch(e) {
                                continue;
                            }
                        }
                    }
                    
                    return {success: false, message: 'No submit method found'};
                """)
                
                if js_submit and js_submit.get('success'):
                    print(f"✅ JavaScript로 제출 성공: {js_submit.get('method')}")
                    login_success = True
                else:
                    print(f"❌ JavaScript 제출 실패: {js_submit.get('message', 'Unknown error')}")
            
            if not login_success:
                print("❌ 로그인 버튼 클릭/폼 제출 실패")
                return False
            
            # 8단계: 로그인 결과 확인
            print("8️⃣ 로그인 결과 확인 중...")
            
            # 페이지 변경 대기
            time.sleep(10)
            
            final_url = self.driver.current_url
            print(f"🌐 최종 URL: {final_url}")
            
            # 로그인 성공 여부 판단
            success_indicators = []
            
            # URL 기반 확인
            if "login" not in final_url.lower() and "auth" not in final_url.lower():
                success_indicators.append("url_change")
            
            # 요소 기반 확인
            page_elements = self.driver.execute_script("""
                var indicators = [];
                
                // 로그아웃 버튼 확인
                if (document.querySelector('a[href*="logout"], .logout, a:contains("로그아웃")')) {
                    indicators.push('logout_button');
                }
                
                // 사용자 정보 확인
                if (document.querySelector('.user-info, .username, .user-name')) {
                    indicators.push('user_info');
                }
                
                // 글쓰기 버튼 확인
                if (document.querySelector('a[href*="write"], a[href*="post"], .write, .new-post')) {
                    indicators.push('write_button');
                }
                
                // 대시보드 확인
                if (document.querySelector('.dashboard, .admin, .manage')) {
                    indicators.push('dashboard');
                }
                
                return indicators;
            """)
            
            success_indicators.extend(page_elements)
            
            if success_indicators:
                print(f"✅ 로그인 성공! 확인 요소: {', '.join(success_indicators)}")
                
                # 성공 시 쿠키 저장
                self.save_cookies()
                return True
            else:
                print("❌ 로그인 실패 - 성공 지표를 찾을 수 없음")
                return False
                
        except Exception as e:
            print(f"❌ 로그인 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_cookies(self):
        """쿠키 저장"""
        try:
            cookies = self.driver.get_cookies()
            tistory_cookies = [c for c in cookies if 'tistory.com' in c.get('domain', '') or 'kakao.com' in c.get('domain', '')]
            
            if tistory_cookies:
                with open('smart_cookies.pkl', 'wb') as f:
                    pickle.dump(tistory_cookies, f)
                print(f"✅ {len(tistory_cookies)}개 쿠키 저장 완료")
                return True
            else:
                print("⚠️ 저장할 쿠키가 없습니다")
                return False
        except Exception as e:
            print(f"❌ 쿠키 저장 실패: {e}")
            return False
    
    def close(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()
            print("🔚 브라우저 종료")

def main():
    """메인 함수"""
    print("🧠 스마트 티스토리 로그인 테스트")
    print("=" * 60)
    
    # 환경변수 확인
    username = os.getenv("TISTORY_USERNAME")
    password = os.getenv("TISTORY_PASSWORD")
    
    if not username or not password:
        print("❌ .env 파일에 로그인 정보를 설정해주세요:")
        print("   TISTORY_USERNAME=your_email@example.com")
        print("   TISTORY_PASSWORD=your_password")
        return
    
    # 개인정보 보호를 위한 마스킹
    if '@' in username:
        email_parts = username.split('@')
        masked_username = f"{email_parts[0][:2]}***@{email_parts[1]}"
    else:
        masked_username = f"{username[:2]}***"
    
    print(f"📧 설정된 아이디: {masked_username}")
    print(f"🔐 비밀번호: {'*' * len(password)}")
    
    # 로그인 테스트 시작
    login_test = SmartTistoryLogin(headless=False)
    
    try:
        success = login_test.smart_login()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 스마트 로그인 성공!")
            print("이제 자동 로그인 기능을 메인 프로그램에 적용할 수 있습니다.")
        else:
            print("❌ 스마트 로그인 실패")
            print("다음을 확인해주세요:")
            print("  - 아이디/비밀번호가 정확한지")
            print("  - 2단계 인증이 설정되어 있는지")
            print("  - 카카오 계정 로그인이 가능한지")
    
    finally:
        input("\n분석이 완료되었습니다. Enter 키를 누르면 브라우저가 종료됩니다...")
        login_test.close()

if __name__ == "__main__":
    main() 