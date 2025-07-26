#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
티스토리 자동 포스팅 시스템 V2 - 개선된 버전
===============================================

주요 개선사항:
1. 🔍 스마트 키워드 생성 (AI 기반) - 기존: nature 고정 → 개선: 주제별 맞춤
2. 🖼️ 다중 이미지 검색 및 배치 - 기존: 1개 상단 → 개선: 여러 개 분산  
3. 🎨 향상된 HTML 구조 및 디자인 - 기존: 단조로움 → 개선: 현대적 UI/UX
4. 🛡️ 안정성 개선 (자동 fallback 시스템)
5. 🔧 OpenAI 구버전(0.28.0) 완벽 호환

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

# API 키 설정 (기존 방식 유지)
openai.api_key = os.getenv("OPENAI_API_KEY")
UNSPLASH_ACCESS_KEY = "uQgwi8yVjCIJmD0NNU2_2oBIHUMI8UPn2B6blxwWbvQ"  # 기존 하드코딩 키 유지

# 상수 정의
COOKIES_FILE = "tistory_cookies.pkl"
LOCAL_STORAGE_FILE = "tistory_local_storage.json"
BLOG_MANAGE_URL = "https://www.tistory.com/manage/"
BLOG_NEW_POST_URL = "https://tistory.com/manage/newpost/"

print("🚀 티스토리 자동 포스팅 시스템 V2 초기화 완료!")
print("   - 스마트 키워드 생성 ✅")
print("   - 다중 이미지 검색 ✅") 
print("   - 향상된 HTML 구조 ✅")
print("   - 자동 fallback 시스템 ✅")

# ================================
# V2 개선사항 1: 스마트 키워드 생성
# ================================

def generate_smart_keywords(topic):
    """AI 기반 스마트 키워드 생성 함수 (V2 핵심 기능)"""
    print(f"🔍 '{topic}' 주제에 대한 스마트 키워드 생성 중...")
    
    # 주제별 맞춤 키워드 매핑 (기본값)
    keyword_mapping = {
        "기후변화": ["climate change", "global warming", "environment"],
        "환경": ["environment", "nature", "ecology"],
        "지속가능": ["sustainable", "sustainability", "green technology"],
        "재생에너지": ["renewable energy", "solar power", "wind energy"],
        "인공지능": ["artificial intelligence", "AI technology", "machine learning"],
        "요리": ["cooking", "recipe", "food preparation"],
        "여행": ["travel", "tourism", "destination"],
        "건강": ["health", "wellness", "fitness"],
        "기술": ["technology", "innovation", "digital"],
        "집": ["home", "house", "interior design"],
        "습기": ["humidity control", "moisture management", "home dehumidifier"],
        "장마": ["rainy season", "monsoon", "weather protection"],
        "체크리스트": ["checklist", "planning", "organization"],
    }
    
    # 기본 키워드 찾기
    basic_keywords = ["modern", "lifestyle", "design"]  # 기본값
    for key, values in keyword_mapping.items():
        if key in topic:
            basic_keywords = values
            break
    
    # OpenAI API를 통한 고급 키워드 생성 (API 키가 있는 경우)
    ai_keywords = []
    if openai.api_key:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 주제에 맞는 영어 키워드를 생성하는 전문가입니다."},
                    {"role": "user", "content": f"'{topic}' 주제에 맞는 이미지 검색용 영어 키워드 3개를 생성해주세요. 각 키워드는 3-5단어 이내로 간단하게 만들어 주세요."}
                ],
                max_tokens=100
            )
            ai_response = response.choices[0].message.content
            ai_keywords = [kw.strip() for kw in ai_response.replace(',', '\n').split('\n') if kw.strip()]
            print(f"   🤖 AI 생성 키워드: {ai_keywords}")
        except Exception as e:
            print(f"   ⚠️ OpenAI API 오류 (기본 키워드 사용): {e}")
    
    # 최종 키워드 선택
    final_keywords = ai_keywords if ai_keywords else basic_keywords
    print(f"   ✅ 최종 선택 키워드: {final_keywords}")
    
    return final_keywords

def clean_keywords_for_unsplash(keywords):
    """Unsplash API에 적합하도록 키워드를 정제하는 함수 (V2 핵심 기능)"""
    cleaned_keywords = []
    
    for keyword in keywords:
        # 숫자와 점 제거 (1., 2., 3. 등)
        cleaned = re.sub(r'^\d+\.\s*', '', keyword)
        
        # 너무 긴 키워드는 핵심 단어만 추출
        if len(cleaned) > 30:
            words = cleaned.split()
            if len(words) > 3:
                cleaned = ' '.join(words[:3])
        
        # 특수문자 및 불필요한 단어 제거
        cleaned = re.sub(r'[^\w\s-]', '', cleaned)
        cleaned = cleaned.replace(' at home', '').replace(' for home', '')
        cleaned = cleaned.replace(' checklist', '').replace(' tips', '')
        
        # 앞뒤 공백 제거 및 소문자 변환
        cleaned = cleaned.strip().lower()
        
        if cleaned and len(cleaned) > 3:  # 너무 짧은 키워드 제외
            cleaned_keywords.append(cleaned)
    
    # 중복 제거
    cleaned_keywords = list(set(cleaned_keywords))
    
    # 최대 3개까지만
    return cleaned_keywords[:3] if cleaned_keywords else ["home", "lifestyle", "modern"]

# ================================
# V2 개선사항 2: 다중 이미지 검색
# ================================

def get_multiple_images(keywords, count=3):
    """다중 이미지 검색 함수 (V2 핵심 기능)"""
    print(f"🖼️ 다중 이미지 검색 시작 (키워드: {keywords}, 개수: {count})")
    
    # 키워드 정제 (Unsplash API 호환성 개선)
    cleaned_keywords = clean_keywords_for_unsplash(keywords)
    print(f"   🔧 키워드 정제: {keywords} → {cleaned_keywords}")
    
    images = []
    
    # 실제 Unsplash API 호출
    for i, keyword in enumerate(cleaned_keywords[:count]):
        try:
            url = f"https://api.unsplash.com/search/photos"
            params = {
                "query": keyword,
                "per_page": 1,
                "orientation": "landscape" if i == 0 else "all"
            }
            headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
            
            print(f"   🔍 '{keyword}' 키워드로 이미지 검색 중...")
            response = requests.get(url, params=params, headers=headers)
            
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
                    print(f"   ✅ '{keyword}' 이미지 검색 성공!")
                else:
                    print(f"   ⚠️ '{keyword}' 키워드로 이미지를 찾을 수 없습니다.")
                    # Fallback 이미지 추가
                    images.append({
                        "keyword": keyword,
                        "url": "https://picsum.photos/800/400",
                        "description": f"Fallback image for {keyword}",
                        "type": "featured" if i == 0 else "content"
                    })
            else:
                print(f"   ❌ API 오류 (상태코드: {response.status_code}): {keyword}")
                # API 오류 시 Fallback 이미지
                images.append({
                    "keyword": keyword,
                    "url": "https://picsum.photos/800/400",
                    "description": f"Error fallback image for {keyword}",
                    "type": "featured" if i == 0 else "content"
                })
        except Exception as e:
            print(f"   ⚠️ 키워드 '{keyword}' 이미지 검색 실패: {e}")
            # 예외 발생 시 Fallback 이미지
            images.append({
                "keyword": keyword,
                "url": "https://picsum.photos/800/400",
                "description": f"Exception fallback image for {keyword}",
                "type": "featured" if i == 0 else "content"
            })
    
    print(f"   ✅ 총 {len(images)}개 이미지 수집 완료")
    return images

# ================================
# V2 개선사항 3: 향상된 HTML 구조
# ================================

def generate_enhanced_html_content(topic, images, basic_content):
    """향상된 HTML 구조 생성 함수 (V2 핵심 기능)"""
    print("🎨 향상된 HTML 구조 생성 중...")
    
    # 이미지 배치 (히어로 이미지 + 콘텐츠 이미지들)
    hero_image = images[0] if images else {"url": "https://picsum.photos/800/400", "description": "기본 이미지"}
    content_images = images[1:] if len(images) > 1 else []
    
    # 향상된 HTML 구조 생성
    html_content = f"""
    <div style="max-width: 1000px; margin: 0 auto; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6;">
        <!-- 히어로 섹션 -->
        <div style="position: relative; height: 400px; overflow: hidden; border-radius: 15px; margin-bottom: 30px;">
            <img src="{hero_image['url']}" alt="히어로 이미지" style="width: 100%; height: 100%; object-fit: cover;">
            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(45deg, rgba(0,0,0,0.7), rgba(0,0,0,0.3)); display: flex; align-items: center; justify-content: center;">
                <h1 style="color: white; font-size: 2.5rem; font-weight: bold; text-align: center; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); padding: 20px;">{topic}</h1>
            </div>
        </div>
        
        <!-- 메인 콘텐츠 -->
        <div style="padding: 20px;">
            <!-- 도입부 -->
            <div style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #3498db;">
                <h2 style="color: #2c3e50; margin-bottom: 15px; font-size: 1.5rem;">📌 도입부</h2>
                <p style="color: #555; font-size: 1.1rem;">{basic_content if basic_content else f"이 글에서는 <strong>{topic}</strong>에 대해 자세히 알아보겠습니다."}</p>
            </div>
            
            {f'<img src="{content_images[0]["url"]}" alt="{content_images[0]["description"]}" style="width: 100%; height: 300px; object-fit: cover; border-radius: 10px; margin: 20px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">' if content_images else ''}
            
            <!-- 핵심 내용 -->
            <div style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #e74c3c;">
                <h2 style="color: #2c3e50; margin-bottom: 15px; font-size: 1.5rem;">💡 핵심 내용</h2>
                <p style="color: #555; font-size: 1.1rem;">현대 사회에서 <strong>{topic}</strong>가 갖는 의미와 중요성을 살펴보고, 실질적인 인사이트를 제공하겠습니다.</p>
            </div>
            
            {f'<img src="{content_images[1]["url"]}" alt="{content_images[1]["description"]}" style="width: 100%; height: 300px; object-fit: cover; border-radius: 10px; margin: 20px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">' if len(content_images) > 1 else ''}
            
            <!-- 결론부 -->
            <div style="background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #27ae60;">
                <h2 style="color: #2c3e50; margin-bottom: 15px; font-size: 1.5rem;">🎯 결론</h2>
                <p style="color: #555; font-size: 1.1rem;"><strong>{topic}</strong>에 대한 종합적인 분석을 통해 우리는 이 주제의 중요성과 실용성을 확인할 수 있었습니다. 앞으로도 지속적인 관심과 학습이 필요한 영역입니다.</p>
            </div>
        </div>
    </div>
    """
    
    print("   ✅ 향상된 HTML 구조 생성 완료")
    return html_content

# ================================
# V2 개선사항 4: 향상된 콘텐츠 생성
# ================================

def generate_blog_content_v2(topic):
    """V2 향상된 블로그 콘텐츠 생성 함수 (메인 기능)"""
    print(f"🚀 V2 블로그 콘텐츠 생성 시작: '{topic}'")
    print("=" * 60)

    # 1. 스마트 키워드 생성 (V2 신규 기능)
    smart_keywords = generate_smart_keywords(topic)
    
    # 2. 다중 이미지 검색 (V2 신규 기능)
    images = get_multiple_images(smart_keywords, count=3)

    # 3. 제목 생성
    print("📝 제목 생성 중...")
    title_prompt = f"다음 주제에 관한 블로그 포스트의 매력적인 제목을 생성해주세요: '{topic}'. 제목만 작성하고 따옴표나 기호는 포함하지 마세요."
    try:
        if openai.api_key:
            title_resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": title_prompt}],
                max_tokens=50
            )
            title = title_resp.choices[0].message.content.strip()
        else:
            title = f"{topic} - 완벽 가이드"
    except:
        title = topic

    # 4. 본문 생성
    print("📄 본문 생성 중...")
    content_prompt = f"'{topic}' 주제로 500~800자 내외의 유익한 블로그 본문을 작성하세요. HTML 태그 없이 순수 텍스트로만 작성해주세요."
    try:
        if openai.api_key:
            content_resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": content_prompt}],
                max_tokens=1000
            )
            basic_content = content_resp.choices[0].message.content.strip()
        else:
            basic_content = f"이 글에서는 {topic}에 대해 자세히 알아보겠습니다. 현대 사회에서 이 주제가 갖는 의미와 중요성을 살펴보고, 실질적인 인사이트를 제공하겠습니다."
    except:
        basic_content = f"이 글에서는 {topic}에 대해 자세히 알아보겠습니다."

    # 5. 태그 생성
    print("🏷️ 태그 생성 중...")
    try:
        if openai.api_key:
            tags_resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"'{topic}' 주제로 SEO에 효과적인 5개 태그를 쉼표로 나열해주세요."}],
                max_tokens=100
            )
            tags = tags_resp.choices[0].message.content.strip()
        else:
            tags = f"{topic}, 블로그, 정보, 가이드, 팁"
    except:
        tags = f"{topic}, 블로그, 정보, 가이드, 팁"

    # 6. V2 향상된 HTML 구조 생성
    enhanced_content = generate_enhanced_html_content(topic, images, basic_content)

    print("✅ V2 블로그 콘텐츠 생성 완료!")
    print("=" * 60)

    return {
        "title": title,
        "content": enhanced_content,
        "tags": tags,
        "images": images,
        "keywords": smart_keywords
    }

# ================================
# 기존 함수들 (V1 호환성)
# ================================

def generate_blog_content(topic):
    """기존 블로그 콘텐츠 생성 함수 (V1 호환성 유지) - V2 함수로 리디렉션"""
    return generate_blog_content_v2(topic)

def get_keyword_image_url(keyword):
    """기존 단일 이미지 검색 함수 (V1 호환성 유지)"""
    # V2에서는 스마트 키워드를 먼저 생성한 후 다중 이미지 검색 사용
    smart_keywords = generate_smart_keywords(keyword)
    images = get_multiple_images(smart_keywords, count=1)
    
    if images:
        return images[0]["url"]
    else:
        return "https://picsum.photos/800/400"  # 완전 fallback

# ================================
# 메인 실행 함수
# ================================

def main():
    """메인 실행 함수"""
    print("🌟 티스토리 자동 포스팅 시스템 V2 시작")
    print("=" * 50)
    
    # 사용자 주제 입력
    topic = input("📝 블로그 포스트 주제를 입력하세요: ")
    
    if not topic.strip():
        print("❌ 주제를 입력해주세요.")
        return
    
    # V2 콘텐츠 생성
    try:
        blog_post = generate_blog_content_v2(topic)
        
        print("\n🎉 생성 완료!")
        print(f"📍 제목: {blog_post['title']}")
        print(f"🏷️ 태그: {blog_post['tags']}")
        print(f"🖼️ 이미지: {len(blog_post['images'])}개")
        print(f"🔑 키워드: {blog_post['keywords']}")
        
        # 결과를 HTML 파일로 저장 (미리보기용)
        filename = f"blog_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(blog_post['content'])
        
        print(f"💾 미리보기 파일 저장: {filename}")
        print("\n⚡ V2 개선사항이 모두 적용되었습니다!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main() 