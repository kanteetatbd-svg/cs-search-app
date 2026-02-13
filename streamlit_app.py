import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

# ดึงกุญแจจาก Secrets เท่านั้น (ห้ามฝังรหัสในโค้ดแล้ว เพราะมันจะพัง)
if "gcp_service_account" in st.secrets:
    info = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(info)
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
else:
    st.error("กุญแจในหน้า Secrets ยังใส่ไม่ครบครับ")
    st.stop()

st.title("⚡ ระบบค้นหาข้อมูล")
search_id = st.text_input("กรอก ID เพื่อค้นหา:")

if search_id:
    query = f"SELECT * FROM `sturdy-sentry-487204-s4.cs_database.case_2025` WHERE string_field_4 = '{search_id}'"
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            st.dataframe(df)
        else:
            st.warning("ไม่พบข้อมูล")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
