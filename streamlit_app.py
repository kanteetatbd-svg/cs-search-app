import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd

# 1. กำหนดสิทธิ์ให้ครอบคลุมทั้ง BigQuery และ Sheets (Drive)
scopes = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/bigquery"
]

# 2. เชื่อมต่อระบบกุญแจ
try:
    credentials = service_account.Credentials.from_service_account_file('key.json', scopes=scopes)
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
except Exception as e:
    st.error(f"❌ ปัญหาเรื่องกุญแจ: {e}")
    st.stop()

st.title("🔍 ระบบค้นหาข้อมูลเคสพนักงาน")

# 3. ส่วนการค้นหา
search_id = st.text_input("กรอก ID พนักงาน (เช่น 9300191):")

if search_id:
    # 💥 จุดสำคัญ: เราจะดึงข้อมูลมาเช็กก่อนว่า BigQuery เห็นชื่อคอลัมน์ว่าอะไร
    table_id = "sturdy-sentry-487204-s4.cs_database.case_2025"
    
    try:
        # ดึงข้อมูล 1 แถวมาเพื่อเช็กชื่อคอลัมน์จริงๆ
        check_df = client.query(f"SELECT * FROM `{table_id}` LIMIT 1").to_dataframe()
        columns = check_df.columns.tolist()
        
        # ค้นหาว่า ID อยู่ในคอลัมน์ไหน (ลองไล่เช็กจากคอลัมน์ที่ 1-6)
        # โดยปกติถ้าไม่มีหัวตาราง มันจะชื่อ string_field_4 สำหรับคอลัมน์ E
        target_col = ""
        if "ID" in columns:
            target_col = "ID"
        elif "string_field_4" in columns:
            target_col = "string_field_4"
        else:
            # ถ้าไม่เจอทั้งคู่ ให้หาคอลัมน์ที่ดูน่าจะเป็น ID ที่สุด
            target_col = columns[4] if len(columns) > 4 else columns[0]

        # 4. เริ่ม Query ค้นหาของจริง
        query = f"SELECT * FROM `{table_id}` WHERE CAST({target_col} AS STRING) = '{search_id}'"
        df = client.query(query).to_dataframe()

        if not df.empty:
            st.success(f"✅ พบข้อมูลในคอลัมน์ [{target_col}]")
            st.dataframe(df)
        else:
            st.warning(f"❓ ไม่พบข้อมูล ID: {search_id}")
            st.info("💡 นี่คือหน้าตาคอลัมน์ที่ระบบเห็นตอนนี้:")
            st.write(check_df) # โชว์ให้พี่เห็นเลยว่าระบบเห็นหัวตารางเป็นคำว่าอะไร
            
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
