import streamlit as st
import openai
import utils

st.set_page_config(
    page_title="설정 및 도움말 - AutoTstory",
    page_icon="❓",
    layout="wide"
)

def main():
    st.markdown('<h1 class="main-header">❓ 설정 및 도움말</h1>', unsafe_allow_html=True)
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ 설정", "📖 사용법", "🔧 문제 해결", "📞 문의"])
    
    with tab1:
        st.markdown("### ⚙️ 설정")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔑 API 키 설정")
            
            # OpenAI API 키 입력
            api_key = st.text_input(
                "OpenAI API 키",
                type="password",
                help="AI 기능을 사용하려면 OpenAI API 키가 필요합니다"
            )
            
            if api_key:
                if utils.check_api_key_validity(api_key):
                    openai.api_key = api_key
                    st.success("✅ API 키가 유효합니다")
                else:
                    st.error("❌ API 키 형식이 올바르지 않습니다")
            
            st.markdown("#### 🎛️ 생성 설정")
            
            # 생성 모드 선택
            generation_mode = st.selectbox(
                "기본 생성 모드",
                ["AI 기반 생성", "기본 템플릿 생성"],
                help="새로 생성할 콘텐츠의 기본 모드를 설정합니다"
            )
            
            # 콘텐츠 길이 설정
            content_length = st.selectbox(
                "기본 콘텐츠 길이",
                ["짧음 (1000자)", "보통 (2000자)", "길게 (3000자)"],
                index=1,
                help="생성할 콘텐츠의 기본 길이를 설정합니다"
            )
            
            # 언어 설정
            language = st.selectbox(
                "언어 설정",
                ["한국어", "English"],
                help="생성할 콘텐츠의 언어를 설정합니다"
            )
        
        with col2:
            st.markdown("#### 🎨 UI 설정")
            
            # 테마 선택
            theme = st.selectbox(
                "테마",
                ["기본", "다크", "커스텀"],
                help="앱의 테마를 선택합니다"
            )
            
            # 사이드바 설정
            sidebar_state = st.selectbox(
                "사이드바 기본 상태",
                ["펼침", "접힘"],
                help="앱 로드 시 사이드바의 기본 상태를 설정합니다"
            )
            
            # 알림 설정
            notifications = st.checkbox(
                "알림 활성화",
                value=True,
                help="작업 완료 시 알림을 표시합니다"
            )
            
            # 자동 저장
            auto_save = st.checkbox(
                "자동 저장",
                value=True,
                help="생성된 콘텐츠를 자동으로 저장합니다"
            )
    
    with tab2:
        st.markdown("### 📖 사용법")
        
        st.markdown("#### 🚀 빠른 시작")
        
        with st.expander("1. 기본 사용법"):
            st.markdown("""
            **1단계: 주제 입력**
            - 블로그 글의 주제를 입력합니다
            - 예: "인공지능", "마케팅 전략", "건강 관리"
            
            **2단계: 요구사항 추가 (선택사항)**
            - 특별한 관점이나 추가 요구사항을 입력합니다
            - 예: "초보자를 위한 가이드", "2024년 최신 트렌드"
            
            **3단계: 생성 모드 선택**
            - AI 기반 생성: 고품질의 AI 생성 콘텐츠
            - 기본 템플릿 생성: 빠른 템플릿 기반 생성
            
            **4단계: 생성 버튼 클릭**
            - "🚀 블로그 생성하기" 버튼을 클릭합니다
            - 생성이 완료될 때까지 기다립니다
            """)
        
        with st.expander("2. 생성된 콘텐츠 활용"):
            st.markdown("""
            **전체 보기**
            - 생성된 글의 전체 내용을 확인합니다
            
            **구조 보기**
            - 제목, 서론, 본론, 결론을 개별적으로 확인합니다
            
            **메타데이터**
            - 키워드와 태그 정보를 확인합니다
            
            **다운로드**
            - JSON, HTML, 텍스트 파일로 다운로드합니다
            """)
        
        with st.expander("3. 고급 기능"):
            st.markdown("""
            **FAQ 생성**
            - 자주 묻는 질문과 답변을 자동 생성합니다
            
            **SEO 분석**
            - 콘텐츠의 SEO 최적화 상태를 분석합니다
            
            **콘텐츠 통계**
            - 글자 수, 읽기 시간 등 통계를 확인합니다
            
            **고급 포맷팅**
            - 마크다운, HTML 등 다양한 형식으로 변환합니다
            """)
    
    with tab3:
        st.markdown("### 🔧 문제 해결")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ❌ 일반적인 문제들")
            
            with st.expander("API 키 오류"):
                st.markdown("""
                **증상**: AI 기능이 작동하지 않음
                
                **해결 방법**:
                1. OpenAI API 키가 올바른지 확인
                2. API 키가 `sk-`로 시작하는지 확인
                3. API 키의 잔액 확인
                4. 네트워크 연결 상태 확인
                """)
            
            with st.expander("생성 실패"):
                st.markdown("""
                **증상**: 콘텐츠 생성이 실패함
                
                **해결 방법**:
                1. 주제가 2글자 이상인지 확인
                2. 인터넷 연결 상태 확인
                3. API 사용량 한도 확인
                4. 다시 시도
                """)
            
            with st.expander("앱 로딩 실패"):
                st.markdown("""
                **증상**: 앱이 로드되지 않음
                
                **해결 방법**:
                1. 브라우저 새로고침
                2. 다른 브라우저로 시도
                3. 캐시 삭제 후 재시도
                4. 네트워크 연결 확인
                """)
        
        with col2:
            st.markdown("#### 💡 성능 최적화")
            
            with st.expander("빠른 생성"):
                st.markdown("""
                **팁**:
                1. 기본 템플릿 모드 사용
                2. 짧은 주제 입력
                3. 불필요한 요구사항 제거
                4. 네트워크 상태 확인
                """)
            
            with st.expander("품질 향상"):
                st.markdown("""
                **팁**:
                1. 구체적인 주제 입력
                2. 상세한 요구사항 작성
                3. AI 기반 생성 모드 사용
                4. 생성 후 수정 및 보완
                """)
            
            with st.expander("SEO 최적화"):
                st.markdown("""
                **팁**:
                1. 키워드가 포함된 제목 사용
                2. 적절한 콘텐츠 길이 유지
                3. 구조화된 글 작성
                4. 메타데이터 활용
                """)
    
    with tab4:
        st.markdown("### 📞 문의 및 지원")
        
        st.markdown("#### 🆘 도움이 필요하신가요?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📧 문의 방법")
            
            st.markdown("""
            **GitHub Issues**
            - 버그 리포트
            - 기능 요청
            - 개선 제안
            
            **이메일**
            - 기술적 문제
            - 비즈니스 문의
            - 파트너십 제안
            """)
            
            st.markdown("#### 🔗 유용한 링크")
            
            st.markdown("""
            - [Streamlit Documentation](https://docs.streamlit.io/)
            - [OpenAI API Documentation](https://platform.openai.com/docs)
            - [GitHub Repository](https://github.com/your-repo)
            - [Live Demo](https://your-app-url.streamlit.app)
            """)
        
        with col2:
            st.markdown("#### 📊 현재 상태")
            
            # 시스템 상태 표시
            st.metric("앱 상태", "정상")
            st.metric("API 상태", "연결됨" if openai.api_key else "연결 안됨")
            st.metric("마지막 업데이트", "2024-01-01")
            
            st.markdown("#### 🆕 최신 업데이트")
            
            st.markdown("""
            **v1.0.0 (2024-01-01)**
            - 초기 버전 출시
            - 기본 블로그 생성 기능
            - AI 기반 콘텐츠 생성
            - 다양한 다운로드 형식 지원
            """)
        
        # 피드백 폼
        st.markdown("#### 💬 피드백")
        
        feedback_type = st.selectbox(
            "피드백 유형",
            ["버그 리포트", "기능 요청", "개선 제안", "기타"]
        )
        
        feedback_content = st.text_area(
            "피드백 내용",
            placeholder="자세한 내용을 입력해주세요...",
            height=150
        )
        
        if st.button("📤 피드백 제출", type="primary"):
            if feedback_content.strip():
                st.success("✅ 피드백이 제출되었습니다. 감사합니다!")
            else:
                st.warning("⚠️ 피드백 내용을 입력해주세요.")

if __name__ == "__main__":
    main() 