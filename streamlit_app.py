import streamlit as st
import pandas as pd
from gspread_pandas import Spread

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 13.0)")

@st.cache_resource
def get_config():
    try:
        # ดึงค่าจาก Secrets ที่เราเพิ่งเซฟไปครับ
        return dict(st.secrets["gcp_service_account"])
    except Exception as e:
        st.error(f"ไม่สามารถอ่านกุญแจลับจาก Secrets ได้: {e}")
        return None

config = get_config()
sheet_id = "1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA"

@st.cache_data(ttl=300)
def load_data(_config):
    if not _config: return None
    try:
        spread = Spread(sheet_id, config=_config)
        return {s.title: spread.sheet_to_df(index=0, sheet=s.title) 
                for s in spread.sheets if not spread.sheet_to_df(index=0, sheet=s.title).empty}
    except Exception as e:
        return str(e)

if config:
    all_data = load_data(config)
    if isinstance(all_data, str):
        st.error(f"❌ เชื่อมต่อ Google Sheets ไม่ได้: {all_data}")
        st.info("💡 พี่เช็คดูว่าแชร์ไฟล์ Sheets ให้เมล cs-search-key@... ในโหมด Editor หรือยังครับ")
    elif all_data:
        choice = st.selectbox("📂 เลือกหมวดหมู่:", list(all_data.keys()))
        query = st.text_input(f"🔍 ค้นหาในหมวด [{choice}]:")
        if query:
            df = all_data[choice]
            result = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)]
            st.dataframe(result) if not result.empty else st.warning("ไม่พบข้อมูล")
