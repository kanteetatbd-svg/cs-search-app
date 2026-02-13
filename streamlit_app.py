import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. การตั้งค่าหน้าตา ---
st.set_page_config(page_title="CS Case Intelligence", page_icon="📝", layout="wide")

# --- 🎯 ระบบจัดการผู้ใช้ ---
USER_DB = {
    "admin": "1234",
    "get": "5566",
    "staff_01": "7788"
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
    except: return None

@st.cache_data(ttl=60)
def load_data_for_edit():
    gc = get_sheets_client()
    if not gc: return {}
    try:
        sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
        all_data = {}
        for ws in sh.worksheets():
            values = ws.get_all_values()
            if not values: continue
            df = pd.DataFrame(values)
            # ระบบ Smart Header ค้นหาหัวตาราง
            header_idx = 0
            max_c = 0
            for i in range(min(15, len(df))):
                count = sum(1 for x in df.iloc[i] if str(x).strip() != "")
                if count > max_c: max_c = count; header_idx = i
            headers = df.iloc[header_idx].tolist()
            df['sheet_row'] = df.index + 1 
            df.columns = headers + ['sheet_row']
            all_data[ws.title] = df.iloc[header_idx+1:].reset_index(drop=True)
        return all_data
    except: return {}

# --- 4. เริ่มการทำงาน ---
if login():
    with st.sidebar:
        st.success(f"👤 ผู้ใช้: **{st.session_state.username}**")
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.title("📝 CS Case Intelligence & Editor")
    master_data = load_data_for_edit()
    search_val = st.text_input("🔍 ค้นหา ID หรือ IMEI:", placeholder="ระบุเลขที่ต้องการค้นหา...")

    if search_val:
        q = search_val.strip().lower()
        found = False
        for title, df in master_data.items():
            mask = df.astype(str).apply(lambda r: r.str.lower().str.contains(q, na=False).any(), axis=1)
            res = df[mask]
            if not res.empty:
                found = True
                st.markdown(f"### 📂 แท็บ: {title}")
                st.dataframe(res.drop(columns=['sheet_row']), use_container_width=True, hide_index=True)
                
                with st.expander(f"🛠️ แก้ไขข้อมูล (พิมพ์เองทุกช่อง)", expanded=True):
                    c1, c2, c3 = st.columns([1, 1, 0.5])
                    
                    # เลือกคอลัมน์ที่จะแก้
                    selectable_cols = [c for c in res.columns if c != 'sheet_row']
                    target_col = c1.selectbox(f"เลือกหัวข้อ", selectable_cols, key=f"sel_{title}")
                    
                    # 🎯 พิมพ์เองทุกอย่าง ไม่มี Dropdown แล้วครับพี่
                    new_val = c2.text_input(f"พิมพ์ค่าใหม่สำหรับ {target_col}:", key=f"inp_{title}")
                    
                    if c3.button("💾 บันทึกข้อมูล", key=f"btn_{title}"):
                        row_idx = int(res.iloc[0]['sheet_row'])
                        with st.spinner('กำลังบันทึก...'):
                            try:
                                gc = get_sheets_client()
                                sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
                                ws = sh.worksheet(title)
                                # ค้นหาเลขคอลัมน์จากหัวตารางแถวที่ 1
                                col_idx = ws.row_values(1).index(target_col) + 1
                                ws.update_cell(row_idx, col_idx, new_val)
                                st.success(f"✅ บันทึกสำเร็จ! คุณ {st.session_state.username} แก้ไขเป็น: {new_val}")
                                st.cache_data.clear()
                            except Exception as e:
                                st.error(f"❌ ไม่สำเร็จ: {e}")
