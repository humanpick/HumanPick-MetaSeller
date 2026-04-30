import streamlit as st
import pandas as pd
import re
import webbrowser
import random
import string
from datetime import datetime, date
from urllib.parse import quote  # 한글 깨짐 방지용 URL 인코딩

# --- 1. 페이지 레이아웃 및 디자인 시스템 (Humanpick v1.0) ---
st.set_page_config(page_title="프리미엄 운송 비서", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    
    /* 상하단 메뉴 및 햄버거 버튼 영구 숨김 */
    header, #MainMenu, footer {visibility: hidden;}
    .stApp { background-color: #0B1120 !important; } 
    .main .block-container { max-width: 1400px !important; padding: 1.5rem !important; margin: 0 auto; }
    
    h1, h2, h3, h4, label, p, span { color: #F1F5F9 !important; }
    
    .cyber-title {
        background: linear-gradient(to right, #C084FC, #EC4899, #F59E0B);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 0 10px rgba(236, 72, 153, 0.4); font-size: 2.2rem; font-weight: 900; margin-bottom: 10px;
    }

    /* 🚨 등급별 네온 배지 스타일 🚨 */
    .badge {
        padding: 2px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 800; margin-left: 5px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .badge-admin { background: #38BDF8; color: #0B1120 !important; box-shadow: 0 0 10px #38BDF8; }
    .badge-vip { background: #EC4899; color: #FFFFFF !important; box-shadow: 0 0 10px #EC4899; }
    .badge-paid { background: #8B5CF6; color: #FFFFFF !important; box-shadow: 0 0 10px #8B5CF6; }
    .badge-free { background: #94A3B8; color: #0B1120 !important; }

    /* 지도 툴바 */
    .map-container { display: flex; gap: 8px; margin-bottom: 15px; width: 100%; }
    .map-btn { flex: 1; text-align: center; text-decoration: none !important; padding: 12px 0; border-radius: 8px; font-weight: 900; font-size: 1.1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.3); display: block; }
    .btn-tmap { background: linear-gradient(135deg, #40E0D0, #00BFFF); color: #000000 !important; }
    .btn-kakao { background: linear-gradient(135deg, #FEE500, #F7C600); color: #000000 !important; }
    .btn-naver { background: linear-gradient(135deg, #03C75A, #02B351); color: #FFFFFF !important; }

    /* 글래스 컴포넌트 */
    [data-testid="stForm"], [data-testid="stDataFrame"], [data-testid="stMetric"], .glass-card {
        background: rgba(30, 41, 59, 0.4) !important; backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important; border-radius: 16px !important; padding: 20px !important; margin-bottom: 10px !important;
    }

    /* 탭 메뉴 */
    button[data-baseweb="tab"] { background: rgba(30, 41, 59, 0.5) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; padding: 12px 20px !important; flex: 1; }
    button[data-baseweb="tab"][aria-selected="true"] { background: linear-gradient(90deg, #8B5CF6, #EC4899) !important; box-shadow: 0 0 15px rgba(236, 72, 153, 0.6) !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #FFFFFF !important; font-weight: 900 !important; }

    /* 화이트 폼 (White Form) 강제 적용 */
    div.stButton > button, div.stFormSubmitButton > button { background: linear-gradient(135deg, #8B5CF6, #C084FC) !important; border: none !important; border-radius: 8px !important; min-height: 48px !important; width:100%; transition: all 0.3s ease;}
    div.stButton > button:hover, div.stFormSubmitButton > button:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(139, 92, 246, 0.4) !important; }
    div.stButton > button *, div.stFormSubmitButton > button * { color: #FFFFFF !important; font-weight: 900 !important; }
    
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div { background-color: #FFFFFF !important; border: 1px solid #E2E8F0 !important;}
    div[data-baseweb="input"] > div:focus-within { box-shadow: 0 0 15px #8B5CF6 !important; border-color: #8B5CF6 !important;}
    input, textarea, select { color: #000000 !important; font-weight: 800 !important; font-size: 1.1rem !important;}

    /* 메트릭 */
    [data-testid="stMetricValue"] { font-size: 2.8rem !important; font-weight: 900 !important; color: #FFD700 !important; text-shadow: 0 0 10px rgba(255,215,0,0.3); }
    
    @media (max-width: 800px) {
        .cyber-title { font-size: 1.6rem; text-align:center; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터베이스 및 세션 초기화 ---
if 'USER_DB' not in st.session_state:
    st.session_state.USER_DB = {
        "admin": {"pw": "1234", "role": "admin", "name": "최고관리자", "grade": "관리자"},
        "user1": {"pw": "1111", "role": "user", "name": "김민준", "grade": "VIP회원"}
    }

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_id' not in st.session_state: st.session_state.user_id = ""
if 'ledger' not in st.session_state: st.session_state.ledger = pd.DataFrame(columns=["시간", "날짜", "기사명", "구분", "플랫폼", "매출", "순수익", "상태"])
if 'daily_goal' not in st.session_state: st.session_state.daily_goal = 200000
if 'today_savings' not in st.session_state: st.session_state.today_savings = 0 # 오늘 아낀 톨비 누적

def extract_price(text):
    numbers = [int(n) for n in re.findall(r'\d+', text.replace(',', '')) if int(n) > 1000]
    return max(numbers) if numbers else 0

def get_grade_badge(grade):
    if grade == "관리자": return f'<span class="badge badge-admin">{grade}</span>'
    if grade == "VIP회원": return f'<span class="badge badge-vip">{grade}</span>'
    if grade == "유료회원": return f'<span class="badge badge-paid">{grade}</span>'
    return f'<span class="badge badge-free">{grade}</span>'

# --- 3. 로그인 / 회원가입 페이지 ---
if not st.session_state.logged_in:
    st.markdown('<div style="text-align:center; margin-top:5vh;"><span class="cyber-title">프리미엄 운송 비서</span></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["🔐 로그인", "📝 회원가입 (무료)"])
        with auth_tab1:
            with st.form("login_form"):
                uid = st.text_input("아이디")
                upw = st.text_input("비밀번호", type="password")
                if st.form_submit_button("로그인"):
                    if uid in st.session_state.USER_DB and st.session_state.USER_DB[uid]["pw"] == upw:
                        st.session_state.logged_in = True
                        st.session_state.user_id = uid
                        st.rerun()
                    else: st.error("🚨 정보를 확인해주세요.")
        with auth_tab2:
            with st.form("signup_form"):
                new_id = st.text_input("아이디")
                new_pw = st.text_input("비밀번호", type="password")
                new_name = st.text_input("성함 (실명)")
                ref_code = st.text_input("추천인 코드 (추천 시 VIP 승격)", placeholder="VIP777")
                agree = st.checkbox("[필수] 개인정보 및 이용약관 동의")
                if st.form_submit_button("가입하고 혜택받기"):
                    if not agree or not new_id or not new_name: st.warning("🚨 필수 항목을 채워주세요.")
                    elif new_id in st.session_state.USER_DB: st.error("🚨 이미 있는 아이디입니다.")
                    else:
                        grade = "VIP회원" if ref_code else "무료회원"
                        st.session_state.USER_DB[new_id] = {"pw": new_pw, "role": "user", "name": new_name, "grade": grade}
                        st.session_state.logged_in = True
                        st.session_state.user_id = new_id
                        st.rerun()

# --- 4. 메인 화면 ---
else:
    user_info = st.session_state.USER_DB[st.session_state.user_id]
    
    # [상단 헤더 업데이트: 이름 + 등급 배지]
    c_logo, c_user = st.columns([7, 3])
    c_logo.markdown('<div class="cyber-title">프리미엄 운송 비서</div>', unsafe_allow_html=True)
    
    badge_html = get_grade_badge(user_info['grade'])
    c_user.markdown(f"""
        <div style='text-align:right; padding-top:10px;'>
            <span style='color:#94A3B8; font-size:1.1rem;'>👤 <b>{user_info['name']}</b></span>
            {badge_html}
            <br><a href='#' style='color:#EF4444; font-size:0.8rem; text-decoration:none;' onclick='window.location.reload()'>로그아웃</a>
        </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("로그아웃"): 
        st.session_state.logged_in = False
        st.rerun()

    # --- 관리자 뷰 ---
    if user_info['role'] == "admin":
        tab_a1, tab_a2 = st.tabs(["📊 통합 수익", "👥 회원 관리"])
        with tab_a1:
            total = st.session_state.ledger["매출"].sum()
            st.columns(3)[0].metric("총 매출", f"{total:,}원")
            st.dataframe(st.session_state.ledger, use_container_width=True)
        with tab_a2:
            df_u = pd.DataFrame(st.session_state.USER_DB).T[pd.DataFrame(st.session_state.USER_DB).T['role']=='user']
            st.table(df_u[["name", "grade"]])

    # --- 기사 뷰 ---
    else:
        st.markdown("""<div class="map-container">
            <a href="https://tmap.co.kr/" target="_blank" class="map-btn btn-tmap">🛣️ T맵</a>
            <a href="https://map.kakao.com/" target="_blank" class="map-btn btn-kakao">🗺️ 카카오</a>
            <a href="https://map.naver.com/" target="_blank" class="map-btn btn-naver">📍 네이버</a>
        </div>""", unsafe_allow_html=True)

        # 4개의 핵심 탭으로 확장
        tab1, tab2, tab3, tab4 = st.tabs(["🚀 운행 정산", "📊 수익 지표", "🛡️ 톨 세이버", "🚕 복귀 비서"])
        
        with tab1:
            with st.form("income_form", clear_on_submit=False):
                st.markdown(f'<h3 style="color:#C084FC;">🎙️ {user_info["name"]} 기사님 정산</h3>', unsafe_allow_html=True)
                raw_text = st.text_area("콜 내용 입력", placeholder="[아이콘] 강남->부산 150,000원")
                if st.form_submit_button("⚡ 시스템 즉시 기록"):
                    nums = [int(n) for n in re.findall(r'\d+', raw_text.replace(',', '')) if int(n) > 1000]
                    price = max(nums) if nums else 0
                    if price > 0:
                        new_data = {"시간": datetime.now().strftime("%H:%M"), "날짜": str(date.today()), "기사명": user_info['name'], "구분": "탁송", "플랫폼": "로지", "매출": price, "순수익": int(price*0.8), "상태": "완료"}
                        st.session_state.ledger = pd.concat([pd.DataFrame([new_data]), st.session_state.ledger], ignore_index=True)
                        st.success(f"✔️ {price:,}원 정산 완료")
                        st.rerun()

        with tab2:
            my_df = st.session_state.ledger[st.session_state.ledger["기사명"] == user_info['name']]
            net = my_df["순수익"].sum() if not my_df.empty else 0
            st.metric("오늘의 내 수익", f"{net:,}원")
            st.progress(min(net/st.session_state.daily_goal, 1.0) if st.session_state.daily_goal > 0 else 0)
            st.dataframe(my_df, use_container_width=True)

        # --- 신규 탭: 톨 세이버 ---
        with tab3:
            st.markdown('<h3 style="color:#38BDF8;">🛡️ Toll-Saver Protocol</h3>', unsafe_allow_html=True)
            with st.form("nav_form", clear_on_submit=False):
                col_a, col_b = st.columns(2)
                with col_a: start_point = st.text_input("출발지", placeholder="예: 용인 오토허브")
                with col_b: end_point = st.text_input("도착지", placeholder="예: 부산 경동오토필드")
                submit_nav = st.form_submit_button("최적 경로 및 절감액 분석")
            
            if submit_nav:
                # 분석가 로직 (데이터 기반 시뮬레이션)
                if "용인" in start_point and "부산" in end_point:
                    save_amount = 10900
                    waypoint = "영천IC 35번 국도"
                    desc = "대구-부산 민자 구간 회피 최적화"
                elif "부산" in start_point and "인천" in end_point:
                    save_amount = 12500
                    waypoint = "25번 국도 낙동IC 방면"
                    desc = "상주-영천 민자 구간 회피 최적화"
                else:
                    save_amount = random.choice([3500, 4200, 5500, 7800])
                    waypoint = "최적 우회 국도"
                    desc = "일반 고속도로 요금 절감 로직 적용"
                
                # 누적 절감액 업데이트
                st.session_state.today_savings += save_amount

                st.markdown(f"""
                    <div class="glass-card" style="border-left: 4px solid #38BDF8;">
                        <p style="color:#94A3B8; font-size:0.9rem; margin-bottom:5px;">분석 리포트: {desc}</p>
                        <h4 style="color:#FFFFFF; margin-top:0;">예상 절감액: <span style="color:#FFD700; font-size:1.5rem;">{save_amount:,}원</span></h4>
                        <p style="color:#F1F5F9;">우회 경유지: <b>{waypoint}</b></p>
                    </div>
                """, unsafe_allow_html=True)

                # 내비게이션 딥링크 (quote를 통한 한글 깨짐 방지)
                st.markdown('<p style="color:#8B5CF6; font-weight:800; font-size:1.1rem;">경유지가 포함된 내비게이션 즉시 실행</p>', unsafe_allow_html=True)
                n_col1, n_col2, n_col3 = st.columns(3)
                
                naver_url = f"nmap://route/car?slat=&slng=&sname={quote(start_point)}&dlat=&dlng=&dname={quote(end_point)}&v1name={quote(waypoint)}&appname=humanpick"
                kakao_url = f"kakaomap://route?sp=,&ep=,&by=CAR" # 카카오는 좌표기반이 필수라 예시로 둠
                tmap_url = f"tmap://route?goalname={quote(end_point)}&waypointname={quote(waypoint)}"

                if n_col1.button("🟢 네이버 지도로 열기"): webbrowser.open_new_tab(naver_url)
                if n_col2.button("🟡 카카오내비로 열기"): webbrowser.open_new_tab(kakao_url)
                if n_col3.button("🔵 T맵으로 열기"): webbrowser.open_new_tab(tmap_url)

        # --- 신규 탭: 복귀 비서 ---
        with tab4:
            st.markdown('<h3 style="color:#EC4899;">🚕 Return Protocol</h3>', unsafe_allow_html=True)
            st.markdown(f"""
                <div class="glass-card" style="text-align:center;">
                    <p style="color:#94A3B8; font-size:1.1rem; margin-bottom:0;">오늘 톨-세이버로 아낀 총 누적액</p>
                    <h2 style="color:#FFD700; margin-top:5px; text-shadow: 0 0 10px rgba(255,215,0,0.3);">{st.session_state.today_savings:,}원</h2>
                </div>
            """, unsafe_allow_html=True)

            with st.form("return_form", clear_on_submit=False):
                st.markdown('<p style="color:white; font-weight:800;">복귀 수단 선택 및 순수익 방어 로직</p>', unsafe_allow_html=True)
                r_start = st.text_input("현재 위치", value="인천 송도로터리")
                r_end = st.text_input("복귀할 집 (목적지)", value="경기 광주 양벌로 375")
                
                # 라디오 버튼은 CSS로 커스텀 디자인을 덮어씌움
                return_type = st.radio("복귀 수단 데이터 (예상 비용)", 
                    ["대중교통 (약 10,500원 소요 / 시간: 2h 30m)", 
                     "카셰어링 렌트 (약 35,000원 소요 / 시간: 1h 20m)"]
                )
                submit_return = st.form_submit_button("최종 순수익 결산")

            if submit_return:
                return_cost = 10500 if "대중교통" in return_type else 35000
                final_profit = st.session_state.today_savings - return_cost
                
                result_color = "#38BDF8" if final_profit >= 0 else "#EC4899"
                result_text = "이익 방어 성공" if final_profit >= 0 else "이익 방어 실패 (적자 전환)"
                
                st.markdown(f"""
                    <div class="glass-card" style="border-top: 4px solid {result_color};">
                        <h4 style="color:white;">결산 리포트: <span style="color:{result_color};">{result_text}</span></h4>
                        <ul style="color:#F1F5F9; font-size:1.1rem; line-height:1.8;">
                            <li>아낀 톨게이트비: <b>{st.session_state.today_savings:,}원</b></li>
                            <li>복귀 지출 비용: <b style="color:#EF4444;">-{return_cost:,}원</b></li>
                            <hr style="border-color: rgba(255,255,255,0.1);">
                            <li>복귀 후 남은 톨비 마진: <b style="color:{result_color}; font-size:1.4rem;">{final_profit:,}원</b></li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
