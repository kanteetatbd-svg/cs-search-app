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
            # หาหัวตาราง
            header_idx = 0
            for i in range(min(15, len(df))):
                if sum(1 for x in df.iloc[i] if str(x).strip() != "") > 5:
                    header_idx = i; break
            headers = df.iloc[header_idx].tolist()
            df = df.iloc[header_idx+1:].reset_index(drop=True)
            df.columns = headers
            all_tabs[ws.title] = df
        st.session_state.raw_data = all_tabs
    return st.session_state.raw_data

# --- 2. ฟังก์ชันบันทึกการเปลี่ยนแปลง ---
def save_changes(tab_name, edited_df):
    try:
        gc = get_sheets_client()
        sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
        ws = sh.worksheet(tab_name)
        
        # กองข้อมูลทั้งหมดเตรียมเขียนทับ (วิธีนี้ชัวร์และง่ายสุดถ้าตารางไม่ใหญ่ยักษ์)
        # เราจะเขียนเริ่มจากแถวที่ 2 (ต่อจากหัวตาราง)
        data_to_update = edited_df.values.tolist()
        ws.update('A2', data_to_update)
        st.toast(f"✅ บันทึกแท็บ {tab_name} เรียบร้อย!", icon="💾")
    except Exception as e:
        st.error(f"❌ บันทึกไม่สำเร็จ: {e}")

# --- 3. หน้าจอหลัก ---
st.title("📊 CS Case Real-time Editor")
st.caption("พิมพ์แก้ไขในตารางได้เลยเหมือน Google Sheets แล้วกด Save ด้านล่าง")

all_data = load_data()

# สร้าง Tabs ตามชื่อใน Google Sheets
tabs = st.tabs(list(all_data.keys()))

for i, (tab_name, df) in enumerate(all_data.items()):
    with tabs[i]:
        st.subheader(f"ไฟล์: {tab_name}")
        
        # 🎯 ไม้ตาย: st.data_editor ทำให้ตารางพิมพ์แก้ได้เหมือน Excel
        edited_df = st.data_editor(
            df, 
            use_container_width=True, 
            num_rows="dynamic", # เพิ่ม/ลบ แถวได้ด้วย
            key=f"editor_{tab_name}"
        )
        
        # ปุ่มบันทึกแยกตามแท็บ
        if st.button(f"💾 บันทึกการแก้ไขใน {tab_name}", key=f"btn_{tab_name}"):
            with st.spinner('กำลังซิงค์ข้อมูลกับ Google Sheets...'):
                save_changes(tab_name, edited_df)
                st.session_state.raw_data[tab_name] = edited_df # อัปเดตข้อมูลในแอปด้วย
