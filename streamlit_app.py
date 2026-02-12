import streamlit as st
import pandas as pd
import json
import base64
from gspread_pandas import Spread

st.set_page_config(page_title="CS Search System", layout="wide")
st.title("🚀 ระบบค้นหาข้อมูล CS (Version 10.0 - SUCCESS)")

# รหัสลับแบบ Base64 (ตัดปัญหาเรื่องเว้นบรรทัดและอักขระพิเศษออก 100%)
encoded_key = "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogInN0dXJkeS1zZW50cnktNDg3MjA0LXM0IiwgInByaXZhdGVfa2V5X2lkIjogIjRmYmVmYTc1MDIwZWZmOTQxMmRlNmRiN2Q0YzgwNjYxOTE3MDE3MjkiLCAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdm9JQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLZ3dnZ1NrQWdFQUFvSUJBUURBZWInInB5dkFlb2FYZVlcblBKNmNoZHJ4ZzdDV250b0ZKM21TTFVlRTZBcUhPZGFzclJSWHErNFhZbzF6THlZU3RuNHJnSG9xMDJ1cXpsdDdcbmRwbVp0dVF6QStqQkJ2cmhZRktXK1Y5enVTUnNKR1NBSHBHdTRmZ2d6Rnh3SVltQXpBejlMd3BSSWQ0V2xuQnhcbmZMczlZREVRa05XRVZ3YzhKN21tK1R5MmZ3UjkyTDAyT1l0K3EzZnMvNzJLWWp4NnN4NFM5bzFUSm1nM2hFUkZcbkFwVE92cll3d0t5TDZvMWhMeTVpcUJKbHU3enFkZHhwakZyVE1STzBXUDJBRkUrelM5SjFDMk1YdlJqWnhVaUNcbmZ6aGxRUkY5OEVoRmVCR0EwcHJXaGVMZ2g5a2xDRlBoZjRWaFBpRk1aSmR4VDMvaVVvTG9UNXNDYmM5dnJOc1xuYTlWYW1XLzlBZ01CQUFFQ2dnRUFBWGJCK212bnlUUjVXTmJ5Zk15UzA1TWVmQStWaU5FQVMwR1NteUZTZUdDR1xuTUUvc2ZGV2QrYmFvSUE1bGZ1SndpcmpiKzJpejhSVXVBbkZWQjZPRFVFNmRyaklIeE5ubVRRUEN3c0hNU09SXG5oUnp3QWRGYUdLdG0xZnRLSEh5MW5TNWFRbndzMTZFTEZ3VVF1aUc3S1FCWU0yTlREK21kUERhNVhsYVFlVlMrXG52MjRGU2Y2Unk5enNXZ3JwZmdVc0Zx dG1wQlJacGZ5b0pRN3Z2anpCTEdITThSM0pIeFcxN1NnZlJaOTY1M1lcbnRDeURIaGRTTjQvTVU2amticUl6RExLYTVDY0tacTVPUmxKY3Vjcis5THl6bUNEclg5NW9qSGdJTCs4U0RZck5cbnk1TGlxU1JYRHFLQzc2d0ZLTHhYZWNMenkyV0FFSFltbURzcmR5VmV1UUtCZ1FEnRHRWg3OTMyZGlMeHNoVnFnXG40M09oeXZWcTVTaDQ4bkd5U1pHZjg0UTJ3MzRUb1hLallWYWNhVlgycjhzTStlSitYRXp6aHQ4c21iTG9WdDBjXG5IeldiZFd2MXIzaEhJYkNFMmJpSajkwcXJCQmZTeUw0bDl5QWZOTjlmOUpEMVRFTW5TUlBHVm9Md3c0YU9GcFxuNTRiK0tzZWVqNXRRbUpuejd1OThhT0tHUU9CZ1FEWStMcHdRV0NtOEZDMFBYTUFIcGdtSXFEMTZzR3pJZWdcbmxtdFV2U0J6VmQ0cXBtT0ZMS0krUTBoT05xbG1JVzl1WXZWQ0hNUmcxWkFVWFpGY1BhQ2NiMjNzUENrYjdBMllclm5zNW1wZm5QQk9nRUdyaVljbDhYd0VoTjVlb3BmSmtEK3NuR0srelVhTWNWYkFXY1k1eHlxclNsRlUrdjRcbk5zaWtscUJaaFFLQmdRQzRtaExDQXVzdjFlZnhkRFF4T1BQVVA0SEVSVWZqR1dIbkJmckV4U0ZjU3duL3R5dlRcbkNsV0hpL0QrYU1QNG1BRFBxd1E2cWhaYzBRd241Z1NUU2FOd0hjR0cwLzY0QStEVCtHMFh3Yk5OaVVFQjIxYlFcbmo5SDZnUzl0M21tSTRGZTlpUzVWVW4wMFZaby9lTEpVSHd6TkhCVXVEejBUMy9UU1lvRkE1RjZHY1FLQmdRQ0VcdG5BOWdkdXY1VGxQZDJST0VDRExKc1BSTzdOSWloMmVRVlU5eDlyWnFkQ004YktYRHVmWU11aC9SYmxWeEsxUlxuazE2enY4cHYrMDV6RmQ3d3pwUnorVWIrekZETVRoU0cyTzNXbTNNcEVqa1Qvamp3Y0FUSlNoNTYxV05wTlhGNVxuL25pVURtbVplaytoS3oyc2luQVc4QXM5YnJ0eU5vREZRQ1I1WGRMV3pRS0JnQ2dGL0N6aHhQR0JhQm5GZEZ6VVxubDRsYm82MTNYaFhLbStLNXBmUGFzTVVCZ0toQ2FZT3FCZkMwQVp5SnVtMEdTSXZmTHBWSGM4dEtLWUh2aVlCMWlcbmU2U2JaVXpnbE4vT080c0Zrb0hPMmpTVlhXeUVjU05kNUU5RCt3Ym02cWw2R1ZKTlZzVlFmclRXNXJzOEUwaTNtXG55dlM1T1RXbi9GQjdWZG42OHd1a0Q5YVU9PSJ9"

# ฟังก์ชันกอดรหัสลับให้กลับมาเป็น JSON
def get_config():
    decoded_bytes = base64.b64decode(encoded_key)
    return json.loads(decoded_bytes)

config = get_config()
sheet_id = "1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA"

@st.cache_data(ttl=300)
def load_all_data():
    try:
        spread = Spread(sheet_id, config=config)
        all_tabs = {s.title: spread.sheet_to_df(index=0, sheet=s.title) for s in spread.sheets if not spread.sheet_to_df(index=0, sheet=s.title).empty}
        return all_tabs
    except Exception as e:
        return str(e)

all_sheets = load_all_data()

if isinstance(all_sheets, str):
    st.error(f"❌ การเชื่อมต่อขัดข้อง: {all_sheets}")
    st.info("ตรวจสอบว่าไฟล์ Google Sheets ได้แชร์ให้ Email ของ Service Account ในโหมด Editor หรือยัง")
else:
    tab_list = list(all_sheets.keys())
    if tab_list:
        selected_tab = st.selectbox("📂 เลือกหมวดหมู่ที่ต้องการค้นหา:", tab_list)
        search_query = st.text_input(f"🔍 ค้นหาในหมวด [{selected_tab}] (ID, IMEI, หรือชื่อ):")

        if search_query:
            df = all_sheets[selected_tab]
            result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
            
            if not result.empty:
                st.success(f"✅ พบข้อมูล {len(result)} รายการ")
                st.dataframe(result, use_container_width=True)
            else:
                st.warning("❌ ไม่พบข้อมูล")
    else:
        st.warning("⚠️ ไม่พบข้อมูลในไฟล์ Google Sheets")
