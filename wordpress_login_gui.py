import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
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

        self.domain_label = QLabel('도메인 (예: example.com)')
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

        self.login_btn = QPushButton('로그인')
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def handle_login(self):
        domain = self.domain_input.text().strip()
        user_id = self.id_input.text().strip()
        user_pw = self.pw_input.text().strip()
        if not domain or not user_id or not user_pw:
            QMessageBox.warning(self, '입력 오류', '모든 정보를 입력해주세요.')
            return
        threading.Thread(target=self.login_wordpress, args=(domain, user_id, user_pw), daemon=True).start()

    def login_wordpress(self, domain, user_id, user_pw):
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

            # 로그인 후 게시글 메뉴 클릭 (id='menu-posts' 내부의 첫 번째 a 태그)
            driver.implicitly_wait(5)
            try:
                posts_menu = driver.find_element(By.ID, 'menu-posts')
                posts_link = posts_menu.find_element(By.TAG_NAME, 'a')
                posts_link.click()
            except Exception as e:
                print(f"게시글 메뉴 클릭 오류: {e}")

            # '새 글 추가' 버튼 클릭 (class='page-title-action')
            driver.implicitly_wait(5)
            try:
                add_post_btn = driver.find_element(By.CLASS_NAME, 'page-title-action')
                add_post_btn.click()
            except Exception as e:
                print(f"새 글 추가 버튼 클릭 오류: {e}")
        except Exception as e:
            QMessageBox.critical(self, '로그인 실패', f'오류 발생: {e}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WordPressLoginApp()
    window.show()
    sys.exit(app.exec_())
