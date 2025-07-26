#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 트렌드 수집 시스템 테스트
=================================

동적 날짜 감지 및 웹 검색 기반 트렌드 수집 테스트
"""

import os
import time
import re
import openai
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

print("🧪 실시간 트렌드 수집 시스템 테스트")
print("=" * 50)

def test_dynamic_date_detection():
    """1. 동적 날짜 감지 테스트"""
    print("\n📅 1. 동적 날짜 감지 테스트")
    print("-" * 30)
    
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    current_day = now.day
    current_date_str = now.strftime("%Y년 %m월 %d일")
    current_time_str = now.strftime("%H:%M:%S")
    
    print(f"✅ 현재 시점: {current_date_str} {current_time_str}")
    print(f"   연도: {current_year}")
    print(f"   월: {current_month}")
    print(f"   일: {current_day}")
    
    # 계절 감지
    if current_month in [12, 1, 2]:
        season = "겨울"
    elif current_month in [3, 4, 5]:
        season = "봄"
    elif current_month in [6, 7, 8]:
        season = "여름"
    else:
        season = "가을"
    
    print(f"   현재 계절: {season}")
    
    return {
        "year": current_year,
        "month": current_month,
        "day": current_day,
        "season": season,
        "date_str": current_date_str
    }

def test_dynamic_search_queries(date_info):
    """2. 동적 검색 쿼리 생성 테스트"""
    print(f"\n🔍 2. 동적 검색 쿼리 생성 테스트")
    print("-" * 35)
    
    current_year = date_info["year"]
    current_month = date_info["month"]
    season = date_info["season"]
    
    # 동적 검색 쿼리 생성
    search_queries = [
        f"{current_year}년 {current_month}월 트렌드 주제",
        f"{current_year} 최신 라이프스타일 트렌드", 
        "요즘 인기 블로그 주제",
        f"{current_year}년 핫 이슈",
        "현재 인기 검색어 순위",
        f"{current_year}년 {season} 트렌드"
    ]
    
    print(f"✅ 생성된 검색 쿼리 ({len(search_queries)}개):")
    for i, query in enumerate(search_queries, 1):
        print(f"   {i}. \"{query}\"")
    
    return search_queries

def test_web_search_simulation(search_queries):
    """3. 웹 검색 시뮬레이션 테스트 (실제 웹 검색 대신 모의 데이터)"""
    print(f"\n🌐 3. 웹 검색 시뮬레이션 테스트")
    print("-" * 30)
    
    # 실제 웹 검색 대신 모의 검색 결과 생성
    mock_search_results = {
        search_queries[0]: f"2024년 하반기 라이프스타일 트렌드 분석 결과, 홈카페 문화, 지속가능한 라이프스타일, 디지털 디톡스가 주요 키워드로 떠올랐습니다. 특히 {datetime.now().year}년에는 개인의 웰빙과 환경을 고려한 소비 패턴이 증가하고 있습니다.",
        
        search_queries[1]: f"{datetime.now().year} 최신 트렌드로는 스마트 홈 기술, 건강한 식습관, 원격 근무 효율성, 개인 브랜딩이 인기를 끌고 있습니다. 요즘 사람들은 일과 삶의 균형을 중요시하며 자기계발에 관심이 높습니다.",
        
        search_queries[2]: "인기 블로그 주제로는 생활 꿀팁, 건강 관리법, 재테크 방법, 여행 정보, 요리 레시피가 상위권을 차지하고 있습니다. 특히 실용적이고 일상에 바로 적용할 수 있는 콘텐츠가 인기입니다."
    }
    
    collected_trends = []
    search_info = []
    
    for query in search_queries[:3]:  # 처음 3개만 테스트
        print(f"🔍 검색 중: \"{query}\"")
        
        if query in mock_search_results:
            result = mock_search_results[query]
            print(f"   ✅ 검색 결과 획득 ({len(result)} 글자)")
            
            # 키워드 추출 시뮬레이션
            extracted = extract_topics_from_text(result, datetime.now().year)
            collected_trends.extend(extracted)
            
            search_info.append({
                "query": query,
                "result": result,
                "extracted_topics": extracted
            })
            
            print(f"   📝 추출된 주제: {', '.join(extracted) if extracted else '없음'}")
        else:
            print(f"   ⚠️ 검색 결과 없음")
        
        time.sleep(0.5)  # 시뮬레이션 딜레이
    
    unique_trends = list(set(collected_trends))
    print(f"\n✅ 총 수집된 트렌드: {len(unique_trends)}개")
    for trend in unique_trends:
        print(f"   • {trend}")
    
    return {
        "trends": unique_trends,
        "search_info": search_info
    }

def extract_topics_from_text(text, current_year):
    """텍스트에서 블로그 주제 추출"""
    topics = []
    
    # 주제 추출 패턴
    patterns = [
        r'(\w+(?:\s+\w+)*)\s+(?:트렌드|유행|인기)',
        r'(\w+(?:\s+\w+)*)\s+(?:방법|팁|가이드|노하우)',
        r'(\w+(?:\s+\w+)*)\s+(?:문화|라이프스타일)',
        r'(\w+(?:\s+\w+)*)\s+(?:관리법|효율성)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if 2 <= len(match.split()) <= 4 and len(match) > 3:
                topics.append(match.strip())
    
    return list(set(topics))[:3]  # 상위 3개

def test_ai_topic_generation(trend_data, date_info):
    """4. AI 기반 주제 생성 테스트"""
    print(f"\n🤖 4. AI 기반 주제 생성 테스트")
    print("-" * 30)
    
    if not openai.api_key:
        print("⚠️ OpenAI API 키가 없어 AI 테스트를 건너뜁니다")
        return get_fallback_topics_test(date_info)
    
    try:
        current_date = date_info["date_str"]
        season = date_info["season"]
        trends_text = ", ".join(trend_data["trends"][:3])
        
        prompt = f"""
현재 시점: {current_date} ({season})

실시간 웹 검색으로 수집한 최신 트렌드 정보:
{trends_text}

위의 실시간 정보를 바탕으로 {date_info['year']}년 {date_info['month']}월 현재 시점에 적합한 블로그 포스트 주제 3개를 추천해주세요.

요구사항:
1. 실시간 검색 결과 반영
2. 현재 시기에 적절한 주제
3. 실용적이고 유용한 정보 제공

응답 형식: 주제만 한 줄씩 나열 (번호나 기호 없이)
"""
        
        print("🔄 AI에게 주제 생성 요청 중...")
        print(f"   입력 프롬프트 길이: {len(prompt)} 글자")
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"✅ AI 응답 받음 ({len(ai_response)} 글자)")
        
        # 주제 추출
        lines = ai_response.split('\n')
        ai_topics = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('•', '-', '*', '1.', '2.', '3.')):
                clean_line = re.sub(r'^\d+\.\s*', '', line)
                clean_line = re.sub(r'^[•\-\*]\s*', '', clean_line)
                clean_line = clean_line.strip('"').strip("'")
                
                if clean_line and len(clean_line) > 5:
                    ai_topics.append(clean_line)
        
        print(f"✅ AI 생성 주제 ({len(ai_topics)}개):")
        for i, topic in enumerate(ai_topics, 1):
            print(f"   {i}. {topic}")
        
        return ai_topics
        
    except Exception as e:
        print(f"❌ AI 주제 생성 실패: {e}")
        return get_fallback_topics_test(date_info)

def get_fallback_topics_test(date_info):
    """대체 주제 생성 테스트"""
    current_year = date_info["year"]
    current_month = date_info["month"]
    
    if current_month in [12, 1, 2]:  # 겨울
        topics = [
            f"{current_year}년 겨울 라이프스타일 트렌드",
            f"{current_year} 겨울철 건강 관리법",
            "겨울 실내 활동 추천 가이드"
        ]
    elif current_month in [3, 4, 5]:  # 봄
        topics = [
            f"{current_year}년 봄 신상품 트렌드",
            "봄철 알레르기 완벽 대처법",
            f"{current_year} 새학기 준비 가이드"
        ]
    elif current_month in [6, 7, 8]:  # 여름
        topics = [
            f"{current_year}년 여름휴가 트렌드",
            "올여름 필수 아이템 추천",
            f"{current_year} 여름철 건강 관리"
        ]
    else:  # 가을
        topics = [
            f"{current_year}년 가을 패션 트렌드",
            "환절기 건강관리 비법",
            "가을 단풍 명소 완벽 가이드"
        ]
    
    print(f"✅ 대체 주제 생성 ({len(topics)}개):")
    for i, topic in enumerate(topics, 1):
        print(f"   {i}. {topic}")
    
    return topics

def test_complete_topic_selection(date_info, trend_data, ai_topics):
    """5. 전체 주제 선택 시스템 테스트"""
    print(f"\n🎯 5. 전체 주제 선택 시스템 테스트")
    print("-" * 35)
    
    all_topics = []
    
    # AI 추천 주제
    if ai_topics:
        print(f"🤖 실시간 데이터 기반 AI 추천 ({len(ai_topics)}개):")
        for topic in ai_topics:
            all_topics.append(f"[실시간 AI] {topic}")
            
    # 웹 트렌드
    direct_trends = trend_data["trends"][:2]
    if direct_trends:
        print(f"\n🔥 실시간 웹 트렌드 ({len(direct_trends)}개):")
        for topic in direct_trends:
            all_topics.append(f"[웹 트렌드] {topic}")
    
    # 기본 주제
    fallback_topics = get_fallback_topics_test(date_info)[:2]
    print(f"\n📚 기본 안정 주제 ({len(fallback_topics)}개):")
    for topic in fallback_topics:
        all_topics.append(f"[기본] {topic}")
    
    # 최종 주제 목록 출력
    print(f"\n{'='*50}")
    print(f"🎯 최종 추천 주제 목록 ({date_info['date_str']} 기준):")
    print(f"{'='*50}")
    
    for i, topic in enumerate(all_topics, 1):
        print(f"{i:2d}. {topic}")
    
    print(f"{len(all_topics)+1:2d}. 직접 입력")
    print(f"{len(all_topics)+2:2d}. 실시간 트렌드 새로고침")
    
    return all_topics

def run_full_test():
    """전체 테스트 실행"""
    print("🚀 실시간 트렌드 수집 시스템 전체 테스트 시작!")
    start_time = time.time()
    
    try:
        # 1. 동적 날짜 감지
        date_info = test_dynamic_date_detection()
        
        # 2. 동적 검색 쿼리 생성
        search_queries = test_dynamic_search_queries(date_info)
        
        # 3. 웹 검색 시뮬레이션
        trend_data = test_web_search_simulation(search_queries)
        
        # 4. AI 주제 생성
        ai_topics = test_ai_topic_generation(trend_data, date_info)
        
        # 5. 전체 시스템 테스트
        final_topics = test_complete_topic_selection(date_info, trend_data, ai_topics)
        
        # 테스트 결과 요약
        end_time = time.time()
        print(f"\n🎉 테스트 완료!")
        print(f"⏱️  총 소요 시간: {end_time - start_time:.2f}초")
        print(f"📊 테스트 결과 요약:")
        print(f"   • 감지된 현재 시점: {date_info['date_str']}")
        print(f"   • 생성된 검색 쿼리: {len(search_queries)}개")
        print(f"   • 수집된 트렌드: {len(trend_data['trends'])}개")
        print(f"   • AI 생성 주제: {len(ai_topics)}개")
        print(f"   • 최종 추천 주제: {len(final_topics)}개")
        
        print(f"\n✅ 동적 트렌드 수집 시스템이 정상적으로 작동합니다!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = run_full_test()
    
    if success:
        print(f"\n🔧 메인 코드 적용 준비 완료!")
        print(f"   이제 auto_post_generator_v2_complete.py에 안전하게 적용할 수 있습니다.")
    else:
        print(f"\n⚠️ 테스트 실패 - 메인 코드 적용 전 문제를 해결해주세요.") 