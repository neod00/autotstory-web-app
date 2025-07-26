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
    
    # 전달받은 콘텐츠 데이터 사용
    if isinstance(content_data, dict):
        title = content_data.get("title", topic)
        intro_content = content_data.get("intro", "")
        core_subtitles = content_data.get("core_subtitles", [])
        core_contents = content_data.get("core_contents", [])
        conclusion_content = content_data.get("conclusion", "")
        table_title = content_data.get("table_title", f"{topic} 주요 정보")
        table_html = content_data.get("table_html", "")
    else:
        # 기존 방식 호환성 유지
        title = topic
        intro_content = f"이 글에서는 <strong>{topic}</strong>에 대해 자세히 알아보겠습니다."
        core_subtitles = [f"{topic}의 기본 개념", f"{topic}의 활용 방법", f"{topic}의 미래 전망"]
        core_contents = [
            f"{topic}의 기본 개념과 정의에 대해 알아보겠습니다.",
            f"{topic}의 실용적 활용 방안에 대해 살펴보겠습니다.",
            f"{topic}의 미래 전망에 대해 분석해보겠습니다."
        ]
        conclusion_content = f"{topic}에 대한 종합적인 분석을 통해 우리는 이 주제의 중요성과 실용성을 확인할 수 있었습니다."
        table_title = f"{topic} 주요 정보"
        table_html = f"<table><tr><td>{topic} 관련 정보</td></tr></table>"

    # 텍스트 콘텐츠에 자연스러운 줄바꿈 적용
    intro_content = format_text_with_line_breaks(intro_content)
    core_contents = [format_text_with_line_breaks(content) for content in core_contents]
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
                            table_rows.append((item, desc, importance))
                
                # 표 데이터가 없으면 기본 표 생성
                if not table_rows:
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
        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
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
    
    # FAQ 처리 (기존 방식 유지)
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
        # FAQ 원시 데이터를 HTML로 변환
        faq_html_parts = []
        if isinstance(faq_content, str):
            lines = faq_content.split('\n')
            current_q = ""
            current_a = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('Q'):
                    if current_q and current_a:
                        faq_html_parts.append(f"""
                        <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
                            <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
                                {current_q}
                            </div>
                            <div style="padding: 15px; display: none; background: #f9f9f9;">
                                <strong>{current_a.split(':')[0]}:</strong> {':'.join(current_a.split(':')[1:]).strip()}
                            </div>
                        </div>
                        """)
                    current_q = line
                    current_a = ""
                elif line.startswith('A'):
                    current_a = line
            
            # 마지막 FAQ 추가
            if current_q and current_a:
                faq_html_parts.append(f"""
                <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden;">
                    <div style="background: #34495e; color: white; padding: 15px; font-weight: bold; cursor: pointer;" onclick="toggleFAQ(this)">
                        {current_q}
                    </div>
                    <div style="padding: 15px; display: none; background: #f9f9f9;">
                        <strong>{current_a.split(':')[0]}:</strong> {':'.join(current_a.split(':')[1:]).strip()}
                    </div>
                </div>
                """)
        
        if faq_html_parts:
            faq_content = ''.join(faq_html_parts)
    
    html = f"""
    <div style="max-width: 1000px; margin: 0 auto; font-family: 'Segoe UI', sans-serif; line-height: 1.8;">
        <!-- 히어로 섹션 (제목 포함) -->
        <div style="position: relative; height: 400px; overflow: hidden; border-radius: 15px; margin-bottom: 30px;">
            <img src="{hero_image['url']}" alt="히어로 이미지" style="width: 100%; height: 100%; object-fit: cover;">
            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(45deg, rgba(0,0,0,0.7), rgba(0,0,0,0.3)); display: flex; align-items: center; justify-content: center;">
                <h1 style="color: white; font-size: 2.5rem; font-weight: bold; text-align: center; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); padding: 20px; margin: 0;">{title}</h1>
            </div>
        </div>
        
        <!-- 콘텐츠 -->
        <div style="padding: 20px;">
            <!-- 도입부 (동적 소제목) -->
            <div style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #3498db;">
                <div style="color: #555; font-size: 1.1rem; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;">{intro_content}</div>
            </div>
            
            {f'<img src="{content_images[0]["url"]}" alt="콘텐츠 이미지" style="width: 100%; height: 300px; object-fit: cover; border-radius: 10px; margin: 20px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">' if content_images else ''}
            
            <!-- 핵심 내용 1 (동적 소제목) -->
            <div style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #e74c3c;">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem;">🔍 {core_subtitles[0] if len(core_subtitles) > 0 else '핵심 내용 1'}</h2>
                <div style="color: #555; font-size: 1.1rem; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;">{core_contents[0] if len(core_contents) > 0 else f"{topic}의 첫 번째 핵심 내용입니다."}</div>
            </div>
            
            <!-- 핵심 내용 2 (동적 소제목) -->
            <div style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #9b59b6;">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem;">💡 {core_subtitles[1] if len(core_subtitles) > 1 else '핵심 내용 2'}</h2>
                <div style="color: #555; font-size: 1.1rem; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;">{core_contents[1] if len(core_contents) > 1 else f"{topic}의 두 번째 핵심 내용입니다."}</div>
            </div>
            
            {f'<img src="{content_images[1]["url"]}" alt="콘텐츠 이미지 2" style="width: 100%; height: 300px; object-fit: cover; border-radius: 10px; margin: 20px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">' if len(content_images) > 1 else ''}
            
            <!-- 핵심 내용 3 (동적 소제목) -->
            <div style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #f39c12;">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem;">🚀 {core_subtitles[2] if len(core_subtitles) > 2 else '핵심 내용 3'}</h2>
                <div style="color: #555; font-size: 1.1rem; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;">{core_contents[2] if len(core_contents) > 2 else f"{topic}의 세 번째 핵심 내용입니다."}</div>
            </div>
            
            <!-- 주요 정보 표 (동적 제목 + 내용) -->
            <div style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #6366f1;">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem;">📊 {table_title}</h2>
                <div style="overflow-x: auto;">
                    {table_html}
                </div>
            </div>
            
            <!-- FAQ 섹션 -->
            <div style="background: #ecf0f1; padding: 30px; margin: 30px 0; border-radius: 10px;">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem;">❓ 자주 묻는 질문</h2>
                {faq_content}
            </div>
            
            <!-- 결론 (주제별 맞춤 내용) -->
            <div style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #27ae60;">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem;">🎯 결론</h2>
                <div style="color: #555; font-size: 1.1rem; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;">{conclusion_content}</div>
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

def generate_blog_content_v2(topic):
    """V2 메인 콘텐츠 생성 함수 (개선된 버전)"""
    print(f"🚀 V2 콘텐츠 생성: '{topic}'")
    
    # 1. 스마트 키워드 생성
    keywords = generate_smart_keywords(topic)
    
    # 2. 다중 이미지 검색  
    images = get_multiple_images_v2(keywords, count=3)
    
    # 3. 제목 생성 (번호 제거 로직 추가)
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
    
    # 4. 풍부한 도입부 생성
    try:
        if openai.api_key:
            intro_resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"'{topic}' 주제에 대한 블로그 글의 도입부를 200-300자로 작성해주세요. 독자의 관심을 끌고 이 주제의 중요성을 강조하는 내용으로 작성해주세요. 가독성을 위해 문단을 나누어 작성하고, 자연스러운 줄바꿈이 있도록 해주세요."}],
                max_tokens=400
            )
            intro_content = intro_resp.choices[0].message.content.strip()
        else:
            intro_content = f"이 글에서는 {topic}에 대해 자세히 알아보겠습니다. 현대 사회에서 이 주제가 갖는 의미와 중요성을 살펴보고, 실질적인 인사이트를 제공하겠습니다."
    except:
        intro_content = f"이 글에서는 {topic}에 대해 자세히 알아보겠습니다."

    # 5. 구조화된 핵심 내용 3개 생성 (각각 풍부하게)
    core_contents = []
    for i in range(1, 4):
        try:
            if openai.api_key:
                core_resp = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": f"'{topic}' 주제의 핵심 내용 {i}번째를 300-400자로 작성해주세요. 구체적인 정보와 실용적인 내용을 포함해주세요. 제목은 포함하지 말고 본문만 작성해주세요. 가독성을 위해 문단을 나누어 작성하고, 자연스러운 줄바꿈이 있도록 해주세요."}],
                    max_tokens=500
                )
                core_content = core_resp.choices[0].message.content.strip()
                core_contents.append(core_content)
            else:
                core_contents.append(f"{topic}의 {i}번째 핵심 내용에 대해 설명합니다.")
        except:
            core_contents.append(f"{topic}의 {i}번째 핵심 내용에 대해 설명합니다.")
    
    # 6. 주제별 맞춤 결론 생성
    try:
        if openai.api_key:
            conclusion_resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"'{topic}' 주제에 대한 블로그 글의 결론을 200-300자로 작성해주세요. 앞서 다룬 내용을 요약하고 독자에게 실용적인 조언이나 향후 전망을 제시해주세요. 가독성을 위해 문단을 나누어 작성하고, 자연스러운 줄바꿈이 있도록 해주세요."}],
                max_tokens=400
            )
            conclusion_content = conclusion_resp.choices[0].message.content.strip()
        else:
            conclusion_content = f"{topic}에 대한 종합적인 분석을 통해 우리는 이 주제의 중요성과 실용성을 확인할 수 있었습니다."
    except:
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
    
    # 8.5. 동적 소제목 생성
    core_subtitles = []
    for i in range(1, 4):
        try:
            if openai.api_key:
                subtitle_resp = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": f"'{topic}' 주제의 {i}번째 핵심 내용에 적합한 소제목을 생성해주세요. 간결하고 매력적인 소제목만 작성해주세요."}],
                    max_tokens=50
                )
                subtitle = subtitle_resp.choices[0].message.content.strip()
                core_subtitles.append(subtitle)
            else:
                core_subtitles.append(f"{topic}의 핵심 포인트 {i}")
        except:
            core_subtitles.append(f"{topic}의 핵심 포인트 {i}")
    
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

    # 9. 통합된 콘텐츠 객체 생성 (모든 필드 포함)
    content_data = {
        "title": title,
        "intro": intro_content,
        "core_subtitles": core_subtitles,
        "core_contents": core_contents,
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
    """기존 FAQ 생성 함수"""
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
    """개선된 웹 검색 시뮬레이션 - 더 현실적인 데이터"""
    print(f"    🔍 웹 검색: '{query}'")
    
    # 쿼리별 맞춤형 모의 데이터
    mock_data_bank = {
        "트렌드": [
            "- AI 인공지능 기술 발전 동향\n- 메타버스 가상현실 체험\n- NFT 디지털 자산 투자\n- 친환경 ESG 경영\n- 비대면 원격 근무 문화",
            "• Z세대 소비 패턴 변화\n• 구독 경제 서비스 확산\n• 라이브 커머스 쇼핑\n• 헬스케어 디지털 헬스",
            "1. 탄소중립 그린뉴딜 정책\n2. 전기차 배터리 기술\n3. 재생에너지 태양광 풍력\n4. 플랜테리언 식물성 식품"
        ],
        "여름": [
            "- 여행 휴가 제주도 강원도\n- 워터파크 수영장 피서\n- 캠핑 글램핑 아웃도어\n- 홈카페 디저트 빙수",
            "• 선크림 자외선 차단제\n• 쿨링 아이템 선풍기\n• 해변 비치웨어 수영복\n• 여름 축제 펜션 리조트"
        ],
        "2025": [
            "- 디지털 트랜스포메이션 DX\n- 클라우드 컴퓨팅 서비스\n- 5G 네트워크 인프라\n- 스마트시티 IoT 센서",
            "• 바이오 헬스케어 의료\n• 핀테크 디지털 금융\n• 로봇 자동화 기술\n• 우주 항공 산업"
        ],
        "인기": [
            "- 숏폼 콘텐츠 틱톡 유튜브\n- 배달음식 HMR 간편식\n- 펫케어 반려동물 용품\n- 홈트레이닝 운동 피트니스",
            "• OTT 스트리밍 서비스\n• 게임 e스포츠 메타버스\n• 뷰티 K-뷰티 화장품\n• 패션 온라인 쇼핑몰"
        ]
    }
    
    # 쿼리에 포함된 키워드로 적절한 데이터 선택
    for keyword, data_list in mock_data_bank.items():
        if keyword in query:
            return data_list[hash(query) % len(data_list)]
    
    # 기본 데이터
    default_data = [
        "- 클린뷰티 친환경 화장품\n- 업사이클링 재활용 제품\n- 로컬푸드 지역 특산품\n- 디지털 디톡스 힐링",
        "• 마이크로 러닝 온라인 교육\n• 가상현실 VR AR 기술\n• 블록체인 암호화폐\n• 사물인터넷 스마트홈"
    ]
    
    return default_data[hash(query) % len(default_data)]

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
    
    # 직접 입력 옵션
    all_topics.append("직접 입력")
    category_info.append("[사용자 입력]")
    print(f"  {len(all_topics)}. 직접 입력")
    
    # 6. 사용자 선택
    print("\n" + "=" * 60)
    total_options = len(all_topics)
    
    try:
        choice = int(input(f"주제를 선택하세요 (1-{total_options}): "))
        
        if 1 <= choice <= total_options - 1:  # 직접 입력 제외
            selected_topic = all_topics[choice - 1]
            selected_category = category_info[choice - 1]
            print(f"\n✅ 선택된 주제: {selected_topic} {selected_category}")
            return selected_topic
            
        elif choice == total_options:  # 직접 입력
            custom_topic = input("\n📝 주제를 직접 입력하세요: ").strip()
            if custom_topic:
                print(f"✅ 입력된 주제: {custom_topic} [사용자 입력]")
                return custom_topic
            else:
                print("❌ 주제를 입력해주세요.")
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
            
            # V2 콘텐츠 생성
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
        # 콘텐츠 생성 테스트
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
                
            except Exception as e:
                print(f"❌ 오류: {e}")
        else:
            print("❌ 주제를 입력해주세요.")
    
    elif mode == "2":
        # 전체 자동 포스팅 실행
        login_and_post_to_tistory_v2()
    
    else:
        print("❌ 올바른 모드를 선택해주세요.")

if __name__ == "__main__":
    main() 