import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. การตั้งค่าหน้าตาและการเชื่อมต่อ (รักษาไว้ครบทุกบรรทัด 100%) ---
st.set_page_config(page_title="CS Smart Intelligence", page_icon="💎", layout="wide")

# 🎨 [PREMIUM CSS] เน้นรูปวงกลมขนาดใหญ่ และแถบสถานะแบบไม่มี Dropdown
st.markdown("""
    <style>
    /* พื้นหลัง Animated Gradient */
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
    
    /* Sidebar แบบ Glassmorphism */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 🎯 รูปโปรไฟล์วงกลมขนาดใหญ่ (180px) */
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
    
    /* 🎯 แถบสถานะ "พร้อมใช้งาน" แบบไม่มี Dropdown (Static) */
    .status-bar-ready {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        padding: 12px 20px;
        border-radius: 12px;
        border: 1px solid rgba(16, 185, 129, 0.4);
        margin-bottom: 25px;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(59, 130, 246, 0.5) !important;
        border-radius: 12px !important;
        height: 52px !important;
    }
    
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6, #2563eb);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: bold;
        transition: all 0.3s ease;
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

# --- 🎯 ระบบจัดการผู้ใช้ ---
USER_DB = {
    "get": {"password": "5566", "default_pic": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"},
    "admin": {"password": "1234", "default_pic": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"}
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

@st.cache_resource
def get_sheets_client():
    creds = Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return gspread.authorize(creds)

# 🚀 [RESTORED] ระบบ Smart Header Logic (35 บรรทัดแห่งความฉลาด)
@st.cache_data(ttl=3600)
def load_data_from_file(filename):
    gc = get_sheets_client()
    try:
        sh = gc.open(filename)
        all_tabs = {}
        for ws in sh.worksheets():
            data = ws.get_all_values()
            if not data: continue
            df = pd.DataFrame(data)
            
            # --- ตรรกะการค้นหาหัวตาราง (Smart Header Search) ---
            header_idx = 0
            for i in range(min(15, len(df))):
                # ตรวจสอบว่าแถวไหนมีข้อมูลจริงเกิน 5 ช่อง
                active_cells = 0
                for val in df.iloc[i]:
                    if str(val).strip() != "":
                        active_cells += 1
                if active_cells > 5:
                    header_idx = i
                    break
            
            headers = df.iloc[header_idx].astype(str).tolist()
            
            # --- ตรรกะการจัดการชื่อคอลัมน์ซ้ำหรือว่าง (Duplicate Handler) ---
            processed_headers = []
            for idx, h in enumerate(headers):
                clean_name = h.strip()
                if not clean_name or clean_name in processed_headers:
                    processed_headers.append(f"Column_{idx+1}")
                else:
                    processed_headers.append(clean_name)
            
            # เก็บเลขแถวต้นฉบับเพื่อใช้ในการ Update
            df['sheet_row'] = df.index + 1
            df.columns = processed_headers + ['sheet_row']
            
            # ตัดส่วนหัวและเก็บข้อมูลจริง
            all_tabs[ws.title] = df.iloc[header_idx+1:].reset_index(drop=True)
        return all_tabs
    except Exception as e:
        st.error(f"⚠️ พังที่ไฟล์ '{filename}': {e}")
        return None

# --- 2. Main Application Flow ---
if login():
    with st.sidebar:
        st.write("") 
        # จัดวางรูปวงกลมกึ่งกลาง
        c1, c2, c3 = st.columns([1, 10, 1])
        with c2:
            if "user_pic" in st.session_state:
                st.image(st.session_state.user_pic, use_container_width=True)
        
        st.markdown(f"<h3 style='text-align: center; color: white;'>คุณ {st.session_state.username}</h3>", unsafe_allow_html=True)
        
        st.divider()
        st.markdown("### 🛠 NAVIGATION")
        app_mode = st.radio("เลือกฟังก์ชัน:", ["🔍 CS Smart Search", "💰 Refund Search"])
        
        st.divider()
        with st.expander("⚙️ ตั้งค่าโปรไฟล์"):
            new_pic = st.file_uploader("เปลี่ยนรูปภาพ", type=["jpg", "png", "jpeg"])
            if new_pic:
                st.session_state.user_pic = new_pic
                st.toast("อัปเดตรูปสำเร็จ!")

        if st.button("🔄 FORCE SYNC", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- ส่วนเนื้อหาหลัก ---
    if app_mode == "🔍 CS Smart Search":
        st.markdown("<h1 class='main-header'>CS INTELLIGENCE</h1>", unsafe_allow_html=True)
        target_file = 'Copy of ไฟล์เก็บเคส2025V1'
    else:
        st.markdown("<h1 class='main-header'>REFUND TRACKER</h1>", unsafe_allow_html=True)
        target_file = 'ไฟล์ข้อมูล_Refund' # พี่เก็ตเปลี่ยนชื่อไฟล์จริงที่นี่

    # 🚀 Pre-loading Engine (Instant Search)
    master_data = load_data_from_file(target_file)
    
    if master_data:
        # 🎯 แถบสถานะแบบ Static ตามสั่ง (ไม่มี Dropdown)
        st.markdown('<div class="status-bar-ready">✅ ข้อมูลพร้อมใช้งาน</div>', unsafe_allow_html=True)
    else:
        st.warning("📡 กำลังรอการเชื่อมต่อไฟล์...")

    search_val = st.text_input("", placeholder=f"🔍 ค้นหาข้อมูลใน {app_mode}...", label_visibility="collapsed")

    if search_val and master_data:
        query = search_val.strip().lower()
        found_flag = False
        
        for tab_name, data_frame in master_data.items():
            # ค้นหาแบบ Case-insensitive ในทุกคอลัมน์
            match_mask = data_frame.drop(columns=['sheet_row']).astype(str).apply(lambda row: row.str.lower().str.contains(query).any(), axis=1)
            result_df = data_frame[match_mask]
            
            if not result_df.empty:
                found_flag = True
                st.markdown(f"<div style='background: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 12px; border-left: 6px solid #3b82f6; margin: 20px 0;'>📁 แท็บ: <b>{tab_name}</b></div>", unsafe_allow_html=True)
                
                # Config สำหรับ Dropdown แก้ไขข้อมูล
                edit_cfg = {
                    "sheet_row": None, 
                    "การแบน": st.column_config.SelectboxColumn("การแบน", options=["ปลด", "แบน", "รอตรวจสอบ"], required=True),
                    "สถานะ": st.column_config.SelectboxColumn("สถานะ", options=["ปกติ", "ไม่ปกติ", "รอดำเนินการ"], required=True)
                }

                updated_df = st.data_editor(result_df, use_container_width=True, hide_index=True, column_config=edit_cfg, key=f"editor_{tab_name}_{search_val}")

                if st.button(f"💾 UPDATE: {tab_name}", key=f"btn_{tab_name}"):
                    with st.spinner('กำลังบันทึกข้อมูลลง Sheets...'):
                        try:
                            gc = get_sheets_client()
                            sheet_obj = gc.open(target_file)
                            worksheet_obj = sheet_obj.worksheet(tab_name)
                            
                            for _, r in updated_df.iterrows():
                                row_id = int(r['sheet_row'])
                                new_vals = r.drop('sheet_row').astype(str).tolist()
                                worksheet_obj.update(f"A{row_id}", [new_vals])
                            
                            st.toast("✅ บันทึกสำเร็จ!", icon="💎")
                            st.cache_data.clear()
                        except Exception as err:
                            st.error(f"❌ บันทึกไม่สำเร็จ: {err}")
                st.divider()

        if not found_flag:
            st.warning(f"ไม่พบข้อมูลสำหรับ: {search_val}")
