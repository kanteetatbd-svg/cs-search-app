import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

# --- 1. ตั้งค่าพื้นฐาน ---
st.set_page_config(page_title="CS Search Reset", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล (เวอร์ชัน Reset)")

# --- 2. เชื่อมต่อกุญแจโดยตรงจากไฟล์ key.json ---
@st.cache_resource
def get_client():
    try:
        # สิทธิ์การเข้าถึง BigQuery และ Google Drive (Sheets)
        scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/drive"
        ]
        # อ่านจากไฟล์ที่พี่อัปโหลดขึ้น GitHub เป๊ะๆ
        creds = service_account.Credentials.from_service_account_file('key.json', scopes=scopes)
        return bigquery.Client(credentials=creds, project=creds.project_id)
    except Exception as e:
        st.error(f"❌ ระบบหาไฟล์ key.json ไม่เจอ หรือไฟล์พัง: {e}")
        return None

client = get_client()

# --- 3. ส่วนค้นหาข้อมูล ---
search_id = st.text_input("🔍 กรอก ID เพื่อค้นหา (เช่น 9300191):")

if client and search_id:
    # ระบุชื่อตารางของพี่
    TABLE_ID = "sturdy-sentry-487204-s4.cs_database.case_2025"
    
    # ใช้ Query แบบกว้าง ค้นหาใน string_field_4 (คอลัมน์ E ใน Sheets)
    sql = f"SELECT * FROM `{TABLE_ID}` WHERE CAST(string_field_4 AS STRING) = '{search_id}'"
    
    try:
        df = client.query(sql).to_dataframe()
        if not df.empty:
            st.success(f"✅ พบข้อมูลสำหรับ ID: {search_id}")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning(f"❌ ไม่พบข้อมูล '{search_id}' ในคอลัมน์ string_field_4")
            # ถ้าหาไม่เจอ ให้โชว์ 3 แถวแรกมาเช็กชื่อคอลัมน์กันตรงๆ เลยพี่
            st.info("ตรวจสอบชื่อคอลัมน์จริงจากตารางด้านล่างนี้ครับ:")
            preview = client.query(f"SELECT * FROM `{TABLE_ID}` LIMIT 3").to_dataframe()
            st.dataframe(preview)
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
