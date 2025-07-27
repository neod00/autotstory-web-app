#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이미지 자동 생성 모듈 - Streamlit 앱용
================================

Unsplash API를 사용한 키워드 기반 이미지 검색 및 다중 이미지 처리
"""

import requests
import json
from typing import List, Dict

# Unsplash API 키 (실제 사용시 유효한 키로 교체)
UNSPLASH_ACCESS_KEY = "uQgwi8yVjCIJmD0NNU2_2oBIHUMI8UPn2B6blxwWbvQ"

def get_multiple_images_v2(keywords: List[str], count: int = 3) -> List[Dict]:
    """다중 이미지 검색 (V2)"""
    images = []
    
    for i, keyword in enumerate(keywords[:count]):
        try:
            # Unsplash API 호출
            url = "https://api.unsplash.com/search/photos"
            params = {
                "query": keyword,
                "per_page": 1,
                "orientation": "landscape"
            }
            headers = {
                "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    photo = data["results"][0]
                    images.append({
                        "keyword": keyword,
                        "url": photo["urls"]["regular"],
                        "alt_text": photo.get("description", "") or photo.get("alt_description", ""),
                        "photographer": photo["user"]["name"],
                        "width": photo["width"],
                        "height": photo["height"],
                        "unsplash_url": photo["links"]["html"],
                        "type": "featured" if i == 0 else "content"
                    })
                    continue
            
            # Fallback 이미지
            images.append({
                "keyword": keyword,
                "url": "https://picsum.photos/800/400",
                "alt_text": f"Fallback image for {keyword}",
                "photographer": "Unknown",
                "width": 800,
                "height": 400,
                "unsplash_url": "https://picsum.photos",
                "type": "featured" if i == 0 else "content"
            })
            
        except Exception as e:
            # 예외 시에도 Fallback 추가
            images.append({
                "keyword": keyword,
                "url": "https://picsum.photos/800/400",
                "alt_text": f"Error fallback for {keyword}",
                "photographer": "Unknown",
                "width": 800,
                "height": 400,
                "unsplash_url": "https://picsum.photos",
                "type": "featured" if i == 0 else "content"
            })
    
    return images

def generate_image_html(images: List[Dict]) -> str:
    """이미지 HTML 생성"""
    if not images:
        return ""
    
    html_parts = []
    for i, image in enumerate(images):
        html_parts.append(f"""
        <div style="margin: 20px 0; text-align: center;">
            <img src="{image['url']}" 
                 alt="{image['alt_text']}" 
                 style="max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <p style="margin-top: 10px; font-size: 0.9rem; color: #666;">
                📸 {image['photographer']} | 
                <a href="{image['unsplash_url']}" target="_blank" style="color: #667eea;">Unsplash에서 보기</a>
            </p>
        </div>
        """)
    
    return ''.join(html_parts)

def get_keyword_image_url(keyword: str) -> str:
    """키워드에 대한 이미지 URL 반환"""
    try:
        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": keyword,
            "per_page": 1,
            "orientation": "landscape"
        }
        headers = {
            "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                return data["results"][0]["urls"]["regular"]
        
        # Fallback
        return "https://picsum.photos/800/400"
        
    except Exception as e:
        return "https://picsum.photos/800/400" 