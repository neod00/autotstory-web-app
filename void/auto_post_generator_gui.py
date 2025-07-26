import sys
import os
import time
import json
import pickle
import threading
import traceback
from pathlib import Path
from functools import partial

# PyQt5 플러그인 경로 설정
if hasattr(sys, 'frozen'):
    path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt', 'plugins')
    os.environ['QT_PLUGIN_PATH'] = path
else:
    # 사이트 패키지에서 플러그인 경로 찾기
    for p in sys.path:
        if os.path.isdir(p) and 'site-packages' in p:
            plugin_path = os.path.join(p, 'PyQt5', 'Qt5', 'plugins')
            if os.path.exists(plugin_path):
                os.environ['QT_PLUGIN_PATH'] = plugin_path
                break
            plugin_path = os.path.join(p, 'PyQt5', 'Qt', 'plugins')
            if os.path.exists(plugin_path):
                os.environ['QT_PLUGIN_PATH'] = plugin_path
                break

# PyQt5 모듈 가져오기
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QTabWidget, QPushButton, 
                            QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, 
                            QRadioButton, QGroupBox, QFileDialog, QMessageBox, 
                            QDialog, QProgressBar, QListWidget, QListWidgetItem, 
                            QSystemTrayIcon, QMenu, QAction, QSplitter, QToolBar, 
                            QStatusBar, QScrollArea, QFormLayout, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, QSettings
from PyQt5.QtGui import QIcon, QFont, QPixmap, QTextCursor, QDesktopServices, QColor

# 스타일시트 (QDarkStyle 사용)
import qdarkstyle

# 기존 auto_post_generator.py에서 사용되는 기능 가져오기
from auto_post_generator import (save_cookies, load_cookies, save_local_storage, 
                                load_local_storage, is_logged_in, 
                                generate_blog_content_with_retry, publish_post, 
                                write_post, BLOG_URL, BLOG_MANAGE_URL, 
                                BLOG_NEW_POST_URL, BLOG_TOPICS, COOKIES_FILE, 
                                LOCAL_STORAGE_FILE)

# 웹 드라이버 관련 모듈
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# OpenAI 라이브러리
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

# PyQt5 플러그인 경로 설정
if hasattr(sys, 'frozen'):
    path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt', 'plugins')
    os.environ['QT_PLUGIN_PATH'] = path
else:
    # 사이트 패키지에서 플러그인 경로 찾기
    for p in sys.path:
        if os.path.isdir(p) and 'site-packages' in p:
            plugin_path = os.path.join(p, 'PyQt5', 'Qt5', 'plugins')
            if os.path.exists(plugin_path):
                os.environ['QT_PLUGIN_PATH'] = plugin_path
                break
            plugin_path = os.path.join(p, 'PyQt5', 'Qt', 'plugins')
            if os.path.exists(plugin_path):
                os.environ['QT_PLUGIN_PATH'] = plugin_path
                break

# 로그 출력 리디렉션을 위한 클래스
class LogStream:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        
    def write(self, text):
        self.buffer += text
        if '\n' in self.buffer:
            self.text_widget.append(self.buffer.rstrip())
            self.text_widget.moveCursor(QTextCursor.End)
            self.buffer = ""
    
    def flush(self):
        if self.buffer:
            self.text_widget.append(self.buffer.rstrip())
            self.text_widget.moveCursor(QTextCursor.End)
            self.buffer = ""


# 웹드라이버 작업을 위한 스레드 클래스
class WebDriverThread(QThread):
    update_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, function, args=(), kwargs=None):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs or {}
        
    def run(self):
        try:
            result = self.function(*self.args, **self.kwargs)
            self.finished_signal.emit(True, result if isinstance(result, dict) else {})
        except Exception as e:
            self.error_signal.emit(str(e))
            self.update_signal.emit(f"오류 발생: {str(e)}\n{traceback.format_exc()}")
            self.finished_signal.emit(False, {})


# 콘텐츠 생성을 위한 스레드 클래스
class ContentGenerationThread(QThread):
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, topic, format_type):
        super().__init__()
        self.topic = topic
        self.format_type = format_type
        
    def run(self):
        try:
            self.update_signal.emit(f"'{self.topic}' 주제로 블로그 콘텐츠를 생성 중입니다...")
            blog_post = generate_blog_content_with_retry(self.topic, self.format_type)
            self.update_signal.emit(f"콘텐츠 생성 완료!\n제목: {blog_post['title']}")
            self.finished_signal.emit(blog_post)
        except Exception as e:
            self.error_signal.emit(str(e))
            self.update_signal.emit(f"콘텐츠 생성 중 오류 발생: {str(e)}\n{traceback.format_exc()}")


# 메인 윈도우 클래스
class TistoryBloggerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.driver = None
        self.blog_post = None
        self.init_ui()
        self.settings = QSettings("AutoTstory", "TistoryBlogger")
        self.load_settings()
        
    def init_ui(self):
        # 윈도우 설정
        self.setWindowTitle("Auto Tstory - 티스토리 자동 포스팅")
        self.setMinimumSize(900, 700)
        
        # 메인 위젯 및 레이아웃 설정
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # 탭 위젯 생성
        self.tabs = QTabWidget()
        self.setup_login_tab()
        self.setup_content_tab()
        self.setup_post_tab()
        self.setup_settings_tab()
        
        # 탭 추가
        self.tabs.addTab(self.login_tab, "로그인")
        self.tabs.addTab(self.content_tab, "콘텐츠 생성")
        self.tabs.addTab(self.post_tab, "게시물 작성")
        self.tabs.addTab(self.settings_tab, "설정")
        
        # 로그 출력 영역
        log_group = QGroupBox("로그")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("background-color: #222; color: #ddd;")
        log_layout.addWidget(self.log_text)
        
        # 상태 표시줄
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("프로그램이 시작되었습니다.")
        
        # 메인 레이아웃에 위젯 추가
        main_layout.addWidget(self.tabs, 3)
        main_layout.addWidget(log_group, 1)
        
        # 중앙 위젯 설정
        self.setCentralWidget(main_widget)
        
        # 로그 리디렉션 설정
        self.log_stream = LogStream(self.log_text)
        
        # 스타일시트 적용
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
        # 최종 UI 업데이트
        self.show()
        self.log_text.append("티스토리 자동 포스팅 프로그램이 시작되었습니다.")
        self.log_text.append("시작하려면 먼저 로그인 탭에서 로그인을 진행해주세요.")

    def setup_login_tab(self):
        """로그인 탭 설정"""
        self.login_tab = QWidget()
        login_layout = QVBoxLayout(self.login_tab)
        
        # 안내 레이블
        header_label = QLabel("티스토리 로그인")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        
        info_label = QLabel("자동 로그인을 시도하거나 수동 로그인을 진행해주세요.")
        info_label.setWordWrap(True)
        
        # 자동 로그인 그룹
        auto_login_group = QGroupBox("자동 로그인")
        auto_login_layout = QVBoxLayout(auto_login_group)
        
        auto_login_info = QLabel("저장된 세션 정보를 이용해 자동으로 로그인합니다.")
        auto_login_info.setWordWrap(True)
        
        self.auto_login_btn = QPushButton("자동 로그인 시도")
        self.auto_login_btn.setIcon(QIcon.fromTheme("network-connect"))
        self.auto_login_btn.clicked.connect(self.start_auto_login)
        
        auto_login_layout.addWidget(auto_login_info)
        auto_login_layout.addWidget(self.auto_login_btn)
        
        # 수동 로그인 그룹
        manual_login_group = QGroupBox("수동 로그인")
        manual_login_layout = QVBoxLayout(manual_login_group)
        
        manual_login_info = QLabel("브라우저 창에서 직접 로그인을 진행합니다.")
        manual_login_info.setWordWrap(True)
        
        self.manual_login_btn = QPushButton("수동 로그인 시작")
        self.manual_login_btn.setIcon(QIcon.fromTheme("document-edit"))
        self.manual_login_btn.clicked.connect(self.start_manual_login)
        
        manual_login_layout.addWidget(manual_login_info)
        manual_login_layout.addWidget(self.manual_login_btn)
        
        # 로그인 상태 확인 그룹
        status_group = QGroupBox("로그인 상태")
        status_layout = QGridLayout(status_group)
        
        self.login_status_label = QLabel("로그인 상태: 확인되지 않음")
        self.login_status_label.setStyleSheet("font-weight: bold;")
        
        self.check_login_btn = QPushButton("로그인 상태 확인")
        self.check_login_btn.clicked.connect(self.check_login_status)
        
        status_layout.addWidget(self.login_status_label, 0, 0)
        status_layout.addWidget(self.check_login_btn, 0, 1)
        
        # 브라우저 제어 그룹
        browser_group = QGroupBox("브라우저 제어")
        browser_layout = QGridLayout(browser_group)
        
        self.open_browser_btn = QPushButton("브라우저 열기")
        self.open_browser_btn.clicked.connect(self.open_browser)
        
        self.close_browser_btn = QPushButton("브라우저 닫기")
        self.close_browser_btn.clicked.connect(self.close_browser)
        self.close_browser_btn.setEnabled(False)
        
        browser_layout.addWidget(self.open_browser_btn, 0, 0)
        browser_layout.addWidget(self.close_browser_btn, 0, 1)
        
        # 레이아웃에 위젯 추가
        login_layout.addWidget(header_label)
        login_layout.addWidget(info_label)
        login_layout.addWidget(auto_login_group)
        login_layout.addWidget(manual_login_group)
        login_layout.addWidget(status_group)
        login_layout.addWidget(browser_group)
        login_layout.addStretch()
    
    def open_browser(self):
        """브라우저 열기"""
        try:
            if self.driver:
                QMessageBox.warning(self, "브라우저 이미 실행 중", "브라우저가 이미 실행 중입니다.")
                return
            
            self.log_text.append("브라우저를 시작합니다...")
            
            # ChromeOptions 설정
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            # WebDriver 설정
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            self.driver.get("https://www.tistory.com")
            
            # UI 업데이트
            self.close_browser_btn.setEnabled(True)
            self.open_browser_btn.setEnabled(False)
            self.status_bar.showMessage("브라우저가 시작되었습니다.")
            self.log_text.append("브라우저가 성공적으로 시작되었습니다.")
            
        except Exception as e:
            self.log_text.append(f"브라우저 시작 중 오류 발생: {str(e)}")
            QMessageBox.critical(self, "오류", f"브라우저 시작 중 오류가 발생했습니다.\n{str(e)}")
    
    def close_browser(self):
        """브라우저 닫기"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                
                # UI 업데이트
                self.close_browser_btn.setEnabled(False)
                self.open_browser_btn.setEnabled(True)
                self.status_bar.showMessage("브라우저가 종료되었습니다.")
                self.log_text.append("브라우저가 종료되었습니다.")
                
            except Exception as e:
                self.log_text.append(f"브라우저 종료 중 오류 발생: {str(e)}")
                QMessageBox.critical(self, "오류", f"브라우저 종료 중 오류가 발생했습니다.\n{str(e)}")
    
    def start_auto_login(self):
        """자동 로그인 시작"""
        if not self.driver:
            QMessageBox.warning(self, "브라우저 필요", "먼저 브라우저를 열어주세요.")
            return
        
        self.log_text.append("\n===== 자동 로그인 시도 =====")
        
        # 스레드에서 자동 로그인 실행
        self.login_thread = WebDriverThread(self.try_auto_login)
        self.login_thread.update_signal.connect(self.log_text.append)
        self.login_thread.status_signal.connect(self.status_bar.showMessage)
        self.login_thread.finished_signal.connect(self.on_login_finished)
        self.login_thread.error_signal.connect(self.on_login_error)
        
        # UI 업데이트
        self.auto_login_btn.setEnabled(False)
        self.manual_login_btn.setEnabled(False)
        self.status_bar.showMessage("자동 로그인 시도 중...")
        
        # 스레드 시작
        self.login_thread.start()
    
    def try_auto_login(self):
        """자동 로그인 로직"""
        try:
            # 모든 쿠키 삭제
            self.driver.delete_all_cookies()
            time.sleep(1)
            
            # 티스토리 메인 페이지 접속
            self.login_thread.update_signal.emit("티스토리 메인 페이지에 접속 중...")
            self.driver.get("https://www.tistory.com")
            time.sleep(3)  # 페이지 로딩 대기
            
            # 저장된 쿠키 로드
            self.login_thread.update_signal.emit("저장된 쿠키 로드 시도 중...")
            cookie_loaded = load_cookies(self.driver)
            
            # 저장된 로컬 스토리지 로드
            self.login_thread.update_signal.emit("저장된 로컬 스토리지 로드 시도 중...")
            storage_loaded = load_local_storage(self.driver)
            
            # 쿠키나 로컬 스토리지 중 하나라도 로드에 실패한 경우
            if not cookie_loaded and not storage_loaded:
                self.login_thread.update_signal.emit("저장된 세션 정보가 없습니다. 자동 로그인이 불가능합니다.")
                return {"success": False, "message": "저장된 세션 정보 없음"}
            
            # 페이지 새로고침하여 로드된 쿠키 적용
            self.login_thread.update_signal.emit("세션 정보 적용을 위해 페이지 새로고침...")
            self.driver.refresh()
            time.sleep(3)
            
            # 로그인 상태 확인
            login_status = is_logged_in(self.driver)
            
            if login_status:
                self.login_thread.update_signal.emit("자동 로그인 성공!")
                return {"success": True, "message": "자동 로그인 성공"}
            else:
                self.login_thread.update_signal.emit("자동 로그인 실패. 수동 로그인을 시도해주세요.")
                return {"success": False, "message": "자동 로그인 실패"}
                
        except Exception as e:
            self.login_thread.update_signal.emit(f"자동 로그인 시도 중 오류 발생: {e}")
            return {"success": False, "message": f"오류: {str(e)}"}
    
    def start_manual_login(self):
        """수동 로그인 시작"""
        if not self.driver:
            QMessageBox.warning(self, "브라우저 필요", "먼저 브라우저를 열어주세요.")
            return
        
        self.log_text.append("\n===== 수동 로그인 시작 =====")
        
        # 스레드에서 수동 로그인 과정 진행
        self.login_thread = WebDriverThread(self.manual_login_process)
        self.login_thread.update_signal.connect(self.log_text.append)
        self.login_thread.status_signal.connect(self.status_bar.showMessage)
        self.login_thread.finished_signal.connect(self.on_login_finished)
        self.login_thread.error_signal.connect(self.on_login_error)
        
        # UI 업데이트
        self.auto_login_btn.setEnabled(False)
        self.manual_login_btn.setEnabled(False)
        self.status_bar.showMessage("수동 로그인 준비 중...")
        
        # 스레드 시작
        self.login_thread.start()
    
    def manual_login_process(self):
        """수동 로그인 로직"""
        try:
            # 기존 세션 정보 삭제
            self.driver.delete_all_cookies()
            
            # 로그인 페이지 접속
            self.login_thread.update_signal.emit("로그인 페이지로 이동합니다...")
            self.driver.get("https://www.tistory.com/auth/login")
            time.sleep(3)
            
            # 사용자에게 로그인 요청
            self.login_thread.update_signal.emit("브라우저에서 로그인을 수동으로 완료해주세요.")
            self.login_thread.update_signal.emit("  * 아이디와 비밀번호를 입력하여 로그인합니다.")
            self.login_thread.update_signal.emit("  * 로그인 완료 후 대시보드나 메인 페이지가 표시되면 성공입니다.")
            
            # 대화상자 표시
            msg = QMessageBox()
            msg.setWindowTitle("수동 로그인")
            msg.setText("브라우저에서 로그인을 수동으로 완료해주세요.\n로그인 완료 후 '확인' 버튼을 클릭하세요.")
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
            # 티스토리 메인 페이지로 이동
            self.login_thread.update_signal.emit("\n티스토리 메인 페이지로 이동합니다...")
            self.driver.get("https://www.tistory.com")
            time.sleep(3)
            
            # 로그인 상태 확인
            login_success = is_logged_in(self.driver)
            
            if login_success:
                self.login_thread.update_signal.emit("로그인 성공 확인! 세션 정보를 저장합니다.")
                
                # 세션 정보 저장
                save_cookies(self.driver)
                save_local_storage(self.driver)
                
                return {"success": True, "message": "수동 로그인 성공"}
            else:
                self.login_thread.update_signal.emit("로그인 상태를 확인할 수 없습니다.")
                
                # 사용자 확인
                confirm_msg = QMessageBox()
                confirm_msg.setWindowTitle("로그인 확인")
                confirm_msg.setText("로그인이 성공적으로 완료되었나요?")
                confirm_msg.setIcon(QMessageBox.Question)
                confirm_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                user_confirm = confirm_msg.exec_() == QMessageBox.Yes
                
                if user_confirm:
                    self.login_thread.update_signal.emit("사용자 확인으로 로그인 성공으로 처리합니다.")
                    
                    # 세션 정보 저장
                    save_cookies(self.driver)
                    save_local_storage(self.driver)
                    
                    return {"success": True, "message": "사용자 확인 로그인 성공"}
                else:
                    self.login_thread.update_signal.emit("로그인이 완료되지 않았습니다. 다시 시도해주세요.")
                    return {"success": False, "message": "로그인 실패"}
                
        except Exception as e:
            self.login_thread.update_signal.emit(f"수동 로그인 처리 중 오류 발생: {e}")
            return {"success": False, "message": f"오류: {str(e)}"}
    
    def on_login_finished(self, success, result):
        """로그인 완료 처리"""
        # UI 업데이트
        self.auto_login_btn.setEnabled(True)
        self.manual_login_btn.setEnabled(True)
        
        if success and result.get("success", False):
            self.login_status_label.setText("로그인 상태: 로그인됨")
            self.login_status_label.setStyleSheet("font-weight: bold; color: #8bc34a;")
            self.status_bar.showMessage(f"로그인 성공: {result.get('message', '')}")
            
            # 콘텐츠 탭으로 이동
            self.tabs.setCurrentIndex(1)
        else:
            self.login_status_label.setText("로그인 상태: 로그인되지 않음")
            self.login_status_label.setStyleSheet("font-weight: bold; color: #f44336;")
            self.status_bar.showMessage(f"로그인 실패: {result.get('message', '')}")
    
    def on_login_error(self, error_msg):
        """로그인 오류 처리"""
        self.auto_login_btn.setEnabled(True)
        self.manual_login_btn.setEnabled(True)
        self.login_status_label.setText("로그인 상태: 오류 발생")
        self.login_status_label.setStyleSheet("font-weight: bold; color: #ff9800;")
        self.status_bar.showMessage(f"로그인 오류: {error_msg}")
        
        QMessageBox.critical(self, "로그인 오류", f"로그인 처리 중 오류가 발생했습니다.\n{error_msg}")
    
    def check_login_status(self):
        """로그인 상태 확인"""
        if not self.driver:
            QMessageBox.warning(self, "브라우저 필요", "먼저 브라우저를 열어주세요.")
            return
        
        try:
            self.log_text.append("로그인 상태를 확인 중...")
            
            login_status = is_logged_in(self.driver)
            
            if login_status:
                self.login_status_label.setText("로그인 상태: 로그인됨")
                self.login_status_label.setStyleSheet("font-weight: bold; color: #8bc34a;")
                self.log_text.append("로그인 상태 확인 완료: 로그인되어 있습니다.")
                self.status_bar.showMessage("로그인 상태: 로그인됨")
            else:
                self.login_status_label.setText("로그인 상태: 로그인되지 않음")
                self.login_status_label.setStyleSheet("font-weight: bold; color: #f44336;")
                self.log_text.append("로그인 상태 확인 완료: 로그인되어 있지 않습니다.")
                self.status_bar.showMessage("로그인 상태: 로그인되지 않음")
                
        except Exception as e:
            self.log_text.append(f"로그인 상태 확인 중 오류 발생: {str(e)}")
            self.login_status_label.setText("로그인 상태: 확인 실패")
            self.login_status_label.setStyleSheet("font-weight: bold; color: #ff9800;")
            self.status_bar.showMessage("로그인 상태 확인 실패")

    def setup_content_tab(self):
        """콘텐츠 생성 탭 설정"""
        self.content_tab = QWidget()
        content_layout = QVBoxLayout(self.content_tab)
        
        # 안내 레이블
        header_label = QLabel("블로그 콘텐츠 생성")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        
        info_label = QLabel("ChatGPT를 이용하여 블로그 콘텐츠를 자동으로 생성합니다.")
        info_label.setWordWrap(True)
        
        # 주제 선택 그룹
        topic_group = QGroupBox("블로그 주제 선택")
        topic_layout = QVBoxLayout(topic_group)
        
        # 주제 선택 라디오 버튼
        self.topic_selection_predefined = QRadioButton("예시 주제 목록에서 선택")
        self.topic_selection_predefined.setChecked(True)
        self.topic_selection_custom = QRadioButton("직접 주제 입력")
        
        self.topic_selection_predefined.toggled.connect(self.toggle_topic_selection)
        
        topic_radio_layout = QHBoxLayout()
        topic_radio_layout.addWidget(self.topic_selection_predefined)
        topic_radio_layout.addWidget(self.topic_selection_custom)
        
        # 예시 주제 목록 콤보박스
        topic_combo_layout = QHBoxLayout()
        topic_combo_label = QLabel("예시 주제:")
        self.topic_combo = QComboBox()
        self.topic_combo.addItems(BLOG_TOPICS)
        topic_combo_layout.addWidget(topic_combo_label)
        topic_combo_layout.addWidget(self.topic_combo)
        
        # 직접 입력 필드
        custom_topic_layout = QHBoxLayout()
        custom_topic_label = QLabel("직접 입력:")
        self.custom_topic_input = QLineEdit()
        self.custom_topic_input.setPlaceholderText("블로그 주제를 직접 입력하세요")
        self.custom_topic_input.setEnabled(False)
        custom_topic_layout.addWidget(custom_topic_label)
        custom_topic_layout.addWidget(self.custom_topic_input)
        
        # 주제 레이아웃에 위젯 추가
        topic_layout.addLayout(topic_radio_layout)
        topic_layout.addLayout(topic_combo_layout)
        topic_layout.addLayout(custom_topic_layout)
        
        # 콘텐츠 형식 그룹
        format_group = QGroupBox("콘텐츠 형식")
        format_layout = QVBoxLayout(format_group)
        
        self.format_html = QRadioButton("HTML 모드 (태그 포함)")
        self.format_text = QRadioButton("일반 텍스트 모드")
        self.format_markdown = QRadioButton("마크다운 모드")
        
        self.format_text.setChecked(True)  # 기본값: 일반 텍스트
        
        format_layout.addWidget(self.format_html)
        format_layout.addWidget(self.format_text)
        format_layout.addWidget(self.format_markdown)
        
        # 생성 버튼
        self.generate_button = QPushButton("콘텐츠 생성")
        self.generate_button.setIcon(QIcon.fromTheme("document-new"))
        self.generate_button.clicked.connect(self.generate_content)
        self.generate_button.setStyleSheet("font-size: 14px; padding: 8px;")
        
        # 생성된 콘텐츠 미리보기 그룹
        preview_group = QGroupBox("생성된 콘텐츠 미리보기")
        preview_layout = QVBoxLayout(preview_group)
        
        # 제목 미리보기
        title_layout = QHBoxLayout()
        title_label = QLabel("제목:")
        title_label.setStyleSheet("font-weight: bold;")
        self.title_preview = QLineEdit()
        self.title_preview.setReadOnly(True)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_preview)
        
        # 태그 미리보기
        tags_layout = QHBoxLayout()
        tags_label = QLabel("태그:")
        tags_label.setStyleSheet("font-weight: bold;")
        self.tags_preview = QLineEdit()
        self.tags_preview.setReadOnly(True)
        tags_layout.addWidget(tags_label)
        tags_layout.addWidget(self.tags_preview)
        
        # 본문 미리보기
        content_preview_label = QLabel("본문:")
        content_preview_label.setStyleSheet("font-weight: bold;")
        self.content_preview = QTextEdit()
        self.content_preview.setReadOnly(True)
        self.content_preview.setMinimumHeight(200)
        
        # 생성 진행 상태 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 불확정 진행 표시
        self.progress_bar.setVisible(False)
        
        # 다음 단계 버튼
        self.next_button = QPushButton("게시물 작성 단계로 이동")
        self.next_button.setIcon(QIcon.fromTheme("go-next"))
        self.next_button.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        self.next_button.setEnabled(False)
        self.next_button.setStyleSheet("font-size: 14px; padding: 8px;")
        
        # 미리보기 레이아웃에 위젯 추가
        preview_layout.addLayout(title_layout)
        preview_layout.addLayout(tags_layout)
        preview_layout.addWidget(content_preview_label)
        preview_layout.addWidget(self.content_preview)
        
        # 콘텐츠 탭 레이아웃에 위젯 추가
        content_layout.addWidget(header_label)
        content_layout.addWidget(info_label)
        content_layout.addWidget(topic_group)
        content_layout.addWidget(format_group)
        content_layout.addWidget(self.generate_button)
        content_layout.addWidget(self.progress_bar)
        content_layout.addWidget(preview_group)
        content_layout.addWidget(self.next_button)
    
    def toggle_topic_selection(self):
        """주제 선택 방식에 따라 UI 업데이트"""
        if self.topic_selection_predefined.isChecked():
            self.topic_combo.setEnabled(True)
            self.custom_topic_input.setEnabled(False)
        else:
            self.topic_combo.setEnabled(False)
            self.custom_topic_input.setEnabled(True)
    
    def generate_content(self):
        """콘텐츠 생성 시작"""
        # 주제 가져오기
        if self.topic_selection_predefined.isChecked():
            topic = self.topic_combo.currentText()
        else:
            topic = self.custom_topic_input.text().strip()
            if not topic:
                QMessageBox.warning(self, "주제 없음", "블로그 주제를 입력해주세요.")
                return
        
        # 형식 선택
        if self.format_html.isChecked():
            format_type = 1  # HTML
        elif self.format_markdown.isChecked():
            format_type = 3  # 마크다운
        else:
            format_type = 2  # 일반 텍스트
        
        # UI 업데이트
        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_bar.showMessage(f"'{topic}' 주제로 콘텐츠 생성 중...")
        self.log_text.append(f"\n===== 콘텐츠 생성 시작 =====")
        self.log_text.append(f"주제: {topic}")
        self.log_text.append(f"형식: {['HTML', '일반 텍스트', '마크다운'][format_type-1]}")
        
        # 스레드에서 콘텐츠 생성 실행
        self.content_thread = ContentGenerationThread(topic, format_type)
        self.content_thread.update_signal.connect(self.log_text.append)
        self.content_thread.finished_signal.connect(self.on_content_generated)
        self.content_thread.error_signal.connect(self.on_content_generation_error)
        
        # 스레드 시작
        self.content_thread.start()
    
    def on_content_generated(self, blog_post):
        """콘텐츠 생성 완료 처리"""
        # 블로그 포스트 저장
        self.blog_post = blog_post
        
        # UI 업데이트
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("콘텐츠 생성 완료!")
        
        # 미리보기 업데이트
        self.title_preview.setText(blog_post.get("title", ""))
        self.tags_preview.setText(blog_post.get("tags", ""))
        self.content_preview.setPlainText(blog_post.get("content", ""))
        
        # 다음 단계 버튼 활성화
        self.next_button.setEnabled(True)
        
        # 결과 로깅
        self.log_text.append(f"제목: {blog_post.get('title', '')}")
        self.log_text.append(f"태그: {blog_post.get('tags', '')}")
        self.log_text.append(f"본문 길이: {len(blog_post.get('content', ''))} 자")
        self.log_text.append("===== 콘텐츠 생성 완료 =====")
        
        # 게시물 작성 탭에 콘텐츠 데이터 전달
        self.update_post_tab_with_content()
        
        # 자동으로 게시물 작성 탭으로 이동할지 물어보기
        reply = QMessageBox.question(
            self, "다음 단계", 
            "콘텐츠 생성이 완료되었습니다. 게시물 작성 탭으로 이동하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.tabs.setCurrentIndex(2)  # 게시물 작성 탭으로 이동
    
    def on_content_generation_error(self, error_msg):
        """콘텐츠 생성 오류 처리"""
        # UI 업데이트
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"콘텐츠 생성 오류: {error_msg}")
        
        # 오류 메시지 표시
        QMessageBox.critical(self, "콘텐츠 생성 오류", f"콘텐츠 생성 중 오류가 발생했습니다.\n{error_msg}")
        
        # 로깅
        self.log_text.append(f"콘텐츠 생성 오류: {error_msg}")
        self.log_text.append("===== 콘텐츠 생성 실패 =====")

    def setup_post_tab(self):
        """게시물 작성 탭 설정"""
        self.post_tab = QWidget()
        post_layout = QVBoxLayout(self.post_tab)
        
        # 안내 레이블
        header_label = QLabel("게시물 작성")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        
        info_label = QLabel("생성된 콘텐츠를 티스토리에 게시합니다.")
        info_label.setWordWrap(True)
        
        # 게시물 정보 그룹
        post_info_group = QGroupBox("게시물 정보")
        post_info_layout = QVBoxLayout(post_info_group)
        
        # 제목 편집
        title_layout = QHBoxLayout()
        title_label = QLabel("제목:")
        title_label.setStyleSheet("font-weight: bold;")
        self.post_title_edit = QLineEdit()
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.post_title_edit)
        
        # 태그 편집
        tags_layout = QHBoxLayout()
        tags_label = QLabel("태그:")
        tags_label.setStyleSheet("font-weight: bold;")
        self.post_tags_edit = QLineEdit()
        self.post_tags_edit.setPlaceholderText("쉼표로 구분하여 입력")
        tags_layout.addWidget(tags_label)
        tags_layout.addWidget(self.post_tags_edit)
        
        # 본문 편집
        content_label = QLabel("본문:")
        content_label.setStyleSheet("font-weight: bold;")
        self.post_content_edit = QTextEdit()
        self.post_content_edit.setMinimumHeight(300)
        
        # 정보 레이아웃에 위젯 추가
        post_info_layout.addLayout(title_layout)
        post_info_layout.addLayout(tags_layout)
        post_info_layout.addWidget(content_label)
        post_info_layout.addWidget(self.post_content_edit)
        
        # 게시 옵션 그룹
        publish_options_group = QGroupBox("게시 옵션")
        publish_options_layout = QVBoxLayout(publish_options_group)
        
        # 임시저장 버튼
        self.save_draft_button = QPushButton("임시저장")
        self.save_draft_button.setIcon(QIcon.fromTheme("document-save"))
        self.save_draft_button.clicked.connect(self.save_draft)
        
        # 발행 버튼
        self.publish_button = QPushButton("발행")
        self.publish_button.setIcon(QIcon.fromTheme("document-send"))
        self.publish_button.clicked.connect(self.publish_post_gui)
        self.publish_button.setStyleSheet("font-size: 14px; padding: 8px;")
        
        # 진행 상태 표시
        self.post_progress_bar = QProgressBar()
        self.post_progress_bar.setRange(0, 0)
        self.post_progress_bar.setVisible(False)
        
        # 게시 옵션 레이아웃에 위젯 추가
        publish_options_layout.addWidget(self.save_draft_button)
        publish_options_layout.addWidget(self.publish_button)
        publish_options_layout.addWidget(self.post_progress_bar)
        
        # 새 글 작성 버튼
        self.new_post_button = QPushButton("새 글 작성")
        self.new_post_button.setIcon(QIcon.fromTheme("document-new"))
        self.new_post_button.clicked.connect(self.new_post)
        
        # 게시물 탭 레이아웃에 위젯 추가
        post_layout.addWidget(header_label)
        post_layout.addWidget(info_label)
        post_layout.addWidget(post_info_group)
        post_layout.addWidget(publish_options_group)
        post_layout.addWidget(self.new_post_button)
    
    def update_post_tab_with_content(self):
        """콘텐츠 생성 결과로 게시물 탭 업데이트"""
        if self.blog_post:
            self.post_title_edit.setText(self.blog_post.get("title", ""))
            self.post_tags_edit.setText(self.blog_post.get("tags", ""))
            self.post_content_edit.setPlainText(self.blog_post.get("content", ""))
            self.log_text.append("게시물 작성 탭에 콘텐츠가 로드되었습니다.")
    
    def save_draft(self):
        """임시저장 실행"""
        if not self.driver:
            QMessageBox.warning(self, "브라우저 필요", "먼저 브라우저를 열어주세요.")
            return
        
        if not self.check_login_before_post():
            return
        
        # 게시물 정보 수집
        title = self.post_title_edit.text().strip()
        tags = self.post_tags_edit.text().strip()
        content = self.post_content_edit.toPlainText().strip()
        
        if not title or not content:
            QMessageBox.warning(self, "내용 부족", "제목과 본문은 필수 입력 사항입니다.")
            return
        
        # 형식 유형 (1=HTML, 2=일반 텍스트, 3=마크다운)
        format_type = 2  # 기본값: 일반 텍스트
        if self.blog_post and 'format_type' in self.blog_post:
            format_type = self.blog_post.get("format_type", 2)
        
        # 현재 게시물 데이터 저장
        self.blog_post = {
            "title": title,
            "content": content,
            "tags": tags,
            "format_type": format_type
        }
        
        # UI 업데이트
        self.post_progress_bar.setVisible(True)
        self.save_draft_button.setEnabled(False)
        self.publish_button.setEnabled(False)
        self.status_bar.showMessage("게시물 임시저장 중...")
        self.log_text.append("\n===== 게시물 임시저장 시작 =====")
        
        # 스레드에서 작업 실행
        self.post_thread = WebDriverThread(
            self.save_draft_process,
            kwargs={"publish": False}
        )
        self.post_thread.update_signal.connect(self.log_text.append)
        self.post_thread.status_signal.connect(self.status_bar.showMessage)
        self.post_thread.finished_signal.connect(self.on_post_operation_finished)
        self.post_thread.error_signal.connect(self.on_post_operation_error)
        
        # 스레드 시작
        self.post_thread.start()
    
    def publish_post_gui(self):
        """게시물 발행 실행"""
        if not self.driver:
            QMessageBox.warning(self, "브라우저 필요", "먼저 브라우저를 열어주세요.")
            return
            
        if not self.check_login_before_post():
            return
        
        # 발행 전 확인
        reply = QMessageBox.question(
            self, "발행 확인", 
            "게시물을 티스토리에 발행하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 게시물 정보 수집
        title = self.post_title_edit.text().strip()
        tags = self.post_tags_edit.text().strip()
        content = self.post_content_edit.toPlainText().strip()
        
        if not title or not content:
            QMessageBox.warning(self, "내용 부족", "제목과 본문은 필수 입력 사항입니다.")
            return
        
        # 형식 유형 (1=HTML, 2=일반 텍스트, 3=마크다운)
        format_type = 2  # 기본값: 일반 텍스트
        if self.blog_post and 'format_type' in self.blog_post:
            format_type = self.blog_post.get("format_type", 2)
        
        # 현재 게시물 데이터 저장
        self.blog_post = {
            "title": title,
            "content": content,
            "tags": tags,
            "format_type": format_type
        }
        
        # UI 업데이트
        self.post_progress_bar.setVisible(True)
        self.save_draft_button.setEnabled(False)
        self.publish_button.setEnabled(False)
        self.status_bar.showMessage("게시물 발행 중...")
        self.log_text.append("\n===== 게시물 발행 시작 =====")
        
        # 스레드에서 작업 실행
        self.post_thread = WebDriverThread(
            self.save_draft_process,
            kwargs={"publish": True}
        )
        self.post_thread.update_signal.connect(self.log_text.append)
        self.post_thread.status_signal.connect(self.status_bar.showMessage)
        self.post_thread.finished_signal.connect(self.on_post_operation_finished)
        self.post_thread.error_signal.connect(self.on_post_operation_error)
        
        # 스레드 시작
        self.post_thread.start()
    
    def save_draft_process(self, publish=False):
        """임시저장 및 발행 처리 로직"""
        try:
            # 게시물 정보
            blog_post = self.blog_post
            
            # 새 글 작성 페이지로 이동
            self.post_thread.update_signal.emit("새 글 작성 페이지로 이동합니다...")
            self.driver.get(BLOG_NEW_POST_URL)
            time.sleep(5)  # 페이지 로딩 대기
            
            # 알림창 처리
            try:
                alert = WebDriverWait(self.driver, 3).until(EC.alert_is_present())
                if alert:
                    alert_text = alert.text
                    self.post_thread.update_signal.emit(f"알림창 감지: {alert_text}")
                    alert.accept()
                    self.post_thread.update_signal.emit("알림창을 자동으로 처리했습니다.")
                    time.sleep(1)
            except:
                pass
            
            # 글 작성 함수 호출
            self.post_thread.update_signal.emit("게시물을 작성합니다...")
            write_post(self.driver, blog_post, blog_post.get("format_type", 2))
            
            # 발행 여부에 따라 처리
            if publish:
                self.post_thread.update_signal.emit("\n발행을 진행합니다...")
                publish_success = publish_post(self.driver)
                
                if publish_success:
                    self.post_thread.update_signal.emit("발행이 완료되었습니다!")
                    return {"success": True, "message": "발행 완료", "published": True}
                else:
                    self.post_thread.update_signal.emit("발행이 완료되지 않았습니다. 글은 임시저장 상태로 남아있습니다.")
                    return {"success": True, "message": "임시저장 완료", "published": False}
            else:
                self.post_thread.update_signal.emit("임시저장이 완료되었습니다.")
                return {"success": True, "message": "임시저장 완료", "published": False}
            
        except Exception as e:
            self.post_thread.update_signal.emit(f"게시물 작성 중 오류 발생: {e}")
            return {"success": False, "message": f"오류: {str(e)}", "published": False}
    
    def on_post_operation_finished(self, success, result):
        """게시물 작업 완료 처리"""
        # UI 업데이트
        self.post_progress_bar.setVisible(False)
        self.save_draft_button.setEnabled(True)
        self.publish_button.setEnabled(True)
        
        if success and result.get("success", False):
            # 성공 메시지
            if result.get("published", False):
                message = "게시물 발행이 완료되었습니다."
                self.status_bar.showMessage(message)
                QMessageBox.information(self, "발행 완료", message)
            else:
                message = "게시물이 임시저장되었습니다."
                self.status_bar.showMessage(message)
                QMessageBox.information(self, "임시저장 완료", message)
        else:
            # 실패 메시지
            message = f"게시물 작업 실패: {result.get('message', '알 수 없는 오류')}"
            self.status_bar.showMessage(message)
            QMessageBox.warning(self, "게시물 작업 실패", message)
    
    def on_post_operation_error(self, error_msg):
        """게시물 작업 오류 처리"""
        # UI 업데이트
        self.post_progress_bar.setVisible(False)
        self.save_draft_button.setEnabled(True)
        self.publish_button.setEnabled(True)
        
        self.status_bar.showMessage(f"게시물 작업 오류: {error_msg}")
        QMessageBox.critical(self, "게시물 작업 오류", f"게시물 작업 중 오류가 발생했습니다.\n{error_msg}")
    
    def new_post(self):
        """새 글 작성 시작"""
        # 진행 중인 작업이 있는지 확인
        if hasattr(self, 'content_thread') and self.content_thread.isRunning():
            QMessageBox.warning(self, "작업 진행 중", "콘텐츠 생성이 진행 중입니다. 완료 후 다시 시도해주세요.")
            return
            
        if hasattr(self, 'post_thread') and self.post_thread.isRunning():
            QMessageBox.warning(self, "작업 진행 중", "게시물 작업이 진행 중입니다. 완료 후 다시 시도해주세요.")
            return
        
        # 변경 사항 저장 확인
        if self.blog_post:
            reply = QMessageBox.question(
                self, "변경 사항 확인", 
                "현재 편집 중인 게시물이 있습니다. 저장하지 않고 새 글을 작성하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        # 입력 필드 초기화
        self.blog_post = None
        self.post_title_edit.clear()
        self.post_tags_edit.clear()
        self.post_content_edit.clear()
        
        # 콘텐츠 탭으로 이동
        self.tabs.setCurrentIndex(1)
        self.log_text.append("\n===== 새 글 작성 시작 =====")
        self.status_bar.showMessage("새 글 작성을 위해 콘텐츠 생성 탭으로 이동했습니다.")
    
    def check_login_before_post(self):
        """게시물 작업 전 로그인 상태 확인"""
        try:
            login_status = is_logged_in(self.driver)
            
            if not login_status:
                QMessageBox.warning(self, "로그인 필요", "티스토리에 로그인되어 있지 않습니다. 로그인 탭에서 로그인을 진행해주세요.")
                self.tabs.setCurrentIndex(0)  # 로그인 탭으로 이동
                return False
                
            return True
            
        except Exception as e:
            self.log_text.append(f"로그인 상태 확인 중 오류 발생: {str(e)}")
            QMessageBox.critical(self, "오류", f"로그인 상태 확인 중 오류가 발생했습니다.\n{str(e)}")
            return False

    def setup_settings_tab(self):
        """설정 탭 설정"""
        self.settings_tab = QWidget()
        settings_layout = QVBoxLayout(self.settings_tab)
        
        # 안내 레이블
        header_label = QLabel("설정")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        
        info_label = QLabel("프로그램 설정을 관리합니다.")
        info_label.setWordWrap(True)
        
        # API 설정 그룹
        api_group = QGroupBox("OpenAI API 설정")
        api_layout = QFormLayout(api_group)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setText(os.getenv("OPENAI_API_KEY", ""))
        
        api_layout.addRow("API 키:", self.api_key_input)
        
        api_save_button = QPushButton("API 키 저장")
        api_save_button.clicked.connect(self.save_api_key)
        api_layout.addRow("", api_save_button)
        
        # 블로그 설정 그룹
        blog_group = QGroupBox("블로그 설정")
        blog_layout = QFormLayout(blog_group)
        
        self.blog_url_input = QLineEdit()
        self.blog_url_input.setText(BLOG_URL)
        blog_layout.addRow("블로그 URL:", self.blog_url_input)
        
        # 주제 관리 그룹
        topics_group = QGroupBox("블로그 주제 관리")
        topics_layout = QVBoxLayout(topics_group)
        
        self.topics_list = QListWidget()
        self.topics_list.addItems(BLOG_TOPICS)
        
        topics_buttons_layout = QHBoxLayout()
        
        add_topic_button = QPushButton("추가")
        add_topic_button.clicked.connect(self.add_topic)
        
        remove_topic_button = QPushButton("제거")
        remove_topic_button.clicked.connect(self.remove_topic)
        
        topics_buttons_layout.addWidget(add_topic_button)
        topics_buttons_layout.addWidget(remove_topic_button)
        
        topics_layout.addWidget(self.topics_list)
        topics_layout.addLayout(topics_buttons_layout)
        
        # 테마 설정 그룹
        theme_group = QGroupBox("테마 설정")
        theme_layout = QVBoxLayout(theme_group)
        
        self.dark_theme_check = QCheckBox("다크 테마 사용")
        self.dark_theme_check.setChecked(True)
        self.dark_theme_check.toggled.connect(self.toggle_theme)
        
        theme_layout.addWidget(self.dark_theme_check)
        
        # 세션 관리 그룹
        session_group = QGroupBox("세션 관리")
        session_layout = QVBoxLayout(session_group)
        
        clear_cookies_button = QPushButton("저장된 쿠키 삭제")
        clear_cookies_button.clicked.connect(self.clear_cookies)
        
        session_layout.addWidget(clear_cookies_button)
        
        # 설정 저장 버튼
        save_settings_button = QPushButton("모든 설정 저장")
        save_settings_button.clicked.connect(self.save_settings)
        save_settings_button.setStyleSheet("font-size: 14px; padding: 8px;")
        
        # 설정 탭 레이아웃에 위젯 추가
        settings_layout.addWidget(header_label)
        settings_layout.addWidget(info_label)
        settings_layout.addWidget(api_group)
        settings_layout.addWidget(blog_group)
        settings_layout.addWidget(topics_group)
        settings_layout.addWidget(theme_group)
        settings_layout.addWidget(session_group)
        settings_layout.addWidget(save_settings_button)
        settings_layout.addStretch()
    
    def save_api_key(self):
        """API 키 저장"""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "API 키 없음", "API 키를 입력해주세요.")
            return
        
        try:
            # .env 파일에 API 키 저장
            env_path = Path(".env")
            
            if env_path.exists():
                # 기존 파일 내용 읽기
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                # API 키 업데이트
                api_key_line_found = False
                new_lines = []
                
                for line in lines:
                    if line.startswith("OPENAI_API_KEY="):
                        new_lines.append(f"OPENAI_API_KEY={api_key}\n")
                        api_key_line_found = True
                    else:
                        new_lines.append(line)
                
                if not api_key_line_found:
                    new_lines.append(f"OPENAI_API_KEY={api_key}\n")
                
                # 파일 다시 쓰기
                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            else:
                # 새 파일 생성
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(f"OPENAI_API_KEY={api_key}\n")
            
            # 환경 변수 업데이트
            os.environ["OPENAI_API_KEY"] = api_key
            openai.api_key = api_key
            
            QMessageBox.information(self, "API 키 저장", "API 키가 성공적으로 저장되었습니다.")
            self.log_text.append("OpenAI API 키가 업데이트되었습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"API 키 저장 중 오류가 발생했습니다.\n{str(e)}")
            self.log_text.append(f"API 키 저장 중 오류 발생: {str(e)}")
    
    def add_topic(self):
        """블로그 주제 추가"""
        topic, ok = QInputDialog.getText(self, "주제 추가", "새 블로그 주제:")
        
        if ok and topic.strip():
            # 중복 검사
            existing_topics = [self.topics_list.item(i).text() for i in range(self.topics_list.count())]
            
            if topic.strip() in existing_topics:
                QMessageBox.warning(self, "중복 주제", "이미 존재하는 주제입니다.")
                return
            
            # 주제 추가
            self.topics_list.addItem(topic.strip())
            self.log_text.append(f"새 주제 추가됨: {topic.strip()}")
            
            # 콤보박스 업데이트
            self.topic_combo.clear()
            for i in range(self.topics_list.count()):
                self.topic_combo.addItem(self.topics_list.item(i).text())
    
    def remove_topic(self):
        """선택된 블로그 주제 제거"""
        selected_items = self.topics_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "선택 없음", "제거할 주제를 선택해주세요.")
            return
        
        for item in selected_items:
            row = self.topics_list.row(item)
            topic = item.text()
            self.topics_list.takeItem(row)
            self.log_text.append(f"주제 제거됨: {topic}")
        
        # 콤보박스 업데이트
        self.topic_combo.clear()
        for i in range(self.topics_list.count()):
            self.topic_combo.addItem(self.topics_list.item(i).text())
    
    def toggle_theme(self, checked):
        """테마 전환"""
        if checked:
            # 다크 테마 적용
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        else:
            # 기본 테마로 복원
            self.setStyleSheet("")
    
    def clear_cookies(self):
        """저장된 쿠키 삭제"""
        reply = QMessageBox.question(
            self, "쿠키 삭제 확인", 
            "저장된 모든 쿠키를 삭제하시겠습니까?\n이 작업은 자동 로그인 정보를 제거합니다.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # 쿠키 파일 삭제
            if os.path.exists(COOKIES_FILE):
                os.remove(COOKIES_FILE)
                self.log_text.append(f"쿠키 파일 '{COOKIES_FILE}'이 삭제되었습니다.")
            
            # 로컬 스토리지 파일 삭제
            if os.path.exists(LOCAL_STORAGE_FILE):
                os.remove(LOCAL_STORAGE_FILE)
                self.log_text.append(f"로컬 스토리지 파일 '{LOCAL_STORAGE_FILE}'이 삭제되었습니다.")
            
            QMessageBox.information(self, "쿠키 삭제 완료", "저장된 쿠키와 로컬 스토리지가 삭제되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "삭제 오류", f"쿠키 삭제 중 오류가 발생했습니다.\n{str(e)}")
            self.log_text.append(f"쿠키 삭제 중 오류 발생: {str(e)}")
    
    def save_settings(self):
        """모든 설정 저장"""
        try:
            # 블로그 URL 저장
            blog_url = self.blog_url_input.text().strip()
            if blog_url:
                # TODO: 전역 변수 업데이트 대신 설정 파일에 저장하도록 개선
                global BLOG_URL, BLOG_MANAGE_URL, BLOG_NEW_POST_URL
                BLOG_URL = blog_url
                BLOG_MANAGE_URL = f"{blog_url}/manage/post"
                BLOG_NEW_POST_URL = f"{blog_url}/manage/newpost"
            
            # 주제 목록 저장
            topics = [self.topics_list.item(i).text() for i in range(self.topics_list.count())]
            if topics:
                # TODO: 전역 변수 업데이트 대신 설정 파일에 저장하도록 개선
                global BLOG_TOPICS
                BLOG_TOPICS = topics
            
            # 테마 설정 저장
            self.settings.setValue("darkTheme", self.dark_theme_check.isChecked())
            
            # API 키 저장
            self.save_api_key()
            
            QMessageBox.information(self, "설정 저장", "모든 설정이 성공적으로 저장되었습니다.")
            self.log_text.append("프로그램 설정이 저장되었습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "설정 저장 오류", f"설정 저장 중 오류가 발생했습니다.\n{str(e)}")
            self.log_text.append(f"설정 저장 중 오류 발생: {str(e)}")
    
    def load_settings(self):
        """저장된 설정 로드"""
        try:
            # 테마 설정 로드
            dark_theme = self.settings.value("darkTheme", True, type=bool)
            self.dark_theme_check.setChecked(dark_theme)
            
            # 기타 설정 로드 (향후 확장)
            
        except Exception as e:
            self.log_text.append(f"설정 로드 중 오류 발생: {str(e)}")
    
    def closeEvent(self, event):
        """프로그램 종료 시 처리"""
        if self.driver:
            try:
                self.driver.quit()
                self.log_text.append("브라우저가 종료되었습니다.")
            except:
                pass
        
        # 설정 저장 확인
        reply = QMessageBox.question(
            self, "종료 확인", 
            "프로그램을 종료하기 전에 설정을 저장하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Cancel:
            event.ignore()
        elif reply == QMessageBox.Yes:
            self.save_settings()
            event.accept()
        else:
            event.accept()


# 메인 실행 코드
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TistoryBloggerApp()
    sys.exit(app.exec_()) 