#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 블로그 글 생성 시스템
=========================

test_simple_specialized.py와 blog_improvements_test.py를 연동하여
전문 분야 주제로 완전한 블로그 글을 생성합니다.
"""

import os
import sys
import time
import re
import openai
from datetime import datetime
from dotenv import load_dotenv

# 기존 모듈들 임포트
sys.path.append('.')
from blog_improvements_test import BlogImprovementTester

# 환경 변수 로드
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class SpecializedBlogGenerator:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.blog_tester = BlogImprovementTester(
            openai_key=self.openai_key,
            unsplash_key="uQgwi8yVjCIJmD0NNU2_2oBIHUMI8UPn2B6blxwWbvQ"
        )
    
    def get_specialized_topic(self):
        """전문 분야 주제 생성 (test_simple_specialized.py 기반)"""
        print("🎯 전문 분야 주제 생성")
        print("=" * 40)
        
        # 날짜 정보 생성
        now = datetime.now()
        date_str = now.strftime("%Y년 %m월 %d일")
        
        if now.month in [12, 1, 2]:
            season = "겨울"
        elif now.month in [3, 4, 5]:
            season = "봄"
        elif now.month in [6, 7, 8]:
            season = "여름"
        else:
            season = "가을"
        
        date_info = {
            "year": now.year, 
            "month": now.month, 
            "season": season, 
            "date_str": date_str
        }
        
        print(f"📅 현재 시점: {date_str} ({season})")
        
        if not self.openai_key:
            print("⚠️ OpenAI API 키가 없어 대체 주제를 사용합니다")
            return "2025년 상반기 미국주식 시장 분석과 투자 전략"
        
        try:
            prompt = f"""
현재: {date_str} ({season})

다음 전문 분야에 특화된 블로그 포스트 주제 3개를 만들어주세요:
분야: 기후변화, 재테크, 정보기술, 미국주식, 과학기술, 지속가능성, 환경정책, 국내주식, 한국/글로벌 경제

조건:
- 전문적이고 심층적인 분석 주제
- 투자자/전문가들이 관심 있을 내용
- "분석", "전망", "전략", "동향" 등의 전문 용어 포함
- {date_info["year"]}년 {date_info["month"]}월 시점성 반영

출력 형식:
1. 주제명
2. 주제명
3. 주제명
"""
            
            print("🔄 AI에게 전문 주제 생성 요청 중...")
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # 주제 추출
            topics = []
            for line in ai_response.split("\n"):
                line = line.strip()
                match = re.match(r"^\d+\.\s*(.+)", line)
                if match:
                    topic = match.group(1).strip()
                    if len(topic) > 10:
                        topics.append(topic)
            
            if topics:
                print(f"✅ 생성된 전문 주제 ({len(topics)}개):")
                for i, topic in enumerate(topics, 1):
                    print(f"   {i}. {topic}")
                
                # 첫 번째 주제 선택 및 정제
                selected_topic = topics[0]
                
                # 제목 정제: 번호, 별표, 불필요한 문자 제거
                clean_topic = selected_topic
                clean_topic = re.sub(r'^\d+\.\s*\*{0,2}', '', clean_topic)  # 번호와 별표 제거
                clean_topic = re.sub(r'\*{2,}', '', clean_topic)  # 연속된 별표 제거
                clean_topic = clean_topic.strip()  # 앞뒤 공백 제거
                
                print(f"\n🎯 선택된 주제: {clean_topic}")
                return clean_topic
            else:
                return "2025년 상반기 미국주식 시장 분석과 투자 전략"
                
        except Exception as e:
            print(f"❌ AI 주제 생성 실패: {e}")
            return "2025년 상반기 미국주식 시장 분석과 투자 전략"
    
    def generate_complete_blog_post(self, topic):
        """완전한 블로그 글 생성"""
        print(f"\n🚀 완전한 블로그 글 생성 시작")
        print("=" * 50)
        print(f"주제: {topic}")
        print("=" * 50)
        
        start_time = time.time()
        
        # 1. 스마트 키워드 생성
        print("\n1️⃣ 스마트 키워드 생성...")
        keyword_result = self.blog_tester.test_smart_keyword_generation(topic)
        
        # 2. 다중 이미지 검색
        print(f"\n2️⃣ 다중 이미지 검색...")
        keywords = keyword_result['final_keywords']
        images = self.blog_tester.test_multi_image_search(keywords, count=3)
        
        # 3. 카테고리 최적화 콘텐츠 생성
        print(f"\n3️⃣ 카테고리 최적화 콘텐츠 생성...")
        content_result = self.blog_tester.test_category_optimized_system(topic)
        
        # 4. HTML 구조 생성
        print(f"\n4️⃣ 향상된 HTML 구조 생성...")
        if content_result and 'category_info' in content_result:
            html_content = self.blog_tester.generate_category_html_structure(
                topic, 
                images, 
                content_result['content_data'], 
                content_result['category_info']
            )
        else:
            # 폴백 처리
            html_content = self.generate_fallback_html(topic, images)
        
        end_time = time.time()
        
        # 5. 결과 요약
        print(f"\n✅ 블로그 글 생성 완료!")
        print(f"⏱️  총 소요 시간: {end_time - start_time:.2f}초")
        print(f"📊 생성 결과:")
        print(f"   • 키워드: {len(keywords)}개")
        print(f"   • 이미지: {len(images)}개")
        print(f"   • HTML 길이: {len(html_content):,} 글자")
        
        return {
            'topic': topic,
            'keywords': keywords,
            'images': images,
            'html_content': html_content,
            'generation_time': end_time - start_time
        }
    
    def generate_fallback_html(self, topic, images):
        """폴백 HTML 생성"""
        hero_image = images[0] if images else {"url": "https://picsum.photos/800/400", "description": "기본 이미지"}
        
        return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .hero {{ position: relative; height: 400px; overflow: hidden; border-radius: 15px; margin-bottom: 30px; }}
        .hero img {{ width: 100%; height: 100%; object-fit: cover; }}
        .hero-title {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                       color: white; font-size: 2rem; font-weight: bold; text-align: center; 
                       text-shadow: 2px 2px 4px rgba(0,0,0,0.7); padding: 20px; }}
        .content {{ background: #f8f9fa; padding: 25px; margin: 20px 0; border-radius: 10px; 
                   border-left: 4px solid #007bff; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <img src="{hero_image['url']}" alt="히어로 이미지">
            <div class="hero-title">{topic}</div>
        </div>
        
        <div class="content">
            <h2>📊 주요 내용</h2>
            <p>이 글에서는 <strong>{topic}</strong>에 대해 전문적이고 심층적으로 분석합니다.</p>
            <p>현재 시점의 최신 동향과 전문가적 관점에서의 인사이트를 제공하며, 
               실용적인 정보와 전략적 방향성을 제시합니다.</p>
        </div>
        
        <div class="content">
            <h2>🎯 핵심 포인트</h2>
            <ul>
                <li>전문적 분석과 데이터 기반 인사이트</li>
                <li>최신 트렌드와 시장 동향 파악</li>
                <li>실용적 활용 방안과 전략 제시</li>
            </ul>
        </div>
    </div>
</body>
</html>
        """
    
    def save_blog_post(self, blog_result):
        """블로그 글을 HTML 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"specialized_blog_{timestamp}.html"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(blog_result['html_content'])
            
            print(f"\n💾 블로그 글 저장 완료!")
            print(f"📁 파일명: {filename}")
            print(f"📍 전체 경로: {os.path.abspath(filename)}")
            
            return filename
            
        except Exception as e:
            print(f"❌ 파일 저장 실패: {e}")
            return None

def main():
    """메인 실행 함수"""
    print("🌟 통합 블로그 글 생성 시스템")
    print("=" * 60)
    print("전문 분야 주제 + 고품질 콘텐츠 + 향상된 디자인")
    print("=" * 60)
    
    try:
        # 생성기 초기화
        generator = SpecializedBlogGenerator()
        
        # 전문 분야 주제 생성
        topic = generator.get_specialized_topic()
        
        # 완전한 블로그 글 생성
        blog_result = generator.generate_complete_blog_post(topic)
        
        # HTML 파일로 저장
        filename = generator.save_blog_post(blog_result)
        
        if filename:
            print(f"\n🎉 성공적으로 전문 분야 블로그 글이 생성되었습니다!")
            print(f"🌐 브라우저에서 '{filename}' 파일을 열어 미리보기하세요!")
        
    except Exception as e:
        print(f"❌ 블로그 글 생성 중 오류: {e}")

if __name__ == "__main__":
    main() 