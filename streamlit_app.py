import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="CS Global Search", layout="wide")
st.title("🔍 ระบบค้นหาข้อมูล CS (Version 25.0 - Global Search)")

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
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(config, scopes=scopes)
        client = gspread.authorize(creds)
        
        all_files = client.openall()
        
        if not all_files:
            st.error("❌ บอทหาไฟล์ไม่เจอครับ!")
        else:
            file_map = {f.title: f.id for f in all_files}
            selected_file_name = st.selectbox("📂 เลือกไฟล์ที่ต้องการใช้งาน:", list(file_map.keys()))
            
            # ช่องค้นหาหลัก (ID เช่น 14833323)
            search_query = st.text_input("🎯 ใส่ ID หรือข้อมูลที่ต้องการค้นหา (จะค้นหาให้ทุกแท็บ):", placeholder="เช่น 14833323")

            if search_query:
                st.divider()
                with st.spinner(f'กำลังค้นหา "{search_query}" ในทุกแท็บ...'):
                    sh = client.open_by_key(file_map[selected_file_name])
                    worksheets = sh.worksheets()
                    found_any = False

                    for ws in worksheets:
                        raw_data = ws.get_all_values()
                        if not raw_data: continue
                        
                        df = pd.DataFrame(raw_data)
                        df.columns = df.iloc[0]
                        df = df[1:].reset_index(drop=True)

                        # ค้นหาข้อมูลในทุกคอลัมน์ของแท็บนี้
                        result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)]

                        if not result.empty:
                            found_any = True
                            with st.expander(f"✅ พบในแท็บ: {ws.title} ({len(result)} รายการ)", expanded=True):
                                st.dataframe(result, use_container_width=True)
                    
                    if not found_any:
                        st.warning(f"❌ ไม่พบข้อมูล '{search_query}' ในแท็บใดเลยของไฟล์นี้")
            else:
                st.info("💡 พิมพ์ข้อมูลที่ต้องการค้นหาด้านบน เพื่อค้นหาจากทุกแท็บพร้อมกันครับ")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
