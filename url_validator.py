#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 유효성 검사 및 미리보기 모듈
================================

URL 콘텐츠 추출 전에 URL의 유효성을 검사하고
미리보기 정보를 제공하는 모듈
"""

import re
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time

class URLValidator:
    """URL 유효성 검사 및 미리보기 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def validate_url(self, url):
        """
        URL 유효성 검사
        
        Args:
            url (str): 검사할 URL
            
        Returns:
            dict: 검사 결과 정보
        """
        result = {
            'valid': False,
            'accessible': False,
            'type': 'unknown',
            'title': '',
            'description': '',
            'error': ''
        }
        
        try:
            # 1. URL 형식 검사
            if not self._is_valid_url_format(url):
                result['error'] = 'URL 형식이 올바르지 않습니다.'
                return result
            
            result['valid'] = True
            
            # 2. URL 타입 감지
            result['type'] = self._detect_url_type(url)
            
            # 3. 접근성 확인
            response = self.session.head(url, timeout=10, allow_redirects=True)
            if response.status_code in [200, 301, 302]:
                result['accessible'] = True
                
                # 4. 미리보기 정보 추출
                preview_info = self._get_preview_info(url)
                result.update(preview_info)
            else:
                result['error'] = f'HTTP 오류: {response.status_code}'
                
        except requests.exceptions.RequestException as e:
            result['error'] = f'네트워크 오류: {str(e)}'
        except Exception as e:
            result['error'] = f'알 수 없는 오류: {str(e)}'
            
        return result
    
    def _is_valid_url_format(self, url):
        """URL 형식 검사"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and bool(parsed.scheme)
        except:
            return False
    
    def _detect_url_type(self, url):
        """URL 타입 감지"""
        domain = urlparse(url).netloc.lower()
        
        # 유튜브 감지
        if 'youtube.com' in domain or 'youtu.be' in domain:
            return 'youtube'
        
        # 뉴스 사이트 감지
        news_domains = [
            'naver.com', 'daum.net', 'chosun.com', 'joongang.co.kr',
            'donga.com', 'hani.co.kr', 'khan.co.kr', 'ytn.co.kr',
            'sbs.co.kr', 'mbc.co.kr', 'kbs.co.kr', 'newsis.com',
            'yna.co.kr', 'mk.co.kr', 'mt.co.kr', 'edaily.co.kr',
            'bbc.com', 'cnn.com', 'reuters.com', 'ap.org'
        ]
        
        for news_domain in news_domains:
            if news_domain in domain:
                return 'news'
        
        # 블로그 플랫폼 감지
        blog_domains = [
            'tistory.com', 'blog.naver.com', 'brunch.co.kr',
            'medium.com', 'wordpress.com', 'blogger.com'
        ]
        
        for blog_domain in blog_domains:
            if blog_domain in domain:
                return 'blog'
        
        return 'website'
    
    def _get_preview_info(self, url):
        """미리보기 정보 추출"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 제목 추출
                title = self._extract_title(soup)
                
                # 설명 추출
                description = self._extract_description(soup)
                
                return {
                    'title': title,
                    'description': description
                }
        except:
            pass
        
        return {
            'title': '',
            'description': ''
        }
    
    def _extract_title(self, soup):
        """제목 추출"""
        # 1. og:title 메타 태그
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        # 2. title 태그
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # 3. h1 태그
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return ''
    
    def _extract_description(self, soup):
        """설명 추출"""
        # 1. og:description 메타 태그
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # 2. description 메타 태그
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # 3. 첫 번째 p 태그
        p_tag = soup.find('p')
        if p_tag:
            text = p_tag.get_text().strip()
            if len(text) > 50:
                return text[:200] + '...' if len(text) > 200 else text
        
        return ''

def validate_url_quick(url):
    """빠른 URL 유효성 검사"""
    validator = URLValidator()
    return validator.validate_url(url)

if __name__ == "__main__":
    # 테스트 코드
    test_urls = [
        "https://youtu.be/CcTlWxLKR80?si=W1wEtd-_AaPRrQSI",
        "https://news.naver.com/",
        "https://invalid-url"
    ]
    
    validator = URLValidator()
    
    for url in test_urls:
        print(f"\n🔍 URL 테스트: {url}")
        result = validator.validate_url(url)
        print(f"✅ 유효성: {'통과' if result['valid'] else '실패'}")
        print(f"🌐 접근성: {'가능' if result['accessible'] else '불가능'}")
        print(f"🏷️ 타입: {result['type']}")
        print(f"📄 제목: {result['title']}")
        print(f"📝 설명: {result['description']}")
        if result['error']:
            print(f"❌ 오류: {result['error']}") 