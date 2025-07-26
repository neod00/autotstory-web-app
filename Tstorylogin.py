from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def post_login_operations():
    # 블로그 관리 페이지 URL 설정
    BLOG_MANAGE_URL = "https://climate-insight.tistory.com/manage/post"
    
    # ChromeOptions 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # WebDriver 자동 관리 설정
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # 사용자에게 로그인 요청
        driver.get("https://www.tistory.com/auth/login")
        print("로그인을 수동으로 진행한 후 'Enter' 키를 눌러주세요.")
        input("로그인 후 계속하려면 Enter 키를 누르세요...")

        # 직접 블로그 관리 페이지로 이동
        print(f"블로그 관리 페이지({BLOG_MANAGE_URL})로 이동합니다...")
        driver.get(BLOG_MANAGE_URL)
        
        # 페이지 로딩 대기
        print("페이지 로딩을 기다립니다...")
        time.sleep(5)  # 충분한 로딩 시간 부여
        
        # iframe 확인 (티스토리 관리 페이지는 iframe을 사용할 수 있음)
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                print(f"{len(iframes)}개의 iframe을 발견했습니다.")
                main_frame = None
                
                # iframe 내용 확인
                for idx, iframe in enumerate(iframes):
                    try:
                        iframe_id = iframe.get_attribute("id") or ""
                        iframe_name = iframe.get_attribute("name") or ""
                        iframe_src = iframe.get_attribute("src") or ""
                        print(f"iframe {idx+1}: id='{iframe_id}', name='{iframe_name}', src='{iframe_src}'")
                        
                        # 관리 페이지 관련 iframe인지 확인
                        if "manage" in iframe_src or "post" in iframe_src:
                            main_frame = iframe
                            print(f"관리 페이지 관련 iframe을 찾았습니다: {idx+1}")
                    except:
                        print(f"iframe {idx+1} 정보 읽기 실패")
                
                # 관리 페이지 관련 iframe으로 전환
                if main_frame:
                    driver.switch_to.frame(main_frame)
                    print("관리 페이지 iframe으로 전환했습니다.")
        except Exception as e:
            print(f"iframe 확인 중 오류: {e}")

        # 현재 페이지 저장 (디버깅용)
        print("현재 페이지를 저장합니다...")
        page_source = driver.page_source
        with open("tistory_posts.html", "w", encoding="utf-8") as file:
            file.write(page_source)

        # 게시물 정보 가져오기
        try:
            print("게시물 정보 찾는 중...")
            
            # 티스토리 블로그 관리 페이지에서 사용되는 선택자들
            selectors = [
                ".list-body .title a", # 게시물 제목 (목록에서)
                ".category-post-list .title", # 카테고리별 게시물 목록
                "table.list-table tr td.title a", # 테이블 형식 목록
                "a.tit_post", # 게시물 제목 링크
                ".post-item a.title", # 게시물 항목 제목
                ".itemTitle", # 게시물 제목 클래스
                ".post_title", # 다른 게시물 제목 클래스
            ]
            
            found = False
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and len(elements) > 0:
                        print(f"선택자 '{selector}'에서 {len(elements)}개의 게시물을 찾았습니다.")
                        for i, element in enumerate(elements[:5]):  # 처음 5개만 출력
                            title = element.text.strip() if element.text.strip() else '(텍스트 없음)'
                            href = element.get_attribute('href') or '(링크 없음)'
                            print(f"게시물 {i+1}: 제목='{title}', 링크='{href}'")
                        found = True
                        break
                except Exception as inner_e:
                    print(f"선택자 '{selector}' 시도 중 오류: {inner_e}")
            
            if not found:
                print("게시물을 찾을 수 있는 요소를 찾지 못했습니다.")
                print("페이지 구조 분석을 시작합니다...")
                
                # 주요 HTML 요소 분석
                for tag in ["table", "div.list", "ul", "section", "article"]:
                    elements = driver.find_elements(By.CSS_SELECTOR, tag)
                    if elements:
                        print(f"{len(elements)}개의 '{tag}' 요소를 찾았습니다.")
                
                # 게시물 관련 키워드 검색
                keywords = ["post", "article", "title", "list", "content"]
                for keyword in keywords:
                    elements = driver.find_elements(By.CSS_SELECTOR, f"[class*='{keyword}'], [id*='{keyword}']")
                    if elements:
                        print(f"{len(elements)}개의 '{keyword}' 관련 요소를 찾았습니다.")
                        for i, elem in enumerate(elements[:3]):
                            try:
                                class_name = elem.get_attribute('class') or ''
                                id_name = elem.get_attribute('id') or ''
                                print(f"  요소 {i+1}: class='{class_name}', id='{id_name}'")
                            except:
                                pass
                
                # 페이지에 있는 모든 링크 분석
                links = driver.find_elements(By.TAG_NAME, "a")
                print(f"페이지에서 {len(links)}개의 링크를 찾았습니다.")
                post_links = []
                
                for link in links:
                    try:
                        href = link.get_attribute('href') or ''
                        if 'post' in href or 'article' in href or 'entry' in href:
                            text = link.text.strip() or '(텍스트 없음)'
                            post_links.append((text, href))
                    except:
                        pass
                
                if post_links:
                    print(f"{len(post_links)}개의 게시물 관련 링크를 찾았습니다:")
                    for i, (text, href) in enumerate(post_links[:10]):
                        print(f"  게시물 링크 {i+1}: 텍스트='{text}', href='{href}'")
            
        except Exception as e:
            print(f"게시물 정보를 가져오는 중 오류 발생: {e}")

    except Exception as e:
        print(f"에러 발생: {e}")
    
    finally:
        # 브라우저 종료
        print("작업 완료. 브라우저를 종료합니다.")
        driver.quit()

# 프로그램 실행
if __name__ == "__main__":
    post_login_operations()
