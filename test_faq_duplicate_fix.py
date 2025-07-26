#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FAQ 중복 제목 문제 해결 테스트
"""

import sys
import os
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 필요한 모듈들 import
try:
    # 파일명에 하이픈이 있어서 직접 import
    import importlib.util
    spec = importlib.util.spec_from_file_location("main_module", "auto_post_generator_v2_complete-BOOK-BF7VOMCU5L.py")
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)
    
    generate_faq_by_content = main_module.generate_faq_by_content
    generate_enhanced_html_v2 = main_module.generate_enhanced_html_v2
    print("✅ FAQ 생성 모듈 로드 성공")
except ImportError as e:
    print(f"❌ 모듈 로드 실패: {e}")
    exit(1)

def test_faq_duplicate_fix():
    """FAQ 중복 제목 문제 해결 테스트"""
    
    # 테스트용 블로그 글 내용
    test_title = "매일 커피값 벌기! 배당으로 생활비 해결하는 ETF 포트폴리오"
    test_content = """
    ## 매일 커피값 벌기! 배당으로 생활비 해결하는 ETF 포트폴리오

    안녕하세요! 오늘은 매일 들어오는 배당금으로 커피값부터 교통비까지 생활비를 해결할 수 있는 방법에 대해 알아보겠습니다.

    ### 현실적인 소액 투자로 배당금 받기

    많은 이들이 꿈꾸는 것이 바로 배당금으로 생활비를 충당하는 것입니다. 이는 높은 초기 투자가 필요하지만, 체계적인 접근을 통해 충분히 달성할 수 있습니다.

    ### 생활비 계산하기

    매일 필요한 생활비를 정확히 파악하는 것이 중요합니다. 예를 들어, 하루 커피값이 4,000원이고 교통비가 3,000원이라면, 매일 목표 배당금은 7,000원이 되어야 합니다.

    ### 요일별 ETF 조합으로 매일 배당금 받기

    매일 7,000원의 배당금을 받기 위해서는 요일별로 다른 배당 주기를 가진 ETF들을 조합해야 합니다. 예를 들어:

    - **월요일**: BLX ETF (연 배당률 32.88%)
    - **화요일**: AMGW ETF (연 배당률 36.65%)
    - **수요일**: MVII ETF (연 배당률 26.75%)
    - **목요일**: YBTC ETF (연 배당률 36.83%)
    - **금요일**: YMAX ETF (연 배당률 49.30%)

    ### 투자 시뮬레이션

    매일 7,000원의 배당금을 받기 위해 각 ETF에 투자해야 하는 금액은 다음과 같습니다:

    - **BLX**: 130만 원
    - **AMGW**: 120만 원
    - **MVII**: 160만 원
    - **YBTC**: 120만 원
    - **YMAX**: 90만 원

    이렇게 투자하면 연간 약 36만 4,000원의 배당금을 창출할 수 있습니다.
    """
    
    print("🔗 FAQ 중복 제목 문제 해결 테스트")
    print("=" * 60)
    
    try:
        # 1. 개선된 FAQ 생성
        print("\n📝 1. 개선된 FAQ 생성 (제목 제외):")
        print("-" * 50)
        faq_content = generate_faq_by_content(test_title, test_content)
        if faq_content:
            print("✅ FAQ 생성 성공!")
            print("생성된 FAQ 내용:")
            print(faq_content[:500] + "..." if len(faq_content) > 500 else faq_content)
            
            # 2. 전체 HTML 생성 테스트
            print("\n📝 2. 전체 HTML 생성 테스트:")
            print("-" * 50)
            
            # 테스트용 데이터
            images = [{'url': 'https://example.com/image1.jpg'}]
            content_data = {
                'title': test_title,
                'intro': '테스트 소개',
                'sections': [{'subtitle': '테스트 섹션', 'content': '테스트 내용'}],
                'conclusion': '테스트 결론'
            }
            
            html_content = generate_enhanced_html_v2(test_title, images, content_data, faq_content)
            
            # HTML 파일로 저장
            filename = f"faq_duplicate_fix_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"💾 테스트 결과가 '{filename}' 파일로 저장되었습니다.")
            
            # 3. 중복 제목 확인
            print("\n📊 3. 중복 제목 확인:")
            print("-" * 50)
            
            # "자주 묻는 질문" 제목이 몇 번 나타나는지 확인
            title_count = html_content.count("자주 묻는 질문")
            question_mark_count = html_content.count("❓")
            
            print(f"📝 '자주 묻는 질문' 제목 개수: {title_count}")
            print(f"❓ 물음표 아이콘 개수: {question_mark_count}")
            
            if title_count == 1 and question_mark_count == 1:
                print("✅ 중복 제목 문제 해결됨!")
            else:
                print("❌ 아직 중복 제목 문제가 있습니다.")
                print(f"   - 제목 개수: {title_count}")
                print(f"   - 아이콘 개수: {question_mark_count}")
            
        else:
            print("❌ FAQ 생성 실패")
        
        print("\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_faq_duplicate_fix() 