"""
티스토리 자동 포스팅 도구의 들여쓰기 오류를 수정하는 스크립트
이 스크립트는 auto_post_generator.py 파일에서 2560-2585줄 부근에 있는 들여쓰기 오류를 수정합니다.
"""

import re
import os
import sys

def fix_indentation_error():
    """들여쓰기 오류를 수정하는 함수"""
    print("티스토리 자동 포스팅 도구의 들여쓰기 오류를 수정합니다...")
    
    # 파일 경로
    source_file = "auto_post_generator.py"
    backup_file = "auto_post_generator.py.bak"
    fixed_file = "auto_post_generator.py.fixed"
    
    # 백업 생성
    if not os.path.exists(backup_file):
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"백업 파일 생성: {backup_file}")
        except Exception as e:
            print(f"백업 생성 중 오류 발생: {e}")
            return False
    else:
        print(f"백업 파일이 이미 존재합니다: {backup_file}")
    
    try:
        # 파일 내용 읽기
        with open(source_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"파일을 읽었습니다. 총 {len(lines)}줄")
        
        # 문제가 있는 부분 찾기 및 수정
        fixed_lines = []
        
        # 오류가 있는 부분 식별을 위한 패턴
        except_pattern = re.compile(r'^\s+except Exception as body_e:')
        recovery_pattern = re.compile(r'^\s+except Exception as recovery_e:')
        iframe_pattern = re.compile(r'^\s+driver\.switch_to\.frame\(iframe_editor\)')
        
        # 수정 모드 플래그
        fix_mode = False
        skip_block = False
        found_error = False
        fixed_count = 0
        
        for i, line in enumerate(lines):
            # 문제 영역 시작 확인
            if "향상된 body 요소 설정 시도 중 오류:" in line and fix_mode is False:
                fixed_lines.append(line)
                fix_mode = True
                found_error = True
                print(f"수정 영역 시작 발견: {i+1}번 줄")
                continue
            
            # 문제 영역 끝 확인
            if fix_mode and "# 방법 D: contenteditable 요소 찾아서 설정" in line:
                fixed_lines.append(line)
                fix_mode = False
                skip_block = False
                print(f"수정 영역 끝 발견: {i+1}번 줄")
                continue
            
            # 문제 영역 내부에서의 처리
            if fix_mode:
                # 중복된 except 블록 시작 확인
                if except_pattern.match(line) and skip_block is False:
                    # 첫 번째 except 블록은 유지
                    fixed_lines.append(line)
                    skip_block = True
                    print(f"첫 번째 except 블록 유지: {i+1}번 줄")
                    continue
                elif except_pattern.match(line) and skip_block is True:
                    # 추가 except 블록은 무시
                    print(f"중복 except 블록 무시: {i+1}번 줄")
                    fixed_count += 1
                    continue
                
                # 잘못된 들여쓰기된 iframe 코드 행 처리
                if iframe_pattern.match(line) and " " * 25 + "driver" in line:
                    # 이 줄은 무시하고 다음 두 줄도 무시
                    print(f"들여쓰기 오류 줄 무시: {i+1}번 줄 - {line.strip()}")
                    fixed_count += 1
                    continue
                
                if skip_block:
                    # 중복 블록 내부는 무시
                    if recovery_pattern.match(line):
                        skip_block = False
                        print(f"중복 except 블록 끝: {i+1}번 줄")
                    else:
                        print(f"중복 블록 내용 무시: {i+1}번 줄")
                        fixed_count += 1
                    continue
                
                fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        if not found_error:
            print("수정할 오류 영역을 찾지 못했습니다!")
            return False
        
        print(f"총 {fixed_count}개의 중복/오류 줄 제거됨")
        
        # 수정된 내용 저장
        with open(fixed_file, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print(f"수정 완료. 수정된 파일: {fixed_file}")
        
        # 원본 파일 교체
        os.replace(fixed_file, source_file)
        print(f"원본 파일 교체 완료.")
        
        return True
    
    except Exception as e:
        print(f"오류 수정 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_indentation_error()
    if success:
        print("수정이 성공적으로 완료되었습니다.")
    else:
        print("수정 중 오류가 발생했습니다.") 