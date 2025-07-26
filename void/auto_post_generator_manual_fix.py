"""
이 코드는 auto_post_generator.py에서 2550-2600줄 부근에 있는 들여쓰기 오류를 수정한 버전입니다.
다음 단계로 수정하세요:
1. auto_post_generator.py 백업 생성 (이미 완료)
2. auto_post_generator.py를 텍스트 에디터로 열기
3. 2550-2600줄 부근의 코드를 아래 코드로 대체
4. 파일 저장 후 실행
"""

# 수정할 코드 시작 (2550-2600 줄 영역)
                            # iframe으로 다시 전환
                            driver.switch_to.frame(iframe_editor)
                            
                            content_set_success = True
                    except Exception as body_e:
                        print(f"향상된 body 요소 설정 시도 중 오류: {body_e}")
                        # iframe에서 복구
                        try:
                            driver.switch_to.default_content()
                            print("오류 발생 후 기본 문서로 복귀")
                        except Exception as recovery_e:
                            print(f"복구 중 추가 오류: {recovery_e}")
                
                # 방법 D: contenteditable 요소 찾아서 설정
                if not content_set_success:
                    try:
                        print("iframe 내 contenteditable 요소 찾기 시도...")
                        editable_result = driver.execute_script("""
                            var editable = document.querySelector('[contenteditable="true"]');
                            if (editable) {
                                editable.innerHTML = arguments[0];
                                
                                // input 이벤트 발생
                                var inputEvent = new Event('input', { bubbles: true });
                                editable.dispatchEvent(inputEvent);
                                
                                // change 이벤트 발생
                                var changeEvent = new Event('change', { bubbles: true });
                                editable.dispatchEvent(changeEvent);
                                
                                return {
                                    success: true,
                                    message: "contenteditable 요소 설정 성공",
                                    contentLength: editable.innerHTML.length
                                };
                            }
                            return { success: false, message: "contenteditable 요소 없음", contentLength: 0 };
                        """, content)
# 수정할 코드 끝 