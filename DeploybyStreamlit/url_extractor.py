#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 콘텐츠 추출 모듈 - Streamlit 앱용
================================

뉴스 기사, 블로그 포스트, 유튜브 영상 등의 URL에서 
콘텐츠를 추출하여 블로그 글 생성에 활용하는 모듈
"""

import requests
import re
import json
from typing import Dict, Optional
from urllib.parse import urlparse
import time

def generate_blog_from_url(url: str, custom_angle: str = "") -> Dict:
    """URL에서 블로그 콘텐츠 생성"""
    try:
        # URL 유효성 검사
        if not url.startswith(('http://', 'https://')):
            return {
                'success': False,
                'error': '올바른 URL 형식이 아닙니다.'
            }
        
        # URL 타입 분류
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        if 'youtube.com' in domain or 'youtu.be' in domain:
            return extract_youtube_content(url, custom_angle)
        elif 'news.naver.com' in domain:
            return extract_naver_news_content(url, custom_angle)
        elif 'blog.naver.com' in domain:
            return extract_naver_blog_content(url, custom_angle)
        else:
            return extract_general_web_content(url, custom_angle)
            
    except Exception as e:
        return {
            'success': False,
            'error': f'콘텐츠 추출 중 오류: {str(e)}'
        }

def extract_youtube_content(url: str, custom_angle: str = "") -> Dict:
    """YouTube 콘텐츠 추출"""
    try:
        # YouTube Data API v3 사용
        api_key = "YOUR_YOUTUBE_API_KEY"  # 실제 사용시 API 키 필요
        
        # 비디오 ID 추출
        video_id = extract_video_id(url)
        if not video_id:
            return {
                'success': False,
                'error': 'YouTube 비디오 ID를 추출할 수 없습니다.'
            }
        
        # 기본 정보 반환 (실제 구현시 API 호출)
        return {
            'success': True,
            'title': f'YouTube 영상 분석',
            'content': f'YouTube 영상에서 추출한 콘텐츠입니다. URL: {url}',
            'tags': 'YouTube, 영상, 분석',
            'source_url': url,
            'source_type': 'youtube',
            'original_title': 'YouTube 영상'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'YouTube 콘텐츠 추출 실패: {str(e)}'
        }

def extract_naver_news_content(url: str, custom_angle: str = "") -> Dict:
    """네이버 뉴스 콘텐츠 추출"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 간단한 텍스트 추출 (실제 구현시 BeautifulSoup 사용)
        content = f'네이버 뉴스에서 추출한 콘텐츠입니다. URL: {url}'
        
        return {
            'success': True,
            'title': f'네이버 뉴스 분석',
            'content': content,
            'tags': '뉴스, 네이버, 분석',
            'source_url': url,
            'source_type': 'news',
            'original_title': '네이버 뉴스'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'네이버 뉴스 콘텐츠 추출 실패: {str(e)}'
        }

def extract_naver_blog_content(url: str, custom_angle: str = "") -> Dict:
    """네이버 블로그 콘텐츠 추출"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 간단한 텍스트 추출 (실제 구현시 BeautifulSoup 사용)
        content = f'네이버 블로그에서 추출한 콘텐츠입니다. URL: {url}'
        
        return {
            'success': True,
            'title': f'네이버 블로그 분석',
            'content': content,
            'tags': '블로그, 네이버, 분석',
            'source_url': url,
            'source_type': 'blog',
            'original_title': '네이버 블로그'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'네이버 블로그 콘텐츠 추출 실패: {str(e)}'
        }

def extract_general_web_content(url: str, custom_angle: str = "") -> Dict:
    """일반 웹사이트 콘텐츠 추출"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 간단한 텍스트 추출 (실제 구현시 BeautifulSoup 사용)
        content = f'웹사이트에서 추출한 콘텐츠입니다. URL: {url}'
        
        return {
            'success': True,
            'title': f'웹사이트 콘텐츠 분석',
            'content': content,
            'tags': '웹사이트, 분석',
            'source_url': url,
            'source_type': 'website',
            'original_title': '웹사이트 콘텐츠'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'웹사이트 콘텐츠 추출 실패: {str(e)}'
        }

def extract_video_id(url: str) -> Optional[str]:
    """YouTube URL에서 비디오 ID 추출"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

class URLContentExtractor:
    """URL 콘텐츠 추출 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_content(self, url: str) -> Dict:
        """URL에서 콘텐츠 추출"""
        return generate_blog_from_url(url) 