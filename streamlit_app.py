import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
import base64

# --- 1. ตั้งค่าหน้าตาและการเชื่อมต่อ (รักษาไว้ครบทุกบรรทัด) ---
st.set_page_config(page_title="CS Smart Intelligence", page_icon="🔍", layout="wide")

# 🎨 [NEW] Custom CSS สำหรับตกแต่งหน้าตาให้สวยระดับพรีเมียม
st.markdown("""
    <style>
    /* พื้นหลังแบบ Gradient */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* ตกแต่ง Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* กล่องข้อมูลแบบ Glassmorphism */
    div.stButton > button {
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #3b82f6;
        border-color: #3b82f6;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
    }
    
    /* หัวข้อ Neon Glow */
    .neon-text {
        color: #fff;
        text-shadow: 0 0 10px rgba(59, 130, 246, 0.8);
        font-weight: bold;
    }
    
    /* ปรับแต่งตาราง Data Editor */
    .stDataEditor {
        background-color: rgba(0, 0, 0, 0.2);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# 🎯 ฟังก์ชันจัดการ Theme (รักษาไว้)
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# --- 🎯 ระบบจัดการผู้ใช้ ---
USER_DB = {
    "get": {"password": "5566", "default_pic": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"},
    "admin": {"password": "1234", "default_pic": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"}
}

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        st.markdown("<h1 style='text-align: center; color: white;'>🔐 CS Intelligence Login</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Access System"):
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

# 🚀 [Restored Section] ระบบโหลดข้อมูลพร้อม Smart Header และการจัดการคอลัมน์ซ้ำ (อยู่ครบ 30+ บรรทัด)
@st.cache_data(ttl=3600)
def load_all_data():
    gc = get_sheets_client()
    sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
    all_tabs = {}
    for ws in sh.worksheets():
        data = ws.get_all_values()
        if not data: continue
        df = pd.DataFrame(data)
        
        # ค้นหาหัวตาราง (Smart Header) - ห้ามลบ
        header_idx = 0
        for i in range(min(15, len(df))):
            non_empty_count = sum(1 for x in df.iloc[i] if str(x).strip() != "")
            if non_empty_count > 5:
                header_idx = i
                break
        
        headers = df.iloc[header_idx].astype(str).tolist()
        
        # จัดการชื่อคอลัมน์ซ้ำหรือว่าง (Duplicate Handler) - ห้ามลบ
        final_headers = []
        for i, h in enumerate(headers):
            clean_h = h.strip()
            if not clean_h or clean_h in final_headers:
                final_headers.append(f"Column_{i+1}")
            else:
                final_headers.append(clean_h)
        
        df['sheet_row'] = df.index + 1
        df.columns = final_headers + ['sheet_row']
        all_tabs[ws.title] = df.iloc[header_idx+1:].reset_index(drop=True)
    return all_tabs

# --- 2. เริ่มทำงานเมื่อล็อกอินผ่าน ---
if login():
    with st.sidebar:
        # ดีไซน์โปรไฟล์ใหม่แบบมีขอบ Neon
        st.markdown("<br>", unsafe_allow_html=True)
        _, col_img, _ = st.columns([0.1, 2.5, 0.1])
        with col_img:
            if "user_pic" in st.session_state:
                st.image(st.session_state.user_pic, use_container_width=True)
        
        st.markdown(f"<h3 style='text-align: center; color: #3b82f6;'>คุณ {st.session_state.username}</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>CS Specialist</p>", unsafe_allow_html=True)
        
        st.divider()
        if st.button("🔄 Sync Data (Refresh)", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        with st.expander("⚙️ Settings"):
            uploaded_file = st.file_uploader("Change Profile Picture", type=["jpg", "png", "jpeg"])
            if uploaded_file is not None:
                st.session_state.user_pic = uploaded_file
                st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- ส่วนเนื้อหาหลัก ---
    st.markdown("<h1 class='neon-text'>🔍 CS Case Instant Search</h1>", unsafe_allow_html=True)
    
    # ดึงข้อมูลมาเตรียมไว้ใน Cache (Instant Search)
    with st.status("📡 Connecting to Galaxy Database...", expanded=False) as status:
        master_data = load_all_data()
        status.update(label="✅ System Ready! ค้นหาได้ทันที", state="complete")

    search_val = st.text_input("", placeholder="พิมพ์ ID หรือ IMEI แล้วกด Enter เพื่อค้นหาทันที...", label_visibility="collapsed")

    if search_val:
        q = search_val.strip().lower()
        found_any = False

        for title, df in master_data.items():
            mask = df.drop(columns=['sheet_row']).astype(str).apply(lambda r: r.str.lower().str.contains(q).any(), axis=1)
            res_df = df[mask]

            if not res_df.empty:
                found_any = True
                st.markdown(f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 10px; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 10px;'>📂 พบข้อมูลในแท็บ: <b>{title}</b></div>", unsafe_allow_html=True)
                
                # Dropdown Config (รักษาไว้ครบถ้วน)
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
                    key=f"editor_{title}_{search_val}"
                )

                if st.button(f"💾 Save Changes in {title}", key=f"btn_{title}"):
                    with st.spinner('Syncing with Google Sheets...'):
                        try:
                            gc = get_sheets_client()
                            sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
                            ws = sh.worksheet(title)
                            for _, row in edited_df.iterrows():
                                actual_row = int(row['sheet_row'])
                                updated_values = row.drop('sheet_row').astype(str).tolist()
                                ws.update(f"A{actual_row}", [updated_values])
                            st.toast("✅ ข้อมูลถูกบันทึกสำเร็จ!", icon="💾")
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                st.divider()

        if not found_any:
            st.warning(f"ไม่พบข้อมูลสำหรับ: {search_val}")
    else:
        st.info("💡 พร้อมทำงาน! ทีม CS สามารถค้นหาข้อมูลเคสได้ทันทีจากช่องค้นหาด้านบน")
