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

# --- จุดเร่งสปีด 1: จำรายชื่อแท็บไว้ ไม่ต้องโหลดใหม่ทุกรอบ ---
@st.cache_data(ttl=600) # จำไว้ 10 นาที
def get_all_tables(_client, project_id, dataset_id):
    return list(_client.list_tables(f"{project_id}.{dataset_id}"))

client = get_bq_client()
search_val = st.text_input("🔍 กรอก ID หรือ IMEI แล้วกด Enter")

if client and search_val:
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    q = search_val.strip()
    
    try:
        tables = get_all_tables(client, PROJECT_ID, DATASET_ID)
        found_data = {}

        with st.spinner('🚀 กำลังประมวลผล...'):
            for table in tables:
                table_full_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
                
                # --- จุดเร่งสปีด 2: ดึงเฉพาะ Schema มาสร้าง SQL (ไม่โหลดข้อมูลจริง) ---
                table_obj = client.get_table(table_full_id)
                columns = [field.name for field in table_obj.schema]
                
                # ค้นหาทุกคอลัมน์ในคำสั่งเดียว
                where_clause = " OR ".join([f"CAST({col} AS STRING) LIKE '%{q}%'" for col in columns])
                sql = f"SELECT * FROM `{table_full_id}` WHERE {where_clause}"
                
                # รัน SQL ฝั่ง Server (คืนค่าเฉพาะแถวที่เจอ)
                df = client.query(sql).to_dataframe()
                
                if not df.empty:
                    found_data[table.table_id] = df

        if found_data:
            st.success(f"✅ ค้นหาเสร็จสิ้น!")
            tabs = st.tabs(list(found_data.keys()))
            for i, (name, df) in enumerate(found_data.items()):
                with tabs[i]:
                    st.subheader(f"📂 แท็บ: {name}")
                    st.dataframe(df, use_container_width=True)
        else:
            st.warning(f"❌ ไม่พบข้อมูล `{q}` ในทุกแท็บ")
            
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
