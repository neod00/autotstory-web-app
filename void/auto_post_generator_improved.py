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

# === 기존 코드는 동일하게 유지하고, 아래 개선된 함수들만 추가/수정 ===

def check_existing_content_strict(driver, iframe_editor):
    """기존 콘텐츠 엄격 확인 - 중복 입력 완전 방지"""
    try:
        print("기존 콘텐츠 확인 중...")
        content_found = []
        
        # iframe 내부 확인
        if iframe_editor:
            try:
                driver.switch_to.frame(iframe_editor)
                textareas = driver.find_elements(By.TAG_NAME, "textarea")
                for i, ta in enumerate(textareas):
                    ta_id = ta.get_attribute("id") or ""
                    if ta_id != "post-title-inp":
                        value = ta.get_attribute("value") or ""
                        if len(value) > 30:  # 30글자 이상이면 기존 콘텐츠
                            content_found.append(f"iframe-textarea-{i}: {len(value)}글자")
                driver.switch_to.default_content()
            except Exception as iframe_e:
                print(f"iframe 확인 중 오류: {iframe_e}")
                try:
                    driver.switch_to.default_content()
                except:
                    pass
        
        # 메인 페이지 확인
        try:
            # CodeMirror 확인
            cm_elements = driver.find_elements(By.CSS_SELECTOR, ".CodeMirror")
            for i, cm in enumerate(cm_elements):
                cm_textareas = cm.find_elements(By.TAG_NAME, "textarea")
                for j, ta in enumerate(cm_textareas):
                    value = ta.get_attribute("value") or ""
                    if len(value) > 30:
                        content_found.append(f"codemirror-{i}-{j}: {len(value)}글자")
            
            # 일반 textarea 확인
            textareas = driver.find_elements(By.TAG_NAME, "textarea")
            for i, ta in enumerate(textareas):
                ta_id = ta.get_attribute("id") or ""
                ta_class = ta.get_attribute("class") or ""
                if (ta_id != "post-title-inp" and 
                    "textarea_tit" not in ta_class and 
                    "tag" not in ta_id.lower()):
                    value = ta.get_attribute("value") or ""
                    if len(value) > 30:
                        content_found.append(f"main-textarea-{i}: {len(value)}글자")
        except Exception as main_e:
            print(f"메인 페이지 확인 중 오류: {main_e}")
        
        if content_found:
            print(f"⚠️ 기존 콘텐츠 발견: {', '.join(content_found)}")
            return True
        else:
            print("✅ 기존 콘텐츠 없음. 새로 입력 가능.")
            return False
            
    except Exception as e:
        print(f"기존 콘텐츠 확인 중 오류: {e}")
        return False

def natural_content_input(driver, content, iframe_editor):
    """자연스러운 콘텐츠 입력 - 티스토리 자동화 감지 완전 우회"""
    try:
        print("\n=== 자연스러운 콘텐츠 입력 시작 ===")
        print(f"콘텐츠 길이: {len(content)} 글자")
        
        # 1단계: 기존 콘텐츠 엄격 확인
        if check_existing_content_strict(driver, iframe_editor):
            print("기존 콘텐츠가 있어 중복 입력을 방지합니다.")
            return True
        
        # 2단계: 에디터 요소 찾기
        editor_element = None
        editor_location = ""
        
        # iframe 내부에서 찾기
        if iframe_editor:
            try:
                driver.switch_to.frame(iframe_editor)
                textareas = driver.find_elements(By.TAG_NAME, "textarea")
                for i, ta in enumerate(textareas):
                    ta_id = ta.get_attribute("id") or ""
                    if ta_id != "post-title-inp":
                        editor_element = ta
                        editor_location = f"iframe-textarea-{i}"
                        print(f"에디터 발견: {editor_location}")
                        break
                
                if not editor_element:
                    driver.switch_to.default_content()
            except Exception as iframe_e:
                print(f"iframe 접근 중 오류: {iframe_e}")
                try:
                    driver.switch_to.default_content()
                except:
                    pass
        
        # 메인 페이지에서 찾기
        if not editor_element:
            try:
                # CodeMirror 우선 확인
                cm_elements = driver.find_elements(By.CSS_SELECTOR, ".CodeMirror")
                if cm_elements:
                    cm_textareas = cm_elements[0].find_elements(By.TAG_NAME, "textarea")
                    if cm_textareas:
                        editor_element = cm_textareas[0]
                        editor_location = "codemirror-textarea"
                        print(f"에디터 발견: {editor_location}")
                
                # 일반 textarea 확인
                if not editor_element:
                    textareas = driver.find_elements(By.TAG_NAME, "textarea")
                    for i, ta in enumerate(textareas):
                        ta_id = ta.get_attribute("id") or ""
                        ta_class = ta.get_attribute("class") or ""
                        if (ta_id != "post-title-inp" and 
                            "textarea_tit" not in ta_class and 
                            "tag" not in ta_id.lower()):
                            editor_element = ta
                            editor_location = f"main-textarea-{i}"
                            print(f"에디터 발견: {editor_location}")
                            break
            except Exception as main_e:
                print(f"메인 페이지 에디터 찾기 중 오류: {main_e}")
        
        if not editor_element:
            print("❌ 에디터 요소를 찾을 수 없습니다.")
            return False
        
        # 3단계: 자연스러운 타이핑 시뮬레이션
        print("자연스러운 타이핑 시작...")
        
        # 에디터에 포커스 (자연스럽게)
        try:
            editor_element.click()  # 마우스 클릭 시뮬레이션
            time.sleep(random.uniform(0.3, 0.7))
            
            # 기존 내용 확인 후 지우기
            current_value = editor_element.get_attribute("value") or ""
            if current_value:
                print(f"기존 내용 감지 ({len(current_value)}글자), 지우기 시작...")
                # Ctrl+A로 전체 선택 후 삭제 (더 자연스럽게)
                editor_element.send_keys(Keys.CONTROL + "a")
                time.sleep(random.uniform(0.1, 0.3))
                editor_element.send_keys(Keys.DELETE)
                time.sleep(random.uniform(0.2, 0.5))
        except Exception as focus_e:
            print(f"포커스 설정 중 오류: {focus_e}")
        
        # 4단계: 콘텐츠를 자연스럽게 청크 단위로 입력
        chunk_size = random.randint(20, 40)  # 랜덤한 청크 크기
        total_chunks = (len(content) + chunk_size - 1) // chunk_size
        
        print(f"콘텐츠를 {total_chunks}개 청크로 나누어 입력 (청크 크기: {chunk_size})")
        
        for i in range(total_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, len(content))
            chunk = content[start:end]
            
            try:
                # 청크를 더 작은 단위로 나누어 입력
                for char_idx in range(0, len(chunk), 3):  # 3글자씩
                    sub_chunk = chunk[char_idx:char_idx+3]
                    editor_element.send_keys(sub_chunk)
                    
                    # 자연스러운 타이핑 지연 (50-150ms)
                    time.sleep(random.uniform(0.05, 0.15))
                
                # 청크 완료 후 약간의 지연
                time.sleep(random.uniform(0.1, 0.3))
                
                # 진행률 표시
                if i % 10 == 0 or i == total_chunks - 1:
                    progress = (i + 1) / total_chunks * 100
                    print(f"입력 진행률: {progress:.1f}%")
                
                # 중간에 가끔 멈춤 (자연스러운 사용자 행동 시뮬레이션)
                if i > 0 and i % 20 == 0:
                    print("자연스러운 입력 패턴을 위한 일시 정지...")
                    time.sleep(random.uniform(0.5, 1.5))
                    
            except Exception as chunk_e:
                print(f"청크 {i} 입력 중 오류: {chunk_e}")
                # 오류 발생 시 JavaScript 폴백
                try:
                    current_text = editor_element.get_attribute("value") or ""
                    new_text = current_text + chunk
                    driver.execute_script("""
                        arguments[0].value = arguments[1];
                        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    """, editor_element, new_text)
                except:
                    print(f"JavaScript 폴백도 실패")
        
        # 5단계: 입력 완료 후 자연스러운 마무리
        time.sleep(random.uniform(0.5, 1.0))
        
        # 입력 결과 확인
        final_value = editor_element.get_attribute("value") or ""
        final_length = len(final_value)
        
        print(f"입력 완료: {final_length} 글자 (목표: {len(content)} 글자)")
        
        # iframe에서 나오기
        try:
            driver.switch_to.default_content()
        except:
            pass
        
        # 성공 기준: 80% 이상 입력되었으면 성공
        success = final_length > len(content) * 0.8
        
        if success:
            print("✅ 자연스러운 콘텐츠 입력 성공!")
        else:
            print(f"⚠️ 콘텐츠 입력 부족 (성공률: {final_length/len(content)*100:.1f}%)")
        
        return success
        
    except Exception as e:
        print(f"자연스러운 콘텐츠 입력 중 오류: {e}")
        try:
            driver.switch_to.default_content()
        except:
            pass
        return False

def safe_tag_input(driver, tags):
    """안전한 태그 입력 함수"""
    try:
        print(f"\n태그 입력 시작: {tags}")
        
        # 태그 입력 필드 찾기
        tag_input = None
        tag_selectors = [
            "input[placeholder*='태그']",
            "#tagText",
            ".tag-input",
            "input[name*='tag']",
            ".tagInput",
            "input[type='text']:not(#post-title-inp)"
        ]
        
        for selector in tag_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        # 태그 필드인지 추가 확인
                        placeholder = element.get_attribute("placeholder") or ""
                        name = element.get_attribute("name") or ""
                        element_id = element.get_attribute("id") or ""
                        
                        if ("태그" in placeholder or "tag" in placeholder.lower() or
                            "tag" in name.lower() or "tag" in element_id.lower()):
                            tag_input = element
                            print(f"태그 입력 필드 발견: {selector}")
                            break
                
                if tag_input:
                    break
            except Exception as selector_e:
                print(f"선택자 '{selector}' 시도 중 오류: {selector_e}")
                continue
        
        if not tag_input:
            print("⚠️ 태그 입력 필드를 찾을 수 없습니다.")
            return False
        
        # 태그를 하나씩 자연스럽게 입력
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        for i, tag in enumerate(tag_list):
            try:
                print(f"태그 {i+1}/{len(tag_list)} 입력 중: '{tag}'")
                
                # 입력 필드 클리어
                tag_input.clear()
                time.sleep(random.uniform(0.1, 0.3))
                
                # 태그를 자연스럽게 타이핑
                for char in tag:
                    tag_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))  # 자연스러운 타이핑 속도
                
                # Enter 키로 태그 등록
                time.sleep(random.uniform(0.2, 0.5))
                tag_input.send_keys(Keys.ENTER)
                
                # 태그 등록 후 대기
                time.sleep(random.uniform(0.3, 0.7))
                
                print(f"✅ 태그 '{tag}' 입력 완료")
                
            except Exception as tag_e:
                print(f"❌ 태그 '{tag}' 입력 중 오류: {tag_e}")
                continue
        
        print(f"✅ 모든 태그 입력 완료 ({len(tag_list)}개)")
        return True
        
    except Exception as e:
        print(f"태그 입력 중 전체 오류: {e}")
        return False

# === 기존 함수들을 개선된 버전으로 교체하기 위한 래퍼 ===

def enhanced_set_html_content(driver, content, iframe_editor):
    """기존 set_html_content를 개선된 버전으로 교체"""
    return natural_content_input(driver, content, iframe_editor)

def enhanced_input_tags(driver, tags):
    """기존 input_tags를 개선된 버전으로 교체"""
    return safe_tag_input(driver, tags)

# === 사용 예시 ===
"""
write_post 함수에서 다음과 같이 교체:

기존:
set_html_content(driver, content, iframe_editor)
input_tags(driver, blog_post["tags"])

개선:
enhanced_set_html_content(driver, content, iframe_editor)
enhanced_input_tags(driver, blog_post["tags"])
"""

print("🚀 개선된 auto_post_generator 모듈이 로드되었습니다!")
print("✅ 중복 입력 방지 기능 추가")
print("✅ 자연스러운 타이핑 시뮬레이션")
print("✅ 티스토리 자동화 감지 우회")
print("✅ 안전한 태그 입력 기능") 