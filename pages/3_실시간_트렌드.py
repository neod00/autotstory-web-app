#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 트렌드 분석 페이지
====================

실시간 트렌딩 주제 수집 및 AI 기반 주제 추천 기능
"""

import streamlit as st
import sys
import os

# 상위 디렉토리의 모듈 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from trend_analyzer import TrendAnalyzer, get_trending_topics, get_ai_suggested_topics
    TREND_ANALYZER_AVAILABLE = True
except ImportError as e:
    TREND_ANALYZER_AVAILABLE = False
    st.error(f"⚠️ 트렌드 분석 모듈 로드 실패: {e}")

def main():
    st.markdown('<h1 class="main-header">🔥 실시간 트렌드 분석</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">현재 트렌딩 주제와 AI 추천 주제를 확인하세요</p>', unsafe_allow_html=True)
    
    if not TREND_ANALYZER_AVAILABLE:
        st.error("❌ 트렌드 분석 기능을 사용할 수 없습니다.")
        return
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["📊 트렌드 분석", "🤖 AI 추천", "🎯 주제 선택"])
    
    with tab1:
        st.markdown("### 📊 실시간 트렌드 분석")
        
        if st.button("🔄 트렌드 새로고침", type="primary"):
            with st.spinner("실시간 트렌드를 분석하고 있습니다..."):
                analyzer = TrendAnalyzer()
                date_info = analyzer.get_current_date_info()
                
                # 현재 시점 정보 표시
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("현재 시점", date_info['formatted_date'])
                with col2:
                    st.metric("계절", date_info['season'])
                with col3:
                    st.metric("요일", date_info['weekday'])
                
                # 트렌딩 주제 수집
                trending_topics = analyzer.get_realtime_trending_topics(date_info)
                
                if trending_topics:
                    st.success(f"✅ {len(trending_topics)}개의 트렌딩 주제를 발견했습니다!")
                    
                    # 트렌딩 주제 표시
                    st.markdown("#### 🔥 실시간 트렌딩 주제")
                    for i, topic in enumerate(trending_topics, 1):
                        st.markdown(f"**{i}.** {topic}")
                    
                    # 트렌드 차트 (간단한 버전)
                    st.markdown("#### 📈 트렌드 분포")
                    import plotly.express as px
                    import pandas as pd
                    
                    # 카테고리별 분류 (간단한 시뮬레이션)
                    categories = []
                    for topic in trending_topics:
                        if any(word in topic for word in ['패션', '스타일', '코디']):
                            categories.append('패션')
                        elif any(word in topic for word in ['건강', '운동', '다이어트']):
                            categories.append('건강')
                        elif any(word in topic for word in ['여행', '휴가', '관광']):
                            categories.append('여행')
                        elif any(word in topic for word in ['요리', '음식', '레시피']):
                            categories.append('요리')
                        else:
                            categories.append('기타')
                    
                    df = pd.DataFrame({
                        '주제': trending_topics,
                        '카테고리': categories
                    })
                    
                    fig = px.bar(df, x='카테고리', title='트렌딩 주제 카테고리별 분포')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 세션에 저장
                    st.session_state.trending_topics = trending_topics
                    st.session_state.date_info = date_info
                else:
                    st.warning("트렌딩 주제를 찾을 수 없습니다.")
    
    with tab2:
        st.markdown("### 🤖 AI 기반 주제 추천")
        
        if st.button("🤖 AI 추천 받기", type="primary"):
            if 'trending_topics' not in st.session_state:
                st.warning("먼저 트렌드 분석을 실행해주세요.")
            else:
                with st.spinner("AI가 맞춤 주제를 추천하고 있습니다..."):
                    analyzer = TrendAnalyzer()
                    date_info = st.session_state.date_info
                    trending_topics = st.session_state.trending_topics
                    
                    ai_topics = analyzer.get_ai_suggested_topics(date_info, trending_topics)
                    
                    if ai_topics:
                        st.success(f"✅ AI가 {len(ai_topics)}개의 맞춤 주제를 추천했습니다!")
                        
                        # AI 추천 주제 표시
                        st.markdown("#### 🤖 AI 추천 주제")
                        for i, topic in enumerate(ai_topics, 1):
                            st.markdown(f"**{i}.** {topic}")
                        
                        # 추천 이유 설명
                        st.markdown("#### 💡 추천 이유")
                        st.info(f"""
현재 시점({date_info['formatted_date']}, {date_info['season']}, {date_info['weekday']})에 
적합한 주제들을 AI가 분석하여 추천했습니다.

- **계절적 특성**: {date_info['season']}에 맞는 주제
- **요일 특성**: {date_info['weekday']}에 적합한 콘텐츠
- **트렌드 반영**: 현재 인기 있는 키워드 기반
- **독자 관심**: 검색 및 클릭률이 높을 것으로 예상되는 주제
                        """)
                        
                        # 세션에 저장
                        st.session_state.ai_topics = ai_topics
                    else:
                        st.warning("AI 추천 주제를 생성할 수 없습니다.")
    
    with tab3:
        st.markdown("### 🎯 주제 선택 및 블로그 생성")
        
        if st.button("📋 추천 주제 목록 보기", type="primary"):
            with st.spinner("추천 주제 목록을 생성하고 있습니다..."):
                analyzer = TrendAnalyzer()
                suggestions = analyzer.get_user_topic_suggestions()
                
                if suggestions:
                    st.session_state.topic_suggestions = suggestions
                    st.success("✅ 추천 주제 목록이 생성되었습니다!")
                    
                    # 주제 선택
                    st.markdown("#### 📝 주제 선택")
                    
                    topics = suggestions['topics']
                    categories = suggestions['categories']
                    
                    # 주제 선택 드롭다운
                    selected_index = st.selectbox(
                        "추천 주제 중에서 선택하세요:",
                        range(len(topics)),
                        format_func=lambda x: f"{x+1}. {topics[x]} {categories[x]}"
                    )
                    
                    if selected_index < len(topics):
                        selected_topic = topics[selected_index]
                        selected_category = categories[selected_index]
                        
                        st.markdown(f"**선택된 주제:** {selected_topic}")
                        st.markdown(f"**카테고리:** {selected_category}")
                        
                        # 주제별 추가 정보
                        if selected_category == "[AI 추천]":
                            st.info("🤖 AI가 현재 시점과 트렌드를 분석하여 추천한 주제입니다.")
                        elif selected_category == "[실시간 트렌딩]":
                            st.info("🔥 현재 실시간으로 인기 있는 주제입니다.")
                        elif selected_category == "[기본 주제]":
                            st.info("📚 항상 인기가 있는 기본 주제입니다.")
                        
                        # 블로그 생성으로 이동
                        if st.button("🚀 이 주제로 블로그 생성하기", type="primary"):
                            if selected_topic == "주제 직접 입력":
                                st.session_state.custom_topic_input = True
                                st.session_state.selected_topic = ""
                            elif selected_topic == "URL 링크로 글 생성":
                                st.session_state.url_based_generation = True
                                st.session_state.selected_topic = ""
                            else:
                                st.session_state.selected_topic = selected_topic
                                st.session_state.custom_topic_input = False
                                st.session_state.url_based_generation = False
                            
                            # 메인 페이지로 리다이렉트
                            st.success("✅ 주제가 선택되었습니다! 메인 페이지에서 블로그를 생성하세요.")
                            st.markdown("""
                            <script>
                                // 메인 페이지로 이동
                                window.location.href = "/";
                            </script>
                            """, unsafe_allow_html=True)
    
    # 사이드바 정보
    with st.sidebar:
        st.markdown("### 📊 트렌드 정보")
        
        if 'date_info' in st.session_state:
            date_info = st.session_state.date_info
            st.markdown(f"**현재 시점:** {date_info['formatted_date']}")
            st.markdown(f"**계절:** {date_info['season']}")
            st.markdown(f"**요일:** {date_info['weekday']}")
        
        if 'trending_topics' in st.session_state:
            st.markdown(f"**트렌딩 주제:** {len(st.session_state.trending_topics)}개")
        
        if 'ai_topics' in st.session_state:
            st.markdown(f"**AI 추천:** {len(st.session_state.ai_topics)}개")
        
        st.markdown("---")
        st.markdown("### 💡 사용 팁")
        st.markdown("""
        - 🔄 **트렌드 새로고침**: 최신 트렌드를 확인하려면 주기적으로 새로고침하세요
        - 🤖 **AI 추천**: 트렌드 분석 후 AI 추천을 받으면 더 정확한 주제를 얻을 수 있습니다
        - 🎯 **주제 선택**: 추천 주제 중에서 블로그 주제를 선택하여 바로 생성할 수 있습니다
        """)

if __name__ == "__main__":
    main() 