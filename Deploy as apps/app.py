import streamlit as st
import os
import time
import json
from datetime import datetime
from auth import authenticate_user, check_authentication
from tistory_automation import TistoryAutomation
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="티스토리 자동 포스팅 시스템",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application function"""
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'automation' not in st.session_state:
        st.session_state.automation = None
    if 'posting_in_progress' not in st.session_state:
        st.session_state.posting_in_progress = False
    if 'posting_results' not in st.session_state:
        st.session_state.posting_results = []
    
    # Authentication check
    if not check_authentication():
        show_login_page()
        return
    
    # Main application interface
    show_main_interface()

def show_login_page():
    """Display login page"""
    st.title("🔐 티스토리 자동 포스팅 시스템")
    st.subheader("보안 로그인")
    
    # Check if required environment variables are set
    required_vars = ['APP_PASSWORD', 'OPENAI_API_KEY', 'UNSPLASH_ACCESS_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        st.error(f"⚠️ 필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        st.info("📋 Streamlit Secrets에서 필요한 키들을 설정해주세요.")
        st.code("""
# Streamlit Secrets 설정 예시
APP_PASSWORD = "your_secure_password"
OPENAI_API_KEY = "sk-your-openai-key"
UNSPLASH_ACCESS_KEY = "your-unsplash-key"
        """)
        return
    
    with st.form("login_form"):
        password = st.text_input("패스워드", type="password", placeholder="보안 패스워드를 입력하세요")
        submit_button = st.form_submit_button("🚀 로그인")
        
        if submit_button:
            if authenticate_user(password):
                st.session_state.authenticated = True
                st.success("✅ 로그인 성공!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ 잘못된 패스워드입니다.")

def show_main_interface():
    """Display main application interface"""
    
    # Header
    st.title("📝 티스토리 자동 포스팅 시스템")
    st.markdown("---")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("🎛️ 제어 패널")
        
        # Logout button
        if st.button("🚪 로그아웃", type="secondary"):
            st.session_state.authenticated = False
            st.session_state.automation = None
            st.rerun()
        
        st.markdown("---")
        
        # System status
        st.subheader("📊 시스템 상태")
        if st.session_state.automation:
            st.success("✅ 자동화 시스템 준비됨")
        else:
            st.info("🔄 자동화 시스템 초기화 중...")
            
        # API status check
        check_api_status()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🚀 포스팅 실행")
        
        # Initialize automation if not already done
        if not st.session_state.automation:
            try:
                with st.spinner("자동화 시스템 초기화 중..."):
                    st.session_state.automation = TistoryAutomation()
                st.success("✅ 자동화 시스템이 준비되었습니다!")
            except Exception as e:
                st.error(f"❌ 자동화 시스템 초기화 실패: {str(e)}")
                return
        
        # Topic input form
        with st.form("posting_form"):
            topic = st.text_input(
                "📝 블로그 주제",
                placeholder="예: 습기 제거 방법, 기후변화 대응책, 재생에너지 동향 등",
                help="AI가 이 주제를 바탕으로 완전한 블로그 포스트를 생성합니다."
            )
            
            # Advanced options
            with st.expander("🔧 고급 설정"):
                image_count = st.slider("이미지 개수", min_value=1, max_value=5, value=3)
                generate_table = st.checkbox("정보 표 생성", value=True)
                generate_faq = st.checkbox("FAQ 섹션 생성", value=True)
            
            submit_button = st.form_submit_button(
                "🚀 포스팅 시작", 
                disabled=st.session_state.posting_in_progress
            )
            
            if submit_button and topic:
                if not st.session_state.posting_in_progress:
                    execute_posting(topic, image_count, generate_table, generate_faq)
                else:
                    st.warning("⚠️ 포스팅이 이미 진행 중입니다.")
            elif submit_button and not topic:
                st.error("❌ 블로그 주제를 입력해주세요.")
    
    with col2:
        st.header("📋 포스팅 기록")
        display_posting_history()

def check_api_status():
    """Check API status and display in sidebar"""
    st.subheader("🔌 API 상태")
    
    # OpenAI API
    if os.getenv('OPENAI_API_KEY'):
        st.success("✅ OpenAI API")
    else:
        st.error("❌ OpenAI API 키 없음")
    
    # Unsplash API
    if os.getenv('UNSPLASH_ACCESS_KEY'):
        st.success("✅ Unsplash API")
    else:
        st.error("❌ Unsplash API 키 없음")
    
    # 배포 환경 안내
    st.markdown("---")
    st.subheader("🌐 배포 환경")
    
    # Streamlit Share 환경 감지
    try:
        import platform
        is_streamlit_share = "streamlit" in str(platform.platform()).lower() or os.getenv("STREAMLIT_SHARING", "false").lower() == "true"
        
        if is_streamlit_share:
            st.info("🌐 Streamlit Share에서 실행 중")
            st.warning("⚠️ 브라우저 자동화는 테스트 모드로만 동작합니다")
        else:
            st.success("💻 로컬 환경에서 실행 중")
    except:
        st.info("🔍 환경 감지 중...")
    
    # 테스트 모드 표시
    if os.getenv("TEST_MODE", "false").lower() == "true":
        st.warning("🧪 테스트 모드 활성화됨")
    else:
        st.info("🚀 실제 포스팅 모드")

def execute_posting(topic, image_count, generate_table, generate_faq):
    """Execute the posting process with real-time updates"""
    
    st.session_state.posting_in_progress = True
    
    # Create progress containers
    progress_container = st.container()
    log_container = st.container()
    
    with progress_container:
        st.subheader("⏳ 포스팅 진행 상황")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
    with log_container:
        st.subheader("📜 실시간 로그")
        log_placeholder = st.empty()
        
    logs = []
    
    try:
        # Step 1: Generate content
        status_text.text("🤖 AI 콘텐츠 생성 중...")
        progress_bar.progress(20)
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] AI 콘텐츠 생성 시작")
        log_placeholder.text_area("로그", "\n".join(logs), height=200)
        
        content_data = st.session_state.automation.generate_content(topic)
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 콘텐츠 생성 완료")
        log_placeholder.text_area("로그", "\n".join(logs), height=200)
        
        # Step 2: Search images
        status_text.text("🖼️ 이미지 검색 중...")
        progress_bar.progress(40)
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 이미지 검색 시작")
        log_placeholder.text_area("로그", "\n".join(logs), height=200)
        
        images = st.session_state.automation.search_images(topic, image_count)
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {len(images)}개 이미지 검색 완료")
        log_placeholder.text_area("로그", "\n".join(logs), height=200)
        
        # Step 3: Generate HTML
        status_text.text("📄 HTML 생성 중...")
        progress_bar.progress(60)
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] HTML 생성 시작")
        log_placeholder.text_area("로그", "\n".join(logs), height=200)
        
        html_content = st.session_state.automation.generate_html(topic, images, content_data)
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ HTML 생성 완료")
        log_placeholder.text_area("로그", "\n".join(logs), height=200)
        
        # Step 4: Post to Tistory
        status_text.text("📤 티스토리에 포스팅 중...")
        progress_bar.progress(80)
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 티스토리 포스팅 시작")
        log_placeholder.text_area("로그", "\n".join(logs), height=200)
        
        result = st.session_state.automation.post_to_tistory(content_data['title'], html_content)
        
        # Step 5: Complete
        progress_bar.progress(100)
        status_text.text("✅ 포스팅 완료!")
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 포스팅 완료!")
        log_placeholder.text_area("로그", "\n".join(logs), height=200)
        
        # Save result
        posting_result = {
            'timestamp': datetime.now().isoformat(),
            'topic': topic,
            'title': content_data['title'],
            'status': 'success' if result else 'failed',
            'logs': logs.copy()
        }
        st.session_state.posting_results.append(posting_result)
        
        if result:
            st.success("🎉 포스팅이 성공적으로 완료되었습니다!")
        else:
            st.error("❌ 포스팅 중 오류가 발생했습니다.")
            
    except Exception as e:
        progress_bar.progress(100)
        status_text.text("❌ 오류 발생")
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 오류: {str(e)}")
        log_placeholder.text_area("로그", "\n".join(logs), height=200)
        
        # Save error result
        posting_result = {
            'timestamp': datetime.now().isoformat(),
            'topic': topic,
            'title': f"오류: {topic}",
            'status': 'error',
            'error': str(e),
            'logs': logs.copy()
        }
        st.session_state.posting_results.append(posting_result)
        
        st.error(f"❌ 포스팅 중 오류가 발생했습니다: {str(e)}")
    
    finally:
        st.session_state.posting_in_progress = False

def display_posting_history():
    """Display posting history"""
    
    if not st.session_state.posting_results:
        st.info("📝 아직 포스팅 기록이 없습니다.")
        return
    
    # Display recent results
    for i, result in enumerate(reversed(st.session_state.posting_results[-5:])):
        with st.expander(f"📄 {result['title'][:30]}... ({result['timestamp'][:16]})"):
            if result['status'] == 'success':
                st.success("✅ 성공")
            elif result['status'] == 'failed':
                st.error("❌ 실패")
            else:
                st.error(f"💥 오류: {result.get('error', 'Unknown error')}")
            
            st.text(f"주제: {result['topic']}")
            st.text(f"시간: {result['timestamp']}")
            
            if st.button(f"로그 보기", key=f"log_{i}"):
                st.text_area("상세 로그", "\n".join(result['logs']), height=150)

if __name__ == "__main__":
    main()
