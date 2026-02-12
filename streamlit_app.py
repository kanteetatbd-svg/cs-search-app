import streamlit as st
from gspread_pandas import Spread

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (ตรวจสอบสถานะ)")

# ข้อมูลกุญแจที่พี่มี (ใส่ให้ครบทุกบรรทัดตามที่เคยทำครับ)
config = {
  "type": "service_account",
  "project_id": "sturdy-sentry-487204-s4",
  "private_key_id": "4fbefa75020eff9412de6db7d4c8066191701729",
  "private_key": """-----BEGIN PRIVATE KEY-----
(ก๊อปปี้กุญแจที่เว้นบรรทัดสวยงามของพี่มาวางตรงนี้ครับ)
-----END PRIVATE KEY-----""",
  "client_email": "cs-search-key@sturdy-sentry-487204-s4.iam.gserviceaccount.com",
  "token_uri": "https://oauth2.googleapis.com/token",
}

sheet_id = "1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA"

try:
    st.info("กำลังพยายามเชื่อมต่อ Google Sheets...")
    spread = Spread(sheet_id, config=config)
    
    # ดึงรายชื่อแท็บทั้งหมดมาโชว์เพื่อทดสอบสิทธิ์
    sheet_names = [s.title for s in spread.sheets]
    st.success(f"✅ เชื่อมต่อสำเร็จ! พบแท็บข้อมูล: {', '.join(sheet_names)}")
    
    selected_tab = st.selectbox("เลือกแท็บเพื่อดูข้อมูล:", sheet_names)
    df = spread.sheet_to_df(index=0, sheet=selected_tab)
    st.dataframe(df.head(10)) # โชว์ 10 แถวแรกเพื่อยืนยันว่าเห็นข้อมูล

except Exception as e:
    st.error("❌ การเชื่อมต่อล้มเหลว")
    st.write(f"สาเหตุที่แท้จริง: {e}")
    st.warning("คำแนะนำ: ตรวจสอบว่าได้เปิด Google Drive API และแชร์ไฟล์ให้ Email Service Account หรือยัง")
