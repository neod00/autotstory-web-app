#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유튜브 URL 테스트 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# URL 콘텐츠 추출 모듈 import
try:
    from url_content_extractor import URLContentExtractor
    URL_CONTENT_AVAILABLE = True
    print("✅ URL 콘텐츠 추출 모듈 로드 성공")
except ImportError as e:
    print(f"❌ URL 콘텐츠 추출 모듈 로드 실패: {e}")
    URL_CONTENT_AVAILABLE = False

def test_youtube_url():
    """유튜브 URL 테스트"""
    if not URL_CONTENT_AVAILABLE:
        print("❌ URL 콘텐츠 추출 모듈을 사용할 수 없습니다.")
        return
    
    # 테스트할 유튜브 URL
    youtube_url = "https://youtu.be/VlHoAkUxYks?si=pfBv50aidhezu00Z"
    
    print(f"🔗 테스트 URL: {youtube_url}")
    print("=" * 50)
    
    # URL 콘텐츠 추출기 생성
    extractor = URLContentExtractor()
    
    try:
        # URL에서 콘텐츠 추출
        print("🔍 URL에서 콘텐츠 추출 중...")
        result = extractor.extract_content_from_url(youtube_url)
        
        if result['success']:
            print("✅ 콘텐츠 추출 성공!")
            print(f"📄 제목: {result['title']}")
            print(f"📝 요약: {result['summary'][:200]}...")
            print(f"🎬 타입: {result['type']}")
            print(f"🔗 원본 URL: {result['url']}")
            
            # 콘텐츠 길이 확인
            content_length = len(result['content'])
            print(f"📏 콘텐츠 길이: {content_length} 글자")
            
            if content_length > 0:
                print("\n📋 추출된 콘텐츠 미리보기:")
                print("-" * 50)
                print(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
                print("-" * 50)
            else:
                print("⚠️ 추출된 콘텐츠가 없습니다.")
                
        else:
            print(f"❌ 콘텐츠 추출 실패: {result['error']}")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_youtube_url() 