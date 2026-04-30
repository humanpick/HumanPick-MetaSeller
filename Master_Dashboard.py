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

# 추가된 라이브러리
try:
    from supabase import create_client, Client
except ImportError:
    pass

warnings.filterwarnings("ignore")

# --- [0. 필수 라이브러리 자동 설치] ---
def install_packages():
    required = {"pandas", "openpyxl", "PyPDF2", "gspread", "oauth2client", "Pillow", "supabase"}
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
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    from PIL import Image
except ImportError:
    st.stop()

# --- [1. 디자인 시스템 및 Supabase 초기화] ---
st.set_page_config(page_title="MetaSeller v4.0", layout="wide", initial_sidebar_state="expanded")

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_supabase()

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    .stApp { background-color: #09090b !important; }
    .glass-card { background: #121214; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 24px; margin-bottom: 16px; }
    
    /* 화이트 폼 & 블랙 텍스트 */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { background-color: #ffffff !important; border-radius: 8px !important; }
    input, select, .stTextArea textarea { color: #000000 !important; font-weight: 600 !important; }
    
    /* 버튼 스타일 */
    .stButton>button { background: #18181b !important; color: #fafafa !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; width: 100%; transition: 0.2s; }
    .stButton>button:hover { background: #8B5CF6 !important; transform: translateY(-2px); }
    
    header, footer, #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- [2. 핵심 로직: 구글 시트 (소싱용) & Supabase (회원용)] ---
def save_to_google_sheet(item_name, grade, reason, detail_data):
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key("1p2pgXtUN5ql_FcflX0WacybNPPnrq33rg1YarfsMEA0")
        current_month = datetime.now().strftime("%Y%m")
        worksheet = spreadsheet.worksheet(current_month)
        worksheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), item_name, grade, reason, detail_data])
        return True, ""
    except Exception as e: return False, str(e)

# --- [3. 사이드바 및 메뉴] ---
with st.sidebar:
    st.markdown("<h2 style='color:white;'>MetaSeller <span style='font-size:0.8rem; color:#8B5CF6;'>v4.0</span></h2>", unsafe_allow_html=True)
    menu = st.radio("메뉴", ["🚀 대시보드", "🗂️ 소싱 DB 관리", "👥 회원 관리 (Supabase)", "✍️ 카피라이팅", "📥 영상 추출"])

# --- [4. 회원 관리 화면 (Supabase 연동)] ---
if menu == "👥 회원 관리 (Supabase)":
    st.markdown("<h1>👥 회원 관리 (Real-time DB)</h1>", unsafe_allow_html=True)
    
    # 데이터 불러오기
    res = supabase.table("members").select("*").execute()
    members_df = pd.DataFrame(res.data)

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>현재 등록된 회원 (Supabase)</h3>", unsafe_allow_html=True)
    st.dataframe(members_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("add_member_supabase"):
        st.markdown("<h3>신규 회원 추가</h3>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            m_email = st.text_input("이메일")
            m_pw = st.text_input("비밀번호", type="password")
        with c2:
            m_name = st.text_input("성함")
            m_status = st.selectbox("상태", ["이용중", "승인대기", "정지"])
        
        if st.form_submit_button("Supabase에 저장"):
            if m_email and m_pw:
                supabase.table("members").insert({
                    "email": m_email, "password": m_pw, "name": m_name, "status": m_status
                }).execute()
                st.success("성공적으로 저장되었습니다!")
                time.sleep(1)
                st.rerun()

# --- [5. 기타 기존 기능들 (생략 - 기존 코드 유지)] ---
elif menu == "🚀 대시보드":
    st.markdown("<h1>대시보드</h1>", unsafe_allow_html=True)
    st.info("기존 대시보드 기능을 여기에 유지합니다.")
