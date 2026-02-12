import streamlit as st
import pandas as pd
from gspread_pandas import Spread

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 18.0 - ทดสอบไฟล์ใหม่)")

@st.cache_resource
def get_config():
    try:
        conf = dict(st.secrets["gcp_service_account"])
        conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        return conf
    except Exception as e:
        st.error(f"ปัญหาที่ Secrets: {e}")
        return None

config = get_config()
# ใส่ ID ของไฟล์ที่ Duplicate มาใหม่ตรงนี้ครับพี่!
sheet_id = "181PeVc4z0Vk6Y7YrTKujX5non-Dlyx5cah2wnCCPn_o"

@st.cache_data(ttl=300)
def load_all_data(_config):
    if not _config: return None
    try:
        spread = Spread(sheet_id, config=_config)
        return {s.title: spread.sheet_to_df(index=0, sheet=s.title) for s in spread.sheets}
    except Exception as e:
        return str(e)

if config:
    all_sheets = load_all_data(config)
    
    if isinstance(all_sheets, str):
        st.error(f"❌ ยังเชื่อมต่อไม่ได้: {all_sheets}")
        st.info("💡 พี่อย่าลืมแชร์ไฟล์ใหม่ให้เมล cs-search-key@... ด้วยนะครับ!")
    elif all_sheets:
        tab_list = list(all_sheets.keys())
        selected_tab = st.selectbox("📂 เลือกหมวดหมู่ที่ต้องการค้นหา:", tab_list)
        
        search_query = st.text_input(f"🔍 ค้นหาในหมวด [{selected_tab}] (พิมพ์สิ่งที่ต้องการหา):")
        
        if search_query:
            df = all_sheets[selected_tab]
            result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
            if not result.empty:
                st.success(f"✅ พบข้อมูล {len(result)} รายการ")
                st.dataframe(result, use_container_width=True)
            else:
                st.warning("❌ ไม่พบข้อมูล")
        else:
            st.info(f"💡 กำลังแสดงข้อมูลในแท็บ: {selected_tab}")
            st.dataframe(all_sheets[selected_tab].head(20))
