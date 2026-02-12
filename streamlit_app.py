import streamlit as st
import pandas as pd
from gspread_pandas import Spread
import traceback

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 1.0 - Debug Mode)")

@st.cache_resource
def get_config():
    try:
        conf = dict(st.secrets["gcp_service_account"])
        if "\\n" in conf["private_key"]:
            conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        return conf
    except Exception as e:
        st.error(f"ปัญหาที่ Secrets: {e}")
        return None

config = get_config()
sheet_id = "1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA"

if config:
    try:
        st.info("กำลังทดสอบดึงข้อมูล...")
        spread = Spread(sheet_id, config=config)
        
        # ดึงทุกแท็บ
        all_tabs = {}
        for s in spread.sheets:
            df = spread.sheet_to_df(index=0, sheet=s.title)
            if not df.empty:
                all_tabs[s.title] = df
        
        if all_tabs:
            st.success(f"✅ เชื่อมต่อสำเร็จ! พบแท็บ: {', '.join(all_tabs.keys())}")
            choice = st.selectbox("📂 เลือกหมวดหมู่:", list(all_tabs.keys()))
            query = st.text_input(f"🔍 ค้นหาในหมวด [{choice}]:")
            if query:
                df_res = all_tabs[choice]
                res = df_res[df_res.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)]
                st.dataframe(res) if not res.empty else st.warning("ไม่พบข้อมูล")
            else:
                st.dataframe(all_tabs[choice].head(10))
        else:
            st.warning("⚠️ ไฟล์ว่างเปล่า หรือไม่มีข้อมูลในแท็บใดเลย")

    except Exception as e:
        st.error("❌ ตรวจพบข้อผิดพลาดขณะเชื่อมต่อ")
        # โชว์ Error แบบละเอียดที่สุดเพื่อหาทางแก้
        st.code(traceback.format_exc()) 
        
        st.info("💡 ถ้าเห็นคำว่า '403 Forbidden' หรือ 'Access Denied' แปลว่า IT บริษัทบล็อกการแชร์ให้เมลนอกองค์กรครับ")
