#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
안전한 사용자 입력 처리 모듈
===========================

키보드 인터럽트 및 기타 예외 상황에서도 안전하게 
사용자 입력을 처리하는 모듈
"""

import sys
import signal
import os
from url_validator import URLValidator

class SafeInputHandler:
    """안전한 입력 처리 클래스"""
    
    def __init__(self):
        self.url_validator = URLValidator()
        self.interrupted = False
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Ctrl+C 시그널 핸들러"""
        print("\n\n⚠️ 입력이 중단되었습니다.")
        self.interrupted = True
    
    def safe_input(self, prompt, input_type="text", validation_func=None):
        """
        안전한 입력 처리
        
        Args:
            prompt (str): 입력 프롬프트
            input_type (str): 입력 타입 ("text", "url", "number", "choice")
            validation_func (callable): 추가 검증 함수
            
        Returns:
            str: 입력된 값 또는 None (중단 시)
        """
        self.interrupted = False
        
        while True:
            try:
                if input_type == "url":
                    return self._safe_url_input(prompt)
                elif input_type == "number":
                    return self._safe_number_input(prompt)
                elif input_type == "choice":
                    return self._safe_choice_input(prompt, validation_func)
                else:
                    return self._safe_text_input(prompt, validation_func)
                    
            except KeyboardInterrupt:
                print("\n⚠️ 입력이 중단되었습니다.")
                retry = self._ask_retry()
                if not retry:
                    return None
                print("다시 시도합니다...\n")
                continue
            except EOFError:
                print("\n⚠️ 입력 스트림이 종료되었습니다.")
                return None
    
    def _safe_text_input(self, prompt, validation_func=None):
        """텍스트 입력 처리"""
        while True:
            try:
                value = input(prompt).strip()
                
                if validation_func:
                    if validation_func(value):
                        return value
                    else:
                        print("❌ 입력값이 유효하지 않습니다. 다시 입력해주세요.")
                        continue
                
                return value
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"❌ 입력 오류: {e}")
                continue
    
    def _safe_url_input(self, prompt):
        """URL 입력 처리 (검증 포함)"""
        while True:
            try:
                url = input(prompt).strip()
                
                if not url:
                    print("❌ URL을 입력해주세요.")
                    continue
                
                print("🔍 URL 유효성 검사 중...")
                validation_result = self.url_validator.validate_url(url)
                
                if not validation_result['valid']:
                    print(f"❌ {validation_result['error']}")
                    continue
                
                if not validation_result['accessible']:
                    print(f"⚠️ URL에 접근할 수 없습니다: {validation_result['error']}")
                    retry = input("그래도 계속 진행하시겠습니까? (y/n): ").strip().lower()
                    if retry != 'y':
                        continue
                
                # 미리보기 정보 표시
                if validation_result['title']:
                    print(f"📄 제목: {validation_result['title']}")
                if validation_result['description']:
                    print(f"📝 설명: {validation_result['description'][:100]}...")
                print(f"🏷️ 타입: {validation_result['type']}")
                
                return url
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"❌ URL 처리 오류: {e}")
                continue
    
    def _safe_number_input(self, prompt):
        """숫자 입력 처리"""
        while True:
            try:
                value = input(prompt).strip()
                return int(value)
                
            except ValueError:
                print("❌ 올바른 숫자를 입력해주세요.")
                continue
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"❌ 숫자 입력 오류: {e}")
                continue
    
    def _safe_choice_input(self, prompt, validation_func):
        """선택지 입력 처리"""
        while True:
            try:
                value = input(prompt).strip()
                
                if validation_func and validation_func(value):
                    return value
                else:
                    print("❌ 올바른 선택지를 입력해주세요.")
                    continue
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"❌ 선택 입력 오류: {e}")
                continue
    
    def _ask_retry(self):
        """재시도 여부 확인"""
        while True:
            try:
                retry = input("\n계속하시겠습니까? (y/n): ").strip().lower()
                if retry in ['y', 'yes', '예', 'ㅇ']:
                    return True
                elif retry in ['n', 'no', '아니오', 'ㄴ']:
                    return False
                else:
                    print("y 또는 n을 입력해주세요.")
                    continue
            except:
                return False
    
    def safe_url_input_with_preview(self, prompt):
        """URL 입력 시 미리보기 제공"""
        print("\n💡 URL 입력 팁:")
        print("  • YouTube: https://youtu.be/... 또는 https://youtube.com/watch?v=...")
        print("  • 뉴스: 네이버, 다음, BBC, CNN 등의 뉴스 기사 URL")
        print("  • 블로그: 티스토리, 네이버 블로그, Medium 등의 블로그 포스트 URL")
        print("  • Ctrl+C로 중단 가능\n")
        
        return self.safe_input(prompt, "url")

# 전역 입력 핸들러 인스턴스
input_handler = SafeInputHandler()

def safe_input(prompt, input_type="text", validation_func=None):
    """전역 안전 입력 함수"""
    return input_handler.safe_input(prompt, input_type, validation_func)

def safe_url_input(prompt):
    """안전한 URL 입력 함수"""
    return input_handler.safe_url_input_with_preview(prompt)

def safe_number_input(prompt):
    """안전한 숫자 입력 함수"""
    return input_handler.safe_input(prompt, "number")

def safe_choice_input(prompt, valid_choices):
    """안전한 선택지 입력 함수"""
    def validate_choice(value):
        try:
            choice = int(value)
            return choice in valid_choices
        except ValueError:
            return False
    
    return input_handler.safe_input(prompt, "choice", validate_choice)

if __name__ == "__main__":
    # 테스트 코드
    print("🧪 안전한 입력 처리 모듈 테스트")
    print("=" * 40)
    
    # URL 입력 테스트
    test_url = safe_url_input("🔗 테스트 URL을 입력하세요: ")
    if test_url:
        print(f"✅ 입력된 URL: {test_url}")
    else:
        print("❌ URL 입력이 취소되었습니다.")
    
    # 숫자 입력 테스트
    test_number = safe_number_input("🔢 숫자를 입력하세요: ")
    if test_number:
        print(f"✅ 입력된 숫자: {test_number}")
    
    # 선택지 입력 테스트
    test_choice = safe_choice_input("📋 선택하세요 (1-3): ", [1, 2, 3])
    if test_choice:
        print(f"✅ 선택된 옵션: {test_choice}") 