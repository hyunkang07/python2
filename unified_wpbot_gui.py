import tkinter as tk
from tkinter import scrolledtext
import requests
from requests.auth import HTTPBasicAuth
try:
    import google.generativeai as genai
except ImportError:
    genai = None

class UnifiedWPBotGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Gemini & WordPress 통합 관리')
        self.geometry('600x700')

        # Gemini API 인증 영역
        frame_gemini = tk.LabelFrame(self, text='Gemini API 인증', padx=10, pady=10)
        frame_gemini.pack(fill='x', padx=10, pady=5)
        tk.Label(frame_gemini, text='API Key').grid(row=0, column=0, sticky='e')
        self.gemini_entry = tk.Entry(frame_gemini, width=40)
        self.gemini_entry.grid(row=0, column=1)
        tk.Label(frame_gemini, text='모델명').grid(row=1, column=0, sticky='e')
        self.gemini_model_entry = tk.Entry(frame_gemini, width=40)
        self.gemini_model_entry.insert(0, 'gemini-2.5-flash')
        self.gemini_model_entry.grid(row=1, column=1)
        self.gemini_btn = tk.Button(frame_gemini, text='Gemini 인증', command=self.check_gemini_api)
        self.gemini_btn.grid(row=2, column=0, columnspan=2, pady=5)
        self.gemini_result = tk.Label(frame_gemini, text='', fg='blue')
        self.gemini_result.grid(row=3, column=0, columnspan=2)

        # 워드프레스 로그인 및 계정 추가 영역
        frame_wp = tk.LabelFrame(self, text='워드프레스 계정 관리', padx=10, pady=10)
        frame_wp.pack(fill='x', padx=10, pady=5)
        tk.Label(frame_wp, text='도메인').grid(row=0, column=0, sticky='e')
        self.domain_entry = tk.Entry(frame_wp, width=40)
        self.domain_entry.grid(row=0, column=1)
        tk.Label(frame_wp, text='아이디').grid(row=1, column=0, sticky='e')
        self.user_entry = tk.Entry(frame_wp, width=40)
        self.user_entry.grid(row=1, column=1)
        tk.Label(frame_wp, text='비밀번호').grid(row=2, column=0, sticky='e')
        self.pw_entry = tk.Entry(frame_wp, show='*', width=40)
        self.pw_entry.grid(row=2, column=1)
        self.wp_add_btn = tk.Button(frame_wp, text='계정 인증 후 추가', command=self.add_wp_account)
        self.wp_add_btn.grid(row=3, column=0, columnspan=2, pady=5)
        self.wp_result = tk.Label(frame_wp, text='', fg='blue')
        self.wp_result.grid(row=4, column=0, columnspan=2)
        tk.Label(frame_wp, text='추가된 계정 목록').grid(row=5, column=0, columnspan=2)
        self.wp_listbox = tk.Listbox(frame_wp, width=50, height=4)
        self.wp_listbox.grid(row=6, column=0, columnspan=2, pady=5)
        self.wp_accounts = []

        # 카테고리 및 글 작성 영역 (이제 __init__에서만 생성)
        frame_cat = tk.LabelFrame(self, text='카테고리 조회 및 글 작성', padx=10, pady=10)
        frame_cat.pack(fill='both', expand=True, padx=10, pady=5)
        tk.Label(frame_cat, text='계정 선택 후 카테고리 조회').grid(row=0, column=0, columnspan=2)
        self.cat_btn = tk.Button(frame_cat, text='선택 계정의 카테고리 조회', command=self.fetch_categories)
        self.cat_btn.grid(row=1, column=0, columnspan=2, pady=5)
        self.category_vars = []
        self.category_checks_frame = tk.Frame(frame_cat)
        self.category_checks_frame.grid(row=6, column=0, columnspan=2, pady=5)
        self.cat_result = scrolledtext.ScrolledText(frame_cat, width=60, height=8)
        self.cat_result.grid(row=2, column=0, columnspan=2)
        tk.Label(frame_cat, text='글 제목').grid(row=3, column=0, sticky='e')
        self.post_title_entry = tk.Entry(frame_cat, width=40)
        self.post_title_entry.grid(row=3, column=1)
        tk.Label(frame_cat, text='글 내용').grid(row=4, column=0, sticky='e')
        self.post_content_entry = tk.Entry(frame_cat, width=40)
        self.post_content_entry.grid(row=4, column=1)
        self.post_btn = tk.Button(frame_cat, text='선택 카테고리에 글 작성', command=self.create_post_to_category)
        self.post_btn.grid(row=5, column=0, columnspan=2, pady=5)
        self.categories = []
        # ...existing code...
    def add_wp_account(self):
        domain = self.domain_entry.get().strip().rstrip('/')
        username = self.user_entry.get().strip()
        password = self.pw_entry.get().strip()
        self.wp_result.config(text='')
        if not domain or not username or not password:
            self.wp_result.config(text='도메인, 아이디, 비밀번호를 모두 입력하세요.', fg='red')
            return
        display = f"{domain} | {username}"

        # 1. Basic Auth 플러그인 활성화 및 REST API 접근 체크
        plugin_check_url = f"{domain}/wp-json/"
        try:
            plugin_resp = requests.get(plugin_check_url, auth=HTTPBasicAuth(username, password))
            if plugin_resp.status_code == 200:
                # 2. 계정 권한(글 작성 가능 여부) 체크
                post_check_url = f"{domain}/wp-json/wp/v2/posts"
                post_resp = requests.post(post_check_url, auth=HTTPBasicAuth(username, password), json={"title": "권한 체크", "content": "테스트", "status": "draft"})
                if post_resp.status_code == 201:
                    self.wp_result.config(text=f'계정이 추가되었습니다: {display}\n플러그인/REST API/권한 정상 (글 작성 가능)', fg='blue')
                elif post_resp.status_code == 401:
                    self.wp_result.config(text=f'계정이 추가되었습니다: {display}\n플러그인 정상, 글 작성 권한 없음 (401)', fg='orange')
                else:
                    self.wp_result.config(text=f'계정이 추가되었습니다: {display}\n플러그인 정상, 글 작성 권한 오류: {post_resp.status_code}', fg='orange')
            elif plugin_resp.status_code == 401:
                self.wp_result.config(text=f'플러그인/REST API 인증 실패 (401): 아이디/비밀번호 또는 플러그인 설정 확인 필요', fg='red')
                return
            else:
                self.wp_result.config(text=f'플러그인/REST API 오류: {plugin_resp.status_code}', fg='red')
                return
        except Exception as e:
            self.wp_result.config(text=f'플러그인/REST API 네트워크 오류: {e}', fg='red')
            return

        self.wp_accounts.append({'domain': domain, 'username': username, 'password': password})
        self.wp_listbox.insert(tk.END, display)
        self.domain_entry.delete(0, tk.END)
        self.user_entry.delete(0, tk.END)
        self.pw_entry.delete(0, tk.END)

    def check_gemini_api(self):
        api_key = self.gemini_entry.get().strip()
        model_name = self.gemini_model_entry.get().strip()
        self.gemini_result.config(text='')
        if not api_key or not model_name:
            self.gemini_result.config(text='Gemini API 키와 모델명을 입력하세요.', fg='red')
            return
        if not genai:
            self.gemini_result.config(text='google-generativeai 라이브러리가 없습니다.', fg='red')
            return
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Explain how AI works in a few words")
            self.gemini_result.config(text=f"Gemini 인증 성공! 응답: {getattr(response, 'text', str(response))}", fg='blue')
            self.gemini_entry.config(state='disabled')
            self.gemini_model_entry.config(state='disabled')
            self.gemini_btn.config(state='disabled')
        except Exception as e:
            self.gemini_result.config(text=f"Gemini 인증 실패: {e}", fg='red')

    def check_wp_login(self):
        domain = self.domain_entry.get().strip().rstrip('/')
        username = self.user_entry.get().strip()
        password = self.pw_entry.get().strip()
        api_url = f"{domain}/wp-json/wp/v2/posts"
        self.wp_result.config(text='')
        if not domain or not username or not password:
            self.wp_result.config(text='도메인, 아이디, 비밀번호를 모두 입력하세요.', fg='red')
            return
        try:
            response = requests.get(api_url, auth=HTTPBasicAuth(username, password))
            if response.status_code == 200:
                self.wp_result.config(text=f'워드프레스 인증 성공! ({domain} | {username})', fg='blue')
            elif response.status_code == 401:
                self.wp_result.config(text='인증 실패: 사용자 이름 또는 비밀번호가 올바르지 않습니다.', fg='red')
            else:
                self.wp_result.config(text=f"오류 발생: {response.status_code}", fg='red')
        except Exception as e:
            self.wp_result.config(text=f"네트워크 또는 요청 오류 발생: {e}", fg='red')

    def fetch_categories(self):
        selection = self.wp_listbox.curselection()
        self.cat_result.delete('1.0', tk.END)
        if not selection:
            self.cat_result.insert(tk.END, '계정을 선택하세요.\n')
            if self.category_menu:
                self.category_menu.pack_forget()
            return
        idx = selection[0]
        account = self.wp_accounts[idx]
        domain = account['domain']
        username = account['username']
        password = account['password']
        categories_url = f"{domain}/wp-json/wp/v2/categories"
        if not domain or not username or not password:
            self.cat_result.insert(tk.END, '도메인, 아이디, 비밀번호를 모두 입력하세요.\n')
            if self.category_menu:
                self.category_menu.pack_forget()
            return
        try:
            response = requests.get(categories_url, auth=HTTPBasicAuth(username, password))
            if response.status_code == 200:
                categories = response.json()
                self.categories = categories
                # 기존 체크박스 제거
                for widget in self.category_checks_frame.winfo_children():
                    widget.destroy()
                self.category_vars = []
                self.cat_result.insert(tk.END, '\n--- 카테고리 목록 ---\n')
                for cat in categories:
                    var = tk.BooleanVar()
                    chk = tk.Checkbutton(self.category_checks_frame, text=f"{cat['name']} (ID:{cat['id']})", variable=var)
                    chk.pack(anchor='w')
                    self.category_vars.append((var, cat['id']))
                    self.cat_result.insert(tk.END, f"ID: {cat['id']} | 이름: {cat['name']}\n")
            elif response.status_code == 401:
                self.cat_result.insert(tk.END, '인증 실패: 사용자 이름 또는 비밀번호가 올바르지 않습니다.\n')
                self.cat_result.insert(tk.END, f"[디버그] 응답 헤더: {response.headers}\n")
                self.cat_result.insert(tk.END, f"[디버그] 응답 본문: {response.text}\n")
            else:
                self.cat_result.insert(tk.END, f"오류 발생: {response.status_code}\n{response.text}\n")
        except Exception as e:
            self.cat_result.insert(tk.END, f"네트워크 또는 요청 오류 발생: {e}\n")

    def create_post_to_category(self):
        selection = self.wp_listbox.curselection()
        if not selection:
            self.cat_result.insert(tk.END, '계정을 선택하세요.\n')
            return
        idx = selection[0]
        account = self.wp_accounts[idx]
        domain = account['domain']
        username = account['username']
        password = account['password']
        if not self.categories:
            self.cat_result.insert(tk.END, '카테고리 정보를 먼저 조회하세요.\n')
            return
        selected_ids = [cat_id for var, cat_id in self.category_vars if var.get()]
        if not selected_ids:
            self.cat_result.insert(tk.END, '카테고리를 하나 이상 선택하세요.\n')
            return
        title = self.post_title_entry.get().strip()
        content = self.post_content_entry.get().strip()
        if not title or not content:
            self.cat_result.insert(tk.END, '글 제목과 내용을 입력하세요.\n')
            return
        post_url = f"{domain}/wp-json/wp/v2/posts"
        post_data = {
            "title": title,
            "content": content,
            "categories": selected_ids,
            "status": "publish"
        }
        try:
            response = requests.post(post_url, auth=HTTPBasicAuth(username, password), json=post_data)
            if response.status_code == 201:
                self.cat_result.insert(tk.END, f"✅ 글이 성공적으로 등록되었습니다! (ID: {response.json().get('id')})\n")
            elif response.status_code == 401:
                self.cat_result.insert(tk.END, '❌ 인증 실패: 사용자 이름 또는 비밀번호가 올바르지 않습니다.\n')
                self.cat_result.insert(tk.END, f"[디버그] 응답 헤더: {response.headers}\n")
                self.cat_result.insert(tk.END, f"[디버그] 응답 본문: {response.text}\n")
            else:
                self.cat_result.insert(tk.END, f"⚠️ 오류 발생: {response.status_code}\n{response.text}\n")
        except Exception as e:
            self.cat_result.insert(tk.END, f"네트워크 또는 요청 오류 발생: {e}\n")

if __name__ == '__main__':
    app = UnifiedWPBotGUI()
    app.mainloop()
