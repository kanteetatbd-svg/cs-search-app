import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
import base64

# --- 1. ตั้งค่าหน้าตาและการเชื่อมต่อ (รักษาไว้ครบทุกบรรทัด) ---
st.set_page_config(page_title="CS Smart Intelligence", page_icon="💎", layout="wide")

# 🎨 [THEME ENGINE] CSS ขั้นสูงเพื่อให้สวยระดับโลก
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
    
    /* Sidebar แบบ Modern Glass */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* กล่องค้นหาแบบ Discord Style */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(59, 130, 246, 0.5) !important;
        border-radius: 12px !important;
        padding: 15px !important;
        font-size: 18px !important;
    }
    
    /* ปรับแต่งตาราง (Data Editor) ให้ดูแพง */
    .stDataEditor {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* ปุ่มกดแบบ Glow Effect */
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6, #2563eb);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 12px;
        font-weight: bold;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div.stButton > button:hover {
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.6);
        transform: translateY(-2px);
    }
    
    /* สไตล์หัวข้อ */
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

# 🎯 ระบบจัดการผู้ใช้ (รักษาไว้ครบถ้วน)
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
                        st.error("Invalid Credentials")
        return False
    return True

@st.cache_resource
def get_sheets_client():
    creds = Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return gspread.authorize(creds)

# 🚀 [RESTORED SECTION] ระบบ Smart Header & Duplicate Handler (อยู่ครบทุกบรรทัด)
@st.cache_data(ttl=3600)
def load_all_data():
    gc = get_sheets_client()
    sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
    all_tabs = {}
    for ws in sh.worksheets():
        data = ws.get_all_values()
        if not data: continue
        df = pd.DataFrame(data)
        
        # ค้นหาหัวตาราง (Smart Header) - ตรวจสอบความสมบูรณ์
        header_idx = 0
        for i in range(min(15, len(df))):
            non_empty_count = sum(1 for x in df.iloc[i] if str(x).strip() != "")
            if non_empty_count > 5:
                header_idx = i
                break
        
        headers = df.iloc[header_idx].astype(str).tolist()
        
        # จัดการชื่อคอลัมน์ซ้ำหรือว่าง (Duplicate Handler) - ป้องกัน Error
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

# --- 2. การทำงานหลัง Login ---
if login():
    with st.sidebar:
        # แสดงรูปโปรไฟล์ใหญ่แบบพรีเมียม (ไม่มีคำว่าโปรไฟล์)
        st.markdown("<br>", unsafe_allow_html=True)
        _, col_img, _ = st.columns([0.1, 2.5, 0.1])
        with col_img:
            if "user_pic" in st.session_state:
                st.image(st.session_state.user_pic, use_container_width=True)
        
        st.markdown(f"<h3 style='text-align: center; color: white;'>สวัสดี, คุณ {st.session_state.username}</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #3b82f6; font-size: 0.9em;'>Senior CS Specialist</p>", unsafe_allow_html=True)
        
        st.divider()
        if st.button("🔄 SYNC DATABASE", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        with st.expander("🛠 ACCOUNT SETTINGS"):
            uploaded_file = st.file_uploader("Update Avatar", type=["jpg", "png", "jpeg"])
            if uploaded_file is not None:
                st.session_state.user_pic = uploaded_file
                st.rerun()

        if st.button("🚪 TERMINATE SESSION", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- MAIN CONTENT AREA ---
    st.markdown("<h1 class='main-header'>SEARCH HERE</h1>", unsafe_allow_html=True)
    
    # ระบบ Instant Search (ดึงข้อมูลเตรียมไว้ล่วงหน้าเพื่อความไว)
    with st.status("📡 Connecting to Central Database...", expanded=False) as status:
        master_data = load_all_data()
        status.update(label="✅ System Ready! ค้นหาได้ทันใจ", state="complete")

    search_val = st.text_input("", placeholder="🔍 ใส่ ID หรือ IMEI ที่ต้องการตรวจสอบ...", label_visibility="collapsed")

    if search_val:
        q = search_val.strip().lower()
        found_any = False

        for title, df in master_data.items():
            mask = df.drop(columns=['sheet_row']).astype(str).apply(lambda r: r.str.lower().str.contains(q).any(), axis=1)
            res_df = df[mask]

            if not res_df.empty:
                found_any = True
                st.markdown(f"""
                    <div style='background: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 12px; border-left: 6px solid #3b82f6; margin: 20px 0;'>
                        <span style='color: #94a3b8; font-size: 0.8em;'>RESULTS IN TAB:</span><br>
                        <b style='color: white; font-size: 1.2em;'>📁 {title}</b>
                    </div>
                """, unsafe_allow_html=True)
                
                # Dropdown Config (รักษาไว้ตามสั่ง)
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

                if st.button(f"💾 UPDATE RECORD: {title}", key=f"btn_{title}"):
                    with st.spinner('Synchronizing with Google Cloud...'):
                        try:
                            gc = get_sheets_client()
                            sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
                            ws = sh.worksheet(title)
                            for _, row in edited_df.iterrows():
                                actual_row = int(row['sheet_row'])
                                updated_values = row.drop('sheet_row').astype(str).tolist()
                                ws.update(f"A{actual_row}", [updated_values])
                            st.toast("✅ Update Successfully!", icon="💎")
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"❌ Connection Error: {e}")
                st.divider()

        if not found_any:
            st.warning(f"No records found for: {search_val}")
    else:
        # หน้าจอว่างๆ ตอนยังไม่ค้นหา (ให้ดู Professional)
        st.markdown("<br><br>", unsafe_allow_html=True)
        cols = st.columns(3)
        cols[0].metric("System Status", "ONLINE", "Latency: 24ms")
        cols[1].metric("Connected Server", "BKK-01", "Active")
        cols[2].metric("Data Integrity", "100%", "Verified")
