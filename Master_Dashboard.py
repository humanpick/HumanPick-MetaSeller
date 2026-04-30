import streamlit as st
import os
import requests 
import warnings
import pandas as pd
import time
import math
import json
import re
from datetime import datetime
import webbrowser
from urllib.parse import quote 
from io import BytesIO

warnings.filterwarnings("ignore")

# --- [0. 필수 라이브러리 체크 (클라우드 환경)] ---
# requirements.txt를 통해 설치되도록 자동 설치 코드를 제거했습니다.
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    from supabase import create_client, Client
except ImportError:
    st.error("🚨 서버에서 필수 부품(Supabase 등)을 조립 중입니다. 약 1~2분 뒤에 화면을 새로고침(F5) 해주세요!")
    st.stop()

# --- [1. 디자인 시스템 (Humanpick v1.0) & 모바일 에러 픽스] ---
st.set_page_config(page_title="MetaSeller v4.0", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    * { font-family: 'Pretendard', sans-serif !important; }
    .stApp { background-color: #0B1120 !important; } /* Humanpick 네이비 배경 */
    
    /* 🚨 모바일 햄버거 버튼 살리기: 상단바 배경 투명, 쓸데없는 버튼만 제거 */
    header[data-testid="stHeader"] { background: transparent !important; }
    #MainMenu, footer, [data-testid="stAppDeployButton"], .stDeployButton { display: none !important; }
    
    /* 모바일 햄버거 버튼 색상 포인트 (퍼플) */
    button[kind="header"] { color: #8B5CF6 !important; }

    /* 글래스 카드 룩 */
    .glass-card { 
        background: rgba(255, 255, 255, 0.05); 
        backdrop-filter: blur(12px); 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        border-radius: 12px; 
        padding: 24px; 
        margin-bottom: 16px; 
        box-shadow: 0 4px 24px -8px rgba(0,0,0,0.5); 
    }
    .glass-card h3 { color: #fafafa; margin-bottom: 12px; }
    
    /* 화이트 폼 & 블랙 텍스트 */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { background-color: #ffffff !important; border-radius: 8px !important; }
    input, select, .stTextArea textarea { color: #000000 !important; font-weight: 600 !important; }
    
    /* 버튼 스타일 (퍼플/인디고 그라데이션) */
    .stButton>button { 
        background: linear-gradient(90deg, #8B5CF6, #EC4899) !important; 
        color: white !important; 
        border: none !important; 
        border-radius: 8px !important; 
        width: 100%; 
        transition: transform 0.2s; 
        font-weight: bold;
    }
    .stButton>button:hover { transform: translateY(-3px); box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4); }
    
    /* DataFrame 투명화 */
    [data-testid="stDataFrame"] { background-color: transparent !important; }
</style>
""", unsafe_allow_html=True)

# --- [2. 데이터베이스 연동 (Supabase & Google Sheets)] ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        return None

supabase = init_supabase()

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

# --- [3. 사이드바 구성] ---
with st.sidebar:
    st.markdown("<h2 style='color:white;'>MetaSeller <span style='font-size:0.8rem; color:#8B5CF6;'>v4.0</span></h2>", unsafe_allow_html=True)
    menu = st.radio("메뉴", [
        "🚀 대시보드", 
        "🗂️ 소싱 DB 관리", 
        "👥 회원 관리 (Supabase)", 
        "💰 정밀 마진 계산기",
        "✍️ 카피라이팅 기획소", 
        "📥 영상 분석 추출"
    ])

# ==========================================
# --- [4. 메인 화면 렌더링 로직] ---
# ==========================================

if menu == "🚀 대시보드":
    st.markdown("<h1>🚀 시스템 홈 (대시보드)</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown("<div class='glass-card'><h3>업로드 대기</h3><p style='font-size:2rem; font-weight:700; color:#fafafa;'>12</p></div>", unsafe_allow_html=True)
    with col2: st.markdown("<div class='glass-card'><h3>소싱 성공률</h3><p style='font-size:2rem; font-weight:700; color:#fafafa;'>84.5%</p></div>", unsafe_allow_html=True)
    with col3: st.markdown("<div class='glass-card'><h3>DB 상태</h3><p style='font-size:1.5rem; font-weight:600; color:#10b981; margin-top:8px;'>Supabase Active</p></div>", unsafe_allow_html=True)
    st.info("👈 좌측 햄버거 메뉴(☰)에서 원하시는 분석 모듈을 선택하여 작업을 시작하세요.")

elif menu == "👥 회원 관리 (Supabase)":
    st.markdown("<h1>👥 💎 MetaSeller 회원 관리 시스템</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.error("🚨 Supabase 연동에 실패했습니다. 스트림릿 설정(Secrets)의 URL과 Key 형식을 다시 확인해주세요.")
    else:
        # 데이터 불러오기
        try:
            res = supabase.table("members").select("*").execute()
            members_df = pd.DataFrame(res.data)
        except Exception as e:
            st.error(f"데이터를 불러오지 못했습니다: {e}")
            members_df = pd.DataFrame()

        # 상단: 회원 목록 표
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #38BDF8;'>현재 등록된 회원 (Real-Time)</h3>", unsafe_allow_html=True)
        if not members_df.empty:
            st.dataframe(members_df, use_container_width=True, hide_index=True)
        else:
            st.info("아직 등록된 회원이 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

        # 하단: 회원 추가 폼
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #EC4899;'>신규 회원 권한 발급</h3>", unsafe_allow_html=True)
        with st.form("add_member_supabase", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                m_email = st.text_input("아이디 (이메일)")
                m_pw = st.text_input("비밀번호", type="password")
            with c2:
                m_name = st.text_input("이름 / 회사명")
                m_status = st.selectbox("상태", ["이용중", "승인대기", "정지", "기간만료"])
            
            if st.form_submit_button("Supabase DB에 즉시 등록"):
                if m_email and m_pw:
                    try:
                        supabase.table("members").insert({
                            "email": m_email, "password": m_pw, "name": m_name, "status": m_status
                        }).execute()
                        st.success(f"[{m_name}] 님의 정보가 안전하게 DB에 저장되었습니다!")
                        time.sleep(1)
                        if hasattr(st, "rerun"): st.rerun()
                        else: st.experimental_rerun()
                    except Exception as e:
                        st.error(f"저장 실패 (중복된 이메일일 수 있습니다): {e}")
                else:
                    st.warning("이메일과 비밀번호는 필수 입력사항입니다.")
        st.markdown("</div>", unsafe_allow_html=True)

elif menu == "💰 정밀 마진 계산기":
    st.markdown("<h1>💰 정밀 마진 계산기</h1>", unsafe_allow_html=True)
    st.info("상품 소싱 시 원가와 물류비를 정밀하게 계산합니다.")
    with st.form("margin_form"):
        col1, col2 = st.columns(2)
        with col1:
            sell_price = st.number_input("예상 판매가 (원)", value=30000)
            cost_price = st.number_input("중국 원가 (위안)", value=50)
        with col2:
            exchange_rate = st.number_input("환율", value=195)
            weight = st.number_input("무게 (kg)", value=1.0)
        
        if st.form_submit_button("계산하기"):
            krw_cost = cost_price * exchange_rate
            shipping = 5000 + (weight * 1000)
            net_profit = sell_price - krw_cost - shipping
            st.success(f"예상 순수익: {int(net_profit):,} 원")

elif menu == "🗂️ 소싱 DB 관리":
    st.markdown("<h1>🗂️ 소싱 DB 관리</h1>", unsafe_allow_html=True)
    st.info("구글 시트에 연결된 소싱 데이터베이스입니다.")

elif menu == "✍️ 카피라이팅 기획소":
    st.markdown("<h1>✍️ 실전 카피라이팅 기획소</h1>", unsafe_allow_html=True)
    st.info("상품 상세페이지용 카피라이팅 모듈입니다.")

elif menu == "📥 영상 분석 추출":
    st.markdown("<h1>📥 영상 분석 및 워터마크 추출</h1>", unsafe_allow_html=True)
    st.info("도유인, 틱톡 등의 영상을 다운로드하고 리서치합니다.")
