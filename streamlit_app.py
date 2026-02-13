import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="CS Turbo Search", layout="wide")
st.title("🚀 ระบบค้นหาเคส CS")

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
search_val = st.text_input("🔍 กรอก ID หรือ IMEI เพื่อค้นหาทันที:")

if client and search_val:
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    q = search_val.strip()
    
    try:
        # 1. ดึงรายชื่อตาราง (แท็บ) ทั้งหมด
        tables = list(client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))
        found_data = {}

        with st.spinner('🚀 กำลังค้นหาข้อมูล...'):
            for table in tables:
                table_full_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
                
                # --- จุดตายที่ทำให้เร็วขึ้น: ใช้ SQL ค้นหาตั้งแต่ต้นทาง ---
                # เราจะไปถาม Schema ของตารางก่อนว่ามีคอลัมน์อะไรบ้าง
                schema = client.get_table(table_full_id).schema
                columns = [field.name for field in schema]
                
                # สร้างคำสั่ง SQL ที่สั่งให้ BigQuery หาจากทุกคอลัมน์เอง
                # ใช้ LIKE เพื่อให้เจอแม้มีช่องว่างแฝง
                where_clause = " OR ".join([f"CAST({col} AS STRING) LIKE '%{q}%'" for col in columns])
                sql = f"SELECT * FROM `{table_full_id}` WHERE {where_clause}"
                
                # ส่งคำสั่งไปรันที่ BigQuery (เร็วมาก!)
                query_job = client.query(sql)
                result_df = query_job.to_dataframe()
                
                if not result_df.empty:
                    found_data[table.table_id] = result_df

        # --- แสดงผลแยกตามแท็บ เหมือนเดิม ---
        if found_data:
            st.success(f"✅ ค้นหาเสร็จสิ้น! พบข้อมูลใน {len(found_data)} แท็บ")
            tabs = st.tabs(list(found_data.keys()))
            for i, (name, df) in enumerate(found_data.items()):
                with tabs[i]:
                    st.subheader(f"📂 ข้อมูลจากแท็บ: {name}")
                    st.dataframe(df, use_container_width=True)
        else:
            st.warning(f"❌ ไม่พบข้อมูล `{q}` ในแท็บไหนเลยครับ")
            
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
