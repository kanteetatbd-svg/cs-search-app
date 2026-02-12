import streamlit as st
import pandas as pd
from gspread_pandas import Spread
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 1.0 - Auto Finder)")

@st.cache_resource
def get_config():
    try:
        conf = dict(st.secrets["gcp_service_account"])
        if "\\n" in conf["private_key"]:
            conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        return conf
    except Exception as e:
        return None

config = get_config()

if config:
    try:
        # ตั้งค่าสิทธิ์การเข้าถึงไฟล์
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(config, scopes=scopes)
        client = gspread.authorize(creds)
        
        # ดึงรายชื่อไฟล์ทั้งหมดที่บอทเห็น (ไฟล์ที่พี่กด 'แชร์' ให้เมลบอทแล้ว)
        all_files = client.openall()
        
        if not all_files:
            st.error("❌ บอทหาไฟล์ไม่เจอเลยครับ!")
            st.info(f"💡 เมลบอทคือ: `{config['client_email']}` พี่ลองเช็คปุ่มแชร์ใน Sheets อีกรอบนะว่าใส่เมลนี้เป๊ะๆ ไหม")
        else:
            # สร้างรายการชื่อไฟล์ให้พี่เลือกเองเลยครับ ไม่ต้องพิมพ์ ID แล้ว!
            file_map = {f.title: f.id for f in all_files}
            selected_file_name = st.selectbox("📂 เลือกไฟล์ Google Sheets ที่ต้องการใช้งาน:", list(file_map.keys()))
            sheet_id = file_map[selected_file_name]
            
            @st.cache_data(ttl=300)
            def load_data(_config, _id):
                spread = Spread(_id, config=_config)
                # ดึงทุกแท็บ (Case2025, GG, truewallet และอื่นๆ)
                return {s.title: spread.sheet_to_df(index=0, sheet=s.title) for s in spread.sheets}
            
            all_sheets = load_data(config, sheet_id)
            
            if all_sheets:
                tab_list = list(all_sheets.keys())
                selected_tab = st.selectbox("📋 เลือกแท็บ (หมวดหมู่):", tab_list)
                search_query = st.text_input(f"🔍 พิมพ์ข้อมูลที่ต้องการค้นหาใน [{selected_tab}]:")
                
                df = all_sheets[selected_tab]
                if search_query:
                    result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
                    if not result.empty:
                        st.success(f"✅ พบข้อมูล {len(result)} รายการ")
                        st.dataframe(result, use_container_width=True)
                    else:
                        st.warning("❌ ไม่พบข้อมูลที่ตรงกัน")
                else:
                    st.info(f"💡 กำลังแสดงข้อมูลในแท็บ: {selected_tab}")
                    st.dataframe(df.head(20), use_container_width=True)
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดทางเทคนิค: {e}")
