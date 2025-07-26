#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
티스토리 자동 로그인 테스트 파일
"""

import os
import time
import json
import pickle
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path

# 환경변수 로드
load_dotenv()

# 설정
BLOG_MANAGE_URL = "https://climate-insight.tistory.com/manage/post"
COOKIES_FILE = "test_cookies.pkl"

class TistoryLoginTest:
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
    
    def save_cookies(self):
        """쿠키 저장"""
        try:
            cookies = self.driver.get_cookies()
            tistory_cookies = [c for c in cookies if 'tistory.com' in c.get('domain', '')]
            
            if tistory_cookies:
                with open(COOKIES_FILE, 'wb') as f:
                    pickle.dump(tistory_cookies, f)
                print(f"✅ {len(tistory_cookies)}개 쿠키 저장 완료")
                return True
            return False
        except Exception as e:
            print(f"❌ 쿠키 저장 실패: {e}")
            return False
    
    def load_cookies(self):
        """쿠키 로드"""
        try:
            if not os.path.exists(COOKIES_FILE):
                print("❌ 쿠키 파일이 없습니다")
                return False
            
            self.driver.get("https://www.tistory.com")
            time.sleep(2)
            
            with open(COOKIES_FILE, 'rb') as f:
                cookies = pickle.load(f)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
            
            self.driver.refresh()
            time.sleep(3)
            print(f"✅ 쿠키 로드 완료")
            return True
            
        except Exception as e:
            print(f"❌ 쿠키 로드 실패: {e}")
            return False
    
    def is_logged_in(self):
        """로그인 상태 확인"""
        try:
            self.driver.get(BLOG_MANAGE_URL)
            time.sleep(5)
            
            current_url = self.driver.current_url
            if "login" in current_url.lower():
                print("❌ 로그인 페이지로 리디렉션됨")
                return False
            
            # 관리 페이지 요소 확인
            admin_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                ".dashboard, .admin-area, .manager-area")
            
            if admin_elements:
                print("✅ 로그인 상태 확인됨")
                return True
            else:
                print("❌ 로그인 상태 확인 실패")
                return False
                
        except Exception as e:
            print(f"❌ 로그인 확인 중 오류: {e}")
            return False
    
    def login_with_credentials(self):
        """환경변수 자격증명으로 로그인"""
        username = os.getenv("TISTORY_USERNAME")
        password = os.getenv("TISTORY_PASSWORD")
        
        if not username or not password:
            print("❌ 환경변수 TISTORY_USERNAME, TISTORY_PASSWORD 설정 필요")
            return False
        
        try:
            print("🔑 자격증명 로그인 시작...")
            self.driver.get("https://www.tistory.com/auth/login")
            time.sleep(3)
            
            # 카카오 로그인 버튼 찾기
            try:
                kakao_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='kakao']"))
                )
                kakao_btn.click()
                print("🎯 카카오 로그인 선택")
                time.sleep(3)
            except:
                print("⚠️ 카카오 로그인 버튼 없음")
            
            # 아이디 입력
            try:
                id_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "loginKey"))
                )
                id_field.send_keys(username)
                print("✏️ 아이디 입력 완료")
            except:
                print("❌ 아이디 입력 실패")
                return False
            
            # 비밀번호 입력
            try:
                pw_field = self.driver.find_element(By.ID, "password")
                pw_field.send_keys(password)
                print("🔒 비밀번호 입력 완료")
            except:
                print("❌ 비밀번호 입력 실패")
                return False
            
            # 로그인 버튼 클릭
            try:
                login_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn_confirm")
                login_btn.click()
                print("🚀 로그인 버튼 클릭")
                time.sleep(5)
            except:
                print("❌ 로그인 버튼 클릭 실패")
                return False
            
            # 로그인 성공 확인
            if "login" not in self.driver.current_url.lower():
                print("✅ 로그인 성공!")
                self.save_cookies()
                return True
            else:
                print("❌ 로그인 실패")
                return False
                
        except Exception as e:
            print(f"❌ 로그인 중 오류: {e}")
            return False
    
    def test_auto_login(self):
        """자동 로그인 테스트"""
        print("🔄 자동 로그인 테스트 시작")
        
        # 1단계: 쿠키로 로그인 시도
        if self.load_cookies() and self.is_logged_in():
            print("✅ 쿠키 기반 자동 로그인 성공!")
            return True
        
        # 2단계: 자격증명으로 로그인
        if self.login_with_credentials():
            print("✅ 자격증명 기반 로그인 성공!")
            return True
        
        print("❌ 모든 로그인 방법 실패")
        return False
    
    def close(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()
            print("🔚 브라우저 종료")

def main():
    print("🤖 티스토리 로그인 테스트")
    print("=" * 40)
    
    test = TistoryLoginTest(headless=False)
    
    try:
        while True:
            print("\n📋 메뉴:")
            print("1. 자동 로그인 테스트")
            print("2. 로그인 상태 확인")
            print("3. 쿠키 저장")
            print("4. 수동 로그인")
            print("0. 종료")
            
            choice = input("선택: ").strip()
            
            if choice == '1':
                test.test_auto_login()
            elif choice == '2':
                test.is_logged_in()
            elif choice == '3':
                test.save_cookies()
            elif choice == '4':
                test.login_with_credentials()
            elif choice == '0':
                break
            else:
                print("잘못된 선택")
    
    finally:
        test.close()

if __name__ == "__main__":
    main() 