import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QFileDialog, QHBoxLayout
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import threading

class WordPressLoginApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('워드프레스 자동 로그인')
        self.setGeometry(100, 100, 350, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.domain_label = QLabel('워드프레스 도메인 (예: example.com)')
        self.domain_input = QLineEdit()
        layout.addWidget(self.domain_label)
        layout.addWidget(self.domain_input)

        self.id_label = QLabel('아이디')
        self.id_input = QLineEdit()
        layout.addWidget(self.id_label)
        layout.addWidget(self.id_input)

        self.pw_label = QLabel('패스워드')
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pw_label)
        layout.addWidget(self.pw_input)

        # 폴더 선택
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel('메모장 폴더 경로')
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText('폴더 경로를 선택하세요')
        self.folder_btn = QPushButton('폴더 선택')
        self.folder_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.folder_btn)
        layout.addLayout(folder_layout)

        self.login_btn = QPushButton('블로그 글 자동 등록 시작')
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '메모장 폴더 선택')
        if folder:
            self.folder_input.setText(folder)

    def handle_login(self):
        domain = self.domain_input.text().strip()
        user_id = self.id_input.text().strip()
        user_pw = self.pw_input.text().strip()
        folder_path = self.folder_input.text().strip()
        if not domain or not user_id or not user_pw or not folder_path:
            QMessageBox.warning(self, '입력 오류', '모든 정보를 입력해주세요.')
            return
        threading.Thread(target=self.login_wordpress, args=(domain, user_id, user_pw, folder_path), daemon=True).start()

    def login_wordpress(self, domain, user_id, user_pw, folder_path):
        import os
        import time
        from selenium.webdriver.common.action_chains import ActionChains
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option('detach', True)
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            url = f"https://{domain}/wp-admin"
            driver.get(url)
            driver.find_element(By.ID, 'user_login').send_keys(user_id)
            driver.find_element(By.ID, 'user_pass').send_keys(user_pw)
            driver.find_element(By.ID, 'wp-submit').click()

            # 게시글 메뉴 클릭
            driver.implicitly_wait(5)
            try:
                posts_menu = driver.find_element(By.ID, 'menu-posts')
                posts_link = posts_menu.find_element(By.TAG_NAME, 'a')
                posts_link.click()
            except Exception as e:
                print(f"게시글 메뉴 클릭 오류: {e}")

            txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
            if not txt_files:
                print('선택한 폴더에 txt 파일이 없습니다.')
                return

            for txt_file in sorted(txt_files):
                # 새 글 추가 버튼 클릭
                driver.implicitly_wait(5)
                try:
                    add_post_btn = driver.find_element(By.CLASS_NAME, 'page-title-action')
                    add_post_btn.click()
                except Exception as e:
                    print(f"새 글 추가 버튼 클릭 오류: {e}")
                    continue

                with open(os.path.join(folder_path, txt_file), 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                # 첫 줄: 제목, 두 번째 줄 건너뛰고, 세 번째 줄부터 본문
                title = lines[0].strip() if lines else ''
                content = ''.join(lines[2:]).strip() if len(lines) > 2 else ''

                # 제목 입력
                time.sleep(2)
                try:
                    title_input = driver.find_element(By.CLASS_NAME, 'editor-post-title__input')
                    title_input.clear()
                    title_input.send_keys(title)
                except Exception as e:
                    print(f"제목 입력 오류: {e}")

                # 본문 입력
                time.sleep(1)
                try:
                    # block-editor-default-block-appender__content 클릭
                    try:
                        appender = driver.find_element(By.CLASS_NAME, 'block-editor-default-block-appender__content')
                        actions = ActionChains(driver)
                        actions.move_to_element(appender).click().perform()
                        time.sleep(0.5)
                    except Exception as e_app:
                        print(f"블록 어펜더 클릭 오류: {e_app}")

                    para = driver.find_element(By.CSS_SELECTOR, '.block-editor-rich-text__editable.wp-block-paragraph.rich-text')
                    actions = ActionChains(driver)
                    actions.move_to_element(para).click().perform()
                    time.sleep(0.5)
                    try:
                        para.send_keys(content)
                    except Exception as e1:
                        driver.execute_script("arguments[0].innerText = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", para, content)
                except Exception as e:
                    print(f"본문 입력 오류: {e}")

                # 저장 버튼 클릭 (class='components-button editor-post-save-draft is-compact is-tertiary')
                time.sleep(1)
                try:
                    save_btn = driver.find_element(By.CSS_SELECTOR, '.components-button.editor-post-save-draft.is-compact.is-tertiary')
                    actions = ActionChains(driver)
                    actions.move_to_element(save_btn).click().perform()
                    time.sleep(2)
                except Exception as e:
                    print(f"저장 버튼 클릭 오류: {e}")

                # 뒤로 가기 (브라우저 back)
                driver.back()
                time.sleep(2)

            print('모든 글 작성 완료')
        except Exception as e:
            QMessageBox.critical(self, '로그인 실패', f'오류 발생: {e}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WordPressLoginApp()
    window.show()
    sys.exit(app.exec_())
