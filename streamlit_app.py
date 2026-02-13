import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import concurrent.futures # ตัวช่วยดึงข้อมูลพร้อมกันทุกแท็บ

st.set_page_config(page_title="CS Case Finder TURBO", layout="wide")
st.title("🚀 ระบบค้นหาเคส CS")

# --- 1. การเชื่อมต่อกุญแจ ---
@st.cache_resource
def get_sheets_client():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('key.json', scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Key Error: {e}")
        return None

# ฟังก์ชันดึงข้อมูล 1 แท็บ
def fetch_worksheet(ws):
    data = ws.get_all_values()
    if data:
        return ws.title, pd.DataFrame(data)
    return ws.title, pd.DataFrame()

# --- 2. ฟังก์ชันโหลดข้อมูลทั้งหมดมาเก็บใน "แคช" ---
# ตั้งเวลาไว้ 15 นาที (900 วินาที) ข้อมูลจะรีเฟรชเอง หรือกดปุ่มรีเฟรชเองก็ได้
@st.cache_data(ttl=900)
def load_all_worksheets_to_memory():
    gc = get_sheets_client()
    if not gc: return {}
    
    sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
    worksheets = sh.worksheets()
    all_data = {}
    
    # ใช้ระบบ Thread ดึงข้อมูลทุกแท็บพร้อมกัน (เร็วขึ้น 5-10 เท่า)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(fetch_worksheet, worksheets))
        for title, df in results:
            if not df.empty:
                all_data[title] = df
    return all_data

# --- 3. ส่วนการทำงานหลัก ---

# ปุ่มรีเฟรชข้อมูลเผื่อพี่มีการแก้ใน Sheets แล้วอยากให้อัปเดตทันที
if st.sidebar.button("🔄 อัปเดตข้อมูลใหม่จาก Sheets"):
    st.cache_data.clear()
    st.rerun()

# โหลดข้อมูลรอไว้เลย
with st.spinner('🚀 กำลังเตรียมข้อมูลให้พร้อมใช้งาน (โหลดครั้งเดียว)...'):
    master_data = load_all_worksheets_to_memory()

st.sidebar.info(f"📊 โหลดข้อมูลจาก {len(master_data)} แท็บเรียบร้อยแล้ว!")

search_val = st.text_input("🔍 กรอก ID หรือ IMEI เพื่อค้นหา")

if search_val:
    q = search_val.strip().lower()
    found_results = {}

    # ค้นหาจากข้อมูลในแรม (ไม่ต้องรอโหลดจากเน็ตแล้ว)
    for title, df in master_data.items():
        mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(q, na=False).any(), axis=1)
        res = df[mask]
        
        if not res.empty:
            found_results[title] = res

    # แสดงผลแบบเรียงต่อกันลงมา
    if found_results:
        st.success(f"✅ เจอข้อมูล `{search_val}` ใน {len(found_results)} แท็บ")
        for name, res_df in found_results.items():
            st.markdown(f"### 📂 แท็บ: {name}")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            st.divider()
    else:
        st.error(f"❌ ไม่พบข้อมูล `{search_val}`")
