import tkinter as tk
from tkinter import messagebox, filedialog
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import os
import pandas as pd
import subprocess
import sys
import time

# --- 전역 변수 ---
excel_file_path = ""

# --- 함수 정의 ---
def select_excel_file():
    """엑셀 파일을 선택하고 경로를 저장하는 함수"""
    global excel_file_path
    filepath = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=(("Excel files", "*.xlsx *.xls"), ("All files", "*.*"))
    )
    if filepath:
        excel_file_path = filepath
        excel_path_label.config(text=os.path.basename(filepath))

def start_process():
    """GUI에서 정보를 가져와 워드프레스 글 발행을 시작하는 메인 함수"""
    if not excel_file_path:
        messagebox.showwarning("파일 없음", "엑셀 파일을 먼저 선택해주세요.")
        return

    try:
        # header=None을 추가하여 첫 번째 행부터 바로 데이터로 읽도록 수정
        df = pd.read_excel(excel_file_path, engine=None, header=None)
        if df.empty or len(df.columns) < 2:
            messagebox.showerror("엑셀 파일 오류", "엑셀 파일이 비어있거나, 제목(A열)과 내용(B열)에 해당하는 두 개의 열이 없습니다.")
            return
    except ImportError as e:
        missing_package = ""
        error_msg = str(e).lower()
        if 'openpyxl' in error_msg:
            missing_package = 'openpyxl'
        elif 'xlrd' in error_msg:
            missing_package = 'xlrd'
        
        if missing_package:
            install_consent = messagebox.askyesno(
                "필수 라이브러리 없음",
                f"엑셀 파일을 읽기 위해 '{missing_package}' 라이브러리가 필요합니다.\n지금 바로 설치하시겠습니까?"
            )
            if install_consent:
                try:
                    # 현재 스크립트를 실행 중인 파이썬을 이용해 라이브러리 설치
                    subprocess.check_call([sys.executable, "-m", "pip", "install", missing_package])
                    messagebox.showinfo("설치 완료", f"'{missing_package}' 라이브러리를 성공적으로 설치했습니다.\n다시 '작업 시작' 버튼을 눌러주세요.")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    messagebox.showerror("설치 실패", f"'{missing_package}' 라이브러리 자동 설치에 실패했습니다.\n터미널을 열어 수동으로 설치해주세요:\npython -m pip install {missing_package}")
            else:
                messagebox.showwarning("작업 취소", "필수 라이브러리가 없어 작업을 진행할 수 없습니다.")
        else:
             messagebox.showerror("라이브러리 오류", f"알 수 없는 라이브러리 오류가 발생했습니다: {e}")
        return
    except Exception as e:
        messagebox.showerror("엑셀 읽기 오류", f"엑셀 파일을 읽는 중 오류가 발생했습니다: {e}")
        return

    domain = domain_entry.get()
    username = username_entry.get()
    password = password_entry.get()

    try:
        delay_seconds = float(delay_entry.get())
        if delay_seconds < 0: raise ValueError
    except ValueError:
        messagebox.showwarning("입력 오류", "딜레이 시간은 0 이상의 숫자로 입력해주세요.")
        return

    if not all([domain, username, password]):
        messagebox.showwarning("입력 오류", "모든 필드를 입력해주세요.")
        return

    try:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 15)

        # 1. 로그인
        login_url = f"https://{domain}/wp-admin"
        driver.get(login_url)

        user_login_elem = wait.until(EC.presence_of_element_located((By.ID, "user_login")))
        user_login_elem.send_keys(username)
        driver.find_element(By.ID, "user_pass").send_keys(password)
        driver.find_element(By.ID, "wp-submit").click()
        
        wait.until(EC.presence_of_element_located((By.ID, "wpadminbar")))

        # 2. 엑셀 파일 반복하며 글 발행
        posts_created = 0
        for index, row in df.iterrows():
            post_title = row.iloc[0]
            post_content = row.iloc[1]

            if pd.isna(post_title) or str(post_title).strip() == "":
                break

            # 새 글 작성 페이지로 이동
            driver.get(f"https://{domain}/wp-admin/post-new.php")
            wait.until(EC.presence_of_element_located((By.ID, "title")))

            # 제목 입력 (클릭이 가로채이는 문제를 해결하기 위해 실제 입력 필드에 직접 입력)
            title_input = wait.until(EC.presence_of_element_located((By.ID, "title")))
            title_input.send_keys(str(post_title))
            time.sleep(delay_seconds)
            
            # 본문 입력 (선택한 에디터 모드에 따라 분기)
            editor_mode_selection = editor_mode.get()

            if editor_mode_selection == "HTML":
                try:
                    wait.until(EC.element_to_be_clickable((By.ID, "content-html"))).click()
                    time.sleep(delay_seconds)
                    content_area = driver.find_element(By.CLASS_NAME, "wp-editor-area")
                    content_area.clear()
                    content_area.send_keys(str(post_content))
                    time.sleep(delay_seconds)
                except Exception as e:
                    messagebox.showerror("에디터 오류", f"HTML 에디터 모드로 전환하거나 내용을 입력하는 데 실패했습니다.\n{e}")
                    break
            elif editor_mode_selection == "Visual":
                try:
                    wait.until(EC.element_to_be_clickable((By.ID, "content-tmce"))).click()
                    time.sleep(delay_seconds)
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "content_ifr")))
                    editor_body = driver.find_element(By.ID, "tinymce")
                    editor_body.clear()
                    editor_body.send_keys(str(post_content))
                    time.sleep(delay_seconds)
                    driver.switch_to.default_content()
                except Exception as e:
                    messagebox.showerror("에디터 오류", f"비주얼 에디터 모드로 전환하거나 내용을 입력하는 데 실패했습니다.\n{e}")
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass
                    break

            # 발행
            publish_button = driver.find_element(By.ID, "publish")
            driver.execute_script("arguments[0].click();", publish_button)
            
            # 발행 완료 확인
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Post published.') or contains(text(), '게시글이 발행되었습니다.')]")))
            
            posts_created += 1

        messagebox.showinfo("성공", f"총 {posts_created}개의 글을 성공적으로 발행했습니다.")

    except (NoSuchElementException, TimeoutException) as e:
        messagebox.showerror("오류", f"페이지의 요소를 찾지 못했거나 시간 초과되었습니다. (클래식 편집기 모드가 맞는지 확인해주세요)\n{e}")
    except Exception as e:
        messagebox.showerror("알 수 없는 오류", f"오류가 발생했습니다: {e}")
    finally:
        # 작업이 끝나면 브라우저를 닫되, 이미 닫혔을 경우 오류를 발생시키지 않음
        if 'driver' in locals():
            try:
                driver.quit()
            except Exception:
                pass

# --- GUI 설정 ---
root = tk.Tk()
root.title("워드프레스 자동 글 발행")
root.geometry("450x320")

main_frame = tk.Frame(root, padx=10, pady=10)
main_frame.pack(fill="both", expand=True)

# 입력 필드
tk.Label(main_frame, text="도메인:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
domain_entry = tk.Entry(main_frame, width=40)
domain_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5)

tk.Label(main_frame, text="아이디:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
username_entry = tk.Entry(main_frame, width=40)
username_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5)

tk.Label(main_frame, text="패스워드:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
password_entry = tk.Entry(main_frame, width=40, show="*")
password_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5)

# 엑셀 파일 선택
tk.Label(main_frame, text="엑셀 파일:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
excel_path_label = tk.Label(main_frame, text="선택된 파일 없음", width=25, anchor="w", fg="gray")
excel_path_label.grid(row=3, column=1, padx=5, pady=5, sticky="w")
excel_select_button = tk.Button(main_frame, text="파일 선택", command=select_excel_file)
excel_select_button.grid(row=3, column=2, padx=5, pady=5, sticky="ew")

# 에디터 모드 선택
editor_mode = tk.StringVar(value="HTML")
tk.Label(main_frame, text="에디터 모드:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
# 라디오 버튼이 겹치지 않도록 프레임 안에 배치
radio_frame = tk.Frame(main_frame)
radio_frame.grid(row=4, column=1, columnspan=2, sticky="w")
tk.Radiobutton(radio_frame, text="HTML", variable=editor_mode, value="HTML").pack(side="left", padx=5)
tk.Radiobutton(radio_frame, text="비주얼", variable=editor_mode, value="Visual").pack(side="left", padx=5)

# 딜레이 설정
tk.Label(main_frame, text="작업 딜레이(초):").grid(row=5, column=0, padx=5, pady=5, sticky="e")
delay_entry = tk.Entry(main_frame, width=10)
delay_entry.grid(row=5, column=1, sticky="w", padx=5)
delay_entry.insert(0, "1")

# 실행 버튼
process_button = tk.Button(main_frame, text="작업 시작", command=start_process, height=2)
process_button.grid(row=6, column=1, columnspan=2, pady=15, sticky="ew")

root.mainloop()
