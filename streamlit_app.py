import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="CS Case Finder Final", layout="wide")
st.title("🚀 ระบบดึงข้อมูลเคสพนักงาน (ค้นหาทุกซอกทุกมุม)")

# --- 1. เชื่อมต่อผ่านไฟล์ key.json โดยตรง ---
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
search_val = st.text_input("🔍 กรอก ID หรือ IMEI เพื่อดึงข้อมูลเคส:")

if client and search_val:
    PROJECT_ID = "sturdy-sentry-487204-s4"
    DATASET_ID = "cs_database"
    q = search_val.strip().lower()
    
    try:
        # ดึงรายชื่อตาราง (แท็บ) ทั้งหมด
        tables = list(client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))
        found_data = {}

        with st.spinner('🚀 กำลังควานหาข้อมูลจากทุกบรรทัด ทุกคอลัมน์...'):
            for table in tables:
                table_id = f"{PROJECT_ID}.{DATASET_ID}.{table.table_id}"
                
                # --- จุดสำคัญ: ดึงข้อมูลมาทั้งหมดโดยไม่มี LIMIT ---
                df = client.query(f"SELECT * FROM `{table_id}`").to_dataframe()
                
                if not df.empty:
                    # ค้นหาในทุกคอลัมน์ โดยแปลงทุกช่องเป็น String ก่อน
                    # วิธีนี้จะทำให้เจอ ID แม้จะอยู่บรรทัดที่เท่าไหร่ หรือคอลัมน์ไหนก็ตาม
                    mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(q, na=False).any(), axis=1)
                    res = df[mask]
                    
                    if not res.empty:
                        found_data[table.table_id] = res

        # --- แสดงผลลัพธ์แยกตามแท็บให้เหมือนในรูป image_a210ba.png ---
        if found_data:
            st.success(f"✅ เจอข้อมูลของ `{search_val}` แล้วพี่!")
            tab_objs = st.tabs(list(found_data.keys()))
            
            for i, (name, data) in enumerate(found_data.items()):
                with tab_objs[i]:
                    st.subheader(f"📂 ข้อมูลจากแท็บ: {name}")
                    # แสดงผลเป็นตารางกว้างๆ เหมือนใน Google Sheets เป๊ะๆ
                    st.dataframe(data, use_container_width=True)
        else:
            st.error(f"❌ ไม่พบข้อมูล `{search_val}` ในบรรทัดไหนเลยครับ")
            # ถ้ายังไม่เจอ ให้โชว์ข้อมูล 50 แถวแรกของแท็บแรกมาดูว่า BigQuery มันดึงอะไรมา
            if tables:
                st.info(f"💡 ข้อมูลที่ระบบ 'เห็น' ในตอนนี้ (ตัวอย่างจากแท็บแรก):")
                debug_df = client.query(f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{tables[0].table_id}` LIMIT 50").to_dataframe()
                st.dataframe(debug_df)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
