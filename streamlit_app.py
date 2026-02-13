import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. การตั้งค่าหน้าตาและการเชื่อมต่อ (รักษาไว้ครบทุกบรรทัด 100%) ---
st.set_page_config(page_title="CS Smart Intelligence", page_icon="💎", layout="wide")

# 🎨 CSS ระดับพรีเมียม: รูปโปรไฟล์วงกลมขนาดใหญ่ (180px) และสไตล์ Glassmorphism
st.markdown("""
    <style>
    /* พื้นหลังแบบ Animated Gradient */
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
    
    /* ตกแต่ง Sidebar แบบกระจกฝ้า */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 🎯 รูปโปรไฟล์วงกลมขนาดใหญ่และชัดเจนตามที่พี่เก็ตสั่ง */
    .stImage img {
        border-radius: 50% !important;
        border: 3px solid #3b82f6;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
        object-fit: cover;
        width: 180px !important;
        height: 180px !important;
        margin-left: auto;
        margin-right: auto;
        display: block;
    }
    
    /* ตกแต่งช่อง Input ค้นหา */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(59, 130, 246, 0.5) !important;
        border-radius: 12px !important;
        height: 50px !important;
        font-size: 18px !important;
    }
    
    /* ตกแต่งปุ่มกด */
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
    
    /* หัวข้อหลักแบบ Neon */
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
                        st.error("❌ Invalid Credentials")
        return False
    return True

@st.cache_resource
def get_sheets_client():
    creds = Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return gspread.authorize(creds)

# 🚀 [RESTORED SECTION] ระบบ Smart Header Logic และการจัดการคอลัมน์ (ห้ามลบเด็ดขาด)
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
            
            # --- ตรรกะการค้นหาแถวที่เป็นหัวตาราง (Smart Header) ---
            header_idx = 0
            for i in range(min(15, len(df))):
                # ตรวจสอบว่าแถวไหนมีข้อมูลหนาแน่นพอ (มากกว่า 5 ช่อง)
                non_empty_count = 0
                for x in df.iloc[i]:
                    if str(x).strip() != "":
                        non_empty_count += 1
                
                if non_empty_count > 5:
                    header_idx = i
                    break
            
            # ดึงข้อมูลหัวตารางมาทำความสะอาด
            headers = df.iloc[header_idx].astype(str).tolist()
            
            # --- ตรรกะการจัดการชื่อคอลัมน์ซ้ำหรือว่าง (Duplicate Handler) ---
            final_headers = []
            for i, h in enumerate(headers):
                clean_h = h.strip()
                if not clean_h or clean_h in final_headers:
                    # ถ้าชื่อว่างหรือซ้ำ ให้ตั้งชื่อเป็น Column_X
                    final_headers.append(f"Column_{i+1}")
                else:
                    final_headers.append(clean_h)
            
            # เก็บเลขแถวจริงจาก Google Sheets (Sheet Row ID)
            df['sheet_row'] = df.index + 1
            df.columns = final_headers + ['sheet_row']
            
            # ตัดส่วนหัวที่เป็นขยะออก และเก็บเฉพาะข้อมูลจริงเริ่มจากใต้ Header
            all_tabs[ws.title] = df.iloc[header_idx+1:].reset_index(drop=True)
            
        return all_tabs
    except Exception as e:
        st.error(f"Error Loading '{filename}': {e}")
        return None

# --- 2. เริ่มต้นการทำงานหลังผ่านการตรวจสอบสิทธิ์ ---
if login():
    with st.sidebar:
        # ส่วนแสดงรูปโปรไฟล์วงกลมขนาดใหญ่
        st.write("") 
        col_img = st.columns([1, 8, 1])[1]
        with col_img:
            if "user_pic" in st.session_state:
                st.image(st.session_state.user_pic, use_container_width=True)
        
        st.markdown(f"<h3 style='text-align: center; color: white;'>คุณ {st.session_state.username}</h3>", unsafe_allow_html=True)
        
        st.divider()
        st.markdown("### 🛠 NAVIGATION")
        app_mode = st.radio("เลือกโหมดการใช้งาน:", ["🔍 CS Smart Search", "💰 Refund Search"])
        
        st.divider()
        # ส่วนตั้งค่ารูปภาพ
        with st.expander("⚙️ ตั้งค่าโปรไฟล์"):
            uploaded_file = st.file_uploader("เปลี่ยนรูปภาพใหม่", type=["jpg", "png", "jpeg"])
            if uploaded_file is not None:
                st.session_state.user_pic = uploaded_file
                st.toast("อัปเดตรูปโปรไฟล์เรียบร้อย!")

        # ปุ่มบังคับรีเฟรชข้อมูล (Sync)
        if st.button("🔄 FORCE SYNC", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        # ปุ่มออกจากระบบ
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- ส่วนเนื้อหาหลัก (Main Content) ---
    if app_mode == "🔍 CS Smart Search":
        st.markdown("<h1 class='main-header'>CS INTELLIGENCE</h1>", unsafe_allow_html=True)
        target_file = 'Copy of ไฟล์เก็บเคส2025V1'
    else:
        st.markdown("<h1 class='main-header'>REFUND TRACKER</h1>", unsafe_allow_html=True)
        target_file = 'ไฟล์ข้อมูล_Refund' # พี่เก็ตเปลี่ยนชื่อไฟล์จริงที่นี่

    # 🚀 ระบบ Pre-loading ข้อมูลลง RAM (ปรับข้อความตามสั่ง)
    with st.status(f"📡 ซิงค์ข้อมูลจาก {target_file}...", expanded=False) as status:
        master_data = load_data_from_file(target_file)
        if master_data:
            # ข้อความตามที่พี่เก็ตสั่งเป๊ะๆ
            status.update(label="✅ ข้อมูลพร้อมใช้งาน", state="complete")
        else:
            status.update(label="❌ เชื่อมต่อล้มเหลว", state="error")

    # ช่องค้นหาขนาดใหญ่ (Instant Search)
    search_val = st.text_input("", placeholder=f"🔍 ค้นหาในโหมด {app_mode}...", label_visibility="collapsed")

    if search_val and master_data:
        q = search_val.strip().lower()
        found_any = False
        
        # วนลูปค้นหาในทุกแท็บที่โหลดมาไว้ในหน่วยความจำ
        for title, df in master_data.items():
            # ค้นหาคำที่ต้องการในทุกคอลัมน์ (ยกเว้น sheet_row)
            mask = df.drop(columns=['sheet_row']).astype(str).apply(lambda r: r.str.lower().str.contains(q).any(), axis=1)
            res_df = df[mask]
            
            if not res_df.empty:
                found_any = True
                st.markdown(f"<div style='background: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 12px; border-left: 6px solid #3b82f6; margin: 20px 0;'>📁 เจอในแท็บ: <b>{title}</b></div>", unsafe_allow_html=True)
                
                # การตั้งค่า Dropdown สำหรับแก้ไขข้อมูล (รักษาไว้ครบถ้วน)
                editor_config = {
                    "sheet_row": None, # ซ่อนคอลัมน์เลขแถว
                    "การแบน": st.column_config.SelectboxColumn("การแบน", options=["ปลด", "แบน", "รอตรวจสอบ"], required=True),
                    "สถานะ": st.column_config.SelectboxColumn("สถานะ", options=["ปกติ", "ไม่ปกติ", "รอดำเนินการ"], required=True)
                }

                # แสดงตารางแก้ไขข้อมูล (Data Editor)
                edited_df = st.data_editor(
                    res_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=editor_config,
                    key=f"ed_{target_file}_{title}_{search_val}"
                )

                # ปุ่มกดบันทึกข้อมูลกลับไปยัง Google Sheets
                if st.button(f"💾 UPDATE: {title}", key=f"btn_{title}"):
                    with st.spinner('กำลังเชื่อมต่อฐานข้อมูลเพื่อบันทึก...'):
                        try:
                            gc = get_sheets_client()
                            sh = gc.open(target_file)
                            ws = sh.worksheet(title)
                            
                            # วนลูปอัปเดตแถวที่ถูกแก้ไข
                            for _, row in edited_df.iterrows():
                                actual_row = int(row['sheet_row'])
                                updated_values = row.drop('sheet_row').astype(str).tolist()
                                # เขียนข้อมูลทับลงในแถวเดิม
                                ws.update(f"A{actual_row}", [updated_values])
                            
                            st.toast("✅ บันทึกข้อมูลสำเร็จ!", icon="💎")
                            st.cache_data.clear() # ล้างแคชเพื่อให้โหลดข้อมูลใหม่หลังเซฟ
                        except Exception as e:
                            st.error(f"❌ บันทึกไม่สำเร็จ: {e}")
                st.divider()

        if not found_any:
            st.warning(f"ไม่พบข้อมูลสำหรับคำค้นหา: `{search_val}`")
