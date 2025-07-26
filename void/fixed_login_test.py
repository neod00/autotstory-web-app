#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

class FixedTistoryLogin:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("✅ 웹드라이버 설정 완료")
    
    def login_step_by_step(self):
        try:
            username = os.getenv("TISTORY_USERNAME")
            password = os.getenv("TISTORY_PASSWORD")
            
            if not username or not password:
                print("❌ 환경변수 설정 필요")
                return False
            
            print("🚀 단계별 로그인 시작")
            
            # 1단계: 로그인 페이지 접속
            print("1️⃣ 티스토리 로그인 페이지 접속...")
            self.driver.get("https://www.tistory.com/auth/login")
            time.sleep(8)  # 충분한 로딩 시간
            
            # 2단계: 카카오 로그인 버튼 클릭
            print("2️⃣ 카카오 로그인 버튼 클릭...")
            
            # 분석 결과를 바탕으로 정확한 선택자 사용
            kakao_clicked = False
            
            # 방법 1: CSS 선택자
            try:
                kakao_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn_login.link_kakao_id")
                kakao_btn.click()
                print("✅ 카카오 버튼 클릭 성공 (CSS)")
                kakao_clicked = True
            except:
                pass
            
            # 방법 2: XPath
            if not kakao_clicked:
                try:
                    kakao_btn = self.driver.find_element(By.XPATH, "//a[contains(text(), '카카오계정으로 로그인')]")
                    kakao_btn.click()
                    print("✅ 카카오 버튼 클릭 성공 (XPath)")
                    kakao_clicked = True
                except:
                    pass
            
            # 방법 3: JavaScript
            if not kakao_clicked:
                js_result = self.driver.execute_script("""
                    var buttons = document.querySelectorAll('a');
                    for (var i = 0; i < buttons.length; i++) {
                        var btn = buttons[i];
                        if (btn.textContent.includes('카카오계정으로 로그인')) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                """)
                
                if js_result:
                    print("✅ 카카오 버튼 클릭 성공 (JS)")
                    kakao_clicked = True
            
            if not kakao_clicked:
                print("❌ 카카오 버튼 클릭 실패")
                return False
            
            # 3단계: 카카오 로그인 페이지 로딩 대기
            print("3️⃣ 카카오 페이지 로딩 대기...")
            time.sleep(10)
            
            print(f"🌐 현재 URL: {self.driver.current_url}")
            
            # 4단계: 아이디 입력
            print("4️⃣ 아이디 입력...")
            
            username_selectors = [
                "#loginId",
                "#loginKey", 
                "input[name='email']",
                "input[name='loginId']",
                "input[type='email']",
                "input[type='text']"
            ]
            
            username_success = False
            for selector in username_selectors:
                try:
                    field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if field.is_displayed() and field.is_enabled():
                        field.clear()
                        field.send_keys(username)
                        print(f"✅ 아이디 입력 성공: {selector}")
                        username_success = True
                        break
                except:
                    continue
            
            if not username_success:
                print("❌ 아이디 입력 실패")
                return False
            
            time.sleep(1)
            
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
            
            time.sleep(1)
            
            # 6단계: 로그인 버튼 클릭
            print("6️⃣ 로그인 버튼 클릭...")
            
            login_selectors = [
                "button[type='submit']",
                ".btn_confirm",
                ".btn-login"
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_displayed() and btn.is_enabled():
                        btn.click()
                        print(f"✅ 로그인 버튼 클릭: {selector}")
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                # JavaScript로 폼 제출
                self.driver.execute_script("document.querySelector('form').submit();")
                print("✅ JavaScript로 폼 제출")
            
            # 7단계: 결과 확인
            print("7️⃣ 로그인 결과 확인...")
            time.sleep(10)
            
            final_url = self.driver.current_url
            print(f"🌐 최종 URL: {final_url}")
            
            if "login" not in final_url.lower():
                print("✅ 로그인 성공!")
                self.save_cookies()
                return True
            else:
                print("❌ 로그인 실패")
                return False
                
        except Exception as e:
            print(f"❌ 오류: {e}")
            return False
    
    def save_cookies(self):
        try:
            cookies = self.driver.get_cookies()
            with open('fixed_cookies.pkl', 'wb') as f:
                pickle.dump(cookies, f)
            print(f"✅ 쿠키 저장 완료")
        except Exception as e:
            print(f"❌ 쿠키 저장 실패: {e}")
    
    def close(self):
        if self.driver:
            self.driver.quit()
            print("🔚 브라우저 종료")

def main():
    print("🤖 수정된 티스토리 로그인 테스트")
    
    username = os.getenv("TISTORY_USERNAME")
    password = os.getenv("TISTORY_PASSWORD")
    
    if not username or not password:
        print("❌ .env 파일에 로그인 정보 설정 필요")
        return
    
    print(f"📧 아이디: {username[:3]}***")
    
    login_test = FixedTistoryLogin(headless=False)
    
    try:
        success = login_test.login_step_by_step()
        
        if success:
            print("\n🎉 로그인 성공!")
        else:
            print("\n❌ 로그인 실패")
    
    finally:
        input("\nEnter 키를 누르면 종료됩니다...")
        login_test.close()

if __name__ == "__main__":
    main() 