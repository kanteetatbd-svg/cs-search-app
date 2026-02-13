import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. การตั้งค่าหน้าตา (UI) ---
st.set_page_config(page_title="CS Case Intelligence", page_icon="📝", layout="wide")

# เพิ่ม CSS ให้ตารางอ่านง่ายขึ้น
st.markdown("""
    <style>
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    .st-emotion-cache-1kyxreq { justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 🎯 ระบบจัดการผู้ใช้ ---
USER_DB = {
    "admin": "1234",
    "get": "5566",
    "staff_01": "7788"
}

# --- 🎯 จุดตั้งค่า Dropdown ---
DROPDOWN_CONFIG = {
    'สถานะ': ['รอตรวจสอบ', 'กำลังดำเนินการ', 'ปิดเคสเรียบร้อย', 'ยกเลิก/ข้อมูลผิด'],
    'ประเภทเคส': ['ID', 'IMEI', 'เปลี่ยนเครื่อง', 'อื่นๆ']
}

# --- 2. ฟังก์ชันตรวจสอบการล็อกอิน ---
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔐 เข้าสู่ระบบ CS Case Management")
        with st.form("login_form"):
            user = st.text_input("ชื่อผู้ใช้งาน (Username)")
            pw = st.text_input("รหัสผ่าน (Password)", type="password")
            submit = st.form_submit_button("เข้าสู่ระบบ")
            
            if submit:
                if user in USER_DB and USER_DB[user] == pw:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.login_time = datetime.datetime.now().strftime("%H:%M:%S")
                    st.rerun()
                else:
                    st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        return False
    return True

# --- 3. เชื่อมต่อ Google Sheets ---
@st.cache_resource
def get_sheets_client():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('key.json', scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ ระบบหากุญแจไม่เจอ: {e}")
        return None

@st.cache_data(ttl=60)
def load_data_for_edit():
    gc = get_sheets_client()
    if not gc: return {}
    try:
        sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
        worksheets = sh.worksheets()
        all_data = {}
        for ws in worksheets:
            data = ws.get_all_values()
            if not data: continue
            df = pd.DataFrame(data)
            header_idx = 0
            max_cols = 0
            for i in range(min(15, len(df))):
                count = sum(1 for x in df.iloc[i] if str(x).strip() != "")
                if count > max_cols:
                    max_cols = count
                    header_idx = i
            headers = df.iloc[header_idx].tolist()
            df['sheet_row'] = df.index + 1 
            df.columns = headers + ['sheet_row']
            df = df.iloc[header_idx+1:].reset_index(drop=True)
            all_data[ws.title] = df
        return all_data
    except: return {}

# --- 4. เริ่มการทำงาน ---
if login():
    # Sidebar แสดงข้อมูลผู้ใช้
    with st.sidebar:
        st.subheader("👤 ข้อมูลผู้ใช้")
        st.success(f"ชื่อ: **{st.session_state.username}**")
        st.info(f"ล็อกอินเมื่อ: {st.session_state.login_time}")
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        st.caption("ระบบ CS Intelligence v2.0")

    st.title("📝 CS Case Intelligence & Editor")
    
    master_data = load_data_for_edit()
    search_val = st.text_input("🔍 ค้นหา ID หรือ IMEI:", placeholder="พิมพ์ข้อมูลที่ต้องการค้นหา...")

    if search_val:
        q = search_val.strip().lower()
        found = False
        for title, df in master_data.items():
            mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(q, na=False).any(), axis=1)
            res = df[mask]
            
            if not res.empty:
                found = True
                st.markdown(f"### 📂 แท็บ: **{title}**")
                # แสดงตารางแบบซ่อนคอลัมน์ระบบ
                st.dataframe(res.drop(columns=['sheet_row']), use_container_width=True, hide_index=True)
                
                with st.expander(f"🛠️ แก้ไขข้อมูลโดยคุณ {st.session_state.username}", expanded=True):
                    col1, col2, col3 = st.columns([1, 1, 0.5])
                    selectable_cols = [c for c in res.columns if c != 'sheet_row']
                    target_col = col1.selectbox(f"เลือกหัวข้อ ({title})", selectable_cols, key=f"sel_{title}")
                    
                    if target_col in DROPDOWN_CONFIG:
                        new_val = col2.selectbox(f"เลือกค่าใหม่:", DROPDOWN_CONFIG[target_col], key=f"val_{title
