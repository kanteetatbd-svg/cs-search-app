import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="CS Case Finder", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูลพนักงาน (ทุกแท็บ/ทุกแถว/ทุกคอลัมน์)")

# --- 1. เชื่อมต่อกุญแจไฟล์ key.json ---
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
search_val = st.text_input("🔍 กรอก ID หรือ IMEI เพื่อค้นหา (ระบบจะควานหาจากทุกที่):")

if client and search_val:
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    q = search_val.strip().lower()
    
    try:
        # ดึงรายชื่อตาราง (แท็บ) ทั้งหมดที่มี
        tables = list(client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))
        found_data = {}

        with st.spinner('🚀 กำลังควานหาข้อมูลจากทุกแท็บ ทุกแถว...'):
            for table in tables:
                table_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
                
                # ดึงข้อมูลทั้งหมดของตารางมาเช็ก (ไม่จำกัดแถว เพื่อให้ข้ามตารางสรุปด้านบนไปได้)
                df = client.query(f"SELECT * FROM `{table_id}`").to_dataframe()
                
                if not df.empty:
                    # แปลงทุกอย่างเป็น String และหาคำที่ต้องการใน "ทุกช่อง" ของแต่ละแถว
                    mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(q, na=False).any(), axis=1)
                    res = df[mask]
                    
                    if not res.empty:
                        found_data[table.table_id] = res

        # --- แสดงผลแยกตามหัวข้อแท็บเหมือนใน Google Sheet ---
        if found_data:
            st.success(f"✅ เจอข้อมูลของ `{search_val}` ใน {len(found_data)} แท็บ")
            tab_objs = st.tabs(list(found_data.keys()))
            
            for i, (name, data) in enumerate(found_data.items()):
                with tab_objs[i]:
                    st.subheader(f"📂 ข้อมูลจากแท็บ: {name}")
                    # แสดงผลเป็นตารางพร้อมข้อมูลทุกอย่างเหมือน Google Sheet
                    st.dataframe(data, use_container_width=True)
        else:
            st.error(f"❌ ไม่พบข้อมูล `{search_val}` ในแท็บไหนเลยครับ")
            # โชว์ข้อมูลดิบเพื่อ Debug (ให้พี่เห็นว่าตอนนี้ระบบ "เห็น" อะไรอยู่)
            st.info("💡 ตัวอย่างข้อมูลที่ระบบเห็นในตอนนี้ (20 แถวแรกของแท็บแรก):")
            if tables:
                debug_df = client.query(f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{tables[0].table_id}` LIMIT 20").to_dataframe()
                st.dataframe(debug_df)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
