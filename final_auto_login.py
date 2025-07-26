#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 티스토리 자동 로그인
2단계 인증 (핸드폰 승인) 대기 기능 포함
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

class FinalTistoryLogin:
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
    
    def complete_login(self):
        """완전 자동 로그인 (2단계 인증 포함)"""
        try:
            username = os.getenv("TISTORY_USERNAME")
            password = os.getenv("TISTORY_PASSWORD")
            
            if not username or not password:
                print("❌ 환경변수 설정 필요")
                return False
            
            print("🎯 최종 로그인 시작")
            print("=" * 50)
            
            # 1단계: 로그인 페이지 접속
            print("1️⃣ 티스토리 로그인 페이지 접속...")
            self.driver.get("https://www.tistory.com/auth/login")
            
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(3)
            
            # 2단계: 카카오 버튼 클릭
            print("2️⃣ 카카오 로그인 버튼 클릭...")
            
            try:
                kakao_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn_login.link_kakao_id"))
                )
                kakao_btn.click()
                print("✅ 카카오 버튼 클릭 성공")
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
                    print("❌ 카카오 버튼 클릭 실패")
                    return False
                print("✅ 카카오 버튼 클릭 성공 (JS)")
            
            # 3단계: 카카오 페이지 로딩 대기
            print("3️⃣ 카카오 페이지 로딩...")
            
            WebDriverWait(self.driver, 15).until(
                lambda driver: "kakao" in driver.current_url.lower() or 
                              len(driver.find_elements(By.CSS_SELECTOR, "input[name='loginId']")) > 0
            )
            time.sleep(3)
            
            # 4단계: 아이디 입력
            print("4️⃣ 아이디 입력...")
            try:
                username_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='loginId']")
                username_field.clear()
                username_field.send_keys(username)
                print("✅ 아이디 입력 성공")
            except:
                print("❌ 아이디 입력 실패")
                return False
            
            # 5단계: 비밀번호 입력
            print("5️⃣ 비밀번호 입력...")
            try:
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                password_field.clear()
                password_field.send_keys(password)
                print("✅ 비밀번호 입력 성공")
            except:
                print("❌ 비밀번호 입력 실패")
                return False
            
            # 6단계: 로그인 버튼 클릭
            print("6️⃣ 로그인 버튼 클릭...")
            try:
                login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_btn.click()
                print("✅ 로그인 버튼 클릭 성공")
            except:
                print("❌ 로그인 버튼 클릭 실패")
                return False
            
            # 7단계: 2단계 인증 처리
            print("7️⃣ 2단계 인증 확인...")
            time.sleep(5)
            
            current_url = self.driver.current_url
            
            if "tmsTwoStepVerification" in current_url or "verification" in current_url.lower():
                print("📱 2단계 인증 필요!")
                print("=" * 50)
                print("🔔 핸드폰에서 카카오톡 알림을 확인하여 로그인을 승인해주세요!")
                print("   - 최대 3분 동안 자동으로 대기합니다")
                print("   - 승인 후 자동으로 다음 단계로 진행됩니다")
                print("=" * 50)
                
                if self.wait_for_approval(max_wait_minutes=3):
                    print("✅ 2단계 인증 승인 완료!")
                else:
                    print("❌ 2단계 인증 승인 시간 초과")
                    return False
            else:
                print("ℹ️ 2단계 인증 불필요")
            
            # 8단계: OAuth 승인 "계속하기" 버튼 클릭
            print("8️⃣ OAuth 승인 확인...")
            time.sleep(3)
            
            # "계속하기" 버튼 찾기 및 클릭
            continue_clicked = False
            try:
                # 정확한 선택자로 "계속하기" 버튼 찾기
                continue_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn_agree[name='user_oauth_approval'][value='true']")
                if continue_btn and continue_btn.is_displayed() and continue_btn.is_enabled():
                    continue_btn.click()
                    print("✅ '계속하기' 버튼 클릭 성공")
                    continue_clicked = True
                else:
                    print("⚠️ '계속하기' 버튼이 비활성화되어 있습니다")
            except:
                print("ℹ️ '계속하기' 버튼을 찾을 수 없습니다 (OAuth 승인 불필요)")
            
            # 대안 방법으로 JavaScript 사용
            if not continue_clicked:
                try:
                    js_result = self.driver.execute_script("""
                        var continueBtn = document.querySelector('button.btn_agree[name="user_oauth_approval"][value="true"]');
                        if (continueBtn && continueBtn.offsetParent !== null) {
                            continueBtn.click();
                            return {success: true, found: true};
                        }
                        
                        // 대안: 텍스트로 찾기
                        var buttons = document.querySelectorAll('button');
                        for (var i = 0; i < buttons.length; i++) {
                            var btn = buttons[i];
                            if (btn.textContent.includes('계속하기') || btn.textContent.includes('계속')) {
                                btn.click();
                                return {success: true, found: true, method: 'text_search'};
                            }
                        }
                        
                        return {success: false, found: false};
                    """)
                    
                    if js_result and js_result.get('success'):
                        print("✅ '계속하기' 버튼 클릭 성공 (JavaScript)")
                        continue_clicked = True
                    else:
                        print("ℹ️ '계속하기' 버튼이 없습니다 (OAuth 승인 단계 생략)")
                except Exception as e:
                    print(f"⚠️ JavaScript 클릭 시도 중 오류: {e}")
            
            # 9단계: 최종 확인
            print("9️⃣ 최종 로그인 확인...")
            time.sleep(5)
            
            if self.check_login_success():
                print("🎉 완전 로그인 성공!")
                self.save_cookies()
                return True
            else:
                print("❌ 로그인 실패")
                return False
                
        except Exception as e:
            print(f"❌ 로그인 중 오류: {e}")
            return False
    
    def wait_for_approval(self, max_wait_minutes=3):
        """2단계 인증 승인 대기"""
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        check_interval = 5
        
        while time.time() - start_time < max_wait_seconds:
            try:
                current_url = self.driver.current_url
                
                # URL 변경 확인 (승인 완료 시)
                if "tmsTwoStepVerification" not in current_url and "verification" not in current_url.lower():
                    print("✅ 승인 완료 - URL 변경 감지!")
                    return True
                
                # 진행 상황 표시
                elapsed = int(time.time() - start_time)
                remaining = max_wait_seconds - elapsed
                
                if elapsed % 15 == 0:  # 15초마다 상태 출력
                    print(f"⏳ 승인 대기 중... (경과: {elapsed}초, 남은: {remaining}초)")
                
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"⚠️ 대기 중 오류: {e}")
                time.sleep(check_interval)
        
        return False
    
    def check_login_success(self):
        """로그인 성공 확인"""
        try:
            current_url = self.driver.current_url
            print(f"🌐 최종 URL: {current_url}")
            
            # URL 기반 확인
            if "login" not in current_url.lower() and "auth" not in current_url.lower():
                return True
            
            # 간단한 요소 확인
            success_elements = self.driver.execute_script("""
                if (document.querySelector('a[href*="logout"]') || 
                    document.querySelector('.logout') ||
                    (document.title.includes('TISTORY') && !document.title.includes('로그인'))) {
                    return true;
                }
                return false;
            """)
            
            return success_elements
            
        except:
            # URL만으로 판단
            current_url = self.driver.current_url
            return "login" not in current_url.lower() and "auth" not in current_url.lower()
    
    def save_cookies(self):
        """쿠키 저장"""
        try:
            cookies = self.driver.get_cookies()
            tistory_cookies = [c for c in cookies if 'tistory.com' in c.get('domain', '') or 'kakao.com' in c.get('domain', '')]
            
            if tistory_cookies:
                with open('final_cookies.pkl', 'wb') as f:
                    pickle.dump(tistory_cookies, f)
                print(f"✅ {len(tistory_cookies)}개 쿠키 저장")
                return True
            return False
        except Exception as e:
            print(f"❌ 쿠키 저장 실패: {e}")
            return False
    
    def close(self):
        if self.driver:
            self.driver.quit()
            print("🔚 브라우저 종료")

def main():
    print("🎯 최종 티스토리 자동 로그인")
    print("(2단계 인증 지원)")
    print("=" * 50)
    
    username = os.getenv("TISTORY_USERNAME")
    password = os.getenv("TISTORY_PASSWORD")
    
    if not username or not password:
        print("❌ .env 파일에 로그인 정보 설정 필요")
        return
    
    # 마스킹된 정보 표시
    if '@' in username:
        masked = f"{username[:2]}***@{username.split('@')[1]}"
    else:
        masked = f"{username[:2]}***"
    
    print(f"📧 아이디: {masked}")
    print("📱 2단계 인증 대기 기능 활성화")
    print()
    
    login_test = FinalTistoryLogin(headless=False)
    
    try:
        success = login_test.complete_login()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 완전 자동 로그인 성공!")
            print("✅ 메인 프로그램 적용 준비 완료!")
        else:
            print("❌ 로그인 실패")
    
    finally:
        input("\nEnter 키를 누르면 종료됩니다...")
        login_test.close()

if __name__ == "__main__":
    main() 