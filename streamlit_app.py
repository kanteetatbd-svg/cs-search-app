import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="BigQuery Multi-Search", layout="wide")
st.title("🚀 ระบบค้นหา ID ทุกตารางใน BigQuery")

# --- 1. เชื่อมต่อกุญแจ (ใช้ Scopes ให้ครบเพื่ออ่าน Sheets ที่เชื่อมกับ BigQuery) ---
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
        st.error(f"❌ กุญแจมีปัญหา: {e}")
        return None

client = get_bq_client()

# --- 2. ส่วนการค้นหา ---
search_id = st.text_input("🔍 กรอก ID พนักงานเพื่อค้นหาในทุกตาราง:", placeholder="เช่น 9300191")

if client and search_id:
    # ระบุชื่อโปรเจกต์และ Dataset
    project_id = "sturdy-sentry-487204-s4"
    dataset_id = "cs_database"
    
    try:
        # ดึงรายชื่อตารางทั้งหมดที่มีใน Dataset นี้ (แทนการเปิดดูทุกแท็บ)
        tables = client.list_tables(f"{project_id}.{dataset_id}")
        
        found_any = False
        st.markdown(f"### 🔎 ผลการค้นหาสำหรับ ID: `{search_id}`")

        for table in tables:
            full_table_id = f"{project_id}.{dataset_id}.{table.table_id}"
            
            # ดึงหัวตารางมาเช็กก่อน 1 แถวเพื่อหาชื่อคอลัมน์
            check_df = client.query(f"SELECT * FROM `{full_table_id}` LIMIT 1").to_dataframe()
            cols = check_df.columns.tolist()
            
            # สร้างคำสั่ง SQL ค้นหา (ค้นหาในทุกคอลัมน์ที่เป็นไปได้ เผื่อ ID อยู่คนละที่)
            # เราจะสร้าง WHERE col1='ID' OR col2='ID' ...
            where_clause = " OR ".join([f"CAST({col} AS STRING) = '{search_id}'" for col in cols])
            sql = f"SELECT * FROM `{full_table_id}` WHERE {where_clause}"
            
            try:
                result_df = client.query(sql).to_dataframe()
                
                if not result_df.empty:
                    found_any = True
                    # แยกโชว์ตามชื่อตาราง (เหมือนแยกตามแท็บ)
                    with st.expander(f"✅ พบข้อมูลในตาราง: {table.table_id}", expanded=True):
                        st.dataframe(result_df, use_container_width=True)
            except:
                continue # ข้ามตารางที่มีปัญหาเรื่องโครงสร้าง

        if not found_any:
            st.warning(f"❌ ไม่พบ ID '{search_id}' ในตารางใดๆ เลย")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
else:
    st.info("💡 ใส่ ID ด้านบน ระบบจะควานหาข้อมูลจากทุกตารางใน BigQuery ให้ทันทีครับ")
