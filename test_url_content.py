#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 콘텐츠 추출 기능 테스트 스크립트
=================================

새로 추가된 URL 기반 블로그 글 생성 기능을 테스트합니다.
"""

import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 필수 API 키 확인
def check_api_keys():
    """필수 API 키들이 설정되어 있는지 확인"""
    keys = {
        'OpenAI API': os.getenv('OPENAI_API_KEY'),
        'Unsplash API': 'uQgwi8yVjCIJmD0NNU2_2oBIHUMI8UPn2B6blxwWbvQ'  # 하드코딩된 키 사용
    }
    
    print("🔑 API 키 확인:")
    for name, key in keys.items():
        if key:
            print(f"  ✅ {name}: 설정됨")
        else:
            print(f"  ❌ {name}: 설정되지 않음")
    
    return all(keys.values())

# 모듈 import 테스트
def test_module_import():
    """URL 콘텐츠 추출 모듈 import 테스트"""
    try:
        from url_content_extractor import generate_blog_from_url, URLContentExtractor
        print("✅ URL 콘텐츠 추출 모듈 import 성공")
        return True
    except ImportError as e:
        print(f"❌ URL 콘텐츠 추출 모듈 import 실패: {e}")
        return False

# 간단한 URL 테스트
def test_simple_url():
    """간단한 URL 콘텐츠 추출 테스트"""
    
    if not test_module_import():
        return False
    
    from url_content_extractor import generate_blog_from_url
    
    # 테스트 URL들
    test_urls = [
        {
            'name': '네이버 뉴스',
            'url': 'https://news.naver.com',
            'description': '네이버 뉴스 메인 페이지'
        },
        {
            'name': 'BBC 뉴스',
            'url': 'https://www.bbc.com/news',
            'description': 'BBC 뉴스 메인 페이지'
        }
    ]
    
    print("\n🔍 URL 콘텐츠 추출 테스트:")
    
    for test_case in test_urls:
        print(f"\n--- {test_case['name']} 테스트 ---")
        print(f"URL: {test_case['url']}")
        print(f"설명: {test_case['description']}")
        
        try:
            result = generate_blog_from_url(test_case['url'], "테스트 관점")
            
            if result['success']:
                print("✅ 콘텐츠 추출 성공!")
                print(f"제목: {result['title'][:100]}...")
                print(f"내용 길이: {len(result['content'])} 글자")
                print(f"태그: {result['tags'][:100]}...")
            else:
                print(f"❌ 콘텐츠 추출 실패: {result['error']}")
                
        except Exception as e:
            print(f"❌ 테스트 중 오류 발생: {e}")
        
        # 사용자 입력 대기
        input("다음 테스트로 진행하려면 엔터키를 누르세요...")

# 메인 시스템 통합 테스트
def test_v2_integration():
    """V2 시스템 통합 테스트"""
    
    if not test_module_import():
        return False
    
    try:
        # V2 시스템의 generate_blog_from_url_v2 함수 테스트
        from auto_post_generator_v2_complete import generate_blog_from_url_v2
        
        print("\n🔧 V2 시스템 통합 테스트:")
        
        test_url = input("테스트할 URL을 입력하세요: ").strip()
        if not test_url:
            print("URL이 입력되지 않았습니다.")
            return False
        
        custom_angle = input("관점/각도를 입력하세요 (선택사항): ").strip()
        
        print(f"\n🔗 V2 시스템으로 URL 처리 중: {test_url}")
        
        result = generate_blog_from_url_v2(test_url, custom_angle)
        
        if result:
            print("✅ V2 시스템 통합 성공!")
            print(f"제목: {result['title']}")
            print(f"태그: {result['tags']}")
            print(f"키워드: {result['keywords']}")
            print(f"이미지 개수: {len(result['images'])}")
            print(f"소스 타입: {result.get('source_type', '알 수 없음')}")
            print(f"HTML 콘텐츠 길이: {len(result['html_content'])} 글자")
            
            # HTML 미리보기 저장
            with open(f"url_test_result_{int(time.time())}.html", 'w', encoding='utf-8') as f:
                f.write(result['html_content'])
            print("📄 HTML 결과가 파일로 저장되었습니다.")
            
        else:
            print("❌ V2 시스템 통합 실패")
            
    except ImportError as e:
        print(f"❌ V2 시스템 모듈 import 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ V2 시스템 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 URL 콘텐츠 추출 기능 테스트")
    print("=" * 50)
    
    # 1. API 키 확인
    if not check_api_keys():
        print("\n⚠️ 일부 API 키가 설정되지 않았습니다.")
        print("   .env 파일을 확인하고 OPENAI_API_KEY를 설정해주세요.")
    
    # 2. 모듈 import 테스트
    if not test_module_import():
        print("\n❌ 모듈 import에 실패했습니다.")
        print("   requirements.txt의 라이브러리들이 설치되었는지 확인하세요:")
        print("   pip install -r requirements.txt")
        return
    
    # 3. 테스트 메뉴
    while True:
        print("\n" + "=" * 50)
        print("🎯 테스트 메뉴")
        print("=" * 50)
        print("1. 간단한 URL 테스트")
        print("2. V2 시스템 통합 테스트")
        print("3. 종료")
        
        choice = input("\n선택하세요 (1-3): ").strip()
        
        if choice == '1':
            test_simple_url()
        elif choice == '2':
            test_v2_integration()
        elif choice == '3':
            print("👋 테스트를 종료합니다.")
            break
        else:
            print("❌ 1, 2, 3 중에서 선택해주세요.")

if __name__ == "__main__":
    import time
    main() 