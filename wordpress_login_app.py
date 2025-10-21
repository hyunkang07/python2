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
from selenium.webdriver.support.ui import Select
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
        wait = WebDriverWait(driver, 30) # 대기 시간을 30초로 늘림

        # 1. 로그인
        login_url = f"https://{domain}/wp-admin"
        driver.get(login_url)

        user_login_elem = wait.until(EC.presence_of_element_located((By.ID, "user_login")))
        user_login_elem.send_keys(username)
        driver.find_element(By.ID, "user_pass").send_keys(password)
        driver.find_element(By.ID, "wp-submit").click()
        
        wait.until(EC.presence_of_element_located((By.ID, "wpadminbar")))

        # 로그인 성공 여부 재확인
        if "wp-login.php" in driver.current_url:
            messagebox.showerror("로그인 실패", "로그인에 실패했습니다. 아이디 또는 비밀번호를 확인해주세요.")
            driver.quit()
            return

        # 2. 첫 번째 새 글 작성 페이지로 이동
        try:
            driver.get(f"https://{domain}/wp-admin/post-new.php")
        except Exception as e:
            messagebox.showerror("페이지 이동 오류", f"'새 글 작성' 페이지로 이동하는 데 실패했습니다.\n\n오류: {e}")
            driver.quit()
            return
        
        # 3. 엑셀 파일 반복하며 글 발행
        posts_created = 0
        for index, row in df.iterrows():
            # (데이터 추출 및 제목, 본문, 이미지, 날짜 입력 로직은 동일)
            # 새 글 작성 페이지 로딩 대기
            wait.until(EC.presence_of_element_located((By.ID, "title")))
            
            # 제목 입력
            title_input = driver.find_element(By.ID, "title")
            title_input.clear()
            title_input.send_keys(str(row.iloc[0]))
            time.sleep(delay_seconds)
            
            # 본문 입력 (이전 코드 복원)
            editor_mode_selection = editor_mode.get()
            if editor_mode_selection == "HTML":
                try:
                    wait.until(EC.element_to_be_clickable((By.ID, "content-html"))).click()
                    time.sleep(delay_seconds)
                    content_area = driver.find_element(By.CLASS_NAME, "wp-editor-area")
                    content_area.clear()
                    content_area.send_keys(str(row.iloc[1]))
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
                    editor_body.send_keys(str(row.iloc[1]))
                    time.sleep(delay_seconds)
                    driver.switch_to.default_content()
                except Exception as e:
                    messagebox.showerror("에디터 오류", f"비주얼 에디터 모드로 전환하거나 내용을 입력하는 데 실패했습니다.\n{e}")
                    try: driver.switch_to.default_content()
                    except: pass
                    break

            # 특성 이미지 URL 입력
            if str(row.iloc[2]).strip():
                try:
                    fifu_input = wait.until(EC.presence_of_element_located((By.ID, "fifu_input_url")))
                    fifu_input.clear()
                    fifu_input.send_keys(str(row.iloc[2]))
                    time.sleep(delay_seconds)
                except TimeoutException:
                    messagebox.showwarning("경고", "특성 이미지 URL 입력 필드(ID='fifu_input_url')를 찾지 못했습니다.")
                    pass

            # 발행 날짜 설정 (D열) - 안정성 강화 및 디버깅 추가
            if str(row.iloc[3]):
                dt_obj = None
                try:
                    # 1. 날짜 형식 파싱 시도
                    dt_obj = pd.to_datetime(str(row.iloc[3]))
                except Exception:
                    messagebox.showwarning("날짜 형식 오류", f"엑셀 D열의 날짜 형식을 변환할 수 없습니다: '{str(row.iloc[3])}'\n\n올바른 형식(예: 2025-10-21 14:30)인지 확인해주세요.")

                if dt_obj:
                    try:
                        # 2. '편집' 링크 클릭 (JS 클릭으로 안정성 향상)
                        edit_timestamp_link = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.edit-timestamp")))
                        driver.execute_script("arguments[0].click();", edit_timestamp_link)
                        
                        # 3. 날짜 입력 필드가 나타날 때까지 대기
                        wait.until(EC.visibility_of_element_located((By.ID, "mm")))
                        
                        # 4. 날짜/시간 값 입력
                        Select(driver.find_element(By.ID, 'mm')).select_by_value(dt_obj.strftime('%m'))
                        jj = driver.find_element(By.ID, 'jj'); jj.clear(); jj.send_keys(dt_obj.strftime('%d'))
                        aa = driver.find_element(By.ID, 'aa'); aa.clear(); aa.send_keys(str(dt_obj.year))
                        hh = driver.find_element(By.ID, 'hh'); hh.clear(); hh.send_keys(dt_obj.strftime('%H'))
                        mn = driver.find_element(By.ID, 'mn'); mn.clear(); mn.send_keys(dt_obj.strftime('%M'))
                        
                        # 5. '확인' 버튼 클릭 (JS 클릭으로 안정성 향상)
                        save_timestamp_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.save-timestamp")))
                        driver.execute_script("arguments[0].click();", save_timestamp_button)

                        # 6. 날짜 편집 영역이 다시 사라질 때까지 대기 (성공 확인)
                        wait.until(EC.invisibility_of_element_located((By.ID, "timestampdiv")))
                        time.sleep(delay_seconds)
                    except Exception as e:
                        messagebox.showwarning("날짜 설정 실패", f"날짜를 설정하는 중 오류가 발생하여 건너뜁니다.\n\n오류: {e}")
                        # 날짜 설정 실패 시 '취소'를 눌러 열린 창을 닫아줌
                        try:
                            cancel_button = driver.find_element(By.CSS_SELECTOR, "a.cancel-timestamp")
                            driver.execute_script("arguments[0].click();", cancel_button)
                        except:
                            pass

            # 임시 저장
            try:
                save_button = wait.until(EC.element_to_be_clickable((By.ID, "save-post")))
                driver.execute_script("arguments[0].click();", save_button)
                # 저장 완료 확인
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Draft saved.') or contains(text(), '초고가 저장되었습니다.')]")))
                posts_created += 1
            except TimeoutException:
                messagebox.showerror("오류", "'임시 저장' 버튼을 찾거나 저장 완료 메시지를 확인할 수 없습니다.")
                break
            
            # 마지막 행이 아니면 '새로 추가' 버튼 클릭 (뒤로 가기 재시도 기능 추가)
            if (index + 1) < len(df) and (pd.notna(df.iloc[index + 1].iloc[0])):
                try:
                    # 페이지 안정화를 위해 3초 대기
                    time.sleep(3)
                    
                    # 1차 시도
                    add_new_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "page-title-action")))
                    driver.execute_script("arguments[0].scrollIntoView(true);", add_new_button)
                    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "page-title-action")))
                    driver.execute_script("arguments[0].click();", add_new_button)
                except TimeoutException:
                    # 1차 시도 실패 시, 뒤로 갔다가 재시도
                    try:
                        driver.back()
                        time.sleep(3) # 페이지 로드 대기
                        
                        # 2차 시도
                        add_new_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "page-title-action")))
                        driver.execute_script("arguments[0].scrollIntoView(true);", add_new_button)
                        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "page-title-action")))
                        driver.execute_script("arguments[0].click();", add_new_button)
                    except TimeoutException:
                        messagebox.showerror("오류", "'새로 추가(page-title-action)' 버튼을 찾지 못하여 작업을 중단합니다.\n\n뒤로 가기 후 재시도했지만 실패했습니다.")
                        break
            else:
                break # 마지막 행이거나 다음 제목이 비어있으면 루프 종료

        messagebox.showinfo("성공", f"총 {posts_created}개의 글을 성공적으로 임시 저장했습니다.")

    except (NoSuchElementException, TimeoutException) as e:
        messagebox.showerror("오류", f"페이지의 요소를 찾지 못했거나 시간 초과되었습니다.\n{e}")
    except Exception as e:
        messagebox.showerror("알 수 없는 오류", f"오류가 발생했습니다: {e}")
    finally:
        if 'driver' in locals():
            try:
                driver.quit() # 자동 종료 기능 복원
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
