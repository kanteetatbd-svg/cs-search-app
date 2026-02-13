import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. ตั้งค่าหน้าตาและการเชื่อมต่อ (รักษาไว้ครบทุกบรรทัด) ---
st.set_page_config(page_title="CS Smart Search & Edit", page_icon="🔍", layout="wide")

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

@st.cache_data(ttl=60)
def load_all_data():
    gc = get_sheets_client()
    sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
    all_tabs = {}
    for ws in sh.worksheets():
        data = ws.get_all_values()
        if not data: continue
        df = pd.DataFrame(data)
        
        # --- [จุดที่เคยหาย] ระบบ Smart Header ค้นหาหัวตารางอัตโนมัติ ---
        header_idx = 0
        for i in range(min(15, len(df))):
            # ถ้าแถวไหนมีข้อมูลมากกว่า 5 คอลัมน์ ให้ถือว่าเป็นหัวตาราง
            if sum(1 for x in df.iloc[i] if str(x).strip() != "") > 5:
                header_idx = i
                break
        
        headers = df.iloc[header_idx].astype(str).tolist()
        
        # --- [จุดที่เคยหาย] ระบบจัดการชื่อคอลัมน์ซ้ำหรือว่าง เพื่อป้องกัน Error ---
        final_headers = []
        for i, h in enumerate(headers):
            clean_h = h.strip()
            if not clean_h or clean_h in final_headers:
                final_headers.append(f"Column_{i+1}")
            else:
                final_headers.append(clean_h)
        
        # เก็บเลขแถวจริง (sheet_row) ไว้ใช้ตอนอัปเดต
        df['sheet_row'] = df.index + 1
        df.columns = final_headers + ['sheet_row']
        
        # ตัดแถวที่เป็น Header ออก และเริ่มเก็บข้อมูลจริง
        all_tabs[ws.title] = df.iloc[header_idx+1:].reset_index(drop=True)
    return all_tabs

# --- 2. เริ่มทำงานเมื่อล็อกอินผ่าน ---
if login():
    with st.sidebar:
        st.markdown("<h2 style='text-align: center;'>👤 โปรไฟล์</h2>", unsafe_allow_html=True)
        
        # จัดวางรูปกึ่งกลางแบบเรียบง่าย ไม่ใช้ CSS ซับซ้อนที่ทำให้พัง
        _, col_img, _ = st.columns([1, 2, 1])
        with col_img:
            if "user_pic" in st.session_state:
                st.image(st.session_state.user_pic, use_container_width=True)
        
        st.markdown(f"<p style='text-align: center; font-size: 18px;'><b>สวัสดี, คุณ {st.session_state.username}</b></p>", unsafe_allow_html=True)
        
        with st.expander("⚙️ ตั้งค่ารูปโปรไฟล์"):
            uploaded_file = st.file_uploader("เลือกรูปภาพใหม่ (JPG/PNG)", type=["jpg", "png", "jpeg"])
            if uploaded_file is not None:
                st.session_state.user_pic = uploaded_file
                st.success("อัปเดตรูปเรียบร้อย!")
                st.rerun()

        st.divider()
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- ส่วนเนื้อหาหลัก (รักษาไว้ครบถ้วน 100%) ---
    st.title("🔍 CS Case Search & Editor")
    
    # ดึงข้อมูลมาเตรียมไว้ใน Cache
    master_data = load_all_data()
    search_val = st.text_input("🔍 ค้นหา ID หรือ IMEI เพื่อแก้ไข:", placeholder="พิมพ์ข้อมูลที่ต้องการค้นหาที่นี่...")

    if search_val:
        q = search_val.strip().lower()
        found_any = False

        for title, df in master_data.items():
            # ตรวจสอบการค้นหาในทุกคอลัมน์ (ยกเว้นเลขแถว)
            mask = df.drop(columns=['sheet_row']).astype(str).apply(lambda r: r.str.lower().str.contains(q).any(), axis=1)
            res_df = df[mask]

            if not res_df.empty:
                found_any = True
                st.markdown(f"### 📂 เจอข้อมูลในแท็บ: **{title}**")
                
                # --- การตั้งค่า Dropdown ตามที่พี่เก็ตต้องการ (การแบน/สถานะ) ---
                editor_config = {
                    "sheet_row": None, # ซ่อนเลขแถวไว้เบื้องหลัง
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

                # แสดงตาราง Editor ที่พิมพ์ทับได้เลย
                edited_df = st.data_editor(
                    res_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=editor_config,
                    key=f"editor_{title}_{search_val}"
                )

                # ปุ่มบันทึกข้อมูลกลับไปยัง Google Sheets
                if st.button(f"💾 ยืนยันการแก้ไขใน {title}", key=f"btn_{title}"):
                    with st.spinner('กำลังเชื่อมต่อ Google Sheets...'):
                        try:
                            gc = get_sheets_client()
                            sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
                            ws = sh.worksheet(title)
                            
                            # วนลูปอัปเดตทีละแถวที่ถูกแก้ไข
                            for _, row in edited_df.iterrows():
                                actual_row = int(row['sheet_row'])
                                updated_values = row.drop('sheet_row').astype(str).tolist()
                                # อัปเดตทั้งแถวเริ่มจากคอลัมน์ A
                                ws.update(f"A{actual_row}", [updated_values])
                            
                            st.toast(f"✅ บันทึกข้อมูลสำเร็จ!", icon="💾")
                            st.cache_data.clear() # ล้าง Cache เพื่อโหลดข้อมูลที่อัปเดตแล้ว
                        except Exception as e:
                            st.error(f"❌ บันทึกไม่สำเร็จ: {e}")
                st.divider()

        if not found_any:
            st.warning(f"ไม่พบข้อมูลสำหรับคำค้นหา: `{search_val}`")
    else:
        st.info("💡 พร้อมใช้งาน! กรุณาพิมพ์ ID หรือ IMEI เพื่อดึงข้อมูลขึ้นมาตรวจสอบและแก้ไข")
