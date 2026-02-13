import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="CS Multi-Table Search", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูลพนักงาน (BigQuery Multi-Table)")

# --- 1. เชื่อมต่อผ่านกุญแจไฟล์ key.json ---
@st.cache_resource
def get_bq_client():
    try:
        # กำหนด Scopes ให้ครอบคลุมการอ่านไฟล์ภายนอก (Google Sheets)
        scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/bigquery"
        ]
        creds = service_account.Credentials.from_service_account_file('key.json', scopes=scopes)
        return bigquery.Client(credentials=creds, project=creds.project_id)
    except Exception as e:
        st.error(f"❌ ระบบหาไฟล์กุญแจไม่เจอหรือไฟล์พัง: {e}")
        return None

client = get_bq_client()

# --- 2. ส่วนการค้นหา ---
search_id = st.text_input("🔍 กรอก ID พนักงานที่ต้องการค้นหา:", placeholder="เช่น 9300191")

if client and search_id:
    # ระบุพิกัด Dataset ของพี่
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    
    try:
        # ดึงรายชื่อตาราง (Table) ทั้งหมดใน Dataset นี้ออกมา (เหมือนรายชื่อแท็บใน Sheets)
        tables = client.list_tables(f"{PROJECT_ID}.{DATASET_ID}")
        
        found_data = {} # เก็บผลลัพธ์: { 'ชื่อตาราง': DataFrame }

        with st.spinner('🚀 กำลังกวาดข้อมูลจากทุกตาราง...'):
            for table in tables:
                table_full_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
                
                # ดึงหัวตารางมาเช็กว่าตารางนี้มีคอลัมน์อะไรบ้าง
                schema_df = client.query(f"SELECT * FROM `{table_full_id}` LIMIT 1").to_dataframe()
                all_columns = schema_df.columns.tolist()
                
                # สร้างคำสั่ง SQL ค้นหา ID จาก "ทุกคอลัมน์" ในตารางนี้ (กันเหนียว)
                where_clauses = [f"CAST({col} AS STRING) = '{search_id.strip()}'" for col in all_columns]
                sql = f"SELECT * FROM `{table_full_id}` WHERE {' OR '.join(where_clauses)}"
                
                try:
                    result_df = client.query(sql).to_dataframe()
                    if not result_df.empty:
                        found_data[table.table_id] = result_df
                except:
                    continue # ข้ามตารางที่อาจจะมีปัญหาเรื่องโครงสร้างข้อมูล

        # --- 3. แสดงผลลัพธ์แบบ "แท็บ" เหมือน Google Sheets ---
        if found_data:
            st.success(f"✅ พบข้อมูลของ ID `{search_id}` ใน {len(found_data)} ตาราง")
            
            # สร้าง Tabs ตามชื่อตารางที่เจอข้อมูล
            tab_list = st.tabs(list(found_data.keys()))
            
            for i, (table_name, df) in enumerate(found_data.items()):
                with tab_list[i]:
                    st.write(f"📊 ข้อมูลจากตาราง: **{table_name}**")
                    # แสดงผลเป็นตารางเหมือน Google Sheets เป๊ะๆ
                    st.dataframe(df, use_container_width=True)
        else:
            st.warning(f"❌ ไม่พบข้อมูล ID `{search_id}` ในตารางใดๆ เลย")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการเข้าถึง BigQuery: {e}")
else:
    st.info("💡 ใส่ ID พนักงานเพื่อเริ่มค้นหาข้อมูลจากทุกตารางในระบบ")
