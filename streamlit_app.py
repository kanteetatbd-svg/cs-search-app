import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 24.0 - Final)")

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
            
            # เปิดไฟล์ที่เลือก
            sh = client.open_by_key(file_map[selected_file_name])
            worksheets = sh.worksheets()
            tab_names = [w.title for w in worksheets]
            
            selected_tab = st.selectbox("📋 เลือกแท็บ (หมวดหมู่):", tab_names)
            
            @st.cache_data(ttl=300)
            def load_raw_data(file_id, sheet_name):
                # ดึงข้อมูลแบบดิบที่สุดเพื่อป้องกัน Error เรื่อง Column Match
                ws = client.open_by_key(file_id).worksheet(sheet_name)
                raw_data = ws.get_all_values()
                if not raw_data: return pd.DataFrame()
                
                # แปลงเป็น DataFrame แบบใจดี (ถ้าคอลัมน์ไม่เท่ากัน มันจะเติมค่าว่างให้เองครับ)
                df = pd.DataFrame(raw_data)
                # ใช้แถวแรกเป็นหัวตาราง
                df.columns = df.iloc[0]
                df = df[1:].reset_index(drop=True)
                return df

            df = load_raw_data(file_map[selected_file_name], selected_tab)
            
            if not df.empty:
                search_query = st.text_input(f"🔍 พิมพ์ข้อมูลที่ต้องการค้นหาใน [{selected_tab}]:")
                
                if search_query:
                    # ค้นหาแบบไม่สนใจตัวพิมพ์เล็ก-ใหญ่
                    result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
                    if not result.empty:
                        st.success(f"✅ พบข้อมูล {len(result)} รายการ")
                        st.dataframe(result, use_container_width=True)
                    else:
                        st.warning("❌ ไม่พบข้อมูลที่ตรงกัน")
                else:
                    st.info(f"💡 แสดงตัวอย่างข้อมูล 20 แถวแรกของแท็บ [{selected_tab}]")
                    st.dataframe(df.head(20), use_container_width=True)
            else:
                st.warning("⚠️ แท็บนี้ไม่มีข้อมูล")
                
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
