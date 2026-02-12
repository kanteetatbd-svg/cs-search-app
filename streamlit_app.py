import streamlit as st
import pandas as pd
import json
from gspread_pandas import Spread

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 3.0)")

# 2. ดึงกุญแจลับจาก Secrets
try:
    secret_json = st.secrets["gcp_service_account"]["json_key"]
    config = json.loads(secret_json)
    sheet_id = "1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA"

    @st.cache_data
    def load_data_securely():
        spread = Spread(sheet_id, config=config)
        # ดึงทุกแท็บมาแสดงเป็นตัวเลือก
        all_data = {sheet.title: spread.sheet_to_df(index=0, sheet=sheet.title) for sheet in spread.sheets}
        return all_data

    all_sheets = load_data_securely()

    # 3. ส่วนแสดงหน้าจอค้นหา
    tab_choice = st.selectbox("📂 เลือกแท็บที่ต้องการค้นหา:", list(all_sheets.keys()))
    search_query = st.text_input("🔍 พิมพ์ข้อมูลเพื่อค้นหา (ID, IMEI, หรือชื่อ):")

    if search_query:
        df = all_sheets[tab_choice]
        # ค้นหาทุกคอลัมน์
        result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
        
        if not result.empty:
            st.success(f"✅ พบข้อมูล {len(result)} รายการ")
            st.dataframe(result, use_container_width=True)
        else:
            st.warning("❌ ไม่พบข้อมูลที่ต้องการ")
    else:
        st.info("💡 กรุณาเลือกแท็บและพิมพ์สิ่งที่ต้องการค้นหาด้านบน")

except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
    st.info("ตรวจสอบว่าได้แปะ Secrets ถูกต้องและแชร์ไฟล์ Google Sheets ให้ Email ของ Service Account หรือยัง")
