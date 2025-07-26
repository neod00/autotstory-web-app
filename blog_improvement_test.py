import os
import time
import requests
import re
import urllib.parse
from dotenv import load_dotenv
import openai

# .env 파일 로드
load_dotenv()

# API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")
UNSPLASH_ACCESS_KEY = "uQgwi8yVjCIJmD0NNU2_2oBIHUMI8UPn2B6blxwWbvQ"

class BlogImprovementTest:
    def __init__(self):
        print("🎯 블로그 개선사항 테스트 프로그램")
        print("=" * 50)
    
    def test_smart_keywords(self, topic):
        """스마트 키워드 생성 테스트"""
        print(f"\n1️⃣ 스마트 키워드 생성 테스트: '{topic}'")
        
        try:
            prompt = f"""
            주제 '{topic}'에 대해 영문 이미지 검색에 효과적인 키워드 5개를 생성해주세요.
            
            조건:
            - 구체적이고 시각적으로 표현 가능한 키워드
            - Unsplash에서 검색 가능성이 높은 키워드
            - 다양한 관점(기술, 환경, 사회 등)을 포함
            
            형식: keyword1, keyword2, keyword3, keyword4, keyword5
            """
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            
            keywords = [k.strip() for k in response.choices[0].message.content.split(',')]
            
            print(f"✅ 생성된 키워드들:")
            for i, keyword in enumerate(keywords, 1):
                print(f"   {i}. {keyword}")
            
            return keywords
            
        except Exception as e:
            print(f"❌ 키워드 생성 실패: {e}")
            # 폴백 키워드
            fallback = ["sustainable technology", "green innovation", "environmental solution", "clean energy", "eco friendly"]
            print(f"💡 폴백 키워드 사용: {fallback}")
            return fallback
    
    def test_multiple_images(self, keywords):
        """다중 이미지 검색 테스트"""
        print(f"\n2️⃣ 다중 이미지 검색 테스트")
        
        found_images = []
        
        for i, keyword in enumerate(keywords[:3], 1):  # 처음 3개만 테스트
            print(f"   🖼️  이미지 {i} 검색: '{keyword}'")
            
            try:
                encoded_keyword = urllib.parse.quote(keyword)
                endpoint = f"https://api.unsplash.com/photos/random"
                params = {
                    "query": encoded_keyword,
                    "client_id": UNSPLASH_ACCESS_KEY,
                    "orientation": "landscape"
                }
                
                response = requests.get(endpoint, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    image_url = data.get("urls", {}).get("regular")
                    
                    if image_url:
                        found_images.append({
                            'keyword': keyword,
                            'url': image_url,
                            'alt': f"{keyword} 관련 이미지"
                        })
                        print(f"      ✅ 이미지 발견: ...{image_url[-30:]}")
                    else:
                        print(f"      ❌ 이미지 URL 없음")
                else:
                    print(f"      ❌ API 오류: {response.status_code}")
                    
            except Exception as e:
                print(f"      ❌ 검색 오류: {e}")
            
            time.sleep(1)  # API 호출 제한 방지
        
        print(f"✅ 총 {len(found_images)}개 이미지 발견")
        return found_images
    
    def test_enhanced_content_structure(self, topic):
        """향상된 콘텐츠 구조 테스트"""
        print(f"\n3️⃣ 향상된 콘텐츠 구조 테스트: '{topic}'")
        
        try:
            prompt = f"""
            주제 '{topic}'에 대한 향상된 블로그 콘텐츠를 다음 구조로 생성해주세요:
            
            1. 매력적인 제목 (30-50자)
            2. 핵심 요약 (100자 내외)
            3. 3개 주요 섹션:
               - 기본 개념 (200자)
               - 현재 동향 (200자) 
               - 실용적 적용 (200자)
            4. 결론 및 행동 유도 (100자)
            
            각 섹션에는 [이미지위치] 표시를 포함하고, HTML 구조로 작성해주세요.
            """
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # 마크다운 코드 블록 제거
            if content.startswith("```html"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            print("✅ 구조화된 콘텐츠 생성 완료")
            return content.strip()
            
        except Exception as e:
            print(f"❌ 콘텐츠 생성 실패: {e}")
            return f"<h1>{topic}</h1><p>콘텐츠 생성에 실패했습니다.</p>"
    
    def create_enhanced_html(self, topic, content, images):
        """향상된 HTML 생성"""
        print(f"\n4️⃣ 향상된 HTML 조립 테스트")
        
        # 이미지 HTML 생성
        image_html_list = []
        for img in images:
            img_html = f'''
            <div class="content-image">
                <img src="{img['url']}" alt="{img['alt']}" loading="lazy">
                <p class="image-caption">{img['keyword']} - 관련 이미지</p>
            </div>'''
            image_html_list.append(img_html)
        
        # 이미지를 콘텐츠에 삽입
        content_with_images = content
        for i, img_html in enumerate(image_html_list):
            placeholder = f"[이미지위치]"
            if placeholder in content_with_images:
                content_with_images = content_with_images.replace(placeholder, img_html, 1)
            else:
                # h2 태그 뒤에 이미지 삽입
                h2_matches = list(re.finditer(r'</h2>', content_with_images))
                if i < len(h2_matches):
                    insert_pos = h2_matches[i].end()
                    content_with_images = (content_with_images[:insert_pos] + 
                                         img_html + 
                                         content_with_images[insert_pos:])
        
        # 전체 HTML 구조
        enhanced_html = f'''
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{topic} - 개선된 블로그</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    color: #333;
                }}
                
                .blog-header {{
                    text-align: center;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 2rem;
                    border-radius: 10px;
                    margin-bottom: 2rem;
                }}
                
                .blog-title {{
                    font-size: 2.2rem;
                    margin-bottom: 0.5rem;
                }}
                
                .reading-info {{
                    background: rgba(255,255,255,0.2);
                    padding: 0.5rem 1rem;
                    border-radius: 20px;
                    display: inline-block;
                }}
                
                .highlight-box {{
                    background: #e8f5e8;
                    border-left: 4px solid #28a745;
                    padding: 1rem;
                    margin: 1.5rem 0;
                    border-radius: 5px;
                }}
                
                .content-image {{
                    text-align: center;
                    margin: 2rem 0;
                }}
                
                .content-image img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }}
                
                .image-caption {{
                    font-size: 0.9rem;
                    color: #666;
                    font-style: italic;
                    margin-top: 0.5rem;
                }}
                
                h1 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 0.5rem;
                }}
                
                h2 {{
                    color: #34495e;
                    margin-top: 2rem;
                }}
                
                .improvement-note {{
                    background: #d1ecf1;
                    border: 1px solid #17a2b8;
                    padding: 1rem;
                    margin: 2rem 0;
                    border-radius: 5px;
                }}
                
                .stats {{
                    background: #f8f9fa;
                    padding: 1rem;
                    border-radius: 5px;
                    margin: 1rem 0;
                }}
            </style>
        </head>
        <body>
            <header class="blog-header">
                <h1 class="blog-title">{topic}</h1>
                <div class="reading-info">
                    📖 개선된 블로그 구조 | 🖼️ {len(images)}개 이미지 포함
                </div>
            </header>
            
            <div class="highlight-box">
                <strong>🎯 개선 포인트:</strong> 
                이 글은 스마트 키워드 기반 이미지 검색, 구조화된 콘텐츠, 
                그리고 향상된 시각적 요소들을 적용한 개선된 버전입니다.
            </div>
            
            <main>
                {content_with_images}
            </main>
            
            <div class="improvement-note">
                <h3>🚀 적용된 개선사항</h3>
                <ul>
                    <li>✅ AI 기반 스마트 키워드 생성</li>
                    <li>✅ 다중 이미지 검색 및 배치</li>
                    <li>✅ 구조화된 HTML 및 CSS</li>
                    <li>✅ 시각적 향상 요소 (하이라이트 박스, 그라디언트 등)</li>
                    <li>✅ 반응형 디자인</li>
                </ul>
            </div>
            
            <div class="stats">
                <h4>📊 생성 통계</h4>
                <p>• 키워드 개수: {len(images)}개</p>
                <p>• 이미지 개수: {len(images)}개</p>
                <p>• 생성 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        '''
        
        print("✅ 향상된 HTML 생성 완료")
        return enhanced_html
    
    def run_full_test(self):
        """전체 테스트 실행"""
        print("\n🚀 전체 개선사항 테스트 시작!")
        
        # 테스트 주제 선택
        test_topics = [
            "기후변화와 환경 문제",
            "재생 에너지 트렌드", 
            "스마트 시티 기술",
            "전기차 시장 동향",
            "탄소중립 정책"
        ]
        
        print("\n📋 테스트 주제 선택:")
        for i, topic in enumerate(test_topics, 1):
            print(f"   {i}. {topic}")
        
        try:
            choice = input(f"\n주제를 선택하세요 (1-{len(test_topics)}): ")
            if choice.isdigit() and 1 <= int(choice) <= len(test_topics):
                selected_topic = test_topics[int(choice) - 1]
            else:
                selected_topic = test_topics[0]
                print(f"기본 주제로 설정: {selected_topic}")
        except:
            selected_topic = test_topics[0]
            print(f"기본 주제로 설정: {selected_topic}")
        
        print(f"\n✅ 선택된 주제: {selected_topic}")
        print("=" * 60)
        
        # 1. 키워드 생성 테스트
        keywords = self.test_smart_keywords(selected_topic)
        
        # 2. 이미지 검색 테스트  
        images = self.test_multiple_images(keywords)
        
        # 3. 콘텐츠 구조 테스트
        content = self.test_enhanced_content_structure(selected_topic)
        
        # 4. HTML 조립 테스트
        final_html = self.create_enhanced_html(selected_topic, content, images)
        
        # 5. 결과 저장
        filename = f"improved_blog_test_{int(time.time())}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        print(f"\n🎉 테스트 완료!")
        print(f"📄 결과 파일: {filename}")
        print(f"🌐 웹 브라우저에서 파일을 열어 결과를 확인하세요.")
        print("\n📊 테스트 결과 요약:")
        print(f"   • 생성된 키워드: {len(keywords)}개")
        print(f"   • 검색된 이미지: {len(images)}개")
        print(f"   • 파일 크기: {len(final_html)} 글자")

if __name__ == "__main__":
    # API 키 확인
    if not openai.api_key:
        print("❌ OpenAI API 키가 설정되지 않았습니다.")
        print("💡 .env 파일에 OPENAI_API_KEY를 설정해주세요.")
    else:
        tester = BlogImprovementTest()
        tester.run_full_test() 