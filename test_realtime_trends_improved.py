#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 실시간 트렌드 분석 테스트
==========================

기존 test_realtime_trends.py의 문제점 개선:
1. AI 주제 생성이 0개 → 개선된 파싱 및 프롬프트
2. 키워드 추출 정확도 → 정규식 패턴 및 필터링 개선
3. 더 현실적인 모의 데이터
"""

import datetime
import time
import re
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def get_current_date_info():
    """현재 시점의 날짜 정보를 동적으로 감지"""
    now = datetime.datetime.now()
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
    print(f"    📝 응답 내용 미리보기: {response_text[:100]}...")
    
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
    for i, topic in enumerate(quality_topics[:5]):  # 처음 5개만 미리보기
        print(f"      {i+1}. {topic}")
    
    # 상위 5개만 반환
    return quality_topics[:5]

def get_ai_suggested_topics_with_realtime_data_improved(date_info, trend_keywords):
    """개선된 AI 기반 실시간 주제 추천"""
    print("  🤖 AI 기반 실시간 주제 추천...")
    
    # OpenAI API 키 확인
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
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

        print(f"    📝 AI 프롬프트 생성 완료 (길이: {len(prompt)} 글자)")
        
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
        print(f"    ✅ AI 응답 수신 완료 (길이: {len(ai_response)} 글자)")
        
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
    print(f"    📝 생성된 검색 쿼리 {len(queries)}개:")
    for i, query in enumerate(queries, 1):
        print(f"      {i}. {query}")
    
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

def get_user_topic_v2_improved():
    """개선된 사용자 주제 선택 시스템 V2"""
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
                return get_user_topic_v2_improved()
        else:
            print(f"❌ 1부터 {total_options} 사이의 번호를 선택해주세요.")
            return get_user_topic_v2_improved()
            
    except ValueError:
        print("❌ 올바른 숫자를 입력해주세요.")
        return get_user_topic_v2_improved()

def main():
    """메인 테스트 함수"""
    print("🚀 개선된 실시간 트렌드 분석 테스트 시작")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 개선된 시스템 테스트
        selected_topic = get_user_topic_v2_improved()
        
        # 결과 요약
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        print(f"✅ 최종 선택된 주제: {selected_topic}")
        print(f"⏱️ 총 소요 시간: {elapsed_time:.2f}초")
        print("🎉 개선된 실시간 트렌드 분석 테스트 완료!")
        
    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 