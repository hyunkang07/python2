import tkinter as tk
from tkinter import scrolledtext
import requests

class WordPressAuthGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('WordPress & Gemini 인증')
        self.geometry('500x500')

        # Gemini API Key
        tk.Label(self, text='Gemini API Key').pack()
        self.gemini_entry = tk.Entry(self, width=50)
        self.gemini_entry.pack()
        tk.Label(self, text='Gemini 모델명').pack()
        self.gemini_model_entry = tk.Entry(self, width=50)
        self.gemini_model_entry.insert(0, 'gemini-2.5-flash')
        self.gemini_model_entry.pack()
        tk.Button(self, text='Gemini API 키 인증', command=self.check_gemini_api).pack(pady=7)

        # 워드프레스 정보
        tk.Label(self, text='도메인 주소 (예: https://example.com)').pack()
        self.domain_entry = tk.Entry(self, width=50)
        self.domain_entry.pack()
        tk.Label(self, text='워드프레스 사용자 이름').pack()
        self.user_entry = tk.Entry(self, width=50)
        self.user_entry.pack()
        tk.Label(self, text='워드프레스 비밀번호').pack()
        self.pw_entry = tk.Entry(self, show='*', width=50)
        self.pw_entry.pack()
        tk.Button(self, text='워드프레스 인증 및 게시물 조회', command=self.fetch_authenticated_data).pack(pady=10)

        self.result_text = scrolledtext.ScrolledText(self, width=60, height=15)
        self.result_text.pack()

    def check_gemini_api(self):
        api_key = self.gemini_entry.get().strip()
        model_name = self.gemini_model_entry.get().strip()
        self.result_text.delete('1.0', tk.END)
        if not api_key or not model_name:
            self.result_text.insert(tk.END, 'Gemini API 키와 모델명을 입력하세요.\n')
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Explain how AI works in a few words")
            self.result_text.insert(tk.END, f"✅ Gemini API 인증 성공!\n응답: {getattr(response, 'text', str(response))}\n")
        except ImportError:
            self.result_text.insert(tk.END, "❌ google-generativeai 라이브러리가 없습니다.\npip install google-generativeai\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"❌ Gemini API 인증 실패: {e}\n")

    def fetch_authenticated_data(self):
        domain = self.domain_entry.get().strip().rstrip('/')
        username = self.user_entry.get().strip()
        password = self.pw_entry.get().strip()
        api_url = f"{domain}/wp-json/wp/v2/posts"
        self.result_text.delete('1.0', tk.END)
        try:
            response = requests.get(api_url, auth=(username, password))
            if response.status_code == 200:
                self.result_text.insert(tk.END, '✅ 워드프레스 인증 성공!\n')
                post_data = response.json()
                self.result_text.insert(tk.END, '--- 게시물 목록 (일부) ---\n')
                for post in post_data[:2]:
                    self.result_text.insert(tk.END, f"제목: {post['title']['rendered']}\nID: {post['id']}\n\n")
            elif response.status_code == 401:
                self.result_text.insert(tk.END, '❌ 인증 실패: 사용자 이름 또는 비밀번호가 올바르지 않습니다.\n')
            else:
                self.result_text.insert(tk.END, f"⚠️ 오류 발생: {response.status_code}\n{response.text}\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"🌐 네트워크 또는 요청 오류 발생: {e}\n")

if __name__ == '__main__':
    app = WordPressAuthGUI()
    app.mainloop()
