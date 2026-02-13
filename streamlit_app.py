import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="CS Search Original View", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (แสดงผลแบบ Original Sheet)")

@st.cache_resource
def get_bq_client():
    try:
        scopes = ["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/drive"]
        creds = service_account.Credentials.from_service_account_file('key.json', scopes=scopes)
        return bigquery.Client(credentials=creds, project=creds.project_id)
    except Exception as e:
        st.error(f"❌ ระบบหากุญแจไม่เจอ: {e}")
        return None

client = get_bq_client()
search_val = st.text_input("🔍 กรอก ID หรือ IMEI เพื่อค้นหา:")

if client and search_val:
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    q = search_val.strip()
    
    try:
        tables = list(client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))
        found_data = {}

        with st.spinner('🚀 กำลังสแกนหาข้อมูลทุกซอกทุกมุม...'):
            for table in tables:
                table_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
                
                # ดึงข้อมูลทั้งหมดของตารางออกมา (ไม่ใช้ LIMIT เพื่อให้เจอข้อมูลที่อยู่ลึกๆ)
                df = client.query(f"SELECT * FROM `{table_id}`").to_dataframe()
                
                if not df.empty:
                    # ค้นหาคำที่ต้องการในทุกแถวและทุกคอลัมน์ โดยแปลงเป็น String ทั้งหมด
                    # วิธีนี้จะทำให้เจอ ID แม้จะอยู่บรรทัดที่เท่าไหร่ก็ตาม
                    mask = df.astype(str).apply(lambda row: row.str.contains(q, case=False, na=False).any(), axis=1)
                    res = df[mask]
                    
                    if not res.empty:
                        found_data[table.table_id] = res

        if found_data:
            st.success(f"✅ พบข้อมูลของ `{q}` แล้วพี่!")
            # แยกหัวข้อตามแท็บ (ชื่อตาราง)
            tabs = st.tabs(list(found_data.keys()))
            for i, (name, data) in enumerate(found_data.items()):
                with tabs[i]:
                    st.subheader(f"📂 ข้อมูลจากแท็บ: {name}")
                    # แสดงผลเป็นตารางพร้อมข้อมูลทุกอย่างเหมือน Google Sheet เป๊ะๆ
                    st.dataframe(data, use_container_width=True)
        else:
            st.error(f"❌ ไม่พบข้อมูล `{q}` ในแท็บไหนเลยครับ")
            st.info("💡 ข้อมูลที่ระบบ 'เห็น' ในตอนนี้ (ตัวอย่างจากแท็บแรก):")
            if tables:
                debug_df = client.query(f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{tables[0].table_id}` LIMIT 20").to_dataframe()
                st.dataframe(debug_df)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
