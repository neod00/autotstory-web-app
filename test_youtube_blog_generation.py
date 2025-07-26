#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유튜브 URL로 블로그 글 생성 테스트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 필요한 모듈들 import
try:
    from url_content_extractor import URLContentExtractor
    # 파일명에 하이픈이 있어서 직접 import 대신 함수를 복사
    URL_CONTENT_AVAILABLE = True
    print("✅ URL 콘텐츠 추출 모듈 로드 성공")
except ImportError as e:
    print(f"❌ URL 콘텐츠 추출 모듈 로드 실패: {e}")
    URL_CONTENT_AVAILABLE = False

def generate_blog_from_url_v2(url, custom_angle=""):
    """
    URL 기반 블로그 콘텐츠 생성 (간단한 버전)
    """
    if not URL_CONTENT_AVAILABLE:
        print("❌ URL 콘텐츠 추출 모듈을 사용할 수 없습니다.")
        return None
    
    try:
        print(f"🔗 URL 기반 콘텐츠 생성 시작: {url}")
        
        # URL에서 콘텐츠 추출
        extractor = URLContentExtractor()
        result = extractor.extract_content_from_url(url)
        
        if not result['success']:
            print(f"❌ URL 콘텐츠 추출 실패: {result['error']}")
            return None
        
        # 간단한 블로그 글 생성
        title = result['title']
        content = result['content']
        summary = result['summary']
        
        # HTML 형식으로 변환
        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        .source-info {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0; border-radius: 4px; }}
        .content {{ margin: 20px 0; }}
        p {{ margin-bottom: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <div class="source-info">
            <p><strong>📎 참고 자료:</strong> <a href="{url}" target="_blank">{title}</a></p>
            <p><strong>💡 관점:</strong> {custom_angle if custom_angle else "원본 내용을 바탕으로 재구성"}</p>
        </div>
        
        <div class="content">
            {summary.replace(chr(10), '<br>')}
        </div>
        
        <div class="content">
            <h2>📋 상세 내용</h2>
            {content.replace(chr(10), '<br>')}
        </div>
    </div>
</body>
</html>
        """
        
        blog_post = {
            'title': title,
            'content': content,
            'html_content': html_content,
            'tags': '투자,ETF,배당,포트폴리오',
            'keywords': 'ETF,배당,투자,포트폴리오',
            'images': [],
            'source_url': url,
            'original_title': title,
            'source_type': 'youtube'
        }
        
        print("✅ URL 기반 블로그 포스트 생성 완료!")
        return blog_post
        
    except Exception as e:
        print(f"❌ URL 기반 콘텐츠 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_youtube_blog_generation():
    """유튜브 URL로 블로그 글 생성 테스트"""
    if not URL_CONTENT_AVAILABLE:
        print("❌ 필요한 모듈을 사용할 수 없습니다.")
        return
    
    # 테스트할 유튜브 URL
    youtube_url = "https://youtu.be/VlHoAkUxYks?si=pfBv50aidhezu00Z"
    
    print(f"🔗 테스트 URL: {youtube_url}")
    print("=" * 60)
    
    try:
        # 1단계: URL에서 콘텐츠 추출
        print("🔍 1단계: URL에서 콘텐츠 추출 중...")
        extractor = URLContentExtractor()
        result = extractor.extract_content_from_url(youtube_url)
        
        if not result['success']:
            print(f"❌ 콘텐츠 추출 실패: {result['error']}")
            return
        
        print("✅ 콘텐츠 추출 성공!")
        print(f"📄 제목: {result['title']}")
        print(f"📏 콘텐츠 길이: {len(result['content'])} 글자")
        
        # 2단계: 블로그 글 생성
        print("\n🎨 2단계: 블로그 글 생성 중...")
        custom_angle = "초보 투자자 관점에서 쉽게 설명"
        
        blog_post = generate_blog_from_url_v2(youtube_url, custom_angle)
        
        if blog_post is None:
            print("❌ 블로그 글 생성 실패")
            return
        
        print("✅ 블로그 글 생성 성공!")
        
        # 3단계: 생성된 블로그 글 정보 출력
        print("\n📋 생성된 블로그 글 정보:")
        print("-" * 50)
        print(f"📄 제목: {blog_post['title']}")
        print(f"🏷️ 태그: {blog_post['tags']}")
        print(f"🔑 키워드: {blog_post['keywords']}")
        print(f"🖼️ 이미지: {len(blog_post['images'])}개")
        print(f"🔗 원본 URL: {blog_post.get('source_url', '없음')}")
        print(f"📝 원본 제목: {blog_post.get('original_title', '없음')}")
        
        # 4단계: HTML 콘텐츠 미리보기
        print("\n📄 HTML 콘텐츠 미리보기:")
        print("-" * 50)
        html_content = blog_post.get('html_content', blog_post.get('content', ''))
        preview_length = 1000
        preview = html_content[:preview_length] + "..." if len(html_content) > preview_length else html_content
        print(preview)
        print("-" * 50)
        
        # 5단계: 파일로 저장
        output_file = "generated_youtube_blog.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n💾 블로그 글이 '{output_file}' 파일로 저장되었습니다.")
        print("✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_youtube_blog_generation() 