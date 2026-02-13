import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="CS Real Case Finder", layout="wide")
st.title("🚀 ระบบดึงข้อมูลเคสพนักงาน (ข้ามส่วนสรุป)")

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
search_val = st.text_input("🔍 กรอก ID หรือ IMEI เพื่อดึงข้อมูลเคส:")

if client and search_val:
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    q = search_val.strip().lower()
    
    try:
        tables = list(client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))
        found_data = {}

        with st.spinner('🚀 กำลังข้ามส่วนสรุปเพื่อหาข้อมูลเคสจริง...'):
            for table in tables:
                table_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
                
                # ดึงข้อมูลทั้งหมดของตารางออกมา
                df = client.query(f"SELECT * FROM `{table_id}`").to_dataframe()
                
                if not df.empty:
                    # แปลงทุกอย่างเป็น String และหา ID/IMEI ในทุกช่อง
                    # ระบบจะหาเจอเฉพาะแถวที่มีข้อมูลจริง ไม่ไปติดตรง Dashboard
                    mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(q, na=False).any(), axis=1)
                    res = df[mask]
                    
                    if not res.empty:
                        found_data[table.table_id] = res

        # --- 2. แสดงผลลัพธ์แยกตามแท็บ เหมือนต้นฉบับ ---
        if found_data:
            st.success(f"✅ พบข้อมูลเคสของ `{search_val}` ใน {len(found_data)} แท็บ")
            tab_objs = st.tabs(list(found_data.keys()))
            
            for i, (name, data) in enumerate(found_data.items()):
                with tab_objs[i]:
                    st.subheader(f"📂 แท็บ: {name}")
                    # แสดงผลเป็นตารางหน้าตาเหมือน Original Google Sheet
                    st.dataframe(data, use_container_width=True)
        else:
            st.error(f"❌ ไม่พบข้อมูลเคสของ `{search_val}`")
            # Debug: โชว์ข้อมูลแถวที่ 10-20 (จุดที่ข้อมูลจริงควรจะเริ่ม)
            if tables:
                st.info(f"💡 ตรวจสอบข้อมูลแถวที่ 10-30 ในแท็บ [{tables[0].table_id}]:")
                debug_df = client.query(f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{tables[0].table_id}` LIMIT 20 OFFSET 10").to_dataframe()
                st.dataframe(debug_df)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
