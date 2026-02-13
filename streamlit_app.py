import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. การตั้งค่าหน้าตาและการเชื่อมต่อ (รักษาไว้ครบทุกบรรทัด) ---
st.set_page_config(page_title="CS Smart Search & Edit", page_icon="🔍", layout="wide")

# 🎯 ฟังก์ชันจัดการ Theme (กลางวัน/กลางคืน)
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

# --- 🎯 ระบบจัดการผู้ใช้ ---
USER_DB = {
    "get": {"password": "5566", "default_pic": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"},
    "admin": {"password": "1234", "default_pic": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"}
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
                    if "user_pic" not in st.session_state:
                        st.session_state.user_pic = USER_DB[user]["default_pic"]
                    st.rerun()
                else:
                    st.error("❌ Username หรือ Password ผิด")
        return False
    return True

@st.cache_resource
def get_sheets_client():
    creds = Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return gspread.authorize(creds)

# 🚀 [Restored Section] ระบบโหลดข้อมูลพร้อม Smart Header และการจัดการคอลัมน์ซ้ำ
@st.cache_data(ttl=3600)
def load_all_data():
    gc = get_sheets_client()
    sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
    all_tabs = {}
    for ws in sh.worksheets():
        data = ws.get_all_values()
        if not data: continue
        df = pd.DataFrame(data)
        
        # --- [จุดที่เคยหาย 1] วนลูปหาแถวที่เป็นหัวตาราง (Smart Header) ---
        header_idx = 0
        for i in range(min(15, len(df))):
            # นับจำนวนช่องที่มีข้อมูล ถ้าเกิน 5 ช่อง ให้ถือว่าเป็นหัวตาราง
            non_empty_count = sum(1 for x in df.iloc[i] if str(x).strip() != "")
            if non_empty_count > 5:
                header_idx = i
                break
        
        headers = df.iloc[header_idx].astype(str).tolist()
        
        # --- [จุดที่เคยหาย 2] ระบบจัดการชื่อคอลัมน์ซ้ำหรือว่าง (Duplicate Handler) ---
        final_headers = []
        for i, h in enumerate(headers):
            clean_h = h.strip()
            if not clean_h or clean_h in final_headers:
                final_headers.append(f"Column_{i+1}")
            else:
                final_headers.append(clean_h)
        
        # เก็บเลขแถวจริง (sheet_row) ไว้ใช้ตอนอัปเดตข้อมูล
        df['sheet_row'] = df.index + 1
        df.columns = final_headers + ['sheet_row']
        
        # เก็บข้อมูลจริงโดยตัดแถวหัวตารางทิ้งไป
        all_tabs[ws.title] = df.iloc[header_idx+1:].reset_index(drop=True)
    return all_tabs

# --- 2. เริ่มทำงานเมื่อล็อกอินผ่าน ---
if login():
    with st.sidebar:
        # ส่วนรูปโปรไฟล์ใหญ่ขึ้น และไม่มีคำว่าโปรไฟล์
        st.write("") 
        _, col_img, _ = st.columns([0.1, 2.5, 0.1])
        with col_img:
            if "user_pic" in st.session_state:
                st.image(st.session_state.user_pic, use_container_width=True)
        
        st.markdown(f"<h3 style='text-align: center;'>คุณ {st.session_state.username}</h3>", unsafe_allow_html=True)
        
        # ปุ่มเปลี่ยนโหมด (รักษาฟังก์ชันเดิม)
        theme_icon = "☀️" if st.session_state.theme == "dark" else "🌙"
        if st.button(f"{theme_icon} เปลี่ยนโหมดธีม", use_container_width=True):
            toggle_theme()
            st.rerun()

        # ปุ่มรีเฟรชข้อมูล (Sync) เพื่อดึงจาก Google Sheets ใหม่
        if st.button("🔄 รีเฟรชข้อมูล (Sync)", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        with st.expander("⚙️ ตั้งค่ารูปโปรไฟล์"):
            uploaded_file = st.file_uploader("เลือกรูปภาพใหม่", type=["jpg", "png", "jpeg"])
            if uploaded_file is not None:
                st.session_state.user_pic = uploaded_file
                st.rerun()

        st.divider()
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- ส่วนเนื้อหาหลัก: ค้นหาและแก้ไข ---
    st.title("🔍 CS Case Instant Search")
    
    # ดึงข้อมูลมาเตรียมไว้ (เพื่อให้ค้นหาเจอทันที)
    with st.status("📡 กำลังเตรียมข้อมูลเพื่อการค้นหาที่รวดเร็ว...", expanded=False) as status:
        master_data = load_all_data()
        status.update(label="✅ ข้อมูลพร้อมใช้งาน! ค้นหาได้ทันที", state="complete")

    search_val = st.text_input("🔍 ค้นหา ID หรือ IMEI:", placeholder="พิมพ์ข้อมูลแล้วผลลัพธ์จะเด้งขึ้นมาทันที...")

    if search_val:
        q = search_val.strip().lower()
        found_any = False

        for title, df in master_data.items():
            # ค้นหาในหน่วยความจำ (Instant Search)
            mask = df.drop(columns=['sheet_row']).astype(str).apply(lambda r: r.str.lower().str.contains(q).any(), axis=1)
            res_df = df[mask]

            if not res_df.empty:
                found_any = True
                st.markdown(f"### 📂 เจอข้อมูลในแท็บ: **{title}**")
                
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
                    key=f"editor_{title}_{search_val}"
                )

                if st.button(f"💾 บันทึกแก้ไข {title}", key=f"btn_{title}"):
                    with st.spinner('กำลังเซฟข้อมูล...'):
                        try:
                            gc = get_sheets_client()
                            sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
                            ws = sh.worksheet(title)
                            for _, row in edited_df.iterrows():
                                actual_row = int(row['sheet_row'])
                                updated_values = row.drop('sheet_row').astype(str).tolist()
                                ws.update(f"A{actual_row}", [updated_values])
                            st.toast("✅ บันทึกสำเร็จ!", icon="💾")
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"❌ พัง: {e}")
                st.divider()

        if not found_any:
            st.warning(f"ไม่พบข้อมูลสำหรับ `{search_val}`")
