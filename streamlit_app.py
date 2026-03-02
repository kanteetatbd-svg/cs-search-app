import streamlit as st
import pandas as pd
import gspread
import time  # 👈 เพิ่มระบบหน่วงเวลา
from st_keyup import st_keyup  # 👈 เพิ่มระบบค้นหา Real-time
from google.oauth2.service_account import Credentials

# --- 1. INITIALIZE SESSION (ป้องกัน Error ตอนยังไม่ Login) ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user" not in st.session_state: st.session_state.user = "Guest"

# --- 2. PREMIUM CSS ---
st.set_page_config(page_title="CS Smart Intelligence", page_icon="💎", layout="wide")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(-45deg, #0f172a, #1e293b, #0f172a, #172554); background-size: 400% 400%; animation: gradient 15s ease infinite; }
    @keyframes gradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    [data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.6) !important; backdrop-filter: blur(15px); border-right: 1px solid rgba(255, 255, 255, 0.1); }
    .stImage img { border-radius: 50% !important; border: 3px solid #3b82f6; box-shadow: 0 0 25px rgba(59, 130, 246, 0.5); object-fit: cover; width: 180px !important; height: 180px !important; margin: 0 auto; display: block; }
    .status-bar-ready { background: rgba(16, 185, 129, 0.15); color: #10b981; padding: 12px 20px; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.4); margin-bottom: 25px; font-weight: bold; text-align: center; }
    .main-header { font-size: 3rem !important; font-weight: 800 !important; background: -webkit-linear-gradient(#eee, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN LOGIC ---
USER_DB = {"test123": "123456", "admin": "123456"}

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: white; padding-top: 100px;'>💎 CS INTELLIGENCE</h1>", unsafe_allow_html=True)
    with st.columns([1, 2, 1])[1]:
        with st.form("login"):
            u = st.text_input("Username").strip()
            p = st.text_input("Password", type="password").strip()
            if st.form_submit_button("AUTHENTICATE"):
                if u in USER_DB and USER_DB[u] == p:
                    st.session_state.logged_in, st.session_state.user = True, u
                    st.rerun()
                else: st.error("❌ ข้อมูลไม่ถูกต้อง")
    st.stop() 

# --- 4. DATA ENGINE (เหลือแค่ CS Search & Refund) ---
CASE_IDS = [id.strip() for id in ['1x1VKAo6pRU7dtjgliSyR-aX3ZQaGeMW9PdFb2HosGbo', '1TRTLSmr4Zh9t0aXpVg5IpiYxEAIIKy1PSCEHHIiqNdY']]
REFUND_ID = '1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA'.strip()

@st.cache_data(ttl=3600)
def load_data(sheet_id):
    try:
        gc = gspread.authorize(Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
        sh = gc.open_by_key(sheet_id)
        tabs = {}
        for ws in sh.worksheets():
            data = ws.get_all_values()
            if not data: continue
            df = pd.DataFrame(data)
            h_idx = next((i for i, row in df.iterrows() if sum(1 for v in row if str(v).strip()) > 5), 0)
            df.columns = [h.strip() if h.strip() else f"Col_{i+1}" for i, h in enumerate(df.iloc[h_idx])]
            df['sheet_row'] = df.index + 1
            tabs[ws.title] = df.iloc[h_idx+1:].reset_index(drop=True)
            
            # 🛑 ระบบหน่วงเวลา 1.5 วินาที กัน Google บล็อก Quota Exceeded
            time.sleep(1.5)
            
        return tabs
    except Exception as e:
        st.sidebar.error(f"❌ โหลดไฟล์ {sheet_id[:5]}... พัง: {str(e)}")
        return None

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
    st.markdown(f"<h3 style='text-align: center; color: white;'>คุณ {st.session_state.user}</h3>", unsafe_allow_html=True)
    st.divider()
    mode = st.radio("เลือกฟังก์ชัน:", ["🔍 CS Search", "💰 Refund Search"])
    if st.button("🔄 SYNC DATA", use_container_width=True): st.cache_data.clear(); st.rerun()
    if st.button("🚪 LOGOUT", use_container_width=True): st.session_state.logged_in = False; st.rerun()

# --- 6. MAIN SYSTEM ---
target = CASE_IDS if mode == "🔍 CS Search" else REFUND_ID
st.markdown(f"<h1 class='main-header'>{mode.split(' ')[1]} SYSTEM</h1>", unsafe_allow_html=True)

master = {}
ids = target if isinstance(target, list) else [target]
with st.spinner('กำลังเชื่อมต่อฐานข้อมูล... (อาจใช้เวลาเล็กน้อยเพื่อป้องกันระบบถูกบล็อก)'):
    for s_id in ids:
        res = load_data(s_id)
        if res:
            for tab, df in res.items():
                master[f"{tab} ({s_id[-4:]})" if len(ids) > 1 else tab] = {"df": df, "id": s_id, "tab": tab}

if master:
    st.markdown('<div class="status-bar-ready">✅ พร้อมใช้งาน</div>', unsafe_allow_html=True)
    
    # ⚡ เปลี่ยนมาใช้ st_keyup สำหรับระบบ "พิมพ์ปุ๊บเจอปั๊บ"
    q_raw = st_keyup("", placeholder=f"⚡ พิมพ์ค้นหาปุ๊บ เจอปั๊บใน {mode}...", label_visibility="collapsed", key=f"search_{mode}")
    q = str(q_raw).strip().lower() if q_raw else ""
    
    if q:
        found_any = False
        for name, info in master.items():
            df = info["df"]
            mask = df.drop(columns=['sheet_row']).astype(str).apply(lambda r: r.str.lower().str.contains(q).any(), axis=1)
            res_df = df[mask]
            
            if not res_df.empty:
                found_any = True
                st.markdown(f"<div style='border-left: 5px solid #3b82f6; padding-left: 15px; margin: 20px 0;'>📁 หมวดหมู่: <b>{name}</b></div>", unsafe_allow_html=True)
                
                cfg = {"sheet_row": None, "การแบน": st.column_config.SelectboxColumn("การแบน", options=["ปลด", "แบน", "รอตรวจสอบ"]), "สถานะ": st.column_config.SelectboxColumn("สถานะ", options=["ปกติ", "ไม่ปกติ", "รอดำเนินการ"])}
                upd = st.data_editor(res_df, use_container_width=True, hide_index=True, column_config=cfg, key=f"ed_{name}_{q}")
                
                if st.button(f"💾 SAVE: {name}", key=f"btn_{name}"):
                    try:
                        gc = gspread.authorize(Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                        ws = gc.open_by_key(info["id"]).worksheet(info["tab"])
                        for _, r in upd.iterrows(): ws.update(f"A{int(r['sheet_row'])}", [r.drop('sheet_row').astype(str).tolist()])
                        st.toast("✅ บันทึกสำเร็จ!"); st.cache_data.clear()
                    except Exception as e: st.error(f"❌ พลาด: {e}")

        if not found_any: st.warning(f"❌ ไม่พบข้อมูลสำหรับ: {q}")
else:
    st.info("📡 กรุณาตรวจสอบ ID ไฟล์และการแชร์สิทธิ์ให้ Service Account")
