import tkinter as tk
from tkinter import scrolledtext
import requests

class WordPressCategoryGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('워드프레스 카테고리 조회')
        self.geometry('400x350')

        tk.Label(self, text='도메인 주소 (예: https://example.com)').pack()
        self.domain_entry = tk.Entry(self, width=50)
        self.domain_entry.pack()
        tk.Label(self, text='워드프레스 사용자 이름').pack()
        self.user_entry = tk.Entry(self, width=50)
        self.user_entry.pack()
        tk.Label(self, text='워드프레스 비밀번호').pack()
        self.pw_entry = tk.Entry(self, show='*', width=50)
        self.pw_entry.pack()
        self.cat_btn = tk.Button(self, text='카테고리 조회', command=self.fetch_categories)
        self.cat_btn.pack(pady=7)
        self.result_text = scrolledtext.ScrolledText(self, width=50, height=10)
        self.result_text.pack()
        self.category_var = tk.StringVar(self)
        self.category_menu = None

    def fetch_categories(self):
        domain = self.domain_entry.get().strip().rstrip('/')
        username = self.user_entry.get().strip()
        password = self.pw_entry.get().strip()
        categories_url = f"{domain}/wp-json/wp/v2/categories"
        self.result_text.delete('1.0', tk.END)
        if not domain or not username or not password:
            self.result_text.insert(tk.END, '도메인, 아이디, 비밀번호를 모두 입력하세요.\n')
            return
        try:
            response = requests.get(categories_url, auth=(username, password))
            if response.status_code == 200:
                categories = response.json()
                self.result_text.insert(tk.END, '\n--- 카테고리 목록 ---\n')
                cat_names = [f"{cat['name']} (ID:{cat['id']})" for cat in categories]
                if self.category_menu:
                    self.category_menu.destroy()
                if cat_names:
                    self.category_var.set(cat_names[0])
                    self.category_menu = tk.OptionMenu(self, self.category_var, *cat_names)
                    self.category_menu.pack()
                for cat in categories:
                    self.result_text.insert(tk.END, f"ID: {cat['id']} | 이름: {cat['name']}\n")
            elif response.status_code == 401:
                self.result_text.insert(tk.END, '❌ 인증 실패: 사용자 이름 또는 비밀번호가 올바르지 않습니다.\n')
            else:
                self.result_text.insert(tk.END, f"⚠️ 오류 발생: {response.status_code}\n{response.text}\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"🌐 네트워크 또는 요청 오류 발생: {e}\n")

if __name__ == '__main__':
    app = WordPressCategoryGUI()
    app.mainloop()
