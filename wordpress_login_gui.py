import tkinter as tk
from tkinter import scrolledtext
import requests

class WordPressLoginGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('워드프레스 로그인')
        self.geometry('400x300')

        tk.Label(self, text='도메인 주소 (예: https://example.com)').pack()
        self.domain_entry = tk.Entry(self, width=50)
        self.domain_entry.pack()
        tk.Label(self, text='워드프레스 사용자 이름').pack()
        self.user_entry = tk.Entry(self, width=50)
        self.user_entry.pack()
        tk.Label(self, text='워드프레스 비밀번호').pack()
        self.pw_entry = tk.Entry(self, show='*', width=50)
        self.pw_entry.pack()
        self.login_btn = tk.Button(self, text='로그인 및 인증', command=self.check_wp_login)
        self.login_btn.pack(pady=7)
        self.result_text = scrolledtext.ScrolledText(self, width=50, height=7)
        self.result_text.pack()

    def check_wp_login(self):
        domain = self.domain_entry.get().strip().rstrip('/')
        username = self.user_entry.get().strip()
        password = self.pw_entry.get().strip()
        api_url = f"{domain}/wp-json/wp/v2/posts"
        self.result_text.delete('1.0', tk.END)
        if not domain or not username or not password:
            self.result_text.insert(tk.END, '도메인, 아이디, 비밀번호를 모두 입력하세요.\n')
            return
        try:
            response = requests.get(api_url, auth=(username, password))
            if response.status_code == 200:
                self.result_text.insert(tk.END, f'✅ 워드프레스 인증 성공! ({domain} | {username})\n')
            elif response.status_code == 401:
                self.result_text.insert(tk.END, '❌ 인증 실패: 사용자 이름 또는 비밀번호가 올바르지 않습니다.\n')
            else:
                self.result_text.insert(tk.END, f"⚠️ 오류 발생: {response.status_code}\n{response.text}\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"🌐 네트워크 또는 요청 오류 발생: {e}\n")

if __name__ == '__main__':
    app = WordPressLoginGUI()
    app.mainloop()
