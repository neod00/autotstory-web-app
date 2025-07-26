import streamlit as st
import openai
import json
from datetime import datetime
import utils
from typing import List, Dict

st.set_page_config(
    page_title="고급 기능 - AutoTstory",
    page_icon="⚙️",
    layout="wide"
)

def generate_faq_content(topic: str, main_content: str) -> List[Dict]:
    """FAQ 콘텐츠 생성"""
    try:
        if not openai.api_key:
            return generate_basic_faq(topic)
        
        prompt = f"""
'{topic}' 주제에 대한 FAQ(자주 묻는 질문)를 생성해주세요.

주요 콘텐츠:
{main_content[:1000]}

요구사항:
1. 5-8개의 실용적인 질문과 답변
2. 초보자부터 고급자까지 다양한 수준의 질문
3. 실제 사용자가 궁금해할 만한 내용
4. 구체적이고 실용적인 답변

JSON 형식으로 응답해주세요:
{{
    "faqs": [
        {{
            "question": "질문",
            "answer": "답변"
        }}
    ]
}}
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        content_text = response.choices[0].message.content.strip()
        
        try:
            faq_data = json.loads(content_text)
            return faq_data.get('faqs', [])
        except:
            return generate_basic_faq(topic)
            
    except Exception as e:
        st.error(f"FAQ 생성 중 오류 발생: {str(e)}")
        return generate_basic_faq(topic)

def generate_basic_faq(topic: str) -> List[Dict]:
    """기본 FAQ 생성"""
    basic_faqs = [
        {
            "question": f"{topic}란 무엇인가요?",
            "answer": f"{topic}는 현대 사회에서 매우 중요한 개념입니다. 이는 다양한 분야에서 활용되며, 실무에서도 필수적인 요소로 자리잡고 있습니다."
        },
        {
            "question": f"{topic}의 주요 장점은 무엇인가요?",
            "answer": f"{topic}의 주요 장점으로는 효율성 향상, 비용 절감, 사용자 경험 개선 등이 있습니다. 이러한 장점들은 실제 비즈니스 성과에 직접적인 영향을 미칩니다."
        },
        {
            "question": f"{topic}를 효과적으로 활용하는 방법은?",
            "answer": f"{topic}를 효과적으로 활용하기 위해서는 체계적인 접근이 필요합니다. 단계별로 학습하고, 실제 프로젝트에 적용해보는 것이 중요합니다."
        },
        {
            "question": f"{topic} 관련 주의사항은?",
            "answer": f"{topic}를 사용할 때는 몇 가지 주의사항이 있습니다. 보안, 성능, 호환성 등을 고려하여 신중하게 접근해야 합니다."
        },
        {
            "question": f"{topic}의 미래 전망은?",
            "answer": f"{topic}는 지속적으로 발전하고 있으며, 앞으로도 더욱 중요한 역할을 할 것으로 예상됩니다. 새로운 기술과의 결합으로 더욱 강력한 도구가 될 것입니다."
        }
    ]
    return basic_faqs

def generate_seo_analysis(content_data: Dict) -> Dict:
    """SEO 분석 생성"""
    analysis = {
        "title_length": len(content_data.get('title', '')),
        "title_score": 0,
        "content_length": len(content_data.get('main_content', '')),
        "content_score": 0,
        "keyword_density": {},
        "suggestions": []
    }
    
    # 제목 분석
    title = content_data.get('title', '')
    if 30 <= len(title) <= 60:
        analysis["title_score"] = 100
    elif 20 <= len(title) <= 70:
        analysis["title_score"] = 80
    else:
        analysis["title_score"] = 60
        analysis["suggestions"].append("제목 길이를 30-60자로 조정하세요.")
    
    # 콘텐츠 길이 분석
    content_length = len(content_data.get('main_content', ''))
    if content_length >= 2000:
        analysis["content_score"] = 100
    elif content_length >= 1500:
        analysis["content_score"] = 80
    elif content_length >= 1000:
        analysis["content_score"] = 60
    else:
        analysis["content_score"] = 40
        analysis["suggestions"].append("콘텐츠를 더 길게 작성하세요 (최소 1500자 권장).")
    
    # 키워드 밀도 분석
    keywords = content_data.get('keywords', [])
    content = content_data.get('main_content', '').lower()
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        count = content.count(keyword_lower)
        density = (count * len(keyword_lower)) / len(content) * 100
        analysis["keyword_density"][keyword] = {
            "count": count,
            "density": round(density, 2)
        }
    
    return analysis

def main():
    st.markdown('<h1 class="main-header">⚙️ 고급 기능</h1>', unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.markdown("### 🔧 고급 도구")
        
        if 'generated_content' in st.session_state and st.session_state.generated_content:
            st.success("✅ 콘텐츠가 생성되어 있습니다")
        else:
            st.warning("⚠️ 먼저 메인 페이지에서 콘텐츠를 생성해주세요")
    
    # 메인 컨텐츠
    if 'generated_content' not in st.session_state or not st.session_state.generated_content:
        st.info("메인 페이지에서 블로그 콘텐츠를 먼저 생성해주세요.")
        return
    
    content = st.session_state.generated_content
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["📋 FAQ 생성", "🔍 SEO 분석", "📊 콘텐츠 통계", "🎨 고급 포맷팅"])
    
    with tab1:
        st.markdown("### 📋 FAQ 생성")
        st.write("주제에 대한 자주 묻는 질문과 답변을 자동으로 생성합니다.")
        
        if st.button("🚀 FAQ 생성하기", type="primary"):
            with st.spinner("FAQ를 생성하고 있습니다..."):
                faqs = generate_faq_content(content.get('title', ''), content.get('main_content', ''))
                
                if faqs:
                    st.session_state.faqs = faqs
                    st.success(f"✅ {len(faqs)}개의 FAQ가 생성되었습니다!")
        
        if 'faqs' in st.session_state and st.session_state.faqs:
            st.markdown("#### 생성된 FAQ")
            
            for i, faq in enumerate(st.session_state.faqs, 1):
                with st.expander(f"Q{i}. {faq['question']}"):
                    st.write(faq['answer'])
            
            # FAQ 다운로드
            faq_json = json.dumps(st.session_state.faqs, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 FAQ JSON 다운로드",
                data=faq_json,
                file_name=f"faq_{utils.get_current_timestamp()}.json",
                mime="application/json"
            )
    
    with tab2:
        st.markdown("### 🔍 SEO 분석")
        st.write("생성된 콘텐츠의 SEO 최적화 상태를 분석합니다.")
        
        if st.button("🔍 SEO 분석하기", type="primary"):
            with st.spinner("SEO 분석을 진행하고 있습니다..."):
                seo_analysis = generate_seo_analysis(content)
                st.session_state.seo_analysis = seo_analysis
        
        if 'seo_analysis' in st.session_state:
            analysis = st.session_state.seo_analysis
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 기본 지표")
                
                # 제목 점수
                st.metric("제목 점수", f"{analysis['title_score']}/100")
                if analysis['title_score'] >= 80:
                    st.success("✅ 제목이 SEO에 최적화되어 있습니다")
                else:
                    st.warning("⚠️ 제목을 개선해보세요")
                
                # 콘텐츠 점수
                st.metric("콘텐츠 점수", f"{analysis['content_score']}/100")
                if analysis['content_score'] >= 80:
                    st.success("✅ 콘텐츠 길이가 적절합니다")
                else:
                    st.warning("⚠️ 콘텐츠를 더 길게 작성해보세요")
                
                # 콘텐츠 길이
                st.metric("콘텐츠 길이", f"{analysis['content_length']}자")
            
            with col2:
                st.markdown("#### 🏷️ 키워드 분석")
                
                for keyword, data in analysis['keyword_density'].items():
                    st.metric(
                        keyword, 
                        f"{data['count']}회 ({data['density']}%)"
                    )
            
            if analysis['suggestions']:
                st.markdown("#### 💡 개선 제안")
                for suggestion in analysis['suggestions']:
                    st.info(suggestion)
    
    with tab3:
        st.markdown("### 📊 콘텐츠 통계")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("제목 길이", f"{len(content.get('title', ''))}자")
            st.metric("서론 길이", f"{len(content.get('introduction', ''))}자")
        
        with col2:
            st.metric("본론 길이", f"{len(content.get('main_content', ''))}자")
            st.metric("결론 길이", f"{len(content.get('conclusion', ''))}자")
        
        with col3:
            st.metric("키워드 수", len(content.get('keywords', [])))
            st.metric("태그 수", len(content.get('tags', [])))
        
        # 읽기 시간 계산
        total_content = (
            content.get('introduction', '') + 
            content.get('main_content', '') + 
            content.get('conclusion', '')
        )
        read_time = utils.calculate_read_time(total_content)
        st.metric("예상 읽기 시간", f"{read_time}분")
        
        # 콘텐츠 분포 차트
        st.markdown("#### 📈 콘텐츠 분포")
        
        import plotly.graph_objects as go
        
        sections = ['서론', '본론', '결론']
        lengths = [
            len(content.get('introduction', '')),
            len(content.get('main_content', '')),
            len(content.get('conclusion', ''))
        ]
        
        fig = go.Figure(data=[
            go.Bar(x=sections, y=lengths, marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        ])
        
        fig.update_layout(
            title="섹션별 글자 수 분포",
            xaxis_title="섹션",
            yaxis_title="글자 수",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown("### 🎨 고급 포맷팅")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📝 마크다운 형식")
            
            markdown_content = f"""# {content.get('title', '')}

## 서론

{content.get('introduction', '')}

## 본론

{content.get('main_content', '')}

## 결론

{content.get('conclusion', '')}

### 키워드
{', '.join(content.get('keywords', []))}

### 태그
{', '.join(content.get('tags', []))}
"""
            
            st.text_area("마크다운 형식", markdown_content, height=400)
            
            st.download_button(
                label="📄 마크다운 다운로드",
                data=markdown_content,
                file_name=f"blog_{utils.get_current_timestamp()}.md",
                mime="text/markdown"
            )
        
        with col2:
            st.markdown("#### 🌐 HTML 형식")
            
            html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{content.get('title', '')}</title>
    <style>
        body {{ font-family: 'Noto Sans KR', sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 10px; }}
        h2 {{ color: #2c3e50; margin-top: 30px; }}
        .keywords, .tags {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{content.get('title', '')}</h1>
        
        <h2>서론</h2>
        <p>{content.get('introduction', '').replace(chr(10), '</p><p>')}</p>
        
        <h2>본론</h2>
        <p>{content.get('main_content', '').replace(chr(10), '</p><p>')}</p>
        
        <h2>결론</h2>
        <p>{content.get('conclusion', '').replace(chr(10), '</p><p>')}</p>
        
        <div class="keywords">
            <strong>키워드:</strong> {', '.join(content.get('keywords', []))}
        </div>
        
        <div class="tags">
            <strong>태그:</strong> {', '.join(content.get('tags', []))}
        </div>
    </div>
</body>
</html>"""
            
            st.text_area("HTML 형식", html_content, height=400)
            
            st.download_button(
                label="🌐 HTML 다운로드",
                data=html_content,
                file_name=f"blog_{utils.get_current_timestamp()}.html",
                mime="text/html"
            )

if __name__ == "__main__":
    main() 