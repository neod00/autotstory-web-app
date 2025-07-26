#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
향상된 로깅 시스템
================

시스템 동작 및 오류에 대한 자세한 로깅을 제공하는 모듈
"""

import logging
import sys
import traceback
from datetime import datetime
import os
from pathlib import Path

class EnhancedLogger:
    """향상된 로깅 클래스"""
    
    def __init__(self, name="AutoTstory", log_level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # 기존 핸들러 제거
        self.logger.handlers.clear()
        
        # 로그 디렉토리 생성
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 파일 핸들러 (상세 로그)
        file_handler = logging.FileHandler(
            log_dir / f"autotistory_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 콘솔 핸들러 (요약 로그)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 포맷터 설정
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter('%(message)s')
        
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 오류 통계
        self.error_count = 0
        self.warning_count = 0
        
    def info(self, message, show_console=True):
        """정보 로그"""
        if show_console:
            print(f"ℹ️ {message}")
        self.logger.info(message)
    
    def success(self, message, show_console=True):
        """성공 로그"""
        if show_console:
            print(f"✅ {message}")
        self.logger.info(f"SUCCESS: {message}")
    
    def warning(self, message, show_console=True):
        """경고 로그"""
        self.warning_count += 1
        if show_console:
            print(f"⚠️ {message}")
        self.logger.warning(message)
    
    def error(self, message, exception=None, show_console=True):
        """오류 로그"""
        self.error_count += 1
        if show_console:
            print(f"❌ {message}")
        
        if exception:
            self.logger.error(f"{message}: {str(exception)}")
            self.logger.error(f"상세 오류 정보:\n{traceback.format_exc()}")
        else:
            self.logger.error(message)
    
    def debug(self, message, show_console=False):
        """디버그 로그"""
        if show_console:
            print(f"🔍 DEBUG: {message}")
        self.logger.debug(message)
    
    def step(self, step_name, details="", show_console=True):
        """단계별 진행 로그"""
        if show_console:
            print(f"🔄 {step_name}")
            if details:
                print(f"   {details}")
        self.logger.info(f"STEP: {step_name} - {details}")
    
    def url_processing(self, url, action, result=None, error=None):
        """URL 처리 관련 로그"""
        if error:
            self.error(f"URL 처리 실패 - {action}: {url}", error)
        else:
            self.success(f"URL 처리 성공 - {action}: {url}")
            if result:
                self.debug(f"URL 처리 결과: {result}")
    
    def web_scraping(self, site, query, result_count=0, error=None):
        """웹 스크래핑 관련 로그"""
        if error:
            self.error(f"웹 스크래핑 실패 - {site}: {query}", error)
        else:
            self.info(f"웹 스크래핑 성공 - {site}: {query} ({result_count}개 결과)")
    
    def content_generation(self, topic, stage, status, details=""):
        """콘텐츠 생성 관련 로그"""
        if status == "start":
            self.step(f"콘텐츠 생성 시작 - {stage}: {topic}", details)
        elif status == "success":
            self.success(f"콘텐츠 생성 성공 - {stage}: {topic}")
        elif status == "error":
            self.error(f"콘텐츠 생성 실패 - {stage}: {topic}", details)
    
    def api_call(self, service, endpoint, status, details=""):
        """API 호출 관련 로그"""
        if status == "success":
            self.success(f"API 호출 성공 - {service}: {endpoint}")
        else:
            self.error(f"API 호출 실패 - {service}: {endpoint}", details)
    
    def system_info(self, info_type, message):
        """시스템 정보 로그"""
        self.info(f"시스템 정보 - {info_type}: {message}")
    
    def performance_metric(self, operation, duration, details=""):
        """성능 메트릭 로그"""
        self.debug(f"성능 - {operation}: {duration:.2f}초 {details}")
    
    def get_summary(self):
        """로그 요약 정보 반환"""
        return {
            'errors': self.error_count,
            'warnings': self.warning_count,
            'log_file': f"logs/autotistory_{datetime.now().strftime('%Y%m%d')}.log"
        }
    
    def show_summary(self):
        """로그 요약 정보 출력"""
        summary = self.get_summary()
        print("\n📊 실행 요약:")
        print(f"   오류: {summary['errors']}개")
        print(f"   경고: {summary['warnings']}개")
        print(f"   로그 파일: {summary['log_file']}")
        
        if summary['errors'] > 0:
            print("\n💡 문제가 발생했습니다. 상세한 오류 정보는 로그 파일을 확인하세요.")

# 전역 로거 인스턴스
logger = EnhancedLogger()

# 편의 함수들
def log_info(message, show_console=True):
    """정보 로그"""
    logger.info(message, show_console)

def log_success(message, show_console=True):
    """성공 로그"""
    logger.success(message, show_console)

def log_warning(message, show_console=True):
    """경고 로그"""
    logger.warning(message, show_console)

def log_error(message, exception=None, show_console=True):
    """오류 로그"""
    logger.error(message, exception, show_console)

def log_debug(message, show_console=False):
    """디버그 로그"""
    logger.debug(message, show_console)

def log_step(step_name, details="", show_console=True):
    """단계별 진행 로그"""
    logger.step(step_name, details, show_console)

def log_url_processing(url, action, result=None, error=None):
    """URL 처리 로그"""
    logger.url_processing(url, action, result, error)

def log_web_scraping(site, query, result_count=0, error=None):
    """웹 스크래핑 로그"""
    logger.web_scraping(site, query, result_count, error)

def log_content_generation(topic, stage, status, details=""):
    """콘텐츠 생성 로그"""
    logger.content_generation(topic, stage, status, details)

def log_api_call(service, endpoint, status, details=""):
    """API 호출 로그"""
    logger.api_call(service, endpoint, status, details)

def show_log_summary():
    """로그 요약 표시"""
    logger.show_summary()

def with_logging(func):
    """로깅 데코레이터"""
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        log_debug(f"함수 시작: {func_name}")
        
        try:
            start_time = datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            logger.performance_metric(func_name, duration)
            
            return result
        except Exception as e:
            log_error(f"함수 오류: {func_name}", e)
            raise
    
    return wrapper

if __name__ == "__main__":
    # 테스트 코드
    print("🧪 향상된 로깅 시스템 테스트")
    print("=" * 40)
    
    # 다양한 로그 레벨 테스트
    log_info("정보 메시지 테스트")
    log_success("성공 메시지 테스트")
    log_warning("경고 메시지 테스트")
    log_error("오류 메시지 테스트")
    log_debug("디버그 메시지 테스트", show_console=True)
    
    # 단계별 로그 테스트
    log_step("테스트 단계 1", "테스트 세부사항")
    
    # URL 처리 로그 테스트
    log_url_processing("https://example.com", "유효성 검사", "성공")
    
    # 웹 스크래핑 로그 테스트
    log_web_scraping("구글", "테스트 쿼리", 5)
    
    # 콘텐츠 생성 로그 테스트
    log_content_generation("테스트 주제", "AI 생성", "success")
    
    # API 호출 로그 테스트
    log_api_call("OpenAI", "chat/completions", "success")
    
    # 로그 요약 표시
    show_log_summary() 