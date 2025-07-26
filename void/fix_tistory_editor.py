"""
티스토리 에디터 HTML 콘텐츠 설정 문제를 해결하는 코드 모음
"""

# 티스토리 에디터에 HTML 콘텐츠를 설정하는 개선된 코드
# auto_post_generator.py 파일 "set_html_content" 함수에 통합해야 함

def apply_html_content_to_editor(driver, content, iframe_editor):
    """HTML 콘텐츠를 티스토리 에디터에 효과적으로 적용하는 함수"""
    try:
        # iframe으로 전환
        if iframe_editor:
            driver.switch_to.frame(iframe_editor)
            
            # 1. 티스토리 에디터에서 실제로 콘텐츠를 저장하는 textarea 찾기
            textarea_result = driver.execute_script("""
                // 모든 textarea 요소 찾기
                var textareas = document.querySelectorAll('textarea');
                console.log("iframe 내 textarea 요소 개수:", textareas.length);
                
                var success = false;
                
                // 콘텐츠용 textarea에 내용 설정 (제목, 태그 필드 제외)
                for (var i = 0; i < textareas.length; i++) {
                    var ta = textareas[i];
                    if (ta.id === 'post-title-inp' || ta.className.includes('textarea_tit') || ta.id === 'tag') {
                        console.log("제목/태그 textarea 제외:", i);
                        continue;
                    }
                    
                    try {
                        // 콘텐츠 설정
                        ta.value = arguments[0];
                        
                        // 이벤트 발생시켜 티스토리 에디터가 변화 감지하도록 함
                        var events = ['input', 'change', 'keyup', 'keydown', 'focus', 'blur'];
                        events.forEach(function(eventType) {
                            ta.dispatchEvent(new Event(eventType, { bubbles: true }));
                        });
                        
                        // 키보드 입력 시뮬레이션 (티스토리 에디터 활성화에 필요)
                        ta.dispatchEvent(new KeyboardEvent('keypress', {
                            bubbles: true, 
                            key: ' ',
                            keyCode: 32,
                            which: 32
                        }));
                        
                        console.log("textarea에 콘텐츠 설정 성공:", i);
                        success = true;
                    } catch (e) {
                        console.error("textarea 설정 오류:", e);
                    }
                }
                
                // CodeMirror 에디터 인스턴스 접근 시도 (티스토리 HTML 에디터)
                var cmElements = document.querySelectorAll('.CodeMirror');
                console.log("CodeMirror 요소 개수:", cmElements.length);
                
                if (cmElements.length > 0) {
                    try {
                        var cmElement = cmElements[0];
                        
                        // CodeMirror 인스턴스 직접 접근
                        if (cmElement.CodeMirror) {
                            cmElement.CodeMirror.setValue(arguments[0]);
                            cmElement.CodeMirror.refresh();
                            cmElement.CodeMirror.focus();
                            console.log("CodeMirror 인스턴스에 값 설정 성공");
                            success = true;
                        }
                        
                        // 중요: CodeMirror의 숨겨진 textarea 요소 찾아서 값 설정
                        var cmTextarea = cmElement.querySelector('textarea');
                        if (cmTextarea) {
                            cmTextarea.value = arguments[0];
                            
                            // 이벤트 발생
                            var events = ['input', 'change', 'keyup'];
                            events.forEach(function(eventType) {
                                cmTextarea.dispatchEvent(new Event(eventType, { bubbles: true }));
                            });
                            console.log("CodeMirror textarea에 값 설정 성공");
                            success = true;
                        }
                        
                        // CodeMirror 에디터의 pre 요소들에도 적용
                        var preElements = cmElement.querySelectorAll('pre.CodeMirror-line');
                        if (preElements.length > 0) {
                            console.log("CodeMirror pre 요소 개수:", preElements.length);
                            
                            var firstPre = preElements[0];
                            var spanElement = firstPre.querySelector('span[role="presentation"]');
                            if (spanElement) {
                                spanElement.innerHTML = arguments[0];
                                console.log("CodeMirror span 요소에 값 설정 성공");
                                success = true;
                            } else {
                                firstPre.innerHTML = '<span role="presentation">' + arguments[0] + '</span>';
                                console.log("CodeMirror pre에 새 span 요소 생성 및 설정");
                                success = true;
                            }
                            
                            // 변경사항 알림
                            firstPre.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    } catch (e) {
                        console.error("CodeMirror 처리 중 오류:", e);
                    }
                }
                
                // body 요소에도 직접 설정 (가장 안전한 방법)
                try {
                    document.body.innerHTML = arguments[0];
                    console.log("body에 직접 콘텐츠 설정");
                    success = true;
                } catch (e) {
                    console.error("body에 콘텐츠 설정 중 오류:", e);
                }
                
                // contenteditable 요소 시도
                var editables = document.querySelectorAll('[contenteditable="true"]');
                if (editables.length > 0) {
                    for (var i = 0; i < editables.length; i++) {
                        try {
                            editables[i].innerHTML = arguments[0];
                            editables[i].dispatchEvent(new Event('input', { bubbles: true }));
                            console.log("contenteditable 요소에 값 설정 성공:", i);
                            success = true;
                        } catch (e) {
                            console.error("contenteditable 설정 오류:", e);
                        }
                    }
                }
                
                return {
                    success: success,
                    message: success ? "티스토리 에디터 동기화 성공" : "티스토리 에디터 동기화 실패"
                };
            """, content)
            
            # 결과 확인
            if textarea_result and textarea_result.get("success"):
                print(f"iframe 내부 에디터 동기화 성공: {textarea_result.get('message')}")
            else:
                print("iframe 내부 에디터 동기화 실패")
            
            # iframe 종료
            driver.switch_to.default_content()
            
            # 부모 프레임에서 티스토리 에디터 API 직접 접근 시도
            parent_result = driver.execute_script("""
                try {
                    // 티스토리 에디터 접근
                    if (window.tistoryEditor) {
                        console.log("tistoryEditor API 발견");
                        
                        // 우선순위에 따라 메소드 시도
                        if (typeof tistoryEditor.setHtmlContent === 'function') {
                            tistoryEditor.setHtmlContent(arguments[0]);
                            return "setHtmlContent 호출 성공";
                        }
                        
                        if (typeof tistoryEditor.setValue === 'function') {
                            tistoryEditor.setValue(arguments[0]);
                            return "setValue 호출 성공";
                        }
                        
                        if (typeof tistoryEditor.setContent === 'function') {
                            tistoryEditor.setContent(arguments[0]);
                            return "setContent 호출 성공";
                        }
                    }
                    
                    // iframe에 직접 접근 시도
                    var iframes = document.querySelectorAll('iframe');
                    for (var i = 0; i < iframes.length; i++) {
                        try {
                            var iframe = iframes[i];
                            var iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                            
                            if (iframeDoc && iframeDoc.body) {
                                // 모든 iframe 내부의 textarea 요소 확인
                                var textareas = iframeDoc.querySelectorAll('textarea');
                                for (var j = 0; j < textareas.length; j++) {
                                    var ta = textareas[j];
                                    if (ta.id !== 'post-title-inp' && !ta.className.includes('textarea_tit')) {
                                        ta.value = arguments[0];
                                        var events = ['input', 'change'];
                                        events.forEach(function(event) {
                                            ta.dispatchEvent(new Event(event, {bubbles: true}));
                                        });
                                        return "iframe " + i + "의 textarea에 값 설정 성공";
                                    }
                                }
                            }
                        } catch (e) {
                            console.log("iframe " + i + " 접근 오류:", e);
                        }
                    }
                    
                    return "적합한 에디터 API 또는 요소를 찾지 못함";
                } catch (e) {
                    return "오류 발생: " + e.message;
                }
            """, content)
            
            # 결과 출력
            print(f"부모 프레임에서 에디터 설정 시도 결과: {parent_result}")
            
            return True
        else:
            print("iframe을 찾지 못했습니다.")
            return False
    except Exception as e:
        print(f"HTML 콘텐츠 적용 중 오류: {e}")
        try:
            # 오류 발생시 iframe에서 복구
            driver.switch_to.default_content()
            print("오류 후 기본 문서로 복귀")
        except:
            pass
        return False

# 사용법:
# 1. auto_post_generator.py의 set_html_content 함수 내에 위 코드 로직 삽입
# 2. CodeMirror 에디터에 콘텐츠 설정이 실패할 경우 이 코드를 사용하도록 수정 