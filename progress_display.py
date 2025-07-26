#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
진행 상황 표시 모듈
=================

사용자에게 명확한 진행 상황과 상태 정보를 제공하는 모듈
"""

import time
import sys
import threading
from datetime import datetime, timedelta

class ProgressDisplay:
    """진행 상황 표시 클래스"""
    
    def __init__(self):
        self.current_task = ""
        self.current_step = 0
        self.total_steps = 0
        self.start_time = None
        self.is_running = False
        self.spinner_thread = None
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.spinner_idx = 0
    
    def start_task(self, task_name, total_steps=1):
        """작업 시작"""
        self.current_task = task_name
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = datetime.now()
        self.is_running = True
        
        print(f"\n🚀 {task_name} 시작")
        print("=" * 60)
        
        if total_steps > 1:
            self._show_progress_bar()
    
    def update_step(self, step_name, step_number=None):
        """단계 업데이트"""
        if step_number:
            self.current_step = step_number
        else:
            self.current_step += 1
        
        # 진행률 계산
        progress = (self.current_step / self.total_steps) * 100 if self.total_steps > 0 else 0
        
        # 경과 시간 계산
        elapsed = datetime.now() - self.start_time if self.start_time else timedelta(0)
        elapsed_str = str(elapsed).split('.')[0]  # 마이크로초 제거
        
        print(f"\n🔄 단계 {self.current_step}/{self.total_steps}: {step_name}")
        print(f"   진행률: {progress:.1f}% | 경과 시간: {elapsed_str}")
        
        if self.total_steps > 1:
            self._show_progress_bar()
    
    def _show_progress_bar(self):
        """진행률 바 표시"""
        progress = self.current_step / self.total_steps
        bar_length = 40
        filled_length = int(bar_length * progress)
        
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        percentage = progress * 100
        
        print(f"   [{bar}] {percentage:.1f}%")
    
    def show_spinner(self, message):
        """스피너 표시 시작"""
        if self.spinner_thread and self.spinner_thread.is_alive():
            self.stop_spinner()
        
        self.is_running = True
        self.spinner_thread = threading.Thread(target=self._spinner_animation, args=(message,))
        self.spinner_thread.daemon = True
        self.spinner_thread.start()
    
    def stop_spinner(self):
        """스피너 표시 중지"""
        self.is_running = False
        if self.spinner_thread:
            self.spinner_thread.join(timeout=1)
        
        # 커서를 다음 줄로 이동
        print()
    
    def _spinner_animation(self, message):
        """스피너 애니메이션"""
        while self.is_running:
            char = self.spinner_chars[self.spinner_idx]
            sys.stdout.write(f"\r{char} {message}")
            sys.stdout.flush()
            
            self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_chars)
            time.sleep(0.1)
    
    def success_message(self, message, details=""):
        """성공 메시지"""
        if self.is_running:
            self.stop_spinner()
        
        print(f"✅ {message}")
        if details:
            print(f"   {details}")
    
    def error_message(self, message, suggestion=""):
        """오류 메시지"""
        if self.is_running:
            self.stop_spinner()
        
        print(f"❌ {message}")
        if suggestion:
            print(f"💡 {suggestion}")
    
    def warning_message(self, message, note=""):
        """경고 메시지"""
        if self.is_running:
            self.stop_spinner()
        
        print(f"⚠️ {message}")
        if note:
            print(f"📝 {note}")
    
    def info_message(self, message, icon="ℹ️"):
        """정보 메시지"""
        print(f"{icon} {message}")
    
    def finish_task(self, success=True, final_message=""):
        """작업 완료"""
        self.is_running = False
        if self.spinner_thread:
            self.stop_spinner()
        
        elapsed = datetime.now() - self.start_time if self.start_time else timedelta(0)
        elapsed_str = str(elapsed).split('.')[0]
        
        if success:
            icon = "🎉"
            status = "완료"
        else:
            icon = "💥"
            status = "실패"
        
        print(f"\n{icon} {self.current_task} {status}!")
        if final_message:
            print(f"   {final_message}")
        print(f"   총 소요 시간: {elapsed_str}")
        print("=" * 60)
    
    def show_url_preview(self, url_info):
        """URL 미리보기 표시"""
        print("\n📋 URL 정보:")
        print("─" * 40)
        print(f"🔗 URL: {url_info.get('url', 'N/A')}")
        print(f"🏷️ 타입: {url_info.get('type', 'unknown')}")
        
        if url_info.get('title'):
            print(f"📄 제목: {url_info['title']}")
        
        if url_info.get('description'):
            desc = url_info['description']
            if len(desc) > 100:
                desc = desc[:100] + "..."
            print(f"📝 설명: {desc}")
        
        print("─" * 40)
    
    def show_content_summary(self, content_info):
        """콘텐츠 요약 표시"""
        print("\n📊 생성된 콘텐츠 정보:")
        print("─" * 40)
        
        if content_info.get('title'):
            print(f"📄 제목: {content_info['title']}")
        
        if content_info.get('content'):
            content_len = len(content_info['content'])
            print(f"📝 내용 길이: {content_len:,} 글자")
        
        if content_info.get('tags'):
            tags = content_info['tags']
            if len(tags) > 80:
                tags = tags[:80] + "..."
            print(f"🏷️ 태그: {tags}")
        
        if content_info.get('images'):
            image_count = len(content_info['images'])
            print(f"🖼️ 이미지: {image_count}개")
        
        if content_info.get('source_url'):
            print(f"🔗 원본 URL: {content_info['source_url']}")
        
        print("─" * 40)
    
    def show_menu(self, title, options, descriptions=None):
        """메뉴 표시"""
        print(f"\n{title}")
        print("=" * 60)
        
        for i, option in enumerate(options, 1):
            desc = ""
            if descriptions and i-1 < len(descriptions):
                desc = f" - {descriptions[i-1]}"
            print(f"  {i}. {option}{desc}")
        
        print("=" * 60)
    
    def show_api_status(self, api_checks):
        """API 상태 표시"""
        print("\n🔑 API 상태 확인:")
        print("─" * 30)
        
        for api_name, status in api_checks.items():
            if status:
                print(f"✅ {api_name}: 설정됨")
            else:
                print(f"❌ {api_name}: 미설정")
        
        print("─" * 30)
    
    def show_system_info(self, system_info):
        """시스템 정보 표시"""
        print("\n💻 시스템 정보:")
        print("─" * 30)
        
        for key, value in system_info.items():
            print(f"• {key}: {value}")
        
        print("─" * 30)

# 전역 진행 상황 표시 인스턴스
progress = ProgressDisplay()

# 편의 함수들
def start_task(task_name, total_steps=1):
    """작업 시작"""
    progress.start_task(task_name, total_steps)

def update_step(step_name, step_number=None):
    """단계 업데이트"""
    progress.update_step(step_name, step_number)

def show_spinner(message):
    """스피너 표시"""
    progress.show_spinner(message)

def stop_spinner():
    """스피너 중지"""
    progress.stop_spinner()

def success_message(message, details=""):
    """성공 메시지"""
    progress.success_message(message, details)

def error_message(message, suggestion=""):
    """오류 메시지"""
    progress.error_message(message, suggestion)

def warning_message(message, note=""):
    """경고 메시지"""
    progress.warning_message(message, note)

def info_message(message, icon="ℹ️"):
    """정보 메시지"""
    progress.info_message(message, icon)

def finish_task(success=True, final_message=""):
    """작업 완료"""
    progress.finish_task(success, final_message)

def show_url_preview(url_info):
    """URL 미리보기"""
    progress.show_url_preview(url_info)

def show_content_summary(content_info):
    """콘텐츠 요약"""
    progress.show_content_summary(content_info)

def show_menu(title, options, descriptions=None):
    """메뉴 표시"""
    progress.show_menu(title, options, descriptions)

def show_api_status(api_checks):
    """API 상태 표시"""
    progress.show_api_status(api_checks)

def show_system_info(system_info):
    """시스템 정보 표시"""
    progress.show_system_info(system_info)

if __name__ == "__main__":
    # 테스트 코드
    print("🧪 진행 상황 표시 모듈 테스트")
    
    # 작업 시작
    start_task("테스트 작업", 5)
    
    # 단계별 진행
    update_step("1단계: 초기화")
    time.sleep(1)
    
    update_step("2단계: 데이터 수집")
    time.sleep(1)
    
    # 스피너 테스트
    show_spinner("데이터 처리 중...")
    time.sleep(2)
    stop_spinner()
    
    update_step("3단계: 분석")
    time.sleep(1)
    
    update_step("4단계: 생성")
    time.sleep(1)
    
    update_step("5단계: 완료")
    
    # 다양한 메시지 테스트
    success_message("테스트 성공", "모든 단계가 완료되었습니다")
    warning_message("주의사항", "이것은 테스트입니다")
    info_message("추가 정보", "🔍")
    
    # 작업 완료
    finish_task(True, "테스트가 성공적으로 완료되었습니다")
    
    # URL 미리보기 테스트
    url_info = {
        'url': 'https://example.com',
        'type': 'website',
        'title': '테스트 웹사이트',
        'description': '이것은 테스트용 웹사이트입니다.'
    }
    show_url_preview(url_info)
    
    # 메뉴 테스트
    show_menu("테스트 메뉴", ["옵션 1", "옵션 2", "옵션 3"], ["첫 번째 옵션", "두 번째 옵션", "세 번째 옵션"]) 