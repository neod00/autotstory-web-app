#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 URL 기반 블로그 글 생성 테스트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 필요한 모듈들 import
try:
    from url_content_extractor import generate_blog_from_url
    print("✅ URL 콘텐츠 추출 모듈 로드 성공")
except ImportError as e:
    print(f"❌ 모듈 로드 실패: {e}")
    exit(1)

def test_improved_url_generation():
    """개선된 URL 기반 블로그 글 생성 테스트"""
    
    # 테스트할 유튜브 URL
    youtube_url = "https://youtu.be/VlHoAkUxYks?si=MtHLZlmm0veDRmkX"
    
    print(f"🔗 테스트 URL: {youtube_url}")
    print("=" * 60)
    
    try:
        # 개선된 관점 지정
        custom_angle = "초보 투자자를 위한 실용적인 가이드와 구체적인 액션 플랜"
        
        print("🎨 개선된 URL 기반 블로그 글 생성 중...")
        print(f"💡 관점: {custom_angle}")
        
        # URL 기반 블로그 글 생성
        result = generate_blog_from_url(youtube_url, custom_angle)
        
        if result['success']:
            print("✅ 개선된 URL 기반 블로그 글 생성 성공!")
            
            # 생성된 콘텐츠 정보 출력
            print(f"\n📋 생성된 블로그 글 정보:")
            print("-" * 50)
            print(f"📄 제목: {result['title']}")
            print(f"📏 본문 길이: {len(result['content'])} 글자")
            print(f"🏷️ 태그: {result['tags']}")
            
            # 본문 미리보기
            print(f"\n📄 본문 미리보기 (처음 500자):")
            print("-" * 50)
            preview = result['content'][:500] + "..." if len(result['content']) > 500 else result['content']
            print(preview)
            print("-" * 50)
            
            # HTML 파일로 저장
            filename = f"improved_url_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{result['title']}</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        .content {{ margin: 20px 0; white-space: pre-wrap; }}
        .tags {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
        .source {{ margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #007bff; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{result['title']}</h1>
        
        <div class="content">
{result['content'].replace(chr(10), '<br>')}
        </div>
        
        <div class="tags">
            <strong>태그:</strong> {result['tags']}
        </div>
        
        <div class="source">
            <p><strong>📎 참고 자료:</strong> <a href="{youtube_url}" target="_blank">{youtube_url}</a></p>
            <p><strong>💡 관점:</strong> {custom_angle}</p>
        </div>
    </div>
</body>
</html>
                """)
            
            print(f"\n💾 개선된 블로그 글이 '{filename}' 파일로 저장되었습니다.")
            print("✅ 테스트 완료!")
            
        else:
            print(f"❌ URL 기반 블로그 글 생성 실패: {result['error']}")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from datetime import datetime
    test_improved_url_generation() 