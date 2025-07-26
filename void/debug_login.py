#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
티스토리 로그인 디버깅용 테스트 파일
"""

import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 환경변수 로드
load_dotenv()

def debug_tistory_login():
    """티스토리 로그인 페이지 구조 분석"""
    
    # 웹드라이버 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print("🔍 티스토리 로그인 페이지 분석 시작")
        
        # 로그인 페이지 접속
        driver.get("https://www.tistory.com/auth/login")
        time.sleep(5)
        
        # 페이지 기본 정보
        print(f"📄 페이지 제목: {driver.title}")
        print(f"🌐 현재 URL: {driver.current_url}")
        
        # 모든 요소 분석
        analysis = driver.execute_script("""
            var result = {
                allButtons: [],
                allInputs: [],
                allLinks: [],
                allForms: []
            };
            
            // 모든 버튼 분석
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                if (btn.offsetParent !== null) { // 보이는 버튼만
                    result.allButtons.push({
                        index: i,
                        text: (btn.textContent || btn.innerText || '').trim(),
                        className: btn.className || '',
                        id: btn.id || '',
                        type: btn.type || '',
                        onclick: btn.onclick ? btn.onclick.toString().substring(0, 50) : ''
                    });
                }
            }
            
            // 모든 링크 분석
            var links = document.querySelectorAll('a');
            for (var i = 0; i < links.length; i++) {
                var link = links[i];
                if (link.offsetParent !== null) { // 보이는 링크만
                    result.allLinks.push({
                        index: i,
                        text: (link.textContent || link.innerText || '').trim(),
                        href: link.href || '',
                        className: link.className || '',
                        id: link.id || ''
                    });
                }
            }
            
            // 모든 입력 필드 분석
            var inputs = document.querySelectorAll('input');
            for (var i = 0; i < inputs.length; i++) {
                var input = inputs[i];
                if (input.offsetParent !== null) { // 보이는 입력 필드만
                    result.allInputs.push({
                        index: i,
                        type: input.type || '',
                        name: input.name || '',
                        id: input.id || '',
                        placeholder: input.placeholder || '',
                        className: input.className || '',
                        value: input.value || ''
                    });
                }
            }
            
            // 모든 폼 분석
            var forms = document.querySelectorAll('form');
            for (var i = 0; i < forms.length; i++) {
                var form = forms[i];
                result.allForms.push({
                    index: i,
                    action: form.action || '',
                    method: form.method || '',
                    className: form.className || '',
                    id: form.id || ''
                });
            }
            
            return result;
        """)
        
        # 결과 출력
        print("\n" + "="*50)
        print("🔘 발견된 버튼들:")
        for btn in analysis['allButtons']:
            print(f"  버튼 {btn['index']}: '{btn['text'][:40]}' | class: {btn['className'][:30]} | id: {btn['id']}")
        
        print("\n" + "="*50)
        print("🔗 발견된 링크들:")
        for link in analysis['allLinks']:
            if 'kakao' in link['href'].lower() or 'kakao' in link['text'].lower() or 'login' in link['href'].lower():
                print(f"  ⭐ 링크 {link['index']}: '{link['text'][:40]}' | href: {link['href'][:50]}")
        
        print("\n" + "="*50)
        print("📝 발견된 입력 필드들:")
        for inp in analysis['allInputs']:
            print(f"  필드 {inp['index']}: {inp['type']} | name: {inp['name']} | id: {inp['id']} | placeholder: {inp['placeholder']}")
        
        print("\n" + "="*50)
        print("📋 발견된 폼들:")
        for form in analysis['allForms']:
            print(f"  폼 {form['index']}: action: {form['action']} | method: {form['method']} | class: {form['className']}")
        
        # 카카오 관련 요소 특별 검색
        print("\n" + "="*50)
        print("🔍 카카오 관련 요소 특별 검색:")
        
        kakao_elements = driver.execute_script("""
            var kakaoElements = [];
            var allElements = document.querySelectorAll('*');
            
            for (var i = 0; i < allElements.length; i++) {
                var el = allElements[i];
                var text = (el.textContent || el.innerText || '').toLowerCase();
                var className = (el.className || '').toLowerCase();
                var id = (el.id || '').toLowerCase();
                var href = (el.href || '').toLowerCase();
                
                if (text.includes('카카오') || text.includes('kakao') || 
                    className.includes('kakao') || id.includes('kakao') || 
                    href.includes('kakao')) {
                    
                    kakaoElements.push({
                        tag: el.tagName,
                        text: text.substring(0, 50),
                        className: className.substring(0, 30),
                        id: id,
                        href: href.substring(0, 50)
                    });
                }
            }
            
            return kakaoElements;
        """)
        
        for i, el in enumerate(kakao_elements):
            print(f"  카카오 요소 {i+1}: {el['tag']} | text: '{el['text']}' | class: {el['className']} | href: {el['href']}")
        
        # 로그인 시도할 요소 제안
        print("\n" + "="*50)
        print("💡 추천 로그인 방법:")
        
        # 카카오 링크가 있는지 확인
        kakao_links = [link for link in analysis['allLinks'] if 'kakao' in link['href'].lower()]
        if kakao_links:
            print(f"  1. 카카오 링크 클릭: {kakao_links[0]['href']}")
        
        # 텍스트 입력 필드 확인
        text_inputs = [inp for inp in analysis['allInputs'] if inp['type'] in ['text', 'email']]
        if text_inputs:
            print(f"  2. 아이디 입력 필드: name='{text_inputs[0]['name']}' id='{text_inputs[0]['id']}'")
        
        # 비밀번호 필드 확인
        password_inputs = [inp for inp in analysis['allInputs'] if inp['type'] == 'password']
        if password_inputs:
            print(f"  3. 비밀번호 입력 필드: name='{password_inputs[0]['name']}' id='{password_inputs[0]['id']}'")
        
        # 제출 버튼 확인
        submit_buttons = [btn for btn in analysis['allButtons'] if btn['type'] == 'submit' or 'login' in btn['text'].lower()]
        if submit_buttons:
            print(f"  4. 제출 버튼: '{submit_buttons[0]['text']}' class='{submit_buttons[0]['className']}'")
        
        # 사용자 입력 대기
        input("\n분석 완료! 브라우저 창을 확인하고 Enter 키를 누르세요...")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_tistory_login() 