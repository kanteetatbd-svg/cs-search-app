import streamlit as st
import pandas as pd
import json
from gspread_pandas import Spread

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 3.1)")

# ดึงกุญแจลับจาก Secrets
try:
    # ดึงค่า json_key ที่เราตั้งไว้ใน Secrets
    secret_json = st.secrets["gcp_service_account"]["json_key"]
    config = json.loads(secret_json)
    sheet_id = "1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA"

    @st.cache_data
    def load_data():
        spread = Spread(sheet_id, config=config)
        # ดึงทุกแท็บ (Sheet) ในไฟล์มาเก็บไว้
        return {s.title: spread.sheet_to_df(index=0, sheet=s.title) for s in spread.sheets}

    all_sheets = load_data()

    # ส่วนแสดงผลหน้าเว็บ
    tab_choice = st.selectbox("📂 เลือกแท็บหลัก:", list(all_sheets.keys()))
    search_query = st.text_input("🔍 พิมพ์ข้อมูลเพื่อค้นหา (ID, IMEI, หรือชื่อ):")

    if search_query:
        df = all_sheets[tab_choice]
        # ค้นหาคำจากทุกช่องในตาราง
        result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
        
        if not result.empty:
            st.success(f"✅ พบข้อมูล {len(result)} รายการ")
            st.dataframe(result, use_container_width=True)
        else:
            st.warning("❌ ไม่พบข้อมูล")
    else:
        st.info("💡 กรุณาเลือกแท็บและพิมพ์สิ่งที่ต้องการค้นหาด้านบน")

except Exception as e:
    st.error(f"ยังเชื่อมต่อไม่ได้: {e}")
    st.info("ตรวจสอบว่าใน Secrets มีบรรทัด json_key = ''' หรือยัง")
