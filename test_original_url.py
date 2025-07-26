#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append('.')

# 파일명에 하이픈이 있으므로 importlib 사용
import importlib.util

# 파일 로드
spec = importlib.util.spec_from_file_location("test_module", "auto_post_generator_v2_complete-BOOK-BF7VOMCU5L.py")
test_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_module)

# 함수 가져오기
generate_blog_from_url_v2 = test_module.generate_blog_from_url_v2

# 테스트 실행
print("🧪 원본 URL로 수정된 코드 테스트 시작...")

try:
    # 원본과 같은 URL 사용 (ETF 관련)
    test_url = 'https://www.youtube.com/watch?v=example_etf_video'  # 실제 ETF 관련 URL로 변경 필요
    
    # 또는 다른 테스트 URL 사용
    test_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    
    result = generate_blog_from_url_v2(test_url)
    
    if result:
        print('✅ 블로그 포스트 생성 성공!')
        print(f'제목: {result["title"]}')
        print(f'본문 길이: {len(result["content"])}')
        
        # 수정된 HTML 파일로 저장
        with open('fixed_url_preview.html', 'w', encoding='utf-8') as f:
            f.write(result['content'])
        print('📄 fixed_url_preview.html 파일로 저장됨')
        
        # 본문 내용 확인
        if '<article' in result['content'] and '</article>' in result['content']:
            # 빈 article 태그가 아닌지 확인
            if '<article style="color: #555; font-size: 1.1rem; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;"></article>' not in result['content']:
                print('✅ 본문 내용이 포함되어 있습니다.')
            else:
                print('⚠️ 본문 내용이 비어있습니다.')
        else:
            print('⚠️ 본문 구조가 올바르지 않습니다.')
            
    else:
        print('❌ 블로그 포스트 생성 실패')
        
except Exception as e:
    print(f'❌ 오류 발생: {e}')
    import traceback
    traceback.print_exc() 