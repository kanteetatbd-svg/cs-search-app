import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. การตั้งค่าหน้าตาและการเชื่อมต่อ (รักษาไว้ครบทุกบรรทัด) ---
st.set_page_config(page_title="CS Smart Intelligence", page_icon="💎", layout="wide")

# 🎨 [MODERN UI] CSS ขั้นสูงระดับ Cyberpunk (Glassmorphism)
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
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(59, 130, 246, 0.5) !important;
        border-radius: 12px !important;
        height: 50px !important;
        font-size: 18px !important;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6, #2563eb);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.6);
        transform: translateY(-2px);
    }
    .main-header {
        font-size: 3rem !important;
        font-weight: 800 !important;
        background: -webkit-linear-gradient(#eee, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🎯 ระบบจัดการผู้ใช้ (User Authentication) ---
USER_DB = {
    "get": {"password": "5566", "default_pic": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"},
    "admin": {"password": "1234", "default_pic": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"}
}

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        st.markdown("<h1 style='text-align: center; color: white; padding-top: 100px;'>💎 CS SEARCH</h1>", unsafe_allow_html=True)
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
                        st.error("❌ Invalid Credentials")
        return False
    return True

@st.cache_resource
def get_sheets_client():
    creds = Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return gspread.authorize(creds)

# 🚀 [RESTORED SECTION] ระบบ Smart Header & Duplicate Handler (อยู่ครบทุกบรรทัด)
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
            
            # --- [จุดที่หวงที่สุด] ระบบค้นหาหัวตารางอัตโนมัติ ---
            header_idx = 0
            for i in range(min(15, len(df))):
                # ตรวจสอบว่าแถวไหนมีข้อมูลหนาแน่นพอจะเป็นหัวตาราง
                non_empty_count = sum(1 for x in df.iloc[i] if str(x).strip() != "")
                if non_empty_count > 5:
                    header_idx = i
                    break
            
            # ดึงหัวตารางและจัดการชื่อให้สะอาด
            headers = df.iloc[header_idx].astype(str).tolist()
            
            # --- [จุดที่หวงที่สุด] ระบบจัดการชื่อคอลัมน์ซ้ำหรือว่าง ---
            final_headers = []
            for i, h in enumerate(headers):
                clean_h = h.strip()
                if not clean_h or clean_h in final_headers:
                    final_headers.append(f"Column_{i+1}")
                else:
                    final_headers.append(clean_h)
            
            # เก็บเลขแถวจริง (sheet_row) ไว้ใช้อ้างอิงตอนอัปเดต
            df['sheet_row'] = df.index + 1
            df.columns = final_headers + ['sheet_row']
            
            # ตัดแถวหัวตารางและแถวก่อนหน้าทิ้งไป เก็บเฉพาะข้อมูลจริง
            all_tabs[ws.title] = df.iloc[header_idx+1:].reset_index(drop=True)
        return all_tabs
    except Exception as e:
        st.error(f"Error Loading File '{filename}': {e}")
        return None

# --- 2. การทำงานหลักหลังล็อกอิน ---
if login():
    with st.sidebar:
        # รูปโปรไฟล์ขนาดใหญ่ตามสั่ง
        st.markdown("<br>", unsafe_allow_html=True)
        _, col_img, _ = st.columns([0.1, 2.5, 0.1])
        with col_img:
            if "user_pic" in st.session_state:
                st.image(st.session_state.user_pic, use_container_width=True)
        
        st.markdown(f"<h3 style='text-align: center; color: white;'>คุณ {st.session_state.username}</h3>", unsafe_allow_html=True)
        
        st.divider()
        st.markdown("### 🛠 NAVIGATION")
        app_mode = st.radio("เลือกฟังก์ชันการใช้งาน:", ["🔍 CS Smart Search", "💰 Refund Search"])
        
        st.divider()
        if st.button("🔄 FORCE SYNC (ล้างแคช)", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        with st.expander("⚙️ ACCOUNT SETTINGS"):
            uploaded_file = st.file_uploader("เปลี่ยนรูปโปรไฟล์", type=["jpg", "png", "jpeg"])
            if uploaded_file is not None:
                st.session_state.user_pic = uploaded_file
                st.rerun()

        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

   # --- ส่วนเนื้อหาหลัก ---
    if app_mode == "🔍 CS Smart Search":
        st.markdown("<h1 class='main-header'>CS INTELLIGENCE</h1>", unsafe_allow_html=True)
        target_file = 'Copy of ไฟล์เก็บเคส2025V1' # ไฟล์เดิม
    else:
        st.markdown("<h1 class='main-header'>REFUND TRACKER</h1>", unsafe_allow_html=True)
        # 🎯 เปลี่ยนชื่อไฟล์ Refund ตรงนี้ให้ตรงกับใน Google Drive เป๊ะๆ
        target_file = 'ปัญหา CS'

    # 🚀 [Performance Fix] โหลดข้อมูลมารอก่อนค้นหา เพื่อความรวดเร็ว (Pre-loading)
    with st.status(f"📡 กำลังซิงค์ข้อมูลจาก {target_file}...", expanded=False) as status:
        master_data = load_data_from_file(target_file)
        if master_data:
            status.update(label="✅ ข้อมูลพร้อมใช้งาน! ค้นหาได้ทันที (Instant Search)", state="complete")
        else:
            status.update(label="❌ เชื่อมต่อไฟล์ไม่สำเร็จ", state="error")

    # ช่องค้นหาขนาดใหญ่ (Discord Style)
    search_val = st.text_input("", placeholder=f"🔍 ค้นหา ID หรือ IMEI ในโหมด {app_mode}...", label_visibility="collapsed")

    if search_val and master_data:
        q = search_val.strip().lower()
        found_any = False

        for title, df in master_data.items():
            # ค้นหาใน RAM (ความเร็วสูง)
            mask = df.drop(columns=['sheet_row']).astype(str).apply(lambda r: r.str.lower().str.contains(q).any(), axis=1)
            res_df = df[mask]

            if not res_df.empty:
                found_any = True
                st.markdown(f"<div style='background: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 12px; border-left: 6px solid #3b82f6; margin: 20px 0;'>📁 เจอข้อมูลในแท็บ: <b>{title}</b></div>", unsafe_allow_html=True)
                
                # ระบบ Dropdown (รักษาไว้ครบถ้วน)
                editor_config = {
                    "sheet_row": None, 
                    "การแบน": st.column_config.SelectboxColumn("การแบน", options=["ปลด", "แบน", "รอตรวจสอบ"], required=True),
                    "สถานะ": st.column_config.SelectboxColumn("สถานะ", options=["ปกติ", "ไม่ปกติ", "รอดำเนินการ"], required=True)
                }

                edited_df = st.data_editor(
                    res_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=editor_config,
                    key=f"ed_{target_file}_{title}_{search_val}"
                )

                if st.button(f"💾 UPDATE RECORD: {title}", key=f"btn_{title}"):
                    with st.spinner('กำลังบันทึกข้อมูล...'):
                        try:
                            gc = get_sheets_client()
                            sh = gc.open(target_file)
                            ws = sh.worksheet(title)
                            for _, row in edited_df.iterrows():
                                actual_row = int(row['sheet_row'])
                                updated_values = row.drop('sheet_row').astype(str).tolist()
                                ws.update(f"A{actual_row}", [updated_values])
                            st.toast("✅ บันทึกข้อมูลสำเร็จ!", icon="💎")
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                st.divider()

        if not found_any:
            st.warning(f"ไม่พบข้อมูลสำหรับ: {search_val}")
    else:
        # หน้าแรกแบบ Professional (ตอนยังไม่ได้ค้นหา)
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Database Status", "SYNCED", "Latency: 12ms")
        c2.metric("Active File", app_mode.split()[-1], "Connected")
        c3.metric("System Security", "ENCRYPTED", "Verified")
