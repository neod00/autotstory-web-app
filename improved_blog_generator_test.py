import os
import time
import json
import requests
import re
import urllib.parse
import random
from dotenv import load_dotenv
import openai

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# Unsplash API 키
UNSPLASH_ACCESS_KEY = "uQgwi8yVjCIJmD0NNU2_2oBIHUMI8UPn2B6blxwWbvQ"

print("🚀 개선된 블로그 생성기 테스트!")
print("=" * 50)

def test_basic_functions():
    """기본 기능 테스트"""
    print("📋 기본 기능 테스트 중...")
    
    # OpenAI API 연결 테스트
    try:
        test_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "안녕하세요"}],
            max_tokens=10
        )
        print("✅ OpenAI API 연결 성공")
    except Exception as e:
        print(f"❌ OpenAI API 연결 실패: {e}")
        return False
    
    # Unsplash API 테스트
    try:
        test_url = f"https://api.unsplash.com/photos/random?client_id={UNSPLASH_ACCESS_KEY}&query=nature"
        response = requests.get(test_url, timeout=5)
        if response.status_code == 200:
            print("✅ Unsplash API 연결 성공")
        else:
            print(f"❌ Unsplash API 연결 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Unsplash API 연결 실패: {e}")
        return False
    
    return True

class ImprovedBlogGenerator:
    def __init__(self):
        self.blog_topics = [
            "기후변화와 환경 문제",
            "지속 가능한 발전", 
            "재생 에너지 트렌드",
            "탄소중립 정책",
            "친환경 생활 습관",
            "스마트 시티 기술",
            "전기차 시장 동향"
        ]
    
    def generate_smart_keywords(self, topic):
        """AI를 활용한 스마트 키워드 생성"""
        try:
            prompt = f"""
            주제 '{topic}'에 대해 영문 이미지 검색에 효과적인 키워드를 생성해주세요.
            
            요구사항:
            1. 메인 키워드 1개 (가장 핵심적인 키워드)
            2. 관련 키워드 4개 (다양한 관점에서)
            3. 각 키워드는 구체적이고 시각적으로 표현 가능해야 함
            4. Unsplash에서 검색 가능성이 높아야 함
            5. 영어로 정확히 표현되어야 함
            
            응답 형식:
            메인: main_keyword
            관련: keyword1, keyword2, keyword3, keyword4
            """
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            
            result = response.choices[0].message.content.strip()
            
            # 키워드 파싱
            lines = result.split('\n')
            main_keyword = ""
            related_keywords = []
            
            for line in lines:
                if line.startswith('메인:'):
                    main_keyword = line.replace('메인:', '').strip()
                elif line.startswith('관련:'):
                    related_keywords = [k.strip() for k in line.replace('관련:', '').split(',')]
            
            return {
                'main': main_keyword,
                'related': related_keywords,
                'all': [main_keyword] + related_keywords
            }
            
        except Exception as e:
            print(f"스마트 키워드 생성 실패: {e}")
            # 폴백 키워드
            fallback_keywords = {
                '기후변화': ['climate change', 'global warming', 'environmental crisis', 'carbon footprint', 'greenhouse effect'],
                '재생에너지': ['renewable energy', 'solar panels', 'wind turbines', 'green technology', 'sustainable power'],
                '지속가능': ['sustainability', 'eco friendly', 'green living', 'environmental protection', 'sustainable development']
            }
            
            for key in fallback_keywords:
                if key in topic:
                    keywords = fallback_keywords[key]
                    return {
                        'main': keywords[0],
                        'related': keywords[1:],
                        'all': keywords
                    }
            
            return {
                'main': 'environmental technology',
                'related': ['sustainability', 'green innovation', 'eco solution', 'clean energy'],
                'all': ['environmental technology', 'sustainability', 'green innovation', 'eco solution', 'clean energy']
            }
    
    def get_multiple_images(self, topic):
        """주제별로 다양한 이미지 검색"""
        keywords_data = self.generate_smart_keywords(topic)
        images = {}
        
        print(f"🔍 생성된 키워드들:")
        print(f"   메인: {keywords_data['main']}")
        print(f"   관련: {', '.join(keywords_data['related'])}")
        
        # 메인 이미지 (hero image)
        hero_image = self.search_image(keywords_data['main'], image_type="hero")
        if hero_image:
            images['hero'] = {
                'url': hero_image,
                'keyword': keywords_data['main'],
                'alt': f"{topic} - {keywords_data['main']}",
                'caption': f"{topic}의 핵심 개념을 보여주는 이미지"
            }
        
        # 콘텐츠 이미지들 (본문 중간 삽입용)
        content_images = []
        for i, keyword in enumerate(keywords_data['related'][:3]):  # 최대 3개
            img_url = self.search_image(keyword, image_type="content")
            if img_url:
                content_images.append({
                    'url': img_url,
                    'keyword': keyword,
                    'alt': f"{topic} - {keyword}",
                    'caption': f"{keyword}과 관련된 시각적 예시"
                })
        
        images['content'] = content_images
        return images
    
    def search_image(self, keyword, image_type="general"):
        """개선된 이미지 검색"""
        try:
            encoded_keyword = urllib.parse.quote(keyword)
            
            params = {
                "query": encoded_keyword,
                "client_id": UNSPLASH_ACCESS_KEY,
                "orientation": "landscape",
                "per_page": 1
            }
            
            if image_type == "hero":
                params["featured"] = "true"
            
            endpoint = "https://api.unsplash.com/photos/random"
            
            print(f"🖼️  이미지 검색: '{keyword}' ({image_type})")
            
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                image_url = data.get("urls", {}).get("regular", "")
                if image_url:
                    print(f"   ✅ 이미지 발견: {image_url[:50]}...")
                    return image_url
                else:
                    print(f"   ❌ 이미지 URL 없음")
            else:
                print(f"   ❌ API 오류: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 이미지 검색 오류: {e}")
        
        return None
    
    def generate_enhanced_content(self, topic):
        """향상된 콘텐츠 생성"""
        print(f"\n📝 '{topic}' 주제로 향상된 블로그 콘텐츠 생성 중...")
        
        # 1. 제목 생성
        title = self.generate_title(topic)
        
        # 2. 구조화된 본문 생성  
        structured_content = self.generate_structured_content(topic)
        
        # 3. 다양한 이미지 수집
        images = self.get_multiple_images(topic)
        
        # 4. 향상된 표 생성
        enhanced_table = self.generate_enhanced_table(topic)
        
        # 5. 인터랙티브 FAQ 생성
        interactive_faq = self.generate_interactive_faq(topic)
        
        # 6. 태그 생성
        tags = self.generate_tags(topic)
        
        # 7. 통합 HTML 조립
        full_content = self.assemble_enhanced_html(
            title, structured_content, images, enhanced_table, interactive_faq
        )
        
        return {
            "title": title,
            "content": full_content,
            "tags": tags,
            "images": images,
            "word_count": self.estimate_word_count(structured_content),
            "reading_time": self.estimate_reading_time(structured_content)
        }
    
    def generate_title(self, topic):
        """매력적인 제목 생성"""
        try:
            prompt = f"""
            주제 '{topic}'에 대한 블로그 포스트의 매력적이고 클릭을 유도하는 제목을 생성해주세요.
            
            조건:
            - SEO에 효과적인 키워드 포함
            - 감정적 어필이 있는 표현 사용  
            - 30-60자 내외
            - 궁금증을 유발하는 요소 포함
            
            제목만 작성하고 따옴표는 제외하세요.
            """
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"제목 생성 오류: {e}")
            return f"{topic}에 대해 알아야 할 모든 것"
    
    def generate_structured_content(self, topic):
        """구조화된 본문 생성"""
        try:
            prompt = f"""
            주제 '{topic}'에 대한 구조화된 블로그 본문을 작성해주세요.
            
            구조:
            1. 도입부 (150-200자): 독자의 관심을 끌고 문제를 제기
            2. 핵심 내용 3개 섹션 (각 200-300자):
               - 첫 번째 섹션: 기본 개념 설명
               - 두 번째 섹션: 현황 및 트렌드 분석  
               - 세 번째 섹션: 실용적인 적용 방안
            3. 결론 (100-150자): 요약 및 행동 유도
            
            요구사항:
            - 각 섹션에는 <h2> 태그로 소제목 포함
            - 중요한 내용은 <strong> 태그로 강조
            - 문단은 <p> 태그로 구분
            - 리스트가 필요한 부분은 <ul><li> 사용
            - [IMAGE_PLACEHOLDER_1], [IMAGE_PLACEHOLDER_2] 등으로 이미지 삽입 위치 표시
            
            HTML 형식으로 작성하되 DOCTYPE, html, head, body 태그는 제외하세요.
            """
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # 마크다운 코드 블록 제거
            if content.startswith("```html") and content.endswith("```"):
                content = content[7:-3].strip()
            elif content.startswith("```") and content.endswith("```"):
                content = content[3:-3].strip()
            
            return content
            
        except Exception as e:
            print(f"본문 생성 오류: {e}")
            return f"<h2>개요</h2><p>{topic}에 대한 기본적인 내용을 다룹니다.</p>"
    
    def generate_enhanced_table(self, topic):
        """향상된 표 생성"""
        try:
            prompt = f"""
            주제 '{topic}'와 관련된 데이터 표를 생성해주세요.
            
            요구사항:
            - 실제적이고 유용한 데이터 포함
            - 4-6개 행, 3-4개 열
            - 표 제목(<caption>) 포함
            - 시각적으로 구분되는 헤더
            - 숫자 데이터가 있다면 단위 명시
            
            HTML <table> 구조로 작성하고, 스타일링을 위한 클래스 포함:
            - <table class="data-table">
            - <thead class="table-header">  
            - <tbody class="table-body">
            """
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            
            table_html = response.choices[0].message.content.strip()
            
            # 마크다운 코드 블록 제거
            if table_html.startswith("```html") and table_html.endswith("```"):
                table_html = table_html[7:-3].strip()
            elif table_html.startswith("```") and table_html.endswith("```"):
                table_html = table_html[3:-3].strip()
            
            return table_html
            
        except Exception as e:
            print(f"표 생성 오류: {e}")
            return f'<table class="data-table"><caption>{topic} 관련 데이터</caption><thead><tr><th>항목</th><th>값</th></tr></thead><tbody><tr><td>예시 데이터</td><td>예시 값</td></tr></tbody></table>'
    
    def generate_interactive_faq(self, topic):
        """인터랙티브 FAQ 생성"""
        try:
            prompt = f"""
            주제 '{topic}'와 관련해 독자들이 자주 묻는 4-5가지 질문과 상세한 답변을 작성해주세요.
            
            요구사항:
            - 실용적이고 구체적인 질문들
            - 각 답변은 100-150자 내외
            - 접을 수 있는 형태로 구현 (<details><summary> 사용)
            - 질문에는 관련 이모지 포함
            
            HTML 구조:
            <div class="faq-container">
                <details class="faq-item">
                    <summary class="faq-question">🤔 질문 내용</summary>
                    <div class="faq-answer">
                        <p>답변 내용</p>
                    </div>
                </details>
            </div>
            """
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800
            )
            
            faq_html = response.choices[0].message.content.strip()
            
            # 마크다운 코드 블록 제거
            if faq_html.startswith("```html") and faq_html.endswith("```"):
                faq_html = faq_html[7:-3].strip()
            elif faq_html.startswith("```") and faq_html.endswith("```"):
                faq_html = faq_html[3:-3].strip()
            
            return faq_html
            
        except Exception as e:
            print(f"FAQ 생성 오류: {e}")
            return f'<div class="faq-container"><details class="faq-item"><summary class="faq-question">🤔 {topic}에 대해 더 알고 싶습니다</summary><div class="faq-answer"><p>추가 정보를 원하시면 관련 자료를 참고해주세요.</p></div></details></div>'
    
    def generate_tags(self, topic):
        """SEO 효과적인 태그 생성"""
        try:
            prompt = f"'{topic}' 주제로 SEO에 효과적인 7개 태그를 쉼표로 나열해주세요. 태그는 구체적이고 검색 가능성이 높아야 합니다."
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"태그 생성 오류: {e}")
            return f"{topic}, 환경, 지속가능성, 트렌드, 분석"
    
    def assemble_enhanced_html(self, title, content, images, table, faq):
        """향상된 HTML 구조 조립"""
        
        # 이미지 HTML 생성
        hero_image_html = ""
        if images.get('hero'):
            hero_img = images['hero']
            hero_image_html = f'''
            <div class="hero-image-container">
                <img src="{hero_img['url']}" 
                     alt="{hero_img['alt']}" 
                     class="hero-image"
                     loading="eager">
                <div class="image-caption">{hero_img['caption']}</div>
            </div>'''
        
        # 콘텐츠 이미지들을 본문에 삽입
        content_with_images = content
        if images.get('content'):
            for i, img in enumerate(images['content']):
                placeholder = f"[IMAGE_PLACEHOLDER_{i+1}]"
                img_html = f'''
                <div class="content-image-container">
                    <img src="{img['url']}" 
                         alt="{img['alt']}" 
                         class="content-image"
                         loading="lazy">
                    <div class="image-caption">{img['caption']}</div>
                </div>'''
                
                if placeholder in content_with_images:
                    content_with_images = content_with_images.replace(placeholder, img_html)
                else:
                    # 적절한 위치에 이미지 삽입 (h2 태그 뒤)
                    h2_matches = list(re.finditer(r'</h2>', content_with_images))
                    if i < len(h2_matches):
                        insert_pos = h2_matches[i].end()
                        content_with_images = (content_with_images[:insert_pos] + 
                                             img_html + 
                                             content_with_images[insert_pos:])
        
        # CSS 스타일 정의
        css_styles = '''
        <style>
        .blog-post {
            max-width: 800px;
            margin: 0 auto;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        
        .post-header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }
        
        .post-title {
            font-size: 2.2rem;
            margin-bottom: 0.5rem;
            font-weight: bold;
        }
        
        .post-meta {
            display: flex;
            justify-content: center;
            gap: 1rem;
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .reading-time {
            background: rgba(255,255,255,0.2);
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
        }
        
        .hero-image-container {
            text-align: center;
            margin: 2rem 0;
        }
        
        .hero-image {
            width: 100%;
            max-width: 600px;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .content-image-container {
            text-align: center;
            margin: 1.5rem 0;
        }
        
        .content-image {
            width: 100%;
            max-width: 500px;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .image-caption {
            font-size: 0.9rem;
            color: #666;
            font-style: italic;
            margin-top: 0.5rem;
        }
        
        .content-outline {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
            margin: 2rem 0;
            border-left: 4px solid #007bff;
        }
        
        .outline-list {
            margin: 1rem 0 0 0;
            padding-left: 1.5rem;
        }
        
        .outline-list li {
            margin: 0.5rem 0;
        }
        
        .highlight-box {
            background: #e8f5e8;
            border: 1px solid #28a745;
            border-radius: 8px;
            padding: 1rem;
            margin: 1.5rem 0;
            display: flex;
            align-items: flex-start;
            gap: 0.8rem;
        }
        
        .highlight-box.warning {
            background: #fff3cd;
            border-color: #ffc107;
        }
        
        .highlight-box.info {
            background: #d1ecf1;
            border-color: #17a2b8;
        }
        
        .box-icon {
            font-size: 1.2rem;
            line-height: 1;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 2rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .data-table caption {
            font-size: 1.1rem;
            font-weight: bold;
            padding: 1rem;
            background: #f8f9fa;
            border-bottom: 2px solid #dee2e6;
        }
        
        .data-table th {
            background: #007bff;
            color: white;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
        }
        
        .data-table td {
            padding: 0.8rem 1rem;
            border-bottom: 1px solid #dee2e6;
        }
        
        .data-table tbody tr:hover {
            background: #f8f9fa;
        }
        
        .faq-container {
            margin: 2rem 0;
        }
        
        .faq-item {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            margin-bottom: 1rem;
            overflow: hidden;
        }
        
        .faq-question {
            background: #f8f9fa;
            padding: 1rem;
            cursor: pointer;
            font-weight: 600;
            border: none;
            width: 100%;
            text-align: left;
            transition: background-color 0.3s;
        }
        
        .faq-question:hover {
            background: #e9ecef;
        }
        
        .faq-answer {
            padding: 1rem;
            background: white;
        }
        
        .section-divider {
            border: none;
            height: 2px;
            background: linear-gradient(to right, transparent, #ddd, transparent);
            margin: 3rem 0;
        }
        
        @media (max-width: 768px) {
            .blog-post {
                margin: 1rem;
            }
            
            .post-title {
                font-size: 1.8rem;
            }
            
            .post-meta {
                flex-direction: column;
                gap: 0.5rem;
            }
        }
        </style>
        '''
        
        # 전체 HTML 조립
        full_html = f'''
        {css_styles}
        
        <article class="blog-post">
            <header class="post-header">
                <h1 class="post-title">{title}</h1>
                <div class="post-meta">
                    <span class="reading-time">📖 {self.estimate_reading_time(content)}분 읽기</span>
                    <span class="word-count">📄 약 {self.estimate_word_count(content)}자</span>
                </div>
            </header>
            
            {hero_image_html}
            
            <div class="content-outline">
                <h3>📋 이 글에서 다룰 내용</h3>
                <ul class="outline-list">
                    <li>핵심 개념과 정의</li>
                    <li>현재 동향 및 트렌드 분석</li>
                    <li>실용적인 적용 방안</li>
                    <li>자주 묻는 질문과 답변</li>
                </ul>
            </div>
            
            <div class="highlight-box">
                <div class="box-icon">💡</div>
                <div class="box-content">
                    <strong>핵심 포인트:</strong> 이 글을 통해 {title.replace('?', '').replace('!', '')}에 대한 종합적인 이해를 얻으실 수 있습니다.
                </div>
            </div>
            
            <main class="post-content">
                {content_with_images}
            </main>
            
            <hr class="section-divider">
            
            <section class="data-section">
                <h2>📊 관련 데이터</h2>
                {table}
            </section>
            
            <hr class="section-divider">
            
            <section class="faq-section">
                <h2>❓ 자주 묻는 질문</h2>
                {faq}
            </section>
            
            <div class="highlight-box info">
                <div class="box-icon">🎯</div>
                <div class="box-content">
                    <strong>다음 단계:</strong> 이 정보를 바탕으로 실제 적용 방안을 고려해 보시기 바랍니다.
                </div>
            </div>
        </article>
        '''
        
        return full_html
    
    def estimate_word_count(self, content):
        """글자 수 추정"""
        text_only = re.sub(r'<[^>]+>', '', content)
        return len(text_only.replace(' ', ''))
    
    def estimate_reading_time(self, content):
        """읽기 시간 추정 (분)"""
        word_count = self.estimate_word_count(content)
        reading_speed = 350
        minutes = max(1, round(word_count / reading_speed))
        return minutes
    
    def save_test_result(self, result, filename):
        """테스트 결과를 HTML 파일로 저장"""
        html_content = f'''
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{result["title"]}</title>
        </head>
        <body>
            {result["content"]}
        </body>
        </html>
        '''
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 테스트 결과가 '{filename}' 파일로 저장되었습니다.")
        
        # 결과 요약 출력
        print(f"\n📊 생성된 콘텐츠 정보:")
        print(f"   제목: {result['title']}")
        print(f"   글자 수: 약 {result['word_count']}자")
        print(f"   읽기 시간: {result['reading_time']}분")
        print(f"   태그: {result['tags']}")
        if result['images'].get('hero'):
            print(f"   메인 이미지: ✅")
        if result['images'].get('content'):
            print(f"   콘텐츠 이미지: {len(result['images']['content'])}개")
    
    def run_test(self):
        """테스트 실행"""
        print("🚀 개선된 블로그 생성기 테스트 시작!")
        print("=" * 60)
        
        # 사용자가 주제 선택
        print("\n📋 사용 가능한 주제들:")
        for i, topic in enumerate(self.blog_topics, 1):
            print(f"   {i}. {topic}")
        
        print(f"   {len(self.blog_topics) + 1}. 직접 입력")
        
        try:
            choice = input(f"\n주제를 선택하세요 (1-{len(self.blog_topics) + 1}): ")
            
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(self.blog_topics):
                    selected_topic = self.blog_topics[choice_num - 1]
                elif choice_num == len(self.blog_topics) + 1:
                    selected_topic = input("주제를 직접 입력하세요: ")
                else:
                    print("잘못된 선택입니다. 첫 번째 주제로 진행합니다.")
                    selected_topic = self.blog_topics[0]
            else:
                print("잘못된 입력입니다. 첫 번째 주제로 진행합니다.")
                selected_topic = self.blog_topics[0]
        except:
            selected_topic = self.blog_topics[0]
        
        print(f"\n✅ 선택된 주제: {selected_topic}")
        print("=" * 60)
        
        # 콘텐츠 생성
        start_time = time.time()
        result = self.generate_enhanced_content(selected_topic)
        generation_time = time.time() - start_time
        
        print(f"\n⏱️  생성 시간: {generation_time:.2f}초")
        
        # 결과 저장
        filename = f"test_blog_{int(time.time())}.html"
        self.save_test_result(result, filename)
        
        print(f"\n🎉 테스트 완료! 웹 브라우저에서 '{filename}' 파일을 열어 결과를 확인하세요.")

if __name__ == "__main__":
    generator = ImprovedBlogGenerator()
    generator.run_test() 