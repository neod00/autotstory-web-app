#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 티스토리 로그인 테스트
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
                print("❌ 환경변수 TISTORY_USERNAME, TISTORY_PASSWORD 설정 필요")
                return False
            
            print("🎯 최종 티스토리 로그인 시작")
            print("=" * 50)
            
            # 1단계: 티스토리 로그인 페이지 접속
            print("1️⃣ 티스토리 로그인 페이지 접속...")
            self.driver.get("https://www.tistory.com/auth/login")
            
            # 페이지 완전 로딩 대기
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(3)
            
            print(f"📄 현재 페이지: {self.driver.title}")
            
            # 2단계: 카카오 로그인 버튼 클릭
            print("2️⃣ 카카오 로그인 버튼 클릭...")
            
            try:
                kakao_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn_login.link_kakao_id"))
                )
                kakao_btn.click()
                print("✅ 카카오 버튼 클릭 성공")
            except:
                # 대안 방법
                js_result = self.driver.execute_script("""
                    var links = document.querySelectorAll('a');
                    for (var i = 0; i < links.length; i++) {
                        var link = links[i];
                        if (link.textContent.includes('카카오계정으로 로그인')) {
                            link.click();
                            return true;
                        }
                    }
                    return false;
                """)
                
                if js_result:
                    print("✅ 카카오 버튼 클릭 성공 (JS)")
                else:
                    print("❌ 카카오 버튼 클릭 실패")
                    return False
            
            # 3단계: 카카오 로그인 페이지 로딩 대기
            print("3️⃣ 카카오 페이지 로딩 대기...")
            
            WebDriverWait(self.driver, 15).until(
                lambda driver: "kakao" in driver.current_url.lower() or 
                              len(driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email']")) > 0
            )
            
            time.sleep(3)
            print(f"🌐 카카오 페이지 URL: {self.driver.current_url}")
            
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
            
            # 7단계: 2단계 인증 대기
            print("7️⃣ 2단계 인증 확인...")
            time.sleep(5)
            
            current_url = self.driver.current_url
            print(f"🌐 현재 URL: {current_url}")
            
            # 2단계 인증 페이지 확인
            if "tmsTwoStepVerification" in current_url or "verification" in current_url.lower():
                print("📱 2단계 인증이 필요합니다!")
                print("=" * 50)
                print("🔔 핸드폰에서 로그인 승인을 해주세요!")
                print("   1. 핸드폰에 카카오톡 알림이 왔는지 확인")
                print("   2. 알림을 터치하여 로그인 승인")
                print("   3. 승인 후 자동으로 다음 단계 진행됩니다")
                print("=" * 50)
                
                # 승인 대기 (최대 3분)
                approval_success = self.wait_for_approval(max_wait_minutes=3)
                
                if approval_success:
                    print("✅ 2단계 인증 승인 완료!")
                else:
                    print("❌ 2단계 인증 승인 시간 초과")
                    return False
            else:
                print("ℹ️ 2단계 인증이 필요하지 않습니다")
            
            # 8단계: 최종 로그인 확인
            print("8️⃣ 최종 로그인 상태 확인...")
            
            # 최종 페이지 로딩 대기
            time.sleep(5)
            
            final_url = self.driver.current_url
            print(f"🌐 최종 URL: {final_url}")
            
            # 로그인 성공 여부 확인
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
        print(f"⏰ 최대 {max_wait_minutes}분 동안 승인을 기다립니다...")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        check_interval = 5  # 5초마다 확인
        
        while time.time() - start_time < max_wait_seconds:
            try:
                current_url = self.driver.current_url
                
                # URL 변경 확인 (승인 완료 시 리디렉션)
                if "tmsTwoStepVerification" not in current_url and "verification" not in current_url.lower():
                    print("✅ URL이 변경되었습니다 - 승인 완료!")
                    return True
                
                # 페이지 내용 변경 확인
                page_changed = self.driver.execute_script("""
                    // 승인 완료 관련 요소 확인
                    if (document.querySelector('.success, .complete, .approved')) {
                        return 'success_element';
                    }
                    
                    // 로딩 상태 확인
                    if (document.querySelector('.loading, .spinner')) {
                        return 'loading';
                    }
                    
                    // 에러 메시지 확인
                    if (document.querySelector('.error, .fail')) {
                        return 'error';
                    }
                    
                    return 'waiting';
                """)
                
                if page_changed == 'success_element':
                    print("✅ 승인 완료 요소 발견!")
                    return True
                elif page_changed == 'error':
                    print("❌ 승인 실패 감지")
                    return False
                
                # 진행 상황 표시
                elapsed = int(time.time() - start_time)
                remaining = max_wait_seconds - elapsed
                
                if elapsed % 30 == 0:  # 30초마다 상태 출력
                    print(f"⏳ 대기 중... (경과: {elapsed}초, 남은 시간: {remaining}초)")
                
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"⚠️ 승인 대기 중 오류: {e}")
                time.sleep(check_interval)
        
        print("⏰ 승인 대기 시간이 초과되었습니다")
        return False
    
    def check_login_success(self):
        """로그인 성공 여부 확인"""
        try:
            current_url = self.driver.current_url
            
            # URL 기반 확인
            if "login" not in current_url.lower() and "auth" not in current_url.lower():
                success_indicators = ["url_change"]
            else:
                success_indicators = []
            
            # 페이지 요소 기반 확인 (JavaScript 오류 수정)
            page_elements = self.driver.execute_script("""
                var indicators = [];
                
                // 로그아웃 버튼 확인 (수정된 선택자)
                if (document.querySelector('a[href*="logout"]') || 
                    document.querySelector('.logout') ||
                    document.querySelector('a').textContent.includes('로그아웃')) {
                    indicators.push('logout_button');
                }
                
                // 사용자 정보 확인
                if (document.querySelector('.user-info') || 
                    document.querySelector('.username') || 
                    document.querySelector('.user-name')) {
                    indicators.push('user_info');
                }
                
                // 글쓰기 버튼 확인
                if (document.querySelector('a[href*="write"]') || 
                    document.querySelector('a[href*="post"]') || 
                    document.querySelector('.write') || 
                    document.querySelector('.new-post')) {
                    indicators.push('write_button');
                }
                
                // 대시보드 확인
                if (document.querySelector('.dashboard') || 
                    document.querySelector('.admin') || 
                    document.querySelector('.manage')) {
                    indicators.push('dashboard');
                }
                
                // 티스토리 메인 페이지 확인
                if (document.querySelector('.tistory') || 
                    document.title.includes('TISTORY') && 
                    !document.title.includes('로그인')) {
                    indicators.push('tistory_main');
                }
                
                return indicators;
            """)
            
            success_indicators.extend(page_elements)
            
            if success_indicators:
                print(f"✅ 로그인 성공 확인: {', '.join(success_indicators)}")
                return True
            else:
                print("❌ 로그인 성공 지표를 찾을 수 없음")
                return False
                
        except Exception as e:
            print(f"⚠️ 로그인 확인 중 오류: {e}")
            # URL만으로 판단
            current_url = self.driver.current_url
            if "login" not in current_url.lower() and "auth" not in current_url.lower():
                print("✅ URL 기반으로 로그인 성공 추정")
                return True
            return False
    
    def save_cookies(self):
        """쿠키 저장"""
        try:
            cookies = self.driver.get_cookies()
            tistory_cookies = [c for c in cookies if 'tistory.com' in c.get('domain', '') or 'kakao.com' in c.get('domain', '')]
            
            if tistory_cookies:
                with open('final_cookies.pkl', 'wb') as f:
                    pickle.dump(tistory_cookies, f)
                print(f"✅ {len(tistory_cookies)}개 쿠키 저장 완료")
                
                # 쿠키 정보 출력
                print("📋 저장된 쿠키:")
                for cookie in tistory_cookies[:5]:  # 처음 5개만 표시
                    print(f"   - {cookie['name']}: {cookie['domain']}")
                if len(tistory_cookies) > 5:
                    print(f"   ... 외 {len(tistory_cookies)-5}개 더")
                
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
    print("🎯 최종 티스토리 자동 로그인 테스트")
    print("(2단계 인증 지원)")
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
    print()
    
    print("📱 2단계 인증 안내:")
    print("   - 로그인 진행 중 핸드폰 승인이 필요할 수 있습니다")
    print("   - 카카오톡 알림을 확인하여 승인해주세요")
    print("   - 최대 3분 동안 자동으로 대기합니다")
    print()
    
    # 로그인 테스트 시작
    login_test = FinalTistoryLogin(headless=False)
    
    try:
        success = login_test.complete_login()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 완전 자동 로그인 성공!")
            print("✅ 이제 메인 프로그램에 적용할 준비가 완료되었습니다!")
            print()
            print("📋 다음 단계:")
            print("   1. final_cookies.pkl 파일이 생성되었습니다")
            print("   2. 이 로그인 로직을 메인 프로그램에 통합")
            print("   3. 완전 자동화 달성!")
        else:
            print("❌ 로그인 실패")
            print()
            print("🔍 확인사항:")
            print("   - 아이디/비밀번호가 정확한지")
            print("   - 2단계 인증을 승인했는지")
            print("   - 네트워크 연결 상태")
    
    finally:
        input("\n테스트가 완료되었습니다. Enter 키를 누르면 브라우저가 종료됩니다...")
        login_test.close()

if __name__ == "__main__":
    main() 