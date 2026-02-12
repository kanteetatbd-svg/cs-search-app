import streamlit as st
import pandas as pd

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="CS Search System", layout="wide")

st.title("🚀 ระบบค้นหาข้อมูล CS (Version 1.0)")
st.markdown("---")

# 2. ลิงก์ไฟล์ Google Sheets (ปรับปรุงให้ดึงข้อมูลได้แม่นยำขึ้น)
sheet_url = "https://docs.google.com/spreadsheets/d/1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA/export?format=xlsx"

@st.cache_data
def load_data():
    # ใช้ลิงก์ดาวน์โหลดตรง เพื่อลดปัญหา HTTPError
    return pd.read_excel(sheet_url, sheet_name=None, engine='openpyxl')

all_sheets = load_data()

# 3. ส่วนของ Filter และช่องค้นหา
col1, col2 = st.columns(2)

with col1:
    tab_choice = st.selectbox("📂 เลือกแท็บหลักที่ต้องการค้นหา:", list(all_sheets.keys()))

with col2:
    search_query = st.text_input("🔍 พิมพ์ ID หรือ IMEI เพื่อค้นหา:", placeholder="กรอกข้อมูลที่นี่...")

st.markdown("---")

# 4. ส่วนแสดงผลตารางข้อมูล
if search_query:
    df = all_sheets[tab_choice]
    # ค้นหาคำที่ต้องการจากทุกช่องในแท็บนั้น
    result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
    
    if not result.empty:
        st.success(f"✅ พบข้อมูลในแท็บ {tab_choice}")
        st.dataframe(result, use_container_width=True)
    else:
        st.warning("❌ ไม่พบข้อมูลที่ท่านต้องการ")
else:
    st.info("💡 กรุณาเลือกแท็บและพิมพ์ข้อมูลเพื่อเริ่มต้นการค้นหา")
