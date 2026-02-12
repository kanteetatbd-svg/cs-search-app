import streamlit as st
import pandas as pd
from gspread_pandas import Spread

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 22.0 - สำเร็จแล้ว!)")

@st.cache_resource
def get_config():
    try:
        conf = dict(st.secrets["gcp_service_account"])
        conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        return conf
    except Exception as e:
        return None

config = get_config()
# ID ที่ถูกต้องแม่นยำจากรูป image_0c27df.jpg ครับ
sheet_id = "181PeVc4z0Vk6Y7YrTKujX5non-Dlyx5cah2wnCCPn_o" 

@st.cache_data(ttl=300)
def load_all_data(_config, _id):
    try:
        spread = Spread(_id, config=_config)
        # ดึงทุกแท็บ (Case2025 และแท็บอื่นๆ ทั้งหมดที่พี่มี)
        return {s.title: spread.sheet_to_df(index=0, sheet=s.title) for s in spread.sheets}
    except Exception as e:
        return str(e)

if config:
    all_sheets = load_all_data(config, sheet_id)
    
    if isinstance(all_sheets, str):
        st.error(f"❌ ยังเข้าไฟล์ไม่ได้: {all_sheets}")
        st.info("💡 พี่แก้ ID ใน GitHub แล้วกด Reboot app อีกรอบนะ")
    elif all_sheets:
        tab_list = list(all_sheets.keys())
        # แสดงรายชื่อแท็บทั้งหมดที่พี่มี
        selected_tab = st.selectbox("📂 เลือกหมวดหมู่ (แท็บ):", tab_list)
        
        search_query = st.text_input(f"🔍 ค้นหาในหมวด [{selected_tab}]:")
        
        df = all_sheets[selected_tab]
        if search_query:
            result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
            if not result.empty:
                st.success(f"✅ พบข้อมูล {len(result)} รายการ")
                st.dataframe(result, use_container_width=True)
            else:
                st.warning("❌ ไม่พบข้อมูล")
        else:
            st.info(f"💡 กำลังแสดงข้อมูลในแท็บ: {selected_tab}")
            st.dataframe(df.head(20))
