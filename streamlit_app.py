import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd

# ฝังกุญแจแบบข้อความยาวพิเศษ (Triple Quotes) เพื่อกัน Error ทุกชนิด
private_key_raw = """-----BEGIN PRIVATE KEY-----
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
nlmtUvSBzVd4qpmOFLKI+Q0hONqlmIW9uYvVCHMRg1ZAUxZFcPaCcb23sPCkb7A2Y
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
-----END PRIVATE KEY-----"""

info = {
  "type": "service_account",
  "project_id": "sturdy-sentry-487204-s4",
  "private_key_id": "4fbefa75020eff9412de6db7d4c8066191701729",
  "private_key": private_key_raw.replace("\\n", "\n"),
  "client_email": "cs-search-key@sturdy-sentry-487204-s4.iam.gserviceaccount.com",
  "client_id": "104477133590766151969",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/cs-search-key%40sturdy-sentry-487204-s4.iam.gserviceaccount.com"
}

credentials = service_account.Credentials.from_service_account_info(info)
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

st.title("ระบบค้นหาข้อมูลเคส")

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
