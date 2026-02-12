import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="CS Search All-in-One", layout="wide")
st.title("🎯 ระบบค้นหาข้อมูลรายไอดี (จากทุกแท็บ)")

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
        # สิทธิ์การเข้าถึง
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(config, scopes=scopes)
        client = gspread.authorize(creds)
        
        # ค้นหาไฟล์ทั้งหมดที่แชร์กับบอท
        all_files = client.openall()
        
        if not all_files:
            st.error("❌ ไม่พบไฟล์ที่แชร์กับระบบ")
        else:
            file_map = {f.title: f.id for f in all_files}
            selected_file_name = st.selectbox("📂 เลือกไฟล์ฐานข้อมูล:", list(file_map.keys()))
            
            # ช่องค้นหาหลัก
            search_query = st.text_input("🔍 ใส่ ID ที่ต้องการดึงข้อมูลทั้งหมด:", placeholder="เช่น 14833323")

            if search_query:
                st.markdown(f"### 📋 ผลการค้นหาสำหรับไอดี: `{search_query}`")
                sh = client.open_by_key(file_map[selected_file_name])
                worksheets = sh.worksheets()
                found_count = 0

                # วนลูปหาในทุกแท็บ
                for ws in worksheets:
                    raw_data = ws.get_all_values()
                    if not raw_data: continue
                    
                    # แปลงข้อมูลดิบเป็นตาราง (ใช้แถวแรกเป็นหัวข้อของแท็บนั้นๆ)
                    df = pd.DataFrame(raw_data)
                    df.columns = df.iloc[0]
                    df = df[1:].reset_index(drop=True)

                    # ค้นหาไอดีในทุกคอลัมน์ของแท็บนี้
                    result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)]

                    if not result.empty:
                        found_count += 1
                        # แสดงผลแยกตามแท็บ พร้อมหัวข้อที่ถูกต้องของแท็บนั้น
                        with st.expander(f"📍 พบข้อมูลในแท็บ: {ws.title}", expanded=True):
                            st.dataframe(result, use_container_width=True)
                
                if found_count == 0:
                    st.warning(f"❌ ไม่พบข้อมูลไอดี '{search_query}' ในแท็บใดเลย")
                else:
                    st.success(f"✅ ค้นหาเสร็จสิ้น พบข้อมูลใน {found_count} แท็บ")
            else:
                st.info("💡 พิมพ์ ID ด้านบนเพื่อดึงข้อมูลจากทุกแท็บมาแสดงผลพร้อมกัน")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
