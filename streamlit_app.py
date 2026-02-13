import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

st.set_page_config(page_title="CS Smart Search & Edit", page_icon="🔍", layout="wide")

# --- 🎯 1. ระบบจัดการผู้ใช้ (เพิ่มโครงสร้างเก็บรูปโปรไฟล์) ---
# พี่เก็ตสามารถเปลี่ยน URL รูปภาพในเครื่องหมายคำพูดได้เลยครับ
USER_DB = {
    "get": {
        "password": "5566", 
        "profile_pic": "https://i.imgur.com/G34g25K.png" # รูปพี่เก็ต
    },
    "admin": {
        "password": "1234", 
        "profile_pic": "https://i.imgur.com/O6S3Jd4.png" # รูปแอดมิน
    },
    "staff_cs": {
        "password": "9999", 
        "profile_pic": "https://i.imgur.com/8Q9S71V.png" # รูปทีมงาน
    }
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
                    # ดึงรูปโปรไฟล์มาเก็บไว้ใน Session
                    st.session_state.profile_pic = USER_DB[user]["profile_pic"]
                    st.rerun()
                else:
                    st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        return False
    return True

# --- 2. การเชื่อมต่อข้อมูล (คงเดิม) ---
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
        # ✅ แสดงรูปโปรไฟล์ (ตรวจสอบก่อนว่ามีข้อมูลใน Session ไหม)
        if "profile_pic" in st.session_state:
            st.image(st.session_state.profile_pic, width=100)
        
        st.success(f"👤 ผู้ใช้: **{st.session_state.username}**")
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        st.caption("CS Intelligence System v3.0")

    st.title("🔍 CS Case Search & Editor")
    
    # ดึงข้อมูลทันทีหลัง Login ตามที่พี่เข้าใจ
    master_data = load_all_data()
    
    search_val = st.text_input("🔍 ค้นหา ID หรือ IMEI เพื่อแก้ไข:", placeholder="พิมพ์ข้อมูลที่นี่...")

    if search_val:
        q = search_val.strip().lower()
        found_any = False

        for title, df in master_data.items():
            mask = df.drop(columns=['sheet_row']).astype(str).apply(lambda r: r.str.lower().str.contains(q).any(), axis=1)
            res_df = df[mask]

            if not res_df.empty:
                found_any = True
                st.markdown(f"### 📂 เจอข้อมูลในแท็บ: **{title}**")
                
                # 🎯 ระบบ Dropdown สำหรับคอลัมน์ "การแบน" และ "สถานะ"
                editor_config = {
                    "sheet_row": None, # ซ่อนเลขแถว
                    "การแบน": st.column_config.SelectboxColumn(
                        "การแบน",
                        options=["ปลด", "แบน", "รอตรวจสอบ"],
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
                    column_config=editor_config,
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
                            
                            st.toast(f"✅ บันทึกสำเร็จ!", icon="💾")
                            st.cache_data.clear() # ล้างแคชเพื่อให้เห็นข้อมูลล่าสุด
                        except Exception as e:
                            st.error(f"❌ บันทึกไม่สำเร็จ: {e}")
                st.divider()

        if not found_any:
            st.warning(f"ไม่พบข้อมูลสำหรับ `{search_val}`")
    else:
        st.info("💡 พิมพ์เลข ID หรือ IMEI เพื่อเริ่มดึงข้อมูลมาแก้ไขครับ")
