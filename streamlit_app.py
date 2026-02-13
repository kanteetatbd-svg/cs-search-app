import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

st.set_page_config(page_title="CS Smart Search & Edit", page_icon="🔍", layout="wide")

# --- 🎯 1. ระบบจัดการผู้ใช้ (ล็อกอินแบบเสถียร ไม่ต้องใช้ Google Cloud) ---
USER_DB = {
    "get": "5566",
    "admin": "1234",
    "staff_cs": "9999"
}

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.title("🔐 ระบบจัดการเคสพนักงาน (Login)")
        with st.form("login_form"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("เข้าสู่ระบบ"):
                if user in USER_DB and USER_DB[user] == pw:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.rerun()
                else:
                    st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        return False
    return True

# --- 2. การเชื่อมต่อข้อมูล ---
@st.cache_resource
def get_sheets_client():
    creds = Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return gspread.authorize(creds)

@st.cache_data(ttl=60)
def load_all_data():
    gc = get_sheets_client()
    sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
    all_tabs = {}
    for ws in sh.worksheets():
        data = ws.get_all_values()
        if not data: continue
        df = pd.DataFrame(data)
        # Smart Header
        header_idx = 0
        for i in range(min(15, len(df))):
            if sum(1 for x in df.iloc[i] if str(x).strip() != "") > 5:
                header_idx = i; break
        headers = df.iloc[header_idx].astype(str).tolist()
        df['sheet_row'] = df.index + 1
        df.columns = headers + ['sheet_row']
        all_tabs[ws.title] = df.iloc[header_idx+1:].reset_index(drop=True)
    return all_tabs

# --- 3. เริ่มทำงานเมื่อล็อกอินผ่านแล้ว ---
if login():
    with st.sidebar:
        st.success(f"👤 ผู้ใช้: **{st.session_state.username}**")
        if st.button("🚪 ออกจากระบบ"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("🔍 CS Case Search & Editor")
    
    # 🎯 ขั้นตอนที่ 1: ค้นหาก่อน
    search_val = st.text_input("🔍 ค้นหา ID หรือ IMEI เพื่อดึงข้อมูลมาแก้ไข:")

    if search_val:
        master_data = load_all_data()
        q = search_val.strip().lower()
        found_any = False

        for title, df in master_data.items():
            mask = df.drop(columns=['sheet_row']).astype(str).apply(lambda r: r.str.lower().str.contains(q).any(), axis=1)
            res_df = df[mask]

            if not res_df.empty:
                found_any = True
                st.markdown(f"### 📂 เจอข้อมูลในแท็บ: **{title}**")
                
                # 🎯 ขั้นตอนที่ 2: ดึงมาเป็นหน้าต่างแก้ไขเหมือน Google Sheets เฉพาะแถวที่เจอ
                edited_df = st.data_editor(
                    res_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={"sheet_row": None}, # ซ่อนเลขแถวไว้เบื้องหลัง
                    key=f"editor_{title}_{search_val}"
                )

                # 🎯 ขั้นตอนที่ 3: ปุ่มบันทึก (เร็วขึ้น ไม่ต้องรีโหลดใหม่ทั้งหมด)
                if st.button(f"💾 บันทึกการแก้ไขใน {title}", key=f"btn_{title}"):
                    with st.spinner('กำลังบันทึก...'):
                        try:
                            gc = get_sheets_client()
                            sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
                            ws = sh.worksheet(title)
                            for _, row in edited_df.iterrows():
                                actual_row = int(row['sheet_row'])
                                updated_values = row.drop('sheet_row').astype(str).tolist()
                                ws.update(f"A{actual_row}", [updated_values])
                            
                            st.toast(f"✅ บันทึกแท็บ {title} เรียบร้อย!", icon="💾")
                            st.cache_data.clear() # ล้างความจำเพื่อให้เห็นค่าใหม่
                        except Exception as e:
                            st.error(f"❌ บันทึกไม่สำเร็จ: {e}")
                st.divider()

        if not found_any:
            st.warning(f"ไม่พบข้อมูลสำหรับ `{search_val}`")
    else:
        st.info("💡 พิมพ์เลข ID เพื่อดึงตารางออกมาแก้ไขครับ")
