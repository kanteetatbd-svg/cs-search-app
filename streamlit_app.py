import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

st.set_page_config(page_title="CS Smart Search & Edit", page_icon="🔍", layout="wide")

# --- 🎯 1. ระบบจัดการผู้ใช้ (เหมือนเดิม) ---
USER_DB = {
    "get": {"password": "5566", "profile_pic": "https://i.imgur.com/G34g25K.png"},
    "admin": {"password": "1234", "profile_pic": "https://i.imgur.com/O6S3Jd4.png"}
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
                if user in USER_DB and USER_DB[user]["password"] == pw:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.profile_pic = USER_DB[user]["profile_pic"]
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
        st.image(st.session_state.profile_pic, width=80)
        st.success(f"👤 ผู้ใช้: **{st.session_state.username}**")
        if st.button("🚪 ออกจากระบบ"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("🔍 CS Case Search & Editor")
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
                
                # 🎯 ส่วนที่เพิ่ม: ตั้งค่า Dropdown ให้กับคอลัมน์ที่ต้องการ
                # พี่สามารถเพิ่มชื่อคอลัมน์ที่ต้องการให้เป็น Dropdown ได้ที่นี่ครับ
                editor_config = {
                    "sheet_row": None, # ซ่อนเลขแถวเหมือนเดิม
                    "การแบน": st.column_config.SelectboxColumn(
                        "การแบน",
                        help="เลือกสถานะการแบน",
                        options=["ปลด", "แบน", "รอตรวจสอบ"], # ใส่ตัวเลือกตามใน Google Sheets เลยครับ
                        required=True,
                    ),
                    "สถานะ": st.column_config.SelectboxColumn(
                        "สถานะ",
                        options=["ปกติ", "ไม่ปกติ", "รอดำเนินการ"],
                        required=True,
                    )
                }

                edited_df = st.data_editor(
                    res_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=editor_config, # ใช้การตั้งค่าที่เรากำหนดไว้ด้านบน
                    key=f"editor_{title}_{search_val}"
                )

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
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"❌ บันทึกไม่สำเร็จ: {e}")
                st.divider()

        if not found_any:
            st.warning(f"ไม่พบข้อมูลสำหรับ `{search_val}`")
