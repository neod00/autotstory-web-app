import re
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime
import random

def clean_text(text: str) -> str:
    """텍스트 정리 및 정규화"""
    if not text:
        return ""
    
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    
    # 불필요한 공백 정리
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    # 문단 구분 정리
    text = re.sub(r'([.!?])\s*\n', r'\1\n\n', text)
    
    return text.strip()

def extract_keywords(text: str, max_keywords: int = 8) -> List[str]:
    """텍스트에서 키워드 추출"""
    # 한국어 키워드 추출 패턴
    keywords = []
    
    # 일반적인 키워드 패턴
    patterns = [
        r'[\w가-힣]+(?:의|와|과|를|을|이|가|에|에서|로|으로)',
        r'[\w가-힣]+(?:방법|전략|기법|기술|도구|플랫폼|서비스)',
        r'[\w가-힣]+(?:관리|개발|설계|분석|최적화|개선)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        keywords.extend(matches)
    
    # 중복 제거 및 정리
    keywords = list(set(keywords))
    keywords = [kw.strip() for kw in keywords if len(kw.strip()) > 1]
    
    # 빈도수 기반 정렬
    keyword_freq = {}
    for keyword in keywords:
        keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
    
    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
    
    return [kw for kw, freq in sorted_keywords[:max_keywords]]

def generate_tags(topic: str, keywords: List[str]) -> List[str]:
    """태그 생성"""
    tags = [topic]
    
    # 키워드에서 태그 추출
    for keyword in keywords:
        if len(keyword) <= 10 and keyword not in tags:
            tags.append(keyword)
    
    # 일반적인 태그 추가
    common_tags = ["가이드", "정보", "팁", "전략", "방법"]
    for tag in common_tags:
        if tag not in tags and len(tags) < 5:
            tags.append(tag)
    
    return tags[:5]

def validate_content(content_data: Dict) -> bool:
    """콘텐츠 데이터 유효성 검사"""
    required_fields = ['title', 'introduction', 'main_content', 'conclusion']
    
    for field in required_fields:
        if field not in content_data or not content_data[field]:
            return False
    
    # 최소 길이 검사
    if len(content_data['introduction']) < 100:
        return False
    
    if len(content_data['main_content']) < 500:
        return False
    
    if len(content_data['conclusion']) < 50:
        return False
    
    return True

def format_content_for_display(content_data: Dict) -> Dict:
    """콘텐츠를 표시용으로 포맷팅"""
    formatted = content_data.copy()
    
    # 줄바꿈 처리
    for key in ['introduction', 'main_content', 'conclusion']:
        if key in formatted:
            formatted[key] = formatted[key].replace('\n', '<br>')
    
    return formatted

def generate_seo_title(topic: str) -> str:
    """SEO 최적화된 제목 생성"""
    title_templates = [
        f"{topic} 완벽 가이드",
        f"{topic} 모든 것 - 완벽 정리",
        f"{topic} 방법과 팁 총정리",
        f"{topic} 알아보기 - 기초부터 심화까지",
        f"{topic} 완벽 가이드 2024",
        f"{topic} 성공 전략과 노하우"
    ]
    
    return random.choice(title_templates)

def calculate_read_time(content: str) -> int:
    """읽기 시간 계산 (분 단위)"""
    # 한국어 기준 분당 약 300자 읽기
    total_chars = len(content)
    read_time = max(1, total_chars // 300)
    return read_time

def generate_summary(content: str, max_length: int = 200) -> str:
    """콘텐츠 요약 생성"""
    if len(content) <= max_length:
        return content
    
    # 문장 단위로 분리
    sentences = re.split(r'[.!?]+', content)
    summary = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        if len(summary + sentence) <= max_length:
            summary += sentence + ". "
        else:
            break
    
    return summary.strip()

def create_meta_description(content_data: Dict) -> str:
    """메타 설명 생성"""
    intro = content_data.get('introduction', '')
    if intro:
        return generate_summary(intro, 150)
    
    main_content = content_data.get('main_content', '')
    return generate_summary(main_content, 150)

def validate_topic(topic: str) -> bool:
    """주제 유효성 검사"""
    if not topic or len(topic.strip()) < 2:
        return False
    
    # 특수문자나 숫자만으로 구성된 경우 제외
    if re.match(r'^[0-9\s\W]+$', topic):
        return False
    
    return True

def sanitize_filename(filename: str) -> str:
    """파일명 정리"""
    # 특수문자 제거
    filename = re.sub(r'[^\w\s-]', '', filename)
    # 공백을 언더스코어로 변경
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename.lower()

def get_current_timestamp() -> str:
    """현재 타임스탬프 반환"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def create_download_filename(prefix: str, extension: str) -> str:
    """다운로드 파일명 생성"""
    timestamp = get_current_timestamp()
    return f"{prefix}_{timestamp}.{extension}"

def format_file_size(size_bytes: int) -> str:
    """파일 크기 포맷팅"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def check_api_key_validity(api_key: str) -> bool:
    """API 키 유효성 검사"""
    if not api_key or len(api_key.strip()) < 10:
        return False
    
    # OpenAI API 키 형식 검사 (sk-로 시작)
    if not api_key.startswith('sk-'):
        return False
    
    return True

def generate_error_message(error_type: str, details: str = "") -> str:
    """에러 메시지 생성"""
    error_messages = {
        "api_key_invalid": "API 키가 유효하지 않습니다. 올바른 OpenAI API 키를 입력해주세요.",
        "content_generation_failed": "콘텐츠 생성에 실패했습니다. 다시 시도해주세요.",
        "topic_invalid": "주제가 유효하지 않습니다. 2글자 이상의 의미있는 주제를 입력해주세요.",
        "network_error": "네트워크 오류가 발생했습니다. 인터넷 연결을 확인해주세요.",
        "rate_limit": "API 사용량 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
    }
    
    base_message = error_messages.get(error_type, "알 수 없는 오류가 발생했습니다.")
    if details:
        return f"{base_message} {details}"
    
    return base_message 