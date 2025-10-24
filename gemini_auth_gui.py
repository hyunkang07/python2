import tkinter as tk
from tkinter import scrolledtext
import google.generativeai as genai

class GeminiAuthGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Gemini API 인증')
        self.geometry('400x200')

        tk.Label(self, text='Gemini API Key').pack()
        self.gemini_entry = tk.Entry(self, width=50)
        self.gemini_entry.pack()
        tk.Label(self, text='Gemini 모델명').pack()
        self.gemini_model_entry = tk.Entry(self, width=50)
        self.gemini_model_entry.insert(0, 'gemini-2.5-flash')
        self.gemini_model_entry.pack()
        self.gemini_btn = tk.Button(self, text='Gemini API 키 인증', command=self.check_gemini_api)
        self.gemini_btn.pack(pady=7)
        self.result_text = scrolledtext.ScrolledText(self, width=50, height=5)
        self.result_text.pack()

    def check_gemini_api(self):
        api_key = self.gemini_entry.get().strip()
        model_name = self.gemini_model_entry.get().strip()
        self.result_text.delete('1.0', tk.END)
        if not api_key or not model_name:
            self.result_text.insert(tk.END, 'Gemini API 키와 모델명을 입력하세요.\n')
            return
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Explain how AI works in a few words")
            self.result_text.insert(tk.END, f"✅ Gemini API 인증 성공!\n응답: {getattr(response, 'text', str(response))}\n")
            self.gemini_entry.config(state='disabled')
            self.gemini_model_entry.config(state='disabled')
            self.gemini_btn.config(state='disabled')
        except ImportError:
            self.result_text.insert(tk.END, "❌ google-generativeai 라이브러리가 없습니다.\npip install google-generativeai\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"❌ Gemini API 인증 실패: {e}\n")

if __name__ == '__main__':
    app = GeminiAuthGUI()
    app.mainloop()
