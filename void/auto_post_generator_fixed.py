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

# auto_post_generator.py에서 가져온 내용 
# 들여쓰기 오류가 있는 부분만 수정

def set_html_content(driver, content, iframe_editor):
    """HTML 모드에서 콘텐츠 설정"""
    print("HTML 모드에서 콘텐츠 설정 시작...")
    
    # iframe으로 전환
    try:
        driver.switch_to.frame(iframe_editor)
        print("iframe으로 전환 성공")
    except Exception as e:
        print(f"iframe 전환 중 오류: {e}")
        return False
    
    content_set_success = False
    
    # 콘텐츠 설정 시도 (여러 방법 시도)
    try:
        # 방법 A: 기본 설정 방법
        try:
            # 직접 document.documentElement.innerHTML 설정
            driver.execute_script("""
                document.documentElement.innerHTML = arguments[0];
            """, content)
            content_set_success = True
            print("document.documentElement.innerHTML 설정 성공")
        except Exception as html_e:
            print(f"HTML 직접 설정 시도 중 오류: {html_e}")
        
        # 방법 B: CodeMirror 에디터 접근 시도
        if not content_set_success:
            try:
                cm_result = driver.execute_script("""
                    var cm = document.querySelector('.CodeMirror');
                    if (cm && cm.CodeMirror) {
                        cm.CodeMirror.setValue(arguments[0]);
                        return true;
                    }
                    return false;
                """, content)
                
                if cm_result:
                    content_set_success = True
                    print("CodeMirror 에디터 설정 성공")
            except Exception as cm_e:
                print(f"CodeMirror 설정 시도 중 오류: {cm_e}")
        
        # 방법 C: body 요소에 직접 설정 - 향상된 버전
        if not content_set_success:
            try:
                print("iframe 내 body 요소에 직접 콘텐츠 설정 및 티스토리 에디터 동기화 시도...")
                
                # body에 innerHTML 설정 및 티스토리 에디터에 연결
                body_result = driver.execute_script("""
                    if (document.body) {
                        try {
                            // 새 내용 설정
                            document.body.innerHTML = arguments[0];
                            
                            // 내용 설정 결과 확인
                            var success = document.body.innerHTML && document.body.innerHTML.length > 100;
                            
                            // 중요: body에 설정된 콘텐츠를 티스토리 에디터와 동기화
                            try {
                                // 모든 textarea에도 내용 동기화 시도 (가장 중요한 단계)
                                var textareas = document.querySelectorAll('textarea');
                                for (var i = 0; i < textareas.length; i++) {
                                    var ta = textareas[i];
                                    // 제목, 태그 필드 제외
                                    if (ta.id === 'post-title-inp' || ta.className.includes('textarea_tit') || ta.id === 'tag') {
                                        continue;
                                    }
                                    ta.value = arguments[0];
                                    ta.dispatchEvent(new Event('input', { bubbles: true }));
                                    ta.dispatchEvent(new Event('change', { bubbles: true }));
                                    
                                    // 키 이벤트 시뮬레이션 - 티스토리 에디터 활성화에 필요
                                    ta.dispatchEvent(new KeyboardEvent('keypress', {
                                        bubbles: true,
                                        key: ' ',
                                        keyCode: 32
                                    }));
                                }
                                
                                // ContentEditable 요소에 내용 설정
                                var editableElements = document.querySelectorAll('[contenteditable="true"]');
                                for (var i = 0; i < editableElements.length; i++) {
                                    editableElements[i].innerHTML = arguments[0];
                                    editableElements[i].dispatchEvent(new Event('input', { bubbles: true }));
                                }
                                
                                // CodeMirror 요소 접근 시도
                                var cmElements = document.querySelectorAll('.CodeMirror');
                                for (var i = 0; i < cmElements.length; i++) {
                                    var cm = cmElements[i];
                                    if (cm.CodeMirror) {
                                        cm.CodeMirror.setValue(arguments[0]);
                                        cm.CodeMirror.refresh();
                                        console.log("CodeMirror 인스턴스에 값 설정 성공");
                                    }
                                }
                                
                                console.log("다중 요소에 콘텐츠 동기화 시도 완료");
                            } catch (syncError) {
                                console.error("콘텐츠 동기화 오류:", syncError);
                            }
                            
                            return {
                                success: success,
                                message: "body innerHTML 설정 " + (success ? "성공" : "실패"),
                                contentLength: document.body.innerHTML.length
                            };
                        } catch (e) {
                            console.error("body 내용 설정 오류:", e);
                            return { success: false, message: "오류: " + e.message, contentLength: 0 };
                        }
                    }
                    return { success: false, message: "body 요소 없음", contentLength: 0 };
                """, content)
                
                if body_result and body_result.get("success"):
                    print(f"향상된 body innerHTML 설정 성공: 길이 = {body_result.get('contentLength')}")
                    
                    # 추가: iframe에서 나간 후 부모 프레임에서 직접 내용 설정 시도
                    driver.switch_to.default_content()
                    parent_result = driver.execute_script("""
                        try {
                            // 부모 프레임에서 tistoryEditor 접근
                            if (window.tistoryEditor) {
                                console.log("부모 프레임 tistoryEditor 발견");
                                
                                if (typeof tistoryEditor.setHtmlContent === 'function') {
                                    tistoryEditor.setHtmlContent(arguments[0]);
                                    return "tistoryEditor.setHtmlContent 호출 성공";
                                }
                                
                                if (typeof tistoryEditor.setValue === 'function') {
                                    tistoryEditor.setValue(arguments[0]);
                                    return "tistoryEditor.setValue 호출 성공";
                                }
                                
                                if (typeof tistoryEditor.setContent === 'function') {
                                    tistoryEditor.setContent(arguments[0]);
                                    return "tistoryEditor.setContent 호출 성공";
                                }
                            }
                            
                            // iframe 내부 콘텐츠 참조 시도
                            var editorIframe = document.querySelector('iframe[id*="editor"]');
                            if (editorIframe) {
                                try {
                                    var iframeDoc = editorIframe.contentDocument || editorIframe.contentWindow.document;
                                    if (iframeDoc) {
                                        // iframe 내부의 textarea에도 접근 시도
                                        var iframeTextareas = iframeDoc.querySelectorAll('textarea');
                                        for (var i = 0; i < iframeTextareas.length; i++) {
                                            var ta = iframeTextareas[i];
                                            if (ta.id !== 'post-title-inp' && !ta.className.includes('textarea_tit')) {
                                                ta.value = arguments[0];
                                                ta.dispatchEvent(new Event('input', { bubbles: true }));
                                                ta.dispatchEvent(new Event('change', { bubbles: true }));
                                            }
                                        }
                                    }
                                } catch (e) {
                                    console.error("iframe 참조 오류:", e);
                                }
                            }
                            
                            return "부모 프레임 처리 완료";
                        } catch (e) {
                            return "부모 프레임 오류: " + e.message;
                        }
                    """, content)
                    
                    print(f"부모 프레임 처리 결과: {parent_result}")
                    
                    # iframe으로 다시 전환
                    driver.switch_to.frame(iframe_editor)
                    
                    content_set_success = True
            except Exception as body_e:
                print(f"향상된 body 요소 설정 시도 중 오류: {body_e}")
                # iframe에서 복구
                try:
                    driver.switch_to.default_content()
                    print("오류 발생 후 기본 문서로 복귀")
                except Exception as recovery_e:
                    print(f"복구 중 추가 오류: {recovery_e}")
        
        # 방법 D: contenteditable 요소 찾아서 설정
        """ 