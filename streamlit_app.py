import streamlit as st
import pandas as pd
from gspread_pandas import Spread

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 20.0 - ตรวจสอบสิทธิ์)")

# ดึงกุญแจลับ
@st.cache_resource
def get_config():
    try:
        conf = dict(st.secrets["gcp_service_account"])
        conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        return conf
    except Exception as e:
        return None

config = get_config()

# ID ไฟล์ใหม่จากรูป URL ของพี่ (ผมแก้พิมพ์เล็ก-ใหญ่ให้ตรงเป๊ะแล้วครับ)
# -> 181PeVc4z0Vk6Y7YrTKujX5non-Dlyx5cah2wnCCPn_o
sheet_id = "181PeVc4z0Vk6Y7YrTKujX5non-Dlyx5cah2wnCCPn_o"

# แถบด้านข้างสำหรับเช็คความถูกต้อง
st.sidebar.header("🔍 ตรวจสอบสิทธิ์การเข้าถึง")
if config:
    st.sidebar.write(f"**1. อีเมลบอทที่แอปใช้:**")
    st.sidebar.code(config['client_email'])
    st.sidebar.write(f"**2. ID ไฟล์ที่แอปเรียก:**")
    st.sidebar.code(sheet_id)
    st.sidebar.warning("⚠️ พี่ต้องก๊อปปี้เมลบอทด้านบน ไปกด 'แชร์' ในไฟล์ Sheets ใหม่ด้วยนะครับ!")

@st.cache_data(ttl=300)
def load_all_data(_config, _id):
    try:
        spread = Spread(_id, config=_config)
        return {s.title: spread.sheet_to_df(index=0, sheet=s.title) for s in spread.sheets}
    except Exception as e:
        return str(e)

if config:
    all_sheets = load_all_data(config, sheet_id)
    
    if isinstance(all_sheets, str):
        st.error(f"❌ ยังเชื่อมต่อไม่ได้: {all_sheets}")
        if "not found" in all_sheets.lower():
            st.info("💡 คำแนะนำ: แอปหาไฟล์ไม่เจอ หรือบอทไม่มีสิทธิ์เข้าถึง พี่ลองเช็คปุ่ม 'แชร์' ใน Sheets อีกรอบนะ")
    elif all_sheets:
        tab_list = list(all_sheets.keys())
        selected_tab = st.selectbox("📂 เลือกหมวดหมู่:", tab_list)
        search_query = st.text_input(f"🔍 ค้นหาในหมวด [{selected_tab}]:")
        
        if search_query:
            df = all_sheets[selected_tab]
            result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
            if not result.empty:
                st.success(f"✅ พบข้อมูล {len(result)} รายการ")
                st.dataframe(result, use_container_width=True)
            else:
                st.warning("❌ ไม่พบข้อมูล")
        else:
            st.info(f"💡 กำลังแสดงข้อมูลแท็บ: {selected_tab}")
            st.dataframe(all_sheets[selected_tab].head(10))
