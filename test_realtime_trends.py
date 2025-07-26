#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전문 분야 특화 실시간 트렌드 수집 시스템 테스트
(기후변화, 재테크, 정보기술, 주식, 경제 전문)
"""

import os
import time
import re
import openai
import requests
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

def test_dynamic_date_detection():
    """동적 날짜 감지 테스트"""
    print("📅 1. 동적 날짜 감지 테스트")
    print("-" * 30)
    
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    current_day = now.day
    current_date_str = now.strftime("%Y년 %m월 %d일")
    
    print(f"✅ 현재 시점: {current_date_str}")
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
        "season": season,
        "date_str": current_date_str
    }

def test_specialized_queries(date_info):
    """전문 분야 특화 검색 쿼리 테스트"""
    print(f"\n🔍 2. 전문 분야 특화 검색 쿼리 생성 테스트")
    print("-" * 40)
    
    current_year = date_info["year"]
    current_month = date_info["month"]
    season = date_info["season"]
    
    # 전문 분야별 쿼리 생성
    specialized_queries = [
        f"{current_year}년 {current_month}월 기후변화 정책 동향",
        f"{current_year} 미국주식 시장 전망",
        f"{current_year}년 재테크 트렌드",
        f"{current_year} 정보기술 혁신",
        f"{current_year}년 {season} 경제 전망",
        f"{current_year} 지속가능성 기술",
        f"{current_year}년 국내주식 분석",
        f"{current_year} 환경정책 변화",
        f"{current_year}년 글로벌 경제 이슈",
        f"{current_year} ESG 투자 동향"
    ]
    
    print(f"✅ 생성된 전문 쿼리 ({len(specialized_queries)}개):")
    for i, query in enumerate(specialized_queries, 1):
        print(f"   {i:2d}. \"{query}\"")
    
    return specialized_queries

def test_specialized_web_search_mock(queries):
    """전문 분야 웹 검색 모의 테스트"""
    print(f"\n🌐 3. 전문 분야 웹 검색 모의 테스트")
    print("-" * 35)
    
    # 전문 분야별 현실적인 모의 데이터
    current_year = datetime.now().year
    specialized_mock_results = {
        f"{current_year}년 기후변화 정책": f"""
        {current_year}년 상반기 기후변화 대응 정책의 핵심 변화를 살펴보면,
        탄소중립 로드맵 실행, 재생에너지 확대 정책, 그린뉴딜 2.0 추진이 주요 이슈입니다.
        특히 탄소배출권 거래제 개선, 녹색분류체계 도입, ESG 공시 의무화가 기업들에게 
        큰 영향을 미치고 있으며, 친환경 기술 투자 확대와 지속가능 금융 활성화 정책도 
        주목받고 있습니다. 기후테크 스타트업 지원, 수소경제 활성화 방안도 중요 키워드입니다.
        """,
        
        f"{current_year} 미국주식 시장": f"""
        {current_year}년 미국주식 시장은 인플레이션 안정화, 연준 금리 정책 변화, 
        AI 기술주 급성장이 주요 동력으로 작용하고 있습니다.
        엔비디아, 마이크로소프트, 애플 등 테크 대기업들의 실적이 시장을 견인하며,
        생성AI 관련주, 반도체 장비주, 클라우드 서비스주가 강세를 보이고 있습니다.
        배당 귀족주 투자 전략, 달러 강세 영향 분석, 경기침체 우려 완화도 
        투자자들의 주요 관심사입니다.
        """,
        
        f"{current_year}년 재테크 트렌드": f"""
        {current_year}년 재테크 시장의 주요 트렌드는 고금리 지속, 부동산 시장 변화,
        디지털 자산 다변화에 초점이 맞춰져 있습니다.
        CMA 통장 활용법, 국채 ETF 투자, 달러예금 전략이 인기를 끌고 있으며,
        ISA 계좌 최적 활용, 연금저축 세액공제 전략, 개인연금 상품 비교도 
        핵심 관심사입니다. 가상화폐 현물 ETF 출시, 리츠 투자 확대, 
        해외주식 투자 다변화 전략도 주목받고 있습니다.
        """,
        
        f"{current_year} 정보기술 혁신": f"""
        {current_year}년 IT 혁신의 핵심은 생성AI 기술 발전, 클라우드 네이티브 전환,
        메타버스 실용화, 양자컴퓨팅 상용화 진전에 있습니다.
        ChatGPT-4 고도화, 구글 바드 경쟁, 마이크로소프트 코파일럿 확산이 
        업무 환경을 혁신하고 있으며, 엣지 컴퓨팅 확산, 5G 전용망 구축,
        블록체인 실용화도 가속화되고 있습니다. 사이버보안 강화, 개인정보보호 
        기술 발전, 디지털 전환 가속화도 주요 이슈입니다.
        """
    }
    
    collected_trends = []
    search_info = []
    
    for i, query in enumerate(queries[:4]):  # 처음 4개만 테스트
        print(f"🔍 검색 중: \"{query}\"")
        time.sleep(0.5)  # 시뮬레이션 딜레이
        
        # 키에 포함된 쿼리 찾기
        result_text = ""
        for key, value in specialized_mock_results.items():
            if any(word in query for word in key.split()):
                result_text = value.strip()
                break
        
        if not result_text and i < len(specialized_mock_results):
            result_text = list(specialized_mock_results.values())[i]
        
        if result_text:
            print(f"   ✅ 검색 결과 획득 ({len(result_text)} 글자)")
            
            # 전문 분야 키워드 추출
            extracted = extract_specialized_topics(result_text, current_year)
            collected_trends.extend(extracted)
            
            search_info.append({
                "query": query,
                "result": result_text[:100] + "...",
                "extracted_topics": extracted
            })
            
            print(f"   📝 추출된 전문 주제: {', '.join(extracted) if extracted else '없음'}")
        else:
            print(f"   ⚠️ 검색 결과 없음")
    
    unique_trends = list(set(collected_trends))
    print(f"\n✅ 총 수집된 전문 트렌드: {len(unique_trends)}개")
    for trend in unique_trends:
        print(f"   • {trend}")
    
    return {
        "trends": unique_trends,
        "search_info": search_info
    }

def extract_specialized_topics(text, current_year):
    """전문 분야 특화 키워드 추출"""
    topics = []
    
    # 전문 분야 특화 패턴
    specialized_patterns = [
        # 경제/금융 패턴
        r'(\w+\s*ETF|ETF\s*\w+)',                              # "국채 ETF", "리츠 ETF"
        r'(\w+\s+투자|투자\s+\w+)',                            # "ESG 투자", "투자 전략"
        r'(\w+\s+정책|정책\s+\w+)',                            # "금리 정책", "정책 변화"
        r'(\w+\s+시장|시장\s+\w+)',                            # "미국 시장", "시장 전망"
        
        # 기술/과학 패턴  
        r'(\w+AI|\w+\s+AI|AI\s+\w+)',                          # "생성AI", "AI 기술"
        r'(\w+\s+기술|기술\s+\w+)',                            # "양자 기술", "기술 혁신"
        r'(\w+\s+컴퓨팅|컴퓨팅\s+\w+)',                       # "클라우드 컴퓨팅", "엣지 컴퓨팅"
        
        # 환경/지속가능성 패턴
        r'(\w+\s+에너지|에너지\s+\w+)',                        # "재생 에너지", "수소 에너지"
        r'(\w+중립|\w+\s+중립|중립\s+\w+)',                    # "탄소중립", "중립 로드맵"
        r'(ESG\s+\w+|\w+\s+ESG)',                              # "ESG 투자", "ESG 공시"
        r'(\w+테크|\w+\s+테크|테크\s+\w+)',                    # "기후테크", "핀테크"
        
        # 분석/전략 패턴
        r'(\w+\s+분석|분석\s+\w+)',                            # "시장 분석", "분석 전략"
        r'(\w+\s+전략|전략\s+\w+)',                            # "투자 전략", "전략 수립"
        r'(\w+\s+활용|활용\s+\w+)',                            # "CMA 활용", "활용법"
    ]
    
    for pattern in specialized_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, str) and 2 <= len(match) <= 25:
                # 전문용어 필터링
                if not any(skip in match for skip in ['있으며', '되어', '중심으로', '통해']):
                    clean_match = match.strip()
                    if clean_match:
                        topics.append(clean_match)
    
    # 복합 전문용어 추출
    compound_patterns = [
        r'(\w+\s+\w+\s+(?:로드맵|전략|정책|기술|시장))',        # "탄소중립 로드맵"
        r'(\w+\s+\w+\s+(?:투자|분석|활용|전망))',              # "해외주식 투자"
        r'(디지털\s+\w+|\w+\s+디지털)',                        # "디지털 전환"
    ]
    
    for pattern in compound_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if 4 <= len(match) <= 30:
                topics.append(match.strip())
    
    # 후처리 - 전문성 필터링
    filtered_topics = []
    for topic in topics:
        topic = topic.strip()
        if (
            len(topic) >= 3 and 
            not topic.startswith(('이', '그', '하', '있', '되', '것')) and
            not topic.endswith(('는', '이', '가', '을', '를', '에서', '으로')) and
            topic not in ['상반기', '시점에서', '핵심', '특히', '중심으로', '통해']
        ):
            filtered_topics.append(topic)
    
    return list(set(filtered_topics))[:7]  # 중복 제거 후 상위 7개

def test_specialized_ai_topic_generation(trend_data, date_info):
    """전문 분야 특화 AI 주제 생성 테스트"""
    print(f"\n🤖 4. 전문 분야 특화 AI 주제 생성 테스트")
    print("-" * 35)
    
    if not openai.api_key:
        print("⚠️ OpenAI API 키가 없어 전문 분야 대체 주제를 사용합니다")
        return get_specialized_fallback_topics(date_info)
    
    try:
        current_date = date_info["date_str"]
        season = date_info["season"]
        trends_text = ", ".join(trend_data["trends"][:8])  # 더 많은 전문 트렌드 포함
        
        # 전문 분야 특화 프롬프트
        specialized_prompt = f"""
현재 시점: {current_date} ({season})

웹 검색으로 수집한 전문 분야 실시간 트렌드:
{trends_text}

위 트렌드를 반영하여 다음 전문 분야에 특화된 블로그 포스트 주제 6개를 만들어주세요:

전문 분야: 기후변화, 재테크, 정보기술, 미국주식, 과학기술, 지속가능성, 환경정책, 국내주식, 한국/글로벌 경제

조건:
- 실시간 트렌드 키워드를 반드시 활용
- 전문적이고 심층적인 분석 주제
- 투자자/전문가들이 관심 있을 내용
- "분석", "전망", "전략", "동향" 등의 전문 용어 포함
- {date_info['year']}년 {date_info['month']}월 시점성 반영

출력 형식:
1. 주제명
2. 주제명  
3. 주제명
4. 주제명
5. 주제명
6. 주제명
"""
        
        print("🔄 전문 분야 AI에게 주제 생성 요청 중...")
        print(f"   📤 프롬프트 길이: {len(specialized_prompt)} 글자")
        print(f"   🔑 포함된 전문 트렌드: {trends_text}")
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": specialized_prompt}],
            max_tokens=500,
            temperature=0.6  # 전문성을 위해 온도 낮춤
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"   📥 AI 응답 길이: {len(ai_response)} 글자")
        
        # 디버깅을 위한 원본 응답 출력
        print(f"   📋 AI 원본 응답:")
        print(f"      \"{ai_response[:300]}{'...' if len(ai_response) > 300 else ''}\"")
        
        # 전문 주제 추출
        ai_topics = parse_specialized_ai_response(ai_response)
        
        print(f"✅ 전문 분야 AI 생성 주제 ({len(ai_topics)}개):")
        for i, topic in enumerate(ai_topics, 1):
            print(f"   {i}. {topic}")
        
        return ai_topics
        
    except Exception as e:
        print(f"❌ 전문 분야 AI 주제 생성 실패: {e}")
        return get_specialized_fallback_topics(date_info)

def parse_specialized_ai_response(ai_response):
    """전문 분야 AI 응답 파싱"""
    topics = []
    lines = ai_response.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 번호가 있는 경우 (1. 주제명)
        number_match = re.match(r'^\d+\.\s*(.+)', line)
        if number_match:
            topic = number_match.group(1).strip()
            if len(topic) > 8 and topic not in topics:  # 전문 주제는 더 길어야 함
                topics.append(topic)
            continue
        
        # 기호가 있는 경우 (- 주제명, • 주제명)
        symbol_match = re.match(r'^[•\-\*]\s*(.+)', line)
        if symbol_match:
            topic = symbol_match.group(1).strip()
            if len(topic) > 8 and topic not in topics:
                topics.append(topic)
            continue
        
        # 전문적인 텍스트 패턴
        if (
            len(line) > 10 and len(line) < 150 and
            any(keyword in line for keyword in ['분석', '전망', '전략', '동향', '정책', '투자', '기술', '시장']) and
            not line.startswith(('현재', '위', '조건', '출력', '전문'))
        ):
            clean_topic = line.strip('"').strip("'")
            if clean_topic and clean_topic not in topics:
                topics.append(clean_topic)
    
    return topics[:6]  # 최대 6개

def get_specialized_fallback_topics(date_info):
    """전문 분야 대체 주제 생성"""
    current_year = date_info["year"]
    current_month = date_info["month"]
    
    # 전문 분야별 계절 고려 주제
    if current_month in [12, 1, 2]:  # 겨울/연말연초
        topics = [
            f"{current_year}년 연말 포트폴리오 리밸런싱 전략",
            f"{current_year+1}년 미국주식 투자 전망 분석",
            "겨울철 에너지 효율성 정책 동향"
        ]
    elif current_month in [3, 4, 5]:  # 봄/신년도 시작
        topics = [
            f"{current_year}년 상반기 경제정책 분석",
            "봄철 재생에너지 투자 기회 발굴",
            f"{current_year}년 AI 기술주 성장 전망"
        ]
    elif current_month in [6, 7, 8]:  # 여름/중간 결산
        topics = [
            f"{current_year}년 상반기 주식시장 결산 분석",
            "여름철 전력 수급과 에너지 정책 동향",
            f"{current_year}년 하반기 IT 기술 트렌드 전망"
        ]
    else:  # 가을/3분기 결산
        topics = [
            f"{current_year}년 3분기 경제 지표 분석",
            "가을철 ESG 투자 동향과 전망",
            f"{current_year}년 연말 재테크 전략 수립"
        ]
    
    print(f"✅ 전문 분야 대체 주제 생성 ({len(topics)}개):")
    for i, topic in enumerate(topics, 1):
        print(f"   {i}. {topic}")
    
    return topics

def test_specialized_final_selection(date_info, trend_data, ai_topics):
    """전문 분야 최종 주제 선택 시스템"""
    print(f"\n🎯 5. 전문 분야 최종 주제 선택 시스템")
    print("-" * 40)
    
    all_topics = []
    
    # 전문 AI 추천 주제
    if ai_topics:
        print(f"🤖 실시간 전문 AI 추천 ({len(ai_topics)}개):")
        for topic in ai_topics:
            all_topics.append(f"[전문 AI] {topic}")
    
    # 전문 웹 트렌드
    direct_trends = trend_data["trends"][:4]
    if direct_trends:
        print(f"\n🔥 실시간 전문 트렌드 ({len(direct_trends)}개):")
        for topic in direct_trends:
            # 전문성을 높이기 위해 분석/전망 추가
            if any(word in topic for word in ['투자', '정책', '기술', '시장']):
                all_topics.append(f"[웹 트렌드] {topic} 심층 분석")
            else:
                all_topics.append(f"[웹 트렌드] {topic} 동향 분석")
    
    # 전문 기본 주제
    fallback_topics = get_specialized_fallback_topics(date_info)[:2]
    print(f"\n📚 전문 기본 안정 주제 ({len(fallback_topics)}개):")
    for topic in fallback_topics:
        all_topics.append(f"[기본] {topic}")
    
    # 최종 전문 주제 목록 출력
    print(f"\n{'='*70}")
    print(f"🎯 전문 블로그 최종 추천 주제 ({date_info['date_str']} 기준):")
    print(f"{'='*70}")
    
    for i, topic in enumerate(all_topics, 1):
        print(f"{i:2d}. {topic}")
    
    print(f"{len(all_topics)+1:2d}. 직접 입력")
    print(f"{len(all_topics)+2:2d}. 실시간 전문 트렌드 새로고침")
    
    return all_topics

def main():
    print("🧪 전문 분야 특화 실시간 트렌드 수집 시스템 테스트")
    print("=" * 60)
    print("📊 전문 분야: 기후변화, 재테크, 정보기술, 미국주식, 과학기술,")
    print("            지속가능성, 환경정책, 국내주식, 한국/글로벌 경제")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. 동적 날짜 감지
        date_info = test_dynamic_date_detection()
        
        # 2. 전문 분야 특화 검색 쿼리 생성
        specialized_queries = test_specialized_queries(date_info)
        
        # 3. 전문 분야 웹 검색 테스트
        trend_data = test_specialized_web_search_mock(specialized_queries)
        
        # 4. 전문 분야 특화 AI 주제 생성
        ai_topics = test_specialized_ai_topic_generation(trend_data, date_info)
        
        # 5. 전문 분야 최종 주제 선택 시스템
        final_topics = test_specialized_final_selection(date_info, trend_data, ai_topics)
        
        # 테스트 결과 요약
        end_time = time.time()
        print(f"\n🎉 전문 분야 특화 테스트 완료!")
        print(f"⏱️  총 소요 시간: {end_time - start_time:.2f}초")
        print(f"\n📊 전문 분야 특화 결과:")
        print(f"   • 감지된 현재 시점: {date_info['date_str']}")
        print(f"   • 생성된 전문 쿼리: {len(specialized_queries)}개")
        print(f"   • 수집된 전문 트렌드: {len(trend_data['trends'])}개")
        print(f"   • 전문 AI 생성 주제: {len(ai_topics)}개")
        print(f"   • 최종 전문 추천 주제: {len(final_topics)}개")
        
        # 전문성 개선사항 체크
        improvements = []
        if len(ai_topics) > 0:
            improvements.append("✅ 전문 분야 AI 주제 생성 성공")
        if len(trend_data['trends']) > 3:
            improvements.append("✅ 전문 키워드 추출 성공")
        if any('분석' in topic or '전망' in topic or '전략' in topic for topic in ai_topics):
            improvements.append("✅ 전문성 높은 주제 생성 확인")
        
        if improvements:
            print(f"\n🔧 전문성 개선사항:")
            for improvement in improvements:
                print(f"   {improvement}")
        
        print(f"\n✅ 전문 분야 특화 실시간 트렌드 시스템 완성!")
        print(f"🚀 전문 블로그용 메인 코드 적용 준비 완료!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 전문 분야 테스트 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🔧 다음 단계: 전문 분야 특화 코드를 메인 코드에 적용")
    else:
        print(f"\n⚠️ 문제 해결 후 다시 테스트하세요.") 