import streamlit as st
import pandas as pd
import json
from gspread_pandas import Spread

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 6.0 - Success)")

# วิธีแก้ปัญหา PEM file: ใช้ฟันหนู 3 ตัวครอบ และลบตัว r ออกเพื่อให้ \n ทำงานจริง
config = {
  "type": "service_account",
  "project_id": "sturdy-sentry-487204-s4",
  "private_key_id": "4fbefa75020eff9412de6db7d4c8066191701729",
  "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDAeb4yvAeoaXeY
0P6chdrxg7CWntoFJ3mSLUeE6AqHOdasrRRXq+4XYo1zLyYStn4rgHoq02uqzlt7
dpmZtuQzA+jBBvrhYFKW+V9zuSRsJGSAHpGu4fzgzFxwIYmAzAz9LwpRId4WlnBx
6LsIYDEQkNWEVwc8J7mm+Ty2fwR92L02OYt+q3fs/72KYJx6sx4S9o1TJmg3hERF
ApTOvrYwwKyL6o1hLz5iqBJlu7zqddxpjFrTMRO0WP2AFE+zS9J1C2MXvRjZxUiC
6zhlQRF98EhFeBGA0prWheLgh9klCFPhf4VhPiFMZJdxT3/iUOoLoT5sCbc9vrNs
a9VamW/9AgMBAAECggEAAXbB+mvnyTR5WNbyfMyS05MefA+ViNEAS0GSmyFSeGCG
ME/sfFWd+baoIA5lfuJwirjb+2iz8RUuAnFVB6ODUE6d2rjIhMxnmTQPCwsHMSOR
hRzwAdFaGKtm1ftKhHy1nS5aQnw16ELFwUQIuiG7KQBYM2NTD+mdPDa5XlaQeVS+
v24FSf6Ry9zsWgrpfgUsFqtmpBRZpfyoJQ4zv2jzBLGHM8R0JHxWw7SgfRZ9653Y
tCYDHhdSN4/MU6jk/qIZDLKa5CcKZq5ORlJcucr+9LyzmCDtX95ojHgIL+8SDYrN
9YLiqSRXDqKC76wFKLxXecLzy2WAEHYmmDsrdyVeuQKBgQDjGEh7932diLrxsVqg
43OhyvVq5Sh48nGySZGf80Q2w34ToXKjKVacaVX1r8Mc+eJ+XEzzht8smbLoVt0c
HzWbdWv1r3hHIbCE02biIj90qrBBfSnL4l9yAfNN9f9JD1T/EnsRPGVoLww4aOFp
v44b+Kseej5tQmJnz7u98aOKGQKBgQDY+WpwQWCm8FC0PXMAHpkGmIqD16sGzIeg
lmtUvSBzVd4qpmOFLKI+Q0hONqlmIW9uYvVCHMRg1ZAUxZFcPaCcb23sPCkb7A2Y
z+5rs5mpfnPBOgEGriYcl8XwEhN4eopfJkD+snGK+zUaMcVbAWcY5xyqsSlFU+v4
NsiklqBZhQKBgQC4mhLCAusv1efxdLQxOPPUP4HERUfjGWHnBfrExSFcSwn/tyvT
ClWHi/D+aMP4mADPqwQ6qhZc0Qwn5gSTSaNwHcGG0/64A+DT+G0XwbNHiUEB21bQ
j9H6gS9g3mmI4Fe9iS5VUn00dZo/eLJUHgzNHBUuDz0T3/TSYoFA5F6GcQKBgQCE
tA9gduv5TlPd2ROECDLJsPRO7NIih2eQVU9x9XZqdCM8bKXDpufYMuh/RblXyK1R
k16zv8pv+05zFd7wzpRz+Ub+zFDMThSG2O3Wm3MpEjkT/jjwcATJSh561WNpNXF5
/niUDmmZekkhKz2sinAW8As9brtyNoDFQCR5XdLWzQKBgCgF/CzhxPGBaBnFdFzU
4lbo613XhXKm+K5pfPasMUBgKhCaYOqBfC0AZyJum0GSIvfLpVHc8tKKYHviYB1i
6SZbUzglN/OO4sFkoHO2jSVXWyEcSNd5E9D+wbm6ql6GVJNVsVQfrTW5rs8E0i3m
yvS5OTW/FB7hVdn68wukD9aU
-----END PRIVATE KEY-----""",
  "client_email": "cs-search-key@sturdy-sentry-487204-s4.iam.gserviceaccount.com",
  "client_id": "104477133590766151969",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/cs-search-key%40sturdy-sentry-487204-s4.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

sheet_id = "1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA"

@st.cache_data
def load_data():
    spread = Spread(sheet_id, config=config)
    return {s.title: spread.sheet_to_df(index=0, sheet=s.title) for s in spread.sheets}

try:
    all_sheets = load_data()
    tab_choice = st.selectbox("📂 เลือกแท็บหลัก:", list(all_sheets.keys()))
    search_query = st.text_input("🔍 ค้นหาข้อมูล (ID, IMEI, ชื่อ):")

    if search_query:
        df = all_sheets[tab_choice]
        result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
        if not result.empty:
            st.success(f"✅ พบ {len(result)} รายการ")
            st.dataframe(result, use_container_width=True)
        else:
            st.warning("❌ ไม่พบข้อมูล")
except Exception as e:
    st.error(f"การเชื่อมต่อขัดข้อง: {e}")
