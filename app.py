import streamlit as st
import openai
import requests
import json
import re
import time
from datetime import datetime
import os
from typing import List, Dict, Optional
import random

# URL 콘텐츠 추출 모듈 import
try:
    from url_extractor import generate_blog_from_url, URLContentExtractor
    URL_CONTENT_AVAILABLE = True
except ImportError as e:
    URL_CONTENT_AVAILABLE = False
    st.warning(f"⚠️ URL 콘텐츠 추출 모듈 로드 실패: {e}")

# 이미지 생성 모듈 import
try:
    from image_generator import get_multiple_images_v2, generate_image_html
    IMAGE_GENERATOR_AVAILABLE = True
except ImportError as e:
    IMAGE_GENERATOR_AVAILABLE = False
    st.warning(f"⚠️ 이미지 생성 모듈 로드 실패: {e}")
except Exception as e:
    IMAGE_GENERATOR_AVAILABLE = False
    st.warning(f"⚠️ 이미지 생성 모듈 초기화 실패: {e}")

# 트렌드 분석 모듈 import
try:
    from trend_analyzer import TrendAnalyzer
    TREND_ANALYZER_AVAILABLE = True
except ImportError as e:
    TREND_ANALYZER_AVAILABLE = False
    st.warning(f"⚠️ 트렌드 분석 모듈 로드 실패: {e}")

# 페이지 설정
st.set_page_config(
    page_title="AutoTstory - 블로그 자동 생성기",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .feature-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
    }
    .stTextArea > div > div > textarea {
        border-radius: 10px;
    }
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        .sub-header {
            font-size: 1.2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0

def clean_generated_content(content):
    """생성된 콘텐츠 정리"""
    if not content:
        return ""
    
    # HTML 태그 제거
    content = re.sub(r'<[^>]+>', '', content)
    
    # 불필요한 공백 정리
    content = re.sub(r'\n\s*\n', '\n\n', content)
    content = re.sub(r' +', ' ', content)
    
    # 문단 구분 정리
    content = re.sub(r'([.!?])\s*\n', r'\1\n\n', content)
    
    return content.strip()

def generate_blog_content(topic: str, custom_angle: str = "", use_ai: bool = True) -> Dict:
    """블로그 콘텐츠 생성"""
    try:
        if not use_ai or not openai.api_key:
            # 기본 템플릿 기반 생성
            return generate_basic_content(topic, custom_angle)
        
        # AI 기반 콘텐츠 생성
        prompt = f"""
'{topic}' 주제로 블로그 글을 작성해주세요.

요구사항:
1. 제목: SEO 최적화된 매력적인 제목
2. 서론: 500-600자, 독자 관심 유도
3. 본론: 2000-2500자, 실용적 정보 제공
4. 결론: 300-400자, 핵심 요약
5. 키워드: SEO용 키워드 5-8개
6. 태그: 관련 태그 3-5개

{custom_angle if custom_angle else ""}

JSON 형식으로 응답해주세요:
{{
    "title": "제목",
    "introduction": "서론",
    "main_content": "본론",
    "conclusion": "결론",
    "keywords": ["키워드1", "키워드2"],
    "tags": ["태그1", "태그2"]
}}
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000,
            temperature=0.7
        )
        
        content_text = response.choices[0].message.content.strip()
        
        # JSON 파싱 시도
        try:
            content_data = json.loads(content_text)
        except:
            # JSON 파싱 실패시 텍스트 기반 파싱
            content_data = parse_text_content(content_text, topic)
        
        return content_data
        
    except Exception as e:
        st.error(f"콘텐츠 생성 중 오류 발생: {str(e)}")
        return generate_basic_content(topic, custom_angle)

def generate_blog_from_url_v2(url: str, custom_angle: str = "") -> Dict:
    """URL 기반 블로그 콘텐츠 생성"""
    if not URL_CONTENT_AVAILABLE:
        st.error("❌ URL 콘텐츠 추출 모듈을 사용할 수 없습니다.")
        return None
    
    try:
        st.info(f"🔗 URL 기반 콘텐츠 생성 시작: {url}")
        
        # URL에서 콘텐츠 생성
        url_result = generate_blog_from_url(url, custom_angle)
        
        if not url_result['success']:
            st.error(f"❌ URL 콘텐츠 생성 실패: {url_result['error']}")
            return None
        
        # 태그 정리
        tags = url_result['tags'].strip()
        if tags:
            tags = tags.replace('#', '').strip()  # 해시태그 제거
        
        # 키워드 생성 (제목에서 추출)
        keywords = extract_keywords_from_title(url_result['title'])
        
        # 이미지 검색 (이미지 생성 기능이 사용 가능한 경우)
        images = []
        if IMAGE_GENERATOR_AVAILABLE:
            st.info("🖼️ 관련 이미지 검색 중...")
            images = get_multiple_images_v2(keywords, count=3)
        
        # V2 시스템 호환 형식으로 변환
        blog_post = {
            'title': url_result['title'],
            'introduction': url_result['content'][:600] + "..." if len(url_result['content']) > 600 else url_result['content'],
            'main_content': url_result['content'],
            'conclusion': generate_conclusion_from_content(url_result['content']),
            'keywords': keywords,
            'tags': tags.split(', ') if tags else [url_result['source_type'], '정보'],
            'images': images,
            'source_url': url_result['source_url'],
            'source_type': url_result['source_type'],
            'original_title': url_result.get('original_title', '')
        }
        
        st.success("✅ URL 기반 블로그 포스트 생성 완료!")
        return blog_post
        
    except Exception as e:
        st.error(f"❌ URL 기반 콘텐츠 생성 중 오류 발생: {e}")
        return None

def extract_keywords_from_title(title: str) -> List[str]:
    """제목에서 키워드 추출"""
    try:
        if not openai.api_key:
            return [title, "정보", "가이드"]
        
        prompt = f"""
다음 제목에서 SEO 키워드를 5-8개 추출해주세요:

제목: {title}

JSON 형식으로 응답해주세요:
{{
    "keywords": ["키워드1", "키워드2", "키워드3"]
}}
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        
        content_text = response.choices[0].message.content.strip()
        
        try:
            data = json.loads(content_text)
            return data.get('keywords', [title, "정보", "가이드"])
        except:
            return [title, "정보", "가이드"]
            
    except Exception as e:
        return [title, "정보", "가이드"]

def generate_conclusion_from_content(content: str) -> str:
    """콘텐츠에서 결론 생성"""
    try:
        if not openai.api_key:
            return content[-300:] + "..." if len(content) > 300 else content
        
        prompt = f"""
다음 콘텐츠의 결론 부분을 300-400자로 작성해주세요:

콘텐츠: {content[:1000]}

요구사항:
1. 300-400자 정도의 결론
2. 핵심 내용 요약
3. 독자에게 도움이 되는 마무리
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return content[-300:] + "..." if len(content) > 300 else content

def generate_basic_content(topic: str, custom_angle: str = "") -> Dict:
    """기본 템플릿 기반 콘텐츠 생성"""
    title = f"{topic} 완벽 가이드"
    introduction = f"""
{topic}에 대해 알아보시나요? 이 글에서는 {topic}의 모든 것을 자세히 살펴보겠습니다.

현대 사회에서 {topic}의 중요성은 날로 증가하고 있습니다. 많은 사람들이 이 주제에 대해 궁금해하고 있지만, 정확한 정보를 찾기 어려운 상황입니다.

이 글을 통해 {topic}에 대한 완전한 이해를 얻으실 수 있습니다. 실용적인 정보와 함께 실제 적용 가능한 팁들도 함께 제공하겠습니다.
""".strip()

    main_content = f"""
## {topic}의 기본 개념

{topic}는 현대 사회에서 매우 중요한 역할을 하고 있습니다. 이 섹션에서는 {topic}의 기본적인 개념과 정의에 대해 알아보겠습니다.

### 핵심 요소들

{topic}를 이해하기 위해서는 몇 가지 핵심 요소들을 파악해야 합니다:

1. **기본 원리**: {topic}의 근본적인 원리와 작동 방식
2. **주요 특징**: 다른 개념들과 구별되는 특징들
3. **적용 분야**: 실제로 활용되는 다양한 분야들

### 실무 적용 방법

이론적 이해뿐만 아니라 실제로 적용할 수 있는 방법들도 알아보겠습니다:

- **단계별 접근**: 체계적인 방법으로 {topic} 적용하기
- **주의사항**: 실무에서 주의해야 할 점들
- **성공 사례**: 실제 성공한 사례들을 통한 학습

## 최신 트렌드와 동향

{topic} 분야의 최신 동향과 트렌드를 파악하는 것도 중요합니다:

### 현재 상황

- **시장 동향**: 현재 {topic} 시장의 상황
- **기술 발전**: 최신 기술과의 결합
- **미래 전망**: 앞으로의 발전 방향

### 전문가 조언

이 분야의 전문가들이 제시하는 조언들도 함께 살펴보겠습니다:

- **전략적 접근**: 효과적인 {topic} 활용 전략
- **리스크 관리**: 주의해야 할 위험 요소들
- **성장 방향**: 지속적인 발전을 위한 방향성
""".strip()

    conclusion = f"""
{topic}에 대한 포괄적인 가이드를 마쳤습니다. 이 글을 통해 {topic}의 기본 개념부터 실무 적용까지 모든 것을 이해하셨을 것입니다.

앞으로 {topic}와 관련된 새로운 정보나 트렌드가 나올 때마다 이 글을 참고하시면 도움이 될 것입니다. 지속적인 학습과 적용을 통해 더욱 전문적인 지식을 쌓아가시기 바랍니다.

{topic}에 대한 추가 질문이나 궁금한 점이 있으시면 언제든지 문의해 주세요.
""".strip()

    keywords = [topic, f"{topic} 가이드", f"{topic} 방법", f"{topic} 팁", f"{topic} 정보"]
    tags = [topic, "가이드", "정보", "팁"]

    # 이미지 검색 (이미지 생성 기능이 사용 가능한 경우)
    images = []
    if IMAGE_GENERATOR_AVAILABLE:
        st.info("🖼️ 관련 이미지 검색 중...")
        images = get_multiple_images_v2(keywords, count=3)
    
    return {
        "title": title,
        "introduction": introduction,
        "main_content": main_content,
        "conclusion": conclusion,
        "keywords": keywords,
        "tags": tags,
        "images": images
    }

def parse_text_content(content_text: str, topic: str) -> Dict:
    """텍스트 기반 콘텐츠 파싱"""
    lines = content_text.split('\n')
    
    title = f"{topic} 완벽 가이드"
    introduction = ""
    main_content = ""
    conclusion = ""
    
    current_section = "introduction"
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if "제목:" in line or "Title:" in line:
            title = line.split(":", 1)[1].strip()
        elif "서론:" in line or "Introduction:" in line:
            current_section = "introduction"
        elif "본론:" in line or "Main:" in line:
            current_section = "main_content"
        elif "결론:" in line or "Conclusion:" in line:
            current_section = "conclusion"
        else:
            if current_section == "introduction":
                introduction += line + "\n"
            elif current_section == "main_content":
                main_content += line + "\n"
            elif current_section == "conclusion":
                conclusion += line + "\n"
    
    return {
        "title": title,
        "introduction": introduction.strip(),
        "main_content": main_content.strip(),
        "conclusion": conclusion.strip(),
        "keywords": [topic, f"{topic} 가이드"],
        "tags": [topic, "가이드"]
    }

def generate_html_content(content_data: Dict) -> str:
    """HTML 형식의 콘텐츠 생성"""
    # 이미지 HTML 생성
    images_html = ""
    if 'images' in content_data and content_data['images']:
        if IMAGE_GENERATOR_AVAILABLE:
            images_html = generate_image_html(content_data['images'])
    
    html_content = f"""
<div class="blog-post">
    <h1>{content_data['title']}</h1>
    
    {images_html}
    
    <div class="introduction">
        <h2>서론</h2>
        {content_data['introduction'].replace('\n', '<br>')}
    </div>
    
    <div class="main-content">
        {content_data['main_content'].replace('\n', '<br>')}
    </div>
    
    <div class="conclusion">
        <h2>결론</h2>
        {content_data['conclusion'].replace('\n', '<br>')}
    </div>
    
    <div class="keywords">
        <h3>키워드</h3>
        <p>{', '.join(content_data['keywords'])}</p>
    </div>
    
    <div class="tags">
        <h3>태그</h3>
        <p>{', '.join(content_data['tags'])}</p>
    </div>
</div>
"""
    return html_content

def main():
    # 헤더
    st.markdown('<h1 class="main-header">📝 AutoTstory</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI 기반 블로그 자동 생성기</p>', unsafe_allow_html=True)
    
    # 사이드바 설정
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        
        # OpenAI API 키 설정
        api_key = st.text_input("OpenAI API 키", type="password", help="AI 기능을 사용하려면 API 키를 입력하세요")
        if api_key:
            openai.api_key = api_key
            st.success("✅ API 키가 설정되었습니다")
        
        # 모드 선택
        generation_mode = st.selectbox(
            "생성 모드",
            ["AI 기반 생성", "기본 템플릿 생성"],
            help="AI 기반 생성은 더 품질 높은 콘텐츠를 제공합니다"
        )
        
        st.markdown("---")
        st.markdown("### 📊 통계")
        if st.session_state.generated_content:
            st.metric("생성된 글자 수", len(str(st.session_state.generated_content)))
    
    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<h2 class="sub-header">🎯 블로그 콘텐츠 생성</h2>', unsafe_allow_html=True)
        
        # 생성 방식 선택
        generation_type = st.radio(
            "생성 방식 선택",
            ["📝 주제 기반 생성", "🔗 URL 기반 생성"],
            help="주제를 직접 입력하거나 URL에서 콘텐츠를 추출할 수 있습니다"
        )
        
        if generation_type == "📝 주제 기반 생성":
            # 주제 기반 생성
            topic = st.text_input("주제 입력", placeholder="예: 인공지능, 마케팅 전략, 건강 관리...")
            custom_angle = st.text_area("특별한 각도나 요구사항", placeholder="원하는 특별한 관점이나 추가 요구사항이 있다면 입력하세요...")
            
            # 생성 버튼
            if st.button("🚀 블로그 생성하기", type="primary"):
                if not topic:
                    st.error("주제를 입력해주세요!")
                else:
                    with st.spinner("블로그 콘텐츠를 생성하고 있습니다..."):
                        use_ai = generation_mode == "AI 기반 생성"
                        content_data = generate_blog_content(topic, custom_angle, use_ai)
                        
                        if content_data:
                            st.session_state.generated_content = content_data
                            st.session_state.current_step = 1
                            st.success("✅ 블로그 콘텐츠가 생성되었습니다!")
        
        else:
            # URL 기반 생성
            url = st.text_input("URL 입력", placeholder="예: https://youtube.com/watch?v=..., https://news.naver.com/...")
            custom_angle = st.text_area("특별한 각도나 요구사항", placeholder="원하는 특별한 관점이나 추가 요구사항이 있다면 입력하세요...")
            
            if st.button("🚀 URL에서 블로그 생성하기", type="primary"):
                if not url:
                    st.error("URL을 입력해주세요!")
                else:
                    with st.spinner("URL에서 콘텐츠를 추출하고 블로그를 생성하고 있습니다..."):
                        content_data = generate_blog_from_url_v2(url, custom_angle)
                        
                        if content_data:
                            st.session_state.generated_content = content_data
                            st.session_state.current_step = 1
                            st.success("✅ URL 기반 블로그 콘텐츠가 생성되었습니다!")
    
    with col2:
        st.markdown('<h3 class="sub-header">📋 기능 안내</h3>', unsafe_allow_html=True)
        
        features = [
            "🤖 AI 기반 콘텐츠 생성",
            "🔗 URL 기반 콘텐츠 추출",
            "📺 YouTube 자막 추출",
            "📰 뉴스/블로그 스크래핑",
            "🖼️ Unsplash 이미지 자동 생성",
            "📝 SEO 최적화된 제목",
            "📊 구조화된 글 작성",
            "🏷️ 키워드 및 태그 자동 생성",
            "🔥 실시간 트렌드 분석",
            "📱 모바일 최적화",
            "⚡ 빠른 생성 속도"
        ]
        
        for feature in features:
            st.markdown(f"<div class='feature-box'>{feature}</div>", unsafe_allow_html=True)
    
    # 생성된 콘텐츠 표시
    if st.session_state.generated_content:
        st.markdown("---")
        st.markdown('<h2 class="sub-header">📄 생성된 콘텐츠</h2>', unsafe_allow_html=True)
        
        content = st.session_state.generated_content
        
        # 탭으로 구분
        tab1, tab2, tab3, tab4 = st.tabs(["📝 전체 보기", "📋 구조 보기", "🏷️ 메타데이터", "💾 다운로드"])
        
        with tab1:
            st.markdown(f"## {content['title']}")
            
            # 소스 정보 표시 (URL 기반 생성인 경우)
            if 'source_url' in content and content['source_url']:
                st.info(f"📎 원본 소스: {content['source_url']} ({content.get('source_type', 'unknown')})")
            
            # 이미지 표시 (이미지가 있는 경우)
            if 'images' in content and content['images']:
                st.markdown("### 🖼️ 관련 이미지")
                for i, image in enumerate(content['images']):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.image(image['url'], caption=f"{image['alt_text']} (by {image['photographer']})", use_column_width=True)
                    with col2:
                        st.markdown(f"**촬영자:** {image['photographer']}")
                        st.markdown(f"**크기:** {image['width']}x{image['height']}")
                        st.markdown(f"[Unsplash에서 보기]({image['unsplash_url']})")
            
            st.markdown("### 서론")
            st.write(content['introduction'])
            st.markdown("### 본론")
            st.write(content['main_content'])
            st.markdown("### 결론")
            st.write(content['conclusion'])
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 제목")
                st.info(content['title'])
                
                st.markdown("#### 서론")
                st.text_area("서론 내용", content['introduction'], height=200, disabled=True)
            
            with col2:
                st.markdown("#### 본론")
                st.text_area("본론 내용", content['main_content'], height=300, disabled=True)
                
                st.markdown("#### 결론")
                st.text_area("결론 내용", content['conclusion'], height=150, disabled=True)
        
        with tab3:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 키워드")
                for keyword in content['keywords']:
                    st.markdown(f"- {keyword}")
            
            with col2:
                st.markdown("#### 태그")
                for tag in content['tags']:
                    st.markdown(f"- {tag}")
        
        with tab4:
            st.markdown("### 다운로드 옵션")
            
            # JSON 다운로드
            json_data = json.dumps(content, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 JSON 파일 다운로드",
                data=json_data,
                file_name=f"blog_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            # HTML 다운로드
            html_content = generate_html_content(content)
            st.download_button(
                label="🌐 HTML 파일 다운로드",
                data=html_content,
                file_name=f"blog_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html"
            )
            
            # 텍스트 다운로드
            text_content = f"""
{content['title']}

서론:
{content['introduction']}

본론:
{content['main_content']}

결론:
{content['conclusion']}

키워드: {', '.join(content['keywords'])}
태그: {', '.join(content['tags'])}
"""
            st.download_button(
                label="📝 텍스트 파일 다운로드",
                data=text_content,
                file_name=f"blog_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

if __name__ == "__main__":
    main() 