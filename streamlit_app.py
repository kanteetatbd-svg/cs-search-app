import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="CS Multi-Tab Search", layout="wide")
st.title("📂 ระบบรวมข้อมูลรายไอดี (ดึงทุกแท็บ/ทุกสถานะ)")

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
            st.error("❌ ไม่พบไฟล์ที่แชร์กับระบบ")
        else:
            file_map = {f.title: f.id for f in all_files}
            selected_file_name = st.selectbox("📊 เลือกไฟล์ฐานข้อมูลที่ต้องการใช้งาน:", list(file_map.keys()))
            
            # รับค่าไอดีจากผู้ใช้
            search_query = st.text_input("🔍 ใส่ ID ที่ต้องการดึงข้อมูลทั้งหมด:", placeholder="พิมพ์ ID แล้วกด Enter")

            if search_query:
                sh = client.open_by_key(file_map[selected_file_name])
                worksheets = sh.worksheets()
                
                st.markdown(f"## 📌 ผลการค้นหาสำหรับไอดี: `{search_query}`")
                found_any = False

                # วนลูปผ่านทุกแท็บเหมือนการเปิดไล่ดูใน Sheets
                for ws in worksheets:
                    # ดึงข้อมูลดิบทั้งหมดจากแท็บนั้น
                    raw_data = ws.get_all_values()
                    if not raw_data:
                        continue
                        
                    # แปลงเป็นตารางโดยใช้แถวแรกเป็นหัวข้อ (Header) เพื่อความเหมือนต้นฉบับ
                    df = pd.DataFrame(raw_data)
                    df.columns = df.iloc[0] # ตั้งชื่อหัวคอลัมน์จากแถวที่ 1
                    df = df[1:].reset_index(drop=True)

                    # ค้นหาไอดีในทุกคอลัมน์ (เผื่อไอดีไปอยู่ในคอลัมน์ที่ต่างกันในแต่ละแท็บ)
                    result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)]

                    if not result.empty:
                        found_any = True
                        # แสดงหัวข้อแท็บให้ชัดเจนเหมือนแบ่งหน้าในไฟล์
                        st.markdown(f"### 📍 ข้อมูลจากแท็บ: **{ws.title}**")
                        # แสดงผลในรูปแบบตารางที่เลื่อนดูได้และขยายเต็มหน้าจอ
                        st.dataframe(result, use_container_width=True)
                        st.divider() # เส้นคั่นระหว่างแท็บเพื่อให้ดูง่าย
                
                if not found_any:
                    st.warning(f"⚠️ ไม่พบข้อมูลไอดี '{search_query}' ในแท็บใดเลยของไฟล์นี้")
                else:
                    st.success(f"🏁 ดึงข้อมูลที่เกี่ยวข้องทั้งหมดเรียบร้อยแล้ว")
            else:
                st.info("💡 กรุณาใส่ ID ด้านบนเพื่อเริ่มการดึงข้อมูลจากทุกแท็บ")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
