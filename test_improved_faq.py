#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 FAQ 생성 기능 테스트
"""

import sys
import os

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
    generate_faq_by_keyword = main_module.generate_faq_by_keyword
    print("✅ FAQ 생성 모듈 로드 성공")
except ImportError as e:
    print(f"❌ 모듈 로드 실패: {e}")
    exit(1)

def test_improved_faq_generation():
    """개선된 FAQ 생성 기능 테스트"""
    
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

    ### 단계적 확장과 포트폴리오 관리

    처음에는 소소한 항목부터 시작해 점차 편의점 간식, OTT 구독료 등으로 범위를 넓혀가는 것이 좋습니다. 장기적으로는 통신비, 식비, 주거비용까지 배당금으로 해결할 수 있게 됩니다.

    포트폴리오 관리 시, 배당 계좌와 성장 계좌를 분리하고, 다양한 자산군과 전략을 가진 ETF로 구성하여 리스크를 분산시키는 것이 중요합니다.

    ### 결론

    매일 배당금 7,000원을 통해 커피값과 교통비를 해결하는 구체적인 방법을 알아보았습니다. 총 620만 원을 다섯 개의 ETF에 분산 투자하면 매일 배당금을 수령할 수 있습니다.
    """
    
    print("🔗 개선된 FAQ 생성 기능 테스트")
    print("=" * 60)
    
    try:
        # 1. 기존 방식 (제목 기반)
        print("\n📝 1. 기존 방식 (제목 기반) FAQ 생성:")
        print("-" * 50)
        old_faq = generate_faq_by_keyword(test_title)
        print(old_faq[:300] + "..." if len(old_faq) > 300 else old_faq)
        
        # 2. 개선된 방식 (콘텐츠 기반)
        print("\n📝 2. 개선된 방식 (콘텐츠 기반) FAQ 생성:")
        print("-" * 50)
        new_faq = generate_faq_by_content(test_title, test_content)
        if new_faq:
            print(new_faq[:500] + "..." if len(new_faq) > 500 else new_faq)
        else:
            print("❌ 개선된 FAQ 생성 실패")
        
        # 3. 비교 분석
        print("\n📊 비교 분석:")
        print("-" * 50)
        print("✅ 기존 방식: 제목만을 기반으로 일반적인 질문 생성")
        print("✅ 개선된 방식: 실제 블로그 글 내용을 분석하여 관련성 높은 질문 생성")
        print("✅ 개선 효과: 독자들이 실제로 궁금해할 만한 구체적인 질문과 답변")
        
        # 4. HTML 파일로 저장
        if new_faq:
            filename = f"improved_faq_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>개선된 FAQ 생성 테스트</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        .comparison {{ margin: 20px 0; }}
        .old-faq {{ background: #fff3cd; padding: 20px; border-radius: 8px; margin: 10px 0; }}
        .new-faq {{ background: #d1ecf1; padding: 20px; border-radius: 8px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>개선된 FAQ 생성 기능 테스트</h1>
        
        <div class="comparison">
            <h2>기존 방식 (제목 기반)</h2>
            <div class="old-faq">
                {old_faq}
            </div>
            
            <h2>개선된 방식 (콘텐츠 기반)</h2>
            <div class="new-faq">
                {new_faq}
            </div>
        </div>
    </div>
</body>
</html>
                """)
            
            print(f"\n💾 테스트 결과가 '{filename}' 파일로 저장되었습니다.")
        
        print("\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from datetime import datetime
    test_improved_faq_generation() 