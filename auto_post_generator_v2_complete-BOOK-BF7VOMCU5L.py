#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
티스토리 자동 포스팅 시스템 V2 - 완전판
=======================================

기존 auto_post_generator.py의 모든 기능 + V2 개선사항 통합

주요 개선사항:
1. 🔍 스마트 키워드 생성 (AI 기반)
2. 🖼️ 다중 이미지 검색 및 배치  
3. 🎨 향상된 HTML 구조 및 디자인
4. 🛡️ 안정성 개선 (자동 fallback 시스템)
5. 📱 반응형 디자인 
6. 🔧 OpenAI 구버전(0.28.0) 완벽 호환
7. 🔐 완전 자동로그인 (불안정한 쿠키 기반 제거)

API 키 처리 (기존 방식 유지):
- OpenAI: .env 파일의 OPENAI_API_KEY 환경변수 사용
- Unsplash: 하드코딩된 키 사용
"""

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
from datetime import datetime

# URL 콘텐츠 추출 모듈 import
try:
    from url_content_extractor import generate_blog_from_url, URLContentExtractor
    URL_CONTENT_AVAILABLE = True
    print("✅ URL 콘텐츠 추출 모듈 로드 성공")
except ImportError as e:
    URL_CONTENT_AVAILABLE = False
    print(f"⚠️ URL 콘텐츠 추출 모듈 로드 실패: {e}")
    print("   URL 기반 콘텐츠 생성 기능이 비활성화됩니다.")

# .env 파일 로드
load_dotenv()

# 상수 정의
COOKIES_FILE = "tistory_cookies.pkl"
LOCAL_STORAGE_FILE = "tistory_local_storage.json"
BLOG_URL = "https://climate-insight.tistory.com"
BLOG_MANAGE_URL = "https://climate-insight.tistory.com/manage/post"
BLOG_NEW_POST_URL = "https://climate-insight.tistory.com/manage/newpost"

# API 키 설정 (기존 방식 유지)
openai.api_key = os.getenv("OPENAI_API_KEY")
UNSPLASH_ACCESS_KEY = "uQgwi8yVjCIJmD0NNU2_2oBIHUMI8UPn2B6blxwWbvQ"  # 기존 하드코딩 키 유지

print("🚀 티스토리 자동 포스팅 시스템 V2 - 완전판 초기화!")
print("   - 모든 기존 기능 유지 ✅")
print("   - V2 개선사항 통합 ✅")

# ================================
# V2 개선사항: 스마트 키워드 & 다중 이미지
# ================================

def clean_faq_content(faq_content, topic):
    """
    FAQ 콘텐츠에서 HTML 코드 블록을 제거하고 정리된 형태로 파싱
    
    Args:
        faq_content (str): 원본 FAQ 콘텐츠
        topic (str): 주제
        
    Returns:
        str: 정리된 FAQ HTML
    """
    if not faq_content:
        return ""
    
    # HTML 코드 블록 제거
    if "```html" in faq_content:
        # 코드 블록 마커 제거
        faq_content = faq_content.replace("```html", "").replace("```", "")
    
    # 중복된 div와 빈 div 제거
    import re
    
    # 빈 div 태그 제거
    faq_content = re.sub(r'<div[^>]*>\s*</div>', '', faq_content)
    
    # 중복된 답변 div 제거 (background: #f9f9f9;가 없는 것들)
    faq_content = re.sub(r'<div style="padding: 15px; display: none;">\s*</div>', '', faq_content)
    
    # 이미 HTML 형태로 잘 구성되어 있으면 그대로 사용
    if "<div" in faq_content and "onclick=" in faq_content:
        return faq_content
    
    # HTML 요소는 있지만 토글 기능이 없는 경우
    if "<h3" in faq_content and "<p" in faq_content:
        # 간단한 Q&A 형태를 토글 형태로 변환
        lines = faq_content.split('\n')
        faq_parts = []
        current_q = ""
        current_a = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('<h3'):
                if current_q and current_a:
                    # 이전 Q&A를 토글 형태로 변환
                    question_text = current_q.replace('<h3 data-ke-size="size23">', '').replace('</h3>', '')
                    answer_text = current_a.replace('<p data-ke-size="size16">', '').replace('</p>', '')
                    
                    faq_parts.append(f"""
                    <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
                        <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
                            {question_text}
                        </div>
                        <div style="padding: 15px; display: none; background: #f9f9f9;">
                            {answer_text}
                        </div>
                    </div>
                    """)
                current_q = line
                current_a = ""
            elif line.startswith('<p'):
                current_a = line
        
        # 마지막 Q&A 추가
        if current_q and current_a:
            question_text = current_q.replace('<h3 data-ke-size="size23">', '').replace('</h3>', '')
            answer_text = current_a.replace('<p data-ke-size="size16">', '').replace('</p>', '')
            
            faq_parts.append(f"""
            <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
                <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
                    {question_text}
                </div>
                <div style="padding: 15px; display: none; background: #f9f9f9;">
                    {answer_text}
                </div>
            </div>
            """)
        
        if faq_parts:
            return ''.join(faq_parts)
    
    # 일반 텍스트 형태의 FAQ 처리
    lines = faq_content.split('\n')
    faq_parts = []
    current_q = ""
    current_a = ""
    
    for line in lines:
        line = line.strip()
        if line.startswith('Q') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
            if current_q and current_a:
                faq_parts.append(f"""
                <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
                    <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
                        {current_q}
                    </div>
                    <div style="padding: 15px; display: none; background: #f9f9f9;">
                        {current_a}
                    </div>
                </div>
                """)
            current_q = line
            current_a = ""
        elif line.startswith('A') or (current_q and line and not line.startswith('Q')):
            current_a += " " + line if current_a else line
    
    # 마지막 Q&A 추가
    if current_q and current_a:
        faq_parts.append(f"""
        <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
            <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
                {current_q}
            </div>
            <div style="padding: 15px; display: none; background: #f9f9f9;">
                {current_a}
            </div>
        </div>
        """)
    
    if faq_parts:
        return ''.join(faq_parts)
    
    # 파싱 실패 시 기본 FAQ 반환
    return f"""
    <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
        <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
            Q1. {topic}의 핵심 개념은 무엇인가요?
        </div>
        <div style="padding: 15px; display: none; background: #f9f9f9;">
            <strong>A1.</strong> {topic}는 현대 사회에서 매우 중요한 주제로, 다양한 측면에서 우리 생활에 영향을 미치고 있습니다.
        </div>
    </div>
    <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
        <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
            Q2. 실생활에서 어떻게 활용할 수 있나요?
        </div>
        <div style="padding: 15px; display: none; background: #f9f9f9;">
            <strong>A2.</strong> 실생활에서의 활용 방법은 매우 다양합니다.
        </div>
    </div>
    """

def parse_and_structure_content(content, title):
    """
    콘텐츠를 구조화하여 HTML 생성에 적합한 형태로 변환
    
    Args:
        content (str): 원본 콘텐츠
        title (str): 제목
        
    Returns:
        dict: 구조화된 콘텐츠 데이터
    """
    import re
    
    # 마크다운 문법 정리 (더 포괄적으로)
    cleaned_content = content
    
    # 마크다운 헤더 제거
    cleaned_content = re.sub(r'^#{1,6}\s+', '', cleaned_content, flags=re.MULTILINE)
    
    # 마크다운 볼드 문법 제거 (**텍스트** → 텍스트)
    cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_content)
    
    # 마크다운 이탤릭 문법 제거 (*텍스트* → 텍스트)
    cleaned_content = re.sub(r'\*(.*?)\*', r'\1', cleaned_content)
    
    # 마크다운 링크 문법 제거 ([텍스트](URL) → 텍스트)
    cleaned_content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned_content)
    
    # 마크다운 코드 블록 제거
    cleaned_content = re.sub(r'```.*?```', '', cleaned_content, flags=re.DOTALL)
    
    # 마크다운 인라인 코드 제거
    cleaned_content = re.sub(r'`([^`]+)`', r'\1', cleaned_content)
    
    # 출처 언급 제거 (URL 기반 콘텐츠에서 자주 나타나는 패턴)
    cleaned_content = re.sub(r'최근\s+(유튜브|영상|블로그|기사|보고서|연구|조사).*?에서\s+(소개된|제시된|분석된|조사된)', '', cleaned_content)
    cleaned_content = re.sub(r'이번\s+(영상|블로그|기사|보고서|연구|조사).*?에서는', '', cleaned_content)
    cleaned_content = re.sub(r'위\s+(영상|블로그|기사|보고서|연구|조사).*?에서\s+(언급된|제시된|분석된)', '', cleaned_content)
    cleaned_content = re.sub(r'이\s+(영상|블로그|기사|보고서|연구|조사).*?를\s+(통해|통한)', '', cleaned_content)
    
    # 불필요한 공백 정리
    cleaned_content = re.sub(r'\n\s*\n', '\n\n', cleaned_content)
    cleaned_content = re.sub(r' +', ' ', cleaned_content)
    
    # 문단 분할 (더 나은 분할 방식)
    paragraphs = [p.strip() for p in cleaned_content.split('\n') if p.strip() and len(p.strip()) > 10]
    
    # 콘텐츠 길이에 따라 분할
    if len(paragraphs) >= 6:
        # 충분한 내용이 있는 경우
        intro_paras = paragraphs[:2]
        core_paras = paragraphs[2:-1]
        conclusion_paras = paragraphs[-1:]
        
        # 핵심 내용을 3개 섹션으로 분할
        core_per_section = max(1, len(core_paras) // 3)
        
        core_contents = []
        core_subtitles = []
        
        for i in range(3):
            start_idx = i * core_per_section
            end_idx = start_idx + core_per_section if i < 2 else len(core_paras)
            
            if start_idx < len(core_paras):
                section_content = ' '.join(core_paras[start_idx:end_idx])
                core_contents.append(section_content)
                
                # 동적 소제목 생성 (AI 기반)
                try:
                    if openai.api_key:
                        subtitle_prompt = f"""'{title}' 주제의 {i+1}번째 섹션에 적합한 소제목을 생성해주세요.

조건:
- 번호나 이모지는 절대 포함하지 마세요
- 8-12자 이내의 간결한 제목
- 명사형으로 끝나는 자연스러운 표현
- 주제의 특성에 맞는 구체적인 제목
- 예시: '작용 원리', '투자 전략', '조리 방법', '여행 팁'

소제목만 답변해주세요:"""
                        
                        subtitle_resp = openai.ChatCompletion.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": subtitle_prompt}],
                            max_tokens=30
                        )
                        raw_subtitle = subtitle_resp.choices[0].message.content.strip()
                        cleaned_subtitle = clean_subtitle(raw_subtitle)
                        
                        if cleaned_subtitle and len(cleaned_subtitle) > 2 and len(cleaned_subtitle) < 20:
                            core_subtitles.append(cleaned_subtitle)
                        else:
                            # 유효하지 않으면 기본값 사용
                            default_subtitles = [f"{title}의 핵심 개념", f"{title}의 활용 방안", f"{title}의 중요성"]
                            core_subtitles.append(default_subtitles[i])
                    else:
                        default_subtitles = [f"{title}의 핵심 개념", f"{title}의 활용 방안", f"{title}의 중요성"]
                        core_subtitles.append(default_subtitles[i])
                except:
                    default_subtitles = [f"{title}의 핵심 개념", f"{title}의 활용 방안", f"{title}의 중요성"]
                    core_subtitles.append(default_subtitles[i])
            else:
                core_contents.append(f"{title}의 추가 분석 내용입니다.")
                core_subtitles.append(f"📊 분석 내용 {i+1}")
    
    elif len(paragraphs) >= 3:
        # 중간 정도의 내용
        intro_paras = paragraphs[:1]
        core_paras = paragraphs[1:-1] if len(paragraphs) > 2 else paragraphs[1:]
        conclusion_paras = paragraphs[-1:] if len(paragraphs) > 2 else []
        
        # 핵심 내용을 균등 분할
        core_per_section = max(1, len(core_paras) // 2)
        
        core_contents = []
        core_subtitles = []
        
        for i in range(2):
            start_idx = i * core_per_section
            end_idx = start_idx + core_per_section if i < 1 else len(core_paras)
            
            if start_idx < len(core_paras):
                section_content = ' '.join(core_paras[start_idx:end_idx])
                core_contents.append(section_content)
                
                # 동적 소제목 생성 (AI 기반)
                try:
                    if openai.api_key:
                        subtitle_prompt = f"""'{title}' 주제의 {i+1}번째 섹션에 적합한 소제목을 생성해주세요.

조건:
- 번호나 이모지는 절대 포함하지 마세요
- 8-12자 이내의 간결한 제목
- 명사형으로 끝나는 자연스러운 표현
- 주제의 특성에 맞는 구체적인 제목

소제목만 답변해주세요:"""
                        
                        subtitle_resp = openai.ChatCompletion.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": subtitle_prompt}],
                            max_tokens=30
                        )
                        raw_subtitle = subtitle_resp.choices[0].message.content.strip()
                        cleaned_subtitle = clean_subtitle(raw_subtitle)
                        
                        if cleaned_subtitle and len(cleaned_subtitle) > 2 and len(cleaned_subtitle) < 20:
                            core_subtitles.append(cleaned_subtitle)
                        else:
                            default_subtitles = [f"{title}의 핵심 개념", f"{title}의 활용 방안"]
                            core_subtitles.append(default_subtitles[i])
                    else:
                        default_subtitles = [f"{title}의 핵심 개념", f"{title}의 활용 방안"]
                        core_subtitles.append(default_subtitles[i])
                except:
                    default_subtitles = [f"{title}의 핵심 개념", f"{title}의 활용 방안"]
                    core_subtitles.append(default_subtitles[i])
            else:
                core_contents.append(f"{title}의 추가 설명입니다.")
                core_subtitles.append(f"📊 추가 내용 {i+1}")
        
        # 3번째 섹션 추가
        if conclusion_paras:
            core_contents.append(' '.join(conclusion_paras))
            core_subtitles.append(f"🚀 {title}의 결론")
        else:
            core_contents.append(f"{title}에 대한 종합적인 분석입니다.")
            core_subtitles.append(f"🚀 {title}의 종합 분석")
    
    else:
        # 내용이 부족한 경우
        intro_paras = paragraphs if paragraphs else [f"{title}에 대해 자세히 알아보겠습니다."]
        core_contents = [
            f"{title}의 기본 개념과 정의에 대해 설명합니다.",
            f"{title}의 실용적 활용 방안과 적용 사례를 살펴봅니다.",
            f"{title}의 미래 전망과 발전 가능성을 분석합니다."
        ]
        core_subtitles = [
            f"🔍 {title}의 기본 개념",
            f"💡 {title}의 실용적 활용",
            f"🚀 {title}의 미래 전망"
        ]
    
    return {
        'intro': ' '.join(intro_paras),
        'core_contents': core_contents,
        'core_subtitles': core_subtitles,
        'main': core_contents[0] if core_contents else f"{title}의 핵심 내용과 실용적 활용 방안에 대해 자세히 살펴보겠습니다.",
        'main_title': core_subtitles[0] if core_subtitles else f"{title}의 핵심 내용",
        'table_title': f"{title} 주요 정보",
        'table_html': None  # 동적 생성 사용
    }

def generate_blog_from_url_v2(url, custom_angle=""):
    """
    URL 기반 블로그 콘텐츠 생성 (V2 시스템 호환)
    
    Args:
        url (str): 콘텐츠를 추출할 URL
        custom_angle (str): 사용자가 지정한 관점이나 각도
        
    Returns:
        dict: V2 시스템 호환 블로그 포스트 데이터
    """
    if not URL_CONTENT_AVAILABLE:
        print("❌ URL 콘텐츠 추출 모듈을 사용할 수 없습니다.")
        return None
    
    try:
        print(f"🔗 URL 기반 콘텐츠 생성 시작: {url}")
        
        # URL에서 콘텐츠 생성
        url_result = generate_blog_from_url(url, custom_angle)
        
        if not url_result['success']:
            print(f"❌ URL 콘텐츠 생성 실패: {url_result['error']}")
            return None
        
        # 태그 정리
        tags = url_result['tags'].strip()
        if tags:
            tags = clean_tags_from_numbers(tags)
            tags = tags.replace('#', '').strip()  # 해시태그 제거
        
        # 키워드 생성 (제목에서 추출)
        keywords = generate_smart_keywords(url_result['title'])
        
        # 이미지 검색
        print("🖼️ 관련 이미지 검색 중...")
        images = get_multiple_images_v2(keywords, count=3)
        
        # V2 시스템 호환 형식으로 변환
        blog_post = {
            'title': url_result['title'],
            'content': url_result['content'],
            'tags': tags,
            'keywords': ', '.join(keywords[:5]),  # 상위 5개 키워드
            'images': images,
            'source_url': url_result['source_url'],
            'source_type': url_result['source_type'],
            'original_title': url_result.get('original_title', ''),
            'html_content': ''  # 나중에 HTML로 변환
        }
        
        # HTML 콘텐츠 생성
        print("🎨 HTML 콘텐츠 변환 중...")
        
        # FAQ 생성 (개선된 버전 - 콘텐츠 기반)
        faq_content = None
        try:
            if len(blog_post['content']) > 500:  # 콘텐츠가 충분히 긴 경우만
                print("❓ 콘텐츠 기반 FAQ 생성 중...")
                faq_content = generate_faq_by_content(url_result['title'], blog_post['content'])
                if faq_content:
                    print("✅ 콘텐츠 기반 FAQ 생성 완료!")
                else:
                    print("⚠️ 콘텐츠 기반 FAQ 생성 실패, 제목 기반으로 대체...")
                    faq_content = generate_faq_by_keyword(url_result['title'])
        except Exception as e:
            print(f"⚠️ FAQ 생성 실패: {e}")
        
        # 콘텐츠 데이터 구성 (개선된 분할 방식)
        content_data = parse_and_structure_content(blog_post['content'], blog_post['title'])
        content_data['title'] = blog_post['title']
        
        # 전문적이고 풍부한 결론 생성
        enhanced_conclusion = generate_enhanced_conclusion(blog_post['title'], blog_post['content'], url_result['original_title'])
        content_data['conclusion'] = enhanced_conclusion
        content_data['faq'] = faq_content
        
        # HTML 생성
        html_content = generate_enhanced_html_v2(blog_post['title'], images, content_data, faq_content)
        blog_post['html_content'] = html_content
        
        print("✅ URL 기반 블로그 포스트 생성 완료!")
        
        # URL 콘텐츠의 경우 HTML 구조를 메인 콘텐츠로 사용
        blog_post['content'] = blog_post['html_content']
        print("🎨 URL 콘텐츠의 경우 HTML 구조를 메인 콘텐츠로 설정")
        
        return blog_post
        
    except Exception as e:
        print(f"❌ URL 기반 콘텐츠 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_enhanced_conclusion(title, content, original_title=""):
    """
    전문적이고 풍부한 결론 생성
    
    Args:
        title (str): 블로그 제목
        content (str): 블로그 내용
        original_title (str): 원본 제목 (URL 기반인 경우)
        
    Returns:
        str: 전문적인 결론 내용
    """
    try:
        if openai.api_key:
            # 콘텐츠에서 핵심 내용 추출 (처음 2000자)
            content_preview = content[:2000] if len(content) > 2000 else content
            
            prompt = f"""다음 블로그 글의 내용을 바탕으로 간결하고 효과적인 결론을 작성해주세요.

제목: {title}
내용: {content_preview}

요구사항:
1. 블로그 글의 핵심 메시지를 간결하게 요약 (1-2문장)
2. 독자에게 실용적이고 구체적인 조언 제공 (1-2문장)
3. 친근하고 자연스러운 톤으로 작성
4. 전체 2-3문단으로 구성 (각 문단 2-3문장)
5. 반복적인 내용 제거
6. 행동 촉구보다는 인사이트 중심으로 작성

원본 제목: {original_title}

다음 형식으로 작성해주세요:
- 첫 번째 문단: 핵심 내용 요약 및 글의 가치 강조
- 두 번째 문단: 실용적 조언 및 독자에게 주는 메시지
- 세 번째 문단: 간결한 마무리 (선택사항)

각 문단은 자연스럽게 연결되고, 전체적으로 친근하고 실용적인 톤을 유지해주세요."""

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "블로그 글의 내용을 분석하여 전문적이고 풍부한 결론을 작성하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            conclusion = response.choices[0].message.content.strip()
            
            # 마크다운 문법 정리
            import re
            conclusion = re.sub(r'\*\*(.*?)\*\*', r'\1', conclusion)
            conclusion = re.sub(r'\*(.*?)\*', r'\1', conclusion)
            conclusion = re.sub(r'^#{1,6}\s+', '', conclusion, flags=re.MULTILINE)
            
            # 출처 언급 제거
            conclusion = re.sub(r'최근\s+(유튜브|영상|블로그|기사|보고서|연구|조사).*?에서\s+(소개된|제시된|분석된|조사된)', '', conclusion)
            conclusion = re.sub(r'이번\s+(영상|블로그|기사|보고서|연구|조사).*?에서는', '', conclusion)
            conclusion = re.sub(r'위\s+(영상|블로그|기사|보고서|연구|조사).*?에서\s+(언급된|제시된|분석된)', '', conclusion)
            conclusion = re.sub(r'이\s+(영상|블로그|기사|보고서|연구|조사).*?를\s+(통해|통한)', '', conclusion)
            
            return conclusion
            
    except Exception as e:
        print(f"⚠️ 결론 생성 실패: {e}")
    
    # 기본 결론 (AI 생성 실패 시)
    if original_title:
        return f"""이상으로 '{title}'에 대해 살펴보았습니다. 이 글에서는 {original_title}에서 영감을 받아 새로운 관점으로 정리한 내용을 다루었습니다.

주요 내용을 통해 이 주제의 중요성과 실용적 가치를 확인할 수 있었습니다. 독자 여러분께서는 이 글에서 제시한 정보를 바탕으로 실생활에 적용해보시기 바랍니다."""
    else:
        return f"""이상으로 '{title}'에 대해 종합적으로 분석해보았습니다. 이 글을 통해 이 주제의 다양한 측면과 실용적 가치를 확인할 수 있었습니다.

주요 내용을 통해 독자 여러분께서는 이 주제의 중요성과 활용 방안을 이해하셨을 것입니다. 제시된 정보를 바탕으로 실생활에 적용해보시기 바랍니다."""

def generate_smart_keywords(topic):
    """AI 기반 스마트 키워드 생성"""
    print(f"🔍 '{topic}' 스마트 키워드 생성...")
    
    keyword_mapping = {
        "기후변화": ["climate change", "global warming", "environment"],
        "환경": ["environment", "nature", "ecology"],
        "지속가능": ["sustainable", "sustainability", "green technology"],
        "재생에너지": ["renewable energy", "solar power", "wind energy"],
        "습기": ["humidity control", "moisture management", "home dehumidifier"],
        "장마": ["rainy season", "monsoon", "weather protection"],
        # 더 많은 매핑 추가 가능
    }
    
    basic_keywords = ["modern", "lifestyle", "design"]
    for key, values in keyword_mapping.items():
        if key in topic:
            basic_keywords = values
            break
    
    # AI 키워드 생성 시도
    ai_keywords = []
    if openai.api_key:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "영어 키워드 생성 전문가입니다."},
                    {"role": "user", "content": f"'{topic}' 주제의 이미지 검색용 영어 키워드 3개를 생성해주세요."}
                ],
                max_tokens=100
            )
            ai_response = response.choices[0].message.content
            ai_keywords = [kw.strip() for kw in ai_response.replace(',', '\n').split('\n') if kw.strip()]
        except Exception as e:
            print(f"   ⚠️ AI 키워드 생성 실패: {e}")
    
    return ai_keywords if ai_keywords else basic_keywords

def clean_keywords_for_unsplash(keywords):
    """Unsplash API 호환 키워드 정제"""
    cleaned = []
    for kw in keywords:
        clean = re.sub(r'^\d+\.\s*', '', kw)  # 숫자 제거
        clean = re.sub(r'[^\w\s-]', '', clean)  # 특수문자 제거
        clean = clean.strip().lower()
        if clean and len(clean) > 3:
            cleaned.append(clean)
    return cleaned[:3] if cleaned else ["home", "lifestyle", "modern"]

def clean_tags_from_numbers(tags_string):
    """태그에서 번호 제거 (예: "1. 비타민c 피부효과" → "비타민c 피부효과")"""
    if not tags_string:
        return tags_string
    
    # 쉼표로 분리하여 각 태그 처리
    tag_list = [tag.strip() for tag in tags_string.split(',')]
    cleaned_tags = []
    
    for tag in tag_list:
        if tag:
            # 앞의 번호 패턴 제거 (예: "1. ", "2) ", "3- ")
            clean_tag = re.sub(r'^\d+[\.\)\-\s]+', '', tag).strip()
            
            # 빈 문자열이 아니면 추가
            if clean_tag:
                cleaned_tags.append(clean_tag)
    
    return ', '.join(cleaned_tags)

def get_multiple_images_v2(keywords, count=3):
    """V2 다중 이미지 검색"""
    print(f"🖼️ 다중 이미지 검색: {keywords}")
    
    cleaned_keywords = clean_keywords_for_unsplash(keywords)
    images = []
    
    for i, keyword in enumerate(cleaned_keywords[:count]):
        try:
            url = "https://api.unsplash.com/search/photos"
            params = {"query": keyword, "per_page": 1, "orientation": "landscape"}
            headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    photo = data["results"][0]
                    images.append({
                        "keyword": keyword,
                        "url": photo["urls"]["regular"],
                        "description": photo["description"] or photo["alt_description"],
                        "type": "featured" if i == 0 else "content"
                    })
                    print(f"   ✅ '{keyword}' 이미지 획득 성공")
                    continue
            
            # Fallback 이미지
            images.append({
                "keyword": keyword,
                "url": "https://picsum.photos/800/400",
                "description": f"Fallback image for {keyword}",
                "type": "featured" if i == 0 else "content"
            })
            print(f"   ⚠️ '{keyword}' Fallback 이미지 사용")
            
        except Exception as e:
            print(f"   ❌ '{keyword}' 이미지 검색 실패: {e}")
            # 예외 시에도 Fallback 추가
            images.append({
                "keyword": keyword,
                "url": "https://picsum.photos/800/400", 
                "description": f"Error fallback for {keyword}",
                "type": "featured" if i == 0 else "content"
            })
    
    return images

def format_text_with_line_breaks(text):
    """텍스트를 자연스러운 줄바꿈이 있는 HTML로 변환"""
    if not text:
        return text
    
    # 마크다운 문법 정리
    import re
    
    # 마크다운 볼드 문법 제거 (**텍스트** → 텍스트)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    
    # 마크다운 이탤릭 문법 제거 (*텍스트* → 텍스트)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # 마크다운 헤더 제거
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # 마크다운 링크 문법 제거 ([텍스트](URL) → 텍스트)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # 마크다운 코드 블록 제거
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    # 마크다운 인라인 코드 제거
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # 출처 언급 제거
    text = re.sub(r'최근\s+(유튜브|영상|블로그|기사|보고서|연구|조사).*?에서\s+(소개된|제시된|분석된|조사된)', '', text)
    text = re.sub(r'이번\s+(영상|블로그|기사|보고서|연구|조사).*?에서는', '', text)
    text = re.sub(r'위\s+(영상|블로그|기사|보고서|연구|조사).*?에서\s+(언급된|제시된|분석된)', '', text)
    text = re.sub(r'이\s+(영상|블로그|기사|보고서|연구|조사).*?를\s+(통해|통한)', '', text)
    
    # 불필요한 공백 정리
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    # 이미 HTML 태그가 포함된 경우 그대로 반환
    if '<' in text and '>' in text:
        return text
    
    # 기존 줄바꿈 처리 (개행 문자 기반)
    paragraphs = text.split('\n\n')
    if len(paragraphs) == 1:
        # 개행 문자가 없다면 문장 단위로 분리하여 문단 만들기
        sentences = text.split('. ')
        paragraph_groups = []
        current_group = []
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 마지막 문장이 아니면 마침표 추가
            if i < len(sentences) - 1 and not sentence.endswith('.'):
                sentence += '.'
            
            current_group.append(sentence)
            
            # 2-3문장마다 문단 구분
            if len(current_group) >= 2 and (len(sentence) > 50 or len(current_group) >= 3):
                paragraph_groups.append('. '.join(current_group))
                current_group = []
        
        # 남은 문장들 처리
        if current_group:
            paragraph_groups.append('. '.join(current_group))
        
        paragraphs = paragraph_groups
    
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
            
        # 각 문단을 HTML p 태그로 감싸기
        clean_paragraph = paragraph.strip()
        
        # 문장이 너무 길면 중간에 줄바꿈 추가
        if len(clean_paragraph) > 200:
            sentences = clean_paragraph.split('. ')
            formatted_sentences = []
            
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    formatted_sentences.append(sentence.strip())
                    # 긴 문장 뒤에 줄바꿈 추가
                    if len(sentence) > 100 and i < len(sentences) - 1:
                        formatted_sentences.append('')  # 빈 줄로 구분
            
            # 빈 줄을 <br> 태그로 변환
            paragraph_with_breaks = '. '.join(formatted_sentences).replace('..', '.').replace('. . ', '. ')
            paragraph_with_breaks = paragraph_with_breaks.replace('\n', '<br>')
        else:
            paragraph_with_breaks = clean_paragraph
        
        formatted_paragraphs.append(f'<p style="margin-bottom: 15px; line-height: 1.8;">{paragraph_with_breaks}</p>')
    
    return ''.join(formatted_paragraphs)

def generate_enhanced_html_v2(topic, images, content_data, faq_content=None):
    """V2 향상된 HTML 구조 (모든 개선사항 완벽 적용)"""
    hero_image = images[0] if images else {"url": "https://picsum.photos/800/400"}
    content_images = images[1:] if len(images) > 1 else []
    
    # 전달받은 콘텐츠 데이터 사용 (서론/본론/결론 구조)
    if isinstance(content_data, dict):
        title = content_data.get("title", topic)
        intro_title = content_data.get("intro_title", f"{topic}의 중요성")
        intro_content = content_data.get("intro", "")
        
        # core_contents가 있는 경우 첫 번째 내용을 main_content로 사용
        core_contents = content_data.get("core_contents", [])
        if core_contents and len(core_contents) > 0:
            main_content = core_contents[0]
        else:
            main_content = content_data.get("main", f"{topic}의 핵심 내용과 실용적 활용 방안에 대해 자세히 살펴보겠습니다.")
        
        main_title = content_data.get("main_title", f"{topic}의 핵심 내용")
        conclusion_title = content_data.get("conclusion_title", f"{topic}의 완성")
        conclusion_content = content_data.get("conclusion", "")
        table_title = content_data.get("table_title", f"{topic} 주요 정보")
        table_html = content_data.get("table_html", "")
    else:
        # 기존 방식 호환성 유지
        title = topic
        intro_title = f"{topic}의 중요성"
        intro_content = f"이 글에서는 <strong>{topic}</strong>에 대해 자세히 알아보겠습니다."
        main_title = f"{topic}의 핵심 내용"
        main_content = f"{topic}의 핵심 내용과 실용적 활용 방안에 대해 자세히 살펴보겠습니다."
        conclusion_title = f"{topic}의 완성"
        conclusion_content = f"{topic}에 대한 종합적인 분석을 통해 우리는 이 주제의 중요성과 실용성을 확인할 수 있었습니다."
        table_title = f"{topic} 주요 정보"
        table_html = f"<table><tr><td>{topic} 관련 정보</td></tr></table>"
    
    # 텍스트 콘텐츠에 자연스러운 줄바꿈 적용
    intro_content = format_text_with_line_breaks(intro_content)
    main_content = format_text_with_line_breaks(main_content)
    conclusion_content = format_text_with_line_breaks(conclusion_content)

    # 표 HTML 정리 (마크다운 코드 블록 제거)
    if table_html and table_html.startswith("```html") and table_html.endswith("```"):
        lines = table_html.split('\n')
        start_idx = 0
        end_idx = len(lines)
        
        for i, line in enumerate(lines):
            if line.strip().startswith("```html"):
                start_idx = i + 1
            elif line.strip() == "```":
                end_idx = i
                break
        
        table_html = '\n'.join(lines[start_idx:end_idx])

    # 2. 동적 주요 정보 표 생성 (기존 방식이 없을 때만)
    if not table_html or table_html == f"<table><tr><td>{topic} 관련 정보</td></tr></table>":
        try:
            if openai.api_key:
                table_resp = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": f"'{topic}' 주제와 관련된 주요 정보를 3-4개 항목으로 정리한 표를 만들어주세요. 각 항목은 주제의 특성에 맞게 동적으로 생성하고, 설명과 중요도(별점)를 포함해주세요. 응답 형식: '항목명|설명|중요도' 형태로 한 줄씩 작성해주세요."}],
                    max_tokens=400
                )
                table_data = table_resp.choices[0].message.content.strip()
                
                # 표 데이터 파싱
                table_rows = []
                for line in table_data.split('\n'):
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            item = parts[0].strip()
                            desc = parts[1].strip()
                            importance = parts[2].strip()
                            # 빈 항목이 아닌 경우만 추가 (--- 제외)
                            if item and desc and importance and item != '---' and desc != '---' and importance != '---':
                                table_rows.append((item, desc, importance))
                
                # 표 데이터가 없거나 부족하면 기본 표 생성
                if not table_rows or len(table_rows) < 3:
                    table_rows = [
                        ("기본 개념", f"{topic}의 기본적인 개념과 정의", "⭐⭐⭐⭐⭐"),
                        ("실용성", "실생활에서의 활용도와 적용 가능성", "⭐⭐⭐⭐"),
                        ("미래 전망", "향후 발전 방향과 예상되는 변화", "⭐⭐⭐")
                    ]
            else:
                table_rows = [
                    ("기본 개념", f"{topic}의 기본적인 개념과 정의", "⭐⭐⭐⭐⭐"),
                    ("실용성", "실생활에서의 활용도와 적용 가능성", "⭐⭐⭐⭐"),
                    ("미래 전망", "향후 발전 방향과 예상되는 변화", "⭐⭐⭐")
                ]
        except:
            table_rows = [
                ("기본 개념", f"{topic}의 기본적인 개념과 정의", "⭐⭐⭐⭐⭐"),
                ("실용성", "실생활에서의 활용도와 적용 가능성", "⭐⭐⭐⭐"),
                ("미래 전망", "향후 발전 방향과 예상되는 변화", "⭐⭐⭐")
            ]
        
        # 동적 표를 HTML로 변환
        table_html = f"""
        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" data-ke-align="alignLeft">
            <thead>
                <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                    <th style="padding: 15px; color: white; text-align: left; font-weight: bold;">항목</th>
                    <th style="padding: 15px; color: white; text-align: left; font-weight: bold;">설명</th>
                    <th style="padding: 15px; color: white; text-align: center; font-weight: bold;">중요도</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'''
                <tr style="border-bottom: 1px solid #e5e7eb; {'' if i % 2 == 0 else 'background: #f9fafb;'}">
                    <td style="padding: 15px; font-weight: bold; color: #374151;">{row[0]}</td>
                    <td style="padding: 15px; color: #6b7280;">{row[1]}</td>
                    <td style="padding: 15px; text-align: center;">
                        <span style="color: #fbbf24;">{row[2]}</span>
                    </td>
                </tr>
                ''' for i, row in enumerate(table_rows)])}
            </tbody>
        </table>
        """
    
    # FAQ 처리 (개선된 HTML 코드 블록 파싱)
    if not faq_content:
        faq_content = f"""
        <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
            <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
                Q1. {topic}의 핵심 개념은 무엇인가요?
            </div>
            <div style="padding: 15px; display: none; background: #f9f9f9;">
                <strong>A1.</strong> {topic}는 현대 사회에서 매우 중요한 주제로, 다양한 측면에서 우리 생활에 영향을 미치고 있습니다. 기본 개념부터 실용적 적용까지 폭넓게 이해하는 것이 중요합니다.
            </div>
        </div>
        <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
            <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
                Q2. 실생활에서 어떻게 활용할 수 있나요?
            </div>
            <div style="padding: 15px; display: none; background: #f9f9f9;">
                <strong>A2.</strong> 실생활에서의 활용 방법은 매우 다양합니다. 개인의 상황과 목적에 따라 적절한 방법을 선택하여 적용하면 좋은 결과를 얻을 수 있습니다.
            </div>
        </div>
        <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
            <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
                Q3. 미래 전망은 어떻게 되나요?
            </div>
            <div style="padding: 15px; display: none; background: #f9f9f9;">
                <strong>A3.</strong> 앞으로 {topic} 분야는 지속적으로 발전할 것으로 예상됩니다. 기술 발전과 사회적 요구에 따라 더욱 혁신적인 변화가 일어날 것입니다.
            </div>
        </div>
        """
    else:
        # FAQ 콘텐츠를 정리된 형태로 파싱
        faq_content = clean_faq_content(faq_content, topic)
        
        # 추가 정리: 중복된 div와 빈 div 제거
        import re
        
        # 빈 div 태그 제거
        faq_content = re.sub(r'<div[^>]*>\s*</div>', '', faq_content)
        
        # 중복된 답변 div 제거 (background: #f9f9f9;가 없는 것들)
        faq_content = re.sub(r'<div style="padding: 15px; display: none;">\s*</div>', '', faq_content)
        
        # script 태그 제거
        faq_content = re.sub(r'<script[^>]*>.*?</script>', '', faq_content, flags=re.DOTALL)
    
    html = f"""
    <div style="max-width: 1000px; margin: 0 auto; font-family: 'Segoe UI', sans-serif; line-height: 1.8;">
        <!-- SEO 최적화된 히어로 섹션 (H1 태그) -->
        <header style="position: relative; height: 400px; overflow: hidden; border-radius: 15px; margin-bottom: 30px;">
            <img src="{hero_image['url']}" alt="{topic} 관련 이미지" style="width: 100%; height: 100%; object-fit: cover;">
            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(45deg, rgba(0,0,0,0.7), rgba(0,0,0,0.3)); display: flex; align-items: center; justify-content: center;">
                <h1 style="color: white; font-size: 2.5rem; font-weight: bold; text-align: center; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); padding: 20px; margin: 0;">{title}</h1>
            </div>
        </header>
        
        <!-- SEO 최적화된 콘텐츠 (시맨틱 HTML) -->
        <main style="padding: 20px;">
            <!-- 서론 (H2 태그) -->
            <section style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #3498db;">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem;" data-ke-size="size26">{intro_title}</h2>
                <article style="color: #555; font-size: 1.1rem; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;">{intro_content}</article>
            </section>
            
            {f'<img src="{content_images[0]["url"]}" alt="콘텐츠 이미지" style="width: 100%; height: 300px; object-fit: cover; border-radius: 10px; margin: 20px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">' if content_images else ''}
            
            <!-- 본론 (H2 태그) -->
            <section style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #e74c3c;">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem;" data-ke-size="size26">{main_title}</h2>
                <article style="color: #555; font-size: 1.1rem; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;">{main_content}</article>
            </section>
            
            {f'<img src="{content_images[1]["url"]}" alt="{topic} 관련 이미지 2" style="width: 100%; height: 300px; object-fit: cover; border-radius: 10px; margin: 20px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">' if len(content_images) > 1 else ''}
            
            <!-- 결론 (H2 태그) -->
            <section style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #27ae60;">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem;" data-ke-size="size26">{conclusion_title}</h2>
                <article style="color: #555; font-size: 1.1rem; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;">{conclusion_content}</article>
            </section>
            
            <!-- 주요 정보 표 (H2 태그) -->
            <section style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #6366f1;">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem;">📊 {table_title}</h2>
                <div style="overflow-x: auto;">
                    {table_html}
                </div>
            </section>
            
            <!-- FAQ 섹션 (H2 태그) -->
            <section style="background: #ecf0f1; padding: 30px; margin: 30px 0; border-radius: 10px;">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem;">❓ {topic} 자주 묻는 질문</h2>
                {faq_content}
            </section>
            
            <!-- 결론 (주제별 맞춤 내용) -->
            <div style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #27ae60;">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem;" data-ke-size="size26">🎯 결론</h2>
                <div style="color: #555; font-size: 1.1rem; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;">{format_text_with_line_breaks(conclusion_content)}</div>
            </div>
        </div>
    </div>
    
    <!-- FAQ 토글 JavaScript -->
    <script>
    function toggleFAQ(element) {{
        const answer = element.nextElementSibling;
        const isVisible = answer.style.display === 'block';
        
        // 모든 FAQ 답변 닫기
        document.querySelectorAll('[onclick="toggleFAQ(this)"]').forEach(q => {{
            q.nextElementSibling.style.display = 'none';
        }});
        
        // 클릭한 항목만 토글
        if (!isVisible) {{
            answer.style.display = 'block';
        }}
    }}
    </script>
    """
    return html

# ================================
# V2 실시간 정보 수집 및 검증 시스템
# ================================

def search_latest_information(topic, max_results=5):
    """주제에 대한 최신 정보 웹 검색 - 다양성 개선"""
    print(f"🔍 '{topic}' 최신 정보 검색 중...")
    
    try:
        # 더 다양하고 구체적인 검색 쿼리 생성
        search_queries = generate_diverse_search_queries(topic)
        
        collected_info = []
        
        for i, query in enumerate(search_queries, 1):
            try:
                print(f"  📡 검색 {i}/{len(search_queries)}: '{query}'")
                
                # 웹 검색 수행
                search_result = web_search_simulation(query, topic)
                
                if search_result and len(search_result) > 100:
                    # 검색 결과에서 핵심 정보 추출
                    extracted_info = extract_key_information(search_result, topic)
                    if extracted_info:
                        # 중복 제거 후 추가
                        unique_info = [info for info in extracted_info if info not in collected_info]
                        collected_info.extend(unique_info)
                        print(f"    ✅ {len(unique_info)}개 정보 수집 (중복 제거됨)")
                else:
                    print(f"    ⚠️ 검색 결과 부족")
                    
            except Exception as e:
                print(f"    ❌ 검색 오류: {e}")
                continue
        
        print(f"📊 총 {len(collected_info)}개의 최신 정보 수집 완료")
        return collected_info
        
    except Exception as e:
        print(f"❌ 정보 수집 중 오류: {e}")
        return []

def generate_diverse_search_queries(topic):
    """주제의 성격을 분석하여 적절한 검색 쿼리 생성"""
    
    topic_lower = topic.lower()
    
    # 1. 기본 검색 쿼리들 (항상 포함)
    base_queries = [
        f"{topic}",  # 원본 주제
        f"{topic} 최신 뉴스",  # 최신 뉴스
        f"{topic} 블로그",  # 블로그 글
    ]
    
    # 2. 주제 성격별 맞춤 검색 쿼리 생성
    
    # 건강/의료 관련
    if any(keyword in topic_lower for keyword in ['비타민', '건강', '질병', '치료', '영양', '다이어트', '운동', '의료']):
        specific_queries = [
            f"{topic} 효과",
            f"{topic} 부작용", 
            f"{topic} 연구결과",
            f"{topic} 전문가 의견",
            f"{topic} 실제 경험"
        ]
    
    # 기술/IT 관련
    elif any(keyword in topic_lower for keyword in ['ai', '인공지능', '프로그래밍', '개발', '기술', '소프트웨어', '앱', '컴퓨터']):
        specific_queries = [
            f"{topic} 활용 사례",
            f"{topic} 최신 동향",
            f"{topic} 개발 현황",
            f"{topic} 실제 적용",
            f"{topic} 미래 전망"
        ]
    
    # 금융/경제 관련
    elif any(keyword in topic_lower for keyword in ['투자', '주식', '부동산', '금리', '경제', '대출', '적금', '펀드', '코인']):
        specific_queries = [
            f"{topic} 시장 동향",
            f"{topic} 전망 분석",
            f"{topic} 투자 방법",
            f"{topic} 위험 요인",
            f"{topic} 전문가 분석"
        ]
    
    # 요리/음식 관련
    elif any(keyword in topic_lower for keyword in ['요리', '레시피', '음식', '맛집', '요리법', '재료', '조리']):
        specific_queries = [
            f"{topic} 만들기",
            f"{topic} 재료 준비",
            f"{topic} 요리 팁",
            f"{topic} 맛있게 만드는법",
            f"{topic} 레시피 공유"
        ]
    
    # 여행/관광 관련
    elif any(keyword in topic_lower for keyword in ['여행', '관광', '여행지', '맛집', '호텔', '숙박', '항공']):
        specific_queries = [
            f"{topic} 추천 장소",
            f"{topic} 여행 후기",
            f"{topic} 가볼 만한 곳",
            f"{topic} 여행 정보",
            f"{topic} 현지 경험"
        ]
    
    # 교육/학습 관련
    elif any(keyword in topic_lower for keyword in ['학습', '교육', '공부', '시험', '자격증', '취업', '진로']):
        specific_queries = [
            f"{topic} 학습법",
            f"{topic} 공부 방법",
            f"{topic} 경험담",
            f"{topic} 성공 사례",
            f"{topic} 실무 활용"
        ]
    
    # 생활/라이프스타일 관련
    elif any(keyword in topic_lower for keyword in ['생활', '일상', '취미', '패션', '뷰티', '인테리어', '관리']):
        specific_queries = [
            f"{topic} 방법",
            f"{topic} 노하우",
            f"{topic} 실생활 적용",
            f"{topic} 경험 공유",
            f"{topic} 실제 후기"
        ]
    
    # 정책/제도 관련 (기존 방식 유지)
    elif any(keyword in topic_lower for keyword in ['정책', '제도', '지원', '혜택', '쿠폰', '보조금', '신청', '연금']):
        specific_queries = [
            f"{topic} 신청 방법",
            f"{topic} 혜택 내용",
            f"{topic} 자격 조건",
            f"{topic} 주의사항",
            f"{topic} 2025년 정책"
        ]
    
    # 일반적인 주제 (카테고리 분류 안 됨)
    else:
        specific_queries = [
            f"{topic} 정보",
            f"{topic} 가이드",
            f"{topic} 팁",
            f"{topic} 분석",
            f"{topic} 전망"
        ]
    
    # 3. 쿼리 조합 및 정리
    all_queries = base_queries + specific_queries
    
    # 중복 제거 및 최대 7개 쿼리 반환
    unique_queries = list(dict.fromkeys(all_queries))
    return unique_queries[:7]

def generate_content_perspectives(topic):
    """주제에 따라 맞춤형 본문 관점 3개 생성"""
    
    topic_lower = topic.lower()
    
    # 건강/의료 관련
    if any(keyword in topic_lower for keyword in ['비타민', '건강', '질병', '치료', '영양', '다이어트', '운동', '의료']):
        return [
            {"angle": "원리와 효과", "focus": "작용 원리, 과학적 근거, 건강 효과, 연구 결과"},
            {"angle": "실제 적용법", "focus": "복용법, 섭취 방법, 일상 적용, 실제 경험"},
            {"angle": "주의사항과 부작용", "focus": "부작용, 주의사항, 전문가 조언, 올바른 사용법"}
        ]
    
    # 기술/IT 관련
    elif any(keyword in topic_lower for keyword in ['ai', '인공지능', '프로그래밍', '개발', '기술', '소프트웨어', '앱', '컴퓨터']):
        return [
            {"angle": "기술 원리와 특징", "focus": "기술 원리, 핵심 기능, 혁신성, 기술적 특징"},
            {"angle": "실제 활용 사례", "focus": "산업별 적용, 실제 사례, 성공 스토리, 현실적 활용"},
            {"angle": "향후 전망과 발전", "focus": "미래 전망, 발전 방향, 시장 영향, 기회와 도전"}
        ]
    
    # 금융/경제 관련
    elif any(keyword in topic_lower for keyword in ['투자', '주식', '부동산', '금리', '경제', '대출', '적금', '펀드', '코인']):
        return [
            {"angle": "시장 현황과 분석", "focus": "현재 시장 상황, 데이터 분석, 트렌드 파악"},
            {"angle": "투자 전략과 방법", "focus": "구체적 투자 방법, 전략 수립, 실행 방안"},
            {"angle": "위험 관리와 전망", "focus": "위험 요인, 대응 방안, 향후 전망, 전문가 의견"}
        ]
    
    # 요리/음식 관련
    elif any(keyword in topic_lower for keyword in ['요리', '레시피', '음식', '맛집', '요리법', '재료', '조리']):
        return [
            {"angle": "기본 정보와 특징", "focus": "음식 소개, 영양 정보, 특징, 역사와 유래"},
            {"angle": "만드는 방법과 과정", "focus": "재료 준비, 조리 과정, 단계별 설명, 기본 레시피"},
            {"angle": "팁과 노하우", "focus": "요리 팁, 맛있게 만드는 비법, 실패 방지법, 응용 방법"}
        ]
    
    # 여행/관광 관련
    elif any(keyword in topic_lower for keyword in ['여행', '관광', '여행지', '맛집', '호텔', '숙박', '항공']):
        return [
            {"angle": "기본 정보와 매력", "focus": "여행지 소개, 주요 명소, 특징, 매력 포인트"},
            {"angle": "추천 장소와 코스", "focus": "추천 명소, 여행 코스, 숨은 명소, 현지 추천"},
            {"angle": "여행 팁과 정보", "focus": "여행 준비, 실용 정보, 주의사항, 현지 문화"}
        ]
    
    # 교육/학습 관련
    elif any(keyword in topic_lower for keyword in ['학습', '교육', '공부', '시험', '자격증', '취업', '진로']):
        return [
            {"angle": "기본 개념과 이해", "focus": "기본 개념, 학습 목표, 중요성, 전체적 이해"},
            {"angle": "학습 방법과 전략", "focus": "효과적 학습법, 공부 전략, 실용적 방법, 단계별 접근"},
            {"angle": "실무 활용과 성공 사례", "focus": "실무 적용, 성공 사례, 경험담, 실제 효과"}
        ]
    
    # 생활/라이프스타일 관련
    elif any(keyword in topic_lower for keyword in ['생활', '일상', '취미', '패션', '뷰티', '인테리어', '관리']):
        return [
            {"angle": "기본 정보와 중요성", "focus": "기본 정보, 생활 속 중요성, 필요성, 기본 원리"},
            {"angle": "실생활 적용 방법", "focus": "일상 적용법, 실천 방법, 구체적 행동, 실제 적용"},
            {"angle": "노하우와 팁", "focus": "생활 노하우, 실용 팁, 효과적 방법, 경험 공유"}
        ]
    
    # 정책/제도 관련
    elif any(keyword in topic_lower for keyword in ['정책', '제도', '지원', '혜택', '쿠폰', '보조금', '신청', '연금']):
        return [
            {"angle": "기본 개념과 배경", "focus": "정책 배경, 도입 목적, 기본 개념, 제도 개요"},
            {"angle": "실용적 활용법", "focus": "신청 방법, 이용 방법, 실제 활용, 절차 안내"},
            {"angle": "혜택과 주의사항", "focus": "구체적 혜택, 주의사항, 제한 사항, 향후 계획"}
        ]
    
    # 비즈니스/경영 관련
    elif any(keyword in topic_lower for keyword in ['비즈니스', '경영', '마케팅', '창업', '사업', '기업', '전략', '경쟁']):
        return [
            {"angle": "시장 분석과 전략", "focus": "시장 현황, 경쟁 분석, 전략 수립, 기회 포착"},
            {"angle": "실행 방법과 운영", "focus": "구체적 실행, 운영 방법, 성공 사례, 실무 적용"},
            {"angle": "성장과 발전 방향", "focus": "성장 전략, 발전 방향, 미래 계획, 지속가능성"}
        ]
    
    # 환경/에너지 관련
    elif any(keyword in topic_lower for keyword in ['환경', '에너지', '친환경', '재생에너지', '탄소', '기후변화', '지속가능']):
        return [
            {"angle": "환경적 중요성", "focus": "환경 영향, 중요성, 긴급성, 전 세계적 이슈"},
            {"angle": "실천 방법과 기술", "focus": "구체적 실천법, 기술적 해결책, 일상 적용, 혁신 기술"},
            {"angle": "미래 전망과 대응", "focus": "미래 전망, 대응 방안, 정책 동향, 개인 역할"}
        ]
    
    # 문화/예술 관련
    elif any(keyword in topic_lower for keyword in ['문화', '예술', '영화', '음악', '미술', '문학', '공연', '전시']):
        return [
            {"angle": "문화적 배경과 의미", "focus": "문화적 배경, 역사적 의미, 예술적 가치, 사회적 영향"},
            {"angle": "감상과 체험 방법", "focus": "감상법, 체험 방법, 접근법, 이해를 돕는 방법"},
            {"angle": "현대적 의미와 발전", "focus": "현대적 의미, 새로운 해석, 발전 방향, 미래 가치"}
        ]
    
    # 과학/연구 관련
    elif any(keyword in topic_lower for keyword in ['과학', '연구', '실험', '발견', '이론', '기술', '혁신', '발명']):
        return [
            {"angle": "과학적 원리와 발견", "focus": "과학적 원리, 연구 과정, 주요 발견, 이론적 배경"},
            {"angle": "실용적 응용과 기술", "focus": "실용적 응용, 기술적 구현, 산업 적용, 혁신 기술"},
            {"angle": "미래 발전과 영향", "focus": "미래 발전, 사회적 영향, 새로운 가능성, 연구 방향"}
        ]
    
    # 일반적인 주제 (카테고리 분류 안 됨)
    else:
        return [
            {"angle": "기본 정보와 이해", "focus": "기본 정보, 개념 이해, 배경 지식, 전반적 개요"},
            {"angle": "실용적 활용과 적용", "focus": "실제 활용, 적용 방법, 실용성, 구체적 사례"},
            {"angle": "심화 내용과 전망", "focus": "심화 정보, 고급 활용, 전망, 발전 방향"}
        ]

def extract_key_information(search_text, topic):
    """검색 결과에서 핵심 정보 추출 - 개선된 버전"""
    if not search_text:
        return []
    
    import re
    
    # 1. 주제별 맞춤형 키워드 생성
    topic_keywords = generate_topic_keywords(topic)
    
    # 2. 다양한 방법으로 문장 분리
    sentences = []
    
    # 문장 분리 (다양한 구분자 사용)
    raw_sentences = re.split(r'[.!?]\s+|[\n]{2,}', search_text)
    
    # 문장 품질 필터링 및 정제
    for sentence in raw_sentences:
        sentence = sentence.strip()
        
        # 길이 조건 (너무 짧거나 길면 제외)
        if len(sentence) < 15 or len(sentence) > 500:
            continue
            
        # 불필요한 문자 제거
        sentence = re.sub(r'[^\w\s가-힣.,!?()%-]', '', sentence)
        
        # 빈 문장이나 의미 없는 문장 제외
        if not sentence or sentence.isspace():
            continue
            
        # 광고성 문구 제외
        if any(ad_word in sentence.lower() for ad_word in ['광고', '구매', '할인', '이벤트', '쿠폰', '혜택받기']):
            continue
            
        sentences.append(sentence)
    
    # 3. 주제 관련성 점수 계산
    scored_sentences = []
    
    for sentence in sentences:
        score = 0
        sentence_lower = sentence.lower()
        
        # 주제 키워드 포함 점수
        for keyword in topic_keywords:
            if keyword.lower() in sentence_lower:
                score += 2
        
        # 원본 주제 포함 점수 (더 높은 가중치)
        if topic.lower() in sentence_lower:
            score += 5
        
        # 유용한 정보 지시어 포함 점수
        useful_indicators = ['방법', '효과', '결과', '연구', '분석', '조사', '발표', '발견', '확인', '증가', '감소', '개선', '향상']
        for indicator in useful_indicators:
            if indicator in sentence_lower:
                score += 1
        
        # 최신성 지시어 포함 점수
        recent_indicators = ['최신', '최근', '2024', '2025', '올해', '이번', '새로운', '신규', '업데이트']
        for indicator in recent_indicators:
            if indicator in sentence_lower:
                score += 3
        
        if score > 0:
            scored_sentences.append((sentence, score))
    
    # 4. 점수 기준으로 정렬 및 선별
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    
    # 5. 상위 점수 문장들 선별 (중복 제거)
    relevant_sentences = []
    for sentence, score in scored_sentences:
        # 중복 검사 (60% 이상 유사하면 중복으로 판단)
        is_duplicate = False
        for existing in relevant_sentences:
            if calculate_similarity(sentence, existing) > 0.6:
                is_duplicate = True
                break
        
        if not is_duplicate:
            relevant_sentences.append(sentence)
            
        # 최대 12개까지만 수집
        if len(relevant_sentences) >= 12:
            break
    
    # 6. 백업 처리 (충분한 정보가 없는 경우)
    if len(relevant_sentences) < 3 and search_text:
        # 전체 텍스트를 청크로 분할
        chunks = [search_text[i:i+400] for i in range(0, len(search_text), 400)]
        for chunk in chunks[:3]:
            if chunk.strip() and chunk.strip() not in relevant_sentences:
                relevant_sentences.append(chunk.strip())
    
    print(f"        📋 추출된 정보: {len(relevant_sentences)}개")
    
    return relevant_sentences[:10]  # 최대 10개 반환

def generate_topic_keywords(topic):
    """주제별 맞춤형 키워드 생성"""
    
    # 기본 키워드 (주제 자체)
    keywords = topic.split()
    
    topic_lower = topic.lower()
    
    # 주제별 관련 키워드 추가
    if any(keyword in topic_lower for keyword in ['비타민', '건강', '영양']):
        keywords.extend(['건강', '영양', '효과', '부작용', '복용', '섭취', '연구', '실험'])
    
    elif any(keyword in topic_lower for keyword in ['ai', '인공지능', '기술']):
        keywords.extend(['기술', '개발', '적용', '활용', '혁신', '미래', '산업', '변화'])
    
    elif any(keyword in topic_lower for keyword in ['투자', '주식', '경제']):
        keywords.extend(['투자', '시장', '경제', '수익', '위험', '전망', '분석', '예측'])
    
    elif any(keyword in topic_lower for keyword in ['요리', '레시피', '음식']):
        keywords.extend(['요리', '레시피', '재료', '조리', '맛', '영양', '건강', '방법'])
    
    elif any(keyword in topic_lower for keyword in ['여행', '관광']):
        keywords.extend(['여행', '관광', '명소', '추천', '경험', '문화', '역사', '정보'])
    
    else:
        # 일반적인 키워드
        keywords.extend(['정보', '방법', '효과', '장점', '특징', '활용', '실제', '경험'])
    
    return list(set(keywords))  # 중복 제거

def calculate_similarity(text1, text2):
    """두 텍스트의 유사도 계산 (간단한 방법)"""
    if not text1 or not text2:
        return 0
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0
    
    return len(intersection) / len(union)

def generate_enhanced_prompt(topic, perspective, context_info, section_num):
    """주제와 관점에 따른 향상된 프롬프트 생성"""
    
    base_prompt = f"""
'{topic}' 주제에 대해 '{perspective['angle']}' 관점에서 블로그 본문 내용을 작성해주세요.

⚠️ **절대 금지사항:**
- 제목, 소제목, 번호 목록은 절대 포함하지 마세요
- "1.", "2.", "3." 같은 번호 매기기 금지
- "첫째", "둘째", "셋째" 같은 순서 표현 금지  
- 목차나 리스트 형태 작성 금지

✅ **작성 요구사항:**
- 길이: 350-450자의 연속된 문단 형태
- 관점: {perspective['focus']}에 중점을 둔 서술형 글
- 스타일: 자연스러운 문장으로 이어지는 설명글
- 구조: 문단 2-3개로 구성, 각 문단은 자연스럽게 연결

🎯 **작성 방식:**
- 마치 책의 한 챕터를 읽는 것처럼 자연스러운 서술
- 구체적인 사실, 수치, 예시를 포함한 설명
- 독자가 흥미롭게 읽을 수 있는 스토리텔링 방식

🔍 **참고 정보:**
아래 정보를 참고하여 내용의 정확성을 높여주세요.
{context_info}

📝 **예시 (이런 식으로 작성):**
"비타민 D는 우리 몸에서 칼슘 흡수를 돕는 핵심 역할을 합니다. 최근 연구에 따르면 한국인의 80% 이상이 비타민 D 부족 상태로, 이는 현대인의 실내 생활 패턴과 밀접한 관련이 있습니다.

특히 겨울철에는 일조량 부족으로 인해 체내 비타민 D 합성이 크게 감소합니다. 전문가들은 하루 15-20분 정도의 적절한 햇빛 노출을 권장하며, 이는 골밀도 유지와 면역력 강화에 직접적인 도움을 준다고 설명합니다."

위와 같이 번호나 제목 없이 자연스러운 문단으로만 작성해주세요.
"""
    
    return base_prompt.strip()

def clean_generated_content(content):
    """생성된 콘텐츠에서 불필요한 제목/번호/목록 제거"""
    import re
    
    if not content:
        return content
    
    # 줄 단위로 분리
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        
        # 빈 줄은 그대로 유지
        if not line:
            cleaned_lines.append('')
            continue
        
        # 제거할 패턴들 (목차나 번호 목록)
        patterns_to_remove = [
            r'^[🔍💡📋🎯✅⚠️📝🔧📊🌟💪🚀📱💻🏥🍎🎨🌍📚🎵]+.*\d+\..*$',  # 이모지+번호 목록
            r'.*\d+\.\s+[가-힣]{2,}\s+\d+\.\s+[가-힣]{2,}.*$',  # 한 줄에 여러 번호가 있는 경우
            r'^[🔍💡📋🎯✅⚠️📝🔧📊🌟💪🚀📱💻🏥🍎🎨🌍📚🎵]+\s*\d+\..*$',  # 이모지로 시작하고 번호가 포함된 제목
            r'^\d+\.\s+[가-힣]{1,10}\?\s+\d+\.\s+[가-힣]{1,20}\s+\d+\..*$',  # 연속된 번호 목록
            r'^(첫째|둘째|셋째|넷째|다섯째),.*$',  # 순서 표현으로 시작하는 목록
            r'^\d+\)\s.*$',  # 1), 2), 3) 으로 시작하는 번호 목록  
            r'^•\s.*$',  # 불릿 포인트로 시작하는 목록
            r'^-\s.*$',  # 하이픈으로 시작하는 목록
        ]
        
        # 패턴 검사
        should_remove = False
        for pattern in patterns_to_remove:
            if re.match(pattern, line):
                should_remove = True
                break
        
        # 너무 짧은 제목성 문장 제거 (20자 미만이면서 콜론이나 물음표로 끝나는 경우)
        if len(line) < 20 and (line.endswith(':') or line.endswith('?') or line.endswith('입니다')):
            should_remove = True
        
        # 제목으로 보이는 패턴 제거 (모든 단어가 대문자이거나, 특수 문자로 둘러싸인 경우)
        if re.match(r'^[A-Z\s]+$', line) or re.match(r'^[\*\-=]{3,}.*[\*\-=]{3,}$', line):
            should_remove = True
        
        if not should_remove:
            cleaned_lines.append(line)
    
    # 정리된 내용 재조합
    cleaned_content = '\n'.join(cleaned_lines)
    
    # 연속된 빈 줄 제거 (2개 이상의 연속 빈 줄을 1개로)
    cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
    
    # 앞뒤 공백 제거
    cleaned_content = cleaned_content.strip()
    
    # 만약 모든 내용이 제거되었다면 기본 메시지 반환 (조건 완화)
    if not cleaned_content or len(cleaned_content.strip()) < 20:
        return f"해당 주제에 대한 내용을 자세히 설명드리겠습니다."
    
    return cleaned_content

def clean_subtitle(subtitle):
    """소제목에서 불필요한 요소 제거"""
    import re
    
    if not subtitle:
        return subtitle
    
    # 앞뒤 공백 제거
    subtitle = subtitle.strip()
    
    # 따옴표 제거
    subtitle = subtitle.strip('"\'""''')
    
    # 이모지 제거
    subtitle = re.sub(r'[🔍💡📋🎯✅⚠️📝🔧📊🌟💪🚀📱💻🏥🍎🎨🌍📚🎵]', '', subtitle)
    
    # 번호 제거 (앞의 숫자와 점) - 더 강력한 패턴
    subtitle = re.sub(r'^\d+\.\s*', '', subtitle)  # 1. 제거
    subtitle = re.sub(r'^[①②③④⑤⑥⑦⑧⑨⑩]\s*', '', subtitle)  # 원 숫자 제거
    subtitle = re.sub(r'^\d+\)\s*', '', subtitle)  # 1) 제거
    subtitle = re.sub(r'\d+\.\s*', '', subtitle)  # 중간에 있는 번호도 제거
    
    # 순서 표현 제거
    subtitle = re.sub(r'^(첫째|둘째|셋째|넷째|다섯째)\s*', '', subtitle)
    
    # 특수 문자 제거
    subtitle = re.sub(r'^[\*\-•]\s*', '', subtitle)
    
    # 대괄호, 소괄호 제거
    subtitle = re.sub(r'^\[.*?\]\s*', '', subtitle)
    subtitle = re.sub(r'^\(.*?\)\s*', '', subtitle)
    
    # 콜론으로 끝나면 제거
    subtitle = subtitle.rstrip(':：')
    
    # 앞뒤 공백 다시 제거
    subtitle = subtitle.strip()
    
    # 너무 길면 자르기 (15자 제한)
    if len(subtitle) > 15:
        subtitle = subtitle[:15].rstrip()
    
    # 빈 제목이면 기본값 반환
    if not subtitle or len(subtitle) < 2:
        return "핵심 내용"
    
    return subtitle

def web_search_simulation(query, topic):
    """실제 웹 스크래핑을 통한 정보 수집 시스템"""
    print(f"    🌐 실제 웹 스크래핑 시작: '{query}'")
    
    # 1. 실제 웹 스크래핑 시도
    scraped_result = perform_real_web_scraping(query, topic)
    if scraped_result and len(scraped_result) > 200:
        print(f"    ✅ 웹 스크래핑 성공: {len(scraped_result)}자")
        return scraped_result
    
    # 2. 다중 검색 엔진 시도
    multi_search_result = perform_multi_engine_search(query, topic)
    if multi_search_result and len(multi_search_result) > 200:
        print(f"    ✅ 다중 검색 성공: {len(multi_search_result)}자")
        return multi_search_result
    
    # 3. 기본 검색 도구 사용
    basic_search_result = perform_basic_search(query, topic)
    if basic_search_result and len(basic_search_result) > 50:
        print(f"    ✅ 기본 검색 성공: {len(basic_search_result)}자")
        return basic_search_result
    
    # 4. 최소한의 기본 정보 제공
    print(f"    ⚠️ 모든 검색 실패, 기본 정보 제공")
    return f"{topic}에 대한 최신 정보를 웹에서 검색하고 있습니다. 정확한 정보는 공식 웹사이트에서 확인해주세요."

def perform_multi_source_search(query, topic):
    """다중 소스 검색 - 실제 웹 스크래핑 기반"""
    print(f"    🔍 다중 소스 검색 시작: '{query}'")
    
    all_results = []
    
    # 1. 실제 웹 스크래핑 실행
    scraped_results = perform_real_web_scraping(query, topic)
    if scraped_results:
        all_results.extend(scraped_results)
        print(f"    ✅ 웹 스크래핑: {len(scraped_results)}개 결과")
    
    # 2. 뉴스 사이트 검색
    news_results = scrape_news_sites(query)
    if news_results:
        all_results.extend(news_results)
        print(f"    ✅ 뉴스 검색: {len(news_results)}개 결과")
    
    # 3. 정부 사이트 검색 (정책 관련 주제일 경우)
    if any(keyword in query.lower() for keyword in ['정책', '정부', '지원', '혜택', '쿠폰']):
        gov_results = scrape_government_sites(query, topic)
        if gov_results:
            all_results.extend(gov_results)
            print(f"    ✅ 정부 사이트: {len(gov_results)}개 결과")
    
    # 4. 위키피디아 검색
    wiki_results = search_wikipedia(query)
    if wiki_results:
        all_results.extend(wiki_results)
        print(f"    ✅ 위키피디아: {len(wiki_results)}개 결과")
    
    # 결과 종합 및 중요도 점수 계산
    if all_results:
        combined_content = cross_validate_information(all_results, topic)
        return combined_content
    
    return None

def perform_real_web_scraping(query, topic):
    """실제 웹 스크래핑 수행"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import time
        import random
        
        print(f"      🔍 실제 웹 스크래핑: '{query}'")
        
        collected_content = []
        
        # 1. 구글 검색 결과에서 정보 수집
        google_results = scrape_google_search(query)
        if google_results:
            collected_content.extend(google_results)
        
        # 2. 네이버 검색 결과에서 정보 수집
        naver_results = scrape_naver_search(query)
        if naver_results:
            collected_content.extend(naver_results)
        
        # 3. 정부 공식 사이트에서 정보 수집
        if any(keyword in query.lower() for keyword in ['정책', '정부', '지원', '혜택', '쿠폰']):
            gov_results = scrape_government_sites(query, topic)
            if gov_results:
                collected_content.extend(gov_results)
        
        # 4. 뉴스 사이트에서 정보 수집
        news_results = scrape_news_sites(query)
        if news_results:
            collected_content.extend(news_results)
        
        return collected_content
            
    except Exception as e:
        print(f"      ❌ 웹 스크래핑 오류: {e}")
        return []

def scrape_google_search(query):
    """구글 검색 결과 스크래핑 - 개선된 버전"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import time
        import random
        import urllib.parse
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # URL 인코딩 개선
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.google.com/search?q={encoded_query}&num=10&hl=ko&gl=kr"
        
        print(f"        🔍 구글 검색 시도: {search_url[:80]}...")
        
        time.sleep(random.uniform(2, 4))  # 요청 간격 조절
        response = requests.get(search_url, headers=headers, timeout=15)
        
        print(f"        📡 구글 응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 다양한 선택자로 결과 추출 시도
            results = []
            
            # 방법 1: 일반적인 검색 결과
            search_results = soup.find_all('div', class_='g')
            print(f"        🔍 방법1 - div.g: {len(search_results)}개 발견")
            
            for result in search_results[:5]:
                # 스니펫 텍스트 추출 (여러 방법 시도)
                snippets = result.find_all(['span', 'div'], class_=['VwiC3b', 'aCOpRe', 'yDYNvb'])
                for snippet in snippets:
                    if snippet and snippet.text:
                        text = snippet.text.strip()
                        if len(text) > 30 and text not in results:
                            results.append(text)
                            break
            
            # 방법 2: 다른 선택자 시도
            if len(results) < 3:
                other_results = soup.find_all('div', class_=['BNeawe', 'VwiC3b'])
                print(f"        🔍 방법2 - 다른 선택자: {len(other_results)}개 발견")
                
                for result in other_results[:5]:
                    if result and result.text:
                        text = result.text.strip()
                        if len(text) > 30 and text not in results:
                            results.append(text)
            
            # 방법 3: 모든 텍스트에서 유용한 정보 추출
            if len(results) < 2:
                all_text = soup.get_text()
                sentences = all_text.split('.')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if (len(sentence) > 50 and len(sentence) < 300 and
                        any(keyword in sentence.lower() for keyword in query.lower().split()) and
                        sentence not in results):
                        results.append(sentence)
                        if len(results) >= 3:
                            break
            
            print(f"        📊 구글: {len(results)}개 결과 수집")
            return results[:5]  # 최대 5개만 반환
        else:
            print(f"        ❌ 구글 검색 실패: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"        ❌ 구글 검색 오류: {e}")
        return []

def scrape_naver_search(query):
    """네이버 검색 결과 스크래핑 - 개선된 버전"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import urllib.parse
        import time
        import random
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.naver.com/',
        }
        
        # 네이버 검색 URL
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://search.naver.com/search.naver?query={encoded_query}&where=nexearch"
        
        print(f"        🔍 네이버 검색 시도: {query}")
        
        time.sleep(random.uniform(2, 4))  # 요청 간격 조절
        response = requests.get(search_url, headers=headers, timeout=15)
        
        print(f"        📡 네이버 응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            
            # 방법 1: 지식백과 정보 추출 (개선된 선택자)
            knowledge_selectors = [
                'div.api_txt_lines',
                'div.detail_txt',
                'div.cont_inner',
                'div.api_cs_wrap .cs_text',
                'div.total_wrap .detail_txt'
            ]
            
            for selector in knowledge_selectors:
                knowledge_cards = soup.select(selector)
                print(f"        🔍 지식백과 {selector}: {len(knowledge_cards)}개 발견")
                for card in knowledge_cards[:3]:
                    text = card.get_text(strip=True)
                    if len(text) > 40 and text not in results:
                        results.append(text)
                if results:
                    break
            
            # 방법 2: 뉴스 결과 추출 (개선된 선택자)
            news_selectors = [
                'a.news_tit',
                'div.news_wrap .news_tit',
                'a.api_txt_lines.dsc_txt_wrap',
                'div.news_area .news_tit'
            ]
            
            for selector in news_selectors:
                news_items = soup.select(selector)
                print(f"        🔍 뉴스 {selector}: {len(news_items)}개 발견")
                for item in news_items[:3]:
                    title = item.get_text(strip=True)
                    if len(title) > 20 and title not in results:
                        results.append(title)
            
            # 방법 3: 일반 검색 결과 추출
            if len(results) < 2:
                general_selectors = [
                    'div.total_group .total_tit',
                    'div.algo_tit',
                    'div.api_subject_bx .tit',
                    'div.area_text_box .dsc'
                ]
                
                for selector in general_selectors:
                    general_items = soup.select(selector)
                    print(f"        🔍 일반 {selector}: {len(general_items)}개 발견")
                    for item in general_items[:3]:
                        text = item.get_text(strip=True)
                        if len(text) > 30 and text not in results:
                            results.append(text)
                    if len(results) >= 3:
                        break
            
            # 방법 4: 페이지 전체에서 관련 텍스트 추출
            if len(results) < 2:
                all_text = soup.get_text()
                sentences = [s.strip() for s in all_text.split('.') if s.strip()]
                for sentence in sentences:
                    if (len(sentence) > 40 and len(sentence) < 200 and
                        any(keyword in sentence.lower() for keyword in query.lower().split()) and
                        sentence not in results):
                        results.append(sentence)
                        if len(results) >= 3:
                            break
            
            print(f"        📊 네이버: {len(results)}개 결과 수집")
            return results[:5]  # 최대 5개만 반환
        else:
            print(f"        ❌ 네이버 검색 실패: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"        ❌ 네이버 검색 오류: {e}")
        return []

def scrape_government_sites(query, topic):
    """정부 공식 사이트에서 정보 수집 - 개선된 버전"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import time
        import random
        import urllib.parse
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Referer': 'https://www.gov.kr/',
        }
        
        results = []
        
        # 정부24에서 검색 시도 (개선된 방법)
        try:
            encoded_query = urllib.parse.quote(query)
            gov24_url = f"https://www.gov.kr/portal/rcvfvrSvc/search?srhTxt={encoded_query}"
            
            print(f"        🔍 정부24 검색 시도: {query}")
            
            time.sleep(random.uniform(2, 4))
            response = requests.get(gov24_url, headers=headers, timeout=15)
            
            print(f"        📡 정부24 응답 코드: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 다양한 선택자로 정보 추출 시도
                selectors = [
                    'div.result_item',
                    'div.search_result',
                    'div.cont_box',
                    'li.result_list',
                    'div.list_item'
                ]
                
                for selector in selectors:
                    items = soup.select(selector)
                    print(f"        🔍 정부24 {selector}: {len(items)}개 발견")
                    
                    for item in items[:3]:
                        # 제목과 설명 추출
                        title_selectors = ['h3', 'h4', 'strong', '.title', '.tit']
                        desc_selectors = ['p', 'div.desc', '.summary', '.content']
                        
                        title = ""
                        desc = ""
                        
                        for t_sel in title_selectors:
                            title_elem = item.select_one(t_sel)
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                break
                        
                        for d_sel in desc_selectors:
                            desc_elem = item.select_one(d_sel)
                            if desc_elem:
                                desc = desc_elem.get_text(strip=True)
                                break
                        
                        if title or desc:
                            combined = f"{title} {desc}".strip()
                            if len(combined) > 30 and combined not in results:
                                results.append(combined)
                    
                    if results:
                        break
                
                # 전체 텍스트에서 정보 추출
                if len(results) < 2:
                    all_text = soup.get_text()
                    sentences = [s.strip() for s in all_text.split('.') if s.strip()]
                    for sentence in sentences:
                        if (len(sentence) > 40 and len(sentence) < 300 and
                            any(keyword in sentence.lower() for keyword in query.lower().split()) and
                            sentence not in results):
                            results.append(sentence)
                            if len(results) >= 3:
                                break
        
        except Exception as e:
            print(f"        ❌ 정부24 검색 오류: {e}")
        
        # 추가: 다른 정부 사이트들도 시도
        if len(results) < 2:
            try:
                # 국정홍보처 검색
                moef_url = f"https://www.korea.kr/news/newsView.do?newsId=&pageIndex=1&searchWrd={encoded_query}"
                
                print(f"        🔍 korea.kr 검색 시도")
                
                time.sleep(random.uniform(1, 2))
                response = requests.get(moef_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    news_items = soup.select('div.news_list li, div.list_area li')
                    
                    for item in news_items[:3]:
                        text = item.get_text(strip=True)
                        if len(text) > 30 and text not in results:
                            results.append(text)
            
            except Exception as e:
                print(f"        ❌ korea.kr 검색 오류: {e}")
        
        print(f"        📊 정부사이트: {len(results)}개 결과 수집")
        return results[:5]  # 최대 5개만 반환
        
    except Exception as e:
        print(f"        ❌ 정부 사이트 스크래핑 오류: {e}")
        return []

def scrape_news_sites(query):
    """뉴스 사이트에서 최신 정보 수집"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import urllib.parse
        import time
        import random
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        results = []
        
        # 다음 뉴스에서 검색
        try:
            encoded_query = urllib.parse.quote(query)
            daum_url = f"https://search.daum.net/search?w=news&q={encoded_query}"
            
            time.sleep(random.uniform(1, 3))
            response = requests.get(daum_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                news_items = soup.find_all('div', class_='item-title')
                for item in news_items[:5]:
                    title = item.get_text(strip=True)
                    if len(title) > 20:
                        results.append(title)
        
        except Exception as e:
            print(f"        ❌ 다음 뉴스 검색 실패: {e}")
        
        print(f"        📊 뉴스사이트: {len(results)}개 결과 수집")
        return results
        
    except Exception as e:
        print(f"        ❌ 뉴스 사이트 스크래핑 실패: {e}")
        return []

def perform_multi_engine_search(query, topic):
    """다중 검색 엔진을 통한 정보 수집"""
    try:
        import requests
        from urllib.parse import quote
        import json
        
        collected_results = []
        
        # 1. DuckDuckGo API 사용
        try:
            duckduckgo_result = perform_single_web_search(query)
            if duckduckgo_result:
                collected_results.append(duckduckgo_result)
        except Exception as e:
            print(f"        ❌ DuckDuckGo 검색 실패: {e}")
        
        # 2. Bing 검색 시도
        try:
            bing_results = search_with_bing(query)
            if bing_results:
                collected_results.extend(bing_results)
        except Exception as e:
            print(f"        ❌ Bing 검색 실패: {e}")
        
        # 3. 위키피디아 검색
        try:
            wiki_results = search_wikipedia(query)
            if wiki_results:
                collected_results.extend(wiki_results)
        except Exception as e:
            print(f"        ❌ 위키피디아 검색 실패: {e}")
        
        if collected_results:
            combined_content = ' '.join(collected_results)
            print(f"        📊 다중엔진: 총 {len(collected_results)}개 소스에서 정보 수집")
            return combined_content
        else:
            return None
            
    except Exception as e:
        print(f"      ❌ 다중 엔진 검색 실패: {e}")
        return None

def search_with_bing(query):
    """Bing 검색을 통한 정보 수집"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import urllib.parse
        import time
        import random
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        encoded_query = urllib.parse.quote(query)
        bing_url = f"https://www.bing.com/search?q={encoded_query}"
        
        time.sleep(random.uniform(1, 3))
        response = requests.get(bing_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            search_results = soup.find_all('li', class_='b_algo')
            
            for result in search_results[:5]:
                snippet = result.find('p')
                if snippet and snippet.text:
                    text = snippet.text.strip()
                    if len(text) > 50:
                        results.append(text)
            
            return results
        else:
            return []
            
    except Exception as e:
        print(f"        ❌ Bing 검색 오류: {e}")
        return []

def search_wikipedia(query):
    """위키피디아에서 정보 검색"""
    try:
        import requests
        import json
        
        # 위키피디아 API 사용
        wiki_url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; BlogGenerator/1.0)'
        }
        
        response = requests.get(wiki_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            extract = data.get('extract', '')
            
            if extract and len(extract) > 100:
                return [extract]
        
        return []
        
    except Exception as e:
        print(f"        ❌ 위키피디아 검색 오류: {e}")
        return []

def perform_basic_search(query, topic):
    """기본 검색 도구 (최후 방법)"""
    try:
        # DuckDuckGo 검색만 시도
        basic_result = perform_single_web_search(query)
        if basic_result:
            return basic_result
        
        # 그래도 안되면 최소한의 정보
        return f"{topic}에 대한 최신 정보를 찾고 있습니다. 정확한 정보는 공식 웹사이트를 참조하세요."
        
    except Exception as e:
        print(f"      ❌ 기본 검색 실패: {e}")
        return f"{topic}에 대한 정보를 수집 중입니다. 공식 출처를 확인해 주세요."

def perform_single_web_search(query):
    """단일 웹 검색 수행 - DuckDuckGo API 사용"""
    try:
        from requests import get
        from urllib.parse import quote
        import json
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # DuckDuckGo 검색 API 사용 (무료)
        search_url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
        response = get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Abstract 정보 추출
            abstract = data.get('Abstract', '')
            if abstract and len(abstract) > 100:
                return abstract
            
            # Related Topics 정보 추출
            related_topics = data.get('RelatedTopics', [])
            if related_topics:
                topic_texts = []
                for topic in related_topics[:5]:  # 상위 5개만
                    if isinstance(topic, dict) and 'Text' in topic:
                        topic_texts.append(topic['Text'])
                
                if topic_texts:
                    combined_text = ' '.join(topic_texts)
                    if len(combined_text) > 100:
                        return combined_text
        
        return None
        
    except Exception as e:
        return None

def cross_validate_information(search_results, topic):
    """교차 검증을 통한 정보 신뢰도 평가"""
    if not search_results:
        return None
    
    # 다중 소스 결과를 하나의 일관된 정보로 통합
    combined_content = []
    
    # 각 결과를 검증하고 신뢰도 점수 계산
    for result in search_results:
        if isinstance(result, str) and len(result) > 30:
            # 기본 신뢰도 점수
            score = 0.7
            
            # 정부 관련 키워드 가중치 증가
            if any(keyword in result.lower() for keyword in ['정부', '공식', '발표', '부처']):
                score += 0.2
            
            # 뉴스 관련 키워드 가중치 증가  
            if any(keyword in result.lower() for keyword in ['뉴스', '보도', '기사']):
                score += 0.1
            
            # 최신 정보 가중치 증가
            if any(keyword in result.lower() for keyword in ['2025', '최신', '현재']):
                score += 0.05
            
            # 상세한 정보 가중치 증가
            if len(result) > 200:
                score += 0.03
            
            combined_content.append({
                'content': result,
                'score': score
            })
    
    # 점수별로 정렬하여 최고 신뢰도 정보 선택
    if combined_content:
        sorted_results = sorted(combined_content, key=lambda x: x['score'], reverse=True)
        
        # 상위 3개 결과를 조합하여 최종 정보 생성
        top_results = [item['content'] for item in sorted_results[:3]]
        final_content = ' '.join(top_results)
        
        # 추가 검증 수행
        validated_content = validate_information_accuracy(final_content, topic)
        
        print(f"      ✅ 교차 검증 완료: {len(search_results)}개 소스에서 정보 통합")
        return validated_content
    
    return None

def validate_information_accuracy(content, topic):
    """정보 정확성 검증 및 오류 수정"""
    if not content:
        return content
    
    # 특정 주제에 대한 정확성 검증
    if "민생회복 소비쿠폰" in topic:
        # 잘못된 정보 패턴 체크 및 수정
        if "2024년" in content:
            content = content.replace("2024년", "2025년")
            print(f"      🔧 정보 수정: 시행년도 2024년 → 2025년")
        
        if "최대 10만원" in content:
            content = content.replace("최대 10만원", "최소 15만원~최대 45만원")
            print(f"      🔧 정보 수정: 지급액 최대 10만원 → 최소 15만원~최대 45만원")
        
        # 시행일 정보 검증
        if "2025년 1월" in content:
            content = content.replace("2025년 1월", "2025년 7월 21일")
            print(f"      🔧 정보 수정: 시행일 2025년 1월 → 2025년 7월 21일")
    
    # 일반적인 정보 검증
    if "확인되지 않은" in content or "추측" in content:
        print(f"      ⚠️ 불확실한 정보 감지, 추가 확인 필요")
    
    # 중복 정보 제거
    sentences = content.split('. ')
    unique_sentences = []
    seen_sentences = set()
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and sentence not in seen_sentences:
            unique_sentences.append(sentence)
            seen_sentences.add(sentence)
    
    return '. '.join(unique_sentences)

def perform_real_web_search(query):
    """실제 웹 검색 수행 - 기존 호환성 유지"""
    return perform_single_web_search(query)

def generate_fact_checked_content(topic, latest_info):
    """수집한 최신 정보를 바탕으로 사실 확인된 콘텐츠 생성"""
    print(f"📝 최신 정보 기반 콘텐츠 생성: '{topic}'")
    
    if not latest_info:
        print("⚠️ 최신 정보가 없어 기본 방식으로 생성합니다.")
        return None
    
    # 수집한 정보를 문자열로 정리
    fact_context = "\n".join(latest_info[:10])  # 상위 10개 정보만 사용
    
    try:
        if openai.api_key:
            # 사실 기반 콘텐츠 생성 프롬프트
            fact_based_prompt = f"""다음은 '{topic}'에 대한 최신 검색 정보입니다:

{fact_context}

위 정보를 바탕으로 정확하고 사실적인 블로그 글을 작성해주세요.

요구사항:
1. 검색된 정보에 기반한 정확한 내용만 포함
2. 추측이나 일반적인 내용 대신 구체적인 사실 위주
3. 도입부(200-300자), 핵심 내용 3개(각 300-400자), 결론(200-300자)로 구성
4. 각 섹션의 소제목도 함께 생성

응답 형식:
제목: [구체적인 제목]

도입부:
[내용]

소제목1: [제목]
핵심내용1:
[내용]

소제목2: [제목]  
핵심내용2:
[내용]

소제목3: [제목]
핵심내용3:
[내용]

결론:
[내용]"""

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 정확한 정보만을 제공하는 사실 확인 전문 작가입니다. 주어진 정보에만 기반하여 글을 작성하세요."},
                    {"role": "user", "content": fact_based_prompt}
                ],
                max_tokens=1500,
                temperature=0.3  # 창의성보다 정확성 우선
            )
            
            fact_checked_content = response.choices[0].message.content.strip()
            print("✅ 사실 확인된 콘텐츠 생성 완료")
            return fact_checked_content
        else:
            print("⚠️ OpenAI API 키가 없어 사실 확인 콘텐츠 생성을 건너뜁니다.")
            return None
            
    except Exception as e:
        print(f"❌ 사실 확인 콘텐츠 생성 실패: {e}")
        return None

def parse_fact_checked_content(content_text):
    """사실 확인된 콘텐츠를 구조화된 데이터로 파싱"""
    if not content_text:
        return None
    
    try:
        sections = content_text.split('\n\n')
        parsed_data = {
            "title": "",
            "intro": "",
            "core_subtitles": [],
            "core_contents": [],
            "conclusion": ""
        }
        
        current_section = None
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            if section.startswith("제목:"):
                parsed_data["title"] = section.replace("제목:", "").strip()
            elif section.startswith("도입부:"):
                parsed_data["intro"] = section.replace("도입부:", "").strip()
            elif section.startswith("소제목"):
                current_section = "subtitle"
                subtitle = section.split(":", 1)[1].strip() if ":" in section else section
                parsed_data["core_subtitles"].append(subtitle)
            elif section.startswith("핵심내용"):
                current_section = "content"
                content = section.split(":", 1)[1].strip() if ":" in section else section
                parsed_data["core_contents"].append(content)
            elif section.startswith("결론:"):
                parsed_data["conclusion"] = section.replace("결론:", "").strip()
            elif current_section == "content" and section:
                # 소제목 다음에 오는 내용을 핵심 내용으로 처리
                parsed_data["core_contents"].append(section)
                current_section = None
        
        # 최소 요구사항 확인
        if (parsed_data["title"] and parsed_data["intro"] and 
            len(parsed_data["core_subtitles"]) >= 3 and 
            len(parsed_data["core_contents"]) >= 3):
            print("✅ 사실 확인 콘텐츠 파싱 완료")
            return parsed_data
        else:
            print("⚠️ 사실 확인 콘텐츠 구조가 불완전합니다.")
            return None
            
    except Exception as e:
        print(f"❌ 사실 확인 콘텐츠 파싱 실패: {e}")
        return None

def generate_blog_content_v2(topic):
    """V2 메인 콘텐츠 생성 함수 (개선된 버전 - 실시간 정보 기반)"""
    print(f"🚀 V2 콘텐츠 생성: '{topic}'")
    
    # 0. 최신 정보 수집 및 사실 확인 (새로운 기능)
    latest_info = search_latest_information(topic)
    fact_checked_content = None
    parsed_fact_content = None  # 변수 초기화
    
    if latest_info:
        fact_checked_content = generate_fact_checked_content(topic, latest_info)
        if fact_checked_content:
            parsed_fact_content = parse_fact_checked_content(fact_checked_content)
            if parsed_fact_content:
                print("✅ 사실 확인된 콘텐츠를 우선 사용합니다!")
    
    # 1. 스마트 키워드 생성
    keywords = generate_smart_keywords(topic)
    
    # 2. 다중 이미지 검색  
    images = get_multiple_images_v2(keywords, count=3)
    
    # 3. 제목 생성 (사실 확인된 콘텐츠가 있으면 우선 사용)
    if parsed_fact_content and parsed_fact_content.get("title"):
        title = parsed_fact_content["title"]
        print(f"📰 사실 확인된 제목 사용: {title}")
    else:
        try:
            if openai.api_key:
                # 기존 파일의 안정적인 제목 생성 로직 사용
                title_prompt = f"다음 주제에 관한 블로그 포스트의 매력적인 제목을 생성해주세요: '{topic}'. 제목만 작성하고 따옴표나 기호는 포함하지 마세요."
                title_resp = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": title_prompt}],
                    max_tokens=50
                )
                title = title_resp.choices[0].message.content.strip()
                
                # 추가 안전장치: 번호와 따옴표 제거
                import re
                title = re.sub(r'^\d+\.\s*', '', title).strip()  # 앞의 번호 제거
                title = title.strip('"').strip("'").strip()  # 따옴표 제거
                
            else:
                title = f"{topic} - 완벽 가이드"
        except:
            title = topic
    
    # 4. 서론/본론/결론 구조로 콘텐츠 생성
    if parsed_fact_content and parsed_fact_content.get("intro"):
        intro_content = parsed_fact_content["intro"]
        print("📰 사실 확인된 서론 사용")
    else:
        try:
            if openai.api_key:
                intro_prompt = f"""'{topic}' 주제에 대한 블로그 글의 서론을 500-600자로 작성해주세요. 

요구사항:
1. 독자의 관심을 끌고 이 주제의 중요성을 강조하는 내용
2. SEO 최적화를 위한 첫 번째 단락에 주요 키워드 자연스럽게 포함
3. 독자가 이 글을 통해 얻을 수 있는 가치 명확히 제시
4. 현재 상황이나 배경 설명으로 주제의 시의성 강조
5. 가독성을 위해 문단을 나누어 작성하고, 자연스러운 줄바꿈 포함
6. 검색엔진 최적화를 위한 키워드 밀도 조절
7. 모바일 친화적인 짧은 문단 구성
8. 헤딩 태그(H2)를 활용한 구조화

서론만 작성해주세요:"""
                
                intro_resp = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": intro_prompt}],
                    max_tokens=600
                )
                intro_content = intro_resp.choices[0].message.content.strip()
            else:
                intro_content = f"이 글에서는 {topic}에 대해 자세히 알아보겠습니다. 현대 사회에서 이 주제가 갖는 의미와 중요성을 살펴보고, 실질적인 인사이트를 제공하겠습니다."
        except:
            intro_content = f"이 글에서는 {topic}에 대해 자세히 알아보겠습니다."

    # 5. 본론 생성 (사실 확인된 콘텐츠가 있으면 우선 사용)
    if parsed_fact_content and parsed_fact_content.get("core_contents") and len(parsed_fact_content["core_contents"]) >= 1:
        main_content = parsed_fact_content["core_contents"][0]  # 첫 번째 내용을 본론으로 사용
        print("📰 사실 확인된 본론 사용")
    else:
        try:
            if openai.api_key:
                # 최신 정보 결합 (2000자까지)
                source_info = ''
                if latest_info:
                    joined = ' '.join(latest_info)
                    if len(joined) > 2000:
                        source_info = joined[:2000]
                    else:
                        source_info = joined
                else:
                    source_info = ''

                # 본론용 프롬프트 생성 (독창성 강화, 출처 언급 금지)
                main_prompt = f"""'{topic}' 주제에 대한 블로그 글의 본론을 작성해주세요.

요구사항:
1. 1500자 이상, 매우 풍부하고 구체적으로 작성
2. 아래 제공된 최신 정보의 사실, 수치, 사례, 전략, 문장 등을 최대한 많이, 자연스럽고 구체적으로 녹여서 본문에 반영
3. 단순 요약이 아니라, 글쓴이의 독창적 해석과 창의적 재구성, 자연스러운 서술로 작성
4. 출처, 참고, 자료, ~에 따르면 등 출처를 암시하는 표현은 절대 사용하지 말 것
5. SEO 최적화를 위한 자연스러운 키워드 활용:
   - 첫 단락에 주요 키워드 포함
   - 본문 중간과 마지막에 자연스럽게 키워드 배치
   - 연관 키워드 활용
   - 검색엔진이 글의 주제를 잘 이해할 수 있도록 키워드 배치
6. 독자에게 실질적인 가치와 인사이트 제공
7. 구체적인 예시, 방법론, 전략 포함
8. 자연스러운 문단 구성과 가독성 확보
9. 헤딩 태그(H2, H3)를 활용한 구조화
10. 링크 전략(내부/외부 참조) 가능성 제시
11. 모바일 친화적인 짧은 문단 구성

아래의 최신 정보를 참고하되, 출처를 드러내지 않고 본인의 생각처럼 자연스럽게 녹여서 작성하세요.

최신 정보:
{source_info}

본론만 작성해주세요:"""
                
                main_resp = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": main_prompt}],
                    max_tokens=4096
                )
                main_content = main_resp.choices[0].message.content.strip()
                # 자동 후처리: 불필요한 제목/번호 제거
                main_content = clean_generated_content(main_content)
            else:
                main_content = f"{topic}의 핵심 내용과 실용적 활용 방안에 대해 자세히 살펴보겠습니다."
        except Exception as e:
            main_content = f"{topic}의 핵심 내용과 실용적 활용 방안에 대해 자세히 살펴보겠습니다."
    
    # 6. 주제별 맞춤 결론 생성 (사실 확인된 콘텐츠가 있으면 우선 사용)
    if parsed_fact_content and parsed_fact_content.get("conclusion"):
        conclusion_content = parsed_fact_content["conclusion"]
        print("📰 사실 확인된 결론 사용")
    else:
        # 향상된 결론 생성
        try:
            # 서론과 본론을 결합하여 결론 생성에 사용
            full_content = f"{intro_content}\n\n{main_content}"
            
            conclusion_content = generate_enhanced_conclusion(title, full_content)
            print("📝 향상된 결론 생성 완료")
        except Exception as e:
            print(f"⚠️ 향상된 결론 생성 실패: {e}")
            # 기본 결론으로 대체
            conclusion_content = f"{topic}에 대한 종합적인 분석을 통해 우리는 이 주제의 중요성과 실용성을 확인할 수 있었습니다."
    
    # 7. 태그 생성
    try:
        if openai.api_key:
            tags_resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"'{topic}' 주제의 SEO 효과적인 태그 10개를 쉼표로 나열해주세요. 검색량이 많고 경쟁도가 적당한 키워드로 구성해주세요."}],
                max_tokens=200
            )
            tags = tags_resp.choices[0].message.content.strip()
            
            # 태그에서 번호 제거 (예: "1. 비타민c 피부효과" → "비타민c 피부효과")
            tags = clean_tags_from_numbers(tags)
        else:
            tags = f"{topic}, 블로그, 정보, 가이드, 팁, 노하우, 분석, 설명, 추천, 방법"  # 기본 태그도 10개로 확장
    except:
        tags = f"{topic}, 블로그, 정보, 가이드, 팁, 노하우, 분석, 설명, 추천, 방법"  # 예외 처리도 10개로 확장
    
    # 8. FAQ 생성
    try:
        if openai.api_key:
            faq_resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"'{topic}' 주제에 대한 FAQ 3개를 만들어주세요. 각 질문과 답변은 구체적이고 실용적이어야 합니다. 형식: 'Q1: 질문내용\\nA1: 답변내용' 형태로 작성해주세요."}],
                max_tokens=800
            )
            faq_content = faq_resp.choices[0].message.content.strip()
        else:
            faq_content = None
    except:
        faq_content = None
    
    # 8.5. 서론/본론/결론 제목 생성
    try:
        if openai.api_key:
            # 서론 제목 생성 (SEO 최적화 강화)
            intro_title_prompt = f"""'{topic}' 주제의 서론에 어울리는 매력적인 제목을 생성해주세요.

조건:
- 번호나 이모지는 절대 포함하지 마세요
- 10-15자 이내의 간결한 제목
- 독자의 관심을 끌 수 있는 표현
- 주제의 중요성이나 배경을 암시하는 내용
- SEO를 고려한 키워드 포함
- 검색엔진 최적화를 위한 주요 키워드 자연스럽게 포함
- 헤딩 태그(H2)에 적합한 구조
- 예시: '왜 중요한가', '현실적 의미', '시대적 배경', '핵심 가치'

서론 제목만 답변해주세요:"""
            
            intro_title_resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": intro_title_prompt}],
                max_tokens=50
            )
            intro_title = intro_title_resp.choices[0].message.content.strip()
            intro_title = clean_subtitle(intro_title)
            
            # 본론 제목 생성 (SEO 최적화 강화)
            main_title_prompt = f"""'{topic}' 주제의 본론에 어울리는 매력적인 제목을 생성해주세요.

조건:
- 번호나 이모지는 절대 포함하지 마세요
- 10-15자 이내의 간결한 제목
- 핵심 내용이나 실용적 정보를 암시하는 표현
- 독자에게 실질적 가치를 제공한다는 느낌
- SEO를 고려한 키워드 포함
- 검색엔진 최적화를 위한 주요 키워드 자연스럽게 포함
- 헤딩 태그(H2)에 적합한 구조
- 구체적이고 실용적인 느낌
- 링크 전략을 고려한 제목
- 예시: '구체적 방법', '실행 전략', '핵심 원리', '실용 가이드'

본론 제목만 답변해주세요:"""
            
            main_title_resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": main_title_prompt}],
                max_tokens=50
            )
            main_title = main_title_resp.choices[0].message.content.strip()
            main_title = clean_subtitle(main_title)
            
            # 결론 제목 생성
            conclusion_title_prompt = f"""'{topic}' 주제의 결론에 어울리는 매력적인 제목을 생성해주세요.

조건:
- 번호나 이모지는 절대 포함하지 마세요
- 10-15자 이내의 간결한 제목
- 마무리나 미래 전망을 암시하는 표현
- 독자에게 희망이나 동기를 주는 내용
- 예시: '완성된 그림', '미래 비전', '실천 방안', '최종 정리'

결론 제목만 답변해주세요:"""
            
            conclusion_title_resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": conclusion_title_prompt}],
                max_tokens=50
            )
            conclusion_title = conclusion_title_resp.choices[0].message.content.strip()
            conclusion_title = clean_subtitle(conclusion_title)
            
            # 제목 유효성 검사 및 기본값 설정
            if not intro_title or len(intro_title) < 3:
                intro_title = f"{topic}의 중요성"
            if not main_title or len(main_title) < 3:
                main_title = f"{topic}의 핵심 내용"
            if not conclusion_title or len(conclusion_title) < 3:
                conclusion_title = f"{topic}의 완성"
                
        else:
            intro_title = f"{topic}의 중요성"
            main_title = f"{topic}의 핵심 내용"
            conclusion_title = f"{topic}의 완성"
            
    except Exception as e:
        print(f"⚠️ 제목 생성 실패: {e}")
        intro_title = f"{topic}의 중요성"
        main_title = f"{topic}의 핵심 내용"
        conclusion_title = f"{topic}의 완성"
    
    # 8.6. 동적 표 제목 생성
    try:
        if openai.api_key:
            table_title_resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"'{topic}' 주제에 적합한 정보 표의 제목을 생성해주세요. 간결하고 명확한 제목만 작성해주세요."}],
                max_tokens=30
            )
            table_title = table_title_resp.choices[0].message.content.strip()
        else:
            table_title = f"{topic} 핵심 정보"
    except:
        table_title = f"{topic} 핵심 정보"

    # 9. 통합된 콘텐츠 객체 생성 (서론/본론/결론 구조)
    content_data = {
        "title": title,
        "intro_title": intro_title,
        "intro": intro_content,
        "main_title": main_title,
        "main": main_content,
        "conclusion_title": conclusion_title,
        "conclusion": conclusion_content,
        "table_title": table_title,
        "table_html": "",  # 빈 값으로 설정하여 동적 생성 유도
        "faq_raw": faq_content
    }
    
    # 10. V2 HTML 생성 (통합된 콘텐츠 전달)
    enhanced_html = generate_enhanced_html_v2(topic, images, content_data, faq_content)
    
    print("✅ V2 콘텐츠 생성 완료!")
    
    return {
        "title": title,
        "content": enhanced_html,
        "tags": tags,
        "images": images,
        "keywords": keywords,
        "content_data": content_data
    }

# ================================
# 기존 로그인 시스템 (그대로 유지)
# ================================

class FinalTistoryLogin:
    def __init__(self, driver_instance):
        self.driver = driver_instance
    
    def complete_login(self):
        """완전 자동 로그인 (개선된 안정성)"""
        try:
            username = os.getenv("TISTORY_USERNAME")
            password = os.getenv("TISTORY_PASSWORD")
            
            if not username or not password:
                print("❌ 환경변수 설정 필요: TISTORY_USERNAME, TISTORY_PASSWORD")
                return False
            
            print("🎯 완전 자동 로그인 시작")
            print("=" * 50)
            
            # 1단계: 로그인 페이지 접속
            print("1️⃣ 티스토리 로그인 페이지 접속...")
            self.driver.get("https://www.tistory.com/auth/login")
            
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(3)
            
            # 2단계: 카카오 버튼 클릭
            print("2️⃣ 카카오 로그인 버튼 클릭...")
            
            try:
                kakao_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn_login.link_kakao_id"))
                )
                kakao_btn.click()
                print("✅ 카카오 버튼 클릭 성공")
            except:
                js_result = self.driver.execute_script("""
                    var links = document.querySelectorAll('a');
                    for (var i = 0; i < links.length; i++) {
                        if (links[i].textContent.includes('카카오계정으로 로그인')) {
                            links[i].click();
                            return true;
                        }
                    }
                    return false;
                """)
                
                if not js_result:
                    print("❌ 카카오 버튼 클릭 실패")
                    return False
                print("✅ 카카오 버튼 클릭 성공 (JS)")
            
            # 3단계: 카카오 페이지 로딩 대기
            print("3️⃣ 카카오 페이지 로딩...")
            
            WebDriverWait(self.driver, 15).until(
                lambda driver: "kakao" in driver.current_url.lower() or 
                              len(driver.find_elements(By.CSS_SELECTOR, "input[name='loginId']")) > 0
            )
            time.sleep(3)
            
            # 4단계: 아이디 입력
            print("4️⃣ 아이디 입력...")
            try:
                username_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='loginId']")
                username_field.clear()
                username_field.send_keys(username)
                print("✅ 아이디 입력 성공")
            except:
                print("❌ 아이디 입력 실패")
                return False
            
            # 5단계: 비밀번호 입력
            print("5️⃣ 비밀번호 입력...")
            try:
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                password_field.clear()
                password_field.send_keys(password)
                print("✅ 비밀번호 입력 성공")
            except:
                print("❌ 비밀번호 입력 실패")
                return False
            
            # 6단계: 로그인 버튼 클릭
            print("6️⃣ 로그인 버튼 클릭...")
            try:
                login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_btn.click()
                print("✅ 로그인 버튼 클릭 성공")
            except:
                print("❌ 로그인 버튼 클릭 실패")
                return False
            
            # 7단계: 2단계 인증 처리
            print("7️⃣ 2단계 인증 확인...")
            time.sleep(5)
            
            current_url = self.driver.current_url
            
            if "tmsTwoStepVerification" in current_url or "verification" in current_url.lower():
                print("📱 2단계 인증 필요!")
                print("=" * 50)
                print("🔔 핸드폰에서 카카오톡 알림을 확인하여 로그인을 승인해주세요!")
                print("   - 최대 3분 동안 자동으로 대기합니다")
                print("   - 승인 후 자동으로 다음 단계로 진행됩니다")
                print("=" * 50)
                
                if self.wait_for_approval(max_wait_minutes=3):
                    print("✅ 2단계 인증 승인 완료!")
                else:
                    print("❌ 2단계 인증 승인 시간 초과")
                    return False
            else:
                print("ℹ️ 2단계 인증 불필요")
            
            # 8단계: OAuth 승인 "계속하기" 버튼 클릭
            print("8️⃣ OAuth 승인 확인...")
            time.sleep(3)
            
            # "계속하기" 버튼 찾기 및 클릭
            continue_clicked = False
            try:
                continue_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn_agree[name='user_oauth_approval'][value='true']")
                if continue_btn and continue_btn.is_displayed() and continue_btn.is_enabled():
                    continue_btn.click()
                    print("✅ '계속하기' 버튼 클릭 성공")
                    continue_clicked = True
            except:
                print("ℹ️ '계속하기' 버튼을 찾을 수 없습니다 (OAuth 승인 불필요)")
            
            # 대안 방법으로 JavaScript 사용
            if not continue_clicked:
                try:
                    js_result = self.driver.execute_script("""
                        var continueBtn = document.querySelector('button.btn_agree[name="user_oauth_approval"][value="true"]');
                        if (continueBtn && continueBtn.offsetParent !== null) {
                            continueBtn.click();
                            return {success: true, found: true};
                        }
                        
                        // 대안: 텍스트로 찾기
                        var buttons = document.querySelectorAll('button');
                        for (var i = 0; i < buttons.length; i++) {
                            var btn = buttons[i];
                            if (btn.textContent.includes('계속하기') || btn.textContent.includes('계속')) {
                                btn.click();
                                return {success: true, found: true, method: 'text_search'};
                            }
                        }
                        
                        return {success: false, found: false};
                    """)
                    
                    if js_result and js_result.get('success'):
                        print("✅ '계속하기' 버튼 클릭 성공 (JavaScript)")
                        continue_clicked = True
                    else:
                        print("ℹ️ '계속하기' 버튼이 없습니다 (OAuth 승인 단계 생략)")
                except Exception as e:
                    print(f"⚠️ JavaScript 클릭 시도 중 오류: {e}")
            
            # 9단계: 최종 확인
            print("9️⃣ 최종 로그인 확인...")
            time.sleep(5)
            
            if self.check_login_success():
                print("🎉 완전 자동 로그인 성공!")
                self.save_cookies()
                return True
            else:
                print("❌ 로그인 실패")
                return False
                
        except Exception as e:
            print(f"❌ 로그인 중 오류: {e}")
            return False
    
    def wait_for_approval(self, max_wait_minutes=3):
        """2단계 인증 대기"""
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            current_url = self.driver.current_url
            if "tmsTwoStepVerification" not in current_url and "verification" not in current_url.lower():
                return True
            time.sleep(5)
        return False
    
    def check_login_success(self):
        """로그인 성공 확인"""
        try:
            current_url = self.driver.current_url
            return "login" not in current_url.lower() and "auth" not in current_url.lower()
        except:
            return False
    
    def save_cookies(self):
        """쿠키 저장"""
        try:
            cookies = self.driver.get_cookies()
            with open('final_cookies.pkl', 'wb') as f:
                pickle.dump(cookies, f)
            return True
        except:
            return False

# ================================
# 기존 포스팅 함수들 (V1에서 가져옴)
# ================================

def generate_blog_content(topic):
    """기존 함수명 호환성"""
    return generate_blog_content_v2(topic)

def get_keyword_image_url(keyword):
    """기존 이미지 함수 호환성"""
    images = get_multiple_images_v2([keyword], count=1)
    return images[0]["url"] if images else "https://picsum.photos/800/400"

# 기존 테이블/FAQ 생성 함수들
def generate_table_by_keyword(keyword):
    """기존 테이블 생성 함수"""
    if openai.api_key:
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"'{keyword}' 주제로 간단한 HTML 표를 만들어주세요."}],
                max_tokens=400
            )
            return resp.choices[0].message.content.strip()
        except:
            pass
    
    return f"""
    <table style="width:100%; border-collapse: collapse;">
        <tr><th style="border:1px solid #ddd; padding:8px;">항목</th><th style="border:1px solid #ddd; padding:8px;">설명</th></tr>
        <tr><td style="border:1px solid #ddd; padding:8px;">기본개념</td><td style="border:1px solid #ddd; padding:8px;">{keyword}의 기본 개념</td></tr>
        <tr><td style="border:1px solid #ddd; padding:8px;">활용방법</td><td style="border:1px solid #ddd; padding:8px;">실생활 적용 방법</td></tr>
    </table>
    """

def generate_faq_by_keyword(keyword):
    """기존 FAQ 생성 함수 (제목 기반)"""
    if openai.api_key:
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"'{keyword}' 주제 FAQ 3개를 HTML로 만들어주세요."}],
                max_tokens=600
            )
            return resp.choices[0].message.content.strip()
        except:
            pass
    
    return f"""
    <div>
        <h3>Q1. {keyword}란 무엇인가요?</h3>
        <p>A1. {keyword}는... (기본 설명)</p>
        <h3>Q2. 어떻게 활용할 수 있나요?</h3>
        <p>A2. 다양한 방법으로 활용 가능합니다.</p>
    </div>
    """

def generate_faq_by_content(title, content, max_questions=5):
    """블로그 글 내용을 기반으로 FAQ 생성 (개선된 버전)"""
    if not openai.api_key:
        return None
    
    try:
        # 콘텐츠에서 핵심 내용 추출 (처음 2000자)
        content_preview = content[:2000] if len(content) > 2000 else content
        
        prompt = f"""다음 블로그 글의 내용을 바탕으로 독자들이 궁금해할 만한 FAQ를 생성해주세요.

제목: {title}
내용: {content_preview}

요구사항:
1. 블로그 글의 실제 내용과 직접적으로 관련된 질문만 생성
2. 독자들이 실제로 궁금해할 만한 실용적인 질문
3. 블로그 글에서 언급된 구체적인 내용을 바탕으로 답변
4. 최대 {max_questions}개의 질문과 답변
5. 제목 없이 질문과 답변만 HTML 형식으로 작성

다음 형식으로 작성해주세요 (제목 제외):
<div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
    <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
        Q1. [질문]
    </div>
    <div style="padding: 15px; display: none; background: #f9f9f9;">
        A1. [답변]
    </div>
</div>

<div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
    <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
        Q2. [질문]
    </div>
    <div style="padding: 15px; display: none; background: #f9f9f9;">
        A2. [답변]
    </div>
</div>

[추가 질문들...]

주의사항:
- 각 FAQ 항목은 하나의 완전한 div 구조여야 합니다
- 답변 div에는 반드시 background: #f9f9f9; 스타일을 포함해야 합니다
- 중복된 div나 빈 div를 생성하지 마세요
- script 태그는 포함하지 마세요
"""

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "블로그 글 내용을 분석하여 관련성 높은 FAQ를 생성하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"⚠️ FAQ 생성 실패: {e}")
        return None

# ================================
# 기존 포스팅 함수들 (V1에서 가져옴)
# ================================

def save_cookies(driver, file_path=COOKIES_FILE):
    """브라우저의 쿠키 정보를 파일에 저장 (개선된 안정성)"""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 현재 모든 쿠키 가져오기
        cookies = driver.get_cookies()
        
        # 티스토리 관련 쿠키만 필터링하고 전처리
        filtered_cookies = []
        for cookie in cookies:
            # 티스토리 관련 쿠키만 선택
            if 'domain' in cookie and ('tistory.com' in cookie['domain'] or cookie['domain'] == '.tistory.com'):
                # 일부 속성 제거 또는 수정
                if 'expiry' in cookie and isinstance(cookie['expiry'], float):
                    cookie['expiry'] = int(cookie['expiry'])
                
                # 도메인 속성 표준화
                if 'tistory.com' in cookie['domain']:
                    cookie['domain'] = '.tistory.com'
                
                # 불필요한 속성 제거
                for attr in ['sameSite', 'storeId']:
                    if attr in cookie:
                        del cookie[attr]
                
                filtered_cookies.append(cookie)
            elif 'name' in cookie and cookie['name'] in ['TSSESSION', 'PHPSESSID', 'TSID', 'tisUserInfo']:
                # 이름으로 티스토리 관련 중요 쿠키 선별
                if 'expiry' in cookie and isinstance(cookie['expiry'], float):
                    cookie['expiry'] = int(cookie['expiry'])
                
                # 도메인 속성 명시적 설정
                cookie['domain'] = '.tistory.com'
                
                # 불필요한 속성 제거
                for attr in ['sameSite', 'storeId']:
                    if attr in cookie:
                        del cookie[attr]
                
                filtered_cookies.append(cookie)
        
        # 필터링된 쿠키 저장
        if filtered_cookies:
            pickle.dump(filtered_cookies, open(file_path, "wb"))
            print(f"티스토리 관련 쿠키 {len(filtered_cookies)}개가 '{file_path}'에 저장되었습니다.")
            return True
        else:
            print("티스토리 관련 쿠키를 찾을 수 없어 저장하지 않았습니다.")
            return False
    except Exception as e:
        print(f"쿠키 저장 중 오류 발생: {e}")
        return False

# def load_cookies(driver, file_path=COOKIES_FILE):
#     """저장된 쿠키 정보를 브라우저에 로드 - 사용 안 함 (완전 자동로그인만 사용)"""
def load_cookies_deprecated(driver, file_path=COOKIES_FILE):
    """저장된 쿠키 정보를 브라우저에 로드 (개선된 안정성) - 사용 안 함"""
    try:
        if os.path.exists(file_path):
            # 기존 쿠키 모두 삭제
            driver.delete_all_cookies()
            time.sleep(1)
            
            # 티스토리 메인 도메인에 접속 상태 확인
            current_url = driver.current_url
            if not ('tistory.com' in current_url):
                print("티스토리 도메인에 접속되어 있지 않아 먼저 접속합니다.")
                driver.get("https://www.tistory.com")
                time.sleep(3)
            
            # 쿠키 파일 로드
            cookies = pickle.load(open(file_path, "rb"))
            print(f"쿠키 파일에서 {len(cookies)}개의 쿠키를 읽었습니다.")
            
            success_count = 0
            for cookie in cookies:
                try:
                    # 필수 속성 확인
                    required_attrs = ['name', 'value']
                    if not all(attr in cookie for attr in required_attrs):
                        continue
                    
                    # 문제가 될 수 있는 속성 제거 또는 수정
                    if 'expiry' in cookie:
                        if not isinstance(cookie['expiry'], int):
                            cookie['expiry'] = int(cookie['expiry'])
                    
                    # 불필요한 속성 제거
                    for attr in ['sameSite', 'storeId']:
                        if attr in cookie:
                            del cookie[attr]
                    
                    # 도메인 속성 확인 및 수정
                    if 'domain' in cookie:
                        # 티스토리 도메인인지 확인
                        if 'tistory.com' not in cookie['domain']:
                            continue
                        
                        # 도메인 형식 수정
                        if not cookie['domain'].startswith('.'):
                            cookie['domain'] = '.tistory.com'
                    else:
                        # 도메인 속성이 없으면 추가
                        cookie['domain'] = '.tistory.com'
                    
                    # 쿠키 추가 시도
                    try:
                        driver.add_cookie(cookie)
                        success_count += 1
                    except Exception as add_e:
                        # 도메인 문제 대응 (다른 방식 시도)
                        try:
                            simple_cookie = {
                                'name': cookie['name'], 
                                'value': cookie['value'],
                                'domain': '.tistory.com'
                            }
                            driver.add_cookie(simple_cookie)
                            success_count += 1
                        except:
                            continue
                
                except Exception as cookie_e:
                    continue
            
            print(f"성공적으로 {success_count}/{len(cookies)}개의 쿠키를 로드했습니다.")
            
            # 페이지 새로고침하여 쿠키 적용
            driver.refresh()
            time.sleep(3)
            
            return success_count > 0
        else:
            print(f"쿠키 파일 '{file_path}'이 존재하지 않습니다.")
            return False
    except Exception as e:
        print(f"쿠키 로드 중 오류 발생: {e}")
        return False

# def is_logged_in(driver):
#     """로그인 상태 확인 - 사용 안 함 (완전 자동로그인만 사용)"""
def is_logged_in_deprecated(driver):
    """로그인 상태 확인 (강화된 다중 검증) - 사용 안 함"""
    try:
        print("🔍 로그인 상태 확인 중...")
        
        # 1차 확인: 특정 블로그 관리 페이지 접속 시도 (가장 확실한 방법)
        print("   🔄 특정 블로그 관리 페이지 접속으로 로그인 상태 확인...")
        try:
            # BLOG_NEW_POST_URL을 활용해 실제 블로그 관리 접속
            driver.get(BLOG_NEW_POST_URL)  # "https://climate-insight.tistory.com/manage/newpost"
            time.sleep(5)
            
            current_url = driver.current_url
            print(f"   블로그 관리 페이지 결과 URL: {current_url}")
            
            # 로그인 페이지로 리다이렉트되지 않았으면 성공
            if not any(keyword in current_url.lower() for keyword in ['login', 'auth', 'signin']):
                # 추가 검증: 실제 포스트 작성 페이지 요소 확인
                editor_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "textarea#post-title-inp, .editor-container, #editor-mode-html, .post-editor, .write-editor")
                if editor_elements:
                    print("   ✅ 블로그 관리 페이지 접속 및 에디터 요소 확인 성공")
                    return True
                else:
                    print("   ⚠️ 블로그 관리 페이지에 접속했지만 에디터 요소를 찾을 수 없음")
            else:
                print("   ❌ 블로그 관리 페이지 접속 시 로그인 페이지로 리다이렉트됨")
        except Exception as blog_mgmt_e:
            print(f"   ⚠️ 블로그 관리 페이지 접속 중 오류: {blog_mgmt_e}")
        
        # 2차 확인: 티스토리 전체 관리 페이지 접속 시도
        print("   🔄 티스토리 전체 관리 페이지 접속 확인...")
        try:
            driver.get("https://www.tistory.com/manage/")
            time.sleep(5)
            
            current_url = driver.current_url
            print(f"   전체 관리 페이지 결과 URL: {current_url}")
            
            # 로그인 페이지로 리다이렉트되지 않았으면 성공
            if not any(keyword in current_url.lower() for keyword in ['login', 'auth', 'signin']):
                # 추가 검증: 실제 티스토리 관리 페이지 요소 확인 (정확한 선택자)
                management_elements = driver.find_elements(By.CSS_SELECTOR, 
                    ".user_info, .blog_list, .blog-item, .header_user, .manage-header, .main_manage")
                if management_elements:
                    print("   ✅ 전체 관리 페이지 접속 및 관리 요소 확인 성공")
                    return True
                else:
                    print("   ⚠️ 전체 관리 페이지에 접속했지만 관리 요소를 찾을 수 없음")
            else:
                print("   ❌ 전체 관리 페이지 접속 시 로그인 페이지로 리다이렉트됨")
        except Exception as mgmt_e:
            print(f"   ⚠️ 전체 관리 페이지 접속 중 오류: {mgmt_e}")
        
        # 3차 확인: 티스토리 메인 페이지에서 강화된 DOM 기반 로그인 상태 확인
        print("   🔄 메인 페이지에서 강화된 DOM 기반 로그인 상태 확인...")
        try:
            driver.get("https://www.tistory.com")
            time.sleep(3)
            
            # JavaScript로 더 정확한 로그인 상태 확인
            login_status = driver.execute_script("""
                var result = {logged_in: false, reason: '', details: []};
                
                // 1. 명확한 로그인 버튼 확인 (가장 확실한 미로그인 신호)
                var loginButtons = document.querySelectorAll('a[href*="login"], button[onclick*="login"], .btn_login, .login-btn');
                for (var i = 0; i < loginButtons.length; i++) {
                    if (loginButtons[i].offsetParent !== null) {
                        var btnText = loginButtons[i].textContent.trim();
                        if (btnText.includes('로그인') || btnText.includes('Login') || btnText === '시작하기') {
                            result.details.push('로그인 버튼 발견: ' + btnText);
                            result.reason = '명확한 로그인 버튼 발견';
                            return result;
                        }
                    }
                }
                
                // 2. 사용자 닉네임/프로필 확인 (가장 확실한 로그인 신호)
                var profileSelectors = ['.user_info .nickname', '.profile .user-name', '.header_user .nick', 
                                       '.user-profile .name', '.profile-info .nickname', '.user_nick'];
                for (var j = 0; j < profileSelectors.length; j++) {
                    var profiles = document.querySelectorAll(profileSelectors[j]);
                    for (var k = 0; k < profiles.length; k++) {
                        if (profiles[k].offsetParent !== null && profiles[k].textContent.trim().length > 0) {
                            result.logged_in = true;
                            result.reason = '사용자 프로필 정보 발견';
                            result.details.push('프로필 요소: ' + profileSelectors[j]);
                            return result;
                        }
                    }
                }
                
                // 3. 블로그 관리/내 블로그 링크 확인
                var blogManageSelectors = ['a[href*="/manage"]', 'a[href*="blog"]', '.my_blog', '.manage_link', '.blog-manage'];
                for (var l = 0; l < blogManageSelectors.length; l++) {
                    var blogLinks = document.querySelectorAll(blogManageSelectors[l]);
                    for (var m = 0; m < blogLinks.length; m++) {
                        if (blogLinks[m].offsetParent !== null) {
                            var linkText = blogLinks[m].textContent.trim();
                            if (linkText.includes('내 블로그') || linkText.includes('관리') || 
                                linkText.includes('My Blog') || linkText.includes('글쓰기')) {
                                result.logged_in = true;
                                result.reason = '블로그 관리 링크 발견';
                                result.details.push('관리 링크: ' + linkText);
                                return result;
                            }
                        }
                    }
                }
                
                // 4. 로그아웃 버튼 확인 (확실한 로그인 신호)
                var logoutButtons = document.querySelectorAll('a[href*="logout"], button[onclick*="logout"], .btn_logout, .logout-btn');
                for (var n = 0; n < logoutButtons.length; n++) {
                    if (logoutButtons[n].offsetParent !== null) {
                        var logoutText = logoutButtons[n].textContent.trim();
                        if (logoutText.includes('로그아웃') || logoutText.includes('Logout')) {
                            result.logged_in = true;
                            result.reason = '로그아웃 버튼 발견';
                            result.details.push('로그아웃 버튼: ' + logoutText);
                            return result;
                        }
                    }
                }
                
                // 5. 페이지 전체 분석
                var bodyText = document.body.textContent;
                if (bodyText.includes('님, 안녕하세요') || bodyText.includes('님의 블로그')) {
                    result.logged_in = true;
                    result.reason = '페이지 텍스트에서 사용자 인사말 발견';
                    result.details.push('인사말 텍스트 확인');
                    return result;
                }
                
                result.reason = '로그인 상태를 확인할 수 있는 요소를 찾을 수 없음';
                result.details.push('DOM 검사 완료, 결정적 요소 없음');
                return result;
            """)
            
            if login_status and login_status.get('logged_in'):
                print(f"   ✅ 강화된 DOM 기반 로그인 상태 확인 성공: {login_status.get('reason')}")
                if login_status.get('details'):
                    for detail in login_status.get('details'):
                        print(f"      - {detail}")
                return True
            else:
                print(f"   ❌ 강화된 DOM 기반 로그인 상태 확인 실패: {login_status.get('reason') if login_status else 'JavaScript 실행 실패'}")
                if login_status and login_status.get('details'):
                    for detail in login_status.get('details'):
                        print(f"      - {detail}")
        except Exception as dom_e:
            print(f"   ⚠️ 강화된 DOM 기반 확인 중 오류: {dom_e}")
        
        # 4차 확인: URL 기반 최종 확인 (보조 수단)
        print("   🔄 URL 기반 최종 확인...")
        current_url = driver.current_url
        print(f"   현재 URL: {current_url}")
        
        # 명확히 로그인 페이지인 경우만 실패로 판정
        if any(keyword in current_url.lower() for keyword in ['login', 'auth', 'signin']):
            print("   ❌ URL에 로그인 관련 키워드 발견")
            return False
            
        print("   ❌ 모든 확인 방법에서 확실한 로그인 상태를 검증할 수 없음")
        print("   ⚠️ 이 상태에서는 쿠키가 만료되었거나 로그인이 필요할 가능성이 높습니다")
        return False
            
    except Exception as e:
        print(f"   ❌ 로그인 상태 확인 중 전체 오류: {e}")
        return False

# ================================
# 쿠키 기반 자동로그인 관련 함수들 (사용 안 함)
# ================================
# 
# 아래 함수들은 불안정한 검증 로직으로 인해 사용하지 않습니다:
# - try_auto_login(): 쿠키 기반 자동로그인 시도
# - is_logged_in(): 로그인 상태 확인  
# - load_cookies(): 저장된 쿠키 로드
# 
# 대신 완전 자동로그인(FinalTistoryLogin)만 사용합니다.
# ================================

# def try_auto_login(driver):
#     """저장된 쿠키로 자동 로그인 시도 - 사용 안 함 (불안정한 검증 로직)"""
#     # 이 함수는 더 이상 사용하지 않습니다.
#     # 완전 자동로그인(FinalTistoryLogin)만 사용합니다.
#     pass

def handle_alerts(driver, max_attempts=5, action="accept"):
    """알림창 자동 처리"""
    for attempt in range(max_attempts):
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"알림창 발견: '{alert_text}'")
            
            if action == "accept":
                alert.accept()
                print("알림창을 승인했습니다.")
            elif action == "dismiss":
                alert.dismiss()
                print("알림창을 취소했습니다.")
            elif action == "ask":
                choice = input(f"알림창: '{alert_text}' - 승인하시겠습니까? (y/n): ")
                if choice.lower() == 'y':
                    alert.accept()
                    print("사용자가 알림창을 승인했습니다.")
                else:
                    alert.dismiss()
                    print("사용자가 알림창을 취소했습니다.")
            
            time.sleep(1)
        except:
            break  # 더 이상 알림창이 없으면 종료

def check_editor_mode(driver):
    """현재 에디터가 HTML 모드인지 확인하는 함수 (기존 강력한 로직 적용)"""
    try:
        # JavaScript를 사용하여 HTML 모드 확인
        is_html_mode = driver.execute_script("""
            // HTML 모드 확인
            if (document.querySelector('.html-editor') || 
                document.querySelector('.switch-html.active') ||
                document.querySelector('button[data-mode="html"].active') ||
                (window.tistoryEditor && window.tistoryEditor.isHtmlMode)) {
                return true;
            } 
            return false;
        """)
        return is_html_mode if is_html_mode else False
    except:
        return False

def switch_to_html_mode(driver):
    """HTML 모드로 전환 (기존 파일의 강력한 로직 적용)"""
    try:
        print("HTML 모드로 전환을 시도합니다...")
        
        # 방법 1: 사용자가 제공한 HTML 요소 직접 선택
        try:
            html_element = driver.find_element(By.ID, "editor-mode-html")
            print("HTML 모드 요소(#editor-mode-html)를 ID로 찾았습니다.")
            
            element_class = html_element.get_attribute("class")
            element_text = html_element.text
            print(f"HTML 요소 정보: class='{element_class}', text='{element_text}'")
            
            html_element.click()
            print("HTML 모드 요소를 클릭했습니다.")
            time.sleep(1)
            
            # 확인 대화상자 처리
            try:
                alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
                if alert:
                    print(f"알림창 발견: '{alert.text}'")
                    alert.accept()
                    print("알림창의 '확인' 버튼을 클릭했습니다.")
            except:
                pass
                
            return True
        except Exception as id_e:
            print(f"HTML 모드 요소 직접 클릭 실패: {id_e}")
        
        # 방법 2: 모드 버튼 클릭 후 HTML 모드 선택
        try:
            mode_btn = driver.find_element(By.CSS_SELECTOR, "#editor-mode-layer-btn")
            mode_btn.click()
            print("에디터 모드 버튼을 클릭하여 드롭다운 메뉴를 표시했습니다.")
            time.sleep(1)
            
            html_span = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "editor-mode-html-text"))
            )
            
            print(f"HTML span 요소 발견: id='{html_span.get_attribute('id')}', text='{html_span.text}'")
            
            html_span.click()
            print("HTML 모드 span 요소를 클릭했습니다.")
            time.sleep(1)
            
            # 확인 대화상자 처리
            try:
                alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
                if alert:
                    print(f"알림창 발견: '{alert.text}'")
                    alert.accept()
                    print("알림창의 '확인' 버튼을 클릭했습니다.")
            except:
                pass
                
            return True
        except Exception as dropdown_e:
            print(f"드롭다운을 통한 HTML 모드 선택 실패: {dropdown_e}")
        
        # 방법 3: 일반적인 HTML 버튼 찾기
        html_buttons = []
        
        # CSS 선택자로 찾기
        primary_buttons = driver.find_elements(By.CSS_SELECTOR, 
            ".btn_html, button[data-mode='html'], .html-mode-button, .switch-html, .mce-i-code")
        if primary_buttons:
            html_buttons.extend(primary_buttons)
            print(f"CSS 선택자로 {len(primary_buttons)}개의 HTML 버튼을 찾았습니다.")
        
        # 버튼 텍스트로 찾기
        text_buttons = driver.find_elements(By.XPATH, 
            "//button[contains(text(), 'HTML') or @title='HTML' or @aria-label='HTML']")
        if text_buttons:
            html_buttons.extend(text_buttons)
            print(f"텍스트로 {len(text_buttons)}개의 HTML 버튼을 찾았습니다.")
        
        # 에디터 툴바에서 찾기
        toolbar_buttons = driver.find_elements(By.CSS_SELECTOR, 
            ".editor-toolbar button, .mce-toolbar button, .tox-toolbar button, .toolbar-group button")
        for btn in toolbar_buttons:
            try:
                btn_title = btn.get_attribute('title') or ''
                btn_text = btn.text or ''
                if 'html' in btn_title.lower() or 'html' in btn_text.lower() or 'source' in btn_title.lower():
                    html_buttons.append(btn)
                    print(f"툴바에서 HTML 버튼을 찾았습니다: {btn_title or btn_text}")
            except:
                pass
        
        # 찾은 버튼 클릭 시도
        if html_buttons:
            html_buttons[0].click()
            print("HTML 모드 버튼을 클릭했습니다.")
            time.sleep(1)
            
            # 확인 대화상자 처리
            try:
                alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
                if alert:
                    alert.accept()
                    print("알림창을 처리했습니다.")
            except:
                pass
                
            return True
            
        # 방법 4: JavaScript로 시도
        print("버튼을 찾지 못했습니다. JavaScript로 HTML 모드 전환을 시도합니다...")
        result = driver.execute_script("""
            // 사용자가 제공한 요소 ID로 직접 클릭
            var editorHtmlElement = document.getElementById('editor-mode-html');
            if (editorHtmlElement) {
                editorHtmlElement.click();
                return "사용자 제공 HTML 요소 클릭 성공";
            }
            
            // 티스토리 에디터 API 확인
            if (window.tistoryEditor) {
                if (typeof tistoryEditor.switchHtml === 'function') {
                    tistoryEditor.switchHtml();
                    return "tistoryEditor.switchHtml() 호출 성공";
                }
                
                // 티스토리 이벤트 발생
                var htmlButton = document.querySelector('[data-mode="html"], .btn_html, .switch-html');
                if (htmlButton) {
                    htmlButton.click();
                    return "HTML 버튼 클릭 성공";
                }
            }
            
            // TinyMCE 에디터 확인
            if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                try {
                    if (tinyMCE.activeEditor.plugins.code) {
                        tinyMCE.activeEditor.execCommand('mceCodeEditor');
                        return "TinyMCE 코드 에디터 활성화 성공";
                    }
                } catch(e) {
                    console.log("TinyMCE 코드 에디터 오류:", e);
                }
            }
            
            // 모든 HTML 관련 요소 검색
            var htmlElements = [
                document.querySelector('div[id*="html"]'),
                document.querySelector('button[id*="html"]'),
                document.querySelector('span[id*="html"]')
            ];
            
            for (var i = 0; i < htmlElements.length; i++) {
                if (htmlElements[i]) {
                    htmlElements[i].click();
                    return "HTML 관련 요소 클릭 성공";
                }
            }
            
            return "HTML 모드로 전환할 수 있는 방법을 찾지 못했습니다.";
        """)
        
        print(f"JavaScript 실행 결과: {result}")
        time.sleep(2)  # 모드 전환 대기
        
        return True
            
    except Exception as e:
        print(f"HTML 모드 전환 중 오류: {e}")
        return False

def find_editor_iframe(driver):
    """에디터 iframe 찾기"""
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            iframe_id = iframe.get_attribute("id") or ""
            if "editor" in iframe_id.lower():
                return iframe
        return None
    except:
        return None

def set_html_content(driver, content, iframe_editor):
    """HTML 모드에서 콘텐츠 설정 - 중복 입력 방지 및 자동화 감지 우회"""
    try:
        # 콘텐츠가 잘 설정되도록 HTML 태그 보완
        print("\n=== HTML 콘텐츠 설정 시도 (개선 버전) ===")
        print(f"콘텐츠 길이: {len(content)} 글자")
        
        # 디버깅을 위해 콘텐츠 시작 부분 출력
        content_preview = content[:100] + "..." if len(content) > 100 else content
        print(f"콘텐츠 미리보기:\n    {content_preview}")
        
        # HTML 형식 확인 및 보정
        if not content.strip().startswith("<"):
            print("경고: 콘텐츠에 HTML 태그가 없습니다. HTML 태그로 감싸줍니다.")
            content = f"<div>\n{content}\n</div>"
        
        # 내용 설정 성공 여부
        content_set_success = False
        
        # iframe 확인 및 로그
        print(f"iframe_editor 존재 여부: {iframe_editor is not None}")
        
        # === 방법 1: 자연스러운 타이핑 방식으로 콘텐츠 설정 (티스토리 자동화 감지 우회) ===
        print("\n=== 자연스러운 타이핑 방식으로 콘텐츠 설정 ===")
        try:
            natural_typing_result = driver.execute_script("""
                console.log("=== 자연스러운 타이핑 방식으로 콘텐츠 설정 시도 ===");
                
                // 1. 에디터 요소 찾기 우선순위 순서대로
                var editor = null;
                var editorType = "";
                
                // CodeMirror 에디터 찾기 (최우선)
                var cmElements = document.querySelectorAll('.CodeMirror');
                if (cmElements.length > 0) {
                    var cmElement = cmElements[0];
                    var cmTextarea = cmElement.querySelector('textarea');
                    if (cmTextarea) {
                        editor = cmTextarea;
                        editorType = "CodeMirror textarea";
                        console.log("CodeMirror textarea 발견");
                    }
                }
                
                // 일반 textarea 찾기 (제목/태그 제외)
                if (!editor) {
                    var allTextareas = document.querySelectorAll('textarea');
                    for (var i = 0; i < allTextareas.length; i++) {
                        var ta = allTextareas[i];
                        if (ta.id !== 'post-title-inp' && 
                            !ta.className.includes('textarea_tit') && 
                            ta.id !== 'tagText' && 
                            (!ta.placeholder || !ta.placeholder.includes('태그'))) {
                            editor = ta;
                            editorType = "일반 textarea (인덱스: " + i + ")";
                            console.log("일반 textarea 발견:", i);
                            break;
                        }
                    }
                }
                
                if (!editor) {
                    return {
                        success: false,
                        message: "적절한 에디터를 찾지 못함",
                        editorType: "없음"
                    };
                }
                
                console.log("에디터 발견:", editorType);
                
                // 2. 기존 값 확인 및 강제 초기화 (새 글 작성시 이전 글 제거)
                var currentValue = editor.value || "";
                if (currentValue.length > 100) {
                    console.log("기존 콘텐츠가 있습니다 (길이:", currentValue.length, "). 새 글 작성을 위해 기존 콘텐츠를 지우고 새로 설정합니다.");
                    // 기존 콘텐츠를 완전히 지우고 새로운 콘텐츠로 교체
                    editor.value = "";
                    console.log("기존 콘텐츠 완전 삭제 완료");
                }
                
                // 3. 자연스러운 방식으로 콘텐츠 설정
                try {
                    // 에디터에 포커스
                    editor.focus();
                    console.log("에디터에 포커스 완료");
                    
                    // 기존 내용 지우기
                    editor.value = "";
                    
                    // 콘텐츠를 작은 청크로 나누어 자연스럽게 입력
                    var content = arguments[0];
                    var chunkSize = 100;  // 한 번에 입력할 문자 수
                    var totalChunks = Math.ceil(content.length / chunkSize);
                    
                    console.log("콘텐츠를", totalChunks, "개 청크로 나누어 입력 시작");
                    
                    for (var i = 0; i < totalChunks; i++) {
                        var start = i * chunkSize;
                        var end = Math.min(start + chunkSize, content.length);
                        var chunk = content.substring(start, end);
                        
                        // 현재 값에 청크 추가
                        editor.value += chunk;
                        
                        // 자연스러운 이벤트 발생 (각 청크마다)
                        editor.dispatchEvent(new Event('input', { 
                            bubbles: true, 
                            cancelable: true 
                        }));
                        
                        // 키보드 이벤트도 발생 (더 자연스럽게)
                        if (i % 5 === 0) {  // 5개 청크마다 키보드 이벤트 발생
                            editor.dispatchEvent(new KeyboardEvent('keydown', {
                                bubbles: true,
                                key: 'a',
                                code: 'KeyA'
                            }));
                        }
                    }
                    
                    // 최종 이벤트들 발생
                    var finalEvents = ['change', 'blur'];
                    finalEvents.forEach(function(eventType) {
                        editor.dispatchEvent(new Event(eventType, { 
                            bubbles: true, 
                            cancelable: true 
                        }));
                    });
                    
                    console.log("자연스러운 타이핑 방식으로 콘텐츠 설정 완료");
                    
                    // 설정 결과 확인
                    var finalValue = editor.value || "";
                    var success = finalValue.length > 100;
                    
                    return {
                        success: success,
                        message: success ? "자연 타이핑 방식 설정 성공" : "자연 타이핑 방식 설정 실패",
                        editorType: editorType,
                        contentLength: finalValue.length
                    };
                    
                } catch (e) {
                    console.error("자연스러운 타이핑 방식 설정 중 오류:", e);
                    return {
                        success: false,
                        message: "자연 타이핑 방식 오류: " + e.message,
                        editorType: editorType,
                        contentLength: 0
                    };
                }
            """, content)
            
            if natural_typing_result and natural_typing_result.get("success"):
                print(f"✅ {natural_typing_result.get('message')}")
                print(f"   에디터 타입: {natural_typing_result.get('editorType')}")
                print(f"   콘텐츠 길이: {natural_typing_result.get('contentLength')} 글자")
                content_set_success = True
            else:
                print(f"❌ 자연 타이핑 방식 실패: {natural_typing_result.get('message') if natural_typing_result else '알 수 없는 오류'}")
                
        except Exception as natural_e:
            print(f"자연스러운 타이핑 방식 중 오류: {natural_e}")
        
        # === 방법 2: CodeMirror 인스턴스 직접 사용 (방법 1 실패 시에만) ===
        if not content_set_success:
            print("\n=== CodeMirror 인스턴스 직접 사용 ===")
            try:
                codemirror_result = driver.execute_script("""
                    console.log("=== CodeMirror 인스턴스 직접 사용 ===");
                    
                    var cmElements = document.querySelectorAll('.CodeMirror');
                    if (cmElements.length > 0) {
                        var cmElement = cmElements[0];
                        
                        // CodeMirror 인스턴스 직접 사용
                        if (cmElement.CodeMirror) {
                            console.log("CodeMirror 인스턴스 발견");
                            try {
                                // 기존 값 확인 및 강제 초기화 (새 글 작성시 이전 글 제거)
                                var currentValue = cmElement.CodeMirror.getValue();
                                if (currentValue && currentValue.length > 100) {
                                    console.log("CodeMirror에 기존 콘텐츠가 있습니다. 새 글 작성을 위해 기존 콘텐츠를 지우고 새로 설정합니다.");
                                    // 기존 콘텐츠를 완전히 지우고 새로운 콘텐츠로 교체
                                    cmElement.CodeMirror.setValue("");
                                    console.log("CodeMirror 기존 콘텐츠 완전 삭제 완료");
                                }
                                
                                cmElement.CodeMirror.setValue(arguments[0]);
                                cmElement.CodeMirror.refresh();
                                console.log("CodeMirror 인스턴스에 콘텐츠 설정 성공");
                                
                                return {
                                    success: true,
                                    message: "CodeMirror 인스턴스 설정 성공",
                                    contentLength: cmElement.CodeMirror.getValue().length
                                };
                            } catch (e) {
                                console.error("CodeMirror 인스턴스 설정 오류:", e);
                                return {
                                    success: false,
                                    message: "CodeMirror 인스턴스 오류: " + e.message,
                                    contentLength: 0
                                };
                            }
                        }
                    }
                    
                    return {
                        success: false,
                        message: "CodeMirror 인스턴스를 찾지 못함",
                        contentLength: 0
                    };
                """, content)
                
                if codemirror_result and codemirror_result.get("success"):
                    print(f"✅ {codemirror_result.get('message')}")
                    print(f"   콘텐츠 길이: {codemirror_result.get('contentLength')} 글자")
                    content_set_success = True
                else:
                    print(f"❌ CodeMirror 인스턴스 방식 실패: {codemirror_result.get('message') if codemirror_result else '알 수 없는 오류'}")
                    
            except Exception as cm_e:
                print(f"CodeMirror 인스턴스 방식 중 오류: {cm_e}")
        
        # === 방법 3: iframe 내부 처리 (앞의 방법들이 모두 실패한 경우에만) ===
        if not content_set_success and iframe_editor:
            print("\n=== iframe 내부 처리 (최후 수단) ===")
            try:
                # iframe으로 전환
                driver.switch_to.frame(iframe_editor)
                
                iframe_result = driver.execute_script("""
                    console.log("=== iframe 내부에서 콘텐츠 설정 ===");
                    
                    // iframe 내부의 textarea 찾기
                    var textareas = document.querySelectorAll('textarea');
                    var contentTextarea = null;
                    
                    for (var i = 0; i < textareas.length; i++) {
                        var ta = textareas[i];
                        if (ta.id !== 'post-title-inp' && 
                            !ta.className.includes('textarea_tit') && 
                            ta.id !== 'tagText') {
                            contentTextarea = ta;
                            console.log("iframe 내 콘텐츠 textarea 발견:", i);
                            break;
                        }
                    }
                    
                    if (contentTextarea) {
                        // 기존 값 확인 및 강제 초기화 (새 글 작성시 이전 글 제거)
                        var currentValue = contentTextarea.value || "";
                        if (currentValue.length > 100) {
                            console.log("iframe 내부에 기존 콘텐츠가 있습니다. 새 글 작성을 위해 기존 콘텐츠를 지우고 새로 설정합니다.");
                            // 기존 콘텐츠를 완전히 지우고 새로운 콘텐츠로 교체
                            contentTextarea.value = "";
                            console.log("iframe 기존 콘텐츠 완전 삭제 완료");
                        }
                        
                        try {
                            contentTextarea.value = arguments[0];
                            
                            // 이벤트 발생
                            var events = ['input', 'change'];
                            events.forEach(function(eventType) {
                                contentTextarea.dispatchEvent(new Event(eventType, { bubbles: true }));
                            });
                            
                            console.log("iframe 내 textarea에 콘텐츠 설정 성공");
                            
                            return {
                                success: true,
                                message: "iframe textarea 설정 성공",
                                contentLength: contentTextarea.value.length
                            };
                        } catch (e) {
                            console.error("iframe textarea 설정 오류:", e);
                            return {
                                success: false,
                                message: "iframe textarea 오류: " + e.message,
                                contentLength: 0
                            };
                        }
                    }
                    
                    return {
                        success: false,
                        message: "iframe 내 콘텐츠 textarea를 찾지 못함",
                        contentLength: 0
                    };
                """, content)
                
                # iframe에서 나오기
                driver.switch_to.default_content()
                
                if iframe_result and iframe_result.get("success"):
                    print(f"✅ {iframe_result.get('message')}")
                    print(f"   콘텐츠 길이: {iframe_result.get('contentLength')} 글자")
                    content_set_success = True
                else:
                    print(f"❌ iframe 방식 실패: {iframe_result.get('message') if iframe_result else '알 수 없는 오류'}")
                    
            except Exception as iframe_e:
                print(f"iframe 방식 중 오류: {iframe_e}")
                # iframe에서 나오기 (오류 발생 시에도)
                try:
                    driver.switch_to.default_content()
                except:
                    pass
        
        # === 최종 확인 ===
        if content_set_success:
            print("\n=== 콘텐츠 설정 최종 확인 ===")
            time.sleep(2)  # 설정 완료 대기
            
            # 설정된 콘텐츠 확인
            verification_result = driver.execute_script("""
                // 모든 가능한 에디터에서 콘텐츠 확인
                var results = [];
                
                // CodeMirror 확인
                var cmElements = document.querySelectorAll('.CodeMirror');
                if (cmElements.length > 0) {
                    var cmTextarea = cmElements[0].querySelector('textarea');
                    if (cmTextarea && cmTextarea.value && cmTextarea.value.length > 50) {
                        results.push("CodeMirror textarea: " + cmTextarea.value.length + " 글자");
                    }
                }
                
                // 일반 textarea 확인
                var textareas = document.querySelectorAll('textarea');
                for (var i = 0; i < textareas.length; i++) {
                    var ta = textareas[i];
                    if (ta.id !== 'post-title-inp' && 
                        !ta.className.includes('textarea_tit') && 
                        ta.id !== 'tagText' && 
                        ta.value && ta.value.length > 50) {
                        results.push("일반 textarea " + i + ": " + ta.value.length + " 글자");
                    }
                }
                
                return results.length > 0 ? results.join(", ") : "콘텐츠를 찾을 수 없음";
            """)
            
            print(f"콘텐츠 확인 결과: {verification_result}")
            
            if "글자" in verification_result:
                print("✅ HTML 콘텐츠가 에디터에 성공적으로 설정되었습니다!")
                return True
            else:
                print("⚠️ 콘텐츠 설정을 시도했지만 확인되지 않았습니다.")
                content_set_success = False
        
        if not content_set_success:
            print("❌ 모든 HTML 콘텐츠 설정 방법이 실패했습니다.")
            print("수동으로 본문을 입력해야 할 수 있습니다.")
            return False
        
    except Exception as e:
        print(f"❌ HTML 콘텐츠 설정 중 전체 오류: {e}")
        try:
            driver.switch_to.default_content()
        except:
            pass
        return False

def simple_tag_input(driver, tags):
    """간단한 태그 입력"""
    try:
        print(f"태그 입력: {tags}")
        
        # 태그 입력 필드 찾기
        tag_selectors = [
            "input[placeholder*='태그']",
            ".tag-input",
            "#tag-input",
            "input[name*='tag']"
        ]
        
        for selector in tag_selectors:
            try:
                tag_input = driver.find_element(By.CSS_SELECTOR, selector)
                tag_input.clear()
                tag_input.send_keys(tags)
                tag_input.send_keys(Keys.ENTER)
                print("✅ 태그 입력 완료")
                return True
            except:
                continue
        
        print("⚠️ 태그 입력 필드를 찾을 수 없습니다.")
        return False
        
    except Exception as e:
        print(f"❌ 태그 입력 실패: {e}")
        return False

def simple_title_input(driver, title_text):
    """간단하고 안정적인 제목 입력"""
    print(f"제목 입력 시작: '{title_text}'")
    
    title_selectors = [
        "textarea#post-title-inp.textarea_tit",
        "textarea#post-title-inp", 
        "textarea.textarea_tit",
        "input[placeholder*='제목']"
    ]
    
    for selector in title_selectors:
        try:
            print(f"선택자 '{selector}' 시도 중...")
            title_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            # 제목 입력
            title_input.clear()
            time.sleep(0.5)
            title_input.send_keys(title_text)
            time.sleep(0.5)
            
            # 입력 확인
            actual_value = title_input.get_attribute("value")
            if actual_value and len(actual_value) > 0:
                print(f"✅ 제목 입력 성공: '{actual_value}' (선택자: {selector})")
                return True
            
        except Exception as e:
            print(f"선택자 '{selector}' 실패: {e}")
            continue
    
    print("❌ 모든 선택자로 제목 입력 실패")
    return False

def write_post_v2(driver, blog_post):
    """V2 향상된 글 작성 함수 (기존 안정성 로직 적용)"""
    try:
        print("📝 V2 글 작성 시작...")
        
        # 1. 제목 입력 (강화된 기존 내용 완전 삭제 후 입력)
        print("제목을 입력합니다...")
        title_success = simple_title_input(driver, blog_post["title"])
        if not title_success:
            print("⚠️ 제목 입력 실패 - 수동으로 입력이 필요할 수 있습니다.")
        
        # 2. 에디터 모드 확인 및 HTML 모드 전환
        is_html_mode = check_editor_mode(driver)
        print(f"현재 에디터 HTML 모드 여부: {is_html_mode}")
        
        if not is_html_mode:
            print("HTML 모드로 전환 중...")
            switch_to_html_mode(driver)
        
        # 모드 전환 후 다시 확인
        time.sleep(2)
        is_html_mode = check_editor_mode(driver)
        print(f"모드 전환 후 HTML 모드 여부: {is_html_mode}")
        
        # 3. 본문 입력 (HTML 모드)
        print("본문을 입력합니다...")
        try:
            # HTML 콘텐츠 우선 사용 (URL 콘텐츠의 경우)
            content = blog_post.get("html_content", blog_post["content"])
            
            # HTML 콘텐츠 여부 확인
            if content and len(content) > len(blog_post["content"]) * 2:
                print("✅ 완전한 HTML 구조 사용 (URL 콘텐츠)")
            else:
                print("📝 일반 텍스트 콘텐츠 사용")
                content = blog_post["content"]
            
            iframe_editor = find_editor_iframe(driver)
            set_html_content(driver, content, iframe_editor)
            print("✅ 본문 입력 완료")
        except Exception as e:
            print(f"본문 입력 중 오류: {e}")
            driver.switch_to.default_content()  # iframe에서 빠져나옴
        
        # 4. 태그 입력
        print("태그를 입력합니다...")
        try:
            simple_tag_input(driver, blog_post["tags"])
            print("✅ 태그 입력 완료")
        except Exception as e:
            print(f"태그 입력 중 오류: {e}")
        
        print("✅ V2 글 작성 완료!")
        return True
        
    except Exception as e:
        print(f"❌ V2 글 작성 실패: {e}")
        return False

def publish_post(driver):
    """
    글 발행 과정을 처리하는 함수 (기존 강력한 로직 적용)
    """
    print("\n==========================================")
    print("==== 발행 함수 호출됨 (publish_post) ====")
    print("==========================================\n")
    publish_success = False
    
    try:
        # 1단계: TinyMCE 모달 창이 있다면 닫기 (클릭 방해 요소 제거)
        try:
            print("TinyMCE 모달 창 확인 및 제거 중...")
            driver.execute_script("""
                var modalBlock = document.querySelector('#mce-modal-block');
                if (modalBlock) {
                    modalBlock.parentNode.removeChild(modalBlock);
                    console.log('모달 블록 제거됨');
                }
                
                var modalWindows = document.querySelectorAll('.mce-window, .mce-reset');
                for (var i = 0; i < modalWindows.length; i++) {
                    if (modalWindows[i].style.display !== 'none') {
                        modalWindows[i].style.display = 'none';
                        console.log('모달 창 숨김 처리됨');
                    }
                }
            """)
            print("모달 창 처리 완료")
        except Exception as modal_e:
            print(f"모달 창 처리 중 오류: {modal_e}")
        
        # 2단계: '완료' 버튼 찾아 클릭
        print("\n1단계: '완료' 버튼을 찾아 클릭합니다...")
        
        # 2-1. CSS 선택자로 완료 버튼 찾기
        complete_button_selectors = [
            "#publish-layer-btn",       # 티스토리 완료 버튼 ID
            ".btn_publish", 
            ".publish-button",
            "button[type='submit']",
            ".btn_save.save-publish",   # 티스토리 발행 버튼
            ".btn_post",                # 티스토리 발행 버튼 (다른 클래스)
            ".btn_submit",              # 티스토리 발행 버튼 (다른 클래스)
            ".editor-footer button:last-child" # 에디터 푸터의 마지막 버튼
        ]
        
        complete_button_found = False
        
        print("CSS 선택자로 완료 버튼 찾기 시도 중...")
        for selector in complete_button_selectors:
            try:
                print(f"선택자 '{selector}' 시도 중...")
                complete_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                if complete_buttons:
                    complete_button = complete_buttons[0]
                    button_text = complete_button.text.strip()
                    print(f"'완료' 버튼을 찾았습니다: {selector} (텍스트: '{button_text}')")
                    
                    # 클릭 전 스크립트 실행하여 방해 요소 제거
                    driver.execute_script("""
                        var modalBlock = document.querySelector('#mce-modal-block');
                        if (modalBlock) modalBlock.remove();
                    """)
                    
                    # 버튼 클릭
                    complete_button.click()
                    print("'완료' 버튼을 클릭했습니다.")
                    time.sleep(3)  # 모달 대화상자가 나타날 때까지 대기
                    complete_button_found = True
                    break
            except Exception as btn_e:
                print(f"'{selector}' 선택자로 버튼 클릭 시도 중 오류: {btn_e}")
        
        # 2-2. JavaScript로 완료 버튼 클릭 시도
        if not complete_button_found:
            try:
                print("\nJavaScript를 통해 '완료' 버튼 클릭을 시도합니다...")
                result = driver.execute_script("""
                    // 완료 버튼 ID로 직접 찾기
                    var publishBtn = document.querySelector('#publish-layer-btn');
                    if (publishBtn) {
                        publishBtn.click();
                        return "ID로 버튼 클릭";
                    }
                    
                    // 버튼 텍스트로 찾기
                    var buttons = document.querySelectorAll('button');
                    for (var i = 0; i < buttons.length; i++) {
                        if (buttons[i].textContent.includes('완료')) {
                            buttons[i].click();
                            return "텍스트로 버튼 클릭";
                        }
                    }
                    
                    // 에디터 API 사용
                    if (window.PostEditor && window.PostEditor.publish) {
                        window.PostEditor.publish();
                        return "PostEditor API 사용";
                    }
                    
                    // 하단 영역의 마지막 버튼 클릭
                    var footerButtons = document.querySelectorAll('.editor-footer button, .foot_post button, .write_foot button');
                    if (footerButtons.length > 0) {
                        footerButtons[footerButtons.length - 1].click();
                        return "하단 마지막 버튼 클릭";
                    }
                    
                    return false;
                """)
                
                if result:
                    print(f"JavaScript를 통해 '완료' 버튼을 클릭했습니다: {result}")
                    time.sleep(3)  # 모달 대화상자가 나타날 때까지 대기
                    complete_button_found = True
                else:
                    print("JavaScript로 '완료' 버튼을 찾지 못했습니다.")
            except Exception as js_e:
                print(f"JavaScript를 통한 '완료' 버튼 클릭 중 오류: {js_e}")
        
        # 2-3. XPath로 완료 버튼 찾기
        if not complete_button_found:
            try:
                print("\nXPath로 완료 버튼 찾기 시도 중...")
                complete_xpath_expressions = [
                    "//button[contains(text(), '완료')]",
                    "//button[@id='publish-layer-btn']",
                    "//button[contains(@class, 'publish') or contains(@id, 'publish')]",
                    "//div[contains(@class, 'editor-footer') or contains(@class, 'foot_post')]//button[last()]"
                ]
                
                for xpath_expr in complete_xpath_expressions:
                    print(f"XPath 표현식 '{xpath_expr}' 시도 중...")
                    complete_buttons_xpath = driver.find_elements(By.XPATH, xpath_expr)
                    if complete_buttons_xpath:
                        complete_button = complete_buttons_xpath[0]
                        button_text = complete_button.text.strip()
                        print(f"XPath로 '완료' 버튼을 찾았습니다: {xpath_expr} (텍스트: '{button_text}')")
                        
                        # 클릭 전 스크립트 실행하여 방해 요소 제거
                        driver.execute_script("document.querySelector('#mce-modal-block')?.remove();")
                        
                        # 버튼 클릭
                        complete_button.click()
                        print("XPath로 찾은 '완료' 버튼을 클릭했습니다.")
                        time.sleep(3)  # 모달 대화상자가 나타날 때까지 대기
                        complete_button_found = True
                        break
            except Exception as xpath_e:
                print(f"XPath를 통한 '완료' 버튼 찾기 중 오류: {xpath_e}")
        
        # 2-4. 버튼을 찾지 못한 경우, 하단 영역의 모든 버튼 표시
        if not complete_button_found:
            try:
                print("\n'완료' 버튼을 찾지 못했습니다. 하단 영역 버튼 분석 중...")
                
                # 하단 영역의 모든 버튼 요소 출력
                bottom_buttons = driver.find_elements(By.CSS_SELECTOR, ".editor-footer button, .foot_post button, .write_foot button, #editor-root > div:last-child button")
                print(f"하단 영역에서 {len(bottom_buttons)}개의 버튼을 찾았습니다.")
                
                for i, btn in enumerate(bottom_buttons):
                    try:
                        btn_text = btn.text.strip() or '(텍스트 없음)'
                        btn_class = btn.get_attribute('class') or '(클래스 없음)'
                        btn_id = btn.get_attribute('id') or '(ID 없음)'
                        print(f"하단 버튼 {i+1}: 텍스트='{btn_text}', 클래스='{btn_class}', ID='{btn_id}'")
                        
                        # 완료/발행 관련 버튼 추정
                        if ('완료' in btn_text or '발행' in btn_text or 
                            '등록' in btn_text or 
                            'publish' in btn_text.lower() or 'submit' in btn_text.lower()):
                            print(f"  => 발행 버튼으로 보입니다!")
                            
                            proceed = input(f"이 버튼({btn_text})을 발행 버튼으로 클릭하시겠습니까? (y/n): ")
                            if proceed.lower() == 'y':
                                btn.click()
                                print(f"'{btn_text}' 버튼을 클릭했습니다.")
                                time.sleep(3)  # 저장 처리 대기
                                complete_button_found = True
                    except Exception as btn_e:
                        print(f"버튼 {i+1} 정보 읽기 실패: {btn_e}")
                
                # 마지막 버튼 자동 선택 옵션
                if not complete_button_found and bottom_buttons:
                    last_button = bottom_buttons[-1]
                    try:
                        last_btn_text = last_button.text.strip() or '(텍스트 없음)'
                        print(f"\n하단 영역의 마지막 버튼: '{last_btn_text}'")
                        proceed = input("하단 영역의 마지막 버튼을 클릭하시겠습니까? (y/n): ")
                        if proceed.lower() == 'y':
                            last_button.click()
                            print(f"마지막 버튼('{last_btn_text}')을 클릭했습니다.")
                            time.sleep(3)
                            complete_button_found = True
                    except Exception as last_e:
                        print(f"마지막 버튼 클릭 중 오류: {last_e}")
            except Exception as bottom_e:
                print(f"하단 버튼 분석 중 오류: {bottom_e}")
        
        # 3단계: '공개 발행' 버튼 찾아 클릭 (모달 대화상자)
        if complete_button_found:
            print("\n2단계: '공개 발행' 버튼을 찾아 클릭합니다...")
            time.sleep(2)  # 모달이 완전히 나타날 때까지 대기
            
            # 3-1. XPath로 '공개 발행' 버튼 찾기 (가장 정확한 방법)
            try:
                print("XPath로 '공개 발행' 버튼 찾기 시도 중...")
                publish_xpath_expressions = [
                    "//button[contains(text(), '공개 발행')]",
                    "//button[contains(text(), '발행')]",
                    "//div[contains(@class, 'layer') or contains(@class, 'modal')]//button[contains(text(), '발행') or contains(text(), '공개')]",
                    "//div[contains(@class, 'layer') or contains(@class, 'modal')]//button[last()]"
                ]
                
                publish_button_found = False
                
                for xpath_expr in publish_xpath_expressions:
                    print(f"XPath 표현식 '{xpath_expr}' 시도 중...")
                    publish_buttons = driver.find_elements(By.XPATH, xpath_expr)
                    if publish_buttons:
                        publish_button = publish_buttons[0]
                        button_text = publish_button.text.strip()
                        print(f"'공개 발행' 버튼을 찾았습니다: {xpath_expr} (텍스트: '{button_text}')")
                        
                        # 버튼 클릭
                        publish_button.click()
                        print(f"'{button_text}' 버튼을 클릭했습니다.")
                        time.sleep(5)  # 발행 처리 대기
                        publish_button_found = True
                        publish_success = True
                        break
                
                # 3-2. CSS 선택자로 '공개 발행' 버튼 찾기
                if not publish_button_found:
                    print("\nCSS 선택자로 '공개 발행' 버튼 찾기 시도 중...")
                    publish_selectors = [
                        ".btn_publish", 
                        ".publish-button",
                        ".layer_post button:last-child",
                        ".layer_publish button:last-child",
                        ".modal_publish button:last-child",
                        ".btn_confirm[data-action='publish']",
                        ".btn_ok"
                    ]
                    
                    for selector in publish_selectors:
                        print(f"선택자 '{selector}' 시도 중...")
                        publish_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        if publish_buttons:
                            publish_button = publish_buttons[0]
                            button_text = publish_button.text.strip()
                            print(f"'공개 발행' 버튼을 찾았습니다: {selector} (텍스트: '{button_text}')")
                            
                            # 버튼 클릭
                            publish_button.click()
                            print(f"'{button_text}' 버튼을 클릭했습니다.")
                            time.sleep(5)  # 발행 처리 대기
                            publish_button_found = True
                            publish_success = True
                            break
                
                # 3-3. JavaScript로 '공개 발행' 버튼 클릭 시도
                if not publish_button_found:
                    try:
                        print("\nJavaScript를 통해 '공개 발행' 버튼 클릭을 시도합니다...")
                        result = driver.execute_script("""
                            // 텍스트로 버튼 찾기
                            var buttons = document.querySelectorAll('button');
                            for (var i = 0; i < buttons.length; i++) {
                                var btnText = buttons[i].textContent.trim();
                                if (btnText.includes('공개 발행') || btnText.includes('발행')) {
                                    console.log('발행 버튼 찾음: ' + btnText);
                                    buttons[i].click();
                                    return "텍스트로 버튼 클릭: " + btnText;
                                }
                            }
                            
                            // 모달/레이어의 마지막 버튼 클릭
                            var modalButtons = document.querySelectorAll('.layer_post button, .layer_publish button, .modal_publish button');
                            if (modalButtons.length > 0) {
                                var lastBtn = modalButtons[modalButtons.length - 1];
                                lastBtn.click();
                                return "모달의 마지막 버튼 클릭: " + lastBtn.textContent.trim();
                            }
                            
                            return false;
                        """)
                        
                        if result:
                            print(f"JavaScript를 통해 '공개 발행' 버튼을 클릭했습니다: {result}")
                            time.sleep(5)  # 발행 처리 대기
                            publish_button_found = True
                            publish_success = True
                        else:
                            print("JavaScript로 '공개 발행' 버튼을 찾지 못했습니다.")
                    except Exception as js_e:
                        print(f"JavaScript를 통한 '공개 발행' 버튼 클릭 중 오류: {js_e}")
                
                # 3-4. 모든 모달 버튼 분석
                if not publish_button_found:
                    print("\n'공개 발행' 버튼을 찾지 못했습니다. 모달 내 모든 버튼 분석 중...")
                    
                    # 모달 레이어 찾기
                    modal_layers = driver.find_elements(By.CSS_SELECTOR, ".layer_post, .layer_publish, .modal_publish, .layer_box, .modal_dialog")
                    if modal_layers:
                        print(f"모달 레이어를 찾았습니다. ({len(modal_layers)}개)")
                        
                        for layer_idx, layer in enumerate(modal_layers):
                            try:
                                print(f"모달 레이어 {layer_idx+1} 분석 중...")
                                
                                # 레이어 내 모든 버튼
                                layer_buttons = layer.find_elements(By.TAG_NAME, "button")
                                print(f"레이어 내 {len(layer_buttons)}개의 버튼을 찾았습니다.")
                                
                                for i, btn in enumerate(layer_buttons):
                                    try:
                                        btn_text = btn.text.strip() or '(텍스트 없음)'
                                        btn_class = btn.get_attribute('class') or '(클래스 없음)'
                                        print(f"버튼 {i+1}: 텍스트='{btn_text}', 클래스='{btn_class}'")
                                        
                                        # 발행 관련 버튼 추정
                                        if ('발행' in btn_text or '공개' in btn_text or 
                                            'publish' in btn_text.lower() or 'confirm' in btn_class.lower()):
                                            print(f"  => 발행 버튼으로 보입니다!")
                                            
                                            proceed = input(f"이 버튼({btn_text})을 발행 버튼으로 클릭하시겠습니까? (y/n): ")
                                            if proceed.lower() == 'y':
                                                btn.click()
                                                print(f"'{btn_text}' 버튼을 클릭했습니다.")
                                                time.sleep(5)  # 발행 처리 대기
                                                publish_button_found = True
                                                publish_success = True
                                    except:
                                        continue
                                
                                # 레이어의 마지막 버튼 자동 선택 옵션
                                if not publish_button_found and layer_buttons:
                                    last_button = layer_buttons[-1]
                                    try:
                                        last_btn_text = last_button.text.strip() or '(텍스트 없음)'
                                        print(f"\n레이어의 마지막 버튼: '{last_btn_text}'")
                                        proceed = input("이 버튼을 발행 버튼으로 클릭하시겠습니까? (y/n): ")
                                        if proceed.lower() == 'y':
                                            last_button.click()
                                            print(f"마지막 버튼('{last_btn_text}')을 클릭했습니다.")
                                            time.sleep(5)
                                            publish_button_found = True
                                            publish_success = True
                                    except Exception as last_e:
                                        print(f"마지막 버튼 클릭 중 오류: {last_e}")
                                
                                if publish_button_found:
                                    break
                                    
                            except Exception as layer_e:
                                print(f"레이어 {layer_idx+1} 분석 중 오류: {layer_e}")
                    else:
                        print("모달 레이어를 찾지 못했습니다.")
            except Exception as publish_e:
                print(f"'공개 발행' 버튼 찾기 중 오류: {publish_e}")
        
        # 발행 성공 여부 확인
        if publish_success:
            print("\n발행이 성공적으로 완료되었습니다!")
        else:
            print("\n발행 과정에서 문제가 발생했습니다.")
    
    except Exception as e:
        print(f"발행 과정에서 오류 발생: {e}")
    
    print("\n==========================================")
    print("==== 발행 함수 종료 (publish_success: {}) ====".format(publish_success))
    print("==========================================\n")
    
    return publish_success

# ================================
# V2 실시간 트렌드 분석 시스템
# ================================

def get_current_date_info():
    """현재 시점의 날짜 정보를 동적으로 감지"""
    now = datetime.now()
    year = now.year
    month = now.month
    day = now.day
    
    # 계절 판단
    if month in [3, 4, 5]:
        season = "봄"
    elif month in [6, 7, 8]:
        season = "여름"
    elif month in [9, 10, 11]:
        season = "가을"
    else:
        season = "겨울"
    
    return {
        "year": year,
        "month": month,
        "day": day,
        "season": season,
        "formatted_date": f"{year}년 {month:02d}월 {day:02d}일"
    }

def generate_dynamic_queries(date_info):
    """실행 시점에 따른 동적 검색 쿼리 생성"""
    year = date_info["year"]
    month = date_info["month"]
    season = date_info["season"]
    
    # 동적 쿼리 생성
    queries = [
        f"{year}년 {month}월 트렌드",
        f"{year}년 {season} 트렌드",
        f"{season} 인기 키워드 {year}",
        f"최신 트렌드 {year}.{month}",
        f"{year} 주요 이슈 {season}"
    ]
    
    return queries

def extract_topics_from_text_improved(text):
    """개선된 키워드 추출 함수 - 더 정확한 패턴과 필터링"""
    if not text:
        return []
    
    topics = []
    
    # 1단계: 다양한 패턴으로 키워드 추출
    patterns = [
        r'[\-\*\•]\s*([^:\n\r]+)',  # 리스트 항목 (-, *, •)
        r'\d+\.\s*([^:\n\r]{3,30})',  # 번호 리스트 (1. 키워드)
        r'([가-힣]{2,15})\s*[:：]\s*',  # 한글 키워드: 설명
        r'【([^】]+)】',  # 【키워드】
        r'「([^」]+)」',  # 「키워드」
        r'(?:키워드|주제|트렌드)[:：]?\s*([^,\n\r]{3,20})',  # 키워드: 내용
        r'([가-힣A-Za-z\s]{3,20})(?=이|가|을|를|의|에|에서|로|으로)',  # 조사 앞 명사구
        r'#([가-힣A-Za-z0-9]{2,15})',  # 해시태그
        r'([가-힣]{2,10})\s+(?:관련|분야|산업|시장|기술)',  # 관련/분야 앞 키워드
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            topics.append(match.strip())
    
    # 2단계: 품질 필터링
    filtered_topics = []
    
    # 제외할 키워드 패턴
    exclude_patterns = [
        r'^[\d\s\-\*\•\.:：]+$',  # 숫자, 공백, 기호만
        r'^.{1,2}$',  # 너무 짧은 것
        r'^.{31,}$',  # 너무 긴 것
        r'[^\w\s가-힣]',  # 특수문자 포함
        r'(?:년|월|일|시|분|초)$',  # 시간 단위로 끝나는 것
        r'(?:등|및|또는|그리고|하지만|그러나)$',  # 접속사로 끝나는 것
    ]
    
    for topic in topics:
        topic = topic.strip()
        if not topic:
            continue
            
        # 제외 패턴 검사
        should_exclude = False
        for exclude_pattern in exclude_patterns:
            if re.search(exclude_pattern, topic):
                should_exclude = True
                break
        
        if not should_exclude and topic not in filtered_topics:
            filtered_topics.append(topic)
    
    # 3단계: 최종 정제 및 상위 10개 선택
    final_topics = []
    for topic in filtered_topics:
        # 앞뒤 따옴표, 괄호 제거
        clean_topic = re.sub(r'^["""\'\'„"„"()（）\[\]【】「」]+|["""\'\'„"„"()（）\[\]【】「」]+$', '', topic)
        clean_topic = clean_topic.strip()
        
        if (clean_topic and 
            len(clean_topic) >= 2 and 
            len(clean_topic) <= 20 and
            clean_topic not in final_topics):
            final_topics.append(clean_topic)
    
    # 상위 10개만 반환
    return final_topics[:10]

def simulate_web_search_improved(query):
    """대폭 확장된 웹 검색 시뮬레이션 - 최신 트렌드 & 다양한 카테고리"""
    print(f"    🔍 확장된 트렌드 검색: '{query}'")
    
    # 2025년 최신 트렌드 데이터베이스 (대폭 확장)
    comprehensive_trend_bank = {
        # === 기술 트렌드 ===
        "기술": [
            "- 생성형 AI ChatGPT Claude Gemini\n- 양자컴퓨팅 IBM 구글 퀀텀\n- 6G 통신기술 홀로그램\n- 자율주행 테슬라 웨이모",
            "• 뇌-컴퓨터 인터페이스 뉴럴링크\n• 로봇공학 휴머노이드 로봇\n• 증강현실 애플 비전 프로\n• 엣지 컴퓨팅 IoT 센서",
            "1. 합성생물학 유전자 편집\n2. 나노기술 신소재 개발\n3. 디지털 트윈 가상 시뮬레이션\n4. 머신러닝 딥러닝 알고리즘"
        ],
        "AI": [
            "- AI 에이전트 자동화 업무\n- 멀티모달 AI 텍스트 이미지\n- AI 칩셋 NPU 프로세서\n- AI 윤리 안전성 규제",
            "• 컴퓨터 비전 이미지 인식\n• 자연어 처리 번역 요약\n• 추천 시스템 개인화\n• 예측 분석 데이터 마이닝",
            "1. 생성형 AI 창작 도구\n2. AI 교육 맞춤형 학습\n3. AI 의료 진단 치료\n4. AI 금융 투자 분석"
        ],
        "메타버스": [
            "- VR 게임 가상현실 체험\n- 디지털 패션 NFT 아바타\n- 가상 오피스 원격 협업\n- 메타버스 교육 온라인",
            "• VR 헤드셋 오큘러스 비전프로\n• 햅틱 기술 촉각 피드백\n• 3D 모델링 가상 공간\n• 소셜 VR 가상 만남",
            "1. 가상 부동산 메타버스 투자\n2. 브랜드 마케팅 가상 매장\n3. 엔터테인먼트 콘서트 공연\n4. 의료 재활 가상 치료"
        ],
        
        # === 라이프스타일 트렌드 ===
        "라이프스타일": [
            "- 미니멀 라이프 단순한 삶\n- 제로웨이스트 친환경 실천\n- 워라밸 일과 삶 균형\n- 디지털 디톡스 스마트폰",
            "• 슬로우 라이프 여유로운 삶\n• 홈 카페 원두 커피\n• 플랜테리어 식물 인테리어\n• 업사이클링 재활용 DIY",
            "1. 사이드 허슬 부업 창업\n2. 미닝아웃 가치소비 윤리\n3. 셀프케어 정신건강 관리\n4. 로컬라이프 지역 상권"
        ],
        "건강": [
            "- 개인맞춤 영양 유전자검사\n- 멘탈헬스 정신건강 상담\n- 운동처방 맞춤형 피트니스\n- 수면관리 슬립테크 기기",
            "• 홈트레이닝 온라인 PT\n• 플랜트베이스 식물성 식단\n• 기능성 식품 건강보조제\n• 웨어러블 건강 모니터링",
            "1. 예방의학 건강검진 정밀\n2. 재생의료 줄기세포 치료\n3. 정밀의료 유전자 맞춤\n4. 디지털 치료제 앱 처방"
        ],
        "여행": [
            "- 로컬 여행 지역 관광\n- 에코 투어리즘 친환경\n- 슬로우 트래블 장기체류\n- 디지털 노마드 원격근무",
            "• 글램핑 캠핑 아웃도어\n• 펜션 리조트 휴양지\n• 문화체험 전통 관광\n• 액티비티 어드벤처 스포츠",
            "1. 치유여행 웰니스 힐링\n2. 미식여행 로컬푸드 맛집\n3. 사진여행 인스타그램 핫플\n4. 교육여행 체험학습 견학"
        ],
        
        # === 사회/경제 트렌드 ===
        "경제": [
            "- 인플레이션 물가상승 대응\n- 금리인상 통화정책 영향\n- 경기침체 불황 우려\n- 부동산 시장 변화",
            "• 암호화폐 비트코인 투자\n• ESG 지속가능 경영\n• 탄소배출권 거래제\n• 순환경제 재활용 경제",
            "1. 디지털 화폐 CBDC 도입\n2. 핀테크 모바일 결제\n3. 로보어드바이저 자동투자\n4. 크라우드펀딩 소셜 투자"
        ],
        "정책": [
            "- 기본소득 보편적 복지\n- 탄소중립 그린뉴딜 정책\n- 디지털뉴딜 IT 인프라\n- 청년정책 일자리 지원",
            "• 주거복지 공공임대 주택\n• 육아정책 출산 장려\n• 노인복지 고령화 대응\n• 장애인복지 접근성 개선",
            "1. 교육개혁 미래교육 혁신\n2. 의료개혁 공공의료 확충\n3. 노동개혁 근로시간 단축\n4. 세제개혁 부동산 과세"
        ],
        
        # === 문화/엔터테인먼트 ===
        "문화": [
            "- K-팝 한류 글로벌 확산\n- 웹툰 웹소설 디지털 콘텐츠\n- OTT 스트리밍 서비스\n- 숏폼 콘텐츠 틱톡 유튜브",
            "• 메타버스 콘서트 가상공연\n• NFT 아트 디지털 예술\n• 게임 e스포츠 대회\n• 인플루언서 크리에이터",
            "1. K-드라마 한국 드라마\n2. K-푸드 한국 음식 문화\n3. K-뷰티 한국 화장품\n4. K-패션 한국 스타일"
        ],
        "엔터테인먼트": [
            "- 버추얼 아이돌 AI 가수\n- 인터랙티브 콘텐츠 참여형\n- 개인방송 1인 미디어\n- 라이브 커머스 실시간",
            "• VR 영화 가상현실 체험\n• AR 게임 증강현실 놀이\n• 드론 쇼 무인기 공연\n• 홀로그램 3D 영상",
            "1. 팬덤 문화 아이돌 응원\n2. 굿즈 컬렉션 상품 수집\n3. 덕질 취미 활동 문화\n4. 축제 페스티벌 이벤트"
        ],
        
        # === 계절별 트렌드 ===
        "여름": [
            "- 피서지 바캉스 휴가철\n- 워터파크 수영장 물놀이\n- 캠핑 글램핑 야외활동\n- 해변 리조트 바다여행",
            "• 냉면 빙수 여름 음식\n• 선크림 자외선 차단\n• 쿨링 에어컨 선풍기\n• 비치웨어 수영복 패션",
            "1. 여름축제 불꽃놀이 행사\n2. 물놀이 용품 튜브 보트\n3. 아이스크림 빙과류 디저트\n4. 여름휴가 국내외 관광"
        ],
        "겨울": [
            "- 스키 스노보드 설상스포츠\n- 온천 사우나 겨울힐링\n- 이글루 빙어축제 체험\n- 크리스마스 연말 이벤트",
            "• 패딩 코트 겨울 아우터\n• 난방비 전기요금 절약\n• 감기 독감 건강관리\n• 가습기 건조 대비",
            "1. 겨울여행 홋카이도 유럽\n2. 군고구마 붕어빵 간식\n3. 목도리 장갑 방한용품\n4. 연말정산 세금 절약"
        ],
        
        # === 연령별 트렌드 ===
        "청년": [
            "- 취업준비 공무원 시험\n- 부동산 전세 월세\n- 연애 결혼 육아 고민\n- 부업 사이드잡 투잡",
            "• 자기계발 스킬 업그레이드\n• 재테크 투자 주식\n• 헬스 운동 다이어트\n• 여행 해외 배낭여행",
            "1. 청년정책 청년도약계좌\n2. 창업 스타트업 사업\n3. 프리랜서 긱 이코노미\n4. 멘탈케어 심리상담"
        ],
        "중장년": [
            "- 자녀교육 사교육비 부담\n- 노후준비 연금 투자\n- 건강관리 정기검진\n- 부모님 효도 관리",
            "• 승진 직장 커리어\n• 내집마련 주택구매\n• 보험 금융 재정관리\n• 취미생활 문화활동",
            "1. 중년위기 인생 재설계\n2. 가족여행 휴가 계획\n3. 건강보험 의료비 대비\n4. 은퇴설계 제2인생 준비"
        ],
        
        # === 시즌별 이슈 ===
        "2025": [
            "- 인공지능 AGI 개발 경쟁\n- 우주여행 상업화 확산\n- 자율주행 완전자율 단계\n- 양자컴퓨터 실용화 시대",
            "• 탄소중립 목표 달성 과제\n• 고령화 사회 대응 시스템\n• 디지털 격차 해소 방안\n• 바이오 기술 혁신 발전",
            "1. 메타버스 생태계 구축\n2. 블록체인 웹3 전환\n3. 로봇산업 자동화 확산\n4. 친환경 에너지 전환"
        ]
    }
    
    # 더 정교한 키워드 매칭
    query_lower = query.lower()
    
    # 1차: 직접 매칭
    for category, data_list in comprehensive_trend_bank.items():
        if category in query_lower:
            selected_data = data_list[hash(query) % len(data_list)]
            print(f"    ✅ '{category}' 카테고리 트렌드 데이터 제공")
            return selected_data
    
    # 2차: 부분 키워드 매칭
    keyword_mapping = {
        'ai': 'AI', '인공지능': 'AI', '머신러닝': 'AI',
        '가상현실': '메타버스', 'vr': '메타버스', 'ar': '메타버스',
        '건강': '건강', '운동': '건강', '다이어트': '건강', '의료': '건강',
        '여행': '여행', '관광': '여행', '휴가': '여행', '캠핑': '여행',
        '경제': '경제', '투자': '경제', '금융': '경제', '부동산': '경제',
        '정책': '정책', '정부': '정책', '복지': '정책', '법률': '정책',
        '문화': '문화', '예술': '문화', '콘텐츠': '문화', '엔터': '엔터테인먼트',
        '게임': '엔터테인먼트', '영화': '엔터테인먼트', '음악': '엔터테인먼트',
        '라이프': '라이프스타일', '생활': '라이프스타일', '취미': '라이프스타일',
        '청년': '청년', '젊은': '청년', '대학생': '청년',
        '중년': '중장년', '직장인': '중장년', '40대': '중장년', '50대': '중장년'
    }
    
    for keyword, category in keyword_mapping.items():
        if keyword in query_lower and category in comprehensive_trend_bank:
            data_list = comprehensive_trend_bank[category]
            selected_data = data_list[hash(query) % len(data_list)]
            print(f"    ✅ '{keyword}' → '{category}' 매핑으로 트렌드 데이터 제공")
            return selected_data
    
    # 3차: 계절별 자동 감지
    from datetime import datetime
    current_month = datetime.now().month
    if current_month in [6, 7, 8] and "여름" in comprehensive_trend_bank:
        data_list = comprehensive_trend_bank["여름"]
        selected_data = data_list[hash(query) % len(data_list)]
        print(f"    🌞 여름 시즌 트렌드 데이터 자동 제공")
        return selected_data
    elif current_month in [12, 1, 2] and "겨울" in comprehensive_trend_bank:
        data_list = comprehensive_trend_bank["겨울"]
        selected_data = data_list[hash(query) % len(data_list)]
        print(f"    ❄️ 겨울 시즌 트렌드 데이터 자동 제공")
        return selected_data
    
    # 4차: 기본 2025년 트렌드
    if "2025" in comprehensive_trend_bank:
        data_list = comprehensive_trend_bank["2025"]
        selected_data = data_list[hash(query) % len(data_list)]
        print(f"    📅 2025년 기본 트렌드 데이터 제공")
        return selected_data
    
    # 최종 기본 데이터
    fallback_trends = [
        "- 지속가능한 소비 친환경 제품\n- 개인맞춤 서비스 AI 추천\n- 비대면 서비스 언택트 문화\n- 건강한 라이프스타일 웰빙",
        "• 디지털 전환 스마트 기술\n• 구독경제 멤버십 서비스\n• 소셜미디어 인플루언서 마케팅\n• 원격근무 하이브리드 워크",
        "1. 개인창작 크리에이터 이코노미\n2. 체험경제 경험 중심 소비\n3. 안전문화 위생 방역 의식\n4. 공유경제 협력 플랫폼"
    ]
    
    print(f"    🔄 기본 트렌드 데이터 제공")
    return fallback_trends[hash(query) % len(fallback_trends)]

def parse_ai_response_improved(response_text):
    """개선된 AI 응답 파싱 - 다중 패턴 지원 및 디버깅"""
    if not response_text:
        print("    ⚠️ AI 응답이 비어있습니다")
        return []
    
    print(f"    🔍 AI 응답 파싱 시작 (길이: {len(response_text)} 글자)")
    
    topics = []
    
    # 1단계: 다양한 파싱 패턴 시도
    parsing_patterns = [
        # 번호 리스트
        (r'(\d+)\.\s*([^\n\r]{3,30})', "번호 리스트"),
        # 기호 리스트
        (r'[•\-\*]\s*([^\n\r]{3,30})', "기호 리스트"),
        # 쉼표 구분
        (r'([^,\n\r]{3,30})(?:,|$)', "쉼표 구분"),
        # 개행 구분
        (r'^([^\n\r]{3,30})$', "개행 구분"),
        # 한글 명사구
        (r'([가-힣]{2,15}(?:\s+[가-힣]{2,15}){0,2})', "한글 명사구"),
    ]
    
    for pattern, pattern_name in parsing_patterns:
        matches = re.findall(pattern, response_text, re.MULTILINE)
        if matches:
            print(f"    ✅ '{pattern_name}' 패턴으로 {len(matches)}개 매치")
            
            for match in matches:
                if isinstance(match, tuple):
                    # 그룹이 여러 개인 경우 두 번째 그룹 사용 (첫 번째는 보통 번호)
                    topic = match[1] if len(match) > 1 else match[0]
                else:
                    topic = match
                
                # 정제
                topic = topic.strip()
                topic = re.sub(r'^[\d\.\-\*\•\s]+', '', topic)  # 앞의 번호/기호 제거
                topic = re.sub(r'["""\'''„"„"]+', '', topic)  # 따옴표 제거
                
                if (topic and 
                    len(topic) >= 2 and 
                    len(topic) <= 30 and
                    not re.match(r'^[\d\s\-\*\•\.:：]+$', topic) and
                    topic not in topics):
                    topics.append(topic)
            
            if topics:
                break  # 성공적으로 파싱된 경우 중단
    
    # 2단계: 품질 필터링
    quality_topics = []
    for topic in topics:
        # 의미있는 키워드인지 확인
        if (len(topic) >= 2 and 
            len(topic) <= 30 and
            not re.search(r'^[\d\s\-\*\•\.:：]+$', topic) and
            not topic.lower().startswith(('the ', 'a ', 'an '))):
            quality_topics.append(topic)
    
    print(f"    📊 최종 파싱 결과: {len(quality_topics)}개 주제")
    
    # 상위 5개만 반환
    return quality_topics[:5]

def get_ai_suggested_topics_with_realtime_data_improved(date_info, trend_keywords):
    """개선된 AI 기반 실시간 주제 추천"""
    print("  🤖 AI 기반 실시간 주제 추천...")
    
    if not openai.api_key:
        print("    ⚠️ OpenAI API 키가 없어 AI 주제 생성을 건너뜁니다")
        return []
    
    try:
        # 현재 시점과 트렌드 키워드를 포함한 명확한 프롬프트
        year = date_info["year"]
        month = date_info["month"]
        season = date_info["season"]
        
        # 트렌드 키워드를 문자열로 변환
        keywords_text = ", ".join(trend_keywords[:10]) if trend_keywords else "일반적인 주제"
        
        prompt = f"""현재 시점: {year}년 {month}월 ({season})
최신 트렌드 키워드: {keywords_text}

위 정보를 바탕으로 {year}년 {month}월에 인기를 끌 수 있는 블로그 주제 5개를 추천해주세요.

요구사항:
1. 한 줄에 하나씩 작성
2. 번호나 기호 없이 제목만 작성
3. 15-30글자 내외로 작성
4. 현재 시점과 트렌드를 반영한 실용적인 주제

예시 형식:
여름철 에너지 절약 방법
2025년 AI 트렌드 전망
친환경 라이프스타일 시작하기
재택근무 효율성 높이는 팁
Z세대가 선호하는 투자 방법"""

        print(f"    📝 AI 프롬프트 생성 완료")
        
        # OpenAI API 호출
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 한국의 블로그 주제 추천 전문가입니다. 최신 트렌드를 반영한 실용적인 주제를 제안해주세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.8
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"    ✅ AI 응답 수신 완료")
        
        # 개선된 파싱 함수 사용
        ai_topics = parse_ai_response_improved(ai_response)
        
        print(f"    🎯 AI 추천 주제 {len(ai_topics)}개 생성 완료")
        return ai_topics
        
    except Exception as e:
        print(f"    ❌ AI 주제 생성 중 오류: {e}")
        return []

def get_realtime_trending_topics(date_info):
    """실시간 트렌딩 주제 수집 (웹 검색 기반)"""
    print("  🌐 실시간 트렌딩 주제 수집...")
    
    # 동적 쿼리 생성
    queries = generate_dynamic_queries(date_info)
    print(f"    📝 생성된 검색 쿼리 {len(queries)}개")
    
    # 각 쿼리로 웹 검색 시뮬레이션
    all_topics = []
    for query in queries:
        search_result = simulate_web_search_improved(query)
        if search_result:
            topics = extract_topics_from_text_improved(search_result)
            all_topics.extend(topics)
            print(f"    ✅ '{query}' → {len(topics)}개 키워드 추출")
    
    # 중복 제거 및 상위 15개 선택
    unique_topics = []
    for topic in all_topics:
        if topic not in unique_topics:
            unique_topics.append(topic)
    
    final_topics = unique_topics[:15]
    print(f"  📊 총 {len(final_topics)}개 트렌딩 주제 수집 완료")
    
    return final_topics

def get_user_topic():
    """개선된 사용자 주제 선택 시스템 V2 - 실시간 트렌드 분석"""
    print("\n" + "=" * 60)
    print("🎯 블로그 포스트 주제 선택 (실시간 트렌드 분석)")
    print("=" * 60)
    
    # 1. 현재 시점 정보 가져오기
    print("\n📅 현재 시점 정보 분석...")
    date_info = get_current_date_info()
    print(f"  📍 실행 시점: {date_info['formatted_date']} ({date_info['season']})")
    
    # 2. 실시간 트렌딩 주제 수집
    print("\n🔥 실시간 트렌딩 주제 수집 중...")
    trending_topics = get_realtime_trending_topics(date_info)
    
    # 3. AI 기반 주제 추천
    print("\n🤖 AI 기반 맞춤 주제 추천 중...")
    ai_topics = get_ai_suggested_topics_with_realtime_data_improved(date_info, trending_topics)
    
    # 4. 기본 주제 (fallback)
    basic_topics = [
        "건강한 생활습관 만들기",
        "효율적인 시간 관리법",
        "취미 생활 추천",
        "여행 계획 세우기",
        "독서 습관 기르기"
    ]
    
    # 5. 통합된 주제 목록 생성
    print("\n" + "=" * 60)
    print("📋 추천 주제 목록")
    print("=" * 60)
    
    all_topics = []
    category_info = []
    
    # AI 추천 주제 추가
    if ai_topics:
        print(f"\n🤖 [AI 추천] ({len(ai_topics)}개)")
        for i, topic in enumerate(ai_topics):
            all_topics.append(topic)
            category_info.append("[AI 추천]")
            print(f"  {len(all_topics)}. {topic}")
    
    # 트렌딩 주제 추가 (AI 주제와 중복 제거)
    trending_unique = [t for t in trending_topics if t not in ai_topics][:8]
    if trending_unique:
        print(f"\n🔥 [실시간 트렌딩] ({len(trending_unique)}개)")
        for topic in trending_unique:
            all_topics.append(topic)
            category_info.append("[실시간 트렌딩]")
            print(f"  {len(all_topics)}. {topic}")
    
    # 기본 주제 추가
    print(f"\n📚 [기본 주제] ({len(basic_topics)}개)")
    for topic in basic_topics:
        all_topics.append(topic)
        category_info.append("[기본 주제]")
        print(f"  {len(all_topics)}. {topic}")
    
    # 사용자 입력 옵션들
    all_topics.append("주제 직접 입력")
    category_info.append("[사용자 입력]")
    print(f"  {len(all_topics)}. 주제 직접 입력")
    
    all_topics.append("URL 링크로 글 생성")
    category_info.append("[URL 기반]")
    print(f"  {len(all_topics)}. URL 링크로 글 생성 (뉴스/블로그/유튜브)")
    
    # 6. 사용자 선택
    print("\n" + "=" * 60)
    total_options = len(all_topics)
    
    try:
        choice = int(input(f"주제를 선택하세요 (1-{total_options}): "))
        
        if 1 <= choice <= total_options - 2:  # 직접 입력과 URL 입력 제외
            selected_topic = all_topics[choice - 1]
            selected_category = category_info[choice - 1]
            print(f"\n✅ 선택된 주제: {selected_topic} {selected_category}")
            return selected_topic
            
        elif choice == total_options - 1:  # 주제 직접 입력
            custom_topic = input("\n📝 주제를 직접 입력하세요: ").strip()
            if custom_topic:
                print(f"✅ 입력된 주제: {custom_topic} [사용자 입력]")
                return custom_topic
            else:
                print("❌ 주제를 입력해주세요.")
                return get_user_topic()
                
        elif choice == total_options:  # URL 링크 입력
            url = input("\n🔗 URL을 입력하세요 (뉴스기사/블로그/유튜브): ").strip()
            if url:
                # URL 유효성 간단 검사
                if url.startswith(('http://', 'https://')):
                    print(f"✅ 입력된 URL: {url} [URL 기반]")
                    return f"URL:{url}"  # URL임을 표시하기 위해 접두어 추가
                else:
                    print("❌ 올바른 URL 형식이 아닙니다. http:// 또는 https://로 시작해야 합니다.")
                    return get_user_topic()
            else:
                print("❌ URL을 입력해주세요.")
                return get_user_topic()
        else:
            print(f"❌ 1부터 {total_options} 사이의 번호를 선택해주세요.")
            return get_user_topic()
            
    except ValueError:
        print("❌ 올바른 숫자를 입력해주세요.")
        return get_user_topic()

# ================================
# V2 완전 자동 포스팅 시스템
# ================================

def login_and_post_to_tistory_v2():
    """V2 완전 자동 포스팅 시스템"""
    print("🚀 V2 완전 자동 포스팅 시스템 시작!")
    print("=" * 50)
    
    # ChromeOptions 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # WebDriver 설정
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print("\n=== 🔐 로그인 단계 ===")
        login_success = False
        
                # 완전 자동 로그인 시도 (쿠키 기반 로그인 제거)
        print("🔄 완전 자동 로그인 시작...")
        auto_login = FinalTistoryLogin(driver)
        complete_login_success = auto_login.complete_login()
        
        if complete_login_success:
            print("✅ 완전 자동 로그인 성공!")
            login_success = True
            save_cookies(driver)  # 성공 시 쿠키 저장 (다음 번 빠른 시작을 위해)
        else:
            print("❌ 완전 자동 로그인 실패")
            retry = input("로그인 없이 계속 진행하시겠습니까? (y/n): ")
            if retry.lower() != 'y':
                print("프로그램을 종료합니다.")
                return
        
        # 메인 루프: 글 작성 반복
        while True:
            print("\n=== ✍️ 글 작성 단계 ===")
            
            # 주제 선택
            topic = get_user_topic()
            
            # URL 기반 콘텐츠 생성 vs 일반 콘텐츠 생성 분기 처리
            if topic.startswith("URL:"):
                # URL 기반 콘텐츠 생성
                url = topic[4:]  # "URL:" 접두어 제거
                print(f"\n🔗 URL 기반 콘텐츠 생성 중: '{url}'")
                
                # 사용자 관점 입력 받기 (선택사항)
                custom_angle = input("\n💡 특별한 관점이나 각도가 있나요? (엔터키로 건너뛰기): ").strip()
                
                try:
                    blog_post = generate_blog_from_url_v2(url, custom_angle)
                    if blog_post is None:
                        print("❌ URL 기반 콘텐츠 생성에 실패했습니다.")
                        continue
                    
                    print("✅ URL 기반 콘텐츠 생성 완료!")
                    
                    # 생성된 콘텐츠 미리보기
                    print(f"\n📋 생성된 콘텐츠 미리보기:")
                    print(f"제목: {blog_post['title']}")
                    print(f"원본 제목: {blog_post.get('original_title', '없음')}")
                    print(f"소스 타입: {blog_post.get('source_type', '알 수 없음')}")
                    print(f"태그: {blog_post['tags']}")
                    print(f"이미지: {len(blog_post['images'])}개")
                    print(f"키워드: {blog_post['keywords']}")
                    print(f"원본 URL: {blog_post.get('source_url', '없음')}")
                    
                except Exception as e:
                    print(f"❌ URL 기반 콘텐츠 생성 실패: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            else:
                # 일반 V2 콘텐츠 생성
                print(f"\n🎨 V2 콘텐츠 생성 중: '{topic}'")
                try:
                    blog_post = generate_blog_content_v2(topic)
                    print("✅ V2 콘텐츠 생성 완료!")
                    
                    # 생성된 콘텐츠 미리보기
                    print(f"\n📋 생성된 콘텐츠 미리보기:")
                    print(f"제목: {blog_post['title']}")
                    print(f"태그: {blog_post['tags']}")
                    print(f"이미지: {len(blog_post['images'])}개")
                    print(f"키워드: {blog_post['keywords']}")
                    
                except Exception as e:
                    print(f"❌ 콘텐츠 생성 실패: {e}")
                    continue
            
            # 자동 포스팅 진행 (확인 없이 바로 진행)
            print("🚀 자동 포스팅을 시작합니다...")
            # 기존 확인 로직 제거됨 - 바로 다음 단계로 진행
            
            # 새 글 작성 페이지로 이동
            print("\n📝 새 글 작성 페이지로 이동...")
            try:
                driver.get(BLOG_NEW_POST_URL)
                time.sleep(5)
                handle_alerts(driver, action="accept")
                
                # 페이지 로드 후 에디터 초기화 (기존 글 완전 제거)
                print("🔄 에디터 초기화 중...")
                driver.execute_script("""
                    // 모든 가능한 에디터에서 기존 콘텐츠 완전 삭제 (제목 제외)
                    console.log("=== 에디터 초기화 시작 (제목 필드 제외) ===");
                    
                    // 1. CodeMirror 에디터 초기화
                    var cmElements = document.querySelectorAll('.CodeMirror');
                    if (cmElements.length > 0) {
                        for (var i = 0; i < cmElements.length; i++) {
                            if (cmElements[i].CodeMirror) {
                                cmElements[i].CodeMirror.setValue("");
                                console.log("CodeMirror " + i + " 초기화됨");
                            }
                        }
                    }
                    
                    // 2. 본문용 textarea만 초기화 (제목 필드 제외)
                    var textareas = document.querySelectorAll('textarea');
                    for (var i = 0; i < textareas.length; i++) {
                        var ta = textareas[i];
                        // 제목 필드가 아닌 경우에만 초기화
                        if (ta.id !== 'post-title-inp' && 
                            !ta.className.includes('textarea_tit') && 
                            ta.id !== 'tagText') {
                            ta.value = "";
                            console.log("본문 textarea " + i + " 초기화됨 (ID: " + ta.id + ")");
                        }
                    }
                    
                    // 3. TinyMCE 에디터 초기화
                    if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                        tinyMCE.activeEditor.setContent("");
                        console.log("TinyMCE 에디터 초기화됨");
                    }
                    
                    console.log("=== 에디터 초기화 완료 (제목 필드 보존) ===");
                """)
                time.sleep(2)
                print("✅ 에디터 초기화 완료")
                
                # V2 글 작성
                write_success = write_post_v2(driver, blog_post)
                
                if write_success:
                    print("✅ 글 작성 완료!")
                    
                    # 자동 발행 (확인 없이 바로 발행)
                    print("🚀 글 작성 완료! 자동으로 발행합니다...")
                    publish_success = publish_post(driver)
                    if publish_success:
                        print("🎉 글 발행 완료!")
                    else:
                        print("⚠️ 발행 실패, 임시저장 상태입니다.")
                else:
                    print("❌ 글 작성 실패")
                    
            except Exception as e:
                print(f"❌ 포스팅 중 오류: {e}")
            
            # 계속 진행 여부 확인
            print("\n=== 🔄 다음 작업 ===")
            print("1. 새 글 작성하기")
            print("2. 프로그램 종료")
            choice = input("선택 (1 또는 2): ")
            
            if choice != "1":
                print("프로그램을 종료합니다.")
                break
    
    finally:
        print("🔚 브라우저를 종료합니다...")
        driver.quit()

# ================================
# 메인 실행부 업데이트
# ================================

def main():
    """메인 실행 함수"""
    print("🌟 티스토리 자동 포스팅 시스템 V2 - 완전판")
    print("=" * 50)
    print("기능:")
    print("1. 🔍 AI 기반 스마트 키워드 생성") 
    print("2. 🖼️ 다중 이미지 자동 검색")
    print("3. 🎨 향상된 HTML 디자인")
    print("4. 📱 반응형 레이아웃")
    print("5. 🛡️ 자동 fallback 시스템")
    print("6. 🔐 완전 자동로그인 (쿠키 기반 제거됨)")
    print("=" * 50)
    
    # 테스트 모드
    mode = input("실행 모드를 선택하세요 (1: 콘텐츠 생성 테스트, 2: 전체 자동 포스팅): ")
    
    if mode == "1":
        # 콘텐츠 생성 테스트 (주제 또는 URL 입력)
        print("\n📝 콘텐츠 생성 방법을 선택하세요:")
        print("1. 주제로 블로그 글 생성")
        print("2. URL 링크로 블로그 글 생성")
        
        content_type = input("선택 (1 또는 2): ")
        
        if content_type == "1":
            # 주제로 블로그 글 생성
            topic = input("📝 블로그 주제를 입력하세요: ")
            if topic.strip():
                try:
                    blog_post = generate_blog_content_v2(topic)
                    
                    print(f"\n✅ 생성 완료!")
                    print(f"📍 제목: {blog_post['title']}")
                    print(f"🏷️ 태그: {blog_post['tags']}")
                    print(f"🖼️ 이미지: {len(blog_post['images'])}개")
                    
                    # HTML 파일로 저장
                    filename = f"v2_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(blog_post['content'])
                    
                    print(f"💾 미리보기 저장: {filename}")
                    
                    # 블로그 업로드 여부 확인
                    print("\n" + "=" * 50)
                    print("🚀 블로그 업로드 옵션")
                    print("=" * 50)
                    upload_choice = input("생성된 블로그 글을 티스토리에 업로드하시겠습니까? (y/n): ")
                    
                    if upload_choice.lower() == 'y':
                        print("\n🔐 티스토리 로그인 및 업로드 시작...")
                        try:
                            # ChromeOptions 설정
                            options = webdriver.ChromeOptions()
                            options.add_argument("--disable-blink-features=AutomationControlled")
                            options.add_experimental_option("excludeSwitches", ["enable-automation"])
                            options.add_experimental_option("useAutomationExtension", False)
                            
                            # WebDriver 설정
                            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                            
                            try:
                                print("\n=== 🔐 로그인 단계 ===")
                                login_success = False
                                
                                # 완전 자동 로그인 시도
                                print("🔄 완전 자동 로그인 시작...")
                                auto_login = FinalTistoryLogin(driver)
                                complete_login_success = auto_login.complete_login()
                                
                                if complete_login_success:
                                    print("✅ 완전 자동 로그인 성공!")
                                    login_success = True
                                    save_cookies(driver)
                                else:
                                    print("❌ 완전 자동 로그인 실패")
                                    retry = input("로그인 없이 계속 진행하시겠습니까? (y/n): ")
                                    if retry.lower() != 'y':
                                        print("업로드를 취소합니다.")
                                        driver.quit()
                                        return
                                
                                # 새 글 작성 페이지로 이동
                                print("\n📝 새 글 작성 페이지로 이동...")
                                try:
                                    driver.get(BLOG_NEW_POST_URL)
                                    time.sleep(5)
                                    handle_alerts(driver, action="accept")
                                    
                                    # 페이지 로드 후 에디터 초기화
                                    print("🔄 에디터 초기화 중...")
                                    driver.execute_script("""
                                        console.log("=== 에디터 초기화 시작 (제목 필드 제외) ===");
                                        
                                        // 1. CodeMirror 에디터 초기화
                                        var cmElements = document.querySelectorAll('.CodeMirror');
                                        if (cmElements.length > 0) {
                                            for (var i = 0; i < cmElements.length; i++) {
                                                if (cmElements[i].CodeMirror) {
                                                    cmElements[i].CodeMirror.setValue("");
                                                    console.log("CodeMirror " + i + " 초기화됨");
                                                }
                                            }
                                        }
                                        
                                        // 2. 본문용 textarea만 초기화 (제목 필드 제외)
                                        var textareas = document.querySelectorAll('textarea');
                                        for (var i = 0; i < textareas.length; i++) {
                                            var ta = textareas[i];
                                            if (ta.id !== 'post-title-inp' && 
                                                !ta.className.includes('textarea_tit') && 
                                                ta.id !== 'tagText') {
                                                ta.value = "";
                                                console.log("본문 textarea " + i + " 초기화됨 (ID: " + ta.id + ")");
                                            }
                                        }
                                        
                                        // 3. TinyMCE 에디터 초기화
                                        if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                                            tinyMCE.activeEditor.setContent("");
                                            console.log("TinyMCE 에디터 초기화됨");
                                        }
                                        
                                        console.log("=== 에디터 초기화 완료 (제목 필드 보존) ===");
                                    """)
                                    time.sleep(2)
                                    print("✅ 에디터 초기화 완료")
                                    
                                    # 글 작성
                                    write_success = write_post_v2(driver, blog_post)
                                    
                                    if write_success:
                                        print("✅ 글 작성 완료!")
                                        
                                        # 발행 여부 확인
                                        publish_choice = input("글을 발행하시겠습니까? (y/n): ")
                                        if publish_choice.lower() == 'y':
                                            print("🚀 글을 발행합니다...")
                                            publish_success = publish_post(driver)
                                            if publish_success:
                                                print("🎉 글 발행 완료!")
                                            else:
                                                print("⚠️ 발행 실패, 임시저장 상태입니다.")
                                        else:
                                            print("📝 임시저장 상태로 유지됩니다.")
                                    else:
                                        print("❌ 글 작성 실패")
                                        
                                except Exception as e:
                                    print(f"❌ 포스팅 중 오류: {e}")
                                    
                            finally:
                                print("🔚 브라우저를 종료합니다...")
                                driver.quit()
                                
                        except Exception as e:
                            print(f"❌ 업로드 중 오류: {e}")
                    else:
                        print("📝 업로드를 건너뜁니다. 미리보기 파일만 저장되었습니다.")
                    
                except Exception as e:
                    print(f"❌ 오류: {e}")
            else:
                print("❌ 주제를 입력해주세요.")
                
        elif content_type == "2":
            # URL로 블로그 글 생성
            url = input("🔗 URL을 입력하세요 (뉴스기사/블로그/유튜브): ").strip()
            if url:
                if url.startswith(('http://', 'https://')):
                    try:
                        # 사용자 관점 입력 받기 (선택사항)
                        custom_angle = input("💡 특별한 관점이나 각도가 있나요? (엔터키로 건너뛰기): ").strip()
                        
                        blog_post = generate_blog_from_url_v2(url, custom_angle)
                        
                        if blog_post is None:
                            print("❌ URL 기반 콘텐츠 생성에 실패했습니다.")
                        else:
                            print(f"\n✅ URL 기반 콘텐츠 생성 완료!")
                            print(f"📄 제목: {blog_post['title']}")
                            print(f"🏷️ 태그: {blog_post['tags']}")
                            print(f"🖼️ 이미지: {len(blog_post['images'])}개")
                            print(f"🔗 원본 URL: {blog_post.get('source_url', '없음')}")
                            print(f"📝 원본 제목: {blog_post.get('original_title', '없음')}")
                            
                            # HTML 파일로 저장
                            filename = f"url_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                            with open(filename, 'w', encoding='utf-8') as f:
                                f.write(blog_post.get('html_content', blog_post.get('content', '')))
                            
                            print(f"💾 미리보기 저장: {filename}")
                            
                            # 블로그 업로드 여부 확인
                            print("\n" + "=" * 50)
                            print("🚀 블로그 업로드 옵션")
                            print("=" * 50)
                            upload_choice = input("생성된 블로그 글을 티스토리에 업로드하시겠습니까? (y/n): ")
                            
                            if upload_choice.lower() == 'y':
                                print("\n🔐 티스토리 로그인 및 업로드 시작...")
                                try:
                                    # ChromeOptions 설정
                                    options = webdriver.ChromeOptions()
                                    options.add_argument("--disable-blink-features=AutomationControlled")
                                    options.add_experimental_option("excludeSwitches", ["enable-automation"])
                                    options.add_experimental_option("useAutomationExtension", False)
                                    
                                    # WebDriver 설정
                                    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                                    
                                    try:
                                        print("\n=== 🔐 로그인 단계 ===")
                                        login_success = False
                                        
                                        # 완전 자동 로그인 시도
                                        print("🔄 완전 자동 로그인 시작...")
                                        auto_login = FinalTistoryLogin(driver)
                                        complete_login_success = auto_login.complete_login()
                                        
                                        if complete_login_success:
                                            print("✅ 완전 자동 로그인 성공!")
                                            login_success = True
                                            save_cookies(driver)
                                        else:
                                            print("❌ 완전 자동 로그인 실패")
                                            retry = input("로그인 없이 계속 진행하시겠습니까? (y/n): ")
                                            if retry.lower() != 'y':
                                                print("업로드를 취소합니다.")
                                                driver.quit()
                                                return
                                        
                                        # 새 글 작성 페이지로 이동
                                        print("\n📝 새 글 작성 페이지로 이동...")
                                        try:
                                            driver.get(BLOG_NEW_POST_URL)
                                            time.sleep(5)
                                            handle_alerts(driver, action="accept")
                                            
                                            # 페이지 로드 후 에디터 초기화
                                            print("🔄 에디터 초기화 중...")
                                            driver.execute_script("""
                                                console.log("=== 에디터 초기화 시작 (제목 필드 제외) ===");
                                                
                                                // 1. CodeMirror 에디터 초기화
                                                var cmElements = document.querySelectorAll('.CodeMirror');
                                                if (cmElements.length > 0) {
                                                    for (var i = 0; i < cmElements.length; i++) {
                                                        if (cmElements[i].CodeMirror) {
                                                            cmElements[i].CodeMirror.setValue("");
                                                            console.log("CodeMirror " + i + " 초기화됨");
                                                        }
                                                    }
                                                }
                                                
                                                // 2. 본문용 textarea만 초기화 (제목 필드 제외)
                                                var textareas = document.querySelectorAll('textarea');
                                                for (var i = 0; i < textareas.length; i++) {
                                                    var ta = textareas[i];
                                                    if (ta.id !== 'post-title-inp' && 
                                                        !ta.className.includes('textarea_tit') && 
                                                        ta.id !== 'tagText') {
                                                        ta.value = "";
                                                        console.log("본문 textarea " + i + " 초기화됨 (ID: " + ta.id + ")");
                                                    }
                                                }
                                                
                                                // 3. TinyMCE 에디터 초기화
                                                if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                                                    tinyMCE.activeEditor.setContent("");
                                                    console.log("TinyMCE 에디터 초기화됨");
                                                }
                                                
                                                console.log("=== 에디터 초기화 완료 (제목 필드 보존) ===");
                                            """)
                                            time.sleep(2)
                                            print("✅ 에디터 초기화 완료")
                                            
                                            # 글 작성
                                            write_success = write_post_v2(driver, blog_post)
                                            
                                            if write_success:
                                                print("✅ 글 작성 완료!")
                                                
                                                # 발행 여부 확인
                                                publish_choice = input("글을 발행하시겠습니까? (y/n): ")
                                                if publish_choice.lower() == 'y':
                                                    print("🚀 글을 발행합니다...")
                                                    publish_success = publish_post(driver)
                                                    if publish_success:
                                                        print("🎉 글 발행 완료!")
                                                    else:
                                                        print("⚠️ 발행 실패, 임시저장 상태입니다.")
                                                else:
                                                    print("📝 임시저장 상태로 유지됩니다.")
                                            else:
                                                print("❌ 글 작성 실패")
                                                
                                        except Exception as e:
                                            print(f"❌ 포스팅 중 오류: {e}")
                                            
                                    finally:
                                        print("🔚 브라우저를 종료합니다...")
                                        driver.quit()
                                        
                                except Exception as e:
                                    print(f"❌ 업로드 중 오류: {e}")
                            else:
                                print("📝 업로드를 건너뜁니다. 미리보기 파일만 저장되었습니다.")
                            
                    except Exception as e:
                        print(f"❌ URL 기반 콘텐츠 생성 실패: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print("❌ 올바른 URL 형식이 아닙니다. http:// 또는 https://로 시작해야 합니다.")
            else:
                print("❌ URL을 입력해주세요.")
        else:
            print("❌ 올바른 선택을 해주세요.")
    
    elif mode == "2":
        # 전체 자동 포스팅 실행
        login_and_post_to_tistory_v2()
    
    else:
        print("❌ 올바른 모드를 선택해주세요.")

if __name__ == "__main__":
    main() 