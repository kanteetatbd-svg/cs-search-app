import streamlit as st
import pandas as pd
from gspread_pandas import Spread

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 9.0 - Final)")

# ข้อมูลกุญแจลับ (จัดรูปแบบใหม่เพื่อลด Error 100%)
config = {
  "type": "service_account",
  "project_id": "sturdy-sentry-487204-s4",
  "private_key_id": "4fbefa75020eff9412de6db7d4c8066191701729",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDAeb4yvAeoaXeY\n0P6chdrxg7CWntoFJ3mSLUeE6AqHOdasrRRXq+4XYo1zLyYStn4rgHoq02uqzlt7\ndpmZtuQzA+jBBvrhYFKW+V9zuSRsJGSAHpGu4fzgzFxwIYmAzAz9LwpRId4WlnBx\n6LsIYDEQkNWEVwc8J7mm+Ty2fwR92L02OYt+q3fs/72KYJx6sx4S9o1TJmg3hERF\nApTOvrYwwKyL6o1hLz5iqBJlu7zqddxpjFrTMRO0WP2AFE+zS9J1C2MXvRjZxUiC\n6zhlQRF98EhFeBGA0prWheLgh9klCFPhf4VhPiFMZJdxT3/iUOoLoT5sCbc9vrNs\na9VamW/9AgMBAAECggEAAXbB+mvnyTR5WNbyfMyS05MefA+ViNEAS0GSmyFSeGCG\nME/sfFWd+baoIA5lfuJwirjb+2iz8RUuAnFVB6ODUE6d2rjIhMxnmTQPCwsHMSOR\nhRzwAdFaGKtm1ftKhHy1nS5aQnw16ELFwUQIuiG7KQBYM2NTD+mdPDa5XlaQeVS+\nv24FSf6Ry9zsWgrpfgUsFqtmpBRZpfyoJQ4zv2jzBLGHM8R0JHxWw7SgfRZ9653Y\ntCYDHhdSN4/MU6jk/qIZDLKa5CcKZq5ORlJcucr+9LyzmCDtX95ojHgIL+8SDYrN\n9YLiqSRXDqKC76wFKLxXecLzy2WAEHYmmDsrdyVeuQKBgQDjGEh7932diLrxsVqg\n43OhyvVq5Sh48nGySZGf80Q2w34ToXKjKVacaVX1r8Mc+eJ+XEzzht8smbLoVt0c\nHzWbdWv1r3hHIbCE02biIj90qrBBfSnL4l9yAfNN9f9JD1T/EnsRPGVoLww4aOFp\nv44b+Kseej5tQmJnz7u98aOKGQKBgQDY+WpwQWCm8FC0PXMAHpkGmIqD16sGzIeg\nlmtUvSBzVd4qpmOFLKI+Q0hONqlmIW9uYvVCHMRg1ZAUxZFcPaCcb23sPCkb7A2Y\nz+5rs5mpfnPBOgEGriYcl8XwEhN4eopfJkD+snGK+zUaMcVbAWcY5xyqsSlFU+v4\NsiklqBZhQKBgQC4mhLCAusv1efxdLQxOPPUP4HERUfjGWHnBfrExSFcSwn/tyvT\nClWHi/D+aMP4mADPqwQ6qhZc0Qwn5gSTSaNwHcGG0/64A+DT+G0XwbNHiUEB21bQ\nj9H6gS9g3mmI4Fe9iS5VUn00dZo/eLJUHgzNHBUuDz0T3/TSYoFA5F6GcQKBgQCE\ntA9gduv5TlPd2ROECDLJsPRO7NIih2eQVU9x9XZqdCM8bKXDpufYMuh/RblXyK1R\nk16zv8pv+05zFd7wzpRz+Ub+zFDMThSG2O3Wm3MpEjkT/jjwcATJSh561WNpNXF5\n/niUDmmZekkhKz2sinAW8As9brtyNoDFQCR5XdLWzQKBgCgF/CzhxPGBaBnFdFzU\n4lbo613XhXKm+K5pfPasMUBgKhCaYOqBfC0AZyJum0GSIvfLpVHc8tKKYHviYB1i\n6SZbUzglN/OO4sFkoHO2jSVXWyEcSNd5E9D+wbm6ql6GVJNVsVQfrTW5rs8E0i3m\nyvS5OTW/FB7hVdn68wukD9aU\n-----END PRIVATE KEY-----\n",
  "client_email": "cs-search-key@sturdy-sentry-487204-s4.iam.gserviceaccount.com",
  "token_uri": "https://oauth2.googleapis.com/token"
}

sheet_id = "1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA"

@st.cache_data(ttl=300)
def load_all_sheets():
    try:
        # เชื่อมต่อ Google Sheets
        spread = Spread(sheet_id, config=config)
        # ดึงทุกแท็บที่มีข้อมูล
        data_dict = {}
        for s in spread.sheets:
            df = spread.sheet_to_df(index=0, sheet=s.title)
            if not df.empty:
                data_dict[s.title] = df
        return data_dict
    except Exception as e:
        return str(e)

# เรียกใช้งานข้อมูล
all_data = load_all_sheets()

if isinstance(all_data, str):
    st.error(f"❌ การเชื่อมต่อขัดข้อง: {all_data}")
    st.info("แนะนำ: ตรวจสอบว่าได้แชร์ไฟล์ให้ Email Service Account ในโหมด Editor หรือยัง")
else:
    # หน้าจอค้นหา
    tab_names = list(all_data.keys())
    if tab_names:
        choice = st.selectbox("📂 เลือกหมวดหมู่ที่ต้องการค้นหา:", tab_names)
        query = st.text_input(f"🔍 ค้นหาในหมวด [{choice}] (ID, IMEI, ชื่อ):")
        
        if query:
            df_selected = all_data[choice]
            result = df_selected[df_selected.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)]
            if not result.empty:
                st.success(f"✅ พบ {len(result)} รายการ")
                st.dataframe(result, use_container_width=True)
            else:
                st.warning("❌ ไม่พบข้อมูล")
    else:
        st.warning("⚠️ ไม่พบข้อมูลในไฟล์ Google Sheets")
