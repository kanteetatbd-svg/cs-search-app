import streamlit as st
import pandas as pd
import gspread
import time  
import duckdb  
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

# --- 4. DATA ENGINE & LOG CONFIG ---
CASE_IDS = [id.strip() for id in ['1x1VKAo6pRU7dtjgliSyR-aX3ZQaGeMW9PdFb2HosGbo', '1TRTLSmr4Zh9t0aXpVg5IpiYxEAIIKy1PSCEHHIiqNdY']]
REFUND_ID = '1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA'.strip()

# 📝 เอา ID ไฟล์สมุดพกมาใส่ตรงนี้ครับ
AUDIT_LOG_ID = '1MfPPlI9T5FQV8od2pIyIvGmBG1-ScvpUM__d5SCkQU8'.strip() 

@st.cache_data(ttl=3600)
def load_data(sheet_id):
    try:
        gc = gspread.authorize(Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
        sh = gc.open_by_key(sheet_id)
        tabs = {}
        for ws in sh.worksheets():
            max_retries = 3
            data = None
            for attempt in range(max_retries):
                try:
                    data = ws.get_all_values()
                    break 
                except Exception as e:
                    if "429" in str(e): 
                        time.sleep(10)  
                    else:
                        raise e 
            
            if not data: continue
            
            df = pd.DataFrame(data)
            try:
                h_idx = next((i for i, row in df.iterrows() if sum(1 for v in row if str(v).strip()) > 5), 0)
                df.columns = [h.strip() if h.strip() else f"Col_{i+1}" for i, h in enumerate(df.iloc[h_idx])]
                df['sheet_row'] = df.index + 1
                df['search_index'] = df.astype(str).agg(' '.join, axis=1).str.lower()
                tabs[ws.title] = df.iloc[h_idx+1:].reset_index(drop=True)
            except:
                continue
                
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
    
    mode = st.radio("เลือกฟังก์ชัน:", ["🔍 CS Search", "💰 Refund Search", "📋 ประวัติการแก้ไข"])
    
    if st.button("🔄 SYNC DATA", use_container_width=True): 
        st.cache_data.clear()
        st.session_state.loaded_sheets = {} 
        st.rerun()
        
    if st.button("🚪 LOGOUT", use_container_width=True): 
        st.session_state.logged_in = False
        st.rerun()

# --- 6. 🚀 PRE-LOAD ALL DATA (โหลดทุกอย่างตุนไว้ตั้งแต่เข้าแอป) ---
ALL_IDS = CASE_IDS + [REFUND_ID]
for s_id in ALL_IDS:
    if s_id not in st.session_state.loaded_sheets:
        msg = "ข้อมูล CS" if s_id in CASE_IDS else "ข้อมูล Refund"
        with st.spinner(f'กำลังโหลด {msg} อัตโนมัติรวดเดียว... (โหลดครั้งแรกอาจใช้เวลาหน่อยนะครับ)'):
            st.session_state.loaded_sheets[s_id] = load_data(s_id)

# --- 7. MAIN SYSTEM ---
if mode == "📋 ประวัติการแก้ไข":
    st.markdown("<h1 class='main-header'>AUDIT LOGS</h1>", unsafe_allow_html=True)
    st.markdown("ตรวจสอบประวัติการแก้ไขข้อมูลทั้งหมดโดยไม่ต้องเปิด Google Sheets")
    
    if AUDIT_LOG_ID == '1MfPPlI9T5FQV8od2pIyIvGmBG1-ScvpUM__d5SCkQU8' or not AUDIT_LOG_ID:
        st.warning("⚠️ โปรดใส่ ID ไฟล์ Google Sheets สำหรับเก็บประวัติ (AUDIT_LOG_ID) ในโค้ดบรรทัดที่ 46 ก่อนครับ")
    else:
        with st.spinner("กำลังดึงประวัติการแก้ไข..."):
            try:
                gc = gspread.authorize(Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                log_ws = gc.open_by_key(AUDIT_LOG_ID).sheet1
                log_data = log_ws.get_all_values()
                
                if len(log_data) > 1: 
                    df_log = pd.DataFrame(log_data[1:], columns=log_data[0])
                    st.dataframe(df_log.iloc[::-1], use_container_width=True, hide_index=True)
                else:
                    st.info("💡 ยังไม่มีประวัติการแก้ไขข้อมูล")
            except Exception as e:
                st.error(f"❌ ดึงข้อมูลประวัติพัง: {e}")

else:
    # เลือกเฉพาะ ID ที่ตรงกับโหมดปัจจุบันมาใช้งาน
    target_ids = CASE_IDS if mode == "🔍 CS Search" else [REFUND_ID]
    st.markdown(f"<h1 class='main-header'>{mode.split(' ')[1]} SYSTEM</h1>", unsafe_allow_html=True)

    master = {}
    for s_id in target_ids:
        res = st.session_state.loaded_sheets.get(s_id)
        if res:
            for tab, df in res.items():
                master[f"{tab} ({s_id[-4:]})" if len(target_ids) > 1 else tab] = {"df": df, "id": s_id, "tab": tab}

    if master:
        st.markdown('<div class="status-bar-ready">✅ ระบบพร้อมใช้งาน!</div>', unsafe_allow_html=True)
        
        q_raw = st_keyup("", placeholder=f"⚡ พิมพ์ Keyword ค้นหา..", label_visibility="collapsed", key=f"search_{mode}", debounce=300)
        q = str(q_raw).strip().lower() if q_raw else ""
        
        if q:
            found_any = False
            search_words = q.split()
            
            for name, info in master.items():
                df = info["df"] 
                
                conditions = " AND ".join([f"search_index LIKE '%{w.replace('''' ''', '' '' '')}%'" for w in search_words])
                sql_query = f"SELECT * FROM df WHERE {conditions}"
                
                try:
                    res_df = duckdb.query(sql_query).to_df()
                except:
                    res_df = pd.DataFrame() 
                
                if not res_df.empty:
                    found_any = True
                    st.markdown(f"<div style='border-left: 5px solid #10b981; padding-left: 15px; margin: 20px 0;'>📁 หมวดหมู่: <b>{name}</b> (เจอ {len(res_df)} รายการ)</div>", unsafe_allow_html=True)
                    
                    display_df = res_df.drop(columns=['search_index'])
                    
                    cfg = {"sheet_row": None, "การแบน": st.column_config.SelectboxColumn("การแบน", options=["ปลด", "แบน", "รอตรวจสอบ"]), "สถานะ": st.column_config.SelectboxColumn("สถานะ", options=["ปกติ", "ไม่ปกติ", "รอดำเนินการ"])}
                    upd = st.data_editor(display_df, use_container_width=True, hide_index=True, column_config=cfg, key=f"ed_{name}_{q}")
                    
                    if st.button(f"💾 SAVE: {name}", key=f"btn_{name}"):
                        try:
                            mask = upd.ne(display_df).any(axis=1)
                            changed_rows = upd[mask]
                            
                            if changed_rows.empty:
                                st.info("💡 ไม่มีการเปลี่ยนแปลงข้อมูล")
                            else:
                                gc = gspread.authorize(Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                                ws = gc.open_by_key(info["id"]).worksheet(info["tab"])
                                
                                current_time = pd.Timestamp.now('Asia/Bangkok').strftime('%Y-%m-%d %H:%M:%S')
                                current_user = st.session_state.user
                                
                                for _, r in changed_rows.iterrows():
                                    update_list = [str(r[col]) for col in display_df.columns if col != 'sheet_row']
                                    ws.update(f"A{int(r['sheet_row'])}", [update_list])
                                    
                                    if AUDIT_LOG_ID and AUDIT_LOG_ID != 'เอา_ID_ไฟล์สมุดพกมาใส่ตรงนี้':
                                        try:
                                            log_ws = gc.open_by_key(AUDIT_LOG_ID).sheet1
                                            log_ws.append_row([current_time, current_user, name, int(r['sheet_row']), str(update_list)])
                                        except Exception as log_e:
                                            print(f"Log Error: {log_e}")
                                            
                                st.toast("✅ บันทึกสำเร็จ!")
                                st.cache_data.clear()
                                st.session_state.loaded_sheets = {}
                                time.sleep(1)
                                st.rerun()
                        except Exception as e: st.error(f"❌ พลาด: {e}")

            if not found_any: st.warning(f"❌ ไม่พบข้อมูลสำหรับ: {q}")
