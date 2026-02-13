import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="BigQuery Turbo Search", layout="wide")
st.title("🚀 ระบบค้นหา BigQuery ความเร็วสูง")

# --- 1. จัดการความปลอดภัย (ดึงกุญแจจาก Secrets) ---
@st.cache_resource
def get_bigquery_client():
    try:
        conf = dict(st.secrets["gcp_service_account"])
        conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        
        # ใส่ Scopes ให้ครบเพื่อป้องกัน Error 403
        scopes = ["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/drive"]
        creds = service_account.Credentials.from_service_account_info(conf, scopes=scopes)
        
        return bigquery.Client(credentials=creds, project=creds.project_id)
    except Exception as e:
        st.error(f"❌ กุญแจมีปัญหา: {e}")
        return None

client = get_bigquery_client()

# --- 2. ส่วนการค้นหา (ทำงานที่ฝั่ง BigQuery เลย) ---
search_query = st.text_input("🔍 ใส่ ID เพื่อค้นหาทันที:", placeholder="เช่น 14833323")

if client and search_query:
    st.markdown(f"🔍 กำลังค้นหา: `{search_query}`")
    
    # ระบุชื่อโปรเจกต์และตารางของพี่
    TABLE_ID = "sturdy-sentry-487204-s4.cs_database.case_2025"
    
    # ใช้ SQL Query (เร็วกว่าโหลดมาทั้งไฟล์เยอะมากครับพี่)
    # ค้นหาในคอลัมน์ string_field_4 (หรือเปลี่ยนเป็นคอลัมน์ที่พี่ต้องการ)
    sql = f"""
        SELECT * FROM `{TABLE_ID}` 
        WHERE CAST(string_field_4 AS STRING) LIKE '%{search_query}%'
        LIMIT 100
    """
    
    try:
        with st.spinner("🚀 BigQuery กำลังประมวลผล..."):
            df = client.query(sql).to_dataframe()
        
        if not df.empty:
            st.success(f"✅ พบข้อมูล {len(df)} รายการ")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning(f"❌ ไม่พบข้อมูล '{search_query}'")
            
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")

else:
    st.info("💡 พิมพ์ ID ด้านบนเพื่อค้นหาข้อมูลจาก BigQuery ได้ทันทีครับ")
