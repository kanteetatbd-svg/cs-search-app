import streamlit as st
import pandas as pd
import gspread
import time  
import duckdb  # 🚀 นางเอกของเราในรอบนี้ (In-memory Database)
from st_keyup import st_keyup  
from google.oauth2.service_account import Credentials

# --- 1. INITIALIZE SESSION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user" not in st.session_state: st.session_state.user = "Guest"
if "loaded_sheets" not in st.session_state: st.session_state.loaded_sheets = {} 

# --- 2. PREMIUM CSS ---
st.set_page_config(page_title="CS Smart Intelligence", page_icon="⚡", layout="wide")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(-45deg, #0f172a, #1e293b, #0f172a, #172554); background-size: 400% 400%; animation: gradient 15s ease infinite; }
    @keyframes gradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    [data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.6) !important; backdrop-filter: blur(15px); border-right: 1px solid rgba(255, 255, 255, 0.1); }
    .stImage img { border-radius: 50% !important; border: 3px solid #10b981; box-shadow: 0 0 25px rgba(16, 185, 129, 0.5); object-fit: cover; width: 180px !important; height: 180px !important; margin: 0 auto; display: block; }
    .status-bar-ready { background: rgba(16, 185, 129, 0.15); color: #10b981; padding: 12px 20px; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.4); margin-bottom: 25px; font-weight: bold; text-align: center; }
    .main-header { font-size: 3rem !important; font-weight: 800 !important; background: -webkit-linear-gradient(#eee, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN LOGIC ---
USER_DB = {"test123": "123456", "admin": "123456"}

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: white; padding-top: 100px;'>⚡ CS INTELLIGENCE</h1>", unsafe_allow_html=True)
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

# --- 4. DATA ENGINE ---
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
            try:
                h_idx = next((i for i, row in df.iterrows() if sum(1 for v in row if str(v).strip()) > 5), 0)
                df.columns = [h.strip() if h.strip() else f"Col_{i+1}" for i, h in enumerate(df.iloc[h_idx])]
                df['sheet_row'] = df.index + 1
                
                # สร้างดัชนีคำค้นหา เพื่อให้ DuckDB วิ่งหาได้ไวระดับเสี้ยววินาที
                df['search_index'] = df.astype(str).agg(' '.join, axis=1).str.lower()
                
                tabs[ws.title] = df.iloc[h_idx+1:].reset_index(drop=True)
            except:
                continue
            time.sleep(0.4)
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
    
    if st.button("🔄 SYNC DATA (อัปเดตข้อมูล)", use_container_width=True): 
        st.cache_data.clear()
        st.session_state.loaded_sheets = {} 
        st.rerun()
        
    if st.button("🚪 LOGOUT", use_container_width=True): 
        st.session_state.logged_in = False
        st.rerun()

# --- 6. MAIN SYSTEM ---
target = CASE_IDS if mode == "🔍 CS Search" else REFUND_ID
st.markdown(f"<h1 class='main-header'>{mode.split(' ')[1]} SYSTEM</h1>", unsafe_allow_html=True)

master = {}
ids = target if isinstance(target, list) else [target]

for s_id in ids:
    if s_id not in st.session_state.loaded_sheets:
        with st.spinner('กำลังเตรียมฐานข้อมูลความเร็วสูง... (โหลดครั้งแรก)'):
            st.session_state.loaded_sheets[s_id] = load_data(s_id)
            
    res = st.session_state.loaded_sheets[s_id]
    if res:
        for tab, df in res.items():
            master[f"{tab} ({s_id[-4:]})" if len(ids) > 1 else tab] = {"df": df, "id": s_id, "tab": tab}

if master:
    st.markdown('<div class="status-bar-ready">✅ ระบบพร้อม! ค้นหาไวระดับ SQL Database</div>', unsafe_allow_html=True)
    
    # หน่วงเวลาจอกระตุกเหลือ 300ms ให้รู้สึกว่าพิมพ์ปุ๊บมาปั๊บจริงๆ
    q_raw = st_keyup("", placeholder=f"⚡ พิมพ์ Keyword ค้นหาใน {mode} (เว้นวรรคเพื่อหาหลายคำได้)...", label_visibility="collapsed", key=f"search_{mode}", debounce=300)
    q = str(q_raw).strip().lower() if q_raw else ""
    
    if q:
        found_any = False
        # แตกคำค้นหาด้วยการเว้นวรรค (เช่น "ปัญหา ล็อกอิน")
        search_words = q.split()
        
        for name, info in master.items():
            df = info["df"] # DuckDB จะอ่านค่าจากตัวแปร df นี้แหละครับ
            
            # 🚀 สร้างคำสั่ง SQL ยิงผ่าน DuckDB (โคตรไว!)
            conditions = " AND ".join([f"search_index LIKE '%{w.replace('''' ''', '' '' '')}%'" for w in search_words])
            sql_query = f"SELECT * FROM df WHERE {conditions}"
            
            try:
                # วิ่งหาผ่าน Memory Database
                res_df = duckdb.query(sql_query).to_df()
            except:
                res_df = pd.DataFrame() # กันเหนียวเผื่อพนักงานพิมพ์อักขระแปลกๆ
            
            if not res_df.empty:
                found_any = True
                st.markdown(f"<div style='border-left: 5px solid #10b981; padding-left: 15px; margin: 20px 0;'>📁 หมวดหมู่: <b>{name}</b> (เจอ {len(res_df)} รายการ)</div>", unsafe_allow_html=True)
                
                # ซ่อนคอลัมน์ดัชนี ไม่ให้พนักงานเห็น
                display_df = res_df.drop(columns=['search_index'])
                
                cfg = {"sheet_row": None, "การแบน": st.column_config.SelectboxColumn("การแบน", options=["ปลด", "แบน", "รอตรวจสอบ"]), "สถานะ": st.column_config.SelectboxColumn("สถานะ", options=["ปกติ", "ไม่ปกติ", "รอดำเนินการ"])}
                upd = st.data_editor(display_df, use_container_width=True, hide_index=True, column_config=cfg, key=f"ed_{name}_{q}")
                
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
