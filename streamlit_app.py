import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="CS Search Original", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูลพนักงาน (ทุกแท็บ)")

# --- 1. เชื่อมต่อกุญแจไฟล์ key.json ---
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

# --- 2. ส่วนการค้นหา ---
search_id = st.text_input("🔍 กรอกข้อมูลเพื่อค้นหา")

if client and search_id:
    # ระบุ Dataset ของพี่ที่ดูจากรูป
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    search_val = search_id.strip()
    
    try:
        # ดึงรายชื่อตารางทั้งหมดใน Dataset (เหมือนชื่อแท็บใน Sheets)
        tables = client.list_tables(f"{PROJECT_ID}.{DATASET_ID}")
        found_data = {} # เก็บข้อมูล { 'ชื่อแท็บ': DataFrame }

        with st.spinner('🚀 กำลังค้นหาข้อมูลจากทุกแท็บ...'):
            for table in tables:
                table_full_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
                
                # ดึงหัวตารางมาเช็กว่าตารางนี้มีคอลัมน์อะไรบ้าง
                schema_df = client.query(f"SELECT * FROM `{table_full_id}` LIMIT 1").to_dataframe()
                cols = schema_df.columns.tolist()
                
                # --- ไม้ตาย: ค้นหา ID จาก "ทุกคอลัมน์" ในตารางนี้ ---
                # ใช้ LIKE เพื่อให้เจอแม้จะมีช่องว่างแฝงอยู่ใน Sheets
                where_clauses = [f"CAST({col} AS STRING) LIKE '%{search_val}%'" for col in cols]
                sql = f"SELECT * FROM `{table_full_id}` WHERE {' OR '.join(where_clauses)}"
                
                result_df = client.query(sql).to_dataframe()
                if not result_df.empty:
                    found_data[table.table_id] = result_df

        # --- 3. แสดงผลแยกตามแท็บเหมือนในไฟล์ต้นฉบับ ---
        if found_data:
            st.success(f"✅ พบข้อมูล ID `{search_val}` ใน {len(found_data)} แท็บ")
            
            # สร้างแถบ Tabs ด้านบนตามชื่อแท็บที่เจอข้อมูล
            tab_objs = st.tabs(list(found_data.keys()))
            
            for i, (tab_name, df) in enumerate(found_data.items()):
                with tab_objs[i]:
                    st.write(f"📂 ข้อมูลจากตาราง: **{tab_name}**")
                    # แสดงตารางแบบเต็มความกว้างเหมือนเปิด Sheet ดู
                    st.dataframe(df, use_container_width=True)
        else:
            st.error(f"❌ ไม่พบข้อมูล `{search_val}` ในแท็บไหนเลยครับพี่")
            # Debug: โชว์ข้อมูลตารางแรกให้เห็นว่าตอนนี้ระบบ "เห็น" อะไรอยู่
            first_table = list(client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))[0].table_id
            st.info(f"💡 ตรวจสอบข้อมูลดิบในตาราง `{first_table}` (3 แถวแรก):")
            debug_df = client.query(f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{first_table}` LIMIT 3").to_dataframe()
            st.dataframe(debug_df)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
