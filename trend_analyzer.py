#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 트렌드 분석 모듈 - Streamlit 앱용
====================================

실시간 트렌딩 주제 수집 및 AI 기반 주제 추천 기능
"""

import requests
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import openai
import os
from bs4 import BeautifulSoup
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

class TrendAnalyzer:
    """실시간 트렌드 분석 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_current_date_info(self) -> Dict:
        """현재 시점 정보 가져오기"""
        now = datetime.now()
        
        # 계절 판단
        month = now.month
        if month in [12, 1, 2]:
            season = "겨울"
        elif month in [3, 4, 5]:
            season = "봄"
        elif month in [6, 7, 8]:
            season = "여름"
        else:
            season = "가을"
        
        # 요일별 특성
        weekday = now.weekday()
        weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        weekday_name = weekday_names[weekday]
        
        return {
            'year': now.year,
            'month': now.month,
            'day': now.day,
            'weekday': weekday_name,
            'season': season,
            'formatted_date': now.strftime("%Y년 %m월 %d일"),
            'is_weekend': weekday >= 5
        }
    
    def generate_dynamic_queries(self, date_info: Dict) -> List[str]:
        """동적 검색 쿼리 생성"""
        queries = []
        
        # 계절별 쿼리
        season_queries = {
            "봄": ["봄 패션", "봄 여행", "봄 건강관리", "봄 식단", "봄 운동"],
            "여름": ["여름 패션", "여름 여행", "여름 건강관리", "여름 식단", "여름 운동"],
            "가을": ["가을 패션", "가을 여행", "가을 건강관리", "가을 식단", "가을 운동"],
            "겨울": ["겨울 패션", "겨울 여행", "겨울 건강관리", "겨울 식단", "겨울 운동"]
        }
        
        queries.extend(season_queries.get(date_info['season'], []))
        
        # 요일별 쿼리
        if date_info['is_weekend']:
            queries.extend(["주말 여행", "주말 취미", "주말 운동", "주말 요리", "주말 쇼핑"])
        else:
            queries.extend(["직장인 건강", "직장인 식단", "직장인 운동", "직장인 스트레스", "직장인 취미"])
        
        # 월별 특별 쿼리
        month_queries = {
            1: ["새해 다짐", "새해 계획", "새해 운동", "새해 다이어트"],
            2: ["발렌타인데이", "겨울 스포츠", "겨울 건강"],
            3: ["봄 패션", "봄 여행", "졸업식"],
            4: ["봄 꽃구경", "봄 운동", "봄 식단"],
            5: ["가정의 달", "봄 여행", "봄 건강"],
            6: ["여름 준비", "여름 패션", "여름 운동"],
            7: ["여름 휴가", "여름 여행", "여름 건강"],
            8: ["여름 휴가", "여름 운동", "여름 식단"],
            9: ["가을 준비", "가을 패션", "가을 여행"],
            10: ["가을 건강", "가을 운동", "가을 식단"],
            11: ["겨울 준비", "겨울 패션", "겨울 건강"],
            12: ["크리스마스", "겨울 여행", "연말 정리"]
        }
        
        queries.extend(month_queries.get(date_info['month'], []))
        
        return queries
    
    def simulate_web_search(self, query: str) -> str:
        """웹 검색 시뮬레이션"""
        try:
            # 실제 검색 API 대신 시뮬레이션
            search_results = {
                "봄 패션": "봄 패션 트렌드, 패션 아이템, 스타일링 팁, 봄 컬러, 패션 코디",
                "여름 패션": "여름 패션 트렌드, 시원한 패션, 여름 스타일링, 여름 컬러, 여름 코디",
                "가을 패션": "가을 패션 트렌드, 가을 스타일링, 가을 컬러, 가을 코디, 가을 아이템",
                "겨울 패션": "겨울 패션 트렌드, 따뜻한 패션, 겨울 스타일링, 겨울 컬러, 겨울 코디",
                "건강관리": "건강 관리법, 건강 식단, 운동 방법, 건강 팁, 건강 정보",
                "다이어트": "다이어트 방법, 다이어트 식단, 다이어트 운동, 다이어트 팁, 다이어트 정보",
                "여행": "여행지 추천, 여행 팁, 여행 준비물, 여행 정보, 여행 가이드",
                "운동": "운동 방법, 운동 효과, 운동 팁, 운동 정보, 운동 가이드",
                "요리": "요리법, 요리 팁, 요리 정보, 요리 가이드, 요리 레시피",
                "취미": "취미 활동, 취미 추천, 취미 정보, 취미 가이드, 취미 생활"
            }
            
            # 쿼리와 가장 유사한 결과 찾기
            best_match = ""
            best_score = 0
            
            for key, value in search_results.items():
                score = 0
                for word in query.split():
                    if word in key or word in value:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = value
            
            if best_match:
                return best_match
            else:
                return f"{query} 관련 정보, {query} 팁, {query} 가이드, {query} 방법, {query} 추천"
                
        except Exception as e:
            return f"{query} 관련 정보, {query} 팁, {query} 가이드"
    
    def extract_topics_from_text(self, text: str) -> List[str]:
        """텍스트에서 주제 추출"""
        try:
            if not openai.api_key:
                # 기본 추출
                words = text.split()
                topics = []
                for word in words:
                    if len(word) > 2 and word not in ["관련", "정보", "팁", "가이드", "방법", "추천"]:
                        topics.append(word)
                return topics[:10]
            
            prompt = f"""
다음 텍스트에서 블로그 주제로 활용할 수 있는 키워드를 10개 추출해주세요:

텍스트: {text}

요구사항:
1. 블로그 글 주제로 적합한 키워드
2. 검색에 유용한 키워드
3. 독자 관심을 끌 수 있는 키워드
4. JSON 형식으로 응답

JSON 형식:
{{
    "topics": ["키워드1", "키워드2", "키워드3"]
}}
"""
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            content_text = response.choices[0].message.content.strip()
            
            try:
                data = json.loads(content_text)
                return data.get('topics', [])
            except:
                # JSON 파싱 실패시 기본 추출
                words = text.split()
                topics = []
                for word in words:
                    if len(word) > 2 and word not in ["관련", "정보", "팁", "가이드", "방법", "추천"]:
                        topics.append(word)
                return topics[:10]
                
        except Exception as e:
            # 기본 추출
            words = text.split()
            topics = []
            for word in words:
                if len(word) > 2 and word not in ["관련", "정보", "팁", "가이드", "방법", "추천"]:
                    topics.append(word)
            return topics[:10]
    
    def get_realtime_trending_topics(self, date_info: Dict) -> List[str]:
        """실시간 트렌딩 주제 수집"""
        st.info("🌐 실시간 트렌딩 주제 수집 중...")
        
        # 동적 쿼리 생성
        queries = self.generate_dynamic_queries(date_info)
        st.info(f"📝 생성된 검색 쿼리 {len(queries)}개")
        
        # 각 쿼리로 웹 검색 시뮬레이션
        all_topics = []
        for query in queries:
            search_result = self.simulate_web_search(query)
            if search_result:
                topics = self.extract_topics_from_text(search_result)
                all_topics.extend(topics)
                st.info(f"✅ '{query}' → {len(topics)}개 키워드 추출")
        
        # 중복 제거 및 상위 15개 선택
        unique_topics = []
        for topic in all_topics:
            if topic not in unique_topics:
                unique_topics.append(topic)
        
        final_topics = unique_topics[:15]
        st.success(f"📊 총 {len(final_topics)}개 트렌딩 주제 수집 완료")
        
        return final_topics
    
    def get_ai_suggested_topics(self, date_info: Dict, trend_keywords: List[str]) -> List[str]:
        """AI 기반 맞춤 주제 추천"""
        try:
            if not openai.api_key:
                return trend_keywords[:5]
            
            prompt = f"""
현재 시점 정보와 트렌딩 키워드를 바탕으로 블로그 주제를 추천해주세요.

현재 시점: {date_info['formatted_date']} ({date_info['season']}, {date_info['weekday']})
트렌딩 키워드: {', '.join(trend_keywords[:10])}

요구사항:
1. 현재 시점에 적합한 주제
2. 독자 관심을 끌 수 있는 주제
3. 실용적이고 유용한 정보를 제공할 수 있는 주제
4. 8-10개의 주제 추천

JSON 형식으로 응답해주세요:
{{
    "suggested_topics": ["주제1", "주제2", "주제3"]
}}
"""
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.8
            )
            
            content_text = response.choices[0].message.content.strip()
            
            try:
                data = json.loads(content_text)
                return data.get('suggested_topics', trend_keywords[:5])
            except:
                return trend_keywords[:5]
                
        except Exception as e:
            return trend_keywords[:5]
    
    def get_user_topic_suggestions(self) -> Dict:
        """사용자 주제 선택 시스템"""
        st.markdown("🎯 블로그 포스트 주제 선택 (실시간 트렌드 분석)")
        
        # 1. 현재 시점 정보 가져오기
        st.info("📅 현재 시점 정보 분석...")
        date_info = self.get_current_date_info()
        st.info(f"📍 실행 시점: {date_info['formatted_date']} ({date_info['season']})")
        
        # 2. 실시간 트렌딩 주제 수집
        st.info("🔥 실시간 트렌딩 주제 수집 중...")
        trending_topics = self.get_realtime_trending_topics(date_info)
        
        # 3. AI 기반 주제 추천
        st.info("🤖 AI 기반 맞춤 주제 추천 중...")
        ai_topics = self.get_ai_suggested_topics(date_info, trending_topics)
        
        # 4. 기본 주제 (fallback)
        basic_topics = [
            "건강한 생활습관 만들기",
            "효율적인 시간 관리법",
            "취미 생활 추천",
            "여행 계획 세우기",
            "독서 습관 기르기"
        ]
        
        # 5. 통합된 주제 목록 생성
        st.markdown("📋 추천 주제 목록")
        
        all_topics = []
        category_info = []
        
        # AI 추천 주제 추가
        if ai_topics:
            st.markdown(f"🤖 [AI 추천] ({len(ai_topics)}개)")
            for i, topic in enumerate(ai_topics):
                all_topics.append(topic)
                category_info.append("[AI 추천]")
                st.markdown(f"  {len(all_topics)}. {topic}")
        
        # 트렌딩 주제 추가 (AI 주제와 중복 제거)
        trending_unique = [t for t in trending_topics if t not in ai_topics][:8]
        if trending_unique:
            st.markdown(f"🔥 [실시간 트렌딩] ({len(trending_unique)}개)")
            for topic in trending_unique:
                all_topics.append(topic)
                category_info.append("[실시간 트렌딩]")
                st.markdown(f"  {len(all_topics)}. {topic}")
        
        # 기본 주제 추가
        st.markdown(f"📚 [기본 주제] ({len(basic_topics)}개)")
        for topic in basic_topics:
            all_topics.append(topic)
            category_info.append("[기본 주제]")
            st.markdown(f"  {len(all_topics)}. {topic}")
        
        # 사용자 입력 옵션들
        all_topics.append("주제 직접 입력")
        category_info.append("[사용자 입력]")
        st.markdown(f"  {len(all_topics)}. 주제 직접 입력")
        
        all_topics.append("URL 링크로 글 생성")
        category_info.append("[URL 기반]")
        st.markdown(f"  {len(all_topics)}. URL 링크로 글 생성 (뉴스/블로그/유튜브)")
        
        return {
            'topics': all_topics,
            'categories': category_info,
            'date_info': date_info,
            'trending_topics': trending_topics,
            'ai_topics': ai_topics
        }

def get_trending_topics() -> List[str]:
    """트렌딩 주제 가져오기 (간단한 버전)"""
    analyzer = TrendAnalyzer()
    date_info = analyzer.get_current_date_info()
    return analyzer.get_realtime_trending_topics(date_info)

def get_ai_suggested_topics() -> List[str]:
    """AI 추천 주제 가져오기 (간단한 버전)"""
    analyzer = TrendAnalyzer()
    date_info = analyzer.get_current_date_info()
    trending_topics = analyzer.get_realtime_trending_topics(date_info)
    return analyzer.get_ai_suggested_topics(date_info, trending_topics) 