import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

# Scopes สำหรับสิทธิ์เข้าถึง Sheets และ BigQuery
scopes = ["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/drive"]

try:
    credentials = service_account.Credentials.from_service_account_file('key.json', scopes=scopes)
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
except Exception as e:
    st.error(f"Error กุญแจ: {e}")
    st.stop()

st.title("ระบบค้นหาข้อมูลเคสพนักงาน")
search_id = st.text_input("กรอก ID พนักงาน:")

if search_id:
    # 1. ลองค้นหาแบบกว้าง (ลองทุกคอลัมน์ที่เป็นไปได้)
    # จากรูป Sheets ของพี่ (image_972b99.jpg) ID อยู่คอลัมน์ E ซึ่งปกติคือ string_field_4
    query = f"""
        SELECT * FROM `sturdy-sentry-487204-s4.cs_database.case_2025` 
        WHERE string_field_4 = '{search_id}'
    """
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            st.success(f"เจอข้อมูลแล้ว!")
            st.dataframe(df)
        else:
            st.warning(f"ไม่พบข้อมูล ID: {search_id} ในคอลัมน์มาตรฐาน")
            
            # 2. จุดตาย: โชว์ข้อมูล 5 แถวแรกให้พี่ดูเลยว่า 'ชื่อคอลัมน์' จริงๆ คืออะไร
            st.info("ตรวจสอบชื่อคอลัมน์จากข้อมูลจริงด้านล่างนี้ครับ:")
            preview_query = "SELECT * FROM `sturdy-sentry-487204-s4.cs_database.case_2025` LIMIT 5"
            preview_df = client.query(preview_query).to_dataframe()
            st.dataframe(preview_df)
            
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
