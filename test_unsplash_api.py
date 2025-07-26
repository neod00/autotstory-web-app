import requests
import urllib.parse

def test_unsplash_api():
    # API 키
    UNSPLASH_ACCESS_KEY = "uQgwi8yVjCIJmD0NNU2_2oBIHUMI8UPn2B6blxwWbvQ"
    
    # 테스트할 키워드
    test_keywords = [
        "nature",                    # 영어 단일 단어
        "renewable energy",          # 영어 복합 단어
        "태양광",                     # 한글 단일 단어
        "재생 에너지 트렌드",          # 한글 복합 단어
    ]
    
    print("=== Unsplash API 테스트 시작 ===")
    
    for keyword in test_keywords:
        # URL 인코딩
        encoded_keyword = urllib.parse.quote(keyword)
        
        print(f"\n테스트 키워드: '{keyword}'")
        print(f"인코딩된 키워드: '{encoded_keyword}'")
        
        # API 요청
        endpoint = f"https://api.unsplash.com/photos/random?query={encoded_keyword}&orientation=landscape&client_id={UNSPLASH_ACCESS_KEY}"
        print(f"API 엔드포인트: {endpoint}")
        
        try:
            # API 요청 수행
            resp = requests.get(endpoint, timeout=5)
            print(f"응답 상태 코드: {resp.status_code}")
            
            # 응답 확인
            if resp.status_code == 200:
                data = resp.json()
                image_url = data.get("urls", {}).get("regular", "")
                print(f"이미지 URL: {image_url}")
            else:
                print(f"에러 응답: {resp.text}")
                
        except Exception as e:
            print(f"요청 중 오류 발생: {e}")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    test_unsplash_api() 