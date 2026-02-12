import streamlit as st
import pandas as pd
from gspread_pandas import Spread

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 15.0 - Debug Mode)")

@st.cache_resource
def get_config():
    try:
        return dict(st.secrets["gcp_service_account"])
    except Exception as e:
        st.error(f"ตรวจพบปัญหาที่หน้า Secrets: {e}")
        return None

config = get_config()
# ตรวจสอบ ID ไฟล์จากรูปของพี่: 1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA
sheet_id = "1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA"

if config:
    try:
        st.info("กำลังทดสอบการเชื่อมต่อ...")
        spread = Spread(sheet_id, config=config)
        
        # ถ้าเชื่อมต่อได้ จะดึงรายชื่อแท็บมาโชว์ครับ
        tab_names = [s.title for s in spread.sheets]
        st.success(f"✅ เชื่อมต่อสำเร็จ! พบแท็บ: {', '.join(tab_names)}")
        
        selected_tab = st.selectbox("📂 เลือกหมวดหมู่:", tab_names)
        df = spread.sheet_to_df(index=0, sheet=selected_tab)
        
        search_query = st.text_input(f"🔍 ค้นหาในหมวด [{selected_tab}]:")
        if search_query:
            result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
            st.dataframe(result, use_container_width=True) if not result.empty else st.warning("ไม่พบข้อมูล")
            
    except Exception as e:
        st.error("❌ การเชื่อมต่อล้มเหลว")
        st.code(str(e)) # โชว์ตัวหนังสือภาษาอังกฤษที่ Google ด่าเรามาครับ
        
        # คำแนะนำเจาะจงตาม Error
        error_msg = str(e).lower()
        if "403" in error_msg:
            st.warning("⚠️ สาเหตุ: Google บล็อกการเข้าถึง (403 Forbidden)")
            st.write("1. เช็คว่าใน Cloud Console เปิดใช้งาน 'Google Drive API' หรือยัง")
            st.write("2. เช็คว่า IT บริษัทบล็อกการแชร์ไฟล์ให้คนนอกองค์กรหรือไม่")
        elif "404" in error_msg:
            st.warning("⚠️ สาเหตุ: หาไฟล์ไม่เจอ (404 Not Found)")
            st.write("เช็คว่า ID ไฟล์ในโค้ดพิมพ์ผิดหรือไม่")
