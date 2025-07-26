import os
import time
import random
import openai
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 블로그 정보 설정
BLOG_URL = "https://climate-insight.tistory.com"
BLOG_MANAGE_URL = "https://climate-insight.tistory.com/manage/post"
BLOG_NEW_POST_URL = "https://climate-insight.tistory.com/manage/newpost"

# 블로그 주제 및 카테고리 설정 (예시 목록)
BLOG_TOPICS = [
    "기후변화와 환경 문제",
    "지속 가능한 발전",
    "재생 에너지 트렌드",
    "탄소중립 정책",
    "친환경 생활 습관"
]

def get_user_topic():
    """
    사용자로부터 블로그 주제를 입력받음
    """
    print("\n=== 블로그 주제 선택 ===")
    print("1. 예시 주제 목록에서 선택")
    print("2. 직접 주제 입력")
    choice = input("선택 (1 또는 2): ")
    
    if choice == "1":
        print("\n예시 주제 목록:")
        for i, topic in enumerate(BLOG_TOPICS, 1):
            print(f"{i}. {topic}")
        
        while True:
            try:
                selection = int(input("\n주제 번호 선택: "))
                if 1 <= selection <= len(BLOG_TOPICS):
                    return BLOG_TOPICS[selection-1]
                else:
                    print(f"1부터 {len(BLOG_TOPICS)}까지의 번호를 입력해주세요.")
            except ValueError:
                print("유효한 숫자를 입력해주세요.")
    else:
        return input("\n블로그 주제를 직접 입력해주세요: ")

def generate_blog_content(topic, use_html=False):
    """
    ChatGPT API를 사용하여 블로그 콘텐츠 생성
    """
    print(f"'{topic}' 주제로 블로그 콘텐츠 생성 중...")
    
    # 제목 생성
    title_prompt = f"다음 주제에 관한 블로그 포스트의 매력적인 제목을 생성해주세요: '{topic}'. 제목만 작성하고 따옴표나 기호는 포함하지 마세요."
    title_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 전문적인 블로그 제목 생성기입니다. 매력적이고 SEO에 최적화된 제목을 생성합니다."},
            {"role": "user", "content": title_prompt}
        ],
        max_tokens=50
    )
    title = title_response.choices[0].message.content.strip()
    
    # 본문 생성
    format_guide = "7. HTML 형식으로 작성하여 <h2>, <p>, <ul>, <ol>, <strong> 등의 태그를 적절히 사용하세요." if use_html else "7. 일반 텍스트로 작성하고, 제목은 '#', '##' 등으로 표시하고 목록은 '-', '*' 등으로 표시하세요."
    
    content_prompt = f"""
    다음 주제에 관한 포괄적인 블로그 포스트를 작성해주세요: '{topic}'
    
    블로그 제목은 '{title}'입니다.
    
    다음 가이드라인을 따라주세요:
    1. 한국어로 작성하세요.
    2. 최소 1000단어 분량으로 작성하세요.
    3. 서론, 본론, 결론 구조를 사용하세요.
    4. 소제목을 포함하여 구조화된 형식으로 작성하세요.
    5. 실제 사례나 통계 데이터를 포함하세요.
    6. 독자의 참여를 유도하는 질문을 포함하세요.
    {format_guide}
    8. 마지막에 5개의 관련 해시태그를 추가하세요.
    """
    
    content_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": "당신은 전문적인 블로그 작가입니다. 독자가 이해하기 쉽고 정보가 풍부한 콘텐츠를 작성합니다."},
            {"role": "user", "content": content_prompt}
        ],
        max_tokens=4000
    )
    content = content_response.choices[0].message.content.strip()
    
    # 태그 생성
    tags_prompt = f"다음 블로그 포스트 주제에 관련된 5개의 SEO 최적화 태그를 생성해주세요 (쉼표로 구분): '{topic}'"
    tags_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 SEO 전문가입니다. 검색 엔진에서 높은 순위를 차지할 수 있는 태그를 제안합니다."},
            {"role": "user", "content": tags_prompt}
        ],
        max_tokens=100
    )
    tags = tags_response.choices[0].message.content.strip()
    
    print(f"제목: {title}")
    print(f"태그: {tags}")
    print("콘텐츠 생성 완료!")
    
    return {
        "title": title,
        "content": content,
        "tags": tags
    }

def login_and_post_to_tistory():
    """
    티스토리에 로그인하고 생성된 콘텐츠 게시
    """
    # ChromeOptions 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # WebDriver 설정
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # 로그인
        driver.get("https://www.tistory.com/auth/login")
        print("로그인을 수동으로 진행한 후 'Enter' 키를 눌러주세요.")
        input("로그인 후 계속하려면 Enter 키를 누르세요...")
        
        # 사용자에게 주제 선택 요청
        selected_topic = get_user_topic()
        
        # HTML 모드 선택 여부
        print("\n=== 콘텐츠 형식 선택 ===")
        print("1. HTML 모드 (태그 포함)")
        print("2. 일반 텍스트 모드")
        format_choice = input("선택 (1 또는 2): ")
        use_html = (format_choice == "1")
        
        # 콘텐츠 생성
        blog_post = generate_blog_content(selected_topic, use_html)
        
        # 새 글 작성 페이지로 이동
        print("새 글 작성 페이지로 이동합니다...")
        driver.get(BLOG_NEW_POST_URL)
        time.sleep(5)  # 페이지 로딩 대기
        
        # iframe 확인 및 전환
        try:
            iframe_editor = None
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                print(f"{len(iframes)}개의 iframe을 발견했습니다.")
                for iframe in iframes:
                    try:
                        iframe_id = iframe.get_attribute("id") or ""
                        iframe_name = iframe.get_attribute("name") or ""
                        iframe_src = iframe.get_attribute("src") or ""
                        print(f"iframe: id='{iframe_id}', name='{iframe_name}', src='{iframe_src}'")
                        if "editor" in iframe_id.lower():
                            iframe_editor = iframe
                            print(f"에디터 iframe을 찾았습니다: {iframe_id}")
                            break
                    except:
                        pass
        except Exception as e:
            print(f"iframe 확인 중 오류: {e}")
        
        # 제목 입력
        try:
            print("제목을 입력합니다...")
            title_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "post-title-inp"))
            )
            title_input.clear()
            title_input.send_keys(blog_post["title"])
            time.sleep(1)
        except Exception as e:
            print(f"제목 입력 중 오류: {e}")
            
            # 대체 제목 입력 필드 찾기
            try:
                title_inputs = driver.find_elements(By.CSS_SELECTOR, 
                    "input[placeholder*='제목'], input.title, .title-input, .post-title input")
                if title_inputs:
                    title_inputs[0].clear()
                    title_inputs[0].send_keys(blog_post["title"])
                    print("대체 제목 필드에 입력했습니다.")
            except Exception as e2:
                print(f"대체 제목 입력 중 오류: {e2}")
        
        # HTML 모드로 전환 (사용자가 HTML 모드를 선택한 경우)
        if use_html:
            try:
                print("HTML 모드로 전환을 시도합니다...")
                
                # 1. TinyMCE 에디터에서 HTML 버튼 찾기
                html_buttons = driver.find_elements(By.CSS_SELECTOR, 
                    ".btn_html, button[data-mode='html'], .html-mode-button, .switch-html, .mce-i-code")
                
                if html_buttons:
                    html_buttons[0].click()
                    print("HTML 모드로 전환했습니다.")
                    time.sleep(1)
                else:
                    # 2. 직접 JavaScript 실행하여 전환 시도
                    try:
                        # TinyMCE 에디터에서 HTML 모드 전환 스크립트 실행
                        driver.execute_script("if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) { tinyMCE.activeEditor.execCommand('mceCodeEditor'); }")
                        print("JavaScript를 통해 HTML 모드로 전환했습니다.")
                        time.sleep(1)
                    except Exception as js_e:
                        print(f"JavaScript를 통한 HTML 모드 전환 중 오류: {js_e}")
                        
                    # 3. XPath를 사용하여 HTML 버튼 찾기 시도
                    try:
                        html_button_xpath = driver.find_elements(By.XPATH, 
                            "//button[contains(@class, 'html') or contains(@title, 'HTML') or contains(@aria-label, 'HTML')]")
                        if html_button_xpath:
                            html_button_xpath[0].click()
                            print("XPath를 통해 HTML 모드 버튼을 찾아 클릭했습니다.")
                            time.sleep(1)
                    except Exception as xpath_e:
                        print(f"XPath를 통한 HTML 모드 버튼 찾기 중 오류: {xpath_e}")
            except Exception as e:
                print(f"HTML 모드 전환 중 오류: {e}")
        
        # 본문 입력
        try:
            print("본문을 입력합니다...")
            
            # 1. TinyMCE 에디터 프레임으로 전환 시도
            if iframe_editor:
                driver.switch_to.frame(iframe_editor)
                print("에디터 iframe으로 전환했습니다.")
                
                try:
                    # TinyMCE 에디터 본문 요소 찾기
                    body_editor = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "tinymce"))
                    )
                    
                    # 기존 내용 지우기
                    body_editor.clear()
                    
                    # 내용이 많은 경우 작은 부분으로 나누어 입력 (입력 오류 방지)
                    content = blog_post["content"]
                    chunk_size = 1000  # 한 번에 입력할 텍스트 크기
                    
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i + chunk_size]
                        body_editor.send_keys(chunk)
                        time.sleep(0.5)  # 입력 간 짧은 대기 시간
                        
                    print("TinyMCE 에디터에 본문을 입력했습니다.")
                    
                    # 기본 컨텐트로 돌아옴
                    driver.switch_to.default_content()
                except Exception as tinymce_e:
                    # 기본 컨텐트로 돌아옴
                    driver.switch_to.default_content()
                    print(f"TinyMCE 에디터를 찾지 못했습니다: {tinymce_e}")
                    print("다른 방법을 시도합니다.")
                    
                    # 2. JavaScript를 사용하여 TinyMCE 내용 설정 시도
                    try:
                        js_result = driver.execute_script("""
                            if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                                tinyMCE.activeEditor.setContent(arguments[0]);
                                return true;
                            }
                            return false;
                        """, blog_post["content"])
                        
                        if js_result:
                            print("JavaScript를 통해 TinyMCE 에디터에 내용을 설정했습니다.")
                        else:
                            # 3. contenteditable div 또는 textarea 찾기
                            content_elements = driver.find_elements(By.CSS_SELECTOR, 
                                "[contenteditable='true'], textarea.editor, .editor-textarea, #content, .editable-area, .ke-content")
                            
                            if content_elements:
                                print(f"{len(content_elements)}개의 에디터 요소를 찾았습니다.")
                                content_elements[0].clear()
                                
                                # 내용이 많은 경우 작은 부분으로 나누어 입력
                                content = blog_post["content"]
                                chunk_size = 1000
                                
                                for i in range(0, len(content), chunk_size):
                                    chunk = content[i:i + chunk_size]
                                    content_elements[0].send_keys(chunk)
                                    time.sleep(0.5)
                                    
                                print("에디터 요소에 본문을 입력했습니다.")
                            else:
                                print("에디터 요소를 찾지 못했습니다.")
                    except Exception as js_editor_e:
                        print(f"JavaScript를 통한 에디터 내용 설정 중 오류: {js_editor_e}")
            else:
                # iframe이 없는 경우 직접 에디터 요소 찾기
                # 1. 일반적인 contenteditable 요소 찾기
                content_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "[contenteditable='true'], textarea.editor, .editor-textarea, #content, .editable-area, .ke-content")
                
                if content_elements:
                    print(f"{len(content_elements)}개의 에디터 요소를 찾았습니다.")
                    content_elements[0].clear()
                    
                    # 내용이 많은 경우 작은 부분으로 나누어 입력
                    content = blog_post["content"]
                    chunk_size = 1000
                    
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i + chunk_size]
                        content_elements[0].send_keys(chunk)
                        time.sleep(0.5)
                        
                    print("에디터 요소에 본문을 입력했습니다.")
                else:
                    # 2. JavaScript를 사용하여 TinyMCE 내용 설정 시도
                    try:
                        js_result = driver.execute_script("""
                            if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                                tinyMCE.activeEditor.setContent(arguments[0]);
                                return true;
                            }
                            return false;
                        """, blog_post["content"])
                        
                        if js_result:
                            print("JavaScript를 통해 TinyMCE 에디터에 내용을 설정했습니다.")
                        else:
                            # 3. 마지막 수단: XPath로 에디터 영역 찾기
                            editor_xpath = driver.find_elements(By.XPATH, 
                                "//*[contains(@class, 'editor') or contains(@id, 'editor')]//div[contains(@class, 'content') or @contenteditable='true']")
                            
                            if editor_xpath:
                                print("XPath를 통해 에디터 영역을 찾았습니다.")
                                editor_xpath[0].clear()
                                
                                # 내용이 많은 경우 작은 부분으로 나누어 입력
                                content = blog_post["content"]
                                chunk_size = 1000
                                
                                for i in range(0, len(content), chunk_size):
                                    chunk = content[i:i + chunk_size]
                                    editor_xpath[0].send_keys(chunk)
                                    time.sleep(0.5)
                                    
                                print("에디터 영역에 본문을 입력했습니다.")
                            else:
                                print("에디터 영역을 찾지 못했습니다.")
                    except Exception as js_editor_e:
                        print(f"JavaScript를 통한 에디터 내용 설정 중 오류: {js_editor_e}")
        
        except Exception as e:
            print(f"본문 입력 중 오류: {e}")
            driver.switch_to.default_content()  # 혹시 모를 iframe에서 빠져나옴
        
        # 태그 입력
        try:
            print("태그를 입력합니다...")
            
            # 다양한 태그 입력 필드 선택자
            tag_selectors = [
                ".tag-input", 
                "#tag", 
                "input[name='tag']", 
                ".tag-box input", 
                ".post-tag-input",
                ".tagname",
                "input[placeholder*='태그']",
                "[data-role='tag-input']",   # 데이터 속성 기반
                ".editor-tag input",         # 티스토리 태그 입력
                "#editor-root input[type='text']:not([id='post-title-inp'])" # 제목이 아닌 텍스트 입력 필드
            ]
            
            tag_found = False
            
            # 1. CSS 선택자로 태그 입력 필드 찾기
            for selector in tag_selectors:
                try:
                    tag_inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                    if tag_inputs:
                        tag_input = tag_inputs[0]
                        
                        # 입력 필드가 보이고 활성화되어 있는지 확인
                        if tag_input.is_displayed() and tag_input.is_enabled():
                            # 현재 값 지우기
                            tag_input.clear()
                            
                            # 쉼표로 구분된 태그를 하나씩 입력
                            tags_list = blog_post["tags"].split(',')
                            
                            # 방법 1: 각 태그를 개별적으로 입력하고 Enter 키 누르기
                            for tag in tags_list:
                                tag = tag.strip()
                                if tag:
                                    tag_input.send_keys(tag)
                                    tag_input.send_keys(Keys.ENTER)
                                    time.sleep(0.5)
                        
                            print(f"태그 필드({selector})에 태그를 입력했습니다.")
                            tag_found = True
                            break
                
                except Exception as tag_e:
                    print(f"선택자 '{selector}' 사용 중 오류: {tag_e}")
            
            # 2. JavaScript를 사용하여 태그 입력 시도
            if not tag_found:
                try:
                    print("JavaScript를 통해 태그 입력을 시도합니다...")
                    
                    # 쉼표로 구분된 모든 태그를 한 번에 입력
                    tags_str = blog_post["tags"].replace(',', ' ')
                    
                    js_result = driver.execute_script("""
                        // 태그 입력 필드 찾기
                        var tagInput = null;
                        
                        // 다양한 선택자로 시도
                        var selectors = [
                            '.tag-input', '#tag', 'input[name="tag"]', '.tag-box input', 
                            '.post-tag-input', '.tagname', 'input[placeholder*="태그"]',
                            '[data-role="tag-input"]', '.editor-tag input'
                        ];
                        
                        for (var i = 0; i < selectors.length; i++) {
                            var elements = document.querySelectorAll(selectors[i]);
                            if (elements.length > 0) {
                                tagInput = elements[0];
                                break;
                            }
                        }
                        
                        // 태그 입력 필드를 찾지 못했을 경우 제목이 아닌 텍스트 입력 필드 찾기
                        if (!tagInput) {
                            var allInputs = document.querySelectorAll('input[type="text"]');
                            for (var i = 0; i < allInputs.length; i++) {
                                // 제목 입력 필드가 아니라면 태그 입력 필드로 간주
                                if (allInputs[i].id !== 'post-title-inp') {
                                    tagInput = allInputs[i];
                                    break;
                                }
                            }
                        }
                        
                        if (tagInput) {
                            // 값 설정
                            tagInput.value = arguments[0];
                            
                            // 이벤트 트리거
                            var event = new Event('input', { bubbles: true });
                            tagInput.dispatchEvent(event);
                            
                            // Enter 키 이벤트 트리거
                            var enterEvent = new KeyboardEvent('keydown', {
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13,
                                which: 13,
                                bubbles: true
                            });
                            tagInput.dispatchEvent(enterEvent);
                            
                            return true;
                        }
                        
                        return false;
                    """, tags_str)
                    
                    if js_result:
                        print("JavaScript를 통해 태그 입력에 성공했습니다.")
                        tag_found = True
                    else:
                        print("JavaScript로 태그 입력 필드를 찾지 못했습니다.")
                except Exception as js_e:
                    print(f"JavaScript를 통한 태그 입력 중 오류: {js_e}")
            
            # 3. XPath를 사용하여 태그 입력 필드 찾기
            if not tag_found:
                try:
                    tag_xpath_expressions = [
                        "//input[contains(@placeholder, '태그')]",
                        "//div[contains(@class, 'tag') or contains(@class, 'Tag')]//input",
                        "//label[contains(text(), '태그') or contains(text(), '태그입력')]//following::input",
                        "//input[contains(@id, 'tag') or contains(@name, 'tag')]"
                    ]
                    
                    for xpath_expr in tag_xpath_expressions:
                        tag_inputs_xpath = driver.find_elements(By.XPATH, xpath_expr)
                        if tag_inputs_xpath:
                            tag_input = tag_inputs_xpath[0]
                            
                            # 현재 값 지우기
                            tag_input.clear()
                            
                            # 쉼표로 구분된 태그를 하나씩 입력
                            tags_list = blog_post["tags"].split(',')
                            for tag in tags_list:
                                tag = tag.strip()
                                if tag:
                                    tag_input.send_keys(tag)
                                    tag_input.send_keys(Keys.ENTER)
                                    time.sleep(0.5)
                        
                            print(f"XPath({xpath_expr})를 통해 태그 입력 필드를 찾았습니다.")
                            tag_found = True
                            break
                except Exception as xpath_e:
                    print(f"XPath를 통한 태그 입력 필드 찾기 중 오류: {xpath_e}")
            
            # 4. 태그 입력 필드를 찾지 못한 경우
            if not tag_found:
                print("태그 입력 필드를 찾지 못했습니다.")
                
                # 모든 입력 필드 출력
                inputs = driver.find_elements(By.TAG_NAME, "input")
                print(f"페이지에서 {len(inputs)}개의 입력 필드를 찾았습니다.")
                
                text_inputs = []
                for i, inp in enumerate(inputs):
                    try:
                        inp_type = inp.get_attribute("type") or ""
                        if inp_type == "text":
                            inp_name = inp.get_attribute("name") or ""
                            inp_id = inp.get_attribute("id") or ""
                            inp_placeholder = inp.get_attribute("placeholder") or ""
                            inp_class = inp.get_attribute("class") or ""
                            
                            # 제목 입력 필드가 아닌 텍스트 입력 필드
                            if inp_id != "post-title-inp":
                                text_inputs.append((i, inp, inp_name, inp_id, inp_placeholder, inp_class))
                                print(f"텍스트 입력 필드 {i+1}: name='{inp_name}', id='{inp_id}', placeholder='{inp_placeholder}', class='{inp_class}'")
                    except:
                        pass
                
                # 텍스트 입력 필드가 있다면 사용자에게 선택 요청
                if text_inputs:
                    print("\n위 텍스트 입력 필드 중 태그 입력에 사용할 필드 번호를 선택하세요:")
                    choice = input("필드 번호 (Enter 키를 누르면 건너뜀): ")
                    
                    if choice.strip():
                        try:
                            idx = int(choice) - 1
                            if 0 <= idx < len(text_inputs):
                                selected_input = text_inputs[idx][1]
                                selected_input.clear()
                                
                                # 쉼표로 구분된 태그를 하나씩 입력
                                tags_list = blog_post["tags"].split(',')
                                for tag in tags_list:
                                    tag = tag.strip()
                                    if tag:
                                        selected_input.send_keys(tag)
                                        selected_input.send_keys(Keys.ENTER)
                                        time.sleep(0.5)
                                
                                print(f"선택한 입력 필드에 태그를 입력했습니다.")
                                tag_found = True
                        except:
                            print("잘못된 입력입니다.")
        
        except Exception as e:
            print(f"태그 입력 중 오류: {e}")
        
        # 임시저장 버튼 클릭
        try:
            print("임시저장 버튼을 찾습니다...")
            
            # 1. 다양한 임시저장 버튼 선택자로 시도
            save_selectors = [
                ".btn_save", 
                ".btn-save", 
                ".save-button", 
                "#save-temp", 
                "button:contains('임시저장')",
                "button[data-action='save']",
                "button.draft",
                ".preview-btn" # 티스토리의 '미리보기' 버튼 (임시저장 기능 포함)
            ]
            
            save_found = False
            for selector in save_selectors:
                try:
                    save_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    if save_buttons:
                        save_button = save_buttons[0]
                        print(f"임시저장 버튼을 찾았습니다: {selector}")
                        save_button.click()
                        print("임시저장 버튼을 클릭했습니다.")
                        time.sleep(3)  # 저장 처리 대기
                        save_found = True
                        break
                except:
                    pass
            
            # 2. JavaScript를 사용하여 저장 기능 시도
            if not save_found:
                try:
                    print("JavaScript를 통해 임시저장을 시도합니다...")
                    # 티스토리 에디터의 저장 관련 JavaScript 실행
                    driver.execute_script("""
                        if (window.PostEditor && window.PostEditor.save) {
                            window.PostEditor.save();
                            return true;
                        } else if (document.querySelector('#save-temp')) {
                            document.querySelector('#save-temp').click();
                            return true;
                        } else if (document.querySelector('.preview-btn')) {
                            document.querySelector('.preview-btn').click();
                            return true;
                        }
                        return false;
                    """)
                    print("JavaScript를 통해 임시저장 명령을 실행했습니다.")
                    time.sleep(3)
                    save_found = True
                except Exception as js_e:
                    print(f"JavaScript를 통한 임시저장 중 오류: {js_e}")
            
            # 3. XPath를 사용하여 버튼 찾기
            if not save_found:
                try:
                    save_xpath_expressions = [
                        "//button[contains(text(), '임시') or contains(text(), '저장') or contains(text(), '미리보기')]",
                        "//button[contains(@class, 'save') or contains(@id, 'save')]",
                        "//a[contains(text(), '임시저장') or contains(@class, 'save')]"
                    ]
                    
                    for xpath_expr in save_xpath_expressions:
                        save_buttons_xpath = driver.find_elements(By.XPATH, xpath_expr)
                        if save_buttons_xpath:
                            save_button = save_buttons_xpath[0]
                            print(f"XPath를 통해 임시저장 버튼을 찾았습니다: {xpath_expr}")
                            save_button.click()
                            print("XPath를 통해 임시저장 버튼을 클릭했습니다.")
                            time.sleep(3)
                            save_found = True
                            break
                except Exception as xpath_e:
                    print(f"XPath를 통한 임시저장 버튼 찾기 중 오류: {xpath_e}")
            
            # 4. 버튼을 찾지 못한 경우 모든 버튼을 분석
            if not save_found:
                print("임시저장 버튼을 찾지 못했습니다.")
                
                # 페이지의 모든 버튼 요소 출력
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                print(f"페이지에서 {len(all_buttons)}개의 버튼을 찾았습니다.")
                
                # 하단 영역의 버튼들 우선 분석
                try:
                    bottom_buttons = driver.find_elements(By.CSS_SELECTOR, ".editor-footer button, .foot_post button, .write_foot button, #editor-root > div:last-child button")
                    if bottom_buttons:
                        print(f"하단 영역에서 {len(bottom_buttons)}개의 버튼을 찾았습니다.")
                        for i, btn in enumerate(bottom_buttons):
                            try:
                                btn_text = btn.text.strip() or '(텍스트 없음)'
                                btn_class = btn.get_attribute('class') or '(클래스 없음)'
                                btn_id = btn.get_attribute('id') or '(ID 없음)'
                                print(f"하단 버튼 {i+1}: 텍스트='{btn_text}', 클래스='{btn_class}', ID='{btn_id}'")
                                
                                # 임시저장 관련 버튼 추정
                                if (btn_text == '미리보기' or btn_text == '저장' or 
                                    '임시' in btn_text or '저장' in btn_text or 
                                    'save' in btn_text.lower() or 'draft' in btn_text.lower() or
                                    'preview' in btn_text.lower()):
                                    print(f"  => 임시저장 버튼으로 보입니다!")
                                    proceed = input("이 버튼을 임시저장 버튼으로 클릭하시겠습니까? (y/n): ")
                                    if proceed.lower() == 'y':
                                        btn.click()
                                        print("선택한 버튼을 클릭했습니다.")
                                        time.sleep(3)  # 저장 처리 대기
                                        save_found = True
                            except:
                                print(f"버튼 {i+1}: (정보 읽기 실패)")
                except Exception as bottom_e:
                    print(f"하단 버튼 분석 중 오류: {bottom_e}")
                
                # 모든 버튼 검사
                if not save_found:
                    for i, btn in enumerate(all_buttons[:15]):
                        try:
                            btn_text = btn.text.strip() or '(텍스트 없음)'
                            btn_class = btn.get_attribute('class') or '(클래스 없음)'
                            btn_id = btn.get_attribute('id') or '(ID 없음)'
                            print(f"버튼 {i+1}: 텍스트='{btn_text}', 클래스='{btn_class}', ID='{btn_id}'")
                            
                            # 임시저장 관련 텍스트가 있는 버튼 발견
                            if ('임시' in btn_text or '저장' in btn_text or '미리보기' in btn_text or
                                'save' in btn_text.lower() or 'draft' in btn_text.lower() or
                                'preview' in btn_class.lower() or 'save' in btn_class.lower()):
                                print(f"  => 임시저장 버튼으로 보입니다!")
                                
                                proceed = input("이 버튼을 임시저장 버튼으로 클릭하시겠습니까? (y/n): ")
                                if proceed.lower() == 'y':
                                    btn.click()
                                    print("선택한 버튼을 클릭했습니다.")
                                    time.sleep(3)  # 저장 처리 대기
                                    save_found = True
                        except:
                            continue
            
        except Exception as e:
            print(f"임시저장 버튼 클릭 중 오류: {e}")
        
        # 발행 확인
        print("\n=== 글 발행 확인 ===")
        print("임시저장된 글을 발행하시겠습니까?")
        proceed = input("발행하기 (y/n): ")
        
        if proceed.lower() == 'y':
            try:
                print("발행 과정을 시작합니다...")
                
                # 1단계: TinyMCE 모달 창이 있다면 닫기 (클릭 방해 요소 제거)
                try:
                    print("TinyMCE 모달 창 확인 및 제거 중...")
                    driver.execute_script("""
                        var modalBlock = document.querySelector('#mce-modal-block');
                        if (modalBlock) {
                            modalBlock.parentNode.removeChild(modalBlock);
                            console.log('모달 블록 제거됨');
                        }
                        
                        var modalWindows = document.querySelectorAll('.mce-window, .mce-reset');
                        for (var i = 0; i < modalWindows.length; i++) {
                            if (modalWindows[i].style.display !== 'none') {
                                modalWindows[i].style.display = 'none';
                                console.log('모달 창 숨김 처리됨');
                            }
                        }
                    """)
                    print("모달 창 처리 완료")
                except Exception as modal_e:
                    print(f"모달 창 처리 중 오류: {modal_e}")
                
                # 2단계: '완료' 버튼 찾아 클릭
                print("\n1단계: '완료' 버튼을 찾아 클릭합니다...")
                
                # 2-1. CSS 선택자로 완료 버튼 찾기
                complete_button_selectors = [
                    "#publish-layer-btn",       # 티스토리 완료 버튼 ID
                    ".btn_publish", 
                    ".publish-button",
                    "button:contains('완료')",  # 티스토리 완료 버튼 텍스트
                    "button[type='submit']",
                    ".btn_save.save-publish",   # 티스토리 발행 버튼
                    ".btn_post",                # 티스토리 발행 버튼 (다른 클래스)
                    ".btn_submit",              # 티스토리 발행 버튼 (다른 클래스)
                    "#editor-root .editor-footer button:last-child" # 에디터 푸터의 마지막 버튼
                ]
                
                complete_button_found = False
                
                for selector in complete_button_selectors:
                    try:
                        complete_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        if complete_buttons:
                            complete_button = complete_buttons[0]
                            button_text = complete_button.text.strip()
                            print(f"'완료' 버튼을 찾았습니다: {selector} (텍스트: '{button_text}')")
                            
                            # 클릭 전 스크립트 실행하여 방해 요소 제거
                            driver.execute_script("""
                                var modalBlock = document.querySelector('#mce-modal-block');
                                if (modalBlock) modalBlock.remove();
                            """)
                            
                            # 버튼 클릭
                            complete_button.click()
                            print("'완료' 버튼을 클릭했습니다.")
                            time.sleep(3)  # 모달 대화상자가 나타날 때까지 대기
                            complete_button_found = True
                            break
                    except Exception as btn_e:
                        print(f"'{selector}' 선택자로 버튼 클릭 시도 중 오류: {btn_e}")
                
                # 2-2. JavaScript로 완료 버튼 클릭 시도
                if not complete_button_found:
                    try:
                        print("JavaScript를 통해 '완료' 버튼 클릭을 시도합니다...")
                        result = driver.execute_script("""
                            // 완료 버튼 ID로 직접 찾기
                            var publishBtn = document.querySelector('#publish-layer-btn');
                            if (publishBtn) {
                                publishBtn.click();
                                return "ID로 버튼 클릭";
                            }
                            
                            // 버튼 텍스트로 찾기
                            var buttons = document.querySelectorAll('button');
                            for (var i = 0; i < buttons.length; i++) {
                                if (buttons[i].textContent.includes('완료')) {
                                    buttons[i].click();
                                    return "텍스트로 버튼 클릭";
                                }
                            }
                            
                            // 에디터 API 사용
                            if (window.PostEditor && window.PostEditor.publish) {
                                window.PostEditor.publish();
                                return "PostEditor API 사용";
                            }
                            
                            // 하단 영역의 마지막 버튼 클릭
                            var footerButtons = document.querySelectorAll('.editor-footer button, .foot_post button, .write_foot button');
                            if (footerButtons.length > 0) {
                                footerButtons[footerButtons.length - 1].click();
                                return "하단 마지막 버튼 클릭";
                            }
                            
                            return false;
                        """)
                        
                        if result:
                            print(f"JavaScript를 통해 '완료' 버튼을 클릭했습니다: {result}")
                            time.sleep(3)  # 모달 대화상자가 나타날 때까지 대기
                            complete_button_found = True
                        else:
                            print("JavaScript로 '완료' 버튼을 찾지 못했습니다.")
                    except Exception as js_e:
                        print(f"JavaScript를 통한 '완료' 버튼 클릭 중 오류: {js_e}")
                
                # 2-3. XPath로 완료 버튼 찾기
                if not complete_button_found:
                    try:
                        complete_xpath_expressions = [
                            "//button[contains(text(), '완료')]",
                            "//button[@id='publish-layer-btn']",
                            "//button[contains(@class, 'publish') or contains(@id, 'publish')]",
                            "//div[contains(@class, 'editor-footer') or contains(@class, 'foot_post')]//button[last()]"
                        ]
                        
                        for xpath_expr in complete_xpath_expressions:
                            complete_buttons_xpath = driver.find_elements(By.XPATH, xpath_expr)
                            if complete_buttons_xpath:
                                complete_button = complete_buttons_xpath[0]
                                button_text = complete_button.text.strip()
                                print(f"XPath로 '완료' 버튼을 찾았습니다: {xpath_expr} (텍스트: '{button_text}')")
                                
                                # 클릭 전 스크립트 실행하여 방해 요소 제거
                                driver.execute_script("document.querySelector('#mce-modal-block')?.remove();")
                                
                                # 버튼 클릭
                                complete_button.click()
                                print("XPath로 찾은 '완료' 버튼을 클릭했습니다.")
                                time.sleep(3)  # 모달 대화상자가 나타날 때까지 대기
                                complete_button_found = True
                                break
                    except Exception as xpath_e:
                        print(f"XPath를 통한 '완료' 버튼 찾기 중 오류: {xpath_e}")
                
                # 2-4. 버튼을 찾지 못한 경우, 하단 영역의 모든 버튼 표시
                if not complete_button_found:
                    try:
                        print("'완료' 버튼을 찾지 못했습니다. 하단 영역 버튼 분석 중...")
                        
                        bottom_buttons = driver.find_elements(By.CSS_SELECTOR, 
                            ".editor-footer button, .foot_post button, .write_foot button, #editor-root > div:last-child button")
                        
                        if bottom_buttons:
                            print(f"하단 영역에서 {len(bottom_buttons)}개의 버튼을 찾았습니다.")
                            
                            for i, btn in enumerate(bottom_buttons):
                                try:
                                    btn_text = btn.text.strip() or '(텍스트 없음)'
                                    btn_class = btn.get_attribute('class') or '(클래스 없음)'
                                    btn_id = btn.get_attribute('id') or '(ID 없음)'
                                    print(f"하단 버튼 {i+1}: 텍스트='{btn_text}', 클래스='{btn_class}', ID='{btn_id}'")
                                except:
                                    print(f"버튼 {i+1}: (정보 읽기 실패)")
                            
                            # 일반적으로 마지막 버튼이 '완료' 버튼
                            print("\n일반적으로 마지막 버튼이 '완료' 버튼입니다.")
                            proceed = input("마지막 버튼을 '완료' 버튼으로 클릭하시겠습니까? (y/n): ")
                            
                            if proceed.lower() == 'y':
                                try:
                                    # 클릭 전 스크립트 실행하여 방해 요소 제거
                                    driver.execute_script("document.querySelector('#mce-modal-block')?.remove();")
                                    
                                    # 마지막 버튼 클릭
                                    bottom_buttons[-1].click()
                                    print("마지막 버튼을 클릭했습니다.")
                                    time.sleep(3)  # 모달 대화상자가 나타날 때까지 대기
                                    complete_button_found = True
                                except Exception as click_e:
                                    print(f"버튼 클릭 중 오류: {click_e}")
                        else:
                            print("하단 영역에서 버튼을 찾지 못했습니다.")
                    except Exception as bottom_e:
                        print(f"하단 버튼 분석 중 오류: {bottom_e}")
                
                # 3단계: '공개 발행' 버튼 찾아 클릭 (2단계 성공 시)
                if complete_button_found:
                    print("\n2단계: '공개 발행' 버튼을 찾아 클릭합니다...")
                    time.sleep(2)  # 모달이 완전히 로드될 때까지 대기
                    
                    # 3-1. CSS 선택자로 공개 발행 버튼 찾기
                    publish_selectors = [
                        ".layer_post button:contains('공개')",          # 공개 텍스트가 있는 버튼
                        ".layer_post button:contains('발행')",          # 발행 텍스트가 있는 버튼
                        ".layer_post .btn.btn-default:not(.btn-cancel)", # 취소 버튼이 아닌 기본 버튼
                        ".layer_post .publish-button",
                        ".layer_post button:last-child",               # 레이어의 마지막 버튼
                        ".layer_post .confirm-button",
                        "#confirmPublishButton"
                    ]
                    
                    publish_button_found = False
                    
                    for selector in publish_selectors:
                        try:
                            publish_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                            if publish_buttons:
                                for btn in publish_buttons:
                                    btn_text = btn.text.strip()
                                    print(f"'공개 발행' 버튼 후보: {selector} (텍스트: '{btn_text}')")
                                    
                                    # '공개' 또는 '발행' 텍스트가 있는 버튼 우선
                                    if '공개' in btn_text or '발행' in btn_text:
                                        print(f"'공개 발행' 버튼을 찾았습니다: {selector} (텍스트: '{btn_text}')")
                                        btn.click()
                                        print("'공개 발행' 버튼을 클릭했습니다.")
                                        time.sleep(5)  # 발행 처리 대기
                                        publish_button_found = True
                                        break
                                
                                # 특정 텍스트가 없지만 버튼이 있으면 첫 번째 버튼 클릭
                                if not publish_button_found and publish_buttons:
                                    btn_text = publish_buttons[0].text.strip()
                                    print(f"'공개 발행' 버튼을 찾았습니다: {selector} (텍스트: '{btn_text}')")
                                    publish_buttons[0].click()
                                    print("'공개 발행' 버튼을 클릭했습니다.")
                                    time.sleep(5)  # 발행 처리 대기
                                    publish_button_found = True
                                
                                if publish_button_found:
                                    break
                        except Exception as btn_e:
                            print(f"'{selector}' 선택자로 '공개 발행' 버튼 클릭 시도 중 오류: {btn_e}")
                    
                    # 3-2. JavaScript로 공개 발행 버튼 클릭 시도
                    if not publish_button_found:
                        try:
                            print("JavaScript를 통해 '공개 발행' 버튼 클릭을 시도합니다...")
                            result = driver.execute_script("""
                                // 레이어 안의 모든 버튼 찾기
                                var layerButtons = document.querySelectorAll('.layer_post button, .layer button');
                                console.log('레이어 버튼 수: ' + layerButtons.length);
                                
                                // 버튼 텍스트로 찾기
                                for (var i = 0; i < layerButtons.length; i++) {
                                    var btnText = layerButtons[i].textContent.trim();
                                    console.log('버튼 ' + i + ': ' + btnText);
                                    
                                    if (btnText.includes('공개') || btnText.includes('발행')) {
                                        console.log('텍스트로 버튼 찾음: ' + btnText);
                                        layerButtons[i].click();
                                        return "텍스트로 버튼 클릭: " + btnText;
                                    }
                                }
                                
                                // 레이어의 마지막 버튼 클릭 (일반적으로 확인/공개 버튼)
                                if (layerButtons.length > 0) {
                                    console.log('마지막 버튼 클릭');
                                    layerButtons[layerButtons.length - 1].click();
                                    return "마지막 버튼 클릭";
                                }
                                
                                return false;
                            """)
                            
                            if result:
                                print(f"JavaScript를 통해 '공개 발행' 버튼을 클릭했습니다: {result}")
                                time.sleep(5)  # 발행 처리 대기
                                publish_button_found = True
                            else:
                                print("JavaScript로 '공개 발행' 버튼을 찾지 못했습니다.")
                        except Exception as js_e:
                            print(f"JavaScript를 통한 '공개 발행' 버튼 클릭 중 오류: {js_e}")
                    
                    # 3-3. XPath로 공개 발행 버튼 찾기
                    if not publish_button_found:
                        try:
                            publish_xpath_expressions = [
                                "//div[contains(@class, 'layer_post') or contains(@class, 'layer')]//button[contains(text(), '공개')]",
                                "//div[contains(@class, 'layer_post') or contains(@class, 'layer')]//button[contains(text(), '발행')]",
                                "//div[contains(@class, 'layer_post') or contains(@class, 'layer')]//button[last()]"
                            ]
                            
                            for xpath_expr in publish_xpath_expressions:
                                publish_buttons_xpath = driver.find_elements(By.XPATH, xpath_expr)
                                if publish_buttons_xpath:
                                    publish_button = publish_buttons_xpath[0]
                                    btn_text = publish_button.text.strip()
                                    print(f"XPath로 '공개 발행' 버튼을 찾았습니다: {xpath_expr} (텍스트: '{btn_text}')")
                                    publish_button.click()
                                    print("XPath로 찾은 '공개 발행' 버튼을 클릭했습니다.")
                                    time.sleep(5)  # 발행 처리 대기
                                    publish_button_found = True
                                    break
                        except Exception as xpath_e:
                            print(f"XPath를 통한 '공개 발행' 버튼 찾기 중 오류: {xpath_e}")
                    
                    # 3-4. 버튼을 찾지 못한 경우, 레이어의 모든 버튼 표시
                    if not publish_button_found:
                        try:
                            print("'공개 발행' 버튼을 찾지 못했습니다. 레이어의 모든 버튼을 분석합니다...")
                            
                            # 레이어 안의 모든 버튼 찾기
                            layer_buttons = driver.find_elements(By.CSS_SELECTOR, 
                                ".layer_post button, .layer button, .layer_toolbar button, #layer-publish button")
                            
                            if layer_buttons:
                                print(f"레이어에서 {len(layer_buttons)}개의 버튼을 찾았습니다.")
                                
                                for i, btn in enumerate(layer_buttons):
                                    try:
                                        btn_text = btn.text.strip() or '(텍스트 없음)'
                                        btn_class = btn.get_attribute('class') or '(클래스 없음)'
                                        btn_id = btn.get_attribute('id') or '(ID 없음)'
                                        print(f"레이어 버튼 {i+1}: 텍스트='{btn_text}', 클래스='{btn_class}', ID='{btn_id}'")
                                    except:
                                        print(f"버튼 {i+1}: (정보 읽기 실패)")
                                
                                # 버튼 선택 요청
                                btn_index = input("\n위 버튼 중 '공개 발행' 버튼으로 사용할 버튼 번호를 입력하세요 (건너뛰려면 Enter): ")
                                
                                if btn_index.strip():
                                    try:
                                        idx = int(btn_index) - 1
                                        if 0 <= idx < len(layer_buttons):
                                            layer_buttons[idx].click()
                                            print(f"{idx+1}번 버튼을 클릭했습니다.")
                                            time.sleep(5)  # 발행 처리 대기
                                            publish_button_found = True
                                    except ValueError:
                                        print("유효한 숫자를 입력하세요.")
                                
                                # 버튼을 선택하지 않았으면 마지막 버튼 제안
                                if not publish_button_found:
                                    proceed = input("레이어의 마지막 버튼을 '공개 발행' 버튼으로 클릭하시겠습니까? (y/n): ")
                                    if proceed.lower() == 'y':
                                        try:
                                            layer_buttons[-1].click()  # 마지막 버튼 클릭
                                            print("마지막 버튼을 클릭했습니다.")
                                            time.sleep(5)  # 발행 처리 대기
                                            publish_button_found = True
                                        except Exception as click_e:
                                            print(f"버튼 클릭 중 오류: {click_e}")
                            else:
                                print("레이어에서 버튼을 찾지 못했습니다.")
                        except Exception as layer_e:
                            print(f"레이어 버튼 분석 중 오류: {layer_e}")
                    
                    # 발행 결과 안내
                    if publish_button_found:
                        print("\n포스팅이 성공적으로 발행되었습니다!")
                    else:
                        print("\n발행 확인 단계에서 '공개 발행' 버튼을 찾지 못했습니다.")
                        print("포스팅은 임시저장 상태로 남아있습니다.")
                else:
                    print("\n'완료' 버튼을 찾지 못해 발행 과정을 완료할 수 없습니다.")
                    print("포스팅은 임시저장 상태로 남아있습니다.")
                
            except Exception as e:
                print(f"발행 과정 중 오류 발생: {e}")
        else:
            print("발행이 취소되었습니다. 글은 임시저장되었습니다.")
        
    except Exception as e:
        print(f"전체 과정에서 오류 발생: {e}")
    
    finally:
        # 작업 완료 후 대기
        input("작업이 완료되었습니다. 브라우저를 종료하려면 Enter 키를 누르세요...")
        driver.quit()

# 메인 함수
if __name__ == "__main__":
    print("ChatGPT를 이용한 티스토리 자동 포스팅 시작")
    login_and_post_to_tistory() 