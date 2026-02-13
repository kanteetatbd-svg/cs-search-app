import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="CS Mega Search Final", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (ID / IMEI) - เวอร์ชันเน้นเจอชัวร์")

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
search_val = st.text_input("🔍 กรอก ID หรือ IMEI ที่ต้องการค้นหา:")

if client and search_val:
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    q = search_val.strip().lower() # ตัดช่องว่างและทำให้เป็นตัวพิมพ์เล็ก
    
    try:
        tables = list(client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))
        found_data = {}

        with st.spinner('🚀 กำลังควานหาในทุกแท็บอย่างละเอียด...'):
            for table in tables:
                table_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
                
                # ดึงข้อมูลทั้งหมดของแท็บนั้นมา (ไม่จำกัดแถว เพื่อให้เจอข้อมูลที่อยู่ลึกๆ)
                df = client.query(f"SELECT * FROM `{table_id}`").to_dataframe()
                
                if not df.empty:
                    # --- จุดที่แก้: แปลงทุกอย่างเป็น String และหาแบบดื้อๆ เลย ---
                    # วิธีนี้จะข้ามพวกค่า None หรือ Error ของประเภทข้อมูลไปได้ครับ
                    mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(q, na=False).any(), axis=1)
                    res = df[mask]
                    
                    if not res.empty:
                        found_data[table.table_id] = res

        if found_data:
            st.success(f"✅ เจอข้อมูลของ `{search_val}` ใน {len(found_data)} แท็บ")
            tabs = st.tabs(list(found_data.keys()))
            for i, (name, data) in enumerate(found_data.items()):
                with tabs[i]:
                    st.subheader(f"📂 ข้อมูลจากแท็บ: {name}")
                    st.dataframe(data, use_container_width=True)
        else:
            st.error(f"❌ ไม่พบข้อมูล `{search_val}` ในแท็บไหนเลยครับ")
            # โชว์ข้อมูล 20 แถวแรกของแท็บแรก เพื่อดูว่าข้อมูลมันเข้าแอปจริงไหม
            if tables:
                st.info(f"💡 ตรวจสอบข้อมูลดิบในแท็บ [{tables[0].table_id}]:")
                debug_df = client.query(f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{tables[0].table_id}` LIMIT 20").to_dataframe()
                st.dataframe(debug_df)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
