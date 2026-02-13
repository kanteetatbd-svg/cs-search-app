import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

# 1. ใช้ Scopes เพื่อให้เข้าถึง Sheets ได้ (จุดที่ติดเมื่อเช้า)
scopes = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/bigquery"
]

# 2. ดึงกุญแจจากไฟล์ key.json ที่พี่อัปโหลดไว้
try:
    credentials = service_account.Credentials.from_service_account_file(
        'key.json', 
        scopes=scopes
    )
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
except Exception as e:
    st.error(f"Error กุญแจ: {e}")
    st.stop()

st.title("ระบบค้นหาข้อมูลเคสพนักงาน")

# 3. ช่องกรอก ID
search_id = st.text_input("กรอก ID พนักงานที่ต้องการค้นหา:")

if search_id:
    # 4. ใช้ Query ตามโครงสร้างที่พี่เคยบอกว่าใช้ได้ (ค้นหาจาก ID)
    # ผมใส่ CAST เพื่อกันเหนียวเผื่อระบบมอง ID เป็นตัวเลขหรือตัวอักษรไม่ตรงกัน
    query = f"""
        SELECT * FROM `sturdy-sentry-487204-s4.cs_database.case_2025` 
        WHERE ID = '{search_id}' 
        OR CAST(ID AS STRING) = '{search_id}'
    """
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            st.write("### ผลการค้นหา:")
            st.dataframe(df)
        else:
            st.warning(f"ไม่พบข้อมูลสำหรับ ID: {search_id}")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
