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

# --- [1. 하이엔드 SaaS 디자인 시스템 적용] ---
st.set_page_config(page_title="MetaSeller v4.0", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* Global Typography & Reset */
    html, body, [class*="css"], h1, h2, h3, h4, h5, h6, p, span, div, label, input, button, select, textarea { 
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif; 
        font-feature-settings: "cv02", "cv03", "cv04", "cv11";
    }
    
    /* Hide Default Elements */
    .stDeployButton, [data-testid="stAppDeployButton"], #MainMenu, [data-testid="stToolbar"], header[data-testid="stHeader"], [data-testid="stSidebarCollapseButton"] { 
        display: none !important; 
    }

    /* Premium Dark Theme Core */
    .stApp { background-color: #09090b !important; }
    p, label, span { color: #a1a1aa !important; margin-bottom: 0 !important; }
    h1 { color: #fafafa !important; font-weight: 700 !important; font-size: 1.75rem !important; letter-spacing: -0.02em; margin-bottom: 1.5rem !important; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 1rem !important; }
    
    /* Layout Balancing (Zero-Scroll 지향 max-width 1400px) */
    .block-container {
        padding-top: 3rem !important; 
        padding-bottom: 3rem !important; 
        padding-left: 4rem !important;
        padding-right: 4rem !important;
        max-width: 1400px !important;
        margin: 0 auto;
    }
    div[data-testid="stVerticalBlock"] { gap: 1.2rem !important; }

    /* Sidebar Refinement */
    [data-testid="stSidebar"] { 
        background-color: #09090b !important; 
        border-right: 1px solid rgba(255,255,255,0.08) !important;
        padding-top: 2rem !important;
    }
    .sidebar-title { 
        color: #fafafa !important;
        font-size: 1.25rem !important; 
        font-weight: 800 !important; 
        letter-spacing: -0.5px;
        margin-bottom: 0px; 
    }
    
    /* Navigation Menu (Radio to Clean List) */
    [data-testid="stRadio"] > label { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] { gap: 4px; }
    [data-testid="stRadio"] div[role="radiogroup"] label {
        background: transparent !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 12px !important; 
        cursor: pointer; width: 100%; display: flex; align-items: center;
        font-size: 0.95rem !important; font-weight: 500 !important; color: #a1a1aa !important; 
        transition: all 0.15s ease !important;
    }
    [data-testid="stRadio"] div[role="radiogroup"] label:hover {
        background: rgba(255, 255, 255, 0.05) !important; color: #fafafa !important;
    }
    [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) { 
        background: #fafafa !important; 
        color: #09090b !important; 
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    [data-testid="stRadio"] div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] { pointer-events: none; }
    [data-testid="stRadio"] div[role="radiogroup"] label div[data-baseweb="radio"] { display: none !important; }

    /* Modern Inputs (White Form & Black Text 완벽 수정본) */
    div[data-baseweb="input"] > div, 
    div[data-baseweb="textarea"] > div, 
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important; 
        border: 1px solid rgba(255,255,255,0.15) !important; 
        border-radius: 8px !important; 
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    
    div[data-baseweb="input"]:focus-within > div, 
    div[data-baseweb="textarea"]:focus-within > div, 
    div[data-baseweb="select"]:focus-within > div {
        border-color: #8B5CF6 !important; 
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.3) !important;
    }
    
    .stTextInput input, 
    .stNumberInput input, 
    .stTextArea textarea, 
    div[data-baseweb="select"] * { 
        color: #09090b !important; 
        -webkit-text-fill-color: #09090b !important; 
        font-size: 0.95rem !important; 
        font-weight: 600 !important;
    }
    
    .stTextInput input, 
    .stNumberInput input, 
    .stTextArea textarea {
        background-color: transparent !important;
    }
    
    ::placeholder { color: #a1a1aa !important; -webkit-text-fill-color: #a1a1aa !important; font-weight: 400 !important; }
    div[data-baseweb="input"] svg, div[data-baseweb="select"] svg { color: #52525b !important; fill: #52525b !important; }
    
    ul[role="listbox"], ul[role="listbox"] * { 
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important; 
        font-weight: 600 !important; 
    }

    /* ========================================================
       Refined Buttons (줄바꿈 방지 및 핏 조절 완료)
       ======================================================== */
    .stButton>button {
        background: #18181b !important; 
        color: #fafafa !important; -webkit-text-fill-color: #fafafa !important; 
        border: 1px solid rgba(255,255,255,0.1) !important; 
        border-radius: 8px !important;
        padding: 0.5rem 0.4rem !important; /* 패딩을 약간 줄여 핏을 맞춤 */
        font-weight: 500 !important; 
        font-size: 0.85rem !important; /* 폰트 사이즈 최적화 */
        white-space: nowrap !important; /* 글자 줄바꿈 강제 방지 */
        letter-spacing: -0.3px !important;
        transition: all 0.2s ease; width: 100%;
    }
    .stButton>button:hover { background: #27272a !important; border-color: rgba(255,255,255,0.2) !important; }
    
    /* Primary Call-to-Action (Submit Buttons) */
    .stFormSubmitButton>button {
        background: #fafafa !important; 
        color: #09090b !important; -webkit-text-fill-color: #09090b !important; 
        border: none !important; 
        border-radius: 8px !important; width: 100%;
        font-weight: 600 !important; 
        white-space: nowrap !important; /* 글자 줄바꿈 강제 방지 */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stFormSubmitButton>button:hover { opacity: 0.9; transform: translateY(-1px); }
    /* ======================================================== */

    /* SaaS Dashboard Cards (Replaces Glass-cards) */
    .glass-card { 
        background: #121214; 
        border: 1px solid rgba(255, 255, 255, 0.08); 
        border-radius: 12px; 
        padding: 24px; 
        box-shadow: 0 4px 24px -8px rgba(0,0,0,0.5); 
        margin-bottom: 16px;
    }
    .glass-card h3 { font-size: 1.05rem; font-weight: 600; color: #fafafa; margin-bottom: 12px; border: none; padding: 0;}
    .glass-card p { font-size: 0.9rem; color: #a1a1aa; line-height: 1.6; margin-bottom: 0px;}
    
    /* Highlight & Data Modules */
    .highlight-box { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 24px; text-align: center; }
    .highlight-title { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: #71717a; margin-bottom: 8px; }
    .highlight-value { font-size: 2.5rem; font-weight: 700; color: #fafafa; letter-spacing: -0.02em; }
    
    /* Alert Customization */
    [data-testid="stAlert"] { background-color: transparent !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; }
    [data-testid="stAlert"] p { color: #fafafa !important; }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #09090b; }
    ::-webkit-scrollbar-thumb { background: #27272a; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #3f3f46; }
    
    /* DataFrame */
    [data-testid="stDataFrame"] { background-color: transparent !important; }
</style>
""", unsafe_allow_html=True)

# --- [2. 코어 보조 함수 (기능 완전 복원)] ---
def rerun_app():
    if hasattr(st, "rerun"): st.rerun()
    else: st.experimental_rerun()

def parse_korean_currency(val_str):
    try:
        clean_str = str(val_str).replace(',', '').replace(' ', '')
        return int(clean_str) if clean_str else 0
    except ValueError: return 0

def save_to_google_sheet(item_name, grade, reason, detail_data):
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        else:
            if not os.path.exists("credentials.json"): 
                return False, "credentials.json 키 파일이 없습니다."
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        
        client = gspread.authorize(creds)
        sheet_id = "1p2pgXtUN5ql_FcflX0WacybNPPnrq33rg1YarfsMEA0"
        spreadsheet = client.open_by_key(sheet_id)
        current_month = datetime.now().strftime("%Y%m")
        
        existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
        if current_month not in existing_sheets:
            worksheet = spreadsheet.add_worksheet(title=current_month, rows=1000, cols=5)
            worksheet.append_row(["저장 시간", "상품명/분류", "소싱 등급", "판독/요약 리포트", "원문/상세 데이터"])
        else:
            worksheet = spreadsheet.worksheet(current_month)
            
        worksheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), item_name, grade, reason, detail_data])
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

def generate_content_auto(prompt, api_key, selected_model="자동 (권장)"):
    if not api_key: return "❌ API 키가 없습니다."
    try:
        models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        res = requests.get(models_url)
        if res.status_code != 200: 
            return f"❌ API 키 인증 실패 (HTTP {res.status_code})\n\n[디버그]\n{res.text}"
        
        available_names = [m['name'].split('/')[-1] for m in res.json().get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        
        targets = ['gemini-1.5-pro', 'gemini-1.5-flash-8b', 'gemini-1.5-flash'] if selected_model == "자동 (권장)" else [selected_model]
        targets = [t for t in targets if t in available_names]
        if not targets: 
            targets = [available_names[0]] if available_names else ['gemini-1.5-flash']
        
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        last_error = ""
        
        for target in targets:
            wait_time = 2
            for attempt in range(2): 
                gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{target}:generateContent?key={api_key}"
                gen_res = requests.post(gen_url, headers=headers, json=data)
                
                if gen_res.status_code == 200: 
                    candidate = gen_res.json().get('candidates', [{}])[0]
                    if 'content' in candidate:
                        return candidate['content']['parts'][0]['text']
                    else:
                        return f"❌ AI가 보안 정책 등의 이유로 답변을 생성하지 못했습니다. (사유: {candidate.get('finishReason', '알 수 없음')})"
                elif gen_res.status_code in [503, 429]: 
                    last_error = f"{target} (트래픽 지연)"
                    time.sleep(wait_time); wait_time += 2; continue
                else: 
                    try: err_msg = gen_res.json().get('error', {}).get('message', gen_res.text)
                    except: err_msg = gen_res.text
                    last_error = f"{target} (HTTP {gen_res.status_code}: {err_msg})"
                    break 
        return f"⚠️ 서버 응답 거부 또는 실패\n\n[구글 원본 에러 메시지]\n{last_error}"
    except Exception as e: return f"❌ 통신 시스템 오류: {e}"

@st.cache_data
def extract_copywriting_materials():
    base_dir = os.path.dirname(os.path.abspath(__file__))
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

# --- [3. 시스템 마스터 로그인 로직] ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'mode' not in st.session_state: st.session_state.mode = "💻 작업 모드 (PC 분석)"

if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div class='glass-card' style='text-align:center; padding: 40px;'>
            <div style='margin-bottom: 24px;'>
                <h1 style='border:none; margin:0; padding:0; font-size:2rem; font-weight:800; letter-spacing:-1px;'>META SELLER</h1>
                <p style='color:#71717a; font-size:0.9rem; margin-top:8px;'>자율형 오토 소싱 에이전트 시스템 v4.0</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            uid = st.text_input("마스터 ID", placeholder="admin 입력")
            upw = st.text_input("비밀번호", type="password", placeholder="••••")
            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
            if st.form_submit_button("시스템 로그인 →"):
                if uid == "admin" and upw == "1234":
                    st.session_state.logged_in = True
                    rerun_app()
                else: st.error("인증 자격 증명이 올바르지 않습니다.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- [4. 사이드바 구성 및 API 영구 저장 시스템] ---
with st.sidebar:
    st.markdown("<p class='sidebar-title'>MetaSeller <span style='font-weight:400; font-size:0.9rem; color:#71717a;'>v4.0</span></p>", unsafe_allow_html=True)
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    mode_selection = st.radio("모드 선택", ["🚗 운전 모드 (음성 소싱)", "💻 작업 모드 (PC 분석)"], index=0 if "운전" in st.session_state.mode else 1)
    if mode_selection != st.session_state.mode:
        st.session_state.mode = mode_selection
        rerun_app()

    if "작업 모드" in st.session_state.mode:
        st.markdown("<div style='height: 16px;'></div><p style='font-size: 0.75rem; color: #52525b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; padding-left: 12px;'>상세 메뉴</p>", unsafe_allow_html=True)
        menu = st.radio("hidden_label", [
            "🚀 시스템 홈 (대시보드)",
            "🗂️ 소싱 DB 관리",
            "🧪 키워드 분석 (트렌드 발굴)", 
            "🛑 지재권 리스크 스캐너", 
            "🏭 공장 판별기 (도매처 검증)", 
            "💰 정밀 마진 계산기", 
            "🎯 광고 해부학 (쿠팡 최적화)",
            "✍️ 카피라이팅 기획소",
            "📥 영상 분석 추출"
        ], index=0, label_visibility="collapsed")
    else:
        menu = "운전모드"

    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    
    # 💡 [API Key 영구 보존 로직 추가]
    key_file_path = os.path.join(os.getcwd(), ".api_key")
    if "api_key_input" not in st.session_state:
        if os.path.exists(key_file_path):
            with open(key_file_path, "r", encoding="utf-8") as f:
                st.session_state.api_key_input = f.read().strip()
        else:
            st.session_state.api_key_input = ""
            
    st.markdown("<p style='font-size:0.75rem; color:#52525b; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; padding-left: 12px;'>환경 설정</p>", unsafe_allow_html=True)
    
    api_key_val = st.text_input("Gemini API Key", type="password", value=st.session_state.api_key_input, label_visibility="collapsed", placeholder="API 키를 입력하세요")
    selected_model = st.selectbox("AI 모델 선택", options=["자동 (권장)", "gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-1.5-pro"], index=0, label_visibility="collapsed")
    
    # 💡 [버튼 크기 안정화 레이아웃: 비율 조절]
    c1, c2 = st.columns([1, 1.35]) 
    with c1:
        if st.button("💾 키 저장"): 
            with open(key_file_path, "w", encoding="utf-8") as f:
                f.write(api_key_val)
            st.session_state.api_key_input = api_key_val
            st.success("저장 완료")
    with c2:
        if st.button("🚪 안전 로그아웃"): 
            st.session_state.logged_in = False
            rerun_app()

# ==========================================
# --- [5. 메인 화면: 🚗 운전 모드] ---
# ==========================================
if "운전 모드" in st.session_state.mode:
    st.markdown("<h1>🚗 운전 모드 (음성 소싱 에이전트)</h1>", unsafe_allow_html=True)
    st.info("💡 모바일 키보드의 **[마이크 🎤] 버튼**을 눌러 상품을 말해주세요. AI가 판독하여 시트로 전송합니다.")
    
    with st.form("drive_mode_form"):
        voice_input = st.text_area("🎙️ 상품 정보 입력창 (음성 입력 후 터치)", height=150, placeholder="예: 상업용 초음파 식기세척기 찾아줘. 중국가 1000위안 정도.")
        uploaded_img = st.file_uploader("📸 현장 사진 업로드 (선택사항)", type=['png', 'jpg', 'jpeg'])
        submit_voice = st.form_submit_button("🚀 즉시 분석 및 시트 저장")

    if submit_voice:
        if not st.session_state.api_key_input: 
            st.error("좌측 사이드바에 API Key를 먼저 입력하고 저장해주세요.")
        elif not voice_input and not uploaded_img: 
            st.warning("분석할 텍스트나 사진을 입력해주세요.")
        else:
            with st.spinner("AI가 데이터를 추정하고 법무 스캔을 진행 중입니다..."):
                prompt = "당신은 B2B 구매대행 전문가입니다. 운전 중인 대표님을 위해 즉시 판단하세요.\n"
                prompt += "1. 단가와 무게를 추정하고 전안법, 전파법 등 통관 여부를 검토.\n"
                prompt += "2. 아래 JSON 양식으로만 답변. 마진 금액은 반드시 콤마(,)를 찍어서 표기.\n\n"
                prompt += f"입력 내용: {voice_input}\n\n"
                prompt += "양식:\n"
                prompt += '{\n  "Item": "추정된 정확한 상품명",\n  "Grade": "1등급(즉시소싱)",\n  "Profit": "예상 순수익 150,000원",\n  "Reason": "이유 2문장 이내 요약"\n}'
                
                res = generate_content_auto(prompt, st.session_state.api_key_input, selected_model)
                if res.startswith("❌") or res.startswith("⚠️"):
                    st.error(res)
                else:
                    try:
                        match = re.search(r'\{.*\}', res, re.DOTALL)
                        if match:
                            data = json.loads(match.group(0))
                            grade_color = "#10B981" if "1" in data.get('Grade', '') or "2" in data.get('Grade', '') else "#F59E0B" if "3" in data.get('Grade', '') else "#EF4444"
                            
                            st.markdown(f"""
                            <div class='glass-card' style='border-left: 4px solid {grade_color};'>
                                <h3 style='color:{grade_color}; margin-top:0;'>{data.get('Grade', '')}</h3>
                                <h2 style='margin-bottom:12px; color:#fafafa; border:none; padding:0;'>{data.get('Item', '')}</h2>
                                <p style='font-size: 1.1rem; color:#fafafa;'><strong>💰 {data.get('Profit', '')}</strong></p>
                                <p style='color:#a1a1aa; line-height:1.6; margin-top:8px;'><strong>판독 리포트:</strong> {data.get('Reason', '')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            is_saved, err_msg = save_to_google_sheet(data.get('Item', ''), data.get('Grade', ''), data.get('Reason', ''), voice_input)
                            if is_saved: 
                                st.cache_data.clear() 
                                st.success("✅ 공유된 [구글 시트]에 투두 리스트가 추가되었습니다!")
                            else: 
                                st.error(f"⚠️ 구글 시트 저장 실패: {err_msg}")
                        else: st.error(f"데이터 파싱 실패. 원본 응답:\n{res}")
                    except Exception as e: st.error(f"오류 발생: {e}\n\n원본 응답:\n{res}")

# ==========================================
# --- [6. 메인 화면: 💻 작업 모드] ---
# ==========================================
elif "작업 모드" in st.session_state.mode:
    
    if menu == "🚀 시스템 홈 (대시보드)":
        st.markdown("<h1>시스템 홈 (대시보드)</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown("<div class='glass-card'><h3>업로드 대기</h3><p style='font-size:2rem; font-weight:700; color:#fafafa;'>12</p></div>", unsafe_allow_html=True)
        with col2: st.markdown("<div class='glass-card'><h3>소싱 성공률</h3><p style='font-size:2rem; font-weight:700; color:#fafafa;'>84.5%</p></div>", unsafe_allow_html=True)
        with col3: st.markdown("<div class='glass-card'><h3>API 상태</h3><p style='font-size:1.5rem; font-weight:600; color:#10b981; margin-top:8px;'>정상 연결됨</p></div>", unsafe_allow_html=True)
        st.info("👈 좌측 메뉴에서 원하시는 분석 모듈을 선택하여 작업을 시작하세요.")

    elif menu == "🗂️ 소싱 DB 관리":
        st.markdown("<h1>소싱 DB 관리</h1>", unsafe_allow_html=True)
        
        col_db1, col_db2 = st.columns([4, 1])
        with col_db1:
            st.info("💡 각 모듈에서 저장한 데이터를 실시간으로 확인하고 관리합니다.")
        with col_db2:
            if st.button("🔄 새로고침", use_container_width=True):
                st.cache_data.clear() 
                rerun_app()

        with st.spinner("소싱 DB 데이터를 불러오는 중입니다..."):
            df_db, db_status = fetch_sourcing_db()
            
        st.markdown(f"<p style='color:#a1a1aa; font-size:0.85rem; margin-bottom:12px;'>상태: {db_status}</p>", unsafe_allow_html=True)
        
        if not df_db.empty:
            st.dataframe(df_db, use_container_width=True, height=450)
        else:
            st.warning("아직 저장된 소싱 데이터가 없습니다.")

        st.markdown("""
        <div style="margin-top: 16px;">
            <a href="https://docs.google.com/spreadsheets/d/1p2pgXtUN5ql_FcflX0WacybNPPnrq33rg1YarfsMEA0/edit?usp=sharing" target="_blank" style="display:block; text-align:center; background: #fafafa; color:#09090b; padding:12px; border-radius:8px; font-weight:600; text-decoration:none; font-size:0.95rem; transition: 0.2s;">
                📝 구글 시트 원본 열람 및 직접 수정하기
            </a>
        </div>
        """, unsafe_allow_html=True)

    elif menu == "🧪 키워드 분석 (트렌드 발굴)":
        st.markdown("<h1>트렌드 키워드 분석 & 번역</h1>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            st.markdown("""
            <div class='glass-card'>
                <h3>📊 1. 네이버 데이터랩 검색</h3>
                <p>쇼핑인사이트에서 현재 뜨고 있는 키워드를 발굴하세요.</p>
                <a href="https://datalab.naver.com/shoppingInsight/sCategory.naver" target="_blank" style="display:block; text-align:center; background: transparent; border: 1px solid #10b981; color:#10b981; padding:10px; border-radius:8px; font-weight:600; text-decoration:none; font-size:0.95rem; margin-top:16px;">
                    📈 네이버 데이터랩 열기
                </a>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("<div class='glass-card' style='padding-bottom:12px;'><h3>🇨🇳 2. 황금 키워드 번역기</h3><p>한국어 상품명을 입력하면 전략 키워드로 변환합니다.</p></div>", unsafe_allow_html=True)
            with st.form("form_kw", clear_on_submit=False):
                keyword_input_val = st.text_input("한국어 상품명 입력:", placeholder="예: 여름 원피스", label_visibility="collapsed")
                btn_translate = st.form_submit_button("✨ 황금 키워드 연성", use_container_width=True)

        if btn_translate:
            if not st.session_state.api_key_input: st.error("사이드바에 API 키를 저장해 주세요.")
            elif not keyword_input_val: st.warning("번역할 한국어 상품명을 입력해 주세요.")
            else:
                with st.spinner("맞춤형 황금 키워드를 연성 중..."):
                    prompt = f"당신은 타오바오 전문가입니다. 한국어 상품명 '{keyword_input_val}'을 타오바오 소싱용으로 번역하세요.\n"
                    prompt += "3가지 소싱 전략 검색어를 만드세요: 1.디자인/감성 2.실용성/기능 3.공장직영/가성비\n"
                    prompt += "형식:\n[TRANSLATION]기본키워드\n[STRATEGY_1]전략1\n[STRATEGY_2]전략2\n[STRATEGY_3]전략3"
                    
                    res = generate_content_auto(prompt, st.session_state.api_key_input, selected_model)
                    st.session_state.ai_kw_res = res
                    st.session_state.ai_kw_input = keyword_input_val

        if 'ai_kw_res' in st.session_state:
            res = st.session_state.ai_kw_res
            keyword_input_val = st.session_state.ai_kw_input
            
            if res.startswith("❌") or res.startswith("⚠️"): 
                st.error(res)
            else:
                trans, s1, s2, s3 = "", "", "", ""
                for line in res.replace('**', '').split('\n'):
                    line = line.strip()
                    if line.startswith('[TRANSLATION]'): trans = line.replace('[TRANSLATION]', '').strip()
                    elif line.startswith('[STRATEGY_1]'): s1 = line.replace('[STRATEGY_1]', '').strip()
                    elif line.startswith('[STRATEGY_2]'): s2 = line.replace('[STRATEGY_2]', '').strip()
                    elif line.startswith('[STRATEGY_3]'): s3 = line.replace('[STRATEGY_3]', '').strip()

                st.success(f"✅ 연성 완료! (중국어 기본 번역: **{trans}**)")
                strategies = [("🎨 디자인/감성", s1), ("⚙️ 실용성/스펙", s2), ("🏭 공장/가성비", s3)]
                db_save_text = f"[기본 번역] {trans} | "
                
                kw_cols = st.columns(3)
                for i, (name, search_query) in enumerate(strategies):
                    if not search_query: continue
                    link = f"https://s.taobao.com/search?q={quote(search_query)}"
                    db_save_text += f"{name.split(' ')[1]}: {search_query} ({link}) | "
                    
                    with kw_cols[i]:
                        st.markdown(f"""
                        <div class='glass-card' style='text-align:center;'>
                            <span style='color:#a1a1aa; font-weight:600; font-size:0.85rem; display:block; margin-bottom:8px;'>{name} 전략</span>
                            <span style='font-size:1.1rem; color:#fafafa; font-weight:700; display:block; margin-bottom:16px;'>{search_query}</span>
                            <a href="{link}" target="_blank" style="text-decoration:none; background: #18181b; border: 1px solid rgba(255,255,255,0.1); color:#fafafa; padding:8px 12px; border-radius:6px; font-weight:500; font-size:0.9rem; display:block; transition: 0.2s;">
                                🔍 타오바오 검색
                            </a>
                        </div>
                        """, unsafe_allow_html=True)

                if st.button("💾 이 키워드 데이터를 소싱 DB에 즉시 저장", use_container_width=True, key="save_kw_db"):
                    with st.spinner("구글 시트로 전송 중..."):
                        is_saved, err_msg = save_to_google_sheet(
                            f"키워드: {keyword_input_val}", 
                            "키워드분석", 
                            f"기본 번역: {trans}", 
                            db_save_text
                        )
                        if is_saved: 
                            st.cache_data.clear()
                            st.success("✅ 소싱 DB에 황금 키워드가 성공적으로 저장되었습니다!")
                        else:
                            st.error(f"⚠️ 구글 시트 저장 실패: {err_msg}")

    elif menu == "🛑 지재권 리스크 스캐너":
        st.markdown("<h1>지재권 리스크 스캐너</h1>", unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2, gap="medium")
        with col_a:
            st.markdown("<div class='glass-card'><h3>🚨 로컬 DB 금칙어 스캔</h3><p>폴더 내 엑셀/CSV 데이터를 바탕으로 금칙어를 1초 만에 걸러냅니다.</p></div>", unsafe_allow_html=True)
            with st.form("form_db_scan", clear_on_submit=False):
                keyword_input_local = st.text_input("상품명 검사 (DB 전용):", placeholder="예: 쓰리잘비", label_visibility="collapsed")
                btn_local = st.form_submit_button("🚨 위험 단어 스캔 시작", use_container_width=True)
            
            if btn_local:
                current_dir = os.getcwd()
                db_files = [f for f in os.listdir(current_dir) if f.lower().endswith(('.csv', '.xlsx', '.xls')) and not f.startswith("~$")]
                if not db_files: 
                    st.error("❌ 현재 폴더에 엑셀/CSV DB 파일이 없습니다.")
                elif keyword_input_local:
                    db_source = db_files[0]
                    file_path = os.path.join(current_dir, db_source)
                    try:
                        if str(db_source).endswith(('.xlsx', '.xls')): df = pd.read_excel(file_path)
                        else:
                            try: df = pd.read_csv(file_path, encoding='utf-8-sig', on_bad_lines='skip')
                            except:
                                try: df = pd.read_csv(file_path, encoding='cp949', on_bad_lines='skip')
                                except: df = pd.read_csv(file_path, encoding='euc-kr', on_bad_lines='skip')
                        found = [val for col in df.columns for val in df[col].astype(str) if len(val.strip()) >= 2 and keyword_input_local.lower().replace(" ","") in val.lower().replace(" ","")]
                        if found: st.error(f"🚨 [적발] DB 금칙어 발견: {', '.join(list(set(found)))}")
                        else: st.success(f"✅ '{keyword_input_local}' (은)는 안전합니다.")
                    except Exception as e: st.error(f"파일 오류: {e}")
                else: st.warning("검사할 단어를 입력하세요.")

        with col_b:
            st.markdown("<div class='glass-card'><h3>🛡️ AI 법무팀 정밀 진단</h3><p>지재권, 인증(KC), 수입금지 여부를 심층 진단합니다.</p></div>", unsafe_allow_html=True)
            with st.form("form_ai_scan", clear_on_submit=False):
                keyword_input_ai = st.text_area("상품 텍스트 또는 상세 설명 입력:", placeholder="예: 220v 중국산 상업용 제빙기", height=70, label_visibility="collapsed")
                btn_ai = st.form_submit_button("🛡️ AI 심층 진단 실행", use_container_width=True)
            
            if btn_ai:
                if not st.session_state.api_key_input: st.warning("API 키를 저장하세요.")
                elif not keyword_input_ai: st.warning("상품 정보를 입력하세요.")
                else:
                    with st.spinner("AI 관세사 분석 중..."):
                        prompt = "이커머스 전문 관세사/변호사로서 통관 리스크 및 법적 리스크를 진단하세요.\n"
                        prompt += "결과는 반드시 JSON 형식으로만 출력하세요.\n"
                        prompt += '{\n  "Level": "안전", \n  "IP_Risk": "결과(1문장)",\n  "Cert_Risk": "결과(1문장)",\n  "Ban_Risk": "결과(1문장)",\n  "Final_Action": "최종 판결(1문장)"\n}\n'
                        prompt += f"[데이터]: {keyword_input_ai}"
                        
                        res = generate_content_auto(prompt, st.session_state.api_key_input, selected_model)
                        st.session_state.ai_ip_res = res
                        st.session_state.ai_ip_item = keyword_input_ai

            if 'ai_ip_res' in st.session_state:
                res = st.session_state.ai_ip_res
                item_val = st.session_state.ai_ip_item
                
                if res.startswith("❌") or res.startswith("⚠️"): st.error(res)
                else:
                    try:
                        match = re.search(r'\{.*\}', res, re.DOTALL)
                        if match:
                            data = json.loads(match.group(0))
                            level = data.get("Level", "위험")
                            border_color, text_color = ("#10B981", "#10B981") if level == "안전" else (("#F59E0B", "#F59E0B") if level == "주의" else ("#EF4444", "#EF4444"))
                            
                            st.markdown(f"""
                            <div class='glass-card' style='border-left: 4px solid {border_color};'>
                                <h3 style='color:{text_color}; margin-top:0; margin-bottom:12px;'>🚨 최종 등급: {level}</h3>
                                <div style='font-size:0.9rem; margin-bottom:6px; color:#a1a1aa;'><span style='color:#fafafa;'>⚖️ 지재권:</span> {data.get('IP_Risk', '')}</div>
                                <div style='font-size:0.9rem; margin-bottom:6px; color:#a1a1aa;'><span style='color:#fafafa;'>📑 인증/규제:</span> {data.get('Cert_Risk', '')}</div>
                                <div style='font-size:0.9rem; margin-bottom:12px; color:#a1a1aa;'><span style='color:#fafafa;'>🚫 수입금지:</span> {data.get('Ban_Risk', '')}</div>
                                <div style='background: rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; text-align:center;'>
                                    <span style='color:{text_color}; font-weight:600; font-size:0.95rem;'>👨‍⚖️ {data.get('Final_Action', '')}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("💾 진단 결과를 소싱 DB에 즉시 저장", use_container_width=True, key="save_ip_db"):
                                with st.spinner("전송 중..."):
                                    is_saved, err_msg = save_to_google_sheet(
                                        item_val, f"법무진단: {level}", data.get('Final_Action', ''), 
                                        f"지재권: {data.get('IP_Risk','')} | 인증: {data.get('Cert_Risk','')}"
                                    )
                                    if is_saved: 
                                        st.cache_data.clear()
                                        st.success("✅ DB 저장 완료!")
                                    else: st.error(f"⚠️ 실패: {err_msg}")
                        else: st.error("파싱 실패.")
                    except Exception as e: st.error(f"오류: {e}")

    elif menu == "🏭 공장 판별기 (도매처 검증)":
        st.markdown("<h1>타오바오 공장 판별기</h1>", unsafe_allow_html=True)
        col1, col2 = st.columns([1.2, 1], gap="medium")
        with col1:
            st.markdown("<div class='glass-card'><h3>🏭 판매자 정보 입력</h3></div>", unsafe_allow_html=True)
            p = st.selectbox("플랫폼:", ("타오바오 / 1688", "티몰 (Tmall)"), index=0)
            l = st.selectbox("등급:", ("하트", "다이아몬드", "파란왕관", "황금왕관"), index=1)
            y = st.number_input("업력 (년):", min_value=1, value=2)
            i = st.selectbox("지표 (DSR 등):", ("빨간색 (우수)", "섞임 (보통)", "초록색 (위험)"), index=1)
            g = st.checkbox("🏅 금메달 판매자")
            
        score = (20 if p=="티몰 (Tmall)" else 0) + {"하트":0, "다이아몬드":10, "파란왕관":25, "황금왕관":30}[l] + (25 if y>=6 else (15 if y>=3 else 0)) + {"빨간색 (우수)":30, "섞임 (보통)":10, "초록색 (위험)":-20}[i] + (15 if g else 0)
        score = min(score, 100)
        with col2:
            res_t, t_c = ("✅ 즉시 소싱", "#10B981") if score>=80 else (("⚠️ 주의 필요", "#F59E0B") if score>=50 else ("❌ 소싱 금지", "#EF4444"))
            st.markdown(f"""
            <div class='glass-card' style='text-align:center; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items:center; min-height:300px;'>
                <p style='font-weight:600; margin-bottom:12px; color:#a1a1aa; font-size:1rem; text-transform:uppercase; letter-spacing:0.05em;'>신뢰도 점수</p>
                <h2 style='color:{t_c}; font-size:4.5rem; margin:0; font-weight:800; line-height:1; border:none;'>{score}<span style='font-size:1.5rem;'>점</span></h2>
                <h3 style='color:{t_c}; margin-top:16px; font-size:1.5rem; font-weight:600;'>{res_t}</h3>
            </div>
            """, unsafe_allow_html=True)

    elif menu == "💰 정밀 마진 계산기":
        st.markdown("<h1>정밀 마진 계산기</h1>", unsafe_allow_html=True)
        
        col_in, col_res = st.columns([1.2, 1], gap="large")
        with col_in:
            st.markdown("<div class='glass-card'><h3>📝 상품 및 물류 스펙</h3>", unsafe_allow_html=True)
            item_name = st.text_input("소싱 상품명 (셀러픽 업로드용):", value="상업용 대용량 제빙기 50kg")
            
            c_p1, c_p2 = st.columns(2)
            with c_p1: 
                cny_price = st.number_input("중국 원가 (¥)", value=50.0, step=1.0)
                exchange_rate = st.number_input("현재 환율 (원)", value=195.0, step=1.0)
            with c_p2: 
                cny_shipping = st.number_input("중국 내 배송비 (¥)", value=0.0, step=1.0)
                apply_tax = st.checkbox("🚨 관부가세 적용 ($150 초과)")
                
            c_w1, c_w2, c_w3, c_w4 = st.columns(4)
            with c_w1: weight = st.number_input("무게 (kg)", value=2.0, step=0.5)
            with c_w2: width = st.number_input("가로 (cm)", value=30.0, step=1.0)
            with c_w3: length = st.number_input("세로 (cm)", value=30.0, step=1.0)
            with c_w4: height = st.number_input("높이 (cm)", value=30.0, step=1.0)
                
            c_s1, c_s2 = st.columns(2)
            with c_s1: sell_price = st.number_input("국내 판매가 (₩)", value=35000.0, step=1000.0)
            with c_s2: market_fee_rate = st.number_input("마켓 수수료율 (%)", value=13.0, step=0.1)
            st.markdown("</div>", unsafe_allow_html=True)

        if weight <= 0.5: base_shipping = 4300
        else: base_shipping = 4950 + math.ceil(max(0, weight - 1) * 2) * 600

        max_side = max(width, length, height)
        sum_sides = width + length + height
        is_kd = (weight >= 20) or (max_side >= 100) or (sum_sides >= 160)

        domestic_fee = 0
        delivery_type = "CJ대한통운"
        delivery_color = "#38BDF8" 
        
        if is_kd:
            delivery_type = "경동화물(이관)"
            delivery_color = "#F87171" 
            vol_fee = 3000 + max(0, math.ceil(((width * length * height) - 20000)/10000) * 500)
            weight_fee = 6000 if weight <= 20 else weight * 350
            domestic_fee = math.ceil(max(vol_fee, weight_fee) * 1.22)
        else:
            if sum_sides > 120: domestic_fee = 4000
            elif sum_sides > 100: domestic_fee = 2000

        platform_fee = sell_price * (market_fee_rate / 100)
        cost_krw = (cny_price + cny_shipping) * exchange_rate
        tax = (cost_krw + base_shipping) * 0.18 if apply_tax else 0
        total_cost = cost_krw + base_shipping + domestic_fee + platform_fee + tax
        net_profit = sell_price - total_cost
        margin_rate = (net_profit / sell_price) * 100 if sell_price > 0 else 0
        profit_color = "#10B981" if net_profit > 0 else "#EF4444"

        with col_res:
            st.markdown(f"""
            <div class='glass-card'>
                <h3 style='margin-bottom:20px;'>📊 재무 분석 (예상 비용)</h3>
                <div style='display:flex; justify-content:space-between; margin-bottom:12px;'><span style='color:#a1a1aa;'>배송사</span><strong style='color:{delivery_color};'>{delivery_type}</strong></div>
                <div style='display:flex; justify-content:space-between; margin-bottom:12px;'><span style='color:#a1a1aa;'>기본 해운비</span><strong style='color:#fafafa;'>{int(base_shipping):,} 원</strong></div>
                <div style='display:flex; justify-content:space-between; margin-bottom:12px;'><span style='color:#a1a1aa;'>국내 추가 배송비</span><strong style='color:#fafafa;'>{int(domestic_fee):,} 원</strong></div>
                <div style='display:flex; justify-content:space-between; margin-bottom:16px;'><span style='color:#a1a1aa;'>관부가세</span><strong style='color:#fafafa;'>{int(tax):,} 원</strong></div>
                <div style='display:flex; justify-content:space-between; font-size:1.1rem; border-top:1px solid rgba(255,255,255,0.1); padding-top:16px;'><span style='color:#fafafa;'>총 원가</span><strong style='color:#EF4444;'>{int(total_cost):,} 원</strong></div>
            </div>
            <div class='highlight-box'>
                <div class='highlight-title'>예상 순수익</div>
                <div class='highlight-value' style='color:{profit_color};'>{int(net_profit):,} 원</div>
                <div style='color:#a1a1aa; font-size:1rem; margin-top:4px;'>(마진율: <span style='color:{profit_color}; font-weight:600;'>{margin_rate:.1f}%</span>)</div>
            </div>
            """, unsafe_allow_html=True)
            
            df = pd.DataFrame([{"상품명": item_name, "판매가": int(sell_price), "원가(위안)": int(cny_price), "원가(원)": int(total_cost - platform_fee), "재고수량": 999, "배송비": 0, "순수익": int(net_profit), "마진율(%)": round(margin_rate, 1)}])
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False)
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                st.download_button("📥 엑셀 다운로드", data=output.getvalue(), file_name=f"SellerPick_{item_name[:5]}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with c_btn2:
                if st.button("💾 DB 즉시 저장", use_container_width=True, key="save_margin_db"):
                    with st.spinner("전송 중..."):
                        is_saved, err_msg = save_to_google_sheet(item_name, "마진분석", f"마진율 {margin_rate:.1f}% ({int(net_profit):,}원)", f"원가 {int(total_cost):,}원")
                        if is_saved: 
                            st.cache_data.clear()
                            st.success("✅ 저장 완료!")
                        else: st.error(f"⚠️ 실패: {err_msg}")

    elif menu == "🎯 광고 해부학 (쿠팡 최적화)":
        st.markdown("<h1>광고 해부학 (쿠팡 최적화)</h1>", unsafe_allow_html=True)
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1: selling_price_str = st.text_input("판매가 (원)", value="25,000")
        with col_m2: cost_price_str = st.text_input("원가+배송비 (원)", value="8,000")
        with col_m3: fulfillment_fee_str = st.text_input("입출고 수수료 (원)", value="3,650")
        with col_m4: commission_rate = st.number_input("판매 수수료 (%)", min_value=0.0, value=11.55, step=0.1) 

        selling_price = parse_korean_currency(selling_price_str)
        cost_price = parse_korean_currency(cost_price_str)
        fulfillment_fee = parse_korean_currency(fulfillment_fee_str)
        commission_cost = int(selling_price * (commission_rate / 100))
        net_margin = selling_price - (cost_price + fulfillment_fee + commission_cost)
        target_roas = 0 if net_margin <= 0 else round((selling_price / net_margin) * 100, 2)
        
        st.markdown(f"""
        <div class='glass-card' style='display:flex; justify-content:space-around; padding:20px;'>
            <div style='text-align:center;'><span style='color:#a1a1aa; font-size:0.9rem; text-transform:uppercase;'>예상 마진</span><br><strong style='color:{"#10B981" if net_margin>0 else "#EF4444"}; font-size:1.5rem;'>{net_margin:,} 원</strong></div>
            <div style='text-align:center;'><span style='color:#a1a1aa; font-size:0.9rem; text-transform:uppercase;'>BEP ROAS (본전 마지노선)</span><br><strong style='color:#FBBF24; font-size:1.5rem;'>{target_roas:,} %</strong></div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("쿠팡 '검색어 리포트' 엑셀/CSV 업로드", type=["csv", "xlsx"])

        if uploaded_file is not None:
            try:
                with st.spinner("해부 중..."):
                    if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
                    else: df = pd.read_excel(uploaded_file)
                
                cols = df.columns
                kw_col = next((c for c in cols if '키워드' in c or '검색어' in c), None)
                spend_col = next((c for c in cols if '광고비' in c or '비용' in c), None)
                conv_col = next((c for c in cols if '전환수' in c or '주문수' in c), None)
                sales_col = next((c for c in cols if '매출' in c or '전환액' in c), None)
                click_col = next((c for c in cols if '클릭' in c), None)

                if not all([kw_col, spend_col, conv_col, sales_col, click_col]): st.error("🚨 엑셀/CSV 형식이 올바르지 않습니다.")
                else:
                    for col in [spend_col, conv_col, sales_col, click_col]:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

                    df['ROAS'] = (df[sales_col] / df[spend_col] * 100).fillna(0).round(2)
                    tab1, tab2, tab3 = st.tabs(["🔥 출혈 키워드", "⭐ 효자 키워드", "🤖 AI 진단 리포트"])
                    
                    with tab1:
                        bleed_df = df[(df[click_col] >= 10) & (df[conv_col] == 0) & (df[spend_col] > 0)].sort_values(by=spend_col, ascending=False)
                        st.dataframe(bleed_df[[kw_col, click_col, spend_col, conv_col]], use_container_width=True, height=250)

                    with tab2:
                        good_df = df[(df['ROAS'] >= target_roas) & (df[conv_col] >= 2)].sort_values(by='ROAS', ascending=False)
                        st.dataframe(good_df[[kw_col, spend_col, sales_col, 'ROAS', conv_col]], use_container_width=True, height=250)

                    with tab3:
                        if st.button("✨ 핵심 요약본 AI 분석", use_container_width=True):
                            if not st.session_state.api_key_input: st.error("API 키를 저장해주세요.")
                            else:
                                with st.spinner("광고 리포트를 분석 중..."):
                                    top_keywords = df.nlargest(3, spend_col)[[kw_col, spend_col, 'ROAS']].to_dict('records')
                                    prompt = f"쿠팡 광고 개선 플랜 3가지.\n목표 ROAS: {target_roas}%, 비용Top3: {top_keywords}"
                                    st.success(generate_content_auto(prompt, st.session_state.api_key_input, selected_model), icon="🎯")
            except Exception as e: st.error(f"오류: {e}")

    elif menu == "✍️ 카피라이팅 기획소":
        st.markdown("<h1>실전 카피라이팅 기획소</h1>", unsafe_allow_html=True)
        
        col_copy1, col_copy2 = st.columns(2, gap="medium")
        with col_copy1:
            st.markdown("<div class='glass-card'><h3>📚 1. 비법서 기반 카피 연성</h3></div>", unsafe_allow_html=True)
            ref_text, file_list, folder_path = extract_copywriting_materials()
            
            with st.form("form_copy_extract", clear_on_submit=False):
                product_desc = st.text_area("✨ 상품 특징 입력:", placeholder="예: 직장인용 거북목 예방 메모리폼 베개", height=100, key="c1")
                btn_extract = st.form_submit_button("🚀 매력적인 카피 추출", use_container_width=True)

        with col_copy2:
            st.markdown("<div class='glass-card'><h3>🕵️ 2. 경쟁사 마케팅 전략 해부</h3></div>", unsafe_allow_html=True)
            with st.form("form_copy_strategy", clear_on_submit=False):
                v_desc = st.text_area("🎥 상세페이지 문구:", height=45, key="c2")
                c_data = st.text_area("💬 반응/댓글 데이터:", height=45, key="c3")
                btn_strategy = st.form_submit_button("✨ 필승 소구점 도출", use_container_width=True)

        if btn_extract:
            if not st.session_state.api_key_input: st.error("API 키를 저장해주세요.")
            elif not product_desc: st.warning("상품의 특징을 입력해주세요.")
            else:
                with st.spinner("카피라이팅을 기획 중입니다..."):
                    res = generate_content_auto(f"자료 기반 카피 제안. 자료:{ref_text[:2000]} 상품:{product_desc} 출력: 1.후킹멘트 2.상품명 3.인트로", st.session_state.api_key_input, selected_model)
                    st.success(res)

        if btn_strategy:
            if not st.session_state.api_key_input: st.error("API 키를 저장해주세요.")
            elif not v_desc and not c_data: st.warning("분석할 데이터를 입력해주세요.")
            else:
                with st.spinner("경쟁사 전략을 역추적 중입니다..."): 
                    res = generate_content_auto(f"경쟁사 분석 필승 소구점 3가지 도출. 스크립트:{v_desc} 댓글:{c_data}", st.session_state.api_key_input, selected_model)
                    st.success(res)

    elif menu == "📥 영상 분석 추출":
        st.markdown("<h1>영상 분석 및 워터마크 추출</h1>", unsafe_allow_html=True)
        col_ext1, col_ext2 = st.columns(2, gap="medium")
        
        with col_ext1:
            st.markdown("<div class='glass-card'><h3>🔍 1. 숏폼 리서치 퀵 링크</h3></div>", unsafe_allow_html=True)
            with st.form("form_media_search", clear_on_submit=False):
                short_query = st.text_input("검색어 입력:", placeholder="예: 여름 원피스", label_visibility="collapsed")
                auto_translate = st.checkbox("🇨🇳 도유인 검색 시 중국어 자동 번역", value=True)
                
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                cd, ct, cy = st.columns(3, gap="small"); cr, cn, ce = st.columns(3, gap="small")
                with cd: btn_dy = st.form_submit_button("🇨🇳 도유인", use_container_width=True)
                with ct: btn_tt = st.form_submit_button("🎵 틱톡", use_container_width=True)
                with cy: btn_yt = st.form_submit_button("▶️ 숏츠", use_container_width=True)
                with cr: btn_ig = st.form_submit_button("📱 릴스", use_container_width=True)
                with cn: btn_nv = st.form_submit_button("🟢 클립", use_container_width=True)

            if btn_dy:
                q = short_query
                if short_query and auto_translate and st.session_state.api_key_input:
                    cn_res = generate_content_auto(f"'{short_query}'를 중국어로 번역해. 단어 1개.", st.session_state.api_key_input, selected_model).strip()
                    if not cn_res.startswith("❌"): q = cn_res
                webbrowser.open_new_tab(f"https://www.douyin.com/search/{quote(q)}" if short_query else "https://www.douyin.com/")
            if btn_tt: webbrowser.open_new_tab(f"https://www.tiktok.com/search?q={quote(short_query)}" if short_query else "https://www.tiktok.com/explore")
            if btn_yt: webbrowser.open_new_tab(f"https://www.youtube.com/results?search_query={quote(short_query)}+shorts" if short_query else "https://www.youtube.com/shorts/")
            if btn_ig: webbrowser.open_new_tab(f"https://www.instagram.com/explore/search/keyword/?q={quote(short_query)}" if short_query else "https://www.instagram.com/reels/")
            if btn_nv: webbrowser.open_new_tab(f"https://search.naver.com/search.naver?query={quote(short_query)}&where=video" if short_query else "https://tv.naver.com/r")

        with col_ext2:
            st.markdown("<div class='glass-card'><h3>📥 2. 워터마크 제거 전용 다운로더</h3></div>", unsafe_allow_html=True)
            if st.button("🚀 🇨🇳 도유인 전용 다운로더 (dlpanda)", use_container_width=True): webbrowser.open_new_tab("https://dlpanda.com/ko")
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 🎵 틱톡 전용 다운로더 (snaptik)", use_container_width=True): webbrowser.open_new_tab("https://snaptik.app/ko")