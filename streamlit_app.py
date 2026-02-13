import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="CS Case Finder FINAL", layout="wide")
st.title("🚀 ระบบค้นหาเคส CS")

# --- 1. เชื่อมต่อ Google Sheets โดยตรง (ข้าม BigQuery ที่มีปัญหา) ---
@st.cache_resource
def get_sheets_client():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        # ใช้ไฟล์ key.json ที่พี่อัปโหลดไว้แล้วใน GitHub
        creds = Credentials.from_service_account_file('key.json', scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ กุญแจมีปัญหา: {e}")
        return None

gc = get_sheets_client()
search_val = st.text_input("🔍 กรอก ID หรือ IMEI เพื่อดึงข้อมูล")

if gc and search_val:
    q = search_val.strip().lower()
    try:
        # เปิดไฟล์ด้วยชื่อ (ตรวจสอบชื่อไฟล์ให้ตรงกับในรูป image_981395.jpg)
        sh = gc.open('Copy of ไฟล์เก็บเคส2025V1') 
        worksheets = sh.worksheets()
        found_results = {}

        with st.spinner('🚀 กำลังค้นหา...'):
            for ws in worksheets:
                # ดึงข้อมูลดิบมาทั้งหมด (รวมแถวว่างและ Dashboard)
                data = ws.get_all_values()
                if not data: continue
                
                df = pd.DataFrame(data)
                
                # --- ไม้ตาย: ค้นหา ID/IMEI ในทุกบรรทัดและทุกคอลัมน์ ---
                # แปลงทุกช่องเป็นตัวหนังสือ -> หาคำที่ต้องการ
                mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(q, na=False).any(), axis=1)
                res = df[mask]
                
                if not res.empty:
                    found_results[ws.title] = res

        if found_results:
            st.success(f"✅ เจอข้อมูล `{search_val}` ใน {len(found_results)} แท็บ")
            tabs = st.tabs(list(found_results.keys()))
            for i, (name, res_df) in enumerate(found_results.items()):
                with tabs[i]:
                    st.subheader(f"📂 แท็บ: {name}")
                    # แสดงผลเป็นตารางหน้าตาเหมือนใน Google Sheet เป๊ะๆ
                    st.dataframe(res_df, use_container_width=True, hide_index=True)
        else:
            st.error(f"❌ ไม่พบข้อมูล `{search_val}` ")
            
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
