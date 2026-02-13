import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="CS Final Search", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล (เวอร์ชันกวาดทุกแท็บ)")

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
search_id = st.text_input("🔍 กรอก ID พนักงาน:")

if client and search_id:
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    search_val = search_id.strip()
    
    try:
        tables = client.list_tables(f"{PROJECT_ID}.{DATASET_ID}")
        found_data = {}

        for table in tables:
            full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
            # ดึงข้อมูลมาทั้งหมด (ไม่จำกัดแถว) เพื่อมาควานหาใน Python แทน
            df_all = client.query(f"SELECT * FROM `{full_table_id}`").to_dataframe()
            
            if not df_all.empty:
                # ค้นหา ID ในทุกคอลัมน์ โดยไม่สนแถวว่าง
                mask = df_all.astype(str).apply(lambda x: x.str.contains(search_val, case=False, na=False)).any(axis=1)
                result_df = df_all[mask]
                
                if not result_df.empty:
                    found_data[table.table_id] = result_df

        if found_data:
            st.success(f"✅ เจอข้อมูล ID `{search_val}` ในตารางด้านล่างครับ!")
            tabs = st.tabs(list(found_data.keys()))
            for i, (name, df) in enumerate(found_data.items()):
                with tabs[i]:
                    st.write(f"📂 ข้อมูลจากแท็บ: **{name}**")
                    st.dataframe(df, use_container_width=True)
        else:
            st.error(f"❌ ไม่พบ ID `{search_val}` ในระบบ (ตรวจสอบข้อมูลดิบด้านล่าง)")
            # โชว์ข้อมูล 50 แถวแรก เพื่อให้พี่เห็นว่าข้อมูลจริงๆ มันเริ่มที่แถวไหน
            first_table = list(client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))[0].table_id
            debug_df = client.query(f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{first_table}` LIMIT 50").to_dataframe()
            st.info(f"💡 ข้อมูลดิบ 50 แถวแรกของ {first_table}:")
            st.dataframe(debug_df)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
