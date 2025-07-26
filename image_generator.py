#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이미지 자동 생성 모듈 - Streamlit 앱용
================================

Unsplash API를 사용한 키워드 기반 이미지 검색 및 다중 이미지 처리
"""

import requests
import json
import re
from typing import List, Dict, Optional
import random

# streamlit import를 조건부로 처리
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    # streamlit이 없을 때를 위한 더미 함수
    def st_info(msg): print(f"INFO: {msg}")
    def st_success(msg): print(f"SUCCESS: {msg}")
    def st_warning(msg): print(f"WARNING: {msg}")
    def st_error(msg): print(f"ERROR: {msg}")
    st = type('st', (), {
        'info': st_info,
        'success': st_success,
        'warning': st_warning,
        'error': st_error
    })()

class ImageGenerator:
    """이미지 자동 생성 클래스"""
    
    def __init__(self):
        # Unsplash API 키 (무료 버전)
        self.unsplash_access_key = "uQgwi8yVjCIJmD0NNU2_2oBIHUMI8UPn2B6blxwWbvQ"
        self.base_url = "https://api.unsplash.com"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Client-ID {self.unsplash_access_key}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def clean_keywords_for_unsplash(self, keywords: List[str]) -> List[str]:
        """Unsplash 검색에 적합한 키워드로 정리"""
        cleaned_keywords = []
        
        for keyword in keywords:
            # 한글 키워드를 영어로 변환 (간단한 매핑)
            english_mapping = {
                '패션': 'fashion',
                '스타일': 'style',
                '코디': 'outfit',
                '건강': 'health',
                '운동': 'exercise',
                '다이어트': 'diet',
                '여행': 'travel',
                '관광': 'tourism',
                '요리': 'cooking',
                '음식': 'food',
                '레시피': 'recipe',
                '취미': 'hobby',
                '독서': 'reading',
                '시간관리': 'time management',
                '생활습관': 'lifestyle',
                '인공지능': 'artificial intelligence',
                'AI': 'artificial intelligence',
                '마케팅': 'marketing',
                '비즈니스': 'business',
                '경제': 'economy',
                '금융': 'finance',
                '투자': 'investment',
                '부동산': 'real estate',
                '주식': 'stock',
                '암호화폐': 'cryptocurrency',
                '기술': 'technology',
                'IT': 'technology',
                '프로그래밍': 'programming',
                '코딩': 'coding',
                '웹개발': 'web development',
                '앱개발': 'app development',
                '디자인': 'design',
                'UX': 'user experience',
                'UI': 'user interface',
                '브랜딩': 'branding',
                '소셜미디어': 'social media',
                '인플루언서': 'influencer',
                '콘텐츠': 'content',
                '블로그': 'blog',
                '유튜브': 'youtube',
                '팟캐스트': 'podcast',
                '교육': 'education',
                '학습': 'learning',
                '온라인강의': 'online course',
                '자기계발': 'self improvement',
                '성장': 'growth',
                '목표': 'goal',
                '성공': 'success',
                '동기부여': 'motivation',
                '명상': 'meditation',
                '요가': 'yoga',
                '피트니스': 'fitness',
                '웰빙': 'wellness',
                '정신건강': 'mental health',
                '스트레스': 'stress',
                '휴식': 'relaxation',
                '힐링': 'healing',
                '자연': 'nature',
                '환경': 'environment',
                '친환경': 'eco friendly',
                '지속가능': 'sustainable',
                '미니멀': 'minimal',
                '심플': 'simple',
                '모던': 'modern',
                '클래식': 'classic',
                '빈티지': 'vintage',
                '트렌디': 'trendy',
                '스타일리시': 'stylish',
                '엘레간트': 'elegant',
                '세련된': 'sophisticated',
                '프리미엄': 'premium',
                '럭셔리': 'luxury',
                '컴팩트': 'compact',
                '효율적': 'efficient',
                '생산성': 'productivity',
                '조직화': 'organization',
                '정리': 'organization',
                '정돈': 'tidying',
                '미니멀리즘': 'minimalism',
                '단순화': 'simplification',
                '최적화': 'optimization',
                '효율성': 'efficiency',
                '시간절약': 'time saving',
                '빠른': 'fast',
                '즉시': 'instant',
                '간편한': 'convenient',
                '쉬운': 'easy',
                '간단한': 'simple',
                '실용적인': 'practical',
                '유용한': 'useful',
                '도움이 되는': 'helpful',
                '유익한': 'beneficial',
                '가치 있는': 'valuable',
                '중요한': 'important',
                '필수적인': 'essential',
                '핵심': 'core',
                '기본': 'basic',
                '기초': 'foundation',
                '원리': 'principle',
                '방법': 'method',
                '기법': 'technique',
                '전략': 'strategy',
                '계획': 'plan',
                '시스템': 'system',
                '프로세스': 'process',
                '워크플로우': 'workflow',
                '루틴': 'routine',
                '습관': 'habit',
                '일상': 'daily',
                '라이프스타일': 'lifestyle',
                '생활': 'life',
                '일': 'work',
                '직장': 'office',
                '회사': 'company',
                '사업': 'business',
                '창업': 'startup',
                '기업': 'enterprise',
                '조직': 'organization',
                '팀': 'team',
                '협업': 'collaboration',
                '소통': 'communication',
                '리더십': 'leadership',
                '관리': 'management',
                '운영': 'operation',
                '전략': 'strategy',
                '마케팅': 'marketing',
                '판매': 'sales',
                '고객': 'customer',
                '서비스': 'service',
                '품질': 'quality',
                '만족도': 'satisfaction',
                '경험': 'experience',
                '감정': 'emotion',
                '기분': 'mood',
                '감사': 'gratitude',
                '행복': 'happiness',
                '기쁨': 'joy',
                '희망': 'hope',
                '꿈': 'dream',
                '비전': 'vision',
                '미래': 'future',
                '발전': 'development',
                '진보': 'progress',
                '혁신': 'innovation',
                '창의성': 'creativity',
                '아이디어': 'idea',
                '영감': 'inspiration',
                '상상력': 'imagination',
                '예술': 'art',
                '문화': 'culture',
                '역사': 'history',
                '전통': 'tradition',
                '현대': 'modern',
                '미래': 'future',
                '디지털': 'digital',
                '온라인': 'online',
                '인터넷': 'internet',
                '모바일': 'mobile',
                '스마트폰': 'smartphone',
                '컴퓨터': 'computer',
                '노트북': 'laptop',
                '태블릿': 'tablet',
                '웨어러블': 'wearable',
                'IoT': 'internet of things',
                '빅데이터': 'big data',
                '머신러닝': 'machine learning',
                '딥러닝': 'deep learning',
                '자동화': 'automation',
                '로봇': 'robot',
                '드론': 'drone',
                'VR': 'virtual reality',
                'AR': 'augmented reality',
                '메타버스': 'metaverse',
                '블록체인': 'blockchain',
                'NFT': 'nft',
                '메타': 'meta',
                '구글': 'google',
                '애플': 'apple',
                '마이크로소프트': 'microsoft',
                '아마존': 'amazon',
                '넷플릭스': 'netflix',
                '스포티파이': 'spotify',
                '인스타그램': 'instagram',
                '페이스북': 'facebook',
                '트위터': 'twitter',
                '링크드인': 'linkedin',
                '틱톡': 'tiktok',
                '줌': 'zoom',
                '슬랙': 'slack',
                '노션': 'notion',
                '피그마': 'figma',
                '캐노바': 'canva',
                '워드프레스': 'wordpress',
                '샵ify': 'shopify',
                '스퀘어': 'square',
                '스트라이프': 'stripe',
                '페이팔': 'paypal',
                '비트코인': 'bitcoin',
                '이더리움': 'ethereum',
                '도지코인': 'dogecoin',
                '카르다노': 'cardano',
                '폴카닷': 'polkadot',
                '솔라나': 'solana',
                '체인링크': 'chainlink',
                '유니스왑': 'uniswap',
                '오픈씨': 'opensea',
                '로블록스': 'roblox',
                '마인크래프트': 'minecraft',
                '포트나이트': 'fortnite',
                '리그오브레전드': 'league of legends',
                '오버워치': 'overwatch',
                '발로란트': 'valorant',
                '피파': 'fifa',
                '콜오브듀티': 'call of duty',
                '배틀그라운드': 'pubg',
                '리니지': 'lineage',
                '메이플스토리': 'maplestory',
                '오버워치': 'overwatch',
                '하스스톤': 'hearthstone',
                '스타크래프트': 'starcraft',
                '디아블로': 'diablo',
                '워크래프트': 'warcraft',
                '스카이림': 'skyrim',
                '폴아웃': 'fallout',
                '어쌔신크리드': 'assassins creed',
                'GTA': 'grand theft auto',
                '레드데드': 'red dead redemption',
                '세컨드라이프': 'second life',
                '시뮬시티': 'simcity',
                '심즈': 'sims',
                '시빌리제이션': 'civilization',
                '문명': 'civilization',
                '에이지오브엠파이어': 'age of empires',
                '토탈워': 'total war',
                '유로파': 'europa universalis',
                '크루세이더킹즈': 'crusader kings',
                '하츠오브아이언': 'hearts of iron',
                '빅토리아': 'victoria',
                '스텔라리스': 'stellaris',
                '엔드리스스페이스': 'endless space',
                '갤럭시': 'galaxy',
                '우주': 'space',
                '별': 'star',
                '행성': 'planet',
                '지구': 'earth',
                '달': 'moon',
                '태양': 'sun',
                '은하': 'galaxy',
                '성운': 'nebula',
                '블랙홀': 'black hole',
                '우주선': 'spaceship',
                '로켓': 'rocket',
                '위성': 'satellite',
                'ISS': 'international space station',
                'NASA': 'nasa',
                '스페이스X': 'spacex',
                '블루오리진': 'blue origin',
                '버진갤럭틱': 'virgin galactic',
                '테슬라': 'tesla',
                '일론머스크': 'elon musk',
                '제프베조스': 'jeff bezos',
                '빌게이츠': 'bill gates',
                '스티브잡스': 'steve jobs',
                '마크저커버그': 'mark zuckerberg',
                '래리페이지': 'larry page',
                '세르게이브린': 'sergey brin',
                '재크도시': 'jack dorsey',
                '에반스피겔': 'evan spiegel',
                '케빈시스트롬': 'kevin systrom',
                '마이크크리거': 'mike krieger',
                '아담모스리': 'adam mosseri',
                '수전워치스키': 'susan wojcicki',
                '닐모한': 'neil mohan',
                '순다피차이': 'sundar pichai',
                '팀쿡': 'tim cook',
                '크레이그페더리기': 'craig federighi',
                '조니아이브': 'jonny ive',
                '필스칼러': 'phil schiller',
                '앤디루빈': 'andy rubin',
                '휴고바라': 'hugo barra',
                '크리스우르손': 'chris urmson',
                '세바스찬스런': 'sebastian thrun',
                '앤드류응': 'andrew ng',
                '얀르쿤': 'yan lecun',
                '제프리힌튼': 'geoffrey hinton',
                '요슈아벤지오': 'yoshua bengio',
                '데미스하사비스': 'demis hassabis',
                '야안굿펠로우': 'ian goodfellow',
                '알렉스크리제브스키': 'alex krizhevsky',
                '일리야수츠케버': 'ilya sutskever',
                '사티아나델라': 'satya nadella',
                '브래드스미스': 'brad smith',
                '스콧거스리': 'scott guthrie',
                '케빈스콧': 'kevin scott',
                '에이미후드': 'amy hood',
                '크리스캐포스': 'chris capossela',
                '라지브수리': 'rajiv suri',
                '앤드류윌슨': 'andrew wilson',
                '제니퍼테일러': 'jennifer taylor',
                '마이크로소프트': 'microsoft',
                '구글': 'google',
                '애플': 'apple',
                '아마존': 'amazon',
                '메타': 'meta',
                '알파벳': 'alphabet',
                '테슬라': 'tesla',
                '넷플릭스': 'netflix',
                '스포티파이': 'spotify',
                '우버': 'uber',
                '리프트': 'lyft',
                '에어비앤비': 'airbnb',
                '도어대시': 'doordash',
                '그럽허브': 'grubhub',
                '인스타카트': 'instacart',
                '웨이모': 'waymo',
                '크루즈': 'cruise',
                '아르고': 'argo',
                '오로라': 'aurora',
                '누로': 'nuro',
                '조이': 'zoox',
                '리비오': 'rivian',
                '루시드': 'lucid',
                '니오': 'nio',
                'XPeng': 'xpeng',
                '리소': 'li auto',
                '바이두': 'baidu',
                '알리바바': 'alibaba',
                '텐센트': 'tencent',
                '바이트댄스': 'bytedance',
                '틱톡': 'tiktok',
                '화웨이': 'huawei',
                '샤오미': 'xiaomi',
                'OPPO': 'oppo',
                'vivo': 'vivo',
                '원플러스': 'oneplus',
                '삼성': 'samsung',
                'LG': 'lg',
                '현대': 'hyundai',
                '기아': 'kia',
                '포드': 'ford',
                'GM': 'general motors',
                '크라이슬러': 'chrysler',
                'BMW': 'bmw',
                '벤츠': 'mercedes benz',
                '아우디': 'audi',
                '폭스바겐': 'volkswagen',
                '볼보': 'volvo',
                '재규어': 'jaguar',
                '랜드로버': 'land rover',
                '미니': 'mini',
                '포르쉐': 'porsche',
                '페라리': 'ferrari',
                '람보르기니': 'lamborghini',
                '마세라티': 'maserati',
                '알파로메오': 'alfa romeo',
                '피아트': 'fiat',
                '르노': 'renault',
                '푸조': 'peugeot',
                '시트로엥': 'citroen',
                '닛산': 'nissan',
                '토요타': 'toyota',
                '혼다': 'honda',
                '마쓰다': 'mazda',
                '스바루': 'subaru',
                '미쓰비시': 'mitsubishi',
                '스즈키': 'suzuki',
                '다이하쓰': 'daihatsu',
                '이스즈': 'isuzu',
                '우베': 'ube',
                '스미토모': 'sumitomo',
                '미쓰이': 'mitsui',
                '마루베니': 'marubeni',
                '이토추': 'ito chu',
                '소지츠': 'sojitz',
                '토요타쓰쇼': 'toyota tsusho',
                '미쓰비시상사': 'mitsubishi corporation',
                '미쓰이상사': 'mitsui co',
                '마루베니상사': 'marubeni corporation',
                '이토추상사': 'ito chu corporation',
                '소지츠상사': 'sojitz corporation',
                '토요타쓰쇼상사': 'toyota tsusho corporation',
                '미쓰비시전기': 'mitsubishi electric',
                '미쓰비시중공업': 'mitsubishi heavy industries',
                '미쓰비시화학': 'mitsubishi chemical',
                '미쓰비시제강': 'mitsubishi steel',
                '미쓰비시제지': 'mitsubishi paper',
                '미쓰비시제약': 'mitsubishi tanabe pharma',
                '미쓰비시화학홀딩스': 'mitsubishi chemical holdings',
                '미쓰비시전기홀딩스': 'mitsubishi electric holdings',
                '미쓰비시중공업홀딩스': 'mitsubishi heavy industries holdings',
                '미쓰비시제강홀딩스': 'mitsubishi steel holdings',
                '미쓰비시제지홀딩스': 'mitsubishi paper holdings',
                '미쓰비시제약홀딩스': 'mitsubishi tanabe pharma holdings',
                '미쓰비시화학홀딩스': 'mitsubishi chemical holdings',
                '미쓰비시전기홀딩스': 'mitsubishi electric holdings',
                '미쓰비시중공업홀딩스': 'mitsubishi heavy industries holdings',
                '미쓰비시제강홀딩스': 'mitsubishi steel holdings',
                '미쓰비시제지홀딩스': 'mitsubishi paper holdings',
                '미쓰비시제약홀딩스': 'mitsubishi tanabe pharma holdings'
            }
            
            # 영어 매핑 확인
            if keyword in english_mapping:
                cleaned_keywords.append(english_mapping[keyword])
            else:
                # 한글 키워드 그대로 사용 (Unsplash가 한글도 지원)
                cleaned_keywords.append(keyword)
        
        return cleaned_keywords[:5]  # 상위 5개만 사용
    
    def get_multiple_images(self, keywords: List[str], count: int = 3) -> List[Dict]:
        """다중 이미지 검색"""
        try:
            if not keywords:
                return []
            
            # 키워드 정리
            cleaned_keywords = self.clean_keywords_for_unsplash(keywords)
            
            if not cleaned_keywords:
                return []
            
            # 메인 키워드로 검색
            main_keyword = cleaned_keywords[0]
            
            st.info(f"🖼️ '{main_keyword}' 키워드로 이미지 검색 중...")
            
            # Unsplash API 호출
            search_url = f"{self.base_url}/search/photos"
            params = {
                'query': main_keyword,
                'per_page': count,
                'orientation': 'landscape'
            }
            
            response = self.session.get(search_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                images = []
                for result in results:
                    image_info = {
                        'url': result['urls']['regular'],
                        'thumb_url': result['urls']['thumb'],
                        'download_url': result['links']['download'],
                        'alt_text': result.get('alt_description', main_keyword),
                        'photographer': result['user']['name'],
                        'photographer_url': result['user']['links']['html'],
                        'unsplash_url': result['links']['html'],
                        'width': result['width'],
                        'height': result['height']
                    }
                    images.append(image_info)
                
                st.success(f"✅ {len(images)}개의 이미지를 찾았습니다!")
                return images
            else:
                st.warning(f"⚠️ 이미지 검색 실패: {response.status_code}")
                return []
                
        except Exception as e:
            st.error(f"❌ 이미지 검색 중 오류 발생: {str(e)}")
            return []
    
    def get_keyword_image_url(self, keyword: str) -> str:
        """키워드 기반 단일 이미지 URL 가져오기"""
        try:
            images = self.get_multiple_images([keyword], count=1)
            if images:
                return images[0]['url']
            else:
                return ""
        except Exception as e:
            st.error(f"❌ 이미지 URL 가져오기 실패: {str(e)}")
            return ""
    
    def generate_image_html(self, images: List[Dict]) -> str:
        """이미지 HTML 생성"""
        if not images:
            return ""
        
        html_parts = []
        
        for i, image in enumerate(images):
            html_part = f"""
<div class="blog-image" style="margin: 20px 0; text-align: center;">
    <img src="{image['url']}" 
         alt="{image['alt_text']}" 
         style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"
         loading="lazy">
    <p style="font-size: 12px; color: #666; margin-top: 8px;">
        Photo by <a href="{image['photographer_url']}" target="_blank" style="color: #007bff;">{image['photographer']}</a> 
        on <a href="{image['unsplash_url']}" target="_blank" style="color: #007bff;">Unsplash</a>
    </p>
</div>
"""
            html_parts.append(html_part)
        
        return "\n".join(html_parts)
    
    def generate_image_gallery_html(self, images: List[Dict], columns: int = 3) -> str:
        """이미지 갤러리 HTML 생성"""
        if not images:
            return ""
        
        html_parts = [f'<div class="image-gallery" style="display: grid; grid-template-columns: repeat({columns}, 1fr); gap: 20px; margin: 20px 0;">']
        
        for image in images:
            html_part = f"""
<div class="gallery-item" style="text-align: center;">
    <img src="{image['thumb_url']}" 
         alt="{image['alt_text']}" 
         style="width: 100%; height: 200px; object-fit: cover; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
         loading="lazy">
    <p style="font-size: 10px; color: #666; margin-top: 4px;">
        by <a href="{image['photographer_url']}" target="_blank" style="color: #007bff;">{image['photographer']}</a>
    </p>
</div>
"""
            html_parts.append(html_part)
        
        html_parts.append('</div>')
        return "\n".join(html_parts)

def get_multiple_images_v2(keywords: List[str], count: int = 3) -> List[Dict]:
    """다중 이미지 검색 (V2 호환)"""
    generator = ImageGenerator()
    return generator.get_multiple_images(keywords, count)

def get_keyword_image_url(keyword: str) -> str:
    """키워드 기반 이미지 URL 가져오기"""
    generator = ImageGenerator()
    return generator.get_keyword_image_url(keyword)

def generate_image_html(images: List[Dict]) -> str:
    """이미지 HTML 생성"""
    generator = ImageGenerator()
    return generator.generate_image_html(images)

def generate_image_gallery_html(images: List[Dict], columns: int = 3) -> str:
    """이미지 갤러리 HTML 생성"""
    generator = ImageGenerator()
    return generator.generate_image_gallery_html(images, columns) 