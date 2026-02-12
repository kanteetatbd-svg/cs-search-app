import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="CS BigQuery Turbo", layout="wide")
st.title("⚡ ระบบค้นหาความเร็วสูง (BigQuery Mode)")

# ฟังก์ชันเชื่อมต่อ BigQuery
@st.cache_resource
def get_bq_client():
    try:
        conf = dict(st.secrets["gcp_service_account"])
        conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        credentials = service_account.Credentials.from_service_account_info(conf)
        # เชื่อมกับโปรเจกต์ของพี่เก็ต
        client = bigquery.Client(credentials=credentials, project="sturdy-sentry-487204-s4")
        return client
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")
        return None

client = get_bq_client()

# ช่องค้นหา
search_query = st.text_input("🔍 ใส่ ID เพื่อค้นหาทันที:", placeholder="พิมพ์เลข ID เช่น 12123xxx")

if search_query and client:
    with st.spinner("🚀 กำลังค้นหาข้อมูล..."):
        # สั่งค้นหาในคอลัมน์ที่น่าจะเป็น ID (field_2)
        sql = f"""
            SELECT * FROM `sturdy-sentry-487204-s4.cs_database.case_2025` 
            WHERE 
                CAST(string_field_0 AS STRING) LIKE '%{search_query}%' OR
                CAST(string_field_1 AS STRING) LIKE '%{search_query}%' OR
                CAST(string_field_2 AS STRING) LIKE '%{search_query}%' OR
                CAST(string_field_3 AS STRING) LIKE '%{search_query}%'
            LIMIT 100
        """
        
        try:
            query_job = client.query(sql)
            results = query_job.to_dataframe()

            if not results.empty:
                st.success(f"✅ พบข้อมูล {len(results)} รายการ")
                st.dataframe(results, use_container_width=True)
            else:
                st.warning(f"❌ ไม่พบข้อมูลสำหรับ '{search_query}'")
        except Exception as e:
            st.error(f"Error: {e}")
else:
    st.info("💡 พิมพ์ข้อมูลด้านบนเพื่อเริ่มการค้นหาครับ")
