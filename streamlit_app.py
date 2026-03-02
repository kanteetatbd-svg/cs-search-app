import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. การตั้งค่าหน้าจอและ CSS (รักษาของเดิมไว้ทั้งหมด) ---
st.set_page_config(page_title="CS Smart Intelligence", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(-45deg, #0f172a, #1e293b, #0f172a, #172554);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stImage img {
        border-radius: 50% !important;
        border: 3px solid #3b82f6;
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.5);
        object-fit: cover;
        width: 180px !important;
        height: 180px !important;
        margin: 0 auto;
        display: block;
    }
    .status-bar-ready {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        padding: 12px 20px;
        border-radius: 12px;
        border: 1px solid rgba(16, 185, 129, 0.4);
        margin-bottom: 25px;
        font-weight: bold;
        text-align: center;
    }
    .main-header {
        font-size: 3rem !important;
        font-weight: 800 !important;
        background: -webkit-linear-gradient(#eee, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🎯 ระบบจัดการผู้ใช้ (รักษาของเดิม) ---
USER_DB = {
    "test123": {"password": "123456", "default_pic": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"},
    "admin": {"password": "123456", "default_pic": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"}
}

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h1 style='text-align: center; color: white; padding-top: 100px;'>💎 CS INTELLIGENCE</h1>", unsafe_allow_html=True)
        cols = st.columns([1, 2, 1])
        with cols[1]:
            with st.form("login_form"):
                user = st.text_input("Username")
                pw = st.text_input("Password", type="password")
                if st.form_submit_button("AUTHENTICATE"):
                    if user in USER_DB and USER_DB[user]["password"] == pw:
                        st.session_state.logged_in = True
                        st.session_state.username = user
                        if "user_pic" not in st.session_state:
                            st.session_state.user_pic = USER_DB[user]["default_pic"]
                        st.rerun()
                    else:
                        st.error("❌ ข้อมูลไม่ถูกต้อง")
        return False
    return True

# --- 🚀 [CONFIG] ใส่ ID ไฟล์ทั้ง 3 ที่นี่ ---
# อ้างอิงจากโปรเจกต์ sturdy-sentry-487204-s4
FAQ_SHEET_ID = '1DkCgWps-wR4kaqMQp9eATV2S0uCf8nTe'
CASE_SHEET_LIST = ['1x1VKAo6pRU7dtjgliSyR-aX3ZQaGeMW9PdFb2HosGbo', '1TRTLSmr4Zh9t0aXpVg5IpiYxEAIIKy1PSCEHHIiqNdY']
REFUND_SHEET_ID = '1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA'

@st.cache_resource
def get_sheets_client():
    creds = Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return gspread.authorize(creds)

# 🚀 [RESTORED] ระบบ Smart Header Logic (คงความฉลาดไว้ครบ)
@st.cache_data(ttl=3600)
def load_data_from_file(sheet_id):
    gc = get_sheets_client()
    try:
        sh = gc.open_by_key(sheet_id) # เปลี่ยนมาใช้ open_by_key เพื่อความเสถียร
        all_tabs = {}
        for ws in sh.worksheets():
            data = ws.get_all_values()
            if not data: continue
            df = pd.DataFrame(data)
            
            header_idx = 0
            for i in range(min(15, len(df))):
                active_cells = sum(1 for val in df.iloc[i] if str(val).strip() != "")
                if active_cells > 5:
                    header_idx = i
                    break
            
            headers = df.iloc[header_idx].astype(str).tolist()
            processed_headers = []
            for idx, h in enumerate(headers):
                clean_name = h.strip()
                if not clean_name or clean_name in processed_headers:
                    processed_headers.append(f"Column_{idx+1}")
                else:
                    processed_headers.append(clean_name)
            
            df['sheet_row'] = df.index + 1
            df.columns = processed_headers + ['sheet_row']
            all_tabs[ws.title] = df.iloc[header_idx+1:].reset_index(drop=True)
        return all_tabs
    except Exception as e:
        st.error(f"⚠️ พังที่ ID '{sheet_id}': {e}")
        return None

# --- ส่วน Main Application ---
if login():
    with st.sidebar:
        st.write("") 
        c1, c2, c3 = st.columns([1, 10, 1])
        with c2:
            if "user_pic" in st.session_state:
                st.image(st.session_state.user_pic, use_container_width=True)
        
        st.markdown(f"<h3 style='text-align: center; color: white;'>คุณ {st.session_state.username}</h3>", unsafe_allow_html=True)
        
        st.divider()
        st.markdown("### 🛠 NAVIGATION")
        # ปรับเป็น 3 เมนูตามแผน
        app_mode = st.radio("เลือกฟังก์ชัน:", ["📋 FAQ", "🔍 CS Smart Search", "💰 Refund Search"])
        
        st.divider()
        if st.button("🔄 FORCE SYNC", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
            # --- 🎯 [ส่วนที่ 2] เริ่มการจัดการเนื้อหาตามเมนูที่เลือก ---
    
    # กำหนด ID ไฟล์ตามโหมดที่เลือก (ใช้ Key แทนชื่อไฟล์เพื่อความเสถียร)
# --- 🎯 [แก้ไขส่วนที่ 2] จัดการเนื้อหาและการโหลดหลายไฟล์ ---
    
    # 1. กำหนด ID ไฟล์ (รองรับทั้ง String เดียว และ List)
    if app_mode == "📋 FAQ":
        target_id = FAQ_SHEET_ID
        header_text = "FAQ DATABASE"
    elif app_mode == "🔍 CS Smart Search":
        target_id = CASE_SHEET_LIST  # ใช้ LIST ที่มี 2025 และ 2026
        header_text = "CS INTELLIGENCE"
    else:
        target_id = REFUND_SHEET_ID
        header_text = "REFUND TRACKER"

    st.markdown(f<h1 class='main-header'>{header_text}</h1>, unsafe_allow_html=True)

    # 2. 🚀 ระบบโหลดข้อมูลอัจฉริยะ (รองรับทั้งไฟล์เดียวและหลายไฟล์)
    master_data = {}
    if isinstance(target_id, list):
        # ถ้าเป็น List (กรณี CS Smart Search) ให้วนลูปโหลดทีละไฟล์
        for s_id in target_id:
            file_data = load_data_from_file(s_id)
            if file_data:
                for tab_name, data_frame in file_data.items():
                    # ต่อท้ายชื่อแท็บด้วย ID 4 ตัวท้าย จะได้รู้ว่ามาจากปีไหน (2025/2026)
                    master_data[f"{tab_name} ({s_id[-4:]})"] = data_frame
    else:
        # ถ้าเป็นไฟล์เดียว (FAQ, Refund) โหลดปกติ
        master_data = load_data_from_file(target_id)
    
    # 3. ตรวจสอบว่ามีข้อมูลไหมแล้วไปต่อ
    if master_data:
        st.markdown('<div class="status-bar-ready">✅ FINISHED</div>', unsafe_allow_html=True)

    # 🚀 โหลดข้อมูล (Smart Header Engine จะทำงานอัตโนมัติ)
    master_data = load_data_from_file(target_id)
    
    if master_data:
        st.markdown('<div class="status-bar-ready">✅ FINISHED</div>', unsafe_allow_html=True)
        
        # ช่องค้นหาขนาดใหญ่
        search_val = st.text_input("", placeholder=f"🔍 ค้นหาใน {app_mode} (กรอก ID, IMEI หรือหัวข้อ...)", label_visibility="collapsed")

        if search_val:
            query = search_val.strip().lower()
            found_flag = False
            
            for tab_name, data_frame in master_data.items():
                # ค้นหาแบบไม่สนตัวพิมพ์เล็ก-ใหญ่ ในทุกคอลัมน์
                match_mask = data_frame.drop(columns=['sheet_row']).astype(str).apply(
                    lambda row: row.str.lower().str.contains(query).any(), axis=1
                )
                result_df = data_frame[match_mask]
                
                if not result_df.empty:
                    found_flag = True
                    st.markdown(f"<div style='background: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 12px; border-left: 6px solid #3b82f6; margin: 20px 0;'>📁 พบข้อมูลในแท็บ: <b>{tab_name}</b></div>", unsafe_allow_html=True)
                    
                    # --- ส่วนของการตั้งค่าการแก้ไขข้อมูล (Data Editor) ---
                    # เฉพาะหน้า Search และ Refund ที่ให้แก้ไขได้
                    if app_mode != "📋 FAQ":
                        # คุณสามารถเพิ่ม options ใน SelectboxColumn ได้ตามต้องการ
                        edit_cfg = {
                            "sheet_row": None, 
                            "การแบน": st.column_config.SelectboxColumn("การแบน", options=["ปลด", "แบน", "รอตรวจสอบ"]),
                            "สถานะ": st.column_config.SelectboxColumn("สถานะ", options=["ปกติ", "ไม่ปกติ", "รอดำเนินการ"])
                        }
                        
                        updated_df = st.data_editor(result_df, use_container_width=True, hide_index=True, column_config=edit_cfg, key=f"ed_{tab_name}_{search_val}")
                        
                        # ปุ่ม Save แยกตามแท็บ
                        if st.button(f"💾 บันทึกการเปลี่ยนแปลงใน {tab_name}", key=f"save_{tab_name}"):
                            with st.spinner('กำลังเขียนข้อมูลกลับไปยัง Google Sheets...'):
                                try:
                                    gc = get_sheets_client()
                                    sh = gc.open_by_key(target_id)
                                    ws = sh.worksheet(tab_name)
                                    
                                    for _, r in updated_df.iterrows():
                                        row_num = int(r['sheet_row'])
                                        new_row_values = r.drop('sheet_row').astype(str).tolist()
                                        ws.update(f"A{row_num}", [new_row_values])
                                    
                                    st.toast("✅ บันทึกสำเร็จ!", icon="💎")
                                    st.cache_data.clear()
                                except Exception as err:
                                    st.error(f"❌ บันทึกพลาด: {err}")
                    else:
                        # หน้า FAQ โชว์เป็นตารางอย่างเดียว (เพื่อความปลอดภัย)
                        st.dataframe(result_df.drop(columns=['sheet_row']), use_container_width=True, hide_index=True)
                    
                    st.divider()

            if not found_flag:
                st.warning(f"❌ ไม่พบข้อมูลสำหรับ: {search_val}")
    else:
        st.info("📡 กำลังรอข้อมูลจาก Google Sheets (ตรวจสอบสิทธิ์การแชร์ไฟล์)...")
