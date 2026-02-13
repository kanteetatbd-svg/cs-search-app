import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="CS Multi-Tab Search", layout="wide")
st.title("🚀 ระบบค้นหาเคส")

# --- 1. เชื่อมต่อกุญแจไฟล์ key.json ---
@st.cache_resource
def get_bq_client():
    try:
        scopes = ["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/drive"]
        creds = service_account.Credentials.from_service_account_file('key.json', scopes=scopes)
        return bigquery.Client(credentials=creds, project=creds.project_id)
    except Exception as e:
        st.error(f"❌ กุญแจมีปัญหา: {e}")
        return None

client = get_bq_client()
search_val = st.text_input("🔍 กรอก ID หรือ IMEI (ระบบจะควานหาให้ทุกซอกทุกมุม):")

if client and search_val:
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    q = search_val.strip().lower() # ตัดช่องว่างและทำให้เป็นตัวเล็กเพื่อความแม่นยำ
    
    try:
        # ดึงรายชื่อแท็บ (ตาราง) ทั้งหมดที่มีใน Dataset
        tables = list(client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))
        found_data = {}

        with st.spinner('🚀 กำลังสแกนทุกช่องข้อมูล...'):
            for table in tables:
                table_full_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
                
                # ดึงข้อมูลทั้งหมดของแท็บนั้นออกมา (ไม่จำกัดแถว)
                df = client.query(f"SELECT * FROM `{table_full_id}`").to_dataframe()
                
                if not df.empty:
                    # --- ไม้ตาย: ค้นหาในทุกคอลัมน์และทุกแถวพร้อมกัน ---
                    # แปลงทุกเซลล์เป็น String -> ทำให้เป็นตัวเล็ก -> เช็กว่ามีคำที่หาไหม
                    mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(q, na=False).any(), axis=1)
                    res = df[mask]
                    
                    if not res.empty:
                        found_data[table.table_id] = res

        # --- แสดงผลแยกตามชื่อแท็บ เหมือน Google Sheets ---
        if found_data:
            st.success(f"✅ เจอข้อมูล `{search_val}` ใน {len(found_data)} แท็บ")
            tab_objs = st.tabs(list(found_data.keys()))
            
            for i, (name, data) in enumerate(found_data.items()):
                with tab_objs[i]:
                    st.subheader(f"📂 ข้อมูลจากแท็บ: {name}")
                    # แสดงตารางแบบดั้งเดิม เห็นครบทุกคอลัมน์ที่เจอ
                    st.dataframe(data, use_container_width=True)
        else:
            st.error(f"❌ ไม่พบข้อมูล `{search_val}` ในแท็บไหนเลยครับ")
            
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
else:
    st.info("💡 ใส่ ID หรือ IMEI แล้วกด Enter")
