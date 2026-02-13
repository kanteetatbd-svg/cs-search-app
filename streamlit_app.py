import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

# สั่งให้แอปอ่านกุญแจจากไฟล์ key.json โดยตรง
try:
    credentials = service_account.Credentials.from_service_account_file('key.json')
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
except Exception as e:
    st.error(f"ระบบหาไฟล์กุญแจไม่เจอ หรือไฟล์พังครับ: {e}")
    st.stop()

st.title("⚡ ระบบค้นหาข้อมูลพนักงาน")

search_id = st.text_input("กรอก ID พนักงาน:")

if search_id:
    # ค้นหาจาก string_field_4 (ID)
    query = f"SELECT * FROM `sturdy-sentry-487204-s4.cs_database.case_2025` WHERE string_field_4 = '{search_id}'"
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            st.success("พบข้อมูล!")
            st.dataframe(df)
        else:
            st.warning("ไม่พบข้อมูลสำหรับ ID นี้")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
