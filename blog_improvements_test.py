#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블로그 개선사항 테스트 프로그램
================================

기존 auto_post_generator.py의 문제점들을 해결한 개선사항들을 테스트합니다.

주요 개선사항:
1. 🔍 스마트 키워드 생성 (AI 기반) - 기존: nature 고정 → 개선: 주제별 맞춤
2. 🖼️ 다중 이미지 검색 및 배치 - 기존: 1개 상단 → 개선: 여러 개 분산  
3. 🎨 향상된 HTML 구조 및 디자인 - 기존: 단조로움 → 개선: 현대적 UI/UX
4. 📱 반응형 디자인 및 사용자 경험 개선
"""

import os
import time
import requests
import urllib.parse
from dotenv import load_dotenv
import openai
import json
import re
from datetime import datetime

# 환경 변수 로드
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
UNSPLASH_KEY = "uQgwi8yVjCIJmD0NNU2_2oBIHUMI8UPn2B6blxwWbvQ"

# API 키 설정 (실제 사용시에는 환경변수나 별도 파일에서 관리)
OPENAI_API_KEY = "your_openai_api_key_here"
UNSPLASH_ACCESS_KEY = "your_unsplash_access_key_here"

def get_api_keys():
    """사용자로부터 API 키를 입력받는 함수"""
    print("\n🔑 API 키 설정")
    print("=" * 50)
    print("더 나은 테스트를 위해 실제 API 키를 사용하실 수 있습니다.")
    print("(선택사항이며, 입력하지 않으면 기본 더미 데이터를 사용합니다)")
    print("")
    
    # OpenAI API 키
    openai_key = input("OpenAI API 키를 입력하세요 (Enter 시 건너뛰기): ").strip()
    if not openai_key:
        openai_key = "your_openai_api_key_here"
        print("OpenAI API 키를 건너뛰었습니다. 기본 키워드 매핑을 사용합니다.")
    else:
        print("✅ OpenAI API 키가 설정되었습니다.")
    
    # Unsplash API 키
    unsplash_key = input("Unsplash API 키를 입력하세요 (Enter 시 건너뛰기): ").strip()
    if not unsplash_key:
        unsplash_key = "your_unsplash_access_key_here"
        print("Unsplash API 키를 건너뛰었습니다. 더미 이미지를 사용합니다.")
    else:
        print("✅ Unsplash API 키가 설정되었습니다.")
    
    print("=" * 50)
    return openai_key, unsplash_key

class BlogImprovementTester:
    def __init__(self, openai_key=None, unsplash_key=None):
        """테스트 클래스 초기화"""
        self.openai_key = openai_key or OPENAI_API_KEY
        self.unsplash_key = unsplash_key or UNSPLASH_ACCESS_KEY
        self.openai_client = None
        
        if self.openai_key != "your_openai_api_key_here":
            try:
                import openai
                openai.api_key = self.openai_key
                self.openai_client = openai  # 구버전에서는 openai 모듈 자체를 사용
                print("✅ OpenAI API 키 설정 성공 (v0.28.0 호환)")
            except Exception as e:
                print(f"❌ OpenAI API 키 설정 실패: {e}")
        else:
            print("ℹ️ OpenAI API 키가 설정되지 않아 기본 키워드 매핑을 사용합니다.")
    
    def test_smart_keyword_generation(self, topic):
        """1. 스마트 키워드 생성 테스트"""
        print(f"🔍 주제 '{topic}'에 대한 스마트 키워드 생성 테스트")
        
        # 주제별 맞춤 키워드 매핑 (기본값)
        keyword_mapping = {
            "기후변화": ["climate change", "global warming", "environment"],
            "인공지능": ["artificial intelligence", "AI technology", "machine learning"],
            "요리": ["cooking", "recipe", "food preparation"],
            "여행": ["travel", "tourism", "destination"],
            "건강": ["health", "wellness", "fitness"],
            "기술": ["technology", "innovation", "digital"],
        }
        
        # 기본 키워드 찾기
        basic_keywords = []
        for key, values in keyword_mapping.items():
            if key in topic:
                basic_keywords.extend(values)
                break
        else:
            basic_keywords = ["general", "lifestyle", "modern"]
        
        # OpenAI API를 통한 고급 키워드 생성 (API 키가 있는 경우)
        ai_keywords = []
        if self.openai_client:
            try:
                response = self.openai_client.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "당신은 주제에 맞는 영어 키워드를 생성하는 전문가입니다."},
                        {"role": "user", "content": f"'{topic}' 주제에 맞는 이미지 검색용 영어 키워드 3개를 생성해주세요. 단순히 번역이 아닌, 시각적으로 매력적인 이미지를 찾을 수 있는 구체적인 키워드로 만들어 주세요."}
                    ],
                    max_tokens=100
                )
                ai_response = response.choices[0].message.content
                ai_keywords = [kw.strip() for kw in ai_response.replace(',', '\n').split('\n') if kw.strip()]
            except Exception as e:
                print(f"   ⚠️ OpenAI API 오류: {e}")
        
        result = {
            "basic_keywords": basic_keywords,
            "ai_keywords": ai_keywords,
            "final_keywords": ai_keywords if ai_keywords else basic_keywords
        }
        
        print(f"   📝 기본 키워드: {basic_keywords}")
        print(f"   🤖 AI 생성 키워드: {ai_keywords}")
        print(f"   ✅ 최종 선택 키워드: {result['final_keywords']}")
        return result
    
    def analyze_topic_category_enhanced(self, topic):
        """정보성 글 주제 카테고리 분석 (강화된 버전)"""
        print(f"\n📊 정보성 글 카테고리 분석: '{topic}'")
        topic_lower = topic.lower()
        
        # 정보성 글에 특화된 카테고리 정의
        categories = {
            'education': {
                'name': '교육/학습',
                'keywords': ['교육', '학습', '공부', '대학', '수업', '강의', '시험', '자격증', '배우기', '익히기'],
                'structure': {
                    'intro_focus': '학습 목표와 중요성',
                    'core_sections': ['기본 개념 및 이론', '단계별 학습 방법', '실습 및 응용'],
                    'table_type': '학습 단계별 가이드',
                    'faq_focus': '학습 관련 질문'
                }
            },
            'science_tech': {
                'name': '과학/기술',
                'keywords': ['과학', '기술', '연구', '실험', '발명', '이론', '물리', '화학', '공학', '혁신', 'AI', '인공지능'],
                'structure': {
                    'intro_focus': '기술적 배경과 혁신성',
                    'core_sections': ['기술 원리 및 메커니즘', '현재 응용 사례', '미래 발전 전망'],
                    'table_type': '기술 사양 및 비교',
                    'faq_focus': '기술적 궁금증'
                }
            },
            'health_medical': {
                'name': '건강/의료',
                'keywords': ['건강', '의료', '질병', '치료', '예방', '약물', '운동', '영양', '다이어트', '피부', '심리건강'],
                'structure': {
                    'intro_focus': '건강상 중요성과 영향',
                    'core_sections': ['원인 및 증상 분석', '치료 및 관리 방법', '예방 및 생활습관'],
                    'table_type': '증상별 대응 가이드',
                    'faq_focus': '건강 관련 궁금증'
                }
            },
            'finance_economy': {
                'name': '금융/경제',
                'keywords': ['경제', '금융', '투자', '주식', '부동산', '저축', '보험', '세금', '연금', '재테크'],
                'structure': {
                    'intro_focus': '경제적 의미와 중요성',
                    'core_sections': ['기본 개념 및 원리', '시장 분석 및 동향', '실용적 활용 전략'],
                    'table_type': '투자 옵션 비교',
                    'faq_focus': '금융 관련 질문'
                }
            },
            'history_culture': {
                'name': '역사/문화',
                'keywords': ['역사', '문화', '전통', '예술', '음악', '문학', '철학', '종교', '사회', '정치'],
                'structure': {
                    'intro_focus': '역사적 맥락과 문화적 의미',
                    'core_sections': ['역사적 배경 및 기원', '주요 사건 및 인물', '현대적 영향 및 의미'],
                    'table_type': '시대별 주요 사건',
                    'faq_focus': '역사문화 질문'
                }
            },
            'environment': {
                'name': '환경/지속가능성',
                'keywords': ['환경', '기후', '지구온난화', '에너지', '재활용', '친환경', '지속가능', '오염', '생태계'],
                'structure': {
                    'intro_focus': '환경문제의 심각성',
                    'core_sections': ['현재 환경 상황', '주요 문제점 분석', '개선 방안 및 실천법'],
                    'table_type': '환경 지표 및 목표',
                    'faq_focus': '환경 보호 질문'
                }
            },
            'law_policy': {
                'name': '법률/정책',
                'keywords': ['법률', '정책', '규제', '제도', '권리', '의무', '계약', '소송', '행정', '정부'],
                'structure': {
                    'intro_focus': '법률적 배경과 필요성',
                    'core_sections': ['법령 및 정책 내용', '적용 범위 및 절차', '실제 사례 및 영향'],
                    'table_type': '법령 요약 및 절차',
                    'faq_focus': '법률 관련 질문'
                }
            },
            'psychology_self': {
                'name': '심리/자기계발',
                'keywords': ['심리', '자기계발', '성공', '동기', '습관', '스트레스', '관계', '소통', '리더십', '목표'],
                'structure': {
                    'intro_focus': '심리적 중요성과 개인 성장',
                    'core_sections': ['심리학적 이론 배경', '실천 방법 및 기법', '장기적 효과 및 변화'],
                    'table_type': '자기계발 단계별 가이드',
                    'faq_focus': '심리 및 성장 질문'
                }
            },
            'comparison_analysis': {
                'name': '비교/분석',
                'keywords': ['비교', '분석', '차이', '장단점', '선택', '평가', '검토', 'vs', '대비'],
                'structure': {
                    'intro_focus': '비교 분석의 목적과 기준',
                    'core_sections': ['주요 비교 요소', '상세 장단점 분석', '선택 가이드 및 결론'],
                    'table_type': '항목별 비교표',
                    'faq_focus': '선택 관련 질문'
                }
            },
            'guide_tutorial': {
                'name': '가이드/튜토리얼',
                'keywords': ['가이드', '방법', '튜토리얼', '단계', '하는법', '만들기', '설치', '사용법', '팁', '노하우'],
                'structure': {
                    'intro_focus': '가이드의 목적과 준비사항',
                    'core_sections': ['사전 준비 및 도구', '단계별 실행 방법', '고급 팁 및 주의사항'],
                    'table_type': '단계별 체크리스트',
                    'faq_focus': '실행 관련 질문'
                }
            }
        }
        
        # 주제 카테고리 매칭
        detected_category = None
        max_matches = 0
        
        for category_key, category_info in categories.items():
            matches = sum(1 for keyword in category_info['keywords'] if keyword in topic_lower)
            if matches > max_matches:
                max_matches = matches
                detected_category = category_key
        
        # 기본 카테고리 설정
        if not detected_category or max_matches == 0:
            detected_category = 'guide_tutorial'  # 기본값으로 가이드/튜토리얼 사용
        
        selected_category = categories[detected_category]
        
        print(f"   🎯 감지된 카테고리: {selected_category['name']}")
        print(f"   📝 매칭된 키워드 수: {max_matches}개")
        print(f"   🏗️ 추천 구조:")
        print(f"      - 도입부 초점: {selected_category['structure']['intro_focus']}")
        print(f"      - 핵심 섹션: {', '.join(selected_category['structure']['core_sections'])}")
        print(f"      - 표 유형: {selected_category['structure']['table_type']}")
        print(f"      - FAQ 초점: {selected_category['structure']['faq_focus']}")
        
        return {
            'category': detected_category,
            'category_info': selected_category,
            'matches': max_matches
        }
    
    def test_multi_image_search(self, keywords, count=3):
        """2. 다중 이미지 검색 테스트"""
        print(f"\n📸 다중 이미지 검색 테스트 (키워드: {keywords}, 개수: {count})")
        
        # 키워드 정제 (Unsplash API 호환성 개선)
        if self.unsplash_key != "your_unsplash_access_key_here":
            cleaned_keywords = self.clean_keywords_for_unsplash(keywords)
            print(f"   🔧 키워드 정제: {keywords} → {cleaned_keywords}")
        else:
            cleaned_keywords = keywords
        
        images = []
        
        if self.unsplash_key == "your_unsplash_access_key_here":
            print("   ⚠️ Unsplash API 키가 설정되지 않아 더미 데이터를 사용합니다.")
            # 더미 이미지 데이터
            for i, keyword in enumerate(cleaned_keywords[:count]):
                images.append({
                    "id": f"dummy_{i}",
                    "url": f"https://picsum.photos/800/400?random={i}",
                    "description": f"Sample image for {keyword}",
                    "keyword": keyword,
                    "type": "featured" if i == 0 else "content"
                })
        else:
            print("   🔄 실제 Unsplash API를 사용해 이미지를 검색합니다...")
            # 실제 Unsplash API 호출
            for i, keyword in enumerate(cleaned_keywords[:count]):
                try:
                    url = f"https://api.unsplash.com/search/photos"
                    params = {
                        "query": keyword,
                        "per_page": 1,
                        "orientation": "landscape" if i == 0 else "all"
                    }
                    headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
                    
                    print(f"   🔍 '{keyword}' 키워드로 이미지 검색 중...")
                    response = requests.get(url, params=params, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data["results"]:
                            photo = data["results"][0]
                            images.append({
                                "id": photo["id"],
                                "url": photo["urls"]["regular"],
                                "description": photo["description"] or photo["alt_description"],
                                "keyword": keyword,
                                "type": "featured" if i == 0 else "content"
                            })
                            print(f"   ✅ '{keyword}' 이미지 검색 성공!")
                        else:
                            print(f"   ⚠️ '{keyword}' 키워드로 이미지를 찾을 수 없습니다.")
                            # 이미지가 없을 때도 더미 이미지 추가
                            images.append({
                                "id": f"dummy_{i}",
                                "url": f"https://picsum.photos/800/400?random={i}",
                                "description": f"Fallback image for {keyword}",
                                "keyword": keyword,
                                "type": "featured" if i == 0 else "content"
                            })
                    else:
                        print(f"   ❌ API 오류 (상태코드: {response.status_code}): {keyword}")
                        # API 오류 시에도 더미 이미지 추가
                        images.append({
                            "id": f"dummy_{i}",
                            "url": f"https://picsum.photos/800/400?random={i}",
                            "description": f"Error fallback image for {keyword}",
                            "keyword": keyword,
                            "type": "featured" if i == 0 else "content"
                        })
                except Exception as e:
                    print(f"   ⚠️ 키워드 '{keyword}' 이미지 검색 실패: {e}")
                    # 예외 발생 시에도 더미 이미지 추가
                    images.append({
                        "id": f"dummy_{i}",
                        "url": f"https://picsum.photos/800/400?random={i}",
                        "description": f"Exception fallback image for {keyword}",
                        "keyword": keyword,
                        "type": "featured" if i == 0 else "content"
                    })
        
        print(f"   ✅ 총 {len(images)}개 이미지 수집 완료")
        for img in images:
            print(f"      - {img['type'].upper()}: {img['keyword']} -> {img['url']}")
        
        return images
    
    def generate_category_optimized_content(self, topic, category_info):
        """카테고리에 최적화된 콘텐츠 생성"""
        print(f"\n✍️ '{category_info['category_info']['name']}' 카테고리 맞춤 콘텐츠 생성")
        
        structure = category_info['category_info']['structure']
        category_name = category_info['category_info']['name']
        
        # AI 기반 콘텐츠 생성 (API 키가 있는 경우)
        if self.openai_client:
            try:
                # 1. 제목 생성
                title_prompt = f"'{topic}' 주제에 대한 {category_name} 카테고리에 특화된 매력적인 블로그 제목을 생성해주세요. 정보성 글에 적합하고 SEO에 효과적인 제목으로 만들어주세요."
                title_response = self.openai_client.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": title_prompt}],
                    max_tokens=60
                )
                title_raw = title_response.choices[0].message.content.strip()
                
                # 제목 정제: 첫 번째 제목만 추출하고 번호, 따옴표, 별표 제거
                import re
                
                # 줄바꿈으로 분리하여 첫 번째 줄만 선택
                title_lines = title_raw.split('\n')
                first_title = title_lines[0].strip()
                
                # 번호, 따옴표, 별표 등 불필요한 문자 제거
                title = re.sub(r'^\d+\.\s*["\'\*]*', '', first_title)  # 앞의 번호와 따옴표/별표
                title = re.sub(r'["\'\*]+$', '', title)  # 뒤의 따옴표/별표
                title = re.sub(r'\*{2,}', '', title)  # 연속된 별표
                title = title.strip().strip('"').strip("'")
                
                # 2. 도입부 생성
                intro_prompt = f"'{topic}' 주제에 대한 도입부를 작성해주세요. {structure['intro_focus']}에 중점을 두고, 독자의 관심을 끌 수 있도록 200-250자로 작성해주세요."
                intro_response = self.openai_client.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": intro_prompt}],
                    max_tokens=300
                )
                intro_content = intro_response.choices[0].message.content.strip()
                
                # 3. 핵심 섹션별 콘텐츠 생성
                core_contents = []
                core_subtitles = structure['core_sections']
                
                for i, section_title in enumerate(core_subtitles):
                    content_prompt = f"'{topic}' 주제의 '{section_title}' 부분에 대해 {category_name} 카테고리에 맞는 상세한 내용을 300-350자로 작성해주세요. 정보성 글답게 구체적이고 실용적인 정보를 포함해주세요."
                    content_response = self.openai_client.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": content_prompt}],
                        max_tokens=400
                    )
                    core_contents.append(content_response.choices[0].message.content.strip())
                
                # 4. 결론 생성
                conclusion_prompt = f"'{topic}' 주제에 대한 결론을 {category_name} 카테고리의 특성에 맞게 작성해주세요. 앞서 다룬 내용을 요약하고 독자에게 실용적인 조언을 200-250자로 제공해주세요."
                conclusion_response = self.openai_client.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": conclusion_prompt}],
                    max_tokens=300
                )
                conclusion_content = conclusion_response.choices[0].message.content.strip()
                
                # 5. 표 제목 생성
                table_title_prompt = f"'{topic}' 주제의 '{structure['table_type']}'에 적합한 표 제목을 간결하게 만들어주세요."
                table_title_response = self.openai_client.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": table_title_prompt}],
                    max_tokens=50
                )
                table_title = table_title_response.choices[0].message.content.strip()
                
                # 6. FAQ 생성
                faq_prompt = f"'{topic}' 주제에 대한 {structure['faq_focus']} 관련 FAQ 3개를 만들어주세요. 각 질문과 답변은 {category_name} 카테고리에 적합하고 실용적이어야 합니다. 형식: 'Q1: 질문\\nA1: 답변' 형태로 작성해주세요."
                faq_response = self.openai_client.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": faq_prompt}],
                    max_tokens=600
                )
                faq_content = faq_response.choices[0].message.content.strip()
                
                print(f"   ✅ AI 기반 {category_name} 카테고리 콘텐츠 생성 완료!")
                
            except Exception as e:
                print(f"   ⚠️ AI 콘텐츠 생성 오류: {e}")
                # 기본 콘텐츠로 대체
                title = f"{topic} - {category_name} 완벽 가이드"
                intro_content = f"이 글에서는 {topic}에 대해 {category_name} 관점에서 자세히 알아보겠습니다."
                core_contents = [f"{topic}의 {section}" for section in structure['core_sections']]
                conclusion_content = f"{topic}에 대한 종합적인 분석을 마치며, 이 정보가 도움이 되기를 바랍니다."
                table_title = f"{topic} {structure['table_type']}"
                faq_content = f"Q1: {topic}에 대해 더 알고 싶습니다.\nA1: 이 글에서 제공한 정보를 참고하시기 바랍니다."
        else:
            # API 키가 없는 경우 기본 콘텐츠
            print(f"   ℹ️ OpenAI API 키가 없어 기본 {category_name} 템플릿을 사용합니다.")
            title = f"{topic} - {category_name} 완벽 가이드"
            intro_content = f"이 글에서는 {topic}에 대해 {category_name} 관점에서 체계적으로 살펴보겠습니다. {structure['intro_focus']}를 중심으로 유용한 정보를 제공합니다."
            core_contents = [
                f"{topic}의 {structure['core_sections'][0]}에 대해 기초부터 심화까지 다루어보겠습니다.",
                f"{structure['core_sections'][1]}을 통해 실제적인 이해를 높여보겠습니다.",
                f"{structure['core_sections'][2]}을 살펴보며 미래를 준비해보겠습니다." if len(structure['core_sections']) > 2 else f"{topic}의 실용적 활용 방안을 알아보겠습니다."
            ]
            conclusion_content = f"{topic}에 대한 {category_name} 관점의 분석을 통해 깊이 있는 이해를 할 수 있었습니다. 이 정보가 실생활에 도움이 되기를 바랍니다."
            table_title = f"{topic} {structure['table_type']}"
            faq_content = f"""Q1: {topic}의 핵심 포인트는 무엇인가요?
A1: 이 글에서 다룬 {structure['core_sections'][0]} 부분이 가장 중요합니다.

Q2: 실제로 어떻게 적용할 수 있나요?
A2: {structure['core_sections'][1] if len(structure['core_sections']) > 1 else '실용적 방법'}을 참고하여 단계적으로 접근해보세요.

Q3: 더 자세한 정보는 어디서 얻을 수 있나요?
A3: 전문 자료나 관련 기관에서 추가 정보를 확인하실 수 있습니다."""
        
        content_data = {
            'title': title,
            'intro': intro_content,
            'core_subtitles': structure['core_sections'],
            'core_contents': core_contents,
            'conclusion': conclusion_content,
            'table_title': table_title,
            'faq_content': faq_content,
            'category': category_name
        }
        
        print(f"   📋 생성된 콘텐츠:")
        print(f"      - 제목: {title}")
        print(f"      - 핵심 섹션: {len(core_contents)}개")
        print(f"      - 표 제목: {table_title}")
        print(f"      - FAQ: 3개 항목")
        
        return content_data
    
    def test_category_optimized_system(self, topic):
        """정보성 글 카테고리 최적화 시스템 통합 테스트"""
        print(f"\n🎯 정보성 글 카테고리 최적화 시스템 테스트")
        print("=" * 60)
        
        # 1. 주제 카테고리 분석
        category_analysis = self.analyze_topic_category_enhanced(topic)
        
        # 2. 카테고리 맞춤 키워드 생성
        keywords_result = self.test_smart_keyword_generation(topic)
        
        # 3. 다중 이미지 검색
        images = self.test_multi_image_search(keywords_result['final_keywords'], count=3)
        
        # 4. 카테고리 최적화 콘텐츠 생성
        content_data = self.generate_category_optimized_content(topic, category_analysis)
        
        # 5. 카테고리별 맞춤 HTML 구조 생성
        html_content = self.generate_category_html_structure(topic, images, content_data, category_analysis)
        
        # 6. 테스트 결과 요약
        print(f"\n📊 테스트 결과 요약")
        print("=" * 40)
        print(f"🏷️ 원본 주제: {topic}")
        print(f"📂 감지된 카테고리: {category_analysis['category_info']['name']}")
        print(f"🔍 키워드: {', '.join(keywords_result['final_keywords'])}")
        print(f"🖼️ 이미지: {len(images)}개")
        print(f"📝 제목: {content_data['title']}")
        print(f"🏗️ 구조: {', '.join(content_data['core_subtitles'])}")
        
        # 7. HTML 파일 저장
        filename = f"category_test_{category_analysis['category']}.html"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"💾 HTML 미리보기 저장: {filename}")
        except Exception as e:
            print(f"❌ 파일 저장 실패: {e}")
        
        return {
            'category_analysis': category_analysis,
            'keywords': keywords_result,
            'images': images,
            'content_data': content_data,
            'html_content': html_content,
            'filename': filename
        }
    
    def generate_category_html_structure(self, topic, images, content_data, category_info):
        """카테고리별 최적화된 HTML 구조 생성"""
        print(f"\n🎨 {category_info['category_info']['name']} 카테고리 맞춤 HTML 생성")
        
        hero_image = images[0] if images else {"url": "https://picsum.photos/800/400", "description": "기본 이미지"}
        content_images = images[1:] if len(images) > 1 else []
        
        category_name = category_info['category_info']['name']
        category_colors = {
            '교육/학습': {'primary': '#4CAF50', 'secondary': '#81C784'},
            '과학/기술': {'primary': '#2196F3', 'secondary': '#64B5F6'},
            '건강/의료': {'primary': '#FF5722', 'secondary': '#FF8A65'},
            '금융/경제': {'primary': '#FF9800', 'secondary': '#FFB74D'},
            '역사/문화': {'primary': '#9C27B0', 'secondary': '#BA68C8'},
            '환경/지속가능성': {'primary': '#4CAF50', 'secondary': '#81C784'},
            '법률/정책': {'primary': '#607D8B', 'secondary': '#90A4AE'},
            '심리/자기계발': {'primary': '#E91E63', 'secondary': '#F06292'},
            '비교/분석': {'primary': '#795548', 'secondary': '#A1887F'},
            '가이드/튜토리얼': {'primary': '#009688', 'secondary': '#4DB6AC'}
        }
        
        colors = category_colors.get(category_name, {'primary': '#2196F3', 'secondary': '#64B5F6'})
        
        # 카테고리별 특화 HTML 생성
        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{content_data['title']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
            line-height: 1.7;
            color: #333;
            background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            border-radius: 20px;
            overflow: hidden;
            margin-top: 20px;
            margin-bottom: 20px;
        }}
        
        .category-badge {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: {colors['primary']};
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
            z-index: 10;
        }}
        
        .hero-section {{
            position: relative;
            height: 400px;
            overflow: hidden;
        }}
        
        .hero-image {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .hero-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, rgba(0,0,0,0.7), rgba(0,0,0,0.3));
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .hero-title {{
            color: white;
            font-size: 2.5rem;
            font-weight: bold;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            padding: 20px;
            max-width: 800px;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .intro-section {{
            background: linear-gradient(135deg, {colors['primary']}15, {colors['secondary']}15);
            padding: 30px;
            margin: 30px 0;
            border-radius: 15px;
            border-left: 5px solid {colors['primary']};
        }}
        
        .section {{
            background: #f8f9fa;
            padding: 30px;
            margin: 25px 0;
            border-radius: 15px;
            border-left: 5px solid {colors['secondary']};
        }}
        
        .section h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.6rem;
            display: flex;
            align-items: center;
        }}
        
        .section-icon {{
            font-size: 1.5rem;
            margin-right: 10px;
        }}
        
        .content-image {{
            width: 100%;
            height: 300px;
            object-fit: cover;
            border-radius: 15px;
            margin: 25px 0;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }}
        
        .info-table {{
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        
        .table-header {{
            background: {colors['primary']};
            color: white;
            padding: 15px;
            font-weight: bold;
            text-align: center;
        }}
        
        .table-content {{
            padding: 20px;
        }}
        
        .faq-section {{
            background: #ecf0f1;
            padding: 30px;
            margin: 30px 0;
            border-radius: 15px;
        }}
        
        .faq-item {{
            background: white;
            border-radius: 10px;
            margin: 15px 0;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .faq-question {{
            background: {colors['primary']};
            color: white;
            padding: 15px;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        .faq-question:hover {{
            background: {colors['secondary']};
        }}
        
        .faq-answer {{
            padding: 15px;
            background: #f9f9f9;
            display: none;
        }}
        
        .conclusion-section {{
            background: linear-gradient(135deg, {colors['secondary']}15, {colors['primary']}15);
            padding: 30px;
            margin: 30px 0;
            border-radius: 15px;
            border-left: 5px solid {colors['secondary']};
        }}
        
        @media (max-width: 768px) {{
            .hero-title {{ font-size: 2rem; }}
            .content {{ padding: 20px; }}
            .section {{ padding: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="category-badge">{category_name}</div>
        
        <div class="hero-section">
            <img src="{hero_image['url']}" alt="히어로 이미지" class="hero-image">
            <div class="hero-overlay">
                <h1 class="hero-title">{content_data['title']}</h1>
            </div>
        </div>
        
        <div class="content">
            <div class="intro-section">
                <p style="font-size: 1.1rem; line-height: 1.8;">{content_data['intro']}</p>
            </div>
            
            {f'<img src="{content_images[0]["url"]}" alt="콘텐츠 이미지" class="content-image">' if content_images else ''}
            
            <div class="section">
                <h2><span class="section-icon">🔍</span>{content_data['core_subtitles'][0]}</h2>
                <p style="font-size: 1.1rem; line-height: 1.8;">{content_data['core_contents'][0]}</p>
            </div>
            
            <div class="section">
                <h2><span class="section-icon">💡</span>{content_data['core_subtitles'][1]}</h2>
                <p style="font-size: 1.1rem; line-height: 1.8;">{content_data['core_contents'][1]}</p>
            </div>
            
            {f'<img src="{content_images[1]["url"]}" alt="콘텐츠 이미지 2" class="content-image">' if len(content_images) > 1 else ''}
            
            <div class="section">
                <h2><span class="section-icon">🚀</span>{content_data['core_subtitles'][2] if len(content_data['core_subtitles']) > 2 else '추가 정보'}</h2>
                <p style="font-size: 1.1rem; line-height: 1.8;">{content_data['core_contents'][2] if len(content_data['core_contents']) > 2 else '더 많은 정보를 제공합니다.'}</p>
            </div>
            
            <div class="info-table">
                <div class="table-header">
                    📊 {content_data['table_title']}
                </div>
                <div class="table-content">
                    <p>카테고리별 맞춤 정보표가 여기에 표시됩니다.</p>
                </div>
            </div>
            
            <div class="faq-section">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.6rem;">❓ 자주 묻는 질문</h2>
                {self._generate_faq_html(content_data['faq_content'])}
            </div>
            
            <div class="conclusion-section">
                <h2 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.6rem;">🎯 결론</h2>
                <p style="font-size: 1.1rem; line-height: 1.8;">{content_data['conclusion']}</p>
            </div>
        </div>
    </div>
    
    <script>
        document.querySelectorAll('.faq-question').forEach(question => {{
            question.addEventListener('click', function() {{
                const answer = this.nextElementSibling;
                const isVisible = answer.style.display === 'block';
                
                // 모든 답변 닫기
                document.querySelectorAll('.faq-answer').forEach(ans => {{
                    ans.style.display = 'none';
                }});
                
                // 클릭한 답변만 토글
                if (!isVisible) {{
                    answer.style.display = 'block';
                }}
            }});
        }});
    </script>
</body>
</html>"""
        
        print(f"   ✅ {category_name} 카테고리 맞춤 HTML 구조 생성 완료!")
        return html_content
    
    def _generate_faq_html(self, faq_content):
        """FAQ 콘텐츠를 HTML로 변환"""
        if not faq_content:
            return '<div class="faq-item"><div class="faq-question">질문이 없습니다.</div></div>'
        
        faq_html = ''
        lines = faq_content.split('\n')
        current_q = ''
        current_a = ''
        
        for line in lines:
            line = line.strip()
            if line.startswith('Q'):
                if current_q and current_a:
                    faq_html += f'''
                    <div class="faq-item">
                        <div class="faq-question">{current_q}</div>
                        <div class="faq-answer">{current_a}</div>
                    </div>'''
                current_q = line
                current_a = ''
            elif line.startswith('A'):
                current_a = line
        
        # 마지막 FAQ 추가
        if current_q and current_a:
            faq_html += f'''
            <div class="faq-item">
                <div class="faq-question">{current_q}</div>
                <div class="faq-answer">{current_a}</div>
            </div>'''
        
        return faq_html
    
    def test_enhanced_html_structure(self, topic, images):
        """3. 향상된 HTML 구조 생성 테스트"""
        print(f"\n🎨 향상된 HTML 구조 생성 테스트")
        
        # 현대적인 CSS 스타일
        css_styles = """
        <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .blog-container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 30px rgba(0,0,0,0.1);
            border-radius: 15px;
            overflow: hidden;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        
        .hero-section {
            position: relative;
            height: 400px;
            overflow: hidden;
        }
        
        .hero-image {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }
        
        .hero-image:hover {
            transform: scale(1.05);
        }
        
        .hero-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, rgba(0,0,0,0.7), rgba(0,0,0,0.3));
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .hero-title {
            color: white;
            font-size: 2.5rem;
            font-weight: bold;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            padding: 20px;
        }
        
        .content-section {
            padding: 40px;
        }
        
        .section-title {
            font-size: 1.8rem;
            color: #2c3e50;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        
        .content-block {
            background: #f8f9fa;
            padding: 25px;
            margin: 20px 0;
            border-radius: 10px;
            border-left: 4px solid #e74c3c;
            transition: all 0.3s ease;
        }
        
        .content-block:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .image-placeholder {
            background: linear-gradient(45deg, #f1f2f6, #ddd);
            border: 2px dashed #bbb;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            color: #666;
            font-style: italic;
        }
        
        .faq-section {
            background: #ecf0f1;
            padding: 30px;
            border-radius: 10px;
            margin-top: 30px;
        }
        
        .faq-item {
            margin-bottom: 15px;
            border: 1px solid #bdc3c7;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .faq-question {
            background: #34495e;
            color: white;
            padding: 15px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s ease;
        }
        
        .faq-question:hover {
            background: #2c3e50;
        }
        
        .faq-answer {
            padding: 15px;
            background: white;
            display: none;
        }
        
        .enhanced-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        
        .enhanced-table th {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 15px;
            font-weight: bold;
        }
        
        .enhanced-table td {
            padding: 15px;
            border-bottom: 1px solid #ecf0f1;
            transition: background 0.3s ease;
        }
        
        .enhanced-table tr:hover {
            background: #f8f9fa;
        }
        
        @media (max-width: 768px) {
            .hero-title {
                font-size: 1.8rem;
            }
            
            .content-section {
                padding: 20px;
            }
            
            .section-title {
                font-size: 1.4rem;
            }
        }
        </style>
        """
        
        # 구조화된 HTML 생성
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{topic} - 향상된 블로그 포스트</title>
            {css_styles}
        </head>
        <body>
            <div class="blog-container">
                <!-- 히어로 섹션 -->
                <div class="hero-section">
                    <img src="{images[0]['url'] if images else 'https://picsum.photos/1000/400'}" 
                         alt="히어로 이미지" class="hero-image">
                    <div class="hero-overlay">
                        <h1 class="hero-title">{topic}</h1>
                    </div>
                </div>
                
                <!-- 메인 콘텐츠 -->
                <div class="content-section">
                    <!-- 도입부 -->
                    <div class="content-block">
                        <h2 class="section-title">📌 도입부</h2>
                        <p>이 글에서는 <strong>{topic}</strong>에 대해 자세히 알아보겠습니다. 
                        현대 사회에서 이 주제가 갖는 의미와 중요성을 살펴보고, 
                        실질적인 인사이트를 제공하겠습니다.</p>
                    </div>
                    
                    <!-- 이미지 플레이스홀더 1 -->
                    <div class="image-placeholder">
                        🖼️ 콘텐츠 이미지 1 자리 - {images[1]['keyword'] if len(images) > 1 else '관련 이미지'}
                        <br><small>실제로는 여기에 {images[1]['url'] if len(images) > 1 else '이미지 URL'}이 표시됩니다</small>
                    </div>
                    
                    <!-- 핵심 내용 1 -->
                    <div class="content-block">
                        <h2 class="section-title">🔍 핵심 내용 1</h2>
                        <p>첫 번째 핵심 주제에 대한 상세한 설명이 들어갑니다. 
                        여기서는 주제의 배경과 기본 개념에 대해 다룹니다.</p>
                        <ul>
                            <li>주요 특징 1</li>
                            <li>주요 특징 2</li>
                            <li>주요 특징 3</li>
                        </ul>
                    </div>
                    
                    <!-- 핵심 내용 2 -->
                    <div class="content-block">
                        <h2 class="section-title">💡 핵심 내용 2</h2>
                        <p>두 번째 핵심 주제에 대한 심화 내용입니다. 
                        실용적인 접근법과 구체적인 예시를 포함합니다.</p>
                    </div>
                    
                    <!-- 이미지 플레이스홀더 2 -->
                    <div class="image-placeholder">
                        🖼️ 콘텐츠 이미지 2 자리 - {images[2]['keyword'] if len(images) > 2 else '관련 이미지'}
                        <br><small>실제로는 여기에 {images[2]['url'] if len(images) > 2 else '이미지 URL'}이 표시됩니다</small>
                    </div>
                    
                    <!-- 핵심 내용 3 -->
                    <div class="content-block">
                        <h2 class="section-title">🚀 핵심 내용 3</h2>
                        <p>세 번째 핵심 주제로, 미래 전망과 발전 방향에 대해 다룹니다. 
                        최신 트렌드와 예상되는 변화를 분석합니다.</p>
                    </div>
                    
                    <!-- 향상된 표 -->
                    <h2 class="section-title">📊 주요 정보 표</h2>
                    <table class="enhanced-table">
                        <thead>
                            <tr>
                                <th>항목</th>
                                <th>설명</th>
                                <th>중요도</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>기본 개념</td>
                                <td>{topic}의 기본적인 개념과 정의</td>
                                <td>⭐⭐⭐⭐⭐</td>
                            </tr>
                            <tr>
                                <td>실용성</td>
                                <td>실생활에서의 활용도와 적용 가능성</td>
                                <td>⭐⭐⭐⭐</td>
                            </tr>
                            <tr>
                                <td>미래 전망</td>
                                <td>향후 발전 방향과 예상되는 변화</td>
                                <td>⭐⭐⭐</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <!-- 인터랙티브 FAQ -->
                    <div class="faq-section">
                        <h2 class="section-title">❓ 자주 묻는 질문</h2>
                        
                        <div class="faq-item">
                            <div class="faq-question" onclick="toggleFAQ(this)">
                                Q1. {topic}의 가장 중요한 특징은 무엇인가요?
                            </div>
                            <div class="faq-answer">
                                A1. 가장 중요한 특징은... (상세한 답변이 여기에 들어갑니다)
                            </div>
                        </div>
                        
                        <div class="faq-item">
                            <div class="faq-question" onclick="toggleFAQ(this)">
                                Q2. 초보자도 쉽게 이해할 수 있나요?
                            </div>
                            <div class="faq-answer">
                                A2. 네, 이 글에서 제공하는 단계별 설명을... (상세한 답변)
                            </div>
                        </div>
                        
                        <div class="faq-item">
                            <div class="faq-question" onclick="toggleFAQ(this)">
                                Q3. 실제로 어떻게 활용할 수 있나요?
                            </div>
                            <div class="faq-answer">
                                A3. 다양한 활용 방법이 있습니다... (구체적인 예시들)
                            </div>
                        </div>
                    </div>
                    
                    <!-- 결론부 -->
                    <div class="content-block">
                        <h2 class="section-title">🎯 결론</h2>
                        <p><strong>{topic}</strong>에 대한 종합적인 분석을 통해 우리는 이 주제의 중요성과 
                        실용성을 확인할 수 있었습니다. 앞으로도 지속적인 관심과 학습이 필요한 영역입니다.</p>
                    </div>
                </div>
            </div>
            
            <!-- JavaScript for FAQ functionality -->
            <script>
            function toggleFAQ(element) {{
                const answer = element.nextElementSibling;
                const isVisible = answer.style.display === 'block';
                
                // 모든 FAQ 답변 닫기
                document.querySelectorAll('.faq-answer').forEach(ans => {{
                    ans.style.display = 'none';
                }});
                
                // 클릭한 항목만 토글
                if (!isVisible) {{
                    answer.style.display = 'block';
                }}
            }}
            
            // 페이지 로드시 애니메이션 효과
            document.addEventListener('DOMContentLoaded', function() {{
                const blocks = document.querySelectorAll('.content-block');
                blocks.forEach((block, index) => {{
                    setTimeout(() => {{
                        block.style.opacity = '0';
                        block.style.transform = 'translateY(20px)';
                        block.style.transition = 'all 0.6s ease';
                        
                        setTimeout(() => {{
                            block.style.opacity = '1';
                            block.style.transform = 'translateY(0)';
                        }}, 100);
                    }}, index * 200);
                }});
            }});
            </script>
        </body>
        </html>
        """
        
        print("   ✅ HTML 구조 생성 완료")
        print("   📋 주요 개선사항:")
        print("      - 현대적인 CSS 디자인 (그라디언트, 호버 효과)")
        print("      - 반응형 레이아웃")
        print("      - 히어로 이미지 + 본문 중간 이미지 배치")
        print("      - 인터랙티브 FAQ (접기/펼치기)")
        print("      - 향상된 표 스타일링")
        print("      - 애니메이션 효과")
        
        return html_content
    
    def run_full_test(self, topic="인공지능의 미래"):
        """전체 테스트 실행"""
        print("=" * 60)
        print("🚀 블로그 자동 생성 개선사항 종합 테스트")
        print("=" * 60)
        print(f"📋 테스트 주제: {topic}")
        print(f"📅 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1단계: 키워드 생성
        keyword_result = self.test_smart_keyword_generation(topic)
        
        # 2단계: 이미지 검색
        images = self.test_multi_image_search(keyword_result['final_keywords'])
        
        # 3단계: HTML 생성
        html_content = self.test_enhanced_html_structure(topic, images)
        
        # 4단계: 결과 저장
        print(f"\n💾 결과 저장 중...")
        filename = f"blog_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"   ✅ 결과가 '{filename}' 파일로 저장되었습니다.")
            print(f"   🌐 브라우저에서 파일을 열어 결과를 확인해보세요!")
        except Exception as e:
            print(f"   ⚠️ 파일 저장 실패: {e}")
        
        # 테스트 요약
        print(f"\n" + "=" * 60)
        print("📊 테스트 요약")
        print("=" * 60)
        print(f"🎯 생성된 키워드: {len(keyword_result['final_keywords'])}개")
        print(f"📸 수집된 이미지: {len(images)}개")
        print(f"🎨 HTML 구조: 향상된 반응형 디자인 적용")
        print(f"⚡ 인터랙티브 요소: FAQ, 호버 효과, 애니메이션")
        print("=" * 60)
        
        return {
            "keywords": keyword_result,
            "images": images,
            "html_file": filename
        }

    def clean_keywords_for_unsplash(self, keywords):
        """Unsplash API에 적합하도록 키워드를 정제하는 함수"""
        cleaned_keywords = []
        
        for keyword in keywords:
            # 숫자와 점 제거 (1., 2., 3. 등)
            cleaned = re.sub(r'^\d+\.\s*', '', keyword)
            
            # 너무 긴 키워드는 핵심 단어만 추출
            if len(cleaned) > 30:
                # 핵심 단어 추출 (첫 2-3개 단어)
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

# 메인 실행부
if __name__ == "__main__":
    print("🔧 블로그 자동 생성 개선사항 테스트 프로그램")
    print("=" * 60)
    
    # API 키 설정
    openai_key, unsplash_key = get_api_keys()
    
    print("\n🎯 테스트 모드를 선택하세요:")
    print("1. 기본 테스트 (기존 방식)")
    print("2. 정보성 글 카테고리 최적화 시스템 테스트 (신규!)")
    print("3. 다양한 카테고리 비교 테스트")
    
    mode_choice = input("\n선택 (1-3): ").strip()
    
    # 테스트 실행
    tester = BlogImprovementTester(openai_key, unsplash_key)
    
    if mode_choice == "2":
        print("\n🎯 정보성 글 카테고리 최적화 시스템 테스트")
        print("=" * 50)
        
        # 추천 주제 목록 (카테고리별)
        suggested_topics = {
            "교육/학습": "효과적인 온라인 학습법",
            "과학/기술": "양자컴퓨터의 원리와 미래",
            "건강/의료": "스트레스 관리와 정신건강",
            "금융/경제": "초보자를 위한 투자 가이드",
            "역사/문화": "한국 전통문화의 현대적 계승",
            "환경/지속가능성": "플라스틱 없는 생활 실천법",
            "법률/정책": "개인정보보호법 완벽 이해",
            "심리/자기계발": "습관 형성의 과학적 원리",
            "비교/분석": "전기차 vs 하이브리드차 선택 가이드",
            "가이드/튜토리얼": "홈베이킹 초보자 완벽 가이드"
        }
        
        print("\n📋 추천 주제 (카테고리별):")
        for i, (category, topic) in enumerate(suggested_topics.items(), 1):
            print(f"{i:2}. [{category}] {topic}")
        
        choice = input(f"\n추천 주제 선택 (1-{len(suggested_topics)}) 또는 직접 입력: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(suggested_topics):
            selected_topic = list(suggested_topics.values())[int(choice)-1]
            selected_category = list(suggested_topics.keys())[int(choice)-1]
            print(f"✅ 선택된 주제: [{selected_category}] {selected_topic}")
        else:
            selected_topic = choice if choice else "인공지능과 교육의 미래"
            print(f"✅ 사용자 입력 주제: {selected_topic}")
        
        # 정보성 글 카테고리 최적화 시스템 테스트 실행
        result = tester.test_category_optimized_system(selected_topic)
        
        print(f"\n🎉 정보성 글 카테고리 최적화 테스트 완료!")
        print(f"📁 생성된 파일: {result['filename']}")
        
    elif mode_choice == "3":
        print("\n🔄 다양한 카테고리 비교 테스트")
        print("=" * 50)
        
        test_topics = [
            "머신러닝 기초 완벽 가이드",
            "당뇨병 예방과 관리법",
            "부동산 투자 전략 분석"
        ]
        
        print("3개의 서로 다른 카테고리 주제로 테스트합니다:")
        for i, topic in enumerate(test_topics, 1):
            print(f"{i}. {topic}")
        
        input("\n계속하려면 Enter를 누르세요...")
        
        for i, topic in enumerate(test_topics, 1):
            print(f"\n{'='*20} 테스트 {i}/3: {topic} {'='*20}")
            result = tester.test_category_optimized_system(topic)
            print(f"✅ 테스트 {i} 완료! 파일: {result['filename']}")
            
            if i < len(test_topics):
                print("다음 테스트를 위해 잠시 대기...")
                import time
                time.sleep(2)
        
        print(f"\n🎉 모든 카테고리 비교 테스트 완료!")
        
    else:
        # 기본 테스트 (기존 방식)
        print("\n📝 기본 테스트 모드")
        custom_topic = input("\n테스트할 주제를 입력하세요 (Enter시 기본값 '인공지능의 미래' 사용): ").strip()
        if not custom_topic:
            custom_topic = "인공지능의 미래"
        
        result = tester.run_full_test(custom_topic)
        print(f"\n🎉 기본 테스트 완료! 생성된 HTML 파일을 브라우저에서 확인해보세요.")
    
    print(f"\n{'='*60}")
    print("💡 테스트 완료 안내:")
    print("   - 생성된 HTML 파일을 브라우저에서 열어 결과를 확인하세요")
    print("   - 각 카테고리별로 다른 구조와 디자인이 적용됩니다")
    print("   - API 키가 설정된 경우 더 풍부한 콘텐츠가 생성됩니다")
    print(f"{'='*60}")
