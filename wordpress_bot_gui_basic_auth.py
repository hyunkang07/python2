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
        self.gemini_btn = tk.Button(self, text='Gemini API 키 인증', command=self.check_gemini_api)
        self.gemini_btn.pack(pady=7)

        # 워드프레스 계정 관리
        tk.Label(self, text='도메인 주소 (예: https://example.com)').pack()
        self.domain_entry = tk.Entry(self, width=50)
        self.domain_entry.pack()
        tk.Label(self, text='워드프레스 사용자 이름').pack()
        self.user_entry = tk.Entry(self, width=50)
        self.user_entry.pack()
        tk.Label(self, text='워드프레스 비밀번호').pack()
        self.pw_entry = tk.Entry(self, show='*', width=50)
        self.pw_entry.pack()
        self.add_wp_btn = tk.Button(self, text='워드프레스 계정 추가', command=self.add_wp_account)
        self.add_wp_btn.pack(pady=5)

        tk.Label(self, text='추가된 워드프레스 계정 목록').pack()
        self.wp_listbox = tk.Listbox(self, width=60, height=5)
        self.wp_listbox.pack()
        self.check_wp_btn = tk.Button(self, text='선택 계정 인증 및 게시물 조회', command=self.fetch_selected_wp_data)
        self.check_wp_btn.pack(pady=5)

    self.result_text = scrolledtext.ScrolledText(self, width=60, height=15)
    self.result_text.pack()

    # 카테고리 선택 옵션
    self.category_var = tk.StringVar(self)
    self.category_menu = None

    # 글 작성 영역
    tk.Label(self, text='글 제목').pack()
    self.post_title_entry = tk.Entry(self, width=50)
    self.post_title_entry.pack()
    tk.Label(self, text='글 내용').pack()
    self.post_content_entry = tk.Entry(self, width=50)
    self.post_content_entry.pack()
    self.post_btn = tk.Button(self, text='선택 카테고리에 글 작성', command=self.create_post_to_category)
    self.post_btn.pack(pady=5)

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
            # 인증 성공 시 입력란과 버튼 비활성화
            self.gemini_entry.config(state='disabled')
            self.gemini_model_entry.config(state='disabled')
            self.gemini_btn.config(state='disabled')
        except ImportError:
            self.result_text.insert(tk.END, "❌ google-generativeai 라이브러리가 없습니다.\npip install google-generativeai\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"❌ Gemini API 인증 실패: {e}\n")
    def add_wp_account(self):
        domain = self.domain_entry.get().strip().rstrip('/')
        username = self.user_entry.get().strip()
        password = self.pw_entry.get().strip()
        if not domain or not username or not password:
            self.result_text.insert(tk.END, '도메인, 아이디, 비밀번호를 모두 입력하세요.\n')
            return
        # 계정 정보를 리스트박스에 추가
        display = f"{domain} | {username}"
        self.wp_listbox.insert(tk.END, display)
        # 계정 정보를 객체에 저장
        if not hasattr(self, 'wp_accounts'):
            self.wp_accounts = []
        self.wp_accounts.append({'domain': domain, 'username': username, 'password': password})
        # 입력란 초기화
        self.domain_entry.delete(0, tk.END)
        self.user_entry.delete(0, tk.END)
        self.pw_entry.delete(0, tk.END)
        self.result_text.insert(tk.END, f"워드프레스 계정이 추가되었습니다: {display}\n")

    def fetch_selected_wp_data(self):
        selection = self.wp_listbox.curselection()
        if not selection:
            self.result_text.insert(tk.END, '계정을 선택하세요.\n')
            return
        idx = selection[0]
        account = self.wp_accounts[idx]
        domain = account['domain']
        username = account['username']
        password = account['password']
        api_url = f"{domain}/wp-json/wp/v2/posts"
        categories_url = f"{domain}/wp-json/wp/v2/categories"
        self.result_text.delete('1.0', tk.END)
        try:
            response = requests.get(api_url, auth=(username, password))
            if response.status_code == 200:
                self.result_text.insert(tk.END, f'✅ 워드프레스 인증 성공! ({domain} | {username})\n')
                post_data = response.json()
                self.result_text.insert(tk.END, '--- 게시물 목록 (일부) ---\n')
                for post in post_data[:2]:
                    self.result_text.insert(tk.END, f"제목: {post['title']['rendered']}\nID: {post['id']}\n\n")
                # 카테고리 조회
                cat_response = requests.get(categories_url, auth=(username, password))
                if cat_response.status_code == 200:
                    categories = cat_response.json()
                    self.result_text.insert(tk.END, '\n--- 카테고리 목록 ---\n')
                    self.categories = categories
                    cat_names = [f"{cat['name']} (ID:{cat['id']})" for cat in categories]
                    if self.category_menu:
                        self.category_menu.destroy()
                    if cat_names:
                        self.category_var.set(cat_names[0])
                        self.category_menu = tk.OptionMenu(self, self.category_var, *cat_names)
                        self.category_menu.pack()
                    for cat in categories:
                        self.result_text.insert(tk.END, f"ID: {cat['id']} | 이름: {cat['name']}\n")
                else:
                    self.result_text.insert(tk.END, f"카테고리 조회 실패: {cat_response.status_code}\n{cat_response.text}\n")
            elif response.status_code == 401:
                self.result_text.insert(tk.END, '❌ 인증 실패: 사용자 이름 또는 비밀번호가 올바르지 않습니다.\n')
            else:
                self.result_text.insert(tk.END, f"⚠️ 오류 발생: {response.status_code}\n{response.text}\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"🌐 네트워크 또는 요청 오류 발생: {e}\n")
    def create_post_to_category(self):
        selection = self.wp_listbox.curselection()
        if not selection:
            self.result_text.insert(tk.END, '계정을 선택하세요.\n')
            return
        idx = selection[0]
        account = self.wp_accounts[idx]
        domain = account['domain']
        username = account['username']
        password = account['password']
        # 카테고리 ID 추출
        if not hasattr(self, 'categories') or not self.categories:
            self.result_text.insert(tk.END, '카테고리 정보를 먼저 조회하세요.\n')
            return
        selected_name = self.category_var.get()
        selected_cat = next((cat for cat in self.categories if f"{cat['name']} (ID:{cat['id']})" == selected_name), None)
        if not selected_cat:
            self.result_text.insert(tk.END, '카테고리를 선택하세요.\n')
            return
        cat_id = selected_cat['id']
        title = self.post_title_entry.get().strip()
        content = self.post_content_entry.get().strip()
        if not title or not content:
            self.result_text.insert(tk.END, '글 제목과 내용을 입력하세요.\n')
            return
        post_url = f"{domain}/wp-json/wp/v2/posts"
        post_data = {
            "title": title,
            "content": content,
            "categories": [cat_id],
            "status": "publish"
        }
        try:
            response = requests.post(post_url, auth=(username, password), json=post_data)
            if response.status_code == 201:
                self.result_text.insert(tk.END, f"✅ 글이 성공적으로 등록되었습니다! (ID: {response.json().get('id')})\n")
            elif response.status_code == 401:
                self.result_text.insert(tk.END, '❌ 인증 실패: 사용자 이름 또는 비밀번호가 올바르지 않습니다.\n')
            else:
                self.result_text.insert(tk.END, f"⚠️ 오류 발생: {response.status_code}\n{response.text}\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"🌐 네트워크 또는 요청 오류 발생: {e}\n")

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
