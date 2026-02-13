import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="CS Mega Search", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (ID / IMEI)")

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
# รับค่าได้ทั้ง ID หรือ IMEI
search_val = st.text_input("🔍 กรอก ID หรือ IMEI ที่ต้องการค้นหา:", placeholder="เช่น 9300191 หรือเลข IMEI ยาวๆ")

if client and search_val:
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    query_str = search_val.strip()
    
    try:
        # 1. ดึงรายชื่อตาราง (แท็บ) ทั้งหมด
        tables = client.list_tables(f"{PROJECT_ID}.{DATASET_ID}")
        found_data = {}

        with st.spinner('🚀 กำลังค้นหาในทุกแท็บอย่างละเอียด...'):
            for table in tables:
                table_full_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
                
                # 2. ดึงข้อมูลทั้งหมดของแท็บนั้นออกมา (แก้ปัญหาเรื่องหัวตารางเลื่อน)
                df_all = client.query(f"SELECT * FROM `{table_full_id}`").to_dataframe()
                
                if not df_all.empty:
                    # 3. ค้นหาแบบ "เจอที่ไหนก็ได้ในแถวนั้น" (Case-insensitive)
                    # ไม่ว่าพี่จะกรอก ID หรือ IMEI มันจะเช็กให้ทุกช่องครับ
                    mask = df_all.astype(str).apply(lambda x: x.str.contains(query_str, case=False, na=False)).any(axis=1)
                    result_df = df_all[mask]
                    
                    if not result_df.empty:
                        found_data[table.table_id] = result_df

        # --- แสดงผลลัพธ์แยกตามแท็บให้เหมือน Original File ---
        if found_data:
            st.success(f"✅ พบข้อมูลที่เกี่ยวข้องกับ `{query_str}` ใน {len(found_data)} แท็บ")
            
            # สร้างแถบ Tabs ด้านบนตามชื่อแท็บที่เจอข้อมูลจริง
            tab_list = st.tabs(list(found_data.keys()))
            
            for i, (tab_name, df) in enumerate(found_data.items()):
                with tab_list[i]:
                    st.subheader(f"📂 แท็บ: {tab_name}")
                    # แสดงข้อมูลหน้าตาเหมือนใน Google Sheet
                    st.dataframe(df, use_container_width=True)
        else:
            st.warning(f"❌ ไม่พบข้อมูล `{query_str}` ในแท็บไหนเลยครับ")
            
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
else:
    st.info("💡 กรุณากรอก ID หรือ IMEI เพื่อเริ่มค้นหาข้อมูลจากทุกแท็บ")
