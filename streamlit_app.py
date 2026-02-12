import streamlit as st
import pandas as pd
from gspread_pandas import Spread

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 16.0 - Success)")

@st.cache_resource
def get_config():
    try:
        # ดึงค่าจาก Secrets ที่พี่เซฟไว้ครับ
        conf = dict(st.secrets["gcp_service_account"])
        # ตรวจสอบและจัดการเรื่องขึ้นบรรทัดใหม่ในรหัสลับ
        if "\\n" in conf["private_key"]:
            conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        return conf
    except Exception as e:
        st.error(f"ตรวจพบปัญหาที่หน้า Secrets: {e}")
        return None

config = get_config()
# ID ไฟล์จากรูปของพี่: 1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA
sheet_id = "1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA"

@st.cache_data(ttl=600)
def load_all_sheets(_config):
    if not _config: return None
    try:
        spread = Spread(sheet_id, config=_config)
        # ดึงทุกแท็บที่มีข้อมูลในไฟล์ Sheets ของพี่ครับ
        return {s.title: spread.sheet_to_df(index=0, sheet=s.title) for s in spread.sheets}
    except Exception as e:
        return str(e)

if config:
    all_data = load_all_sheets(config)
    
    if isinstance(all_data, str):
        st.error(f"❌ เชื่อมต่อไม่ได้: {all_data}")
        st.info("แนะนำ: ลองกด Reboot app อีกครั้ง หรือเช็คว่าเมลบอทยังอยู่ในรายชื่อแชร์ของไฟล์ไหม")
    elif all_data:
        # แสดงเมนูเลือกแท็บ (เช่น Case2025 และแท็บอื่นๆ)
        tab_list = list(all_data.keys())
        selected_tab = st.selectbox("📂 เลือกหมวดหมู่ที่ต้องการค้นหา:", tab_list)
        
        search_query = st.text_input(f"🔍 ค้นหาในหมวด [{selected_tab}] (IMEI, ชื่อ, ID):")
        
        if search_query:
            df = all_data[selected_tab]
            # ค้นหาทุกคอลัมน์ในตาราง
            result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
            
            if not result.empty:
                st.success(f"✅ พบข้อมูล {len(result)} รายการ")
                st.dataframe(result, use_container_width=True)
            else:
                st.warning("❌ ไม่พบข้อมูลที่ตรงกัน")
        else:
            st.info(f"💡 กำลังแสดงข้อมูลในแท็บ: {selected_tab}")
            st.dataframe(all_data[selected_tab].head(10))
