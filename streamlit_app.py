import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="CS Smart Editor", page_icon="📊", layout="wide")

# --- 1. เชื่อมต่อ (คงความเร็วเดิม) ---
@st.cache_resource
def get_sheets_client():
    creds = Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return gspread.authorize(creds)

def load_data():
    if 'raw_data' not in st.session_state:
        gc = get_sheets_client()
        sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
        all_tabs = {}
        for ws in sh.worksheets():
            data = ws.get_all_values()
            if not data: continue
            df = pd.DataFrame(data)
            
            # ค้นหาหัวตาราง
            header_idx = 0
            for i in range(min(15, len(df))):
                if sum(1 for x in df.iloc[i] if str(x).strip() != "") > 5:
                    header_idx = i; break
            
            headers = df.iloc[header_idx].astype(str).tolist()
            
            # 🎯 จุดแก้: จัดการชื่อคอลัมน์ที่ซ้ำหรือว่าง (Prevent Duplicate/Empty Column Names)
            final_headers = []
            for i, h in enumerate(headers):
                clean_h = h.strip()
                if not clean_h or clean_h in final_headers:
                    final_headers.append(f"Column_{i+1}")
                else:
                    final_headers.append(clean_h)
            
            df = df.iloc[header_idx+1:].reset_index(drop=True)
            df.columns = final_headers
            all_tabs[ws.title] = df
        st.session_state.raw_data = all_tabs
    return st.session_state.raw_data

# --- 2. ฟังก์ชันบันทึก ---
def save_changes(tab_name, edited_df):
    try:
        gc = get_sheets_client()
        sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
        ws = sh.worksheet(tab_name)
        # เขียนทับข้อมูลทั้งหมดเริ่มจากแถว 2 (ใต้ Header)
        data_to_update = edited_df.astype(str).values.tolist()
        ws.update('A2', data_to_update)
        st.toast(f"✅ บันทึกแท็บ {tab_name} เรียบร้อย!", icon="💾")
    except Exception as e:
        st.error(f"❌ บันทึกไม่สำเร็จ: {e}")

# --- 3. หน้าจอหลัก ---
st.title("📊 CS Case Real-time Editor")
st.caption("คลิกพิมพ์แก้ไขในตารางได้เลยเหมือน Google Sheets")

try:
    all_data = load_data()
    tabs = st.tabs(list(all_data.keys()))

    for i, (tab_name, df) in enumerate(all_data.items()):
        with tabs[i]:
            st.subheader(f"ไฟล์: {tab_name}")
            
            # แสดง Editor แบบพิมพ์แก้ไขได้
            edited_df = st.data_editor(
                df, 
                use_container_width=True, 
                num_rows="dynamic",
                key=f"editor_{tab_name}"
            )
            
            if st.button(f"💾 บันทึก {tab_name}", key=f"btn_{tab_name}"):
                with st.spinner('กำลังบันทึก...'):
                    save_changes(tab_name, edited_df)
                    st.session_state.raw_data[tab_name] = edited_df
except Exception as e:
    st.error(f"ระบบขัดข้อง: {e}")
    if st.button("🔄 ลองรีโหลดข้อมูลใหม่"):
        if 'raw_data' in st.session_state: del st.session_state.raw_data
        st.rerun()
