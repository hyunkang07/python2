import tkinter as tk
from tkinter import messagebox
from gemini_auth_gui import GeminiAuthGUI
from wordpress_login_gui import WordPressLoginGUI
from wordpress_category_gui import WordPressCategoryGUI

class MainIntegrationGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Gemini & WordPress 통합 관리')
        self.geometry('500x250')

        tk.Label(self, text='통합 관리 메뉴').pack(pady=10)
        self.gemini_btn = tk.Button(self, text='Gemini API 인증', command=self.open_gemini)
        self.gemini_btn.pack(pady=5)
        self.wp_login_btn = tk.Button(self, text='워드프레스 로그인', command=self.open_wp_login)
        self.wp_login_btn.pack(pady=5)
        self.wp_cat_btn = tk.Button(self, text='워드프레스 카테고리 조회', command=self.open_wp_category)
        self.wp_cat_btn.pack(pady=5)

    def open_gemini(self):
        win = GeminiAuthGUI()
        win.mainloop()

    def open_wp_login(self):
        win = WordPressLoginGUI()
        win.mainloop()

    def open_wp_category(self):
        win = WordPressCategoryGUI()
        win.mainloop()

if __name__ == '__main__':
    app = MainIntegrationGUI()
    app.mainloop()
