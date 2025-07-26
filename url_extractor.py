#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 콘텐츠 추출 모듈 - Streamlit 앱용
================================

뉴스 기사, 블로그 포스트, 유튜브 영상 등의 URL에서 
콘텐츠를 추출하여 블로그 글 생성에 활용하는 모듈
"""

import re
import requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import time
import openai
import os
from typing import Dict, Optional, List
import random

# streamlit import를 조건부로 처리
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    # streamlit이 없을 때를 위한 더미 함수
    def st_info(msg): print(f"INFO: {msg}")
    def st_success(msg): print(f"SUCCESS: {msg}")
    def st_warning(msg): print(f"WARNING: {msg}")
    def st_error(msg): print(f"ERROR: {msg}")
    st = type('st', (), {
        'info': st_info,
        'success': st_success,
        'warning': st_warning,
        'error': st_error
    })()

# YouTube 자막 추출을 위한 라이브러리 (선택적 import)
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
    YOUTUBE_TRANSCRIPT_AVAILABLE = True
except ImportError:
    YOUTUBE_TRANSCRIPT_AVAILABLE = False
    st.warning("⚠️ youtube-transcript-api가 설치되지 않아 유튜브 자막 추출 기능이 제한됩니다.")

class URLContentExtractor:
    """URL에서 콘텐츠를 추출하는 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_content_from_url(self, url: str) -> Dict:
        """
        URL에서 콘텐츠를 추출하는 메인 함수
        
        Args:
            url (str): 추출할 URL
            
        Returns:
            dict: 추출된 콘텐츠 정보
        """
        try:
            # URL 유형 판단
            url_type = self._detect_url_type(url)
            
            st.info(f"🔍 URL 타입 감지: {url_type}")
            st.info(f"📎 처리할 URL: {url}")
            
            if url_type == 'youtube':
                return self._extract_youtube_content(url)
            elif url_type == 'news':
                return self._extract_news_content(url)
            elif url_type == 'blog':
                return self._extract_blog_content(url)
            else:
                return self._extract_generic_content(url)
                
        except Exception as e:
            st.error(f"❌ URL 콘텐츠 추출 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'title': '',
                'content': '',
                'summary': '',
                'url': url
            }
    
    def _detect_url_type(self, url: str) -> str:
        """URL 타입을 감지하는 함수"""
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
            'tistory.com', 'blog.naver.com', 'blog.daum.net',
            'medium.com', 'wordpress.com', 'blogspot.com'
        ]
        
        for blog_domain in blog_domains:
            if blog_domain in domain:
                return 'blog'
        
        return 'generic'
    
    def _extract_youtube_content(self, url: str) -> Dict:
        """유튜브 영상에서 콘텐츠 추출"""
        try:
            video_id = self._extract_video_id(url)
            if not video_id:
                return {'success': False, 'error': '유효하지 않은 YouTube URL입니다.'}
            
            # 비디오 정보 가져오기
            video_info = self._get_youtube_video_info(video_id)
            
            # 자막 추출 시도
            transcript = self._get_youtube_transcript_web(video_id)

            # 자막이 정상적으로 추출된 경우에만 요약 생성
            if transcript and not (
                transcript.startswith('자막 추출 실패:') or
                transcript.startswith('자막을 찾을 수 없습니다.') or
                transcript.startswith('YouTube Transcript API가 설치되지 않아')
            ):
                summary = self._summarize_youtube_content(video_info, transcript)
                return {
                    'success': True,
                    'title': video_info.get('title', ''),
                    'content': summary,
                    'summary': summary,
                    'url': url,
                    'source_type': 'youtube',
                    'original_title': video_info.get('title', ''),
                    'video_id': video_id,
                    'duration': video_info.get('duration', ''),
                    'channel': video_info.get('channel', ''),
                    'transcript': transcript
                }
            else:
                # 자막이 없거나 추출 실패 시 안내 메시지 반환
                return {
                    'success': False,
                    'error': f'유튜브 자막을 추출할 수 없습니다.\n사유: {transcript}',
                    'title': video_info.get('title', ''),
                    'content': '',
                    'summary': '',
                    'url': url,
                    'source_type': 'youtube',
                    'original_title': video_info.get('title', ''),
                    'video_id': video_id,
                    'duration': video_info.get('duration', ''),
                    'channel': video_info.get('channel', ''),
                    'transcript': transcript
                }
        except Exception as e:
            return {'success': False, 'error': f'YouTube 콘텐츠 추출 실패: {str(e)}'}
    
    def _extract_news_content(self, url: str) -> Dict:
        """뉴스 기사에서 콘텐츠 추출"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 제목 추출
            title = ''
            title_selectors = ['h1', '.title', '.headline', '.article-title', 'title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    break
            
            # 본문 추출
            content = ''
            content_selectors = [
                '.article-content', '.news-content', '.content', 
                '.article-body', '.post-content', 'article'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 불필요한 요소 제거
                    for elem in content_elem.find_all(['script', 'style', 'nav', 'header', 'footer']):
                        elem.decompose()
                    content = content_elem.get_text().strip()
                    break
            
            if not content:
                # fallback: 모든 p 태그 수집
                paragraphs = soup.find_all('p')
                content = '\n\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50])
            
            # 요약 생성
            summary = self._summarize_news_content(title, content)
            
            return {
                'success': True,
                'title': title,
                'content': content,
                'summary': summary,
                'url': url,
                'source_type': 'news',
                'original_title': title
            }
            
        except Exception as e:
            return {'success': False, 'error': f'뉴스 콘텐츠 추출 실패: {str(e)}'}
    
    def _extract_blog_content(self, url: str) -> Dict:
        """블로그 포스트에서 콘텐츠 추출"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 제목 추출
            title = ''
            title_selectors = ['h1', '.post-title', '.entry-title', '.title', 'title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    break
            
            # 본문 추출
            content = ''
            content_selectors = [
                '.post-content', '.entry-content', '.content', 
                '.article-content', '.blog-content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 불필요한 요소 제거
                    for elem in content_elem.find_all(['script', 'style', 'nav', 'header', 'footer']):
                        elem.decompose()
                    content = content_elem.get_text().strip()
                    break
            
            # 메타 설명 추출
            meta_description = ''
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                meta_description = meta_desc.get('content', '')
            
            # 요약 생성
            summary = self._summarize_blog_content(title, content, meta_description)
            
            return {
                'success': True,
                'title': title,
                'content': content,
                'summary': summary,
                'url': url,
                'source_type': 'blog',
                'original_title': title,
                'meta_description': meta_description
            }
            
        except Exception as e:
            return {'success': False, 'error': f'블로그 콘텐츠 추출 실패: {str(e)}'}
    
    def _extract_generic_content(self, url: str) -> Dict:
        """일반 웹페이지에서 콘텐츠 추출"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 제목 추출
            title = ''
            title_elem = soup.find('title')
            if title_elem:
                title = title_elem.get_text().strip()
            
            # 본문 추출 (가장 긴 텍스트 블록)
            content = ''
            text_blocks = soup.find_all(['p', 'div', 'article', 'section'])
            
            longest_block = ''
            for block in text_blocks:
                text = block.get_text().strip()
                if len(text) > len(longest_block) and len(text) > 100:
                    longest_block = text
            
            content = longest_block
            
            # 요약 생성
            summary = self._summarize_generic_content(title, content)
            
            return {
                'success': True,
                'title': title,
                'content': content,
                'summary': summary,
                'url': url,
                'source_type': 'generic',
                'original_title': title
            }
            
        except Exception as e:
            return {'success': False, 'error': f'일반 콘텐츠 추출 실패: {str(e)}'}
    
    def _extract_video_id(self, url: str) -> Optional[str]:
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
    
    def _get_youtube_video_info(self, video_id: str) -> Dict:
        """YouTube 비디오 정보 가져오기"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 제목 추출
            title = ''
            title_elem = soup.find('title')
            if title_elem:
                title = title_elem.get_text().strip()
                title = title.replace(' - YouTube', '')
            
            # 채널명 추출
            channel = ''
            channel_elem = soup.find('link', attrs={'itemprop': 'name'})
            if channel_elem:
                channel = channel_elem.get('content', '')
            
            return {
                'title': title,
                'channel': channel,
                'video_id': video_id,
                'url': url
            }
            
        except Exception as e:
            st.warning(f"YouTube 비디오 정보 추출 실패: {e}")
            return {
                'title': f'YouTube Video {video_id}',
                'channel': 'Unknown',
                'video_id': video_id,
                'url': f"https://www.youtube.com/watch?v={video_id}"
            }
    
    def _get_youtube_transcript_web(self, video_id: str) -> str:
        """유튜브 자막 추출 (최신 youtube-transcript-api 호환)"""
        try:
            if not YOUTUBE_TRANSCRIPT_AVAILABLE:
                return "YouTube Transcript API가 설치되지 않아 자막을 가져올 수 없습니다."
            transcript_data = None
            # 한국어 우선
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
            except Exception:
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                except Exception:
                    try:
                        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
                    except Exception as e:
                        return f"자막 추출 실패: {str(e)}"
            if transcript_data:
                formatter = TextFormatter()
                return formatter.format_transcript(transcript_data)
            else:
                return "자막을 찾을 수 없습니다."
        except Exception as e:
            return f"자막 추출 실패: {str(e)}"
    
    def _summarize_youtube_content(self, video_info: Dict, transcript: str) -> str:
        """YouTube 콘텐츠 요약"""
        try:
            if not openai.api_key:
                return f"제목: {video_info.get('title', '')}\n\n내용: {transcript[:1000]}..."
            
            prompt = f"""
다음 YouTube 영상의 내용을 블로그 글 형태로 요약해주세요:

제목: {video_info.get('title', '')}
채널: {video_info.get('channel', '')}
자막 내용: {transcript[:2000]}

요구사항:
1. 800-1200자 정도의 블로그 글 형태로 작성
2. 구조화된 형태 (서론, 본론, 결론)
3. 핵심 내용을 명확하게 전달
4. 독자가 이해하기 쉽게 작성
"""
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"제목: {video_info.get('title', '')}\n\n내용: {transcript[:1000]}..."
    
    def _summarize_news_content(self, title: str, content: str) -> str:
        """뉴스 콘텐츠 요약"""
        try:
            if not openai.api_key:
                return content[:1000] + "..." if len(content) > 1000 else content
            
            prompt = f"""
다음 뉴스 기사를 블로그 글 형태로 요약해주세요:

제목: {title}
내용: {content[:2000]}

요구사항:
1. 800-1200자 정도의 블로그 글 형태로 작성
2. 구조화된 형태 (서론, 본론, 결론)
3. 핵심 내용을 명확하게 전달
4. 독자가 이해하기 쉽게 작성
"""
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return content[:1000] + "..." if len(content) > 1000 else content
    
    def _summarize_blog_content(self, title: str, content: str, meta_description: str) -> str:
        """블로그 콘텐츠 요약"""
        try:
            if not openai.api_key:
                return content[:1000] + "..." if len(content) > 1000 else content
            
            prompt = f"""
다음 블로그 포스트를 개선된 블로그 글 형태로 재구성해주세요:

제목: {title}
설명: {meta_description}
내용: {content[:2000]}

요구사항:
1. 800-1200자 정도의 개선된 블로그 글 형태로 작성
2. 구조화된 형태 (서론, 본론, 결론)
3. 핵심 내용을 명확하게 전달
4. 독자가 이해하기 쉽게 작성
5. SEO 최적화 고려
"""
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return content[:1000] + "..." if len(content) > 1000 else content
    
    def _summarize_generic_content(self, title: str, content: str) -> str:
        """일반 콘텐츠 요약"""
        try:
            if not openai.api_key:
                return content[:1000] + "..." if len(content) > 1000 else content
            
            prompt = f"""
다음 웹페이지 내용을 블로그 글 형태로 요약해주세요:

제목: {title}
내용: {content[:2000]}

요구사항:
1. 800-1200자 정도의 블로그 글 형태로 작성
2. 구조화된 형태 (서론, 본론, 결론)
3. 핵심 내용을 명확하게 전달
4. 독자가 이해하기 쉽게 작성
"""
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return content[:1000] + "..." if len(content) > 1000 else content

def generate_blog_from_url(url: str, custom_angle: str = "") -> Dict:
    """
    URL 기반 블로그 콘텐츠 생성
    
    Args:
        url (str): 콘텐츠를 추출할 URL
        custom_angle (str): 사용자가 지정한 관점이나 각도
        
    Returns:
        dict: 블로그 포스트 데이터
    """
    try:
        extractor = URLContentExtractor()
        result = extractor.extract_content_from_url(url)
        
        if not result['success']:
            return {
                'success': False,
                'error': result['error'],
                'title': '',
                'content': '',
                'tags': '',
                'source_url': url,
                'source_type': 'unknown'
            }
        
        # 태그 생성
        tags = generate_tags_from_content(result['title'], result['content'])
        
        return {
            'success': True,
            'title': result['title'],
            'content': result['content'],
            'tags': tags,
            'source_url': url,
            'source_type': result['source_type'],
            'original_title': result.get('original_title', ''),
            'summary': result.get('summary', '')
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'title': '',
            'content': '',
            'tags': '',
            'source_url': url,
            'source_type': 'unknown'
        }

def generate_tags_from_content(title: str, content: str) -> str:
    """콘텐츠에서 태그 생성"""
    try:
        if not openai.api_key:
            return "블로그, 정보, 가이드"
        
        prompt = f"""
다음 콘텐츠에 적합한 태그를 5-8개 생성해주세요:

제목: {title}
내용: {content[:500]}

요구사항:
1. 콤마로 구분된 태그 목록
2. 한국어 태그
3. 관련성 높은 태그
4. 검색에 유용한 태그
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        
        tags = response.choices[0].message.content.strip()
        return tags
        
    except Exception as e:
        return "블로그, 정보, 가이드" 