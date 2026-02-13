import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. ตั้งค่าหน้าตาและการเชื่อมต่อ (รักษาไว้ครบทุกบรรทัด) ---
st.set_page_config(page_title="CS Smart Search & Edit", page_icon="🔍", layout="wide")

# CSS ตกแต่งให้ Sidebar ดูดีขึ้น (Avatar วงกลม)
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    .profile-img {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #4CAF50;
        margin-bottom: 10px;
    }
    .user-name {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

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
        
        header_idx = 0
        for i in range(min(15, len(df))):
            if sum(1 for x in df.iloc[i] if str(x).strip() != "") > 5:
                header_idx = i; break
        
        headers = df.iloc[header_idx].astype(str).tolist()
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
        # ส่วนโปรไฟล์ที่ปรับปรุงใหม่ (ไม่ทุเรศแล้วพี่!)
        st.markdown(f'<div style="text-align: center;"><img src="{"https://cdn-icons-png.flaticon.com/512/3135/3135715.png" if isinstance(st.session_state.user_pic, str) else "data:image/png;base64,..."}" class="profile-img"></div>', unsafe_allow_html=True)
        # กรณีอัปโหลดรูปใหม่
        if not isinstance(st.session_state.user_pic, str):
            st.image(st.session_state.user_pic, width=100)
            
        st.markdown(f'<div style="text-align: center;" class="user-name">สวัสดี, คุณ {st.session_state.username}</div>', unsafe_allow_html=True)
        
        with st.expander("⚙️ ตั้งค่าโปรไฟล์"):
            uploaded_file = st.file_uploader("เปลี่ยนรูปโปรไฟล์", type=["jpg", "png", "jpeg"])
            if uploaded_file is not None:
                st.session_state.user_pic = uploaded_file
                st.success("อัปเดตรูปแล้ว!")
                st.rerun()

        st.divider()
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- ส่วนเนื้อหาหลัก (รักษาไว้ครบถ้วน 100%) ---
    st.title("🔍 CS Case Search & Editor")
    
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
                
                editor_config = {
                    "sheet_row": None, 
                    "การแบน": st.column_config.SelectboxColumn("การแบน", options=["ปลด", "แบน", "รอตรวจสอบ"], required=True),
                    "สถานะ": st.column_config.SelectboxColumn("สถานะ", options=["ปกติ", "ไม่ปกติ", "รอดำเนินการ"], required=True)
                }

                edited_df = st.data_editor(res_df, use_container_width=True, hide_index=True, column_config=editor_config, key=f"editor_{title}_{search_val}")

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
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"❌ พัง: {e}")
