#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 콘텐츠 추출 모듈
================

뉴스 기사, 블로그 포스트, 유튜브 영상 등의 URL에서 
콘텐츠를 추출하여 블로그 글 생성에 활용하는 모듈
"""

import re
import requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import newspaper
from newspaper import Article
import feedparser
import time
import openai
import os
from dotenv import load_dotenv

# YouTube 자막 추출을 위한 라이브러리 (선택적 import)
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
    YOUTUBE_TRANSCRIPT_AVAILABLE = True
except ImportError:
    YOUTUBE_TRANSCRIPT_AVAILABLE = False
    print("⚠️ youtube-transcript-api가 설치되지 않아 유튜브 자막 추출 기능이 제한됩니다.")

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정 (기존 시스템과 동일한 방식)
openai.api_key = os.getenv("OPENAI_API_KEY")

class URLContentExtractor:
    """URL에서 콘텐츠를 추출하는 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_content_from_url(self, url):
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
            
            print(f"🔍 URL 타입 감지: {url_type}")
            print(f"📎 처리할 URL: {url}")
            
            if url_type == 'youtube':
                return self._extract_youtube_content(url)
            elif url_type == 'news':
                return self._extract_news_content(url)
            elif url_type == 'blog':
                return self._extract_blog_content(url)
            else:
                return self._extract_generic_content(url)
                
        except Exception as e:
            print(f"❌ URL 콘텐츠 추출 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'title': '',
                'content': '',
                'summary': '',
                'url': url
            }
    
    def _detect_url_type(self, url):
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
            'tistory.com', 'blog.naver.com', 'brunch.co.kr',
            'medium.com', 'wordpress.com', 'blogger.com'
        ]
        
        for blog_domain in blog_domains:
            if blog_domain in domain:
                return 'blog'
        
        return 'generic'
    
    def _extract_youtube_content(self, url):
        """유튜브 영상 콘텐츠 추출"""
        try:
            # 유튜브 영상 ID 추출
            video_id = self._extract_video_id(url)
            if not video_id:
                raise Exception("유튜브 영상 ID를 추출할 수 없습니다.")
            
            # 영상 정보 추출 (제목, 설명)
            video_info = self._get_youtube_video_info(video_id)
            
            # 자막 추출 시도 (YouTube Transcript API 없이 웹 스크래핑 방식)
            transcript = self._get_youtube_transcript_web(video_id)
            
            # AI를 이용한 콘텐츠 요약
            summary = self._summarize_youtube_content(video_info, transcript)
            
            return {
                'success': True,
                'type': 'youtube',
                'title': video_info.get('title', ''),
                'content': transcript,
                'summary': summary,
                'description': video_info.get('description', ''),
                'url': url,
                'video_id': video_id
            }
            
        except Exception as e:
            print(f"❌ 유튜브 콘텐츠 추출 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'title': '',
                'content': '',
                'summary': '',
                'url': url
            }
    
    def _extract_news_content(self, url):
        """뉴스 기사 콘텐츠 추출"""
        try:
            # newspaper3k 사용
            article = Article(url)
            article.download()
            article.parse()
            
            # 한국어 기사의 경우 추가 처리
            if not article.text:
                # BeautifulSoup을 사용한 보조 추출
                response = self.session.get(url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 뉴스 본문 추출 (일반적인 태그들)
                content_selectors = [
                    'article', '.article-body', '.news-content', 
                    '.content', '.post-content', '#newsContent',
                    '.article-content', '.news-article'
                ]
                
                content = ""
                for selector in content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        content = elements[0].get_text(strip=True)
                        break
                
                if not content:
                    # 텍스트 길이 기준으로 가장 긴 p 태그들 추출
                    paragraphs = soup.find_all('p')
                    long_paragraphs = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 100]
                    content = '\n\n'.join(long_paragraphs[:10])  # 상위 10개 문단
                
                article.text = content
            
            # AI를 이용한 뉴스 요약
            summary = self._summarize_news_content(article.title, article.text)
            
            return {
                'success': True,
                'type': 'news',
                'title': article.title or '',
                'content': article.text or '',
                'summary': summary,
                'authors': article.authors,
                'publish_date': article.publish_date,
                'url': url
            }
            
        except Exception as e:
            print(f"❌ 뉴스 콘텐츠 추출 실패: {e}")
            return self._extract_generic_content(url)
    
    def _extract_blog_content(self, url):
        """블로그 포스트 콘텐츠 추출"""
        try:
            # newspaper3k 사용
            article = Article(url)
            article.download()
            article.parse()
            
            # 추가 정보 추출
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 메타 정보 추출
            meta_description = ""
            meta_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
            if meta_tag:
                meta_description = meta_tag.get('content', '')
            
            # AI를 이용한 블로그 요약
            summary = self._summarize_blog_content(article.title, article.text, meta_description)
            
            return {
                'success': True,
                'type': 'blog',
                'title': article.title or '',
                'content': article.text or '',
                'summary': summary,
                'meta_description': meta_description,
                'authors': article.authors,
                'publish_date': article.publish_date,
                'url': url
            }
            
        except Exception as e:
            print(f"❌ 블로그 콘텐츠 추출 실패: {e}")
            return self._extract_generic_content(url)
    
    def _extract_generic_content(self, url):
        """일반 웹페이지 콘텐츠 추출"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 제목 추출
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
            
            # 본문 추출
            # 다양한 콘텐츠 선택자 시도
            content_selectors = [
                'main', 'article', '.content', '.post-content',
                '.entry-content', '.post-body', '.article-body',
                '.page-content', '#content', '.main-content'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text(strip=True)
                    break
            
            # 선택자로 찾지 못한 경우 p 태그들 추출
            if not content:
                paragraphs = soup.find_all('p')
                long_paragraphs = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50]
                content = '\n\n'.join(long_paragraphs[:15])
            
            # AI를 이용한 콘텐츠 요약
            summary = self._summarize_generic_content(title, content)
            
            return {
                'success': True,
                'type': 'generic',
                'title': title,
                'content': content,
                'summary': summary,
                'url': url
            }
            
        except Exception as e:
            print(f"❌ 일반 콘텐츠 추출 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'title': '',
                'content': '',
                'summary': '',
                'url': url
            }
    
    def _extract_video_id(self, url):
        """유튜브 URL에서 영상 ID 추출"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _get_youtube_video_info(self, video_id):
        """유튜브 영상 정보 추출 (제목, 설명)"""
        try:
            # 유튜브 페이지 직접 파싱
            url = f"https://www.youtube.com/watch?v={video_id}"
            response = self.session.get(url, timeout=10)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 제목 추출
            title = ""
            title_tag = soup.find('meta', attrs={'property': 'og:title'})
            if title_tag:
                title = title_tag.get('content', '')
            
            # 설명 추출
            description = ""
            desc_tag = soup.find('meta', attrs={'property': 'og:description'})
            if desc_tag:
                description = desc_tag.get('content', '')
            
            return {
                'title': title,
                'description': description
            }
            
        except Exception as e:
            print(f"❌ 유튜브 영상 정보 추출 실패: {e}")
            return {'title': '', 'description': ''}
    
    def _get_youtube_transcript_web(self, video_id):
        """유튜브 자막 추출 (YouTube Transcript API 사용)"""
        try:
            if not YOUTUBE_TRANSCRIPT_AVAILABLE:
                return "YouTube Transcript API가 설치되지 않아 자막을 가져올 수 없습니다. 영상 설명을 참고하세요."
            
            # 한국어 자막 우선 시도, 없으면 영어, 그 다음 자동 생성 자막
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 수동 한국어 자막 찾기
            try:
                transcript = transcript_list.find_manually_created_transcript(['ko'])
                formatter = TextFormatter()
                transcript_data = transcript.fetch()
                transcript_text = formatter.format_transcript(transcript_data)
                print(f"   ✅ 한국어 수동 자막 발견 (길이: {len(transcript_text)} 글자)")
                return transcript_text
            except:
                pass
            
            # 수동 영어 자막 찾기
            try:
                transcript = transcript_list.find_manually_created_transcript(['en'])
                formatter = TextFormatter()
                transcript_data = transcript.fetch()
                transcript_text = formatter.format_transcript(transcript_data)
                print(f"   ✅ 영어 수동 자막 발견 (길이: {len(transcript_text)} 글자)")
                return transcript_text
            except:
                pass
            
            # 자동 생성 자막 찾기 (한국어 우선)
            try:
                transcript = transcript_list.find_generated_transcript(['ko'])
                formatter = TextFormatter()
                transcript_data = transcript.fetch()
                transcript_text = formatter.format_transcript(transcript_data)
                print(f"   ✅ 한국어 자동 자막 발견 (길이: {len(transcript_text)} 글자)")
                return transcript_text
            except:
                pass
            
            # 자동 생성 자막 찾기 (영어)
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
                formatter = TextFormatter()
                transcript_data = transcript.fetch()
                transcript_text = formatter.format_transcript(transcript_data)
                print(f"   ✅ 영어 자동 자막 발견 (길이: {len(transcript_text)} 글자)")
                return transcript_text
            except:
                pass
            
            # 사용 가능한 첫 번째 자막 사용
            try:
                for transcript in transcript_list:
                    try:
                        formatter = TextFormatter()
                        transcript_data = transcript.fetch()
                        transcript_text = formatter.format_transcript(transcript_data)
                        language = transcript.language_code
                        print(f"   ✅ {language} 자막 발견 (길이: {len(transcript_text)} 글자)")
                        return transcript_text
                    except:
                        continue
            except:
                pass
            
            return "자막을 찾을 수 없습니다. 영상 설명을 참고하세요."
            
        except Exception as e:
            print(f"❌ 유튜브 자막 추출 실패: {e}")
            return "자막 추출에 실패했습니다. 영상 설명을 참고하세요."
    
    def _summarize_youtube_content(self, video_info, transcript):
        """유튜브 콘텐츠 요약"""
        if not os.getenv("OPENAI_API_KEY"):
            return "AI 요약을 위한 OpenAI API 키가 설정되지 않았습니다."
        
        try:
            content = f"제목: {video_info.get('title', '')}\n설명: {video_info.get('description', '')}\n자막: {transcript}"
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "유튜브 영상 내용을 블로그 글로 재구성하는 전문가입니다."},
                    {"role": "user", "content": f"다음 유튜브 영상 정보를 바탕으로 블로그 글을 위한 핵심 내용을 요약하고 재구성해주세요:\n\n{content}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ 유튜브 콘텐츠 요약 실패: {e}")
            return video_info.get('description', '')
    
    def _summarize_news_content(self, title, content):
        """뉴스 콘텐츠 요약"""
        if not os.getenv("OPENAI_API_KEY"):
            return "AI 요약을 위한 OpenAI API 키가 설정되지 않았습니다."
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "뉴스 기사를 블로그 글로 재구성하는 전문가입니다."},
                    {"role": "user", "content": f"다음 뉴스 기사를 바탕으로 블로그 글을 위한 핵심 내용을 요약하고 재구성해주세요:\n\n제목: {title}\n\n내용: {content[:3000]}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ 뉴스 콘텐츠 요약 실패: {e}")
            return content[:500] + "..."
    
    def _summarize_blog_content(self, title, content, meta_description):
        """블로그 콘텐츠 요약"""
        if not os.getenv("OPENAI_API_KEY"):
            return "AI 요약을 위한 OpenAI API 키가 설정되지 않았습니다."
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "블로그 포스트를 다른 관점에서 재구성하는 전문가입니다."},
                    {"role": "user", "content": f"다음 블로그 포스트를 바탕으로 새로운 블로그 글을 위한 핵심 내용을 요약하고 재구성해주세요:\n\n제목: {title}\n설명: {meta_description}\n\n내용: {content[:3000]}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ 블로그 콘텐츠 요약 실패: {e}")
            return content[:500] + "..."
    
    def _summarize_generic_content(self, title, content):
        """일반 콘텐츠 요약"""
        if not os.getenv("OPENAI_API_KEY"):
            return "AI 요약을 위한 OpenAI API 키가 설정되지 않았습니다."
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "웹 콘텐츠를 블로그 글로 재구성하는 전문가입니다."},
                    {"role": "user", "content": f"다음 웹 콘텐츠를 바탕으로 블로그 글을 위한 핵심 내용을 요약하고 재구성해주세요:\n\n제목: {title}\n\n내용: {content[:3000]}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ 일반 콘텐츠 요약 실패: {e}")
            return content[:500] + "..."


def generate_blog_from_url(url, custom_angle=""):
    """
    URL에서 추출한 콘텐츠를 바탕으로 블로그 글을 생성하는 함수
    
    Args:
        url (str): 콘텐츠를 추출할 URL
        custom_angle (str): 사용자가 지정한 관점이나 각도
        
    Returns:
        dict: 생성된 블로그 글 정보
    """
    extractor = URLContentExtractor()
    
    # 1. URL에서 콘텐츠 추출
    print("🔍 URL에서 콘텐츠 추출 중...")
    extracted_content = extractor.extract_content_from_url(url)
    
    if not extracted_content['success']:
        return {
            'success': False,
            'error': extracted_content['error'],
            'title': '',
            'content': '',
            'tags': ''
        }
    
    # 2. 추출된 콘텐츠를 바탕으로 블로그 글 생성
    print("🤖 추출된 콘텐츠를 바탕으로 블로그 글 생성 중...")
    
    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise Exception("OpenAI API 키가 설정되지 않았습니다.")
        
        # 프롬프트 구성
        source_info = f"원본 제목: {extracted_content['title']}\n원본 URL: {url}\n"
        source_content = extracted_content['summary'] or extracted_content['content']
        
        angle_instruction = f"\n관점/각도: {custom_angle}\n" if custom_angle else ""
        
        prompt = f"""다음 {extracted_content['type']} 콘텐츠를 바탕으로 전문적이고 풍부한 블로그 포스트를 작성해주세요.

{source_info}

원본 내용:
{source_content[:4000]}

{angle_instruction}

요구사항:
1. 원본 내용을 참고하되, 완전히 새로운 관점에서 재구성
2. 한국어로 작성하며, 전문적이고 깊이 있는 내용으로 구성
3. 블로그 독자에게 실용적이고 가치 있는 정보를 제공
4. 구체적인 사례, 데이터, 팁, 노하우를 포함
5. 독자의 궁금증을 해결할 수 있는 실용적인 조언 포함
6. 관련 업계 동향, 최신 정보, 전문가 관점을 반영
7. 독자가 실제로 적용할 수 있는 액션 플랜 제시
8. 적절한 제목과 구조화된 내용 (도입부, 본론, 결론)
9. 관련 키워드와 태그 포함

작성 가이드:
- 도입부: 주제의 중요성과 독자에게 미치는 영향 설명
- 본론: 구체적인 방법론, 사례, 팁, 주의사항 등을 상세히 설명
- 결론: 핵심 요약과 실천 방안 제시
- 각 섹션은 독자가 이해하기 쉽도록 명확하게 구분
- 전문 용어는 쉽게 설명하고, 실용적인 예시 포함

결과를 다음 형식으로 제공해주세요:
TITLE: [매력적이고 구체적인 블로그 제목]
CONTENT: [전문적이고 풍부한 블로그 본문 - 최소 2000자 이상]
TAGS: [관련 태그들을 쉼표로 구분]
"""

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "URL 기반 콘텐츠를 재구성하는 블로그 작성 전문가입니다. 전문적이고 깊이 있는 내용을 작성하며, 독자에게 실용적인 가치를 제공하는 것이 목표입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.8
        )
        
        generated_content = response.choices[0].message.content
        
        # 응답 파싱
        title = ""
        content = ""
        tags = ""
        
        lines = generated_content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('TITLE:'):
                current_section = 'title'
                title = line.replace('TITLE:', '').strip()
            elif line.startswith('CONTENT:'):
                current_section = 'content'
                content = line.replace('CONTENT:', '').strip()
            elif line.startswith('TAGS:'):
                current_section = 'tags'
                tags = line.replace('TAGS:', '').strip()
            elif current_section == 'content' and line:
                content += '\n' + line
            elif current_section == 'tags' and line:
                tags += ' ' + line
        
        return {
            'success': True,
            'title': title or extracted_content['title'],
            'content': content or extracted_content['summary'],
            'tags': tags,
            'source_url': url,
            'source_type': extracted_content['type'],
            'original_title': extracted_content['title']
        }
        
    except Exception as e:
        print(f"❌ 블로그 글 생성 실패: {e}")
        return {
            'success': False,
            'error': str(e),
            'title': extracted_content['title'],
            'content': extracted_content['summary'],
            'tags': ''
        }


if __name__ == "__main__":
    # 테스트 코드
    test_url = input("테스트할 URL을 입력하세요: ")
    custom_angle = input("특별한 관점이나 각도가 있다면 입력하세요 (선택사항): ")
    
    result = generate_blog_from_url(test_url, custom_angle)
    
    if result['success']:
        print("\n🎉 블로그 글 생성 성공!")
        print(f"제목: {result['title']}")
        print(f"태그: {result['tags']}")
        print(f"내용 길이: {len(result['content'])} 글자")
        print(f"\n내용 미리보기:\n{result['content'][:500]}...")
    else:
        print(f"\n❌ 실패: {result['error']}") 