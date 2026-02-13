import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# ตั้งค่าหน้าจอให้กว้างเพื่อดูตารางง่ายๆ
st.set_page_config(page_title="CS Case Tracker", layout="wide")
st.title("🚀 ระบบค้นหาเคสพนักงาน (แยกตามแท็บ)")

# --- 1. เชื่อมต่อกุญแจไฟล์ key.json ---
@st.cache_resource
def get_bq_client():
    try:
        scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/bigquery"
        ]
        creds = service_account.Credentials.from_service_account_file('key.json', scopes=scopes)
        return bigquery.Client(credentials=creds, project=creds.project_id)
    except Exception as e:
        st.error(f"❌ ระบบหากุญแจไม่เจอ: {e}")
        return None

client = get_bq_client()

# --- 2. ส่วนการค้นหา ---
search_id = st.text_input("🔍 กรอก ID พนักงานที่ต้องการติดตามเคส:", placeholder="เช่น 9300191")

if client and search_id:
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    
    try:
        # ดึงรายชื่อตารางทั้งหมด (ซึ่งก็คือชื่อแท็บใน Sheets ของพี่)
        tables = client.list_tables(f"{PROJECT_ID}.{DATASET_ID}")
        
        found_results = {} # เก็บข้อมูล { 'ชื่อแท็บ': DataFrame }

        with st.spinner('กำลังค้นหาข้อมูลจากทุกแท็บ...'):
            for table in tables:
                table_full_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
                
                # เช็กหัวตารางเพื่อหาชื่อคอลัมน์ทั้งหมด
                sample = client.query(f"SELECT * FROM `{table_full_id}` LIMIT 1").to_dataframe()
                cols = sample.columns.tolist()
                
                # สร้าง SQL ค้นหา ID จากทุกคอลัมน์ในแท็บนี้ (เผื่อพี่วาง ID ไว้ไม่ตรงกัน)
                where_clause = " OR ".join([f"CAST({c} AS STRING) = '{search_id.strip()}'" for c in cols])
                sql = f"SELECT * FROM `{table_full_id}` WHERE {where_clause}"
                
                df_result = client.query(sql).to_dataframe()
                
                # ถ้าเจอข้อมูลในแท็บนี้ ให้เก็บไว้โชว์
                if not df_result.empty:
                    found_results[table.table_id] = df_result

        # --- 3. การแสดงผลแบบแยกหัวข้อตามแท็บ ---
        if found_results:
            st.success(f"✅ พบข้อมูลของ ID `{search_id}` ใน {len(found_results)} หัวข้อ (แท็บ)")
            
            # สร้างแถบ Tabs ด้านบนตามชื่อแท็บที่เจอข้อมูล
            tab_objects = st.tabs(list(found_results.keys()))
            
            for i, (tab_name, df) in enumerate(found_results.items()):
                with tab_objects[i]:
                    st.subheader(f"📂 ข้อมูลจากแท็บ: {tab_name}")
                    # โชว์ข้อมูลเป็นตารางเหมือนใน Sheets
                    st.dataframe(df, use_container_width=True)
        else:
            st.warning(f"❌ ไม่พบข้อมูล ID `{search_id}` ในแท็บไหนเลยครับ")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
else:
    st.info("💡 กรุณากรอก ID เพื่อเริ่มการค้นหา")
