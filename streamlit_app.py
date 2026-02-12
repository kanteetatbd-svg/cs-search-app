import streamlit as st
import pandas as pd
import json
from gspread_pandas import Spread

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 11.0 - Final)")

# ดึงกุญแจลับจากระบบ Secrets โดยตรง
@st.cache_resource
def get_config():
    try:
        # อ่านค่าเป็น JSON ตรงๆ ตัดปัญหา PEM และ Unicode error ครับ
        config_str = st.secrets["service_account_json"]
        return json.loads(config_str)
    except Exception as e:
        st.error(f"ไม่สามารถอ่านกุญแจลับได้: {e}")
        return None

config = get_config()
sheet_id = "1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA"

@st.cache_data(ttl=600)
def load_all_data(_config):
    if not _config: return None
    try:
        spread = Spread(sheet_id, config=_config)
        all_tabs = {s.title: spread.sheet_to_df(index=0, sheet=s.title) 
                    for s in spread.sheets if not spread.sheet_to_df(index=0, sheet=s.title).empty}
        return all_tabs
    except Exception as e:
        return str(e)

if config:
    all_sheets = load_all_data(config)

    if isinstance(all_sheets, str):
        st.error(f"❌ การเชื่อมต่อขัดข้อง: {all_sheets}")
    elif all_sheets:
        tab_list = list(all_sheets.keys())
        selected_tab = st.selectbox("📂 เลือกหมวดหมู่ที่ต้องการค้นหา:", tab_list)
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
        st.warning("⚠️ ไม่พบข้อมูลในไฟล์ Google Sheets")
