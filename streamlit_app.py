import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

# เพิ่ม Scopes เพื่อให้กุญแจมีสิทธิ์เข้าถึงทั้ง BigQuery และ Google Drive (Sheets)
scopes = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/bigquery"
]

try:
    # อ่านกุญแจจากไฟล์ key.json พร้อมระบุ Scopes ที่จำเป็น
    credentials = service_account.Credentials.from_service_account_file(
        'key.json', 
        scopes=scopes
    )
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
except Exception as e:
    st.error(f"ระบบหาไฟล์ key.json ไม่เจอ หรือไฟล์พังครับ: {e}")
    st.stop()

st.title("⚡ ระบบค้นหาข้อมูลพนักงาน")
search_id = st.text_input("กรอก ID พนักงาน:")

if search_id:
    query = f"SELECT * FROM `sturdy-sentry-487204-s4.cs_database.case_2025` WHERE string_field_4 = '{search_id}'"
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            st.success("พบข้อมูล!")
            st.dataframe(df)
        else:
            st.warning("ไม่พบข้อมูลสำหรับ ID นี้")
    except Exception as e:
        # ถ้ายังขึ้น 403 ให้ลองรีเฟรชหน้าแอปอีกทีครับ
        st.error(f"เกิดข้อผิดพลาด: {e}")
