import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="Debug Search", layout="wide")
st.title("🔎 ระบบสแกนหา ID (เวอร์ชันละเอียด)")

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
search_id = st.text_input("🔍 ใส่ ID พนักงาน:")

if client and search_id:
    project_id = "sturdy-sentry-487204-s4"
    dataset_id = "cs_database"
    
    try:
        tables = client.list_tables(f"{project_id}.{dataset_id}")
        found_any = False

        for table in tables:
            full_table_id = f"{project_id}.{dataset_id}.{table.table_id}"
            
            # ดึงข้อมูล 5 แถวแรกมาโชว์ให้พี่ดูเลยว่า 'ของจริง' หน้าตาเป็นไง
            st.write(f"📊 กำลังค้นหาในตาราง: `{table.table_id}`")
            sample_df = client.query(f"SELECT * FROM `{full_table_id}` LIMIT 5").to_dataframe()
            
            # สร้าง Query ที่ 'ตัดช่องว่าง' และ 'ค้นหาแบบยืดหยุ่น'
            # ค้นหาทุกคอลัมน์ โดยตัด Space ทิ้งก่อนเทียบ
            where_clauses = [f"TRIM(CAST({col} AS STRING)) = '{search_id.strip()}'" for col in sample_df.columns]
            sql = f"SELECT * FROM `{full_table_id}` WHERE {' OR '.join(where_clauses)}"
            
            result_df = client.query(sql).to_dataframe()
            
            if not result_df.empty:
                found_any = True
                st.success(f"✅ เจอแล้วในตาราง {table.table_id}!")
                st.dataframe(result_df)
            else:
                # ถ้าไม่เจอ โชว์ข้อมูลที่มันมีอยู่ให้พี่ดู 5 แถว เพื่อเทียบว่าเราพิมพ์ผิดตรงไหน
                with st.expander(f"❌ ไม่พบใน {table.table_id} (คลิกเพื่อดูข้อมูลตัวอย่างในตารางนี้)"):
                    st.write("นี่คือข้อมูล 5 แถวแรกที่ระบบเห็นตอนนี้:")
                    st.dataframe(sample_df)

        if not found_any:
            st.error(f"หา ID `{search_id}` ไม่พบในทุกตารางครับพี่")

    except Exception as e:
        st.error(f"Error: {e}")
