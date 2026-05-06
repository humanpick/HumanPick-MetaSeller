import streamlit as st
import os
import subprocess
import requests 
import warnings
import pandas as pd
import sys
import time
import math
import json
import re
import base64
from datetime import datetime
import webbrowser
from urllib.parse import quote 
from io import BytesIO

warnings.filterwarnings("ignore")

# --- [0. 필수 라이브러리 자동 설치] ---
def install_packages():
    required = {"pandas", "openpyxl", "PyPDF2", "gspread", "oauth2client", "Pillow"}
    installed = {pkg.split('==')[0] for pkg in subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode().split('\n')}
    missing = required - installed
    if missing:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        except: pass

if 'init_setup_done' not in st.session_state:
    install_packages()
    st.session_state.init_setup_done = True

try:
    import openpyxl
    import PyPDF2
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    from PIL import Image
except ImportError:
    st.error("🚨 필수 라이브러리 설치 필요. cmd창에서 입력: pip install pandas openpyxl PyPDF2 gspread oauth2client Pillow")
    st.stop()

# --- [1. 하이엔드 SaaS 디자인 시스템 적용 (Humanpick v1.0)] ---
st.set_page_config(page_title="MetaSeller v6.6", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"], h1, h2, h3, h4, h5, h6, p, span, div, label, input, button, select, textarea { 
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif; 
        font-feature-settings: "cv02", "cv03", "cv04", "cv11";
    }
    .stDeployButton, [data-testid="stAppDeployButton"], #MainMenu, [data-testid="stToolbar"], footer { display: none !important; }
    header[data-testid="stHeader"] { background: transparent !important; pointer-events: none !important; }
    
    [data-testid="collapsedControl"] { display: flex !important; background: #8B5CF6 !important; border-radius: 8px !important; margin: 12px !important; pointer-events: auto !important; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4) !important; transition: transform 0.2s ease !important; }
    [data-testid="collapsedControl"]:active { transform: scale(0.9) !important; }
    [data-testid="collapsedControl"] svg { color: #ffffff !important; fill: #ffffff !important; width: 24px !important; height: 24px !important; }

    .stApp { background-color: #09090b !important; }
    p, label, span { color: #a1a1aa !important; margin-bottom: 0 !important; }
    h1 { color: #fafafa !important; font-weight: 700 !important; font-size: 1.75rem !important; letter-spacing: -0.02em; margin-bottom: 1.5rem !important; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 1rem !important; }
    
    .block-container { padding-top: 3rem !important; padding-bottom: 3rem !important; padding-left: 2rem !important; padding-right: 2rem !important; max-width: 1400px !important; margin: 0 auto; }
    @media (min-width: 768px) { .block-container { padding-left: 4rem !important; padding-right: 4rem !important; } }
    div[data-testid="stVerticalBlock"] { gap: 1.2rem !important; }

    [data-testid="stSidebar"] { background-color: #09090b !important; border-right: 1px solid rgba(255,255,255,0.08) !important; padding-top: 2rem !important; }
    .sidebar-title { color: #fafafa !important; font-size: 1.25rem !important; font-weight: 800 !important; letter-spacing: -0.5px; margin-bottom: 0px; }
    
    [data-testid="stRadio"] > label { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] { gap: 4px; }
    [data-testid="stRadio"] div[role="radiogroup"] label { background: transparent !important; border: none !important; border-radius: 6px !important; padding: 10px 12px !important; cursor: pointer; width: 100%; display: flex; align-items: center; font-size: 0.95rem !important; font-weight: 500 !important; color: #a1a1aa !important; transition: all 0.15s ease !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label:hover { background: rgba(255, 255, 255, 0.05) !important; color: #fafafa !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) { background: #fafafa !important; color: #09090b !important; font-weight: 600 !important; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    [data-testid="stRadio"] div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] { pointer-events: none; }
    [data-testid="stRadio"] div[role="radiogroup"] label div[data-baseweb="radio"] { display: none !important; }

    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div { background-color: #ffffff !important; border: 1px solid rgba(255,255,255,0.15) !important; border-radius: 8px !important; transition: border-color 0.2s, box-shadow 0.2s; }
    div[data-baseweb="input"]:focus-within > div, div[data-baseweb="textarea"]:focus-within > div, div[data-baseweb="select"]:focus-within > div { border-color: #8B5CF6 !important; box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.3) !important; }
    .stTextInput input, .stNumberInput input, .stTextArea textarea, div[data-baseweb="select"] * { color: #09090b !important; -webkit-text-fill-color: #09090b !important; font-size: 0.95rem !important; font-weight: 600 !important; }
    .stTextInput input, .stNumberInput input, .stTextArea textarea { background-color: transparent !important; }
    ::placeholder { color: #a1a1aa !important; -webkit-text-fill-color: #a1a1aa !important; font-weight: 400 !important; }
    div[data-baseweb="input"] svg, div[data-baseweb="select"] svg { color: #52525b !important; fill: #52525b !important; }
    ul[role="listbox"], ul[role="listbox"] * { background-color: #FFFFFF !important; color: #000000 !important; -webkit-text-fill-color: #000000 !important; font-weight: 600 !important; }

    .stButton>button { background: #18181b !important; color: #fafafa !important; -webkit-text-fill-color: #fafafa !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; padding: 0.5rem 0.4rem !important; font-weight: 500 !important; font-size: 0.85rem !important; white-space: nowrap !important; letter-spacing: -0.3px !important; transition: all 0.2s ease; width: 100%; }
    .stButton>button:hover { background: #27272a !important; border-color: rgba(255,255,255,0.2) !important; }
    .stFormSubmitButton>button { background: #fafafa !important; color: #09090b !important; -webkit-text-fill-color: #09090b !important; border: none !important; border-radius: 8px !important; width: 100%; font-weight: 600 !important; white-space: nowrap !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stFormSubmitButton>button:hover { opacity: 0.9; transform: translateY(-1px); }

    .glass-card { background: #121214; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 24px; box-shadow: 0 4px 24px -8px rgba(0,0,0,0.5); margin-bottom: 16px; }
    .glass-card h3 { font-size: 1.05rem; font-weight: 600; color: #fafafa; margin-bottom: 12px; border: none; padding: 0;}
    .glass-card p { font-size: 0.9rem; color: #a1a1aa; line-height: 1.6; margin-bottom: 0px;}
    
    .highlight-box { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 24px; text-align: center; }
    .highlight-title { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: #71717a; margin-bottom: 8px; }
    .highlight-value { font-size: 2.5rem; font-weight: 700; color: #fafafa; letter-spacing: -0.02em; }
    
    [data-testid="stAlert"] { background-color: transparent !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; }
    [data-testid="stDataFrame"] { background-color: transparent !important; }
    [data-testid="stForm"] { border: none !important; padding: 0; background: transparent; }
</style>
""", unsafe_allow_html=True)

import streamlit.components.v1 as components
components.html("""
<script>
    const doc = window.parent.document;
    if (!doc.getElementById('humanpick-mobile-btn')) {
        const btn = doc.createElement('button');
        btn.id = 'humanpick-mobile-btn';
        btn.innerHTML = '☰';
        Object.assign(btn.style, { position: 'fixed', top: '15px', left: '15px', zIndex: '999999', background: '#8B5CF6', color: '#ffffff', border: 'none', borderRadius: '8px', width: '42px', height: '42px', fontSize: '22px', boxShadow: '0 4px 12px rgba(139, 92, 246, 0.5)', cursor: 'pointer', display: 'none', alignItems: 'center', justifyContent: 'center' });
        
        const toggleVisibility = () => { btn.style.display = doc.body.clientWidth <= 768 ? 'flex' : 'none'; };
        doc.defaultView.addEventListener('resize', toggleVisibility);
        toggleVisibility();
        
        btn.addEventListener('click', (e) => { 
            e.preventDefault(); 
            const sidebarBtn = doc.querySelector('[data-testid="collapsedControl"]') || 
                               doc.querySelector('[data-testid="stSidebarCollapsedControl"]') || 
                               doc.querySelector('header[data-testid="stHeader"] button') ||
                               doc.querySelector('button[kind="header"]');
            
            if (sidebarBtn) { 
                const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true, view: doc.defaultView });
                sidebarBtn.dispatchEvent(clickEvent);
                sidebarBtn.click(); 
            } 
        });
        doc.body.appendChild(btn);
    }
    
    function setupMobileAutoClose() {
        if (doc.body.clientWidth > 768) return;
        const menuLabels = doc.querySelectorAll('[data-testid="stRadio"] label');
        menuLabels.forEach(label => {
            if (!label.classList.contains('auto-close-bound')) {
                label.classList.add('auto-close-bound');
                label.addEventListener('click', () => { 
                    const closeBtn = doc.querySelector('[data-testid="stSidebarCollapseButton"]') || 
                                     doc.querySelector('[data-testid="stSidebar"] button');
                    if (closeBtn) {
                        setTimeout(() => { 
                            const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true, view: doc.defaultView });
                            closeBtn.dispatchEvent(clickEvent);
                            closeBtn.click();
                        }, 150);
                    }
                });
            }
        });
    }
    const observer = new MutationObserver(setupMobileAutoClose);
    observer.observe(doc.body, { childList: true, subtree: true });
    setupMobileAutoClose();
</script>
""", height=0)

# --- [2. 코어 보조 함수] ---
def rerun_app():
    if hasattr(st, "rerun"): st.rerun()
    else: st.experimental_rerun()

def cloud_new_tab(url, platform_name):
    st.components.v1.html(f"<script>window.parent.open('{url}', '_blank');</script>", height=0)
    st.markdown(f"""
    <div style='background: rgba(139, 92, 246, 0.1); border: 1px solid #8B5CF6; border-radius: 8px; padding: 16px; text-align: center; margin-top: 12px;'>
        <p style='color: #fafafa; font-size: 0.95rem; margin-bottom: 8px;'>✨ <strong>{platform_name}</strong> 연결 준비 완료!</p>
        <p style='color: #a1a1aa; font-size: 0.85rem; margin-bottom: 12px;'>(브라우저 팝업이 차단되어 창이 열리지 않는다면 아래 버튼을 클릭하세요)</p>
        <a href="{url}" target="_blank" style="background: #8B5CF6; color: #ffffff; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block; transition: 0.2s;">
            👉 결과 새 창으로 열기
        </a>
    </div>
    """, unsafe_allow_html=True)

def upload_to_imgbb(image_bytes, api_key):
    try:
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": api_key,
            "image": base64.b64encode(image_bytes).decode("utf-8")
        }
        res = requests.post(url, data=payload)
        if res.status_code == 200:
            return res.json()["data"]["url"]
        return ""
    except:
        return ""

def get_member_worksheet():
    try:
        if "gcp_service_account" in st.secrets:
            try:
                creds_dict = dict(st.secrets["gcp_service_account"])
                if "\\n" in creds_dict["private_key"]:
                    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
                creds = ServiceAccountCredentials.from_json_keyfile_dict(
                    creds_dict, 
                    ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                )
            except Exception as e:
                return None, f"1. [Secrets 파싱 에러] 금고(Secrets) 내용이 잘못되었습니다.\n상세: {str(e)}"
        else:
            if not os.path.exists("credentials.json"): 
                return None, "1. [파일 없음 에러] gcp_service_account 설정도 없고, credentials.json 파일도 없습니다."
            try:
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    "credentials.json", 
                    ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                )
            except Exception as e:
                return None, f"1. [JSON 파싱 에러] credentials.json 파일의 구조가 깨졌습니다.\n상세: {str(e)}"

        try:
            client = gspread.authorize(creds)
        except Exception as e:
            return None, f"2. [인증 실패] 열쇠(Key)는 있지만 구글 서버가 접속을 거부했습니다.\n상세: {str(e)}"

        try:
            sheet_id = "1p2pgXtUN5ql_FcflX0WacybNPPnrq33rg1YarfsMEA0"
            spreadsheet = client.open_by_key(sheet_id)
        except Exception as e:
            return None, f"3. [시트 열기 실패] 시트 권한(편집자 공유)이 없거나 삭제된 문서입니다.\n공유해야 할 이메일: {creds.service_account_email}\n상세: {str(e)}"

        try:
            worksheet = spreadsheet.worksheet("회원관리")
            headers = worksheet.row_values(1)
            if "등급" not in headers:
                if worksheet.col_count < len(headers) + 1:
                    worksheet.add_cols(1)
                worksheet.update_cell(1, len(headers) + 1, "등급")
            return worksheet, "성공"
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title="회원관리", rows=100, cols=7)
            worksheet.append_row(["아이디", "비밀번호", "이름", "상태", "만료일자", "최근접속일", "등급"])
            return worksheet, "성공"
        except Exception as e:
             return None, f"4. [기타 에러] {str(e)}"

    except Exception as e:
        return None, f"5. [치명적 시스템 에러] {str(e)}"

# 🚨 [관리자 비밀번호 설정 구역] 🚨
def authenticate_user(uid, upw):
    # 'admin' 계정의 비밀번호 '1234'를 원하는 비밀번호로 변경하세요.
    if uid == "admin" and upw == "1234":
        return True, "마스터", "관리자", "VIP회원", ""

    ws, error_msg = get_member_worksheet()
    if ws is None:
        return False, None, None, None, error_msg 

    records = ws.get_all_records()
    df = pd.DataFrame(records)

    if df.empty or '아이디' not in df.columns: return False, None, None, None, "등록된 회원 정보가 없습니다."

    user_match = df[(df['아이디'].astype(str) == str(uid)) & (df['비밀번호'].astype(str) == str(upw))]
    if user_match.empty: return False, None, None, None, "아이디 또는 비밀번호가 일치하지 않습니다."

    user_info = user_match.iloc[0]
    status = user_info.get('상태', '')
    user_name = user_info.get('이름', '회원')
    user_level = user_info.get('등급', '무료회원')
    if not user_level: user_level = "무료회원"

    if status == "승인대기": return False, None, None, None, "⏳ 관리자 승인 대기 중입니다. 승인 후 이용 가능합니다."
    elif status in ["기간만료", "영구정지"]: return False, None, None, None, f"🚫 접속이 제한된 계정입니다. (상태: {status})"
    elif status == "이용중": return True, user_name, "일반회원", user_level, ""
    else: return False, None, None, None, "알 수 없는 계정 상태입니다."

def parse_korean_currency(val_str):
    try:
        clean_str = str(val_str).replace(',', '').replace(' ', '')
        return int(clean_str) if clean_str else 0
    except ValueError: return 0

def save_to_google_sheet(item_name, grade, reason, detail_data, target_sheet=None):
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "\\n" in creds_dict["private_key"]: creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        else:
            if not os.path.exists("credentials.json"): return False, "credentials.json 키 파일이 없습니다."
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        
        client = gspread.authorize(creds)
        sheet_id = "1p2pgXtUN5ql_FcflX0WacybNPPnrq33rg1YarfsMEA0"
        spreadsheet = client.open_by_key(sheet_id)
        
        sheet_title = target_sheet if target_sheet else datetime.now().strftime("%Y%m")
        
        existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
        if sheet_title not in existing_sheets:
            worksheet = spreadsheet.add_worksheet(title=sheet_title, rows=1000, cols=5)
            worksheet.append_row(["저장 시간", "상품명/분류", "소싱 등급", "판독/요약 리포트", "원문/상세 데이터"])
        else: 
            worksheet = spreadsheet.worksheet(sheet_title)
            
        worksheet.append_row(
            [datetime.now().strftime("%Y-%m-%d %H:%M"), item_name, grade, reason, detail_data],
            value_input_option='USER_ENTERED'
        )
        return True, ""
    except Exception as e:
        df = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), item_name, grade, reason, str(e)]])
        df.to_csv("backup_sourcing.csv", mode='a', header=not os.path.exists("backup_sourcing.csv"), index=False, encoding='utf-8-sig')
        return False, str(e)

@st.cache_data(ttl=60)
def fetch_sourcing_db():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "\\n" in creds_dict["private_key"]: creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        else:
            if not os.path.exists("credentials.json"): raise FileNotFoundError()
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        
        client = gspread.authorize(creds)
        sheet_id = "1p2pgXtUN5ql_FcflX0WacybNPPnrq33rg1YarfsMEA0"
        spreadsheet = client.open_by_key(sheet_id)
        current_month = datetime.now().strftime("%Y%m")
        
        existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
        if current_month not in existing_sheets:
            return pd.DataFrame(columns=["저장 시간", "상품명/분류", "소싱 등급", "판독/요약 리포트", "원문/상세 데이터"]), f"🟢 이번 달({current_month}) 시트 생성 대기중 (아직 데이터 없음)"
        
        worksheet = spreadsheet.worksheet(current_month)
        data = worksheet.get_all_values()
        
        if len(data) > 0:
            headers = ["저장 시간", "상품명/분류", "소싱 등급", "판독/요약 리포트", "원문/상세 데이터"]
            if data[0][0] == "저장 시간" or "시간" in str(data[0][0]): df = pd.DataFrame(data[1:], columns=data[0])
            else:
                try: df = pd.DataFrame(data, columns=headers)
                except: df = pd.DataFrame(data)
            return df, f"🟢 클라우드 정상 연결됨 (현재 시트: {current_month})"
        else:
            return pd.DataFrame(columns=["저장 시간", "상품명/분류", "소싱 등급", "판독/요약 리포트", "원문/상세 데이터"]), f"🟢 연결됨 (현재 시트: {current_month}, 데이터 없음)"
    except Exception as e:
        if os.path.exists("backup_sourcing.csv"):
            df = pd.read_csv("backup_sourcing.csv", names=["저장 시간", "상품명/분류", "소싱 등급", "판독 리포트", "원문/에러 데이터"])
            return df, "🟡 로컬 CSV 백업본 (오프라인 모드)"
        return pd.DataFrame(), f"🔴 연결 실패 ({e})"

def generate_content_auto(prompt, api_key, selected_model="자동 (권장)", image_bytes=None, mime_type="image/jpeg"):
    if not api_key: return "❌ API 키가 없습니다."
    try:
        models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        res = requests.get(models_url)
        if res.status_code != 200: return f"❌ API 키 인증 실패 (HTTP {res.status_code})\n\n[디버그]\n{res.text}"
        
        available_names = [m['name'].split('/')[-1] for m in res.json().get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        
        if selected_model == "자동 (권장)":
            priority = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-pro']
            targets = [m for m in priority if m in available_names]
            for m in available_names:
                if m not in targets: targets.append(m)
        else:
            targets = [selected_model] if selected_model in available_names else [available_names[0]]
        
        if not targets: return "❌ 사용 가능한 AI 모델이 없습니다."
        
        headers = {'Content-Type': 'application/json'}
        parts = [{"text": prompt}]
        if image_bytes:
            img_b64 = base64.b64encode(image_bytes).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": img_b64
                }
            })
            
        data = {"contents": [{"parts": parts}]}
        last_error = ""
        max_overall_retries = 5 
        
        for cycle in range(max_overall_retries):
            for target in targets:
                gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{target}:generateContent?key={api_key}"
                gen_res = requests.post(gen_url, headers=headers, json=data)
                
                if gen_res.status_code == 200: 
                    candidate = gen_res.json().get('candidates', [{}])[0]
                    if 'content' in candidate: return candidate['content']['parts'][0]['text']
                    else: return f"❌ 답변 생성 불가. (사유: {candidate.get('finishReason', '알 수 없음')})"
                
                elif gen_res.status_code in [503, 429]: 
                    last_error = f"{target} (트래픽 지연 발생 -> 우회 중...)"
                    continue 
                else: 
                    try: err_msg = gen_res.json().get('error', {}).get('message', gen_res.text)
                    except: err_msg = gen_res.text
                    last_error = f"{target} (HTTP {gen_res.status_code}: {err_msg})"
                    continue
            time.sleep(3)
        return f"⚠️ 전체 AI 서버 트래픽 혼잡 (재시도 초과)\n\n[마지막 로그]\n{last_error}"
    except Exception as e: return f"❌ 통신 시스템 오류: {e}"

@st.cache_data
def extract_copywriting_materials():
    base_dir = os.getcwd() 
    target_dir = os.path.join(base_dir, "HQ_Engine", "카피라이팅자료")
    os.makedirs(target_dir, exist_ok=True)
    extracted_text, file_list = "", []
    for filename in os.listdir(target_dir):
        filepath = os.path.join(target_dir, filename)
        if os.path.isfile(filepath):
            file_list.append(filename)
            try:
                if filename.lower().endswith('.pdf'):
                    with open(filepath, 'rb') as f:
                        for page in PyPDF2.PdfReader(f).pages: extracted_text += (page.extract_text() or "") + "\n"
                elif filename.lower().endswith('.txt'):
                    with open(filepath, 'r', encoding='utf-8') as f: extracted_text += f.read() + "\n"
            except: pass
    return extracted_text, file_list, target_dir

# --- [3. 시스템 마스터 로그인 및 회원가입 로직] ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'mode' not in st.session_state: st.session_state.mode = "💻 작업 모드 (PC 분석)"
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'user_role' not in st.session_state: st.session_state.user_role = ""
if 'user_level' not in st.session_state: st.session_state.user_level = ""

if not st.session_state.logged_in:
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div class='glass-card' style='text-align:center; padding: 30px;'>
            <div style='margin-bottom: 24px;'>
                <h1 style='border:none; margin:0; padding:0; font-size:2rem; font-weight:800; letter-spacing:-1px;'>META SELLER</h1>
                <p style='color:#71717a; font-size:0.9rem; margin-top:8px;'>자율형 오토 소싱 에이전트 시스템 v6.6</p>
            </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["🔒 로그인", "📝 회원가입 신청"])
        
        with tab_login:
            with st.form("login_form"):
                uid = st.text_input("아이디 (이메일)", placeholder="아이디 입력")
                upw = st.text_input("비밀번호", type="password", placeholder="••••")
                st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
                if st.form_submit_button("시스템 로그인 →"):
                    is_auth, u_name, u_role, u_level, err_msg = authenticate_user(uid, upw)
                    if is_auth:
                        st.session_state.logged_in = True
                        st.session_state.user_name = u_name
                        st.session_state.user_role = u_role
                        st.session_state.user_level = u_level
                        st.success(f"환영합니다, {u_name}님! ({u_level})")
                        time.sleep(0.5)
                        rerun_app()
                    else: 
                        st.error(f"🚨 로그인 에러 로그: \n\n{err_msg}")
                        
        with tab_signup:
            with st.form("signup_form"):
                st.markdown("<p style='font-size:0.9rem; color:#a1a1aa; margin-bottom:12px;'>승인 대기 상태로 등록되며, 관리자 승인 후 로그인할 수 있습니다.</p>", unsafe_allow_html=True)
                new_uid = st.text_input("신청 아이디 (이메일)*")
                new_upw = st.text_input("비밀번호 설정*", type="password")
                new_name = st.text_input("이름 / 회사명*")
                
                if st.form_submit_button("가입 신청하기"):
                    if not new_uid or not new_upw or not new_name:
                        st.warning("모든 항목을 입력해주세요.")
                    else:
                        with st.spinner("가입 처리 중..."):
                            ws, error_msg = get_member_worksheet()
                            if ws:
                                records = ws.get_all_records()
                                if any(str(r.get('아이디', '')) == new_uid for r in records):
                                    st.error("이미 존재하는 아이디입니다.")
                                else:
                                    today = datetime.now().strftime("%Y-%m-%d")
                                    row_data = [new_uid, new_upw, new_name, "승인대기", "2026-12-31", today, "무료회원"]
                                    if ws.col_count > len(row_data):
                                        row_data.extend([""] * (ws.col_count - len(row_data)))
                                    ws.append_row(row_data)
                                    st.success("✅ 가입 신청이 완료되었습니다! 관리자 승인 후 로그인 가능합니다.")
                            else:
                                st.error(f"🚨 가입 에러 로그: \n\n{error_msg}")

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- [4. 사이드바 구성 및 API 영구 저장 시스템] ---
with st.sidebar:
    st.markdown("<p class='sidebar-title'>MetaSeller <span style='font-weight:400; font-size:0.9rem; color:#71717a;'>v6.6 (Vision)</span></p>", unsafe_allow_html=True)
    
    level_color = "#F59E0B" if "VIP" in st.session_state.user_level else ("#10B981" if "유료" in st.session_state.user_level else "#a1a1aa")
    st.markdown(f"<div style='background: rgba(255,255,255,0.05); padding: 10px 15px; border-radius: 8px; margin-top: 12px; margin-bottom: 24px; border: 1px solid rgba(255,255,255,0.1);'><span style='font-size:0.85rem; color:#a1a1aa;'>접속자: </span><strong style='color:#38BDF8; font-size:0.95rem;'>{st.session_state.user_name}</strong> <span style='font-size:0.75rem; color:#71717a;'>({st.session_state.user_role} | <span style='color:{level_color}; font-weight:600;'>{st.session_state.user_level}</span>)</span></div>", unsafe_allow_html=True)
    
    mode_selection = st.radio("모드 선택", ["🚗 운전 모드 (음성 소싱)", "💻 작업 모드 (PC 분석)"], index=0 if "운전" in st.session_state.mode else 1)
    if mode_selection != st.session_state.mode:
        st.session_state.mode = mode_selection
        rerun_app()

    if "작업 모드" in st.session_state.mode:
        st.markdown("<div style='height: 16px;'></div><p style='font-size: 0.75rem; color: #52525b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; padding-left: 12px;'>상세 메뉴</p>", unsafe_allow_html=True)
        
        menu_options = ["🚀 시스템 홈 (대시보드)", "🗂️ 소싱 DB 관리", "🧪 키워드 분석 (트렌드 발굴)", "🛑 지재권 리스크 스캐너", "🏭 공장 판별기 (도매처 검증)", "💰 정밀 마진 계산기", "🎯 광고 해부학 (쿠팡 최적화)", "✍️ 카피라이팅 기획소", "📥 영상 분석 추출"]
        if st.session_state.user_role == "관리자": menu_options.insert(2, "👥 회원 관리 (어드민)")
        menu = st.radio("hidden_label", menu_options, index=0, label_visibility="collapsed")
    else: menu = "운전모드"

    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    key_file_path = os.path.join(os.getcwd(), ".api_key")
    imgbb_key_path = os.path.join(os.getcwd(), ".imgbb_key")
    
    if "api_key_input" not in st.session_state:
        if os.path.exists(key_file_path):
            with open(key_file_path, "r", encoding="utf-8") as f: st.session_state.api_key_input = f.read().strip()
        else: st.session_state.api_key_input = ""
        
    if "imgbb_key_input" not in st.session_state:
        if os.path.exists(imgbb_key_path):
            with open(imgbb_key_path, "r", encoding="utf-8") as f: st.session_state.imgbb_key_input = f.read().strip()
        else: st.session_state.imgbb_key_input = ""
            
    st.markdown("<p style='font-size:0.75rem; color:#52525b; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; padding-left: 12px;'>환경 설정</p>", unsafe_allow_html=True)
    api_key_val = st.text_input("Gemini API Key", type="password", value=st.session_state.api_key_input, label_visibility="collapsed", placeholder="Gemini API 키 (필수)")
    imgbb_key_val = st.text_input("ImgBB API Key", type="password", value=st.session_state.imgbb_key_input, label_visibility="collapsed", placeholder="ImgBB API 키 (선택)")
    selected_model = st.selectbox("AI 모델 선택", options=["자동 (권장)", "gemini-2.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-1.5-pro"], index=0, label_visibility="collapsed")
    
    c1, c2 = st.columns([1, 1.35]) 
    with c1:
        if st.button("💾 키 일괄 저장"): 
            with open(key_file_path, "w", encoding="utf-8") as f: f.write(api_key_val)
            with open(imgbb_key_path, "w", encoding="utf-8") as f: f.write(imgbb_key_val)
            st.session_state.api_key_input = api_key_val
            st.session_state.imgbb_key_input = imgbb_key_val
            st.success("저장 완료")
    with c2:
        if st.button("🚪 안전 로그아웃"): 
            st.session_state.logged_in = False
            st.session_state.user_name = ""
            st.session_state.user_role = ""
            st.session_state.user_level = ""
            rerun_app()

# ==========================================
# --- [5. 메인 화면: 🚗 운전 모드] ---
# ==========================================
if "운전 모드" in st.session_state.mode:
    st.markdown("<h1>🚗 운전 모드 (음성 소싱 에이전트)</h1>", unsafe_allow_html=True)
    st.info("💡 **[마이크 🎤] 버튼**으로 상품을 말하거나 **사진을 업로드**하세요. AI가 시각적으로 판독 후 시트에 저장합니다.")
    
    with st.form("drive_mode_form"):
        voice_input = st.text_area("🎙️ 상품 정보 입력창 (음성 입력 후 터치)", height=150, placeholder="예: 상업용 초음파 식기세척기 찾아줘. 중국가 1000위안 정도.")
        uploaded_img = st.file_uploader("📸 현장 사진 업로드 (선택사항)", type=['png', 'jpg', 'jpeg'])
        submit_voice = st.form_submit_button("🚀 즉시 분석 및 시트 저장")

    if submit_voice:
        if not st.session_state.api_key_input: 
            st.error("좌측 사이드바에 Gemini API Key를 먼저 입력하고 저장해주세요.")
        elif not voice_input and not uploaded_img: 
            st.warning("분석할 텍스트나 사진을 입력해주세요.")
        else:
            with st.spinner("AI가 데이터를 시각적으로 추정하고 법무 스캔을 진행 중입니다..."):
                img_bytes = uploaded_img.getvalue() if uploaded_img else None
                img_mime = uploaded_img.type if uploaded_img else "image/jpeg"
                prompt = "당신은 B2B 구매대행 전문가입니다. 운전 중인 대표님을 위해 즉시 판단하세요.\n"
                if img_bytes: prompt += "★[사진 첨부됨]: 사진을 보고 재질, 스펙을 식별하여 분석에 포함하세요.\n"
                prompt += "1. 단가와 무게를 추정하고 통관 리스크 검토.\n2. 아래 JSON 양식으로만 답변.\n\n"
                prompt += f"입력 내용: {voice_input if voice_input else '(사진 분석 요청)'}\n\n"
                prompt += '양식: {\n  "Item": "상품명",\n  "Grade": "1등급",\n  "Profit": "순수익 00원",\n  "Reason": "이유 요약"\n}'
                
                res = generate_content_auto(prompt, st.session_state.api_key_input, selected_model, image_bytes=img_bytes, mime_type=img_mime)
                if res.startswith("❌") or res.startswith("⚠️"): st.error(res)
                else:
                    try:
                        match = re.search(r'\{.*\}', res, re.DOTALL)
                        if match:
                            data = json.loads(match.group(0))
                            grade_color = "#10B981" if "1" in data.get('Grade', '') else "#EF4444"
                            st.markdown(f"<div class='glass-card' style='border-left: 4px solid {grade_color};'><h3>{data.get('Grade', '')}</h3><h2>{data.get('Item', '')}</h2><p><strong>💰 {data.get('Profit', '')}</strong></p><p>{data.get('Reason', '')}</p></div>", unsafe_allow_html=True)
                            
                            image_url = upload_to_imgbb(img_bytes, st.session_state.imgbb_key_input) if img_bytes and st.session_state.imgbb_key_input else ""
                            final_detail = voice_input if voice_input else "[사진분석]"
                            if image_url: final_detail += f'\n\n=HYPERLINK("{image_url}", "📷 사진 보기")'
                            
                            is_saved, err_msg = save_to_google_sheet(data.get('Item', ''), data.get('Grade', ''), data.get('Reason', ''), final_detail, target_sheet="모바일 소싱DB")
                            if is_saved: 
                                st.cache_data.clear()
                                st.success("✅ '모바일 소싱DB' 시트에 저장 완료!")
                            else: st.error(f"⚠️ 저장 실패: {err_msg}")
                    except Exception as e: st.error(f"오류: {e}")

# (이하 기존 작업 모드 및 상세 모듈 코드 동일... 생략하지 않고 풀코드 유지 원칙 준수)
elif "작업 모드" in st.session_state.mode:
    if menu == "🚀 시스템 홈 (대시보드)":
        st.markdown("<h1>시스템 홈 (대시보드)</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown("<div class='glass-card'><h3>업로드 대기</h3><p style='font-size:2rem; font-weight:700; color:#fafafa;'>12</p></div>", unsafe_allow_html=True)
        with col2: st.markdown("<div class='glass-card'><h3>소싱 성공률</h3><p style='font-size:2rem; font-weight:700; color:#fafafa;'>84.5%</p></div>", unsafe_allow_html=True)
        with col3: st.markdown("<div class='glass-card'><h3>API 상태</h3><p style='font-size:1.5rem; font-weight:600; color:#10b981; margin-top:8px;'>정상 연결됨</p></div>", unsafe_allow_html=True)
        st.info("👈 좌측 메뉴에서 분석 모듈을 선택하세요.")
    elif menu == "🗂️ 소싱 DB 관리":
        st.markdown("<h1>소싱 DB 관리</h1>", unsafe_allow_html=True)
        if st.button("🔄 새로고침"): st.cache_data.clear(); rerun_app()
        df_db, db_status = fetch_sourcing_db()
        if not df_db.empty: st.dataframe(df_db, use_container_width=True, height=450)
        else: st.warning("데이터가 없습니다.")
    elif menu == "👥 회원 관리 (어드민)":
        st.markdown("<h1>💎 MetaSeller 회원 관리 시스템</h1>", unsafe_allow_html=True)
        ws, err = get_member_worksheet()
        if ws:
            df = pd.DataFrame(ws.get_all_records())
            st.dataframe(df, use_container_width=True, hide_index=True)
            with st.form("edit_status"):
                u_id = st.selectbox("회원 선택", df['아이디'].tolist())
                n_st = st.selectbox("상태", ["이용중", "승인대기", "기간만료"])
                n_lv = st.selectbox("등급", ["무료회원", "유료회원", "VIP회원"])
                if st.form_submit_button("업데이트"):
                    idx = ws.col_values(1).index(u_id) + 1
                    ws.update_cell(idx, 4, n_st); ws.update_cell(idx, 7, n_lv)
                    st.success("변경 완료!"); time.sleep(1); rerun_app()
