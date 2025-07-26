import os
import hashlib
import streamlit as st
from datetime import datetime, timedelta

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(password: str) -> bool:
    """Authenticate user with password"""
    stored_password = os.getenv('APP_PASSWORD')
    
    if not stored_password:
        st.error("⚠️ APP_PASSWORD 환경변수가 설정되지 않았습니다.")
        return False
    
    # For simplicity, we'll compare directly (in production, use hashed passwords)
    if password == stored_password:
        # Set session authentication
        st.session_state.authenticated = True
        st.session_state.auth_timestamp = datetime.now()
        return True
    
    return False

def check_authentication() -> bool:
    """Check if user is authenticated and session is valid"""
    if not st.session_state.get('authenticated', False):
        return False
    
    # Check session timeout (24 hours)
    auth_time = st.session_state.get('auth_timestamp')
    if auth_time:
        if datetime.now() - auth_time > timedelta(hours=24):
            st.session_state.authenticated = False
            st.session_state.auth_timestamp = None
            return False
    
    return True

def logout_user():
    """Logout user and clear session"""
    st.session_state.authenticated = False
    st.session_state.auth_timestamp = None
    if 'automation' in st.session_state:
        del st.session_state.automation
