import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="CS Turbo Search", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS")

@st.cache_resource
def get_bq_client():
    try:
        scopes = ["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/drive"]
        creds = service_account.Credentials.from_service_account_file('key.json', scopes=scopes)
        return bigquery.Client(credentials=creds, project=creds.project_id)
    except Exception as e:
        st.error(f"❌ กุญแจพัง: {e}")
        return None

client = get_bq_client()
search_id = st.text_input("🔍 กรอก ID พนักงาน (พิมพ์แค่เลขก็ได้ครับ):")

if client and search_id:
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    search_val = search_id.strip() # ตัดช่องว่างหน้า-หลังที่พี่อาจจะเผลอพิมพ์ไป
    
    try:
        tables = client.list_tables(f"{PROJECT_ID}.{DATASET_ID}")
        found_results = {}

        for table in tables:
            full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
            
            # ดึงโครงสร้างตารางมาดูว่ามีคอลัมน์อะไรบ้าง
            schema_query = f"SELECT * FROM `{full_table_id}` LIMIT 1"
            sample_df = client.query(schema_query).to_dataframe()
            cols = sample_df.columns.tolist()
            
            # --- ไม้ตาย: สร้าง Query ที่ค้นหา "ทุกคอลัมน์" และ "ใช้ LIKE" เพื่อให้เจอแม้มีช่องว่าง ---
            # ใช้ TRIM เพื่อตัดสเปซบาร์ในฐานข้อมูลทิ้งตอนค้นหา
            where_clauses = [f"TRIM(CAST({col} AS STRING)) LIKE '%{search_val}%'" for col in cols]
            sql = f"SELECT * FROM `{full_table_id}` WHERE {' OR '.join(where_clauses)}"
            
            result_df = client.query(sql).to_dataframe()
            if not result_df.empty:
                found_results[table.table_id] = result_df

        if found_results:
            st.success(f"✅ เจอข้อมูล ID `{search_val}` แล้ว!")
            tab_objs = st.tabs(list(found_results.keys()))
            for i, (name, df) in enumerate(found_results.items()):
                with tab_objs[i]:
                    st.dataframe(df, use_container_width=True)
        else:
            st.warning(f"❌ ไม่พบข้อมูล `{search_val}` ในทุกแท็บ")
            # ถ้าหาไม่เจอ ให้โชว์ข้อมูล 3 แถวแรกของแท็บแรกมาให้พี่ดูเลยว่ามันพังตรงไหน
            st.info("💡 ตรวจสอบข้อมูลดิบในระบบ (3 แถวแรก):")
            first_table = list(client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))[0].table_id
            debug_df = client.query(f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{first_table}` LIMIT 3").to_dataframe()
            st.write(f"ตาราง: {first_table}")
            st.dataframe(debug_df)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
